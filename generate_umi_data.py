#!/usr/bin/env python3
"""
UMI Data Generator for MinIO + LakeFS Performance Testing

Simulates realistic UMI dataset patterns:
- Video streams (224x224x3 at 60Hz)
- Pose data (small JSON files)
- Gripper states (small binary files)
- Action sequences (timestamped data)
"""

import os
import json
import time
import numpy as np
import tempfile
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any
import concurrent.futures
import boto3
from botocore.config import Config
import cv2

@dataclass
class UMIDataConfig:
    """Configuration for UMI data generation"""
    num_demonstrations: int = 100
    frames_per_demo: int = 1800  # 30 seconds at 60Hz
    video_resolution: tuple = (224, 224, 3)
    video_fps: int = 60
    pose_frequency: int = 60  # Hz
    gripper_frequency: int = 60  # Hz
    tasks: List[str] = None
    
    def __post_init__(self):
        if self.tasks is None:
            self.tasks = [
                "pick_cube", "stack_blocks", "pour_water", "fold_cloth",
                "open_door", "press_button", "slide_drawer", "flip_switch"
            ]

class UMIDataGenerator:
    def __init__(self, config: UMIDataConfig, s3_endpoint: str = "http://localhost:80"):
        self.config = config
        self.s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin123',
            config=Config(
                region_name='us-east-1',
                retries={'max_attempts': 3},
                max_pool_connections=50
            )
        )
        self.bucket_name = 'umi-data'
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            print(f"✅ Created bucket: {self.bucket_name}")
    
    def generate_video_frame(self, demo_id: int, frame_id: int, task: str) -> np.ndarray:
        """Generate a synthetic video frame"""
        frame = np.random.randint(0, 255, self.config.video_resolution, dtype=np.uint8)
        
        # Add some structured content to make it realistic
        # Simulate robot arm in frame
        center = (112, 112)
        radius = 20 + int(10 * np.sin(frame_id * 0.1))
        cv2.circle(frame, center, radius, (0, 255, 0), 2)
        
        # Add task-specific visual cues
        task_color = hash(task) % 255
        cv2.putText(frame, f"{task[:8]}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (task_color, task_color, 255), 1)
        
        return frame
    
    def generate_pose_data(self, demo_id: int, frame_id: int, timestamp: float) -> Dict[str, Any]:
        """Generate robot pose data"""
        return {
            "timestamp": timestamp,
            "demo_id": demo_id,
            "frame_id": frame_id,
            "end_effector_pose": {
                "position": [
                    0.5 + 0.1 * np.sin(timestamp),
                    0.3 + 0.1 * np.cos(timestamp),
                    0.2 + 0.05 * np.sin(timestamp * 2)
                ],
                "orientation": [0.0, 0.0, 0.0, 1.0]  # quaternion
            },
            "joint_angles": np.random.normal(0, 0.1, 7).tolist(),
            "joint_velocities": np.random.normal(0, 0.01, 7).tolist()
        }
    
    def generate_gripper_data(self, demo_id: int, frame_id: int, timestamp: float) -> Dict[str, Any]:
        """Generate gripper state data"""
        return {
            "timestamp": timestamp,
            "demo_id": demo_id,
            "frame_id": frame_id,
            "gripper_state": np.random.choice(['open', 'closed', 'moving']),
            "gripper_position": np.random.uniform(0, 1),
            "gripper_force": np.random.uniform(0, 10),
            "contact_detected": np.random.choice([True, False])
        }
    
    def upload_video_chunk(self, demo_id: int, task: str, chunk_start: int, chunk_size: int):
        """Upload a chunk of video frames as a single file"""
        frames = []
        for i in range(chunk_start, min(chunk_start + chunk_size, self.config.frames_per_demo)):
            frame = self.generate_video_frame(demo_id, i, task)
            frames.append(frame)
        
        # Create video chunk
        video_array = np.stack(frames)
        
        # Upload as compressed numpy array
        with tempfile.NamedTemporaryFile(suffix='.npz') as tmp_file:
            np.savez_compressed(tmp_file.name, frames=video_array)
            tmp_file.seek(0)
            
            key = f"demonstrations/{task}/demo_{demo_id:04d}/video/chunk_{chunk_start:06d}_{chunk_start+chunk_size:06d}.npz"
            self.s3_client.upload_file(tmp_file.name, self.bucket_name, key)
            
        return len(frames)
    
    def upload_sensor_data(self, demo_id: int, task: str, frame_data: List[tuple]):
        """Upload pose and gripper data in batches"""
        pose_batch = []
        gripper_batch = []
        
        for frame_id, timestamp in frame_data:
            pose_batch.append(self.generate_pose_data(demo_id, frame_id, timestamp))
            gripper_batch.append(self.generate_gripper_data(demo_id, frame_id, timestamp))
        
        # Upload pose data
        pose_key = f"demonstrations/{task}/demo_{demo_id:04d}/poses/poses_{frame_data[0][0]:06d}_{frame_data[-1][0]:06d}.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=pose_key,
            Body=json.dumps(pose_batch, indent=2)
        )
        
        # Upload gripper data
        gripper_key = f"demonstrations/{task}/demo_{demo_id:04d}/gripper/gripper_{frame_data[0][0]:06d}_{frame_data[-1][0]:06d}.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=gripper_key,
            Body=json.dumps(gripper_batch, indent=2)
        )
        
        return len(pose_batch)
    
    def generate_demonstration(self, demo_id: int, task: str) -> Dict[str, Any]:
        """Generate a complete demonstration"""
        start_time = time.time()
        demo_start_timestamp = datetime.now().timestamp()
        
        print(f"🤖 Generating demo {demo_id} for task '{task}'...")
        
        # Generate metadata
        metadata = {
            "demo_id": demo_id,
            "task": task,
            "start_timestamp": demo_start_timestamp,
            "duration": self.config.frames_per_demo / self.config.video_fps,
            "total_frames": self.config.frames_per_demo,
            "video_resolution": self.config.video_resolution,
            "fps": self.config.video_fps,
            "success": np.random.choice([True, False], p=[0.8, 0.2])  # 80% success rate
        }
        
        # Upload metadata
        metadata_key = f"demonstrations/{task}/demo_{demo_id:04d}/metadata.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2)
        )
        
        # Process data in chunks to simulate streaming
        chunk_size = 300  # 5 seconds of video at 60fps
        sensor_batch_size = 60  # 1 second of sensor data
        
        upload_stats = {
            "video_chunks": 0,
            "sensor_batches": 0,
            "total_frames": 0
        }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            
            # Upload video in chunks
            for chunk_start in range(0, self.config.frames_per_demo, chunk_size):
                future = executor.submit(self.upload_video_chunk, demo_id, task, chunk_start, chunk_size)
                futures.append(('video', future))
            
            # Upload sensor data in batches
            for batch_start in range(0, self.config.frames_per_demo, sensor_batch_size):
                batch_end = min(batch_start + sensor_batch_size, self.config.frames_per_demo)
                frame_data = [
                    (i, demo_start_timestamp + i / self.config.video_fps) 
                    for i in range(batch_start, batch_end)
                ]
                future = executor.submit(self.upload_sensor_data, demo_id, task, frame_data)
                futures.append(('sensor', future))
            
            # Collect results
            for data_type, future in futures:
                try:
                    result = future.result(timeout=30)
                    if data_type == 'video':
                        upload_stats["video_chunks"] += 1
                        upload_stats["total_frames"] += result
                    else:
                        upload_stats["sensor_batches"] += 1
                except Exception as e:
                    print(f"❌ Upload failed for {data_type}: {e}")
        
        generation_time = time.time() - start_time
        print(f"✅ Demo {demo_id} completed in {generation_time:.2f}s - "
              f"{upload_stats['video_chunks']} video chunks, {upload_stats['sensor_batches']} sensor batches")
        
        return {
            "demo_id": demo_id,
            "task": task,
            "generation_time": generation_time,
            "upload_stats": upload_stats
        }
    
    def generate_dataset(self) -> Dict[str, Any]:
        """Generate the complete UMI dataset"""
        print(f"🚀 Starting UMI dataset generation:")
        print(f"   - {self.config.num_demonstrations} demonstrations")
        print(f"   - {len(self.config.tasks)} tasks")
        print(f"   - {self.config.frames_per_demo} frames per demo")
        print(f"   - {self.config.video_fps} fps")
        print()
        
        start_time = time.time()
        results = []
        
        # Distribute demonstrations across tasks
        demos_per_task = self.config.num_demonstrations // len(self.config.tasks)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            demo_id = 0
            
            for task in self.config.tasks:
                for _ in range(demos_per_task):
                    future = executor.submit(self.generate_demonstration, demo_id, task)
                    futures.append(future)
                    demo_id += 1
            
            # Process remaining demos
            remaining = self.config.num_demonstrations - demo_id
            for i in range(remaining):
                task = self.config.tasks[i % len(self.config.tasks)]
                future = executor.submit(self.generate_demonstration, demo_id, task)
                futures.append(future)
                demo_id += 1
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=60)
                    results.append(result)
                except Exception as e:
                    print(f"❌ Demo generation failed: {e}")
        
        total_time = time.time() - start_time
        
        # Generate summary
        summary = {
            "total_demonstrations": len(results),
            "total_time": total_time,
            "avg_time_per_demo": total_time / len(results) if results else 0,
            "tasks": self.config.tasks,
            "config": {
                "frames_per_demo": self.config.frames_per_demo,
                "video_resolution": self.config.video_resolution,
                "fps": self.config.video_fps
            },
            "estimated_data_size_gb": self._estimate_data_size(),
            "generation_timestamp": datetime.now().isoformat()
        }
        
        # Upload summary
        summary_key = "dataset_summary.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=summary_key,
            Body=json.dumps(summary, indent=2)
        )
        
        print(f"\n🎉 Dataset generation complete!")
        print(f"   - Generated: {len(results)} demonstrations")
        print(f"   - Total time: {total_time:.2f} seconds")
        print(f"   - Avg per demo: {summary['avg_time_per_demo']:.2f} seconds")
        print(f"   - Estimated size: {summary['estimated_data_size_gb']:.2f} GB")
        
        return summary
    
    def _estimate_data_size(self) -> float:
        """Estimate total dataset size in GB"""
        # Video: frames * resolution * 3 bytes (uint8) per demo
        video_size_per_demo = self.config.frames_per_demo * np.prod(self.config.video_resolution)
        
        # Sensor data: ~1KB per frame (JSON)
        sensor_size_per_demo = self.config.frames_per_demo * 1024 * 2  # pose + gripper
        
        total_size_bytes = self.config.num_demonstrations * (video_size_per_demo + sensor_size_per_demo)
        
        # Account for compression (~50% for video, ~80% for JSON)
        compressed_size = video_size_per_demo * 0.5 + sensor_size_per_demo * 0.8
        total_compressed = self.config.num_demonstrations * compressed_size
        
        return total_compressed / (1024**3)  # Convert to GB

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate UMI dataset for testing')
    parser.add_argument('--demos', type=int, default=10, help='Number of demonstrations')
    parser.add_argument('--frames', type=int, default=300, help='Frames per demonstration')
    parser.add_argument('--endpoint', default='http://localhost:80', help='S3 endpoint')
    parser.add_argument('--quick', action='store_true', help='Quick test with minimal data')
    
    args = parser.parse_args()
    
    if args.quick:
        config = UMIDataConfig(
            num_demonstrations=2,
            frames_per_demo=60,  # 1 second of video
            tasks=["pick_cube", "stack_blocks"]
        )
    else:
        config = UMIDataConfig(
            num_demonstrations=args.demos,
            frames_per_demo=args.frames
        )
    
    generator = UMIDataGenerator(config, args.endpoint)
    summary = generator.generate_dataset()
    
    print(f"\n📊 Generation Summary:")
    print(f"   - Bucket: {generator.bucket_name}")
    print(f"   - Endpoint: {args.endpoint}")
    print(f"   - Total size: {summary['estimated_data_size_gb']:.2f} GB")

if __name__ == "__main__":
    main()