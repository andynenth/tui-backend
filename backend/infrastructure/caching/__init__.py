"""
Caching infrastructure for high-performance data access.

This module provides:
- Cache abstractions and interfaces
- In-memory cache with TTL and eviction policies
- Distributed cache support
- Common caching patterns (cache-aside, write-through, etc.)
- Cache invalidation strategies
- Cache warming capabilities
"""

from datetime import timedelta
from .base import (
    ICache,
    IBatchCache,
    ITaggedCache,
    IDistributedCache,
    CacheConfig,
    CacheEntry,
    CacheBackend,
    EvictionPolicy,
    CacheLock,
    CacheKeyBuilder,
    CacheDecorator,
    CacheInvalidator,
    CacheWarmer as BaseCacheWarmer,
)

from .memory_cache import MemoryCache

from .distributed_cache import (
    DistributedCache,
    IRedisClient,
    MockRedisClient,
    DistributedCacheLock,
)

from .cache_patterns import (
    IDataSource,
    CacheAsidePattern,
    WriteThroughPattern,
    WriteBehindPattern,
    RefreshAheadPattern,
    CacheStampede,
)

from .cache_strategies import (
    InvalidationStrategy,
    InvalidationRule,
    SmartInvalidator,
    CacheWarmer,
    WarmUpTask,
    warm_frequently_accessed,
    warm_by_pattern,
)

__all__ = [
    # Base interfaces
    "ICache",
    "IBatchCache",
    "ITaggedCache",
    "IDistributedCache",
    "CacheConfig",
    "CacheEntry",
    "CacheBackend",
    "EvictionPolicy",
    "CacheLock",
    "CacheKeyBuilder",
    "CacheDecorator",
    "CacheInvalidator",
    "BaseCacheWarmer",
    # Implementations
    "MemoryCache",
    "DistributedCache",
    "IRedisClient",
    "MockRedisClient",
    "DistributedCacheLock",
    # Patterns
    "IDataSource",
    "CacheAsidePattern",
    "WriteThroughPattern",
    "WriteBehindPattern",
    "RefreshAheadPattern",
    "CacheStampede",
    # Strategies
    "InvalidationStrategy",
    "InvalidationRule",
    "SmartInvalidator",
    "CacheWarmer",
    "WarmUpTask",
    "warm_frequently_accessed",
    "warm_by_pattern",
]


# Convenience factory functions


def create_memory_cache(
    max_size: int = 10000,
    default_ttl: timedelta = None,
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
) -> MemoryCache:
    """Create a configured memory cache instance."""
    from datetime import timedelta

    config = CacheConfig(
        backend=CacheBackend.MEMORY,
        max_size=max_size,
        default_ttl=default_ttl,
        eviction_policy=eviction_policy,
    )
    return MemoryCache(config)


def create_distributed_cache(
    redis_client: IRedisClient = None,
    key_prefix: str = "cache",
    default_ttl: timedelta = None,
    serializer: str = "json",
) -> DistributedCache:
    """Create a configured distributed cache instance."""
    from datetime import timedelta

    config = CacheConfig(
        backend=CacheBackend.REDIS,
        default_ttl=default_ttl,
        options={"key_prefix": key_prefix},
    )
    return DistributedCache(config, redis_client, serializer)
