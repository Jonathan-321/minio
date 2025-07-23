# MinIO + AIStor + LakeFS Demo for UMI Dataset

A comprehensive demo environment for testing MinIO with AIStor and LakeFS using real Universal Manipulation Interface (UMI) datasets.

## 🚀 Quick Start

### Local Development
```bash
# Start the stack
docker compose up -d

# Wait for services, then initialize LakeFS
./setup-lakefs.sh

# Download real UMI data
python3 download_umi_data.py --dataset cup_arrangement_lab

# Run performance benchmarks
python3 benchmark_performance.py --report results.txt
```

### Remote Deployment
```bash
# Deploy to remote server
./deploy-remote.sh your-server.com ubuntu ~/.ssh/your-key

# Connect with local tunneling
./connect-remote.sh
```

## 📊 Services & Ports

| Service | Port | Description |
|---------|------|-------------|
| MinIO S3 API | 80 | S3-compatible API |
| MinIO Console | 9090 | Web management UI |
| LakeFS | 8000 | Git-like data versioning |
| Grafana | 3000 | Performance monitoring |
| Prometheus | 9091 | Metrics collection |

## 🔑 Default Credentials

- **MinIO**: `minioadmin` / `minioadmin123`
- **LakeFS**: `admin` / `admin123`
- **Grafana**: `admin` / `admin123`

## 📁 Architecture

```
MinIO Cluster (3 nodes) + AIStor
├── Nginx Load Balancer
├── LakeFS (Git-like versioning)
├── Grafana + Prometheus (Monitoring)
└── UMI Dataset Pipeline
```

## 🎯 Key Features

- **AIStor Integration**: Automatic small file optimization
- **Real UMI Data**: Cup arrangement, bimanual tasks
- **Performance Testing**: Latency, throughput, concurrent access
- **Monitoring**: Real-time metrics and dashboards
- **Remote Deployment**: Production-ready cloud setup

## 📈 Benchmark Results

The benchmark suite tests:
- **Sequential Access**: Video playback simulation
- **Random Access**: Data exploration patterns  
- **Concurrent Reads**: Multi-user scenarios
- **File Size Categories**: Small/medium/large file performance
- **LakeFS Operations**: Version control overhead

## 🔧 Customization

Edit `docker-compose.yml` to:
- Scale MinIO nodes
- Adjust memory limits
- Configure storage paths
- Enable/disable AIStor

## 📚 UMI Datasets Supported

- `cup_arrangement_lab` (305 demos)
- `cup_arrangement_wild` (1,447 demos) 
- `bimanual_dish_washing` (258 demos)
- `bimanual_cloth_folding` (249 demos)

## 🚨 Performance Notes

- AIStor automatically optimizes small files
- Large video files use MinIO's native performance
- 3-node cluster provides redundancy and scale
- Nginx load balancer distributes requests

## 🛠 Troubleshooting

```bash
# Check service status
docker compose ps

# View logs
docker compose logs minio1
docker compose logs lakefs

# Restart services
docker compose restart

# Reset everything
docker compose down -v
docker compose up -d
```# minio
