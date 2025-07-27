#!/usr/bin/env python3
"""
Simple Cache Performance Test

Quick cache validation for Step 6.2.2 cache migration.
"""

import asyncio
import sys
import time
import statistics
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from infrastructure.caching.memory_cache import MemoryCache
from infrastructure.caching.base import CacheConfig, CacheBackend, EvictionPolicy
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Simple cache performance test."""
    logger.info("🚀 Starting simple cache performance test...")
    
    # Initialize cache with proper config
    config = CacheConfig(
        backend=CacheBackend.MEMORY,
        max_size=1000,
        default_ttl=timedelta(minutes=30),
        eviction_policy=EvictionPolicy.LRU
    )
    cache = MemoryCache(config)
    
    # Test 1: Set performance
    logger.info("📝 Testing cache set performance...")
    test_data = {f"key_{i}": f"value_{i}_{'x' * 50}" for i in range(100)}
    
    set_times = []
    for key, value in test_data.items():
        start_time = time.perf_counter()
        await cache.set(key, value)
        end_time = time.perf_counter()
        set_times.append((end_time - start_time) * 1000)  # ms
    
    avg_set_time = statistics.mean(set_times)
    print(f"✅ Cache Set Performance:")
    print(f"  Average: {avg_set_time:.4f}ms")
    print(f"  95th percentile: {statistics.quantiles(set_times, n=20)[18]:.4f}ms")
    
    # Test 2: Get performance (cache hits)
    logger.info("🔍 Testing cache get performance...")
    get_times = []
    hits = 0
    
    for key in list(test_data.keys())[:50]:  # Test subset
        start_time = time.perf_counter()
        value = await cache.get(key)
        end_time = time.perf_counter()
        get_times.append((end_time - start_time) * 1000)  # ms
        if value is not None:
            hits += 1
    
    avg_get_time = statistics.mean(get_times)
    hit_rate = (hits / 50) * 100
    
    print(f"✅ Cache Get Performance:")
    print(f"  Average: {avg_get_time:.4f}ms")
    print(f"  Hit rate: {hit_rate:.1f}%")
    
    # Test 3: Cache miss performance
    logger.info("❌ Testing cache miss performance...")
    miss_times = []
    
    for i in range(10):
        start_time = time.perf_counter()
        value = await cache.get(f"nonexistent_key_{i}")
        end_time = time.perf_counter()
        miss_times.append((end_time - start_time) * 1000)  # ms
        assert value is None, f"Unexpected cache hit for nonexistent key"
    
    avg_miss_time = statistics.mean(miss_times)
    print(f"✅ Cache Miss Performance:")
    print(f"  Average: {avg_miss_time:.4f}ms")
    
    # Test 4: Cache invalidation
    logger.info("🗑️ Testing cache invalidation...")
    test_key = "invalidation_test"
    await cache.set(test_key, "test_value")
    
    # Verify item exists
    value_before = await cache.get(test_key)
    
    # Delete item
    await cache.delete(test_key)
    
    # Verify item is gone
    value_after = await cache.get(test_key)
    
    invalidation_working = value_before is not None and value_after is None
    print(f"✅ Cache Invalidation: {'Working' if invalidation_working else 'Failed'}")
    
    # Test 5: Eviction policy (LRU)
    logger.info("🔄 Testing LRU eviction policy...")
    
    # Create small cache to force eviction
    small_config = CacheConfig(
        backend=CacheBackend.MEMORY,
        max_size=5,  # Very small
        eviction_policy=EvictionPolicy.LRU
    )
    small_cache = MemoryCache(small_config)
    
    # Fill cache
    for i in range(5):
        await small_cache.set(f"evict_key_{i}", f"value_{i}")
    
    # Access some items to establish LRU order
    await small_cache.get("evict_key_0")
    await small_cache.get("evict_key_4")
    
    # Add one more item to trigger eviction
    await small_cache.set("evict_key_5", "value_5")
    
    # Check eviction worked
    key_0_exists = await small_cache.get("evict_key_0") is not None  # Should exist (recently accessed)
    key_1_exists = await small_cache.get("evict_key_1") is not None  # Should be evicted
    key_5_exists = await small_cache.get("evict_key_5") is not None  # Should exist (just added)
    
    eviction_working = key_0_exists and not key_1_exists and key_5_exists
    print(f"✅ LRU Eviction: {'Working' if eviction_working else 'Failed'}")
    
    # Performance requirements validation
    requirements = {
        "hit_rate_over_80": hit_rate > 80,
        "get_time_under_1ms": avg_get_time < 1.0,
        "eviction_working": eviction_working,
        "invalidation_working": invalidation_working
    }
    
    print(f"\n🎯 Cache Requirements Validation:")
    all_passed = True
    for req, passed in requirements.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {req}: {passed}")
        if not passed:
            all_passed = False
    
    print(f"\n📊 Overall Result: {'✅ PASS' if all_passed else '❌ FAIL'}")
    
    # Memory usage
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"💾 Memory usage: {memory_mb:.2f}MB")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Cache test failed: {e}")
        sys.exit(1)