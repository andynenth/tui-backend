"""
Distributed cache adapter for Redis and other backends.

This provides cache functionality that can be shared across multiple
application instances.
"""

import asyncio
import json
import pickle
from typing import Optional, Dict, Any, List, Set, Union
from datetime import datetime, timedelta
import uuid
from abc import ABC, abstractmethod

from .base import (
    ICache,
    IBatchCache,
    ITaggedCache,
    IFullCache,
    IDistributedCache,
    CacheConfig,
    CacheEntry,
    CacheBackend,
    CacheLock
)


class IRedisClient(ABC):
    """Interface for Redis client to allow mocking and different implementations."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: bytes, ex: Optional[int] = None) -> None:
        pass
    
    @abstractmethod
    async def delete(self, *keys: str) -> int:
        pass
    
    @abstractmethod
    async def exists(self, *keys: str) -> int:
        pass
    
    @abstractmethod
    async def mget(self, *keys: str) -> List[Optional[bytes]]:
        pass
    
    @abstractmethod
    async def mset(self, mapping: Dict[str, bytes]) -> None:
        pass
    
    @abstractmethod
    async def expire(self, key: str, seconds: int) -> bool:
        pass
    
    @abstractmethod
    async def ttl(self, key: str) -> int:
        pass
    
    @abstractmethod
    async def incr(self, key: str) -> int:
        pass
    
    @abstractmethod
    async def decr(self, key: str) -> int:
        pass
    
    @abstractmethod
    async def sadd(self, key: str, *members: str) -> int:
        pass
    
    @abstractmethod
    async def srem(self, key: str, *members: str) -> int:
        pass
    
    @abstractmethod
    async def smembers(self, key: str) -> Set[str]:
        pass
    
    @abstractmethod
    async def flushdb(self) -> None:
        pass


class MockRedisClient(IRedisClient):
    """Mock Redis client for testing without Redis dependency."""
    
    def __init__(self):
        self._storage: Dict[str, Union[bytes, int, Set[str]]] = {}
        self._expiry: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[bytes]:
        async with self._lock:
            if key in self._expiry and datetime.utcnow() > self._expiry[key]:
                del self._storage[key]
                del self._expiry[key]
                return None
            
            value = self._storage.get(key)
            return value if isinstance(value, bytes) else None
    
    async def set(self, key: str, value: bytes, ex: Optional[int] = None) -> None:
        async with self._lock:
            self._storage[key] = value
            if ex:
                self._expiry[key] = datetime.utcnow() + timedelta(seconds=ex)
    
    async def delete(self, *keys: str) -> int:
        async with self._lock:
            deleted = 0
            for key in keys:
                if key in self._storage:
                    del self._storage[key]
                    self._expiry.pop(key, None)
                    deleted += 1
            return deleted
    
    async def exists(self, *keys: str) -> int:
        async with self._lock:
            count = 0
            for key in keys:
                if key in self._storage:
                    if key not in self._expiry or datetime.utcnow() <= self._expiry[key]:
                        count += 1
            return count
    
    async def mget(self, *keys: str) -> List[Optional[bytes]]:
        results = []
        for key in keys:
            value = await self.get(key)
            results.append(value)
        return results
    
    async def mset(self, mapping: Dict[str, bytes]) -> None:
        async with self._lock:
            self._storage.update(mapping)
    
    async def expire(self, key: str, seconds: int) -> bool:
        async with self._lock:
            if key in self._storage:
                self._expiry[key] = datetime.utcnow() + timedelta(seconds=seconds)
                return True
            return False
    
    async def ttl(self, key: str) -> int:
        async with self._lock:
            if key not in self._storage:
                return -2
            if key not in self._expiry:
                return -1
            
            remaining = (self._expiry[key] - datetime.utcnow()).total_seconds()
            return max(0, int(remaining))
    
    async def incr(self, key: str) -> int:
        async with self._lock:
            value = self._storage.get(key, 0)
            if isinstance(value, int):
                value += 1
            else:
                value = 1
            self._storage[key] = value
            return value
    
    async def decr(self, key: str) -> int:
        async with self._lock:
            value = self._storage.get(key, 0)
            if isinstance(value, int):
                value -= 1
            else:
                value = -1
            self._storage[key] = value
            return value
    
    async def sadd(self, key: str, *members: str) -> int:
        async with self._lock:
            s = self._storage.get(key, set())
            if not isinstance(s, set):
                s = set()
            
            added = 0
            for member in members:
                if member not in s:
                    s.add(member)
                    added += 1
            
            self._storage[key] = s
            return added
    
    async def srem(self, key: str, *members: str) -> int:
        async with self._lock:
            s = self._storage.get(key, set())
            if not isinstance(s, set):
                return 0
            
            removed = 0
            for member in members:
                if member in s:
                    s.remove(member)
                    removed += 1
            
            if s:
                self._storage[key] = s
            else:
                del self._storage[key]
            
            return removed
    
    async def smembers(self, key: str) -> Set[str]:
        async with self._lock:
            s = self._storage.get(key, set())
            return s if isinstance(s, set) else set()
    
    async def flushdb(self) -> None:
        async with self._lock:
            self._storage.clear()
            self._expiry.clear()


class DistributedCache(IFullCache, IDistributedCache):
    """
    Distributed cache implementation using Redis or similar backends.
    
    Features:
    - Shared cache across multiple instances
    - Atomic operations
    - Distributed locks
    - Tag-based invalidation
    - JSON/Pickle serialization
    """
    
    def __init__(
        self,
        config: CacheConfig,
        redis_client: Optional[IRedisClient] = None,
        serializer: str = "json"
    ):
        """
        Initialize distributed cache.
        
        Args:
            config: Cache configuration
            redis_client: Redis client instance (uses mock if not provided)
            serializer: Serialization method ("json" or "pickle")
        """
        self._config = config
        self._client = redis_client or MockRedisClient()
        self._serializer = serializer
        
        # Key prefixes
        self._prefix = config.options.get('key_prefix', 'cache')
        self._tag_prefix = f"{self._prefix}:tags"
        self._meta_prefix = f"{self._prefix}:meta"
        
        # Default TTL
        self._default_ttl = config.default_ttl
        
        # Statistics (local only)
        self._stats = {
            'operations': 0,
            'errors': 0
        }
    
    def _make_key(self, key: str) -> str:
        """Create full key with prefix."""
        return f"{self._prefix}:{key}"
    
    def _make_tag_key(self, tag: str) -> str:
        """Create tag index key."""
        return f"{self._tag_prefix}:{tag}"
    
    def _make_meta_key(self, key: str) -> str:
        """Create metadata key."""
        return f"{self._meta_prefix}:{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if self._serializer == "json":
            return json.dumps(value).encode('utf-8')
        else:
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        if self._serializer == "json":
            return json.loads(data.decode('utf-8'))
        else:
            return pickle.loads(data)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            self._stats['operations'] += 1
            
            full_key = self._make_key(key)
            data = await self._client.get(full_key)
            
            if data is None:
                return None
            
            return self._deserialize(data)
            
        except Exception as e:
            self._stats['errors'] += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        tags: Optional[Set[str]] = None
    ) -> None:
        """Set value in cache."""
        try:
            self._stats['operations'] += 1
            
            full_key = self._make_key(key)
            serialized = self._serialize(value)
            
            # Calculate TTL in seconds
            ttl_seconds = None
            if ttl:
                ttl_seconds = int(ttl.total_seconds())
            elif self._default_ttl:
                ttl_seconds = int(self._default_ttl.total_seconds())
            
            # Set value with TTL
            await self._client.set(full_key, serialized, ex=ttl_seconds)
            
            # Handle tags
            if tags:
                # Store tags for this key
                meta_key = self._make_meta_key(key)
                await self._client.set(
                    meta_key,
                    self._serialize(list(tags)),
                    ex=ttl_seconds
                )
                
                # Add key to tag indexes
                for tag in tags:
                    tag_key = self._make_tag_key(tag)
                    await self._client.sadd(tag_key, key)
            
        except Exception as e:
            self._stats['errors'] += 1
            raise
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self._stats['operations'] += 1
            
            # Remove from tag indexes first
            meta_key = self._make_meta_key(key)
            tags_data = await self._client.get(meta_key)
            
            if tags_data:
                tags = self._deserialize(tags_data)
                for tag in tags:
                    tag_key = self._make_tag_key(tag)
                    await self._client.srem(tag_key, key)
            
            # Delete metadata
            await self._client.delete(meta_key)
            
            # Delete main key
            full_key = self._make_key(key)
            result = await self._client.delete(full_key)
            
            return result > 0
            
        except Exception as e:
            self._stats['errors'] += 1
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            self._stats['operations'] += 1
            
            full_key = self._make_key(key)
            result = await self._client.exists(full_key)
            
            return result > 0
            
        except Exception as e:
            self._stats['errors'] += 1
            return False
    
    async def clear(self) -> None:
        """Clear all entries from cache."""
        try:
            self._stats['operations'] += 1
            
            # In production, this would need to be more careful
            # For now, flush the entire database (development only)
            if isinstance(self._client, MockRedisClient):
                await self._client.flushdb()
            else:
                # Would need to implement pattern-based deletion
                pass
            
        except Exception as e:
            self._stats['errors'] += 1
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'backend': 'distributed',
            'stats': dict(self._stats),
            'serializer': self._serializer,
            'prefix': self._prefix
        }
    
    # IBatchCache implementation
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        try:
            self._stats['operations'] += 1
            
            full_keys = [self._make_key(key) for key in keys]
            values = await self._client.mget(*full_keys)
            
            results = {}
            for key, value in zip(keys, values):
                if value is not None:
                    results[key] = self._deserialize(value)
            
            return results
            
        except Exception as e:
            self._stats['errors'] += 1
            return {}
    
    async def set_many(
        self,
        entries: Dict[str, Any],
        ttl: Optional[timedelta] = None,
        tags: Optional[Set[str]] = None
    ) -> None:
        """Set multiple values in cache."""
        # For simplicity, use individual sets
        # In production, would use pipeline or MSET with custom TTL handling
        for key, value in entries.items():
            await self.set(key, value, ttl=ttl, tags=tags)
    
    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple values from cache."""
        try:
            self._stats['operations'] += 1
            
            # Handle tag cleanup first
            for key in keys:
                meta_key = self._make_meta_key(key)
                tags_data = await self._client.get(meta_key)
                
                if tags_data:
                    tags = self._deserialize(tags_data)
                    for tag in tags:
                        tag_key = self._make_tag_key(tag)
                        await self._client.srem(tag_key, key)
            
            # Delete metadata keys
            meta_keys = [self._make_meta_key(key) for key in keys]
            await self._client.delete(*meta_keys)
            
            # Delete main keys
            full_keys = [self._make_key(key) for key in keys]
            result = await self._client.delete(*full_keys)
            
            return result
            
        except Exception as e:
            self._stats['errors'] += 1
            return 0
    
    # ITaggedCache implementation
    
    async def get_by_tag(self, tag: str) -> Dict[str, Any]:
        """Get all entries with a specific tag."""
        try:
            self._stats['operations'] += 1
            
            tag_key = self._make_tag_key(tag)
            members = await self._client.smembers(tag_key)
            
            if not members:
                return {}
            
            # Get all values
            keys = list(members)
            return await self.get_many(keys)
            
        except Exception as e:
            self._stats['errors'] += 1
            return {}
    
    async def delete_by_tag(self, tag: str) -> int:
        """Delete all entries with a specific tag."""
        try:
            self._stats['operations'] += 1
            
            tag_key = self._make_tag_key(tag)
            members = await self._client.smembers(tag_key)
            
            if not members:
                return 0
            
            # Delete all keys with this tag
            keys = list(members)
            deleted = await self.delete_many(keys)
            
            # Clean up tag index
            await self._client.delete(tag_key)
            
            return deleted
            
        except Exception as e:
            self._stats['errors'] += 1
            return 0
    
    async def get_tags(self, key: str) -> Set[str]:
        """Get tags for a specific key."""
        try:
            self._stats['operations'] += 1
            
            meta_key = self._make_meta_key(key)
            tags_data = await self._client.get(meta_key)
            
            if tags_data:
                tags = self._deserialize(tags_data)
                return set(tags)
            
            return set()
            
        except Exception as e:
            self._stats['errors'] += 1
            return set()
    
    # IDistributedCache implementation
    
    async def lock(self, key: str, timeout: timedelta) -> 'DistributedCacheLock':
        """Acquire distributed lock."""
        lock_key = f"{self._prefix}:lock:{key}"
        lock_value = str(uuid.uuid4())
        
        return DistributedCacheLock(
            lock_key,
            lock_value,
            self._client,
            timeout
        )
    
    async def increment(self, key: str, delta: int = 1) -> int:
        """Atomic increment operation."""
        try:
            self._stats['operations'] += 1
            
            full_key = self._make_key(key)
            
            if delta == 1:
                return await self._client.incr(full_key)
            else:
                # Would use INCRBY in real Redis
                for _ in range(abs(delta)):
                    if delta > 0:
                        result = await self._client.incr(full_key)
                    else:
                        result = await self._client.decr(full_key)
                return result
            
        except Exception as e:
            self._stats['errors'] += 1
            raise
    
    async def decrement(self, key: str, delta: int = 1) -> int:
        """Atomic decrement operation."""
        return await self.increment(key, -delta)


class DistributedCacheLock(CacheLock):
    """Distributed lock implementation using Redis."""
    
    def __init__(
        self,
        key: str,
        value: str,
        client: IRedisClient,
        timeout: timedelta
    ):
        super().__init__(key, None)
        self.value = value
        self.client = client
        self.timeout = timeout
    
    async def __aenter__(self):
        """Acquire lock with timeout."""
        timeout_seconds = int(self.timeout.total_seconds())
        
        # Try to acquire lock with SET NX EX
        # In real Redis, would use SET with NX and EX options
        acquired = False
        start_time = datetime.utcnow()
        
        while not acquired:
            # Check if lock exists
            existing = await self.client.get(self.key)
            if existing is None:
                # Try to set
                await self.client.set(
                    self.key,
                    self.value.encode('utf-8'),
                    ex=timeout_seconds
                )
                
                # Verify we got it
                check = await self.client.get(self.key)
                if check and check.decode('utf-8') == self.value:
                    acquired = True
                    self.acquired = True
            
            if not acquired:
                # Check timeout
                if datetime.utcnow() - start_time > self.timeout:
                    raise TimeoutError(f"Could not acquire lock {self.key}")
                
                # Brief sleep before retry
                await asyncio.sleep(0.01)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release lock if we own it."""
        if self.acquired:
            # Only delete if we still own it
            current = await self.client.get(self.key)
            if current and current.decode('utf-8') == self.value:
                await self.client.delete(self.key)
            
            self.acquired = False