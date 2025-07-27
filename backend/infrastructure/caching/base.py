"""
Base interfaces and abstractions for the caching infrastructure.

This module provides the foundation for implementing different caching
strategies while maintaining a consistent interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Generic, Dict, Any, List, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import asyncio


T = TypeVar('T')


class CacheBackend(Enum):
    """Available cache backends."""
    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"
    HYBRID = "hybrid"


class EvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"        # Least Recently Used
    LFU = "lfu"        # Least Frequently Used
    FIFO = "fifo"      # First In First Out
    TTL = "ttl"        # Time To Live based
    RANDOM = "random"  # Random eviction


@dataclass
class CacheConfig:
    """Configuration for cache backends."""
    backend: CacheBackend
    max_size: Optional[int] = None
    default_ttl: Optional[timedelta] = None
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    connection_string: Optional[str] = None
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {}


@dataclass
class CacheEntry(Generic[T]):
    """Represents a cached value with metadata."""
    value: T
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl: Optional[timedelta]
    tags: Set[str]
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return datetime.utcnow() > self.created_at + self.ttl
    
    def touch(self) -> None:
        """Update last access time and count."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1


class ICache(ABC, Generic[T]):
    """
    Abstract base class for cache implementations.
    
    Provides basic cache operations that all implementations must support.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[timedelta] = None,
        tags: Optional[Set[str]] = None
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (overrides default)
            tags: Tags for grouped invalidation
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if exists and not expired
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries from cache."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache metrics
        """
        pass


class IBatchCache(ICache[T]):
    """Extension for batch operations."""
    
    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of found key-value pairs
        """
        pass
    
    @abstractmethod
    async def set_many(
        self,
        entries: Dict[str, T],
        ttl: Optional[timedelta] = None,
        tags: Optional[Set[str]] = None
    ) -> None:
        """
        Set multiple values in cache.
        
        Args:
            entries: Dictionary of key-value pairs
            ttl: Time to live for all entries
            tags: Tags for all entries
        """
        pass
    
    @abstractmethod
    async def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Number of entries deleted
        """
        pass


class ITaggedCache(ICache[T]):
    """Extension for tag-based operations."""
    
    @abstractmethod
    async def get_by_tag(self, tag: str) -> Dict[str, T]:
        """
        Get all entries with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            Dictionary of key-value pairs
        """
        pass
    
    @abstractmethod
    async def delete_by_tag(self, tag: str) -> int:
        """
        Delete all entries with a specific tag.
        
        Args:
            tag: Tag to delete by
            
        Returns:
            Number of entries deleted
        """
        pass
    
    @abstractmethod
    async def get_tags(self, key: str) -> Set[str]:
        """
        Get tags for a specific key.
        
        Args:
            key: Cache key
            
        Returns:
            Set of tags
        """
        pass


class IDistributedCache(ICache[T]):
    """Extension for distributed cache operations."""
    
    @abstractmethod
    async def lock(self, key: str, timeout: timedelta) -> 'CacheLock':
        """
        Acquire distributed lock.
        
        Args:
            key: Lock key
            timeout: Lock timeout
            
        Returns:
            Lock context manager
        """
        pass
    
    @abstractmethod
    async def increment(self, key: str, delta: int = 1) -> int:
        """
        Atomic increment operation.
        
        Args:
            key: Counter key
            delta: Increment value
            
        Returns:
            New value after increment
        """
        pass
    
    @abstractmethod
    async def decrement(self, key: str, delta: int = 1) -> int:
        """
        Atomic decrement operation.
        
        Args:
            key: Counter key
            delta: Decrement value
            
        Returns:
            New value after decrement
        """
        pass


class CacheLock:
    """Distributed lock for cache operations."""
    
    def __init__(self, key: str, cache: IDistributedCache):
        self.key = key
        self.cache = cache
        self.acquired = False
    
    async def __aenter__(self):
        """Acquire lock."""
        # Implementation depends on backend
        self.acquired = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release lock."""
        if self.acquired:
            # Release lock logic
            self.acquired = False


class CacheKeyBuilder:
    """
    Utility for building consistent cache keys.
    
    Helps maintain key naming conventions across the application.
    """
    
    def __init__(self, prefix: str = "", separator: str = ":"):
        self.prefix = prefix
        self.separator = separator
    
    def build(self, *parts: str) -> str:
        """
        Build cache key from parts.
        
        Args:
            *parts: Key components
            
        Returns:
            Formatted cache key
        """
        if self.prefix:
            parts = (self.prefix,) + parts
        return self.separator.join(str(p) for p in parts)
    
    def with_prefix(self, prefix: str) -> 'CacheKeyBuilder':
        """Create new builder with additional prefix."""
        new_prefix = self.build(prefix) if self.prefix else prefix
        return CacheKeyBuilder(new_prefix, self.separator)


class CacheDecorator:
    """
    Decorator for caching function results.
    
    Provides easy integration of caching into existing code.
    """
    
    def __init__(
        self,
        cache: ICache,
        key_builder: Optional[CacheKeyBuilder] = None,
        ttl: Optional[timedelta] = None,
        tags: Optional[Set[str]] = None
    ):
        self.cache = cache
        self.key_builder = key_builder or CacheKeyBuilder()
        self.ttl = ttl
        self.tags = tags
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate function with caching."""
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            cache_key = self.key_builder.build(*key_parts)
            
            # Try to get from cache
            cached_value = await self.cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await self.cache.set(cache_key, result, ttl=self.ttl, tags=self.tags)
            
            return result
        
        return wrapper


class CacheInvalidator:
    """
    Manages cache invalidation strategies.
    
    Provides patterns for keeping cache consistent with data changes.
    """
    
    def __init__(self, cache: ICache):
        self.cache = cache
        self._invalidation_rules: List[Callable] = []
    
    def add_rule(self, rule: Callable[[str, Any], List[str]]) -> None:
        """
        Add invalidation rule.
        
        Args:
            rule: Function that returns keys to invalidate based on event
        """
        self._invalidation_rules.append(rule)
    
    async def invalidate(self, event_type: str, event_data: Any) -> int:
        """
        Invalidate cache entries based on event.
        
        Args:
            event_type: Type of event that occurred
            event_data: Event data
            
        Returns:
            Number of entries invalidated
        """
        keys_to_invalidate = set()
        
        for rule in self._invalidation_rules:
            keys = rule(event_type, event_data)
            keys_to_invalidate.update(keys)
        
        invalidated = 0
        for key in keys_to_invalidate:
            if await self.cache.delete(key):
                invalidated += 1
        
        return invalidated


class CacheWarmer:
    """
    Handles cache warming strategies.
    
    Pre-loads cache with frequently accessed data.
    """
    
    def __init__(self, cache: ICache):
        self.cache = cache
        self._warm_up_tasks: List[Callable] = []
    
    def add_task(self, task: Callable) -> None:
        """
        Add warm-up task.
        
        Args:
            task: Async function that loads data into cache
        """
        self._warm_up_tasks.append(task)
    
    async def warm_up(self) -> Dict[str, Any]:
        """
        Execute all warm-up tasks.
        
        Returns:
            Summary of warming results
        """
        results = {
            'tasks_executed': 0,
            'entries_loaded': 0,
            'errors': []
        }
        
        for task in self._warm_up_tasks:
            try:
                entries = await task(self.cache)
                results['tasks_executed'] += 1
                results['entries_loaded'] += entries
            except Exception as e:
                results['errors'].append({
                    'task': task.__name__,
                    'error': str(e)
                })
        
        return results