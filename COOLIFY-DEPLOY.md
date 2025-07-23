# 🚀 Coolify Deployment Guide

Deploy your MinIO cluster with LakeFS and AIStor on Coolify in minutes!

## Prerequisites

- Coolify subscription and server setup
- Git repository with this code
- Domain name (optional, can use server IP)

## Quick Deploy

### 1. Create New Project in Coolify

1. **Login to Coolify Dashboard**
2. **Create New Project** → Name: `minio-robotics-cluster`
3. **Add Git Repository** → Connect this repository

### 2. Deploy Services

Coolify will auto-detect the `docker-compose.cloud.yml` file. Here's how to deploy each service:

#### A. Deploy the Full Stack

1. **Create New Resource** → **Docker Compose**
2. **Select Repository** → Choose your repo
3. **Docker Compose File**: `docker-compose.cloud.yml`
4. **Set Environment Variables**:

```env
# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your-secure-password

# LakeFS Configuration  
LAKEFS_SECRET_KEY=your-32-character-secret-key-here-1234
LAKEFS_USER=admin
LAKEFS_ACCESS_KEY=AKIAIOSFOLKFSSAMPLES
LAKEFS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYSAMPLEKEY

# AIStor Configuration
AISTOR_CACHE_SIZE=4GB
AISTOR_THRESHOLD=1MB

# Monitoring
GRAFANA_USER=admin  
GRAFANA_PASS=your-grafana-password

# Domain (update with your domain)
DOMAIN=your-domain.com
MINIO_SERVER_URL=https://s3.your-domain.com
```

5. **Deploy** → Click Deploy

### 3. Configure Domains (Optional)

Set up custom domains for clean access:

1. **S3 API**: `s3.your-domain.com` → Port 80
2. **MinIO Console**: `console.your-domain.com` → Port 9090  
3. **LakeFS**: `lakefs.your-domain.com` → Port 8000
4. **Grafana**: `grafana.your-domain.com` → Port 3000

### 4. Enable SSL

Coolify automatically handles SSL certificates with Let's Encrypt:

1. **Go to each service**
2. **Enable SSL/TLS**
3. **Force HTTPS redirect**

## Service URLs After Deployment

Replace `your-server.com` with your actual domain/IP:

| Service | URL | Credentials |
|---------|-----|-------------|
| MinIO S3 API | https://s3.your-server.com | minioadmin / your-password |
| MinIO Console | https://console.your-server.com | minioadmin / your-password |
| LakeFS | https://lakefs.your-server.com | admin / (setup required) |
| Grafana | https://grafana.your-server.com | admin / your-password |
| Prometheus | https://prometheus.your-server.com | No auth |

## Testing Your Deployment

### 1. Generate Sample Data

```bash
# Update endpoint to your domain
python3 download_umi_data.py --generate --upload --minio-endpoint s3.your-server.com
```

### 2. Run Performance Tests

```bash
# Test small file performance (robotics pose/gripper data)
python3 download_umi_data.py --benchmark small_file_performance --minio-endpoint s3.your-server.com

# Create experiment configurations
python3 download_umi_data.py --experiments --upload --minio-endpoint s3.your-server.com
```

### 3. Access Services

- **MinIO Console**: Manage buckets, users, policies
- **LakeFS**: Version control your robotics datasets
- **Grafana**: Monitor performance metrics
- **AIStor**: Automatic small file optimization

## Coolify-Specific Features

### Auto-Deploy on Git Push

1. **Enable Git Auto-Deploy** in Coolify
2. **Push changes** to your repository  
3. **Automatic redeploy** happens within minutes

### Health Checks

Coolify automatically monitors service health:
- **MinIO**: HTTP health endpoint
- **LakeFS**: API availability check
- **Grafana**: Dashboard accessibility
- **AIStor**: Custom health check

### Scaling

Scale services based on load:

1. **Go to Service Settings**
2. **Adjust Resource Limits**:
   - MinIO: 2-8 GB RAM per node
   - LakeFS: 1-4 GB RAM
   - AIStor: 512MB-2GB RAM
   - Grafana: 512MB-1GB RAM

### Backup Strategy

**Volumes to Backup**:
- `minio1-data`, `minio2-data`, `minio3-data` → Your robotics data
- `lakefs-data` → Data versioning metadata
- `grafana-data` → Dashboards and configurations
- `prometheus-data` → Metrics history

**Coolify Backup**:
1. **Enable Automated Backups** in project settings
2. **Set backup frequency** (daily recommended)
3. **Configure backup destination** (S3, FTP, etc.)

## Production Optimizations

### Security

```env
# Use strong passwords
MINIO_ROOT_PASSWORD=very-secure-password-here
LAKEFS_SECRET_KEY=random-32-character-string-for-encryption
GRAFANA_PASS=another-secure-password

# Disable public access if not needed
LAKEFS_STATS_ENABLED=false
```

### Performance

```env
# Increase cache size for larger datasets
AISTOR_CACHE_SIZE=8GB

# Adjust threshold for your file sizes
AISTOR_THRESHOLD=5MB  # For larger robotics files
```

### Monitoring

- **Set up alerts** in Grafana for disk usage, API latency
- **Configure log aggregation** in Coolify
- **Monitor AIStor cache hit rates** for optimization

## Troubleshooting

### Service Won't Start

1. **Check logs** in Coolify dashboard
2. **Verify environment variables** are set correctly
3. **Ensure sufficient resources** allocated

### Cannot Access Services

1. **Check domain configuration** in Coolify
2. **Verify SSL certificates** are generated
3. **Test with server IP** instead of domain

### Performance Issues

1. **Monitor resource usage** in Coolify
2. **Scale up services** if needed
3. **Check AIStor cache hit rates** in logs
4. **Optimize MinIO cluster** based on access patterns

## Cost Optimization

### Coolify Resource Settings

- **MinIO nodes**: 1-2 GB RAM each (3-6 GB total)
- **LakeFS**: 512MB-1GB RAM
- **AIStor**: 256-512MB RAM  
- **Nginx**: 128-256MB RAM
- **Total**: ~5-8 GB RAM for full stack

### Cloud Provider Recommendations

- **Hetzner**: €20-40/month for suitable server
- **DigitalOcean**: $40-80/month droplet
- **AWS/GCP**: Use spot instances for development

Perfect for testing robotics data workflows before scaling to production! 🤖