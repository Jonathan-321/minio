#!/bin/bash

echo "🚀 Deploying Local MinIO Cluster with LakeFS and AIStor"
echo "======================================================="

# Set Docker paths
DOCKER_PATH="/Volumes/Docker/Docker.app/Contents/Resources/bin/docker"
DOCKER_COMPOSE_PATH="/Volumes/Docker/Docker.app/Contents/Resources/bin/docker-compose"

# Fallback to system paths if mounted volume not available
if [ ! -f "$DOCKER_PATH" ]; then
    DOCKER_PATH="docker"
    DOCKER_COMPOSE_PATH="docker-compose"
fi

# Check if Docker is running
if ! $DOCKER_PATH info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    echo "💡 Or run: ./install-docker.sh"
    exit 1
fi

# Check for required files
if [ ! -f "docker-compose.local.yml" ]; then
    echo "❌ docker-compose.local.yml not found!"
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
$DOCKER_COMPOSE_PATH -f docker-compose.local.yml down -v 2>/dev/null

# Pull latest images
echo "📥 Pulling latest Docker images..."
$DOCKER_COMPOSE_PATH -f docker-compose.local.yml pull

# Start the stack
echo "🚀 Starting MinIO cluster, LakeFS, and AIStor..."
$DOCKER_COMPOSE_PATH -f docker-compose.local.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

# Check MinIO nodes
for port in 9001 9002 9003; do
    if curl -s "http://localhost:$port/minio/health/live" >/dev/null; then
        echo "✅ MinIO node (port $port) is healthy"
    else
        echo "❌ MinIO node (port $port) is not responding"
    fi
done

# Check LakeFS
if curl -s "http://localhost:8000/api/v1/config" >/dev/null; then
    echo "✅ LakeFS is healthy"
else
    echo "❌ LakeFS is not responding"
fi

echo ""
echo "🎉 Local deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "   MinIO Console 1: http://localhost:9091 (admin/minioadmin123)"
echo "   MinIO Console 2: http://localhost:9092 (admin/minioadmin123)"  
echo "   MinIO Console 3: http://localhost:9093 (admin/minioadmin123)"
echo "   LakeFS UI:       http://localhost:8000 (setup required)"
echo ""
echo "🔧 MinIO Endpoints:"
echo "   Node 1: http://localhost:9001"
echo "   Node 2: http://localhost:9002"
echo "   Node 3: http://localhost:9003"
echo ""
echo "⚡ Quick test commands:"
echo "   python3 download_umi_data.py --generate --upload"
echo "   python3 download_umi_data.py --experiments --upload"
echo "   python3 download_umi_data.py --benchmark small_file_performance"
echo ""
echo "📋 View running containers:"
echo "   $DOCKER_COMPOSE_PATH -f docker-compose.local.yml ps"
echo ""
echo "📄 View logs:"
echo "   $DOCKER_COMPOSE_PATH -f docker-compose.local.yml logs -f [service-name]"
echo ""
echo "🔴 Stop all services:" 
echo "   $DOCKER_COMPOSE_PATH -f docker-compose.local.yml down"