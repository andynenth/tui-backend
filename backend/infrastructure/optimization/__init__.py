"""
Optimization infrastructure for performance tuning.

Provides memory optimization, caching, and performance monitoring.
"""

from .object_pool import (
    ObjectPool,
    AsyncObjectPool,
    ObjectFactory,
    ObjectPoolConfig,
    ListFactory,
    DictFactory,
    ByteArrayFactory,
    get_pool,
    clear_all_pools,
    pooled_object,
)
from .performance_profiler import (
    PerformanceProfiler,
    ProfileScope,
    profile,
    profile_async,
    get_profiler,
    ProfileReport,
)
from .memory_manager import (
    MemoryManager,
    MemoryStats,
    memory_limit,
    track_memory,
    get_memory_manager,
)

__all__ = [
    # Object pooling
    "ObjectPool",
    "AsyncObjectPool",
    "ObjectFactory",
    "ObjectPoolConfig",
    "ListFactory",
    "DictFactory",
    "ByteArrayFactory",
    "get_pool",
    "clear_all_pools",
    "pooled_object",
    # Performance profiling
    "PerformanceProfiler",
    "ProfileScope",
    "profile",
    "profile_async",
    "get_profiler",
    "ProfileReport",
    # Memory management
    "MemoryManager",
    "MemoryStats",
    "memory_limit",
    "track_memory",
    "get_memory_manager",
]
