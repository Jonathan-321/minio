#!/bin/bash

# Deploy to your DigitalOcean server
# Usage: ./deploy-to-server.sh YOUR_SERVER_IP

SERVER_IP=$1

if [ -z "$SERVER_IP" ]; then
    echo "❌ Please provide server IP"
    echo "Usage: ./deploy-to-server.sh YOUR_SERVER_IP"
    exit 1
fi

echo "🚀 Deploying MinIO cluster to $SERVER_IP"
echo "========================================="

# Upload files to server
echo "📤 Uploading files..."
scp -o StrictHostKeyChecking=no docker-compose.cloud.yml root@$SERVER_IP:/root/docker-compose.yml
scp -o StrictHostKeyChecking=no nginx.conf root@$SERVER_IP:/root/
scp -o StrictHostKeyChecking=no prometheus.yml root@$SERVER_IP:/root/
scp -o StrictHostKeyChecking=no setup-lakefs.sh root@$SERVER_IP:/root/
scp -o StrictHostKeyChecking=no requirements.txt root@$SERVER_IP:/root/
scp -o StrictHostKeyChecking=no *.py root@$SERVER_IP:/root/

# Deploy on server
echo "🔧 Setting up server..."
ssh -o StrictHostKeyChecking=no root@$SERVER_IP << 'EOF'

echo "📦 Updating system..."
apt-get update -y
apt-get install -y python3-pip htop iotop docker.io docker-compose-plugin

echo "🐳 Starting Docker..."
systemctl enable docker
systemctl start docker

echo "📁 Creating directories..."
mkdir -p /mnt/{minio1-data,minio1-data2,minio2-data,minio2-data2,minio3-data,minio3-data2}
mkdir -p /mnt/{lakefs-data,postgres-data,grafana-data,prometheus-data}
chmod 755 /mnt/minio*
chown -R 1001:1001 /mnt/minio*

echo "🔑 Creating environment..."
cat > .env << 'ENVEOF'
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=changeme123!
MINIO_SERVER_URL=http://localhost:9000
POSTGRES_PASSWORD=postgres123!
LAKEFS_SECRET_KEY=your-32-character-secret-key-1234
GRAFANA_PASSWORD=grafana123!
ENVEOF

echo "🐍 Installing Python packages..."
pip3 install boto3 zarr numpy opencv-python requests tqdm matplotlib pandas

echo "🚀 Starting MinIO cluster..."
docker compose up -d

echo "⏳ Waiting for services..."
sleep 45

echo "🏞️ Setting up LakeFS..."
chmod +x setup-lakefs.sh
./setup-lakefs.sh

echo "✅ Deployment complete!"
echo ""
echo "🌐 Access URLs:"
echo "  MinIO Console: http://$(curl -s ifconfig.me):9001"
echo "  LakeFS: http://$(curl -s ifconfig.me):8000"
echo "  Grafana: http://$(curl -s ifconfig.me):3000"
echo ""
echo "🔑 Credentials:"
echo "  MinIO: minioadmin / changeme123!"
echo "  LakeFS: admin / admin123"
echo "  Grafana: admin / grafana123!"

EOF

echo ""
echo "✅ Deployment successful!"
echo ""
echo "🌐 Your MinIO cluster is ready at:"
echo "  MinIO Console: http://$SERVER_IP:9001"
echo "  LakeFS: http://$SERVER_IP:8000"
echo "  Grafana: http://$SERVER_IP:3000"
echo ""
echo "🧪 Test it now:"
echo "  python3 quick-test.py --endpoint http://$SERVER_IP:9000 --lakefs http://$SERVER_IP:8000"
echo ""
echo "🔧 SSH to server:"
echo "  ssh root@$SERVER_IP"