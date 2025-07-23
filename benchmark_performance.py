#!/usr/bin/env python3
"""
MinIO + LakeFS Performance Benchmarker for UMI Data

Tests latency and throughput with realistic UMI dataset access patterns:
- Sequential video frame loading
- Random access to pose data
- Batch loading for training
- Concurrent access simulation
"""

import os
import sys
import time
import json
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
import boto3
from botocore.config import Config
import numpy as np
from dataclasses import dataclass
import requests
import tempfile

@dataclass
class BenchmarkConfig:
    """Configuration for performance benchmarks"""
    s3_endpoint: str = "http://localhost:80"
    bucket_name: str = "umi-real-data"
    dataset_name: str = "cup_arrangement_lab"
    num_threads: int = 4
    num_iterations: int = 100
    chunk_size_kb: int = 1024
    timeout_seconds: int = 30

class PerformanceBenchmarker:
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.s3_client = boto3.client(
            's3',
            endpoint_url=config.s3_endpoint,
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin123',
            config=Config(
                region_name='us-east-1',
                retries={'max_attempts': 3},
                max_pool_connections=50
            )
        )
        self.session = requests.Session()
        self.results = {}
    
    def list_dataset_files(self, dataset_name: str = None) -> List[Dict[str, Any]]:
        """List all files in a dataset"""
        if dataset_name is None:
            dataset_name = self.config.dataset_name
        
        prefix = f"datasets/{dataset_name}/"
        files = []
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.config.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified']
                    })
        except Exception as e:
            print(f"❌ Error listing files: {e}")
        
        return files
    
    def benchmark_single_file_read(self, file_key: str) -> Dict[str, float]:
        """Benchmark reading a single file"""
        start_time = time.time()
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.config.bucket_name,
                Key=file_key
            )
            
            # Read the entire file
            data = response['Body'].read()
            
            end_time = time.time()
            
            return {
                'success': True,
                'latency': end_time - start_time,
                'size_bytes': len(data),
                'throughput_mbps': len(data) / (1024 * 1024) / (end_time - start_time),
                'file_key': file_key
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'latency': time.time() - start_time,
                'file_key': file_key
            }
    
    def benchmark_concurrent_reads(self, file_keys: List[str], num_threads: int = None) -> Dict[str, Any]:
        """Benchmark concurrent file reads"""
        if num_threads is None:
            num_threads = self.config.num_threads
        
        print(f"🔄 Testing concurrent reads: {len(file_keys)} files, {num_threads} threads")
        
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(self.benchmark_single_file_read, key): key 
                      for key in file_keys[:self.config.num_iterations]}
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        end_time = time.time()
        
        # Calculate statistics
        successful_reads = [r for r in results if r.get('success', False)]
        failed_reads = [r for r in results if not r.get('success', False)]
        
        if successful_reads:
            latencies = [r['latency'] for r in successful_reads]
            throughputs = [r['throughput_mbps'] for r in successful_reads]
            sizes = [r['size_bytes'] for r in successful_reads]
            
            stats = {
                'total_files': len(file_keys),
                'successful_reads': len(successful_reads),
                'failed_reads': len(failed_reads),
                'total_time': end_time - start_time,
                'total_bytes': sum(sizes),
                'latency_stats': {
                    'mean': statistics.mean(latencies),
                    'median': statistics.median(latencies),
                    'min': min(latencies),
                    'max': max(latencies),
                    'std': statistics.stdev(latencies) if len(latencies) > 1 else 0
                },
                'throughput_stats': {
                    'mean_mbps': statistics.mean(throughputs),
                    'median_mbps': statistics.median(throughputs),
                    'min_mbps': min(throughputs),
                    'max_mbps': max(throughputs),
                    'total_mbps': sum(sizes) / (1024 * 1024) / (end_time - start_time)
                }
            }
        else:
            stats = {
                'total_files': len(file_keys),
                'successful_reads': 0,
                'failed_reads': len(failed_reads),
                'total_time': end_time - start_time,
                'error': 'All reads failed'
            }
        
        return stats
    
    def benchmark_sequential_access(self, file_keys: List[str]) -> Dict[str, Any]:
        """Benchmark sequential file access (simulating video playback)"""
        print(f"📹 Testing sequential access: {len(file_keys)} files")
        
        results = []
        start_time = time.time()
        
        for i, key in enumerate(file_keys[:self.config.num_iterations]):
            result = self.benchmark_single_file_read(key)
            results.append(result)
            
            if i % 10 == 0:
                print(f"  Progress: {i}/{min(len(file_keys), self.config.num_iterations)}")
        
        end_time = time.time()
        
        successful_reads = [r for r in results if r.get('success', False)]
        
        if successful_reads:
            latencies = [r['latency'] for r in successful_reads]
            throughputs = [r['throughput_mbps'] for r in successful_reads]
            sizes = [r['size_bytes'] for r in successful_reads]
            
            return {
                'access_pattern': 'sequential',
                'total_files': len(results),
                'successful_reads': len(successful_reads),
                'total_time': end_time - start_time,
                'avg_latency': statistics.mean(latencies),
                'avg_throughput_mbps': statistics.mean(throughputs),
                'total_throughput_mbps': sum(sizes) / (1024 * 1024) / (end_time - start_time),
                'latency_p95': sorted(latencies)[int(0.95 * len(latencies))] if len(latencies) > 20 else max(latencies)
            }
        
        return {'error': 'All sequential reads failed'}
    
    def benchmark_random_access(self, file_keys: List[str]) -> Dict[str, Any]:
        """Benchmark random file access (simulating data exploration)"""
        print(f"🎲 Testing random access: {len(file_keys)} files")
        
        # Randomly sample files
        import random
        sampled_keys = random.sample(file_keys, min(len(file_keys), self.config.num_iterations))
        
        results = []
        start_time = time.time()
        
        for i, key in enumerate(sampled_keys):
            result = self.benchmark_single_file_read(key)
            results.append(result)
            
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(sampled_keys)}")
        
        end_time = time.time()
        
        successful_reads = [r for r in results if r.get('success', False)]
        
        if successful_reads:
            latencies = [r['latency'] for r in successful_reads]
            throughputs = [r['throughput_mbps'] for r in successful_reads]
            sizes = [r['size_bytes'] for r in successful_reads]
            
            return {
                'access_pattern': 'random',
                'total_files': len(results),
                'successful_reads': len(successful_reads),
                'total_time': end_time - start_time,
                'avg_latency': statistics.mean(latencies),
                'avg_throughput_mbps': statistics.mean(throughputs),
                'total_throughput_mbps': sum(sizes) / (1024 * 1024) / (end_time - start_time),
                'latency_p95': sorted(latencies)[int(0.95 * len(latencies))] if len(latencies) > 20 else max(latencies)
            }
        
        return {'error': 'All random reads failed'}
    
    def benchmark_file_size_categories(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Benchmark different file size categories"""
        print("📊 Testing different file sizes...")
        
        # Categorize files by size
        categories = {
            'small': [],      # < 1MB
            'medium': [],     # 1MB - 10MB  
            'large': [],      # 10MB - 100MB
            'xlarge': []      # > 100MB
        }
        
        for file_info in files:
            size = file_info['size']
            if size < 1024 * 1024:
                categories['small'].append(file_info)
            elif size < 10 * 1024 * 1024:
                categories['medium'].append(file_info)
            elif size < 100 * 1024 * 1024:
                categories['large'].append(file_info)
            else:
                categories['xlarge'].append(file_info)
        
        results = {}
        
        for category, file_list in categories.items():
            if not file_list:
                continue
            
            print(f"  Testing {category} files ({len(file_list)} files)...")
            
            # Test a sample of each category
            sample_size = min(20, len(file_list))
            sample_files = file_list[:sample_size]
            
            category_results = []
            for file_info in sample_files:
                result = self.benchmark_single_file_read(file_info['key'])
                if result.get('success'):
                    category_results.append(result)
            
            if category_results:
                latencies = [r['latency'] for r in category_results]
                throughputs = [r['throughput_mbps'] for r in category_results]
                
                results[category] = {
                    'file_count': len(file_list),
                    'tested_files': len(category_results),
                    'avg_latency': statistics.mean(latencies),
                    'avg_throughput_mbps': statistics.mean(throughputs),
                    'avg_file_size_mb': statistics.mean([r['size_bytes'] for r in category_results]) / (1024 * 1024)
                }
        
        return results
    
    def benchmark_lakefs_operations(self) -> Dict[str, Any]:
        """Benchmark LakeFS-specific operations"""
        print("🌊 Testing LakeFS operations...")
        
        lakefs_url = "http://localhost:8000"
        auth = ('admin', 'admin123')
        
        operations = {}
        
        try:
            # Test repository listing
            start_time = time.time()
            response = self.session.get(f"{lakefs_url}/api/v1/repositories", auth=auth)
            operations['list_repositories'] = {
                'success': response.status_code == 200,
                'latency': time.time() - start_time,
                'status_code': response.status_code
            }
            
            # Test branch listing
            start_time = time.time()
            response = self.session.get(f"{lakefs_url}/api/v1/repositories/umi-dataset/branches", auth=auth)
            operations['list_branches'] = {
                'success': response.status_code == 200,
                'latency': time.time() - start_time,
                'status_code': response.status_code
            }
            
            # Test file listing through LakeFS
            start_time = time.time()
            response = self.session.get(
                f"{lakefs_url}/api/v1/repositories/umi-dataset/objects",
                params={'ref': 'main'},
                auth=auth
            )
            operations['list_objects'] = {
                'success': response.status_code == 200,
                'latency': time.time() - start_time,
                'status_code': response.status_code
            }
            
        except Exception as e:
            operations['error'] = str(e)
        
        return operations
    
    def run_comprehensive_benchmark(self, dataset_name: str = None) -> Dict[str, Any]:
        """Run all benchmark tests"""
        if dataset_name is None:
            dataset_name = self.config.dataset_name
        
        print(f"🚀 Starting comprehensive benchmark for dataset: {dataset_name}")
        print(f"   Endpoint: {self.config.s3_endpoint}")
        print(f"   Threads: {self.config.num_threads}")
        print(f"   Iterations: {self.config.num_iterations}")
        print()
        
        # List files
        files = self.list_dataset_files(dataset_name)
        if not files:
            return {'error': f'No files found for dataset {dataset_name}'}
        
        file_keys = [f['key'] for f in files]
        
        print(f"📁 Found {len(files)} files")
        total_size = sum(f['size'] for f in files)
        print(f"💾 Total size: {total_size / 1024**3:.2f} GB")
        print()
        
        benchmark_results = {
            'dataset_name': dataset_name,
            'config': {
                'num_files': len(files),
                'total_size_gb': total_size / 1024**3,
                'num_threads': self.config.num_threads,
                'num_iterations': self.config.num_iterations
            },
            'timestamp': time.time()
        }
        
        # Run benchmarks
        try:
            # 1. Concurrent reads
            benchmark_results['concurrent_reads'] = self.benchmark_concurrent_reads(file_keys)
            
            # 2. Sequential access
            benchmark_results['sequential_access'] = self.benchmark_sequential_access(file_keys)
            
            # 3. Random access  
            benchmark_results['random_access'] = self.benchmark_random_access(file_keys)
            
            # 4. File size categories
            benchmark_results['file_size_categories'] = self.benchmark_file_size_categories(files)
            
            # 5. LakeFS operations
            benchmark_results['lakefs_operations'] = self.benchmark_lakefs_operations()
            
        except Exception as e:
            benchmark_results['error'] = str(e)
        
        return benchmark_results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable performance report"""
        report = []
        report.append("=" * 60)
        report.append("📊 UMI Dataset Performance Benchmark Report")
        report.append("=" * 60)
        report.append(f"Dataset: {results.get('dataset_name', 'Unknown')}")
        report.append(f"Files: {results['config']['num_files']}")
        report.append(f"Total Size: {results['config']['total_size_gb']:.2f} GB")
        report.append("")
        
        # Concurrent reads
        if 'concurrent_reads' in results:
            cr = results['concurrent_reads']
            report.append("🔄 Concurrent Read Performance:")
            report.append(f"  Success Rate: {cr['successful_reads']}/{cr['total_files']} ({cr['successful_reads']/cr['total_files']*100:.1f}%)")
            if 'throughput_stats' in cr:
                report.append(f"  Avg Throughput: {cr['throughput_stats']['mean_mbps']:.1f} MB/s")
                report.append(f"  Total Throughput: {cr['throughput_stats']['total_mbps']:.1f} MB/s")
                report.append(f"  Avg Latency: {cr['latency_stats']['mean']*1000:.1f} ms")
                report.append(f"  P95 Latency: {cr['latency_stats']['max']*1000:.1f} ms")
            report.append("")
        
        # Sequential access
        if 'sequential_access' in results:
            sa = results['sequential_access']
            if 'avg_throughput_mbps' in sa:
                report.append("📹 Sequential Access (Video Playback Simulation):")
                report.append(f"  Avg Throughput: {sa['avg_throughput_mbps']:.1f} MB/s")
                report.append(f"  Total Throughput: {sa['total_throughput_mbps']:.1f} MB/s")
                report.append(f"  Avg Latency: {sa['avg_latency']*1000:.1f} ms")
                report.append(f"  P95 Latency: {sa['latency_p95']*1000:.1f} ms")
                report.append("")
        
        # Random access
        if 'random_access' in results:
            ra = results['random_access']
            if 'avg_throughput_mbps' in ra:
                report.append("🎲 Random Access (Data Exploration Simulation):")
                report.append(f"  Avg Throughput: {ra['avg_throughput_mbps']:.1f} MB/s")
                report.append(f"  Total Throughput: {ra['total_throughput_mbps']:.1f} MB/s")
                report.append(f"  Avg Latency: {ra['avg_latency']*1000:.1f} ms")
                report.append(f"  P95 Latency: {ra['latency_p95']*1000:.1f} ms")
                report.append("")
        
        # File size performance
        if 'file_size_categories' in results:
            report.append("📊 Performance by File Size:")
            for category, stats in results['file_size_categories'].items():
                report.append(f"  {category.upper()} ({stats['avg_file_size_mb']:.1f} MB avg):")
                report.append(f"    Throughput: {stats['avg_throughput_mbps']:.1f} MB/s")
                report.append(f"    Latency: {stats['avg_latency']*1000:.1f} ms")
            report.append("")
        
        # LakeFS operations
        if 'lakefs_operations' in results:
            lo = results['lakefs_operations']
            report.append("🌊 LakeFS Operations:")
            for op, stats in lo.items():
                if isinstance(stats, dict) and 'success' in stats:
                    status = "✅" if stats['success'] else "❌"
                    report.append(f"  {op}: {status} ({stats['latency']*1000:.1f} ms)")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Benchmark UMI dataset performance')
    parser.add_argument('--dataset', default='cup_arrangement_lab', help='Dataset name to benchmark')
    parser.add_argument('--endpoint', default='http://localhost:80', help='MinIO endpoint')
    parser.add_argument('--threads', type=int, default=4, help='Number of concurrent threads')
    parser.add_argument('--iterations', type=int, default=100, help='Number of iterations per test')
    parser.add_argument('--output', help='Output file for results (JSON)')
    parser.add_argument('--report', help='Output file for human-readable report')
    
    args = parser.parse_args()
    
    config = BenchmarkConfig(
        s3_endpoint=args.endpoint,
        dataset_name=args.dataset,
        num_threads=args.threads,
        num_iterations=args.iterations
    )
    
    benchmarker = PerformanceBenchmarker(config)
    
    try:
        results = benchmarker.run_comprehensive_benchmark()
        
        # Generate report
        report = benchmarker.generate_report(results)
        print(report)
        
        # Save results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Results saved to {args.output}")
        
        if args.report:
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"📊 Report saved to {args.report}")
    
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()