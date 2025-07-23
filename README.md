# MinIO Cluster with LakeFS and AIStor for Robotics Data

A complete Docker Compose setup for testing robotics data storage and processing with MinIO distributed storage, LakeFS data versioning, and AIStor small file optimization.

## Quick Start

1. **Start Docker Desktop** (if not already running)
   ```bash
   # Install Docker if needed
   ./install-docker.sh
   ```

2. **Deploy the local stack**
   ```bash
   chmod +x deploy-local.sh
   ./deploy-local.sh
   ```

3. **Generate and upload sample UMI data**
   ```bash
   pip install minio
   python3 download_umi_data.py --generate --upload
   ```

## Architecture

### Components
- **MinIO Cluster**: 3-node distributed storage cluster
- **LakeFS**: Data versioning and branching for ML workflows  
- **AIStor**: Placeholder service for small file optimization
- **MC Setup**: Automated bucket creation and configuration

### Storage Layout
```
umi-raw/
├── pose/           # Joint angles, end-effector positions
├── gripper/        # Gripper states and force data
└── video/          # Camera feeds and visual data

umi-processed/
├── compressed/     # Compressed datasets
└── features/       # Extracted features

umi-experiments/
├── benchmarks/     # Performance test results
└── results/        # Experiment outputs
```

## Data Generation and Testing

### Generate Sample Data
```bash
# Generate robotics data with different sizes
python3 download_umi_data.py --generate

# Upload to MinIO cluster
python3 download_umi_data.py --generate --upload

# Create experiment configurations
python3 download_umi_data.py --experiments --upload
```

### Run Performance Tests
```bash
# Test small file performance (pose/gripper data)
python3 download_umi_data.py --benchmark small_file_performance

# Custom endpoint
python3 download_umi_data.py --benchmark small_file_performance --minio-endpoint localhost:9002
```

## Service Access

| Service | URL | Credentials |
|---------|-----|-------------|
| MinIO Console 1 | http://localhost:9091 | minioadmin / minioadmin123 |
| MinIO Console 2 | http://localhost:9092 | minioadmin / minioadmin123 |
| MinIO Console 3 | http://localhost:9093 | minioadmin / minioadmin123 |
| LakeFS UI | http://localhost:8000 | Setup on first access |

### MinIO API Endpoints
- Node 1: `http://localhost:9001`
- Node 2: `http://localhost:9002`  
- Node 3: `http://localhost:9003`

## AIStor Optimization

The AIStor sidecar optimizes small file performance for robotics workloads:

- **Caches files < 1MB** (pose data, gripper states, configs)
- **Monitors access patterns** and prefetches frequently used data
- **Provides metrics** on cache hit rates and performance gains

```bash
# View AIStor logs
docker-compose -f docker-compose.local.yml logs -f aistor

# AIStor cache is mounted at ./aistor/cache/
ls -la aistor/cache/
```

## Experiment Workflows

### 1. Small File Performance
Tests pose and gripper data read/write performance:
```bash
python3 download_umi_data.py --benchmark small_file_performance
```

### 2. Large File Streaming  
Tests video data streaming (when available):
```bash
# TODO: Implement video streaming benchmarks
```

### 3. Mixed Workload
Tests concurrent robotics data operations:
```bash  
# TODO: Implement mixed workload benchmarks
```

## LakeFS Integration

1. **Initialize LakeFS** (first time only):
   ```bash
   curl -X POST http://localhost:8000/api/v1/setup \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"password"}'
   ```

2. **Create repository**:
   ```bash
   # Via LakeFS UI at http://localhost:8000
   # Repository name: robotics-data
   # Storage namespace: s3://lakefs-storage
   ```

3. **Version your data**:
   ```bash
   # Use LakeFS CLI or API to create branches, commits, merges
   # Perfect for ML experiment tracking
   ```

## Cloud Deployment

This setup is designed for easy cloud deployment with minimal changes:

1. **Update endpoints** in `docker-compose.cloud.yml`
2. **Configure persistent volumes** for production
3. **Set up load balancers** for MinIO endpoints
4. **Enable TLS** for secure access

## File Structure

```
miniodemo/
├── docker-compose.local.yml    # Local development stack
├── deploy-local.sh            # Local deployment script
├── download_umi_data.py       # Data generation and testing
├── scripts/
│   └── setup-buckets.sh      # MinIO bucket initialization
├── aistor/
│   └── optimizer.py          # AIStor optimization logic
└── data/                     # Generated data directory
    └── umi/
        ├── pose_data.json
        ├── gripper_data.json
        └── experiments/
```

## Troubleshooting

### Docker Issues
```bash
# Restart Docker Desktop
# Check Docker is running
docker info

# View container logs
docker-compose -f docker-compose.local.yml logs [service-name]
```

### MinIO Issues
```bash
# Check MinIO health
curl http://localhost:9001/minio/health/live

# Reset MinIO data
docker-compose -f docker-compose.local.yml down -v
```

### Port Conflicts
If ports are in use, update the port mappings in `docker-compose.local.yml`:
```yaml
ports:
  - "9001:9000"  # Change 9001 to available port
```

## Next Steps

1. **Add real UMI datasets** by implementing actual download from https://umi-data.github.io/
2. **Implement video streaming** benchmarks for large file testing
3. **Add monitoring** with Prometheus/Grafana
4. **Cloud deployment** scripts for AWS/GCP/Azure
5. **ML pipeline integration** with popular robotics frameworks