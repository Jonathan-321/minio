#!/usr/bin/env python3
"""
AIStor Placeholder - Small File Optimization for Robotics Data
Optimizes storage and retrieval of small files (pose data, gripper states)
while maintaining efficient access to large files (video streams).
"""

import os
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class FileMetadata:
    """Metadata for cached files"""
    file_path: str
    size: int
    hash: str
    access_count: int
    last_access: float
    cache_location: Optional[str] = None

class AIStor:
    """Placeholder AIStor implementation for small file optimization"""
    
    def __init__(self):
        self.cache_dir = Path("/cache")
        self.small_files_dir = self.cache_dir / "small-files"
        self.metadata_dir = self.cache_dir / "metadata" 
        self.temp_dir = self.cache_dir / "temp"
        
        # Configuration
        self.small_file_threshold = int(os.getenv("SMALL_FILE_THRESHOLD", "1048576"))  # 1MB
        self.cache_size_limit = self._parse_size(os.getenv("CACHE_SIZE", "1GB"))
        
        # Runtime state
        self.metadata_cache: Dict[str, FileMetadata] = {}
        self.current_cache_size = 0
        
        self._initialize_cache()
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '1GB' to bytes"""
        size_str = size_str.upper()
        multipliers = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                return int(size_str[:-len(suffix)]) * multiplier
        return int(size_str)
    
    def _initialize_cache(self):
        """Initialize cache directories and load metadata"""
        for dir_path in [self.small_files_dir, self.metadata_dir, self.temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing metadata
        metadata_file = self.metadata_dir / "cache_metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                data = json.load(f)
                self.metadata_cache = {
                    k: FileMetadata(**v) for k, v in data.items()
                }
        
        print(f"🤖 AIStor initialized:")
        print(f"   Cache directory: {self.cache_dir}")
        print(f"   Small file threshold: {self.small_file_threshold / 1024 / 1024:.1f}MB")
        print(f"   Cache size limit: {self.cache_size_limit / 1024 / 1024 / 1024:.1f}GB")
    
    def should_cache(self, file_path: str, file_size: int) -> bool:
        """Determine if file should be cached based on size and type"""
        if file_size > self.small_file_threshold:
            return False
        
        # Cache pose data, gripper states, small configs
        robotics_extensions = {'.json', '.yaml', '.yml', '.csv', '.txt', '.pkl'}
        path = Path(file_path)
        
        return path.suffix.lower() in robotics_extensions
    
    def cache_file(self, file_path: str, file_data: bytes) -> str:
        """Cache a small file and return cache location"""
        file_hash = hashlib.sha256(file_data).hexdigest()[:16]
        cache_path = self.small_files_dir / f"{file_hash}_{Path(file_path).name}"
        
        # Write to cache
        with open(cache_path, 'wb') as f:
            f.write(file_data)
        
        # Update metadata
        metadata = FileMetadata(
            file_path=file_path,
            size=len(file_data),
            hash=file_hash,
            access_count=1,
            last_access=time.time(),
            cache_location=str(cache_path)
        )
        
        self.metadata_cache[file_path] = metadata
        self.current_cache_size += len(file_data)
        
        # Check cache size limits
        self._enforce_cache_limits()
        
        print(f"📁 Cached: {file_path} -> {cache_path}")
        return str(cache_path)
    
    def get_cached_file(self, file_path: str) -> Optional[bytes]:
        """Retrieve file from cache if available"""
        if file_path not in self.metadata_cache:
            return None
        
        metadata = self.metadata_cache[file_path]
        cache_path = Path(metadata.cache_location)
        
        if not cache_path.exists():
            # Cache file missing, remove from metadata
            del self.metadata_cache[file_path]
            return None
        
        # Update access statistics
        metadata.access_count += 1
        metadata.last_access = time.time()
        
        with open(cache_path, 'rb') as f:
            data = f.read()
        
        print(f"⚡ Cache hit: {file_path}")
        return data
    
    def _enforce_cache_limits(self):
        """Remove old cached files if cache is too large"""
        if self.current_cache_size <= self.cache_size_limit:
            return
        
        # Sort by access time (LRU)
        sorted_files = sorted(
            self.metadata_cache.items(),
            key=lambda x: x[1].last_access
        )
        
        for file_path, metadata in sorted_files:
            if self.current_cache_size <= self.cache_size_limit * 0.8:
                break
            
            # Remove file
            cache_path = Path(metadata.cache_location)
            if cache_path.exists():
                cache_path.unlink()
                self.current_cache_size -= metadata.size
            
            del self.metadata_cache[file_path]
            print(f"🗑️  Evicted from cache: {file_path}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_files = len(self.metadata_cache)
        avg_file_size = (
            self.current_cache_size / total_files if total_files > 0 else 0
        )
        
        return {
            "total_cached_files": total_files,
            "current_cache_size_mb": round(self.current_cache_size / 1024 / 1024, 2),
            "cache_limit_mb": round(self.cache_size_limit / 1024 / 1024, 2),
            "cache_utilization": round(self.current_cache_size / self.cache_size_limit * 100, 1),
            "avg_file_size_kb": round(avg_file_size / 1024, 2),
            "most_accessed_files": [
                (path, meta.access_count) 
                for path, meta in sorted(
                    self.metadata_cache.items(),
                    key=lambda x: x[1].access_count,
                    reverse=True
                )[:5]
            ]
        }
    
    def monitor_loop(self):
        """Main monitoring loop"""
        print("🔄 Starting AIStor monitoring loop...")
        
        while True:
            try:
                stats = self.get_cache_stats()
                print(f"📊 Cache Stats: {stats['total_cached_files']} files, "
                      f"{stats['cache_utilization']}% utilized")
                
                # Save metadata periodically
                metadata_file = self.metadata_dir / "cache_metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump({
                        k: asdict(v) for k, v in self.metadata_cache.items()
                    }, f, indent=2)
                
                time.sleep(60)  # Monitor every minute
                
            except KeyboardInterrupt:
                print("🛑 AIStor monitoring stopped")
                break
            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                time.sleep(10)

if __name__ == "__main__":
    aistor = AIStor()
    aistor.monitor_loop()