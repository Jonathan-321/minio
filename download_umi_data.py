#!/usr/bin/env python3
"""
UMI Data Downloader and Uploader
Downloads sample robotics data from UMI DATA HUB and uploads to MinIO cluster
"""

import os
import json
import requests
import zipfile
from pathlib import Path
from minio import Minio
from minio.error import S3Error
import argparse
from typing import List, Dict, Any
import hashlib
import time

class UMIDataManager:
    """Manages UMI robotics data download and upload to MinIO"""
    
    def __init__(self, minio_endpoint="localhost:9001", 
                 access_key="minioadmin", secret_key="minioadmin123"):
        self.data_dir = Path("./data/umi")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # MinIO client setup
        self.minio_client = Minio(
            minio_endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        
        # UMI data sources (sample URLs - replace with actual UMI hub URLs)
        self.data_sources = {
            "pose_data": {
                "url": "https://umi-data.github.io/samples/pose_data.json",
                "bucket": "umi-raw",
                "prefix": "pose/",
                "description": "Robot pose and joint angle data"
            },
            "gripper_data": {
                "url": "https://umi-data.github.io/samples/gripper_data.json", 
                "bucket": "umi-raw",
                "prefix": "gripper/",
                "description": "Gripper state and force data"
            },
            "video_sample": {
                "url": "https://umi-data.github.io/samples/video_sample.mp4",
                "bucket": "umi-raw", 
                "prefix": "video/",
                "description": "Camera feed and visual data"
            }
        }
    
    def generate_sample_data(self):
        """Generate sample robotics data for testing"""
        print("🤖 Generating sample UMI robotics data...")
        
        # Generate pose data (joint angles, end-effector positions)
        pose_data = {
            "timestamp": time.time(),
            "episodes": []
        }
        
        for episode in range(5):
            episode_data = {
                "episode_id": f"ep_{episode:03d}",
                "duration": 10.0 + episode * 2,
                "frames": []
            }
            
            for frame in range(100):
                frame_data = {
                    "frame_id": frame,
                    "timestamp": frame * 0.1,
                    "joint_angles": [0.1 * frame + i * 0.05 for i in range(7)],
                    "end_effector_pos": [
                        0.5 + 0.001 * frame,
                        0.3 + 0.002 * frame, 
                        0.2 + 0.001 * frame
                    ],
                    "end_effector_rot": [0, 0, 0.001 * frame, 1]
                }
                episode_data["frames"].append(frame_data)
            
            pose_data["episodes"].append(episode_data)
        
        pose_file = self.data_dir / "pose_data.json"
        with open(pose_file, 'w') as f:
            json.dump(pose_data, f, indent=2)
        
        # Generate gripper data
        gripper_data = {
            "timestamp": time.time(),
            "episodes": []
        }
        
        for episode in range(5):
            episode_data = {
                "episode_id": f"ep_{episode:03d}",
                "gripper_states": []
            }
            
            for frame in range(100):
                state = {
                    "frame_id": frame,
                    "timestamp": frame * 0.1,
                    "gripper_position": 0.5 + 0.3 * (frame % 20) / 20,
                    "gripper_force": [1.2, 0.8, 2.1],
                    "contact_detected": frame % 15 < 3,
                    "object_detected": frame % 25 < 5
                }
                episode_data["gripper_states"].append(state)
            
            gripper_data["episodes"].append(episode_data)
        
        gripper_file = self.data_dir / "gripper_data.json"
        with open(gripper_file, 'w') as f:
            json.dump(gripper_data, f, indent=2)
        
        # Generate metadata files for different data sizes
        self._generate_size_variants()
        
        print(f"✅ Sample data generated in {self.data_dir}")
        return [pose_file, gripper_file]
    
    def _generate_size_variants(self):
        """Generate data files of varying sizes for performance testing"""
        sizes = {
            "small": 100,      # 100 frames
            "medium": 1000,    # 1000 frames  
            "large": 10000     # 10000 frames
        }
        
        for size_name, frame_count in sizes.items():
            # Large pose dataset
            large_data = {"episodes": []}
            for ep in range(frame_count // 100):
                episode = {
                    "episode_id": f"{size_name}_ep_{ep:03d}",
                    "frames": [
                        {
                            "frame_id": f,
                            "joint_angles": [f * 0.001 + i * 0.01 for i in range(7)],
                            "end_effector_pos": [f * 0.0001, f * 0.0002, 0.2]
                        }
                        for f in range(100)
                    ]
                }
                large_data["episodes"].append(episode)
            
            size_file = self.data_dir / f"pose_data_{size_name}.json"
            with open(size_file, 'w') as f:
                json.dump(large_data, f)
            
            print(f"📊 Generated {size_name} dataset: {size_file.stat().st_size / 1024:.1f} KB")
    
    def upload_to_minio(self, local_files: List[Path]):
        """Upload files to MinIO cluster"""
        print("📤 Uploading data to MinIO cluster...")
        
        for file_path in local_files:
            try:
                # Determine bucket and object name based on file type
                if "pose" in file_path.name:
                    bucket_name = "umi-raw"
                    object_name = f"pose/{file_path.name}"
                elif "gripper" in file_path.name:
                    bucket_name = "umi-raw" 
                    object_name = f"gripper/{file_path.name}"
                else:
                    bucket_name = "umi-raw"
                    object_name = f"misc/{file_path.name}"
                
                # Ensure bucket exists
                if not self.minio_client.bucket_exists(bucket_name):
                    self.minio_client.make_bucket(bucket_name)
                
                # Upload file
                self.minio_client.fput_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    file_path=str(file_path)
                )
                
                print(f"✅ Uploaded: {file_path.name} -> s3://{bucket_name}/{object_name}")
                
            except S3Error as e:
                print(f"❌ Upload failed for {file_path.name}: {e}")
    
    def create_experiment_configs(self):
        """Create experiment configuration files"""
        print("⚙️  Creating experiment configurations...")
        
        experiments = {
            "small_file_performance": {
                "description": "Test small file (pose/gripper) read/write performance",
                "data_types": ["pose", "gripper"],
                "file_sizes": ["small", "medium"],
                "operations": ["read", "write", "batch_read"],
                "metrics": ["latency", "throughput", "cache_hit_rate"]
            },
            "large_file_streaming": {
                "description": "Test video streaming and large file handling",
                "data_types": ["video"],
                "file_sizes": ["large"],
                "operations": ["stream_read", "partial_read"],
                "metrics": ["bandwidth", "latency", "buffer_efficiency"]
            },
            "mixed_workload": {
                "description": "Test mixed robotics workload (pose + video)",
                "data_types": ["pose", "gripper", "video"],
                "file_sizes": ["small", "medium", "large"],
                "operations": ["concurrent_read", "batch_write"],
                "metrics": ["overall_throughput", "resource_utilization"]
            }
        }
        
        experiments_dir = self.data_dir / "experiments"
        experiments_dir.mkdir(exist_ok=True)
        
        for exp_name, config in experiments.items():
            config_file = experiments_dir / f"{exp_name}.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"📝 Created experiment config: {config_file}")
        
        return list(experiments_dir.glob("*.json"))
    
    def run_benchmark(self, experiment_name: str):
        """Run a simple benchmark experiment"""
        print(f"🏃 Running benchmark: {experiment_name}")
        
        start_time = time.time()
        
        if experiment_name == "small_file_performance":
            # Test small file operations
            for i in range(10):
                obj_name = f"pose/test_pose_{i}.json"
                try:
                    # Write test
                    test_data = {"frame": i, "data": [i] * 100}
                    self.minio_client.put_object(
                        "umi-experiments",
                        obj_name,
                        json.dumps(test_data).encode(),
                        len(json.dumps(test_data))
                    )
                    
                    # Read test
                    response = self.minio_client.get_object("umi-experiments", obj_name)
                    data = json.loads(response.read().decode())
                    response.close()
                    
                except Exception as e:
                    print(f"❌ Benchmark error: {e}")
        
        duration = time.time() - start_time
        print(f"⏱️  Benchmark completed in {duration:.2f} seconds")
        
        return {
            "experiment": experiment_name,
            "duration": duration,
            "timestamp": time.time()
        }

def main():
    parser = argparse.ArgumentParser(description="UMI Data Manager")
    parser.add_argument("--generate", action="store_true", help="Generate sample data")
    parser.add_argument("--upload", action="store_true", help="Upload data to MinIO")
    parser.add_argument("--experiments", action="store_true", help="Create experiment configs")
    parser.add_argument("--benchmark", type=str, help="Run benchmark experiment")
    parser.add_argument("--minio-endpoint", default="localhost:9001", help="MinIO endpoint")
    
    args = parser.parse_args()
    
    manager = UMIDataManager(minio_endpoint=args.minio_endpoint)
    
    if args.generate:
        files = manager.generate_sample_data()
        if args.upload:
            manager.upload_to_minio(files)
    
    if args.experiments:
        exp_files = manager.create_experiment_configs()
        if args.upload:
            manager.upload_to_minio(exp_files)
    
    if args.benchmark:
        result = manager.run_benchmark(args.benchmark)
        print(f"📊 Benchmark result: {result}")

if __name__ == "__main__":
    main()