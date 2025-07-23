#!/bin/bash

# Deploy ControlPlane-style MinIO setup locally
echo "🚀 Deploying ControlPlane-style MinIO"
echo "====================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop first:"
    echo "   https://www.docker.com/products/docker-desktop/"
    echo ""
    echo "💡 Or run: ./install-docker.sh"
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is ready"
echo ""

# Stop any existing containers
echo "🧹 Stopping existing containers..."
docker compose -f minio-demo.yaml down 2>/dev/null || true

# Pull latest images
echo "📥 Pulling latest images..."
docker compose -f minio-demo.yaml pull

# Start the ControlPlane-style setup
echo "🚀 Starting MinIO (ControlPlane style)..."
docker compose -f minio-demo.yaml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
echo "📊 Service status:"
docker compose -f minio-demo.yaml ps

echo ""
echo "🧪 Testing the deployment..."

# Install MinIO client if not present
if ! command -v mc &> /dev/null; then
    echo "📥 Installing MinIO client (mc)..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -O https://dl.min.io/client/mc/release/darwin-amd64/mc
        chmod +x mc
        sudo mv mc /usr/local/bin/ 2>/dev/null || mv mc ~/mc
        echo "   MinIO client installed as ~/mc (if sudo failed)"
        MC_CMD="~/mc"
    else
        # Linux
        curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
        chmod +x mc
        sudo mv mc /usr/local/bin/ 2>/dev/null || mv mc ~/mc
        echo "   MinIO client installed as ~/mc (if sudo failed)"
        MC_CMD="~/mc"
    fi
else
    MC_CMD="mc"
fi

# Wait a bit more for nginx to be ready
sleep 10

echo ""
echo "🔧 Setting up MinIO client..."

# Configure mc alias (like ControlPlane demo)
echo "This is a demo test" > test.txt

echo "📋 Current aliases:"
$MC_CMD alias ls

echo ""
echo "🔗 Adding MinIO alias..."
$MC_CMD alias set demo http://localhost minioadmin minioadmin

echo ""
echo "🧪 Running ControlPlane-style tests..."

# Test bucket operations (like ControlPlane demo)
echo "📦 Creating bucket..."
$MC_CMD mb demo/mybucket

echo "📤 Uploading test file..."
$MC_CMD cp test.txt demo/mybucket

echo "📋 Listing buckets..."
$MC_CMD ls demo

echo "📋 Listing bucket contents..."
$MC_CMD ls demo/mybucket

echo "📥 Downloading file..."
$MC_CMD cp demo/mybucket/test.txt ./downloaded.txt

echo "✅ Verifying download..."
cat downloaded.txt

echo "🗑️  Cleaning up..."
$MC_CMD rm demo/mybucket/test.txt
$MC_CMD ls demo/mybucket

# Clean up test files
rm -f test.txt downloaded.txt

echo ""
echo "🐍 Testing with Python S3..."
python3 miniotest.py http://localhost

echo ""
echo "✅ ControlPlane-style MinIO deployment complete!"
echo ""
echo "🌐 Access URLs:"
echo "   S3 API: http://localhost (port 80)"
echo "   MinIO Console: http://localhost:9090"
echo "   Direct S3 API: http://localhost:9000"
echo "   Direct Console: http://localhost:9001"
echo ""
echo "🔑 Credentials:"
echo "   Username: minioadmin"
echo "   Password: minioadmin"
echo ""
echo "🛠️  Management commands:"
echo "   View logs: docker compose -f minio-demo.yaml logs -f"
echo "   Stop: docker compose -f minio-demo.yaml down"
echo "   Restart: docker compose -f minio-demo.yaml restart"
echo ""
echo "🧪 Test again:"
echo "   python3 miniotest.py http://localhost"