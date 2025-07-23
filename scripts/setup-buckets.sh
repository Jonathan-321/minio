#!/bin/bash

echo "🪣 Setting up MinIO buckets for UMI robotics data..."

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO cluster to be ready..."
sleep 15

# Configure aliases for all MinIO nodes
mc alias set minio1 http://minio1:9000 minioadmin minioadmin123
mc alias set minio2 http://minio2:9000 minioadmin minioadmin123
mc alias set minio3 http://minio3:9000 minioadmin minioadmin123

# Test connectivity
echo "🔍 Testing MinIO connectivity..."
mc admin info minio1

# Create buckets for different data types
echo "📦 Creating buckets..."

# Raw UMI data buckets
mc mb minio1/umi-raw --ignore-existing
mc mb minio1/umi-raw/video --ignore-existing
mc mb minio1/umi-raw/pose --ignore-existing
mc mb minio1/umi-raw/gripper --ignore-existing

# Processed data buckets
mc mb minio1/umi-processed --ignore-existing
mc mb minio1/umi-processed/compressed --ignore-existing
mc mb minio1/umi-processed/features --ignore-existing

# Experiment buckets
mc mb minio1/umi-experiments --ignore-existing
mc mb minio1/umi-experiments/benchmarks --ignore-existing
mc mb minio1/umi-experiments/results --ignore-existing

# LakeFS storage bucket
mc mb minio1/lakefs-storage --ignore-existing

# Set lifecycle policies for data management
echo "⚙️  Setting up lifecycle policies..."
cat > /tmp/lifecycle-raw.json << EOF
{
    "Rules": [
        {
            "ID": "DeleteOldRawData",
            "Status": "Enabled",
            "Expiration": {
                "Days": 90
            }
        }
    ]
}
EOF

cat > /tmp/lifecycle-experiments.json << EOF
{
    "Rules": [
        {
            "ID": "ArchiveExperiments",
            "Status": "Enabled",
            "Transition": {
                "Days": 30,
                "StorageClass": "STANDARD_IA"
            }
        }
    ]
}
EOF

mc ilm import minio1/umi-raw < /tmp/lifecycle-raw.json
mc ilm import minio1/umi-experiments < /tmp/lifecycle-experiments.json

# Set notification configurations for processing pipeline
echo "🔔 Setting up event notifications..."
mc event add minio1/umi-raw arn:minio:sqs::_:webhook --event put --suffix .mp4
mc event add minio1/umi-raw arn:minio:sqs::_:webhook --event put --suffix .json

# Create versioning for important buckets
echo "📋 Enabling versioning..."
mc version enable minio1/umi-processed
mc version enable minio1/umi-experiments

echo "✅ Bucket setup complete!"
echo ""
echo "📊 Bucket Summary:"
mc ls minio1/
echo ""
echo "💾 Storage Info:"
mc admin info minio1