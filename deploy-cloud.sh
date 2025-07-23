#!/bin/bash

echo "🚀 Deploying MinIO Cluster to Cloud"
echo "==================================="

# Configuration
SERVER_USER=${1:-ubuntu}
SERVER_HOST=${2:-""}
SSH_KEY=${3:-"~/.ssh/id_rsa"}
PROJECT_NAME="minioDemoProject"

if [ -z "$SERVER_HOST" ]; then
    echo "❌ Usage: $0 [user] [server-host] [ssh-key]"
    echo "   Example: $0 ubuntu myserver.com ~/.ssh/id_rsa"
    exit 1
fi

echo "📋 Deployment Configuration:"
echo "   Server: $SERVER_USER@$SERVER_HOST"
echo "   SSH Key: $SSH_KEY"
echo "   Project: $PROJECT_NAME"
echo ""

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found: $SSH_KEY"
    exit 1
fi

# Test SSH connection
echo "🔐 Testing SSH connection..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "echo 'SSH connection successful'" 2>/dev/null; then
    echo "❌ Cannot connect to server. Please check:"
    echo "   - Server is running and accessible"
    echo "   - SSH key has correct permissions (chmod 600)"
    echo "   - User has access to the server"
    exit 1
fi

echo "✅ SSH connection successful"

# Create project directory on server
echo "📁 Creating project directory..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "mkdir -p ~/$PROJECT_NAME && rm -rf ~/$PROJECT_NAME/*"

# Copy project files
echo "📤 Uploading project files..."
rsync -avz --progress -e "ssh -i $SSH_KEY" \
    --exclude='.git' \
    --exclude='data/' \
    --exclude='node_modules/' \
    --exclude='.DS_Store' \
    . "$SERVER_USER@$SERVER_HOST:~/$PROJECT_NAME/"

if [ $? -ne 0 ]; then
    echo "❌ Failed to upload files"
    exit 1
fi

echo "✅ Files uploaded successfully"

# Install Docker on server if needed
echo "🐳 Installing Docker on server..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" << 'EOF'
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        echo "Docker installed successfully"
    else
        echo "Docker already installed"
    fi
    
    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        echo "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo "Docker Compose installed successfully"
    else
        echo "Docker Compose already installed"
    fi
EOF

# Setup environment variables
echo "⚙️ Setting up environment..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" << EOF
    cd ~/$PROJECT_NAME
    
    # Copy environment template
    cp .env.cloud .env
    
    # Update server IP in environment
    SERVER_IP=\$(curl -s ifconfig.me)
    sed -i "s/your-server-ip-here/\$SERVER_IP/g" .env
    sed -i "s/your-domain.com/\$SERVER_IP/g" .env
    
    echo "Environment configured with server IP: \$SERVER_IP"
EOF

# Deploy the stack
echo "🚀 Deploying stack..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" << EOF
    cd ~/$PROJECT_NAME
    
    # Make scripts executable
    chmod +x deploy-local.sh scripts/setup-buckets.sh
    
    # Pull images first
    docker-compose -f docker-compose.cloud.yml pull
    
    # Start the stack
    docker-compose -f docker-compose.cloud.yml up -d
    
    echo "Waiting for services to start..."
    sleep 30
    
    # Check service status
    docker-compose -f docker-compose.cloud.yml ps
EOF

# Get server IP and show access information
SERVER_IP=$(ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "curl -s ifconfig.me")

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "📊 Service URLs:"
echo "   MinIO S3 API:     http://$SERVER_IP"
echo "   MinIO Console:    http://$SERVER_IP:9090"
echo "   LakeFS:           http://$SERVER_IP:8000" 
echo "   Grafana:          http://$SERVER_IP:3000 (admin/admin123)"
echo "   Prometheus:       http://$SERVER_IP:9090"
echo ""
echo "🔑 Default Credentials:"
echo "   MinIO:    minioadmin / minioadmin123"
echo "   LakeFS:   admin / (setup required)"
echo "   Grafana:  admin / admin123"
echo ""
echo "🔧 Management Commands:"
echo "   SSH to server:    ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST"
echo "   View logs:        docker-compose -f docker-compose.cloud.yml logs -f [service]"
echo "   Stop services:    docker-compose -f docker-compose.cloud.yml down"
echo "   Update stack:     docker-compose -f docker-compose.cloud.yml pull && docker-compose -f docker-compose.cloud.yml up -d"
echo ""
echo "⚡ Test Commands:"
echo "   Generate data:    python3 download_umi_data.py --generate --minio-endpoint $SERVER_IP:80"
echo "   Run benchmark:    python3 download_umi_data.py --benchmark small_file_performance --minio-endpoint $SERVER_IP:80"