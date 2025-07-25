"""
In-memory cache service implementation.

This module provides a simple in-memory implementation of the CacheService
interface for development and testing.
"""

import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import asyncio

from application.interfaces import CacheService

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a cached value with expiration."""
    
    def __init__(self, value: Any, ttl: Optional[int] = None):
        """
        Initialize cache entry.
        
        Args:
            value: The cached value
            ttl: Time to live in seconds
        """
        self.value = value
        self.created_at = datetime.utcnow()
        self.expires_at = (
            datetime.utcnow() + timedelta(seconds=ttl)
            if ttl else None
        )
    
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class InMemoryCacheService(CacheService):
    """
    In-memory implementation of cache service.
    
    This provides a simple cache for development. In production,
    this would be replaced with Redis or similar.
    """
    
    def __init__(self):
        """Initialize the cache service."""
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value or None if not found/expired
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired():
            # Remove expired entry
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set a value in cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
        """
        self._cache[key] = CacheEntry(value, ttl)
        self._sets += 1
        logger.debug(f"Cached {key} with TTL {ttl}s")
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key existed and was deleted
        """
        if key in self._cache:
            del self._cache[key]
            self._deletes += 1
            logger.debug(f"Deleted cache key {key}")
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key exists and hasn't expired
        """
        entry = self._cache.get(key)
        if entry is None:
            return False
        
        if entry.is_expired():
            del self._cache[key]
            return False
        
        return True
    
    async def clear(self) -> None:
        """Clear all cached values."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")
    
    async def _cleanup_loop(self):
        """Periodically clean up expired entries."""
        while True:
            try:
                # Wait 60 seconds between cleanups
                await asyncio.sleep(60)
                
                # Find expired entries
                expired_keys = []
                for key, entry in self._cache.items():
                    if entry.is_expired():
                        expired_keys.append(key)
                
                # Remove expired entries
                for key in expired_keys:
                    del self._cache[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / max(total_requests, 1)
        
        return {
            'entries': len(self._cache),
            'hits': self._hits,
            'misses': self._misses,
            'sets': self._sets,
            'deletes': self._deletes,
            'hit_rate': hit_rate
        }
    
    async def close(self):
        """Close the cache service and cleanup resources."""
        self._cleanup_task.cancel()
        try:
            await self._cleanup_task
        except asyncio.CancelledError:
            pass