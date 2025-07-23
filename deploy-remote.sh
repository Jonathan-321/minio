#!/bin/bash

# Remote MinIO + LakeFS Deployment Script
# Optimized for cloud server deployment with performance tuning

set -e

REMOTE_HOST=${1:-"your-server.com"}
REMOTE_USER=${2:-"ubuntu"}
SSH_KEY=${3:-"~/.ssh/id_rsa"}

echo "🚀 Deploying MinIO + LakeFS stack to remote server"
echo "   Host: $REMOTE_HOST"
echo "   User: $REMOTE_USER"
echo ""

# Function to run commands on remote server
remote_exec() {
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "$@"
}

# Function to copy files to remote server
remote_copy() {
    scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$1" "$REMOTE_USER@$REMOTE_HOST:$2"
}

echo "📋 Step 1: Checking remote server requirements..."

# Check if server is accessible
if ! remote_exec "echo 'Server accessible'"; then
    echo "❌ Cannot connect to remote server"
    exit 1
fi

# Check system resources
echo "🔍 Checking system resources..."
remote_exec "echo 'CPU cores:' \$(nproc) && echo 'Memory:' \$(free -h | grep Mem | awk '{print \$2}') && echo 'Disk:' \$(df -h / | tail -1 | awk '{print \$4}') available"

echo ""
echo "📦 Step 2: Installing dependencies..."

# Update system and install Docker
remote_exec "
sudo apt-get update -y
sudo apt-get install -y docker.io docker-compose-plugin curl htop iotop
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $REMOTE_USER
"

echo ""
echo "📁 Step 3: Creating deployment directory..."
remote_exec "mkdir -p ~/miniodemo"

echo ""
echo "📤 Step 4: Copying configuration files..."

# Copy all necessary files
for file in docker-compose.yml nginx.conf prometheus.yml setup-lakefs.sh; do
    echo "  Copying $file..."
    remote_copy "$file" "~/miniodemo/"
done

# Copy Python scripts
for script in download_umi_data.py benchmark_performance.py; do
    echo "  Copying $script..."
    remote_copy "$script" "~/miniodemo/"
done

# Copy Grafana configuration
echo "  Copying Grafana config..."
remote_exec "mkdir -p ~/miniodemo/grafana/provisioning/datasources"
remote_copy "grafana/provisioning/datasources/prometheus.yml" "~/miniodemo/grafana/provisioning/datasources/"

echo ""
echo "🔧 Step 5: Configuring for production..."

# Create production docker-compose override
remote_exec "cat > ~/miniodemo/docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  minio1:
    volumes:
      - /data/minio1:/data
    environment:
      MINIO_PROMETHEUS_AUTH_TYPE: public
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  minio2:
    volumes:
      - /data/minio2:/data
    environment:
      MINIO_PROMETHEUS_AUTH_TYPE: public
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  minio3:
    volumes:
      - /data/minio3:/data
    environment:
      MINIO_PROMETHEUS_AUTH_TYPE: public
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  nginx:
    ports:
      - '80:80'
      - '9090:9090'
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro

  lakefs:
    environment:
      - LAKEFS_STATS_ENABLED=false
      - LAKEFS_LOGGING_LEVEL=WARN
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
EOF"

# Create production nginx config
remote_exec "cat > ~/miniodemo/nginx.prod.conf << 'EOF'
events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Performance tuning
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    upstream minio {
        least_conn;
        keepalive 32;
        server minio1:9000 max_fails=3 fail_timeout=30s;
        server minio2:9000 max_fails=3 fail_timeout=30s;
        server minio3:9000 max_fails=3 fail_timeout=30s;
    }

    upstream minio-console {
        least_conn;
        server minio1:9001;
        server minio2:9001;
        server minio3:9001;
    }

    server {
        listen 80;
        server_name _;

        client_max_body_size 5G;
        client_body_buffer_size 128k;
        client_body_timeout 300s;
        client_header_timeout 60s;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
        proxy_request_buffering off;

        location / {
            proxy_pass http://minio;
            proxy_http_version 1.1;
            proxy_set_header Host \$http_host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_set_header Connection \"\";
            
            # WebSocket support
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \"upgrade\";
        }
    }

    server {
        listen 9090;
        server_name _;

        location / {
            proxy_pass http://minio-console;
            proxy_http_version 1.1;
            proxy_set_header Host \$http_host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection \"upgrade\";
        }
    }
}
EOF"

echo ""
echo "💾 Step 6: Setting up data directories..."
remote_exec "
sudo mkdir -p /data/minio{1,2,3}
sudo chown -R 1001:1001 /data/minio*
sudo chmod 755 /data/minio*
"

echo ""
echo "🐍 Step 7: Installing Python dependencies..."
remote_exec "
sudo apt-get install -y python3-pip
pip3 install boto3 zarr numpy opencv-python requests tqdm
"

echo ""
echo "⚙️ Step 8: Optimizing system for MinIO..."
remote_exec "
# Increase file descriptor limits
echo '* soft nofile 65536' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65536' | sudo tee -a /etc/security/limits.conf

# Optimize kernel parameters
echo 'net.core.rmem_max = 268435456' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 268435456' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 87380 268435456' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 268435456' | sudo tee -a /etc/sysctl.conf

# Apply kernel parameters
sudo sysctl -p

# Disable swap for better performance
sudo swapoff -a
"

echo ""
echo "🚀 Step 9: Starting services..."
remote_exec "
cd ~/miniodemo
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
"

echo ""
echo "⏳ Step 10: Waiting for services to be ready..."
sleep 30

echo ""
echo "🔧 Step 11: Initializing LakeFS..."
remote_exec "cd ~/miniodemo && chmod +x setup-lakefs.sh && ./setup-lakefs.sh"

echo ""
echo "🎯 Step 12: Creating quick start script..."
remote_exec "cat > ~/miniodemo/quick-start.sh << 'EOF'
#!/bin/bash
# Quick start script for MinIO + LakeFS demo

echo \"🚀 MinIO + LakeFS Demo Environment\"
echo \"=================================\"
echo \"\"
echo \"📊 System Status:\"
docker compose ps
echo \"\"
echo \"🌐 Access URLs:\"
echo \"  MinIO S3 API: http://$(curl -s ifconfig.me):80\"
echo \"  MinIO Console: http://$(curl -s ifconfig.me):9090\"
echo \"  LakeFS UI: http://$(curl -s ifconfig.me):8000\"
echo \"  Grafana: http://$(curl -s ifconfig.me):3000\"
echo \"\"
echo \"🔑 Credentials:\"
echo \"  MinIO: minioadmin / minioadmin123\"
echo \"  LakeFS: admin / admin123\"
echo \"  Grafana: admin / admin123\"
echo \"\"
echo \"📥 Download UMI data:\"
echo \"  python3 download_umi_data.py --dataset cup_arrangement_lab\"
echo \"\"
echo \"📊 Run benchmarks:\"
echo \"  python3 benchmark_performance.py --dataset cup_arrangement_lab --report results.txt\"
echo \"\"
EOF"

remote_exec "chmod +x ~/miniodemo/quick-start.sh"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Access your deployment at:"
echo "   MinIO Console: http://$REMOTE_HOST:9090"
echo "   LakeFS UI: http://$REMOTE_HOST:8000"
echo "   Grafana: http://$REMOTE_HOST:3000"
echo ""
echo "🔑 Default credentials:"
echo "   MinIO: minioadmin / minioadmin123"
echo "   LakeFS: admin / admin123"
echo "   Grafana: admin / admin123"
echo ""
echo "🚀 Next steps:"
echo "   1. SSH to your server: ssh -i $SSH_KEY $REMOTE_USER@$REMOTE_HOST"
echo "   2. Run quick start: cd miniodemo && ./quick-start.sh"
echo "   3. Download data: python3 download_umi_data.py --dataset cup_arrangement_lab"
echo "   4. Run benchmarks: python3 benchmark_performance.py"
echo ""

# Create local connection script
cat > connect-remote.sh << EOF
#!/bin/bash
echo "🔗 Connecting to remote MinIO + LakeFS deployment"
echo "Server: $REMOTE_HOST"
ssh -i "$SSH_KEY" -L 8000:localhost:8000 -L 9090:localhost:9090 -L 3000:localhost:3000 "$REMOTE_USER@$REMOTE_HOST"
EOF

chmod +x connect-remote.sh

echo "💻 Local access script created: ./connect-remote.sh"
echo "   Run this to tunnel remote services to your local machine"