"""Redis cache and pub/sub service for Railway.app integration."""
import logging
from typing import Any, Optional
from functools import wraps
import json

import redis
from redis.connection import ConnectionPool
from redis.exceptions import ConnectionError, RedisError

from ..core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Service for Redis operations with Railway connection support"""
    
    def __init__(self):
        """Initialize Redis client with Railway connection parameters"""
        self.enabled = False
        self.client: Optional[redis.Redis] = None
        self.connection_pool: Optional[ConnectionPool] = None
        
        if not settings.REDIS_URL:
            logger.warning("Redis URL not configured")
            return
        
        try:
            # Parse Redis URL (supports redis://user:password@host:port/db)
            self.connection_pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                health_check_interval=30,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL
                    3: 5,  # TCP_KEEPCNT
                },
            )
            
            self.client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            if self._test_connection():
                self.enabled = True
                logger.info("Redis service initialized successfully")
            else:
                logger.error("Redis connection test failed")
        
        except Exception as e:
            logger.error(f"Failed to initialize Redis service: {e}")
            self.enabled = False
    
    def _test_connection(self) -> bool:
        """Test Redis connectivity"""
        try:
            result = self.client.ping()
            logger.info(f"Redis ping successful: {result}")
            return result == True or result == b"PONG"
        except (ConnectionError, RedisError) as e:
            logger.error(f"Redis connection test failed: {e}")
            return False
    
    def is_healthy(self) -> bool:
        """Check if Redis is healthy"""
        if not self.enabled:
            return False
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    # Cache operations
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        try:
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except RedisError as e:
            logger.error(f"Redis get failed for key '{key}': {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized if dict/list)
            ttl: Time to live in seconds
        """
        if not self.enabled:
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)
            return True
        except RedisError as e:
            logger.error(f"Redis set failed for key '{key}': {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """Delete one or more keys from cache"""
        if not self.enabled:
            return 0
        try:
            return self.client.delete(*keys)
        except RedisError as e:
            logger.error(f"Redis delete failed: {e}")
            return 0
    
    def exists(self, *keys: str) -> int:
        """Check if keys exist"""
        if not self.enabled:
            return 0
        try:
            return self.client.exists(*keys)
        except RedisError as e:
            logger.error(f"Redis exists check failed: {e}")
            return 0
    
    def clear(self, pattern: str = "*") -> int:
        """Clear keys matching pattern"""
        if not self.enabled:
            return 0
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Redis clear failed: {e}")
            return 0
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        if not self.enabled:
            return 0
        try:
            return self.client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis increment failed for key '{key}': {e}")
            return 0
    
    def decr(self, key: str, amount: int = 1) -> int:
        """Decrement counter"""
        if not self.enabled:
            return 0
        try:
            return self.client.decrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis decrement failed for key '{key}': {e}")
            return 0
    
    # Pub/Sub operations
    def publish(self, channel: str, message: str) -> int:
        """Publish message to channel"""
        if not self.enabled:
            return 0
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            return self.client.publish(channel, message)
        except RedisError as e:
            logger.error(f"Redis publish failed for channel '{channel}': {e}")
            return 0
    
    def subscribe(self, *channels: str):
        """Subscribe to channels (returns pubsub object)"""
        if not self.enabled:
            return None
        try:
            pubsub = self.client.pubsub()
            pubsub.subscribe(*channels)
            return pubsub
        except RedisError as e:
            logger.error(f"Redis subscribe failed: {e}")
            return None
    
    # List operations (for queues)
    def lpush(self, key: str, *values: Any) -> int:
        """Push values to list head"""
        if not self.enabled:
            return 0
        try:
            serialized = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in values]
            return self.client.lpush(key, *serialized)
        except RedisError as e:
            logger.error(f"Redis lpush failed for key '{key}': {e}")
            return 0
    
    def rpush(self, key: str, *values: Any) -> int:
        """Push values to list tail"""
        if not self.enabled:
            return 0
        try:
            serialized = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in values]
            return self.client.rpush(key, *serialized)
        except RedisError as e:
            logger.error(f"Redis rpush failed for key '{key}': {e}")
            return 0
    
    def lpop(self, key: str) -> Optional[Any]:
        """Pop value from list head"""
        if not self.enabled:
            return None
        try:
            value = self.client.lpop(key)
            if value:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except RedisError as e:
            logger.error(f"Redis lpop failed for key '{key}': {e}")
            return None
    
    def rpop(self, key: str) -> Optional[Any]:
        """Pop value from list tail"""
        if not self.enabled:
            return None
        try:
            value = self.client.rpop(key)
            if value:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except RedisError as e:
            logger.error(f"Redis rpop failed for key '{key}': {e}")
            return None
    
    def llen(self, key: str) -> int:
        """Get list length"""
        if not self.enabled:
            return 0
        try:
            return self.client.llen(key)
        except RedisError as e:
            logger.error(f"Redis llen failed for key '{key}': {e}")
            return 0
    
    # Hash operations
    def hset(self, key: str, mapping: dict) -> int:
        """Set hash fields"""
        if not self.enabled:
            return 0
        try:
            # Serialize values
            serialized = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    serialized[k] = json.dumps(v)
                else:
                    serialized[k] = v
            return self.client.hset(key, mapping=serialized)
        except RedisError as e:
            logger.error(f"Redis hset failed for key '{key}': {e}")
            return 0
    
    def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field"""
        if not self.enabled:
            return None
        try:
            value = self.client.hget(key, field)
            if value:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except RedisError as e:
            logger.error(f"Redis hget failed for key '{key}': {e}")
            return None
    
    def hgetall(self, key: str) -> dict:
        """Get all hash fields"""
        if not self.enabled:
            return {}
        try:
            data = self.client.hgetall(key)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            return result
        except RedisError as e:
            logger.error(f"Redis hgetall failed for key '{key}': {e}")
            return {}
    
    def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields"""
        if not self.enabled:
            return 0
        try:
            return self.client.hdel(key, *fields)
        except RedisError as e:
            logger.error(f"Redis hdel failed for key '{key}': {e}")
            return 0
    
    # Expiration/TTL operations
    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        if not self.enabled:
            return False
        try:
            return self.client.expire(key, seconds)
        except RedisError as e:
            logger.error(f"Redis expire failed for key '{key}': {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get time to live (in seconds)"""
        if not self.enabled:
            return -1
        try:
            return self.client.ttl(key)
        except RedisError as e:
            logger.error(f"Redis ttl check failed for key '{key}': {e}")
            return -1
    
    # Utility
    def flush_db(self) -> bool:
        """Flush all keys in current database"""
        if not self.enabled:
            return False
        try:
            self.client.flushdb()
            return True
        except RedisError as e:
            logger.error(f"Redis flush failed: {e}")
            return False
    
    def get_info(self) -> dict:
        """Get Redis server info"""
        if not self.enabled:
            return {}
        try:
            return self.client.info()
        except RedisError as e:
            logger.error(f"Redis info failed: {e}")
            return {}


# Global Redis service instance
redis_service = RedisService()


def cache_result(ttl: int = 300):
    """Decorator to cache function results in Redis"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{func.__module__}.{func.__name__}:{args}:{kwargs}"
            
            # Try to get from cache
            cached = redis_service.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_service.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{func.__module__}.{func.__name__}:{args}:{kwargs}"
            
            # Try to get from cache
            cached = redis_service.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_service.set(cache_key, result, ttl)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


import asyncio
