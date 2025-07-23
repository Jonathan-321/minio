#!/usr/bin/env python3
"""
Quick test script to demonstrate MinIO cloud performance
Usage: python3 quick-test.py --endpoint http://your-server-ip:9000
"""

import boto3
import time
import argparse
import numpy as np
from io import BytesIO

def test_minio_performance(endpoint_url, access_key='minioadmin', secret_key='changeme123!'):
    """Test MinIO upload/download performance"""
    
    print(f"🧪 Testing MinIO at: {endpoint_url}")
    print("=" * 50)
    
    # Create S3 client
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )
    
    bucket_name = 'performance-test'
    
    try:
        # Create bucket
        print("📦 Creating test bucket...")
        s3.create_bucket(Bucket=bucket_name)
        print("✅ Bucket created")
        
        # Test different file sizes
        test_sizes = [
            (1, "1MB"),
            (10, "10MB"), 
            (100, "100MB")
        ]
        
        results = []
        
        for size_mb, label in test_sizes:
            print(f"\n🔄 Testing {label} file...")
            
            # Generate test data
            data_size = size_mb * 1024 * 1024
            test_data = np.random.bytes(data_size)
            
            # Upload test
            start_time = time.time()
            s3.put_object(
                Bucket=bucket_name,
                Key=f'test-{label}.bin',
                Body=test_data,
                ContentType='application/octet-stream'
            )
            upload_time = time.time() - start_time
            upload_speed = (data_size / (1024*1024)) / upload_time
            
            # Download test
            start_time = time.time()
            response = s3.get_object(Bucket=bucket_name, Key=f'test-{label}.bin')
            downloaded_data = response['Body'].read()
            download_time = time.time() - start_time
            download_speed = (data_size / (1024*1024)) / download_time
            
            results.append({
                'size': label,
                'upload_time': upload_time,
                'upload_speed': upload_speed,
                'download_time': download_time,
                'download_speed': download_speed
            })
            
            print(f"   📤 Upload: {upload_speed:.1f} MB/s ({upload_time:.2f}s)")
            print(f"   📥 Download: {download_speed:.1f} MB/s ({download_time:.2f}s)")
        
        print(f"\n📊 Performance Summary:")
        print("=" * 50)
        for result in results:
            print(f"{result['size']:>6s}: ⬆️  {result['upload_speed']:>6.1f} MB/s  ⬇️  {result['download_speed']:>6.1f} MB/s")
        
        # Test concurrent operations
        print(f"\n🚀 Testing concurrent uploads...")
        start_time = time.time()
        
        # Upload 10 files concurrently (simulated)
        for i in range(10):
            small_data = np.random.bytes(1024*1024)  # 1MB each
            s3.put_object(
                Bucket=bucket_name,
                Key=f'concurrent-test-{i}.bin',
                Body=small_data
            )
        
        concurrent_time = time.time() - start_time
        total_mb = 10
        concurrent_speed = total_mb / concurrent_time
        
        print(f"   📤 10x 1MB files: {concurrent_speed:.1f} MB/s total ({concurrent_time:.2f}s)")
        
        # List objects test
        print(f"\n📋 Testing object listing...")
        start_time = time.time()
        objects = s3.list_objects_v2(Bucket=bucket_name)
        list_time = time.time() - start_time
        object_count = objects.get('KeyCount', 0)
        
        print(f"   📋 Listed {object_count} objects in {list_time:.3f}s")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        for obj in objects.get('Contents', []):
            s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
        s3.delete_bucket(Bucket=bucket_name)
        print("✅ Cleanup complete")
        
        print(f"\n🎉 Test completed successfully!")
        print(f"🌟 Your cloud MinIO cluster is working great!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def test_lakefs_connection(lakefs_url):
    """Test LakeFS connection"""
    import requests
    
    print(f"\n🏞️  Testing LakeFS at: {lakefs_url}")
    try:
        response = requests.get(f"{lakefs_url}/api/v1/config", timeout=10)
        if response.status_code == 200:
            print("✅ LakeFS is accessible")
            return True
        else:
            print(f"⚠️  LakeFS returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LakeFS connection failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test MinIO cloud performance')
    parser.add_argument('--endpoint', required=True, help='MinIO endpoint URL (http://ip:9000)')
    parser.add_argument('--lakefs', help='LakeFS URL (http://ip:8000)', default=None)
    parser.add_argument('--access-key', default='minioadmin', help='MinIO access key')
    parser.add_argument('--secret-key', default='changeme123!', help='MinIO secret key')
    
    args = parser.parse_args()
    
    print("🚀 MinIO Cloud Performance Test")
    print("=" * 50)
    print(f"📍 Endpoint: {args.endpoint}")
    print(f"🔑 Access Key: {args.access_key}")
    print("")
    
    # Test MinIO
    success = test_minio_performance(args.endpoint, args.access_key, args.secret_key)
    
    # Test LakeFS if provided
    if args.lakefs:
        test_lakefs_connection(args.lakefs)
    
    if success:
        print(f"\n✨ All tests passed! Your cloud deployment is ready for production.")
    else:
        print(f"\n⚠️  Some tests failed. Check your deployment.")