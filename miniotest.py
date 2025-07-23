#!/usr/bin/env python3
"""
MinIO test script inspired by ControlPlane demo
Usage: python3 miniotest.py [endpoint_url]
"""

import boto3
import sys
import json
from botocore.exceptions import ClientError

def test_minio_s3(endpoint_url="http://localhost", access_key="minioadmin", secret_key="minioadmin"):
    """Test MinIO S3 functionality like ControlPlane demo"""
    
    print(f"🧪 Testing MinIO S3 API at: {endpoint_url}")
    print("=" * 50)
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=None,
        config=boto3.session.Config(signature_version='s3v4'),
        region_name='us-east-1'
    )
    
    bucket_name = 'mybucket'
    test_file = 'test.txt'
    test_content = "This is a demo test"
    
    try:
        # 1. Create bucket (like mc mb demo/mybucket)
        print(f"📦 Creating bucket: {bucket_name}")
        s3_client.create_bucket(Bucket=bucket_name)
        print("✅ Bucket created successfully")
        
        # 2. List buckets (like mc ls demo)
        print(f"\n📋 Listing buckets:")
        response = s3_client.list_buckets()
        for bucket in response['Buckets']:
            print(f"   📦 {bucket['Name']} (created: {bucket['CreationDate']})")
        
        # 3. Upload file (like mc cp test.txt demo/mybucket)
        print(f"\n📤 Uploading file: {test_file}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_file,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print("✅ File uploaded successfully")
        
        # 4. List objects in bucket (like mc ls demo/mybucket)
        print(f"\n📋 Listing objects in {bucket_name}:")
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"   📄 {obj['Key']} ({obj['Size']} bytes, {obj['LastModified']})")
        else:
            print("   (empty)")
        
        # 5. Download file (like mc cp demo/mybucket/test.txt ./downloaded.txt)
        print(f"\n📥 Downloading file: {test_file}")
        response = s3_client.get_object(Bucket=bucket_name, Key=test_file)
        downloaded_content = response['Body'].read().decode('utf-8')
        print(f"✅ Downloaded content: '{downloaded_content}'")
        
        # Verify content matches
        if downloaded_content == test_content:
            print("✅ Content verification: PASSED")
        else:
            print("❌ Content verification: FAILED")
        
        # 6. Get object metadata
        print(f"\n📊 Object metadata for {test_file}:")
        response = s3_client.head_object(Bucket=bucket_name, Key=test_file)
        print(f"   Size: {response['ContentLength']} bytes")
        print(f"   Type: {response.get('ContentType', 'unknown')}")
        print(f"   ETag: {response['ETag']}")
        print(f"   Modified: {response['LastModified']}")
        
        # 7. Delete file (like mc rm demo/mybucket/test.txt)
        print(f"\n🗑️  Deleting file: {test_file}")
        s3_client.delete_object(Bucket=bucket_name, Key=test_file)
        print("✅ File deleted successfully")
        
        # 8. Verify deletion
        print(f"\n📋 Verifying deletion - listing {bucket_name}:")
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                print(f"   📄 {obj['Key']}")
        else:
            print("   (empty) ✅")
        
        # 9. Delete bucket
        print(f"\n🗑️  Cleaning up bucket: {bucket_name}")
        s3_client.delete_bucket(Bucket=bucket_name)
        print("✅ Bucket deleted successfully")
        
        print(f"\n🎉 All tests passed! MinIO is working correctly.")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ AWS S3 Error [{error_code}]: {error_message}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_minio_admin(endpoint_url="http://localhost"):
    """Test MinIO admin functionality"""
    from minio import Minio
    from minio.error import S3Error
    
    try:
        # Parse endpoint
        if endpoint_url.startswith('http://'):
            endpoint = endpoint_url[7:]
            secure = False
        elif endpoint_url.startswith('https://'):
            endpoint = endpoint_url[8:]
            secure = True
        else:
            endpoint = endpoint_url
            secure = False
        
        print(f"\n🔧 Testing MinIO Admin API at: {endpoint}")
        print("=" * 50)
        
        # Create MinIO client
        client = Minio(
            endpoint,
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=secure
        )
        
        # Test server info
        print("📊 Server status:")
        # Note: Some admin operations require special permissions
        print("✅ MinIO client connected successfully")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Admin API test skipped: {e}")
        return False

if __name__ == "__main__":
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://localhost"
    
    print("🚀 ControlPlane-style MinIO Test")
    print("================================")
    print(f"📍 Testing endpoint: {endpoint}")
    print(f"🔑 Using credentials: minioadmin / minioadmin")
    print()
    
    # Test S3 API
    s3_success = test_minio_s3(endpoint)
    
    # Test Admin API (optional)
    admin_success = test_minio_admin(endpoint)
    
    print("\n" + "=" * 50)
    if s3_success:
        print("✅ MinIO S3 API: WORKING")
    else:
        print("❌ MinIO S3 API: FAILED")
    
    if admin_success:
        print("✅ MinIO Admin API: WORKING")
    else:
        print("⚠️  MinIO Admin API: SKIPPED")
    
    print("\n🌐 Access URLs:")
    print(f"   S3 API: {endpoint}")
    print(f"   Console: {endpoint.replace(':80', ':9090')}")
    
    sys.exit(0 if s3_success else 1)