import redis
import json
import logging
from typing import Optional, Any
from datetime import timedelta
from ..core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.redis_client.ping()
            self.enabled = True
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}. Caching disabled.")
            self.enabled = False
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL in seconds"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if not self.enabled:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache delete pattern error: {e}")
            return False
    
    def get_sensor_stats(self, sensor_id: str) -> Optional[dict]:
        """Get cached sensor statistics"""
        return self.get(f"sensor:stats:{sensor_id}")
    
    def set_sensor_stats(self, sensor_id: str, stats: dict, ttl: int = 60):
        """Cache sensor statistics"""
        return self.set(f"sensor:stats:{sensor_id}", stats, ttl)
    
    def get_municipality_stats(self, municipality_id: str) -> Optional[dict]:
        """Get cached municipality statistics"""
        return self.get(f"municipality:stats:{municipality_id}")
    
    def set_municipality_stats(self, municipality_id: str, stats: dict, ttl: int = 120):
        """Cache municipality statistics"""
        return self.set(f"municipality:stats:{municipality_id}", stats, ttl)
    
    def invalidate_sensor_cache(self, sensor_id: str):
        """Invalidate all cache for a sensor"""
        return self.delete_pattern(f"sensor:*:{sensor_id}")
    
    def invalidate_municipality_cache(self, municipality_id: str):
        """Invalidate all cache for a municipality"""
        return self.delete_pattern(f"municipality:*:{municipality_id}")

cache_service = CacheService()
