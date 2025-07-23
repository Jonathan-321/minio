#!/bin/bash

set -e

echo "🚀 Setting up LakeFS with MinIO..."

# Wait for services to be ready
echo "⏳ Waiting for MinIO and LakeFS to be ready..."
sleep 30

# Check if LakeFS is accessible
until curl -f http://localhost:8000/api/v1/config; do
    echo "Waiting for LakeFS..."
    sleep 5
done

# Initialize LakeFS
echo "🔧 Initializing LakeFS..."
lakefs_auth_response=$(curl -s -X POST http://localhost:8000/api/v1/setup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "email": "admin@example.com"
  }')

# Extract access key and secret key
access_key=$(echo $lakefs_auth_response | grep -o '"access_key_id":"[^"]*' | cut -d'"' -f4)
secret_key=$(echo $lakefs_auth_response | grep -o '"secret_access_key":"[^"]*' | cut -d'"' -f4)

echo "✅ LakeFS initialized with credentials:"
echo "Access Key: $access_key"
echo "Secret Key: $secret_key"

# Create a test repository for UMI data
echo "📁 Creating UMI data repository..."
curl -X POST http://localhost:8000/api/v1/repositories \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n admin:admin123 | base64)" \
  -d '{
    "name": "umi-dataset",
    "storage_namespace": "s3://umi-data/",
    "default_branch": "main"
  }'

echo "✅ Repository 'umi-dataset' created successfully!"

# Create sample branches for different experiments
echo "🌿 Creating experiment branches..."
for branch in "experiment-1" "experiment-2" "baseline"; do
  curl -X POST http://localhost:8000/api/v1/repositories/umi-dataset/branches \
    -H "Content-Type: application/json" \
    -H "Authorization: Basic $(echo -n admin:admin123 | base64)" \
    -d "{
      \"name\": \"$branch\",
      \"source\": \"main\"
    }"
  echo "✅ Branch '$branch' created"
done

echo "🎉 LakeFS setup complete!"
echo ""
echo "🌐 Access URLs:"
echo "  - LakeFS UI: http://localhost:8000"
echo "  - MinIO Console: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin123)"
echo ""
echo "📊 Credentials:"
echo "  - LakeFS: admin/admin123"
echo "  - MinIO: minioadmin/minioadmin123"