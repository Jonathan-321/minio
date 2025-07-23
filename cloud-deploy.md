# ☁️ Cloud Deployment Guide

Deploy your MinIO cluster with LakeFS and AIStor to any cloud server or use Coolify for easy management.

## 🚀 Quick Start Options

### Option 1: Coolify (Recommended - Easiest)

Perfect if you have a Coolify subscription! See [COOLIFY-DEPLOY.md](COOLIFY-DEPLOY.md) for detailed instructions.

**Quick Steps:**
1. Push code to Git repository
2. Create new Docker Compose project in Coolify
3. Set environment variables
4. Deploy with one click!

### Option 2: Any Cloud Server

Deploy to DigitalOcean, AWS, GCP, Hetzner, or any VPS.

## 🖥️ Cloud Server Deployment

### Prerequisites

- Ubuntu 20.04+ server (2+ GB RAM, 20+ GB storage)
- SSH access with key authentication
- Domain name (optional, can use IP)

### 1. Automated Deployment

```bash
# Deploy to your server
./deploy-cloud.sh ubuntu your-server.com ~/.ssh/your-key

# Example with DigitalOcean droplet
./deploy-cloud.sh root 165.22.123.45 ~/.ssh/do_key

# Example with AWS EC2
./deploy-cloud.sh ubuntu ec2-54-123-45-67.compute-1.amazonaws.com ~/.ssh/aws-key.pem
```

The script will:
- ✅ Test SSH connection
- ✅ Upload all project files
- ✅ Install Docker & Docker Compose
- ✅ Configure environment variables
- ✅ Deploy the full stack
- ✅ Show service URLs and credentials

### 2. Manual Deployment

If you prefer manual control:

```bash
# 1. Upload files to server
rsync -avz --progress -e "ssh -i ~/.ssh/your-key" . user@server:~/miniodemo/

# 2. SSH to server
ssh -i ~/.ssh/your-key user@server

# 3. Install Docker (if needed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 4. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. Configure environment
cd ~/miniodemo
cp .env.cloud .env
# Edit .env with your settings

# 6. Deploy
docker-compose -f docker-compose.cloud.yml up -d
```

## 🌐 Service Access

After deployment, access your services at:

| Service | URL | Default Port |
|---------|-----|--------------|
| MinIO S3 API | `http://your-server:80` | 80 |
| MinIO Console | `http://your-server:9090` | 9090 |
| LakeFS | `http://your-server:8000` | 8000 |
| Grafana | `http://your-server:3000` | 3000 |
| Prometheus | `http://your-server:9090` | 9090 |

### Default Credentials

- **MinIO**: `minioadmin` / `minioadmin123`
- **LakeFS**: `admin` / (setup required on first access)
- **Grafana**: `admin` / `admin123`

## ⚙️ Configuration

### Environment Variables

Edit `.env` file on your server:

```env
# MinIO - Use strong passwords in production!
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your-secure-password-here

# LakeFS - Generate a secure 32-character key
LAKEFS_SECRET_KEY=your-32-character-secret-key-here

# AIStor Optimization
AISTOR_CACHE_SIZE=4GB    # Increase for more caching
AISTOR_THRESHOLD=1MB     # Files smaller than this get cached

# Monitoring
GRAFANA_USER=admin
GRAFANA_PASS=your-grafana-password

# Domain (optional)
DOMAIN=your-domain.com
MINIO_SERVER_URL=https://s3.your-domain.com
```

### Custom Domain Setup

1. **Point DNS** to your server IP
2. **Update nginx config** for your domain
3. **Add SSL certificate** (Let's Encrypt recommended)

```bash
# Install certbot for SSL
sudo apt install snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d s3.your-domain.com
```

## 🧪 Testing Your Deployment

### 1. Health Check

```bash
# Check all services are running
curl http://your-server/minio/health/live
curl http://your-server:8000/api/v1/config
curl http://your-server:3000/api/health
```

### 2. Generate Test Data

```bash
# From your local machine or server
pip install minio

# Generate and upload robotics data
python3 download_umi_data.py --generate --upload --minio-endpoint your-server:80

# Run performance benchmarks
python3 download_umi_data.py --benchmark small_file_performance --minio-endpoint your-server:80
```

### 3. Access Services

- **MinIO Console**: Create buckets, manage users
- **LakeFS**: Set up repositories for data versioning  
- **Grafana**: View performance dashboards
- **AIStor**: Monitor cache performance in logs

## 📊 Monitoring & Maintenance

### View Logs

```bash
# SSH to server
ssh -i ~/.ssh/your-key user@server
cd ~/miniodemo

# View service logs
docker-compose -f docker-compose.cloud.yml logs -f minio1
docker-compose -f docker-compose.cloud.yml logs -f lakefs
docker-compose -f docker-compose.cloud.yml logs -f aistor
```

### Performance Monitoring

- **Grafana Dashboards**: `http://your-server:3000`
  - MinIO cluster metrics
  - Storage usage and performance
  - AIStor cache hit rates
  - System resource usage

- **Prometheus Metrics**: `http://your-server:9090`
  - Raw metrics for custom queries
  - Service health status
  - Alert configurations

### Backup Strategy

**Important Data Locations:**
```bash
# MinIO data (your robotics datasets)
docker volume ls | grep minio.*-data

# LakeFS metadata (version control)
docker volume ls | grep lakefs-data

# Grafana dashboards
docker volume ls | grep grafana-data
```

**Backup Commands:**
```bash
# Backup volumes to tar files
docker run --rm -v miniodemo_minio1-data:/data -v $(pwd):/backup alpine tar czf /backup/minio1-backup.tar.gz -C /data .
docker run --rm -v miniodemo_lakefs-data:/data -v $(pwd):/backup alpine tar czf /backup/lakefs-backup.tar.gz -C /data .
```

## 🔧 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check container logs
docker-compose -f docker-compose.cloud.yml logs [service-name]

# Restart stack
docker-compose -f docker-compose.cloud.yml down
docker-compose -f docker-compose.cloud.yml up -d
```

**Can't access services:**
```bash
# Check if ports are open
sudo ufw status
sudo ufw allow 80,8000,9090,3000/tcp

# Check if services are listening
netstat -tlnp | grep -E ':(80|8000|9090|3000)'
```

**Performance issues:**
```bash
# Check resource usage
docker stats

# Scale MinIO if needed (edit docker-compose.cloud.yml)
# Add more nodes or increase memory limits

# Monitor AIStor cache efficiency
docker-compose -f docker-compose.cloud.yml logs aistor | grep "Cache"
```

### Resource Requirements

**Minimum (Testing):**
- 2 GB RAM
- 2 CPU cores  
- 20 GB storage

**Recommended (Production):**
- 8 GB RAM
- 4 CPU cores
- 100+ GB SSD storage

**Cloud Provider Costs:**
- **DigitalOcean**: $24-48/month
- **AWS EC2**: $30-60/month  
- **Hetzner**: €15-30/month
- **Google Cloud**: $25-50/month

## 🚀 Production Optimizations

### Security Hardening

```bash
# Change default passwords
nano .env  # Update all passwords

# Enable firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80,443,8000,9090,3000/tcp

# Disable password authentication
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart ssh
```

### SSL/HTTPS Setup

```bash
# Install nginx for SSL termination
sudo apt install nginx certbot python3-certbot-nginx

# Get SSL certificates
sudo certbot --nginx -d your-domain.com

# Update nginx config for MinIO
sudo nano /etc/nginx/sites-available/minio
```

### Scaling

- **Add more MinIO nodes** for increased storage/performance
- **Increase AIStor cache size** for better small file performance  
- **Use cloud load balancers** for high availability
- **Set up monitoring alerts** for proactive maintenance

Perfect for production robotics data workloads! 🤖🚀