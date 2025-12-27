"""
Cache Compression Service
Implements Zstandard compression for cache data to reduce memory usage
"""

import logging
from typing import Any, Optional, Dict
import json
try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False
    zstd = None

logger = logging.getLogger(__name__)


class CacheCompressionService:
    """
    Service for compressing cache data using Zstandard
    
    Zstandard provides:
    - High compression ratios (better than gzip)
    - Fast compression/decompression
    - Low CPU overhead
    - Reduces cache memory usage by 50-70%
    """
    
    def __init__(self, compression_level: int = 3):
        """
        Initialize compression service
        
        Args:
            compression_level: Zstandard compression level (1-22, default 3)
        """
        if not ZSTD_AVAILABLE:
            logger.warning("zstandard not available, compression disabled")
            self.compressor = None
            self.decompressor = None
        else:
            self.compression_level = compression_level
            self.compressor = zstd.ZstdCompressor(level=compression_level)
            self.decompressor = zstd.ZstdDecompressor()
        self.min_size_to_compress = 1024  # Only compress data > 1KB
    
    def compress(self, data: Any) -> bytes:
        """
        Compress data for caching
        
        Args:
            data: Data to compress (will be JSON serialized)
        
        Returns:
            Compressed bytes
        """
        if not ZSTD_AVAILABLE or not self.compressor:
            # Fallback to uncompressed
            return json.dumps(data).encode("utf-8")
        
        try:
            # Serialize to JSON
            json_data = json.dumps(data).encode("utf-8")
            
            # Only compress if data is large enough
            if len(json_data) < self.min_size_to_compress:
                return json_data
            
            # Compress
            compressed = self.compressor.compress(json_data)
            
            # Add header to indicate compression
            header = b"ZSTD:" + len(compressed).to_bytes(4, "big")
            return header + compressed
        except Exception as e:
            logger.error(f"Compression failed: {e}", exc_info=True)
            # Fallback to uncompressed
            return json.dumps(data).encode("utf-8")
    
    def decompress(self, compressed_data: bytes) -> Any:
        """
        Decompress cached data
        
        Args:
            compressed_data: Compressed bytes
        
        Returns:
            Decompressed data (deserialized from JSON)
        """
        if not ZSTD_AVAILABLE or not self.decompressor:
            # Fallback to JSON parsing
            if isinstance(compressed_data, bytes):
                return json.loads(compressed_data.decode("utf-8"))
            return json.loads(compressed_data)
        
        try:
            # Check if data is compressed
            if compressed_data.startswith(b"ZSTD:"):
                # Extract compressed data (skip 5-byte header + 4-byte length)
                compressed = compressed_data[9:]
                # Decompress
                json_data = self.decompressor.decompress(compressed)
            else:
                # Not compressed, use as-is
                json_data = compressed_data
            
            # Deserialize from JSON
            return json.loads(json_data.decode("utf-8"))
        except Exception as e:
            logger.error(f"Decompression failed: {e}", exc_info=True)
            # Try to parse as plain JSON
            try:
                if isinstance(compressed_data, bytes):
                    return json.loads(compressed_data.decode("utf-8"))
                return json.loads(compressed_data)
            except:
                raise ValueError("Failed to decompress data")
    
    def get_compression_stats(self, original_data: Any, compressed_data: bytes) -> Dict[str, Any]:
        """
        Get compression statistics
        
        Args:
            original_data: Original data
            compressed_data: Compressed data
        
        Returns:
            Dictionary with compression stats
        """
        original_size = len(json.dumps(original_data).encode("utf-8"))
        compressed_size = len(compressed_data)
        compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        return {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "space_saved": original_size - compressed_size,
        }


# Global instance
cache_compression_service = CacheCompressionService()
