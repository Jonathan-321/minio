# Manual DigitalOcean Deployment Guide

## Option 1: Wait for CLI install (recommended)
The `brew install doctl` is running in background. Once complete, run:
```bash
./deploy-digitalocean.sh
```

## Option 2: Manual deployment (faster start)

### Step 1: Create DigitalOcean Account
1. Go to https://digitalocean.com
2. Create account (get $200 credit with referral)

### Step 2: Create Droplet
1. Click "Create" → "Droplets"
2. **Image**: Ubuntu 22.04 LTS
3. **Size**: Basic plan, 4GB RAM, 2 vCPUs ($24/month)
4. **Region**: New York 3 (or closest to you)
5. **Authentication**: SSH Key (generate if needed)
6. **Hostname**: minio-cluster
7. Click "Create Droplet"

### Step 3: Connect and Deploy
Once droplet is ready, get its IP address and run:

```bash
# Replace YOUR_DROPLET_IP with actual IP
./deploy-remote.sh YOUR_DROPLET_IP ubuntu ~/.ssh/your_key

# Or manual SSH:
ssh root@YOUR_DROPLET_IP

# Then on the server:
git clone https://github.com/your-repo/miniodemo.git
cd miniodemo
docker compose -f docker-compose.cloud.yml up -d
```

## Testing the Deployment

### Quick Test Script
```bash
# Test MinIO connection
python3 -c "
import boto3
s3 = boto3.client('s3', 
    endpoint_url='http://YOUR_IP:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='changeme123!')
print('✅ MinIO connection successful')
print('Buckets:', s3.list_buckets())
"

# Download and test with real data
python3 download_umi_data.py --dataset cup_arrangement_lab
python3 benchmark_performance.py --dataset cup_arrangement_lab
```

### Access URLs
- **MinIO Console**: http://YOUR_IP:9001
- **LakeFS**: http://YOUR_IP:8000  
- **Grafana**: http://YOUR_IP:3000

### Default Credentials
- **MinIO**: minioadmin / changeme123!
- **LakeFS**: admin / admin123
- **Grafana**: admin / grafana123!

## Expected Performance Gains
- **Upload speed**: 50-200 MB/s (vs 5-20 MB/s locally)
- **Download speed**: 100-500 MB/s (vs 10-50 MB/s locally)
- **IOPS**: 3000+ (vs 100-500 locally)
- **Latency**: <1ms (vs 10-50ms locally)