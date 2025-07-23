#!/bin/bash

# DigitalOcean MinIO Cluster Deployment Script
# Usage: ./deploy-digitalocean.sh

set -e

echo "🌊 DigitalOcean MinIO + LakeFS Deployment"
echo "========================================"
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "❌ DigitalOcean CLI (doctl) not found"
    echo "Install: https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Configuration
PROJECT_NAME="minio-cluster"
REGION="nyc3"
SIZE="s-2vcpu-4gb"  # $24/month
IMAGE="docker-20-04"
SSH_KEY_NAME="minio-key"

echo "📋 Configuration:"
echo "  Project: $PROJECT_NAME"
echo "  Region: $REGION"  
echo "  Size: $SIZE"
echo "  Image: $IMAGE"
echo ""

# Generate SSH key if it doesn't exist
if [ ! -f ~/.ssh/minio_rsa ]; then
    echo "🔑 Generating SSH key..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/minio_rsa -N "" -C "minio-cluster"
    
    # Add to DigitalOcean
    doctl compute ssh-key create "$SSH_KEY_NAME" --public-key "$(cat ~/.ssh/minio_rsa.pub)"
fi

echo "🚀 Creating DigitalOcean droplet..."

# Create droplet
DROPLET_ID=$(doctl compute droplet create $PROJECT_NAME \
    --region $REGION \
    --size $SIZE \
    --image $IMAGE \
    --ssh-keys $(doctl compute ssh-key list --format ID --no-header | head -1) \
    --enable-monitoring \
    --enable-ipv6 \
    --format ID --no-header)

echo "   Droplet ID: $DROPLET_ID"

# Wait for droplet to be ready
echo "⏳ Waiting for droplet to be ready..."
while [ "$(doctl compute droplet get $DROPLET_ID --format Status --no-header)" != "active" ]; do
    echo "   Status: $(doctl compute droplet get $DROPLET_ID --format Status --no-header)"
    sleep 10
done

# Get droplet IP
DROPLET_IP=$(doctl compute droplet get $DROPLET_ID --format PublicIPv4 --no-header)
echo "🌐 Droplet IP: $DROPLET_IP"

# Wait for SSH to be ready
echo "⏳ Waiting for SSH to be ready..."
while ! ssh -i ~/.ssh/minio_rsa -o ConnectTimeout=5 -o StrictHostKeyChecking=no root@$DROPLET_IP "echo 'SSH ready'" 2>/dev/null; do
    echo "   Waiting for SSH..."
    sleep 10
done

echo "📦 Setting up droplet..."

# Upload files
echo "📤 Uploading configuration files..."
scp -i ~/.ssh/minio_rsa -o StrictHostKeyChecking=no docker-compose.cloud.yml root@$DROPLET_IP:/root/docker-compose.yml
scp -i ~/.ssh/minio_rsa -o StrictHostKeyChecking=no nginx.conf root@$DROPLET_IP:/root/
scp -i ~/.ssh/minio_rsa -o StrictHostKeyChecking=no prometheus.yml root@$DROPLET_IP:/root/
scp -i ~/.ssh/minio_rsa -o StrictHostKeyChecking=no setup-lakefs.sh root@$DROPLET_IP:/root/
scp -i ~/.ssh/minio_rsa -o StrictHostKeyChecking=no requirements.txt root@$DROPLET_IP:/root/
scp -i ~/.ssh/minio_rsa -o StrictHostKeyChecking=no *.py root@$DROPLET_IP:/root/

# Setup environment
ssh -i ~/.ssh/minio_rsa -o StrictHostKeyChecking=no root@$DROPLET_IP << 'EOF'
# Create environment file
cat > .env << 'ENVEOF'
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=changeme123!
MINIO_SERVER_URL=http://localhost:9000
POSTGRES_PASSWORD=postgres123!
LAKEFS_SECRET_KEY=your-32-character-secret-key-1234
GRAFANA_PASSWORD=grafana123!
ENVEOF

# Create data directories
mkdir -p /mnt/{minio1-data,minio1-data2,minio2-data,minio2-data2,minio3-data,minio3-data2}
mkdir -p /mnt/{lakefs-data,postgres-data,grafana-data,prometheus-data}

# Set permissions
chmod 755 /mnt/minio*
chown -R 1001:1001 /mnt/minio*

# Update system
apt-get update -y
apt-get install -y python3-pip htop iotop

# Install Python dependencies
pip3 install -r requirements.txt

# System optimizations
echo '* soft nofile 65536' >> /etc/security/limits.conf
echo '* hard nofile 65536' >> /etc/security/limits.conf

# Kernel optimizations
echo 'net.core.rmem_max = 268435456' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 268435456' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_rmem = 4096 87380 268435456' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_wmem = 4096 65536 268435456' >> /etc/sysctl.conf
sysctl -p

# Start services
docker compose up -d

# Wait for services
sleep 30

# Setup LakeFS
chmod +x setup-lakefs.sh
./setup-lakefs.sh

echo "✅ Setup complete!"
EOF

# Create access script
cat > access-cluster.sh << EOFACCESS
#!/bin/bash
echo "🔗 Accessing MinIO cluster on DigitalOcean"
echo "IP: $DROPLET_IP"
echo ""
echo "🌐 Web interfaces:"
echo "  MinIO Console: http://$DROPLET_IP:9001"
echo "  LakeFS: http://$DROPLET_IP:8000"  
echo "  Grafana: http://$DROPLET_IP:3000"
echo ""
echo "🔑 Default credentials:"
echo "  MinIO: minioadmin / changeme123!"
echo "  LakeFS: admin / admin123"
echo "  Grafana: admin / grafana123!"
echo ""
echo "🖥️  SSH access:"
echo "ssh -i ~/.ssh/minio_rsa root@$DROPLET_IP"
EOFACCESS

chmod +x access-cluster.sh

echo ""
echo "✅ DigitalOcean deployment complete!"
echo ""
echo "🌐 Access your cluster:"
echo "  IP Address: $DROPLET_IP"
echo "  MinIO Console: http://$DROPLET_IP:9001"
echo "  LakeFS: http://$DROPLET_IP:8000"
echo "  Grafana: http://$DROPLET_IP:3000"
echo ""
echo "🔑 Credentials:"
echo "  MinIO: minioadmin / changeme123!"
echo "  LakeFS: admin / admin123"
echo "  Grafana: admin / grafana123!"
echo ""
echo "💻 Quick access: ./access-cluster.sh"
echo "🔧 SSH: ssh -i ~/.ssh/minio_rsa root@$DROPLET_IP"
echo ""
echo "💰 Monthly cost: ~$24 (single droplet)"
echo ""
echo "🚀 Next steps:"
echo "  1. Run: ./access-cluster.sh"
echo "  2. Test: python3 download_umi_data.py"
echo "  3. Benchmark: python3 benchmark_performance.py"