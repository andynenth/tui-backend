#!/usr/bin/env python3
"""
Cache Performance Testing Tool

Tests cache infrastructure performance for Phase 6.2.2 migration validation.
"""

import asyncio
import sys
import time
import statistics
import logging
import json
from pathlib import Path
from typing import Dict, Any, List
import uuid

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from infrastructure.caching.memory_cache import MemoryCache
from infrastructure.caching.distributed_cache import DistributedCache
from infrastructure.caching.base import CacheConfig
from datetime import timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CachePerformanceTester:
    """Tests cache performance for migration validation."""
    
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        
    async def test_memory_cache_performance(self) -> Dict[str, Any]:
        """Test memory cache performance."""
        logger.info("🧠 Testing memory cache performance...")
        
        config = CacheConfig(
            ttl=timedelta(minutes=30),
            max_size=1000,
            eviction_policy="lru"
        )
        cache = MemoryCache(config)
        
        # Test data
        test_data = {f"key_{i}": f"value_{i}_{'x' * 100}" for i in range(100)}
        
        # Test 1: Set performance
        set_times = []
        for key, value in test_data.items():
            start_time = time.perf_counter()
            await cache.set(key, value)
            end_time = time.perf_counter()
            set_times.append((end_time - start_time) * 1000)  # ms
        
        # Test 2: Get performance (cache hits)
        get_times = []
        for key in list(test_data.keys())[:50]:  # Test subset
            start_time = time.perf_counter()
            value = await cache.get(key)
            end_time = time.perf_counter()
            get_times.append((end_time - start_time) * 1000)  # ms
            assert value is not None, f"Cache miss for key {key}"
        
        # Test 3: Cache miss performance
        miss_times = []
        for i in range(10):
            start_time = time.perf_counter()
            value = await cache.get(f"nonexistent_key_{i}")
            end_time = time.perf_counter()
            miss_times.append((end_time - start_time) * 1000)  # ms
            assert value is None, f"Unexpected cache hit for nonexistent key"
        
        # Test 4: Cache statistics
        stats = cache.get_stats()
        hit_rate = (stats.get('hits', 0) / max(stats.get('total_requests', 1), 1)) * 100
        
        results = {
            "avg_set_time": statistics.mean(set_times),
            "avg_get_time": statistics.mean(get_times),
            "avg_miss_time": statistics.mean(miss_times),
            "p95_get_time": statistics.quantiles(get_times, n=20)[18] if len(get_times) >= 20 else max(get_times),
            "hit_rate": hit_rate,
            "cache_size": len(test_data),
            "stats": stats
        }
        
        print(f"\n🧠 Memory Cache Performance:")
        print(f"  Set time: {results['avg_set_time']:.4f}ms")
        print(f"  Get time: {results['avg_get_time']:.4f}ms")
        print(f"  Miss time: {results['avg_miss_time']:.4f}ms")
        print(f"  Hit rate: {results['hit_rate']:.2f}%")
        
        return results
    
    async def test_cache_eviction_policies(self) -> Dict[str, Any]:
        """Test cache eviction policies."""
        logger.info("🔄 Testing cache eviction policies...")
        
        # Test LRU eviction
        lru_config = CacheConfig(
            ttl=timedelta(minutes=30),
            max_size=10,  # Small size to force eviction
            eviction_policy="lru"
        )
        lru_cache = MemoryCache(lru_config)
        
        # Fill cache to capacity
        for i in range(10):
            await lru_cache.set(f"key_{i}", f"value_{i}")
        
        # Access some keys to establish LRU order
        await lru_cache.get("key_0")
        await lru_cache.get("key_5")
        await lru_cache.get("key_9")
        
        # Add one more item to trigger eviction
        await lru_cache.set("key_10", "value_10")
        
        # Check that least recently used items were evicted
        eviction_results = {}
        for i in range(11):
            value = await lru_cache.get(f"key_{i}")
            eviction_results[f"key_{i}"] = value is not None
        
        # Test TTL eviction
        ttl_config = CacheConfig(
            ttl=timedelta(milliseconds=100),  # Very short TTL
            max_size=1000
        )
        ttl_cache = MemoryCache(ttl_config)
        
        # Set items and wait for expiration
        await ttl_cache.set("ttl_key", "ttl_value")
        immediate_value = await ttl_cache.get("ttl_key")
        
        # Wait for TTL expiration
        await asyncio.sleep(0.15)  # 150ms > 100ms TTL
        expired_value = await ttl_cache.get("ttl_key")
        
        results = {
            "lru_eviction_working": not eviction_results["key_1"],  # Should be evicted
            "lru_accessed_preserved": eviction_results["key_0"],  # Should be preserved
            "ttl_immediate_hit": immediate_value is not None,
            "ttl_expiration_working": expired_value is None,
            "eviction_results": eviction_results
        }
        
        print(f"\n🔄 Eviction Policy Results:")
        print(f"  LRU eviction: {'✅' if results['lru_eviction_working'] else '❌'}")
        print(f"  LRU preservation: {'✅' if results['lru_accessed_preserved'] else '❌'}")
        print(f"  TTL immediate: {'✅' if results['ttl_immediate_hit'] else '❌'}")
        print(f"  TTL expiration: {'✅' if results['ttl_expiration_working'] else '❌'}")
        
        return results
    
    async def test_cache_invalidation(self) -> Dict[str, Any]:
        """Test cache invalidation functionality."""
        logger.info("🗑️ Testing cache invalidation...")
        
        config = CacheConfig(
            ttl=timedelta(minutes=30),
            max_size=1000
        )
        cache = MemoryCache(config)
        
        # Set test data
        test_keys = [f"invalidation_key_{i}" for i in range(10)]
        for key in test_keys:
            await cache.set(key, f"value_for_{key}")
        
        # Test single key invalidation
        await cache.delete(test_keys[0])
        single_invalidation = await cache.get(test_keys[0])
        
        # Test multiple key invalidation
        await cache.delete_many(test_keys[1:3])
        multi_invalidation = [await cache.get(key) for key in test_keys[1:3]]
        
        # Test cache clear
        remaining_before_clear = await cache.get(test_keys[5])
        await cache.clear()
        remaining_after_clear = await cache.get(test_keys[5])
        
        results = {
            "single_key_invalidation": single_invalidation is None,
            "multi_key_invalidation": all(value is None for value in multi_invalidation),
            "cache_clear_working": remaining_before_clear is not None and remaining_after_clear is None
        }
        
        print(f"\n🗑️ Cache Invalidation Results:")
        for test, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {test}")
        
        return results
    
    async def test_concurrent_cache_access(self) -> Dict[str, Any]:
        """Test concurrent cache access performance."""
        logger.info("⚡ Testing concurrent cache access...")
        
        config = CacheConfig(
            ttl=timedelta(minutes=30),
            max_size=1000
        )
        cache = MemoryCache(config)
        
        # Pre-populate cache
        for i in range(50):
            await cache.set(f"concurrent_key_{i}", f"value_{i}")
        
        # Concurrent read test
        async def concurrent_read_task():
            start_time = time.perf_counter()
            tasks = [cache.get(f"concurrent_key_{i}") for i in range(25)]
            results = await asyncio.gather(*tasks)
            return time.perf_counter() - start_time, len([r for r in results if r is not None])
        
        # Run multiple concurrent read tests
        concurrent_times = []
        hit_counts = []
        for _ in range(5):
            read_time, hits = await concurrent_read_task()
            concurrent_times.append(read_time * 1000)  # Convert to ms
            hit_counts.append(hits)
        
        # Sequential read test for comparison
        start_time = time.perf_counter()
        sequential_hits = 0
        for i in range(25):
            result = await cache.get(f"concurrent_key_{i}")
            if result is not None:
                sequential_hits += 1
        sequential_time = (time.perf_counter() - start_time) * 1000
        
        results = {
            "avg_concurrent_time": statistics.mean(concurrent_times),
            "sequential_time": sequential_time,
            "concurrency_speedup": sequential_time / statistics.mean(concurrent_times),
            "hit_consistency": all(hits == hit_counts[0] for hits in hit_counts),
            "avg_hits": statistics.mean(hit_counts)
        }
        
        print(f"\n⚡ Concurrent Access Results:")
        print(f"  Concurrent time: {results['avg_concurrent_time']:.2f}ms")
        print(f"  Sequential time: {results['sequential_time']:.2f}ms")
        print(f"  Speedup: {results['concurrency_speedup']:.2f}x")
        print(f"  Hit consistency: {'✅' if results['hit_consistency'] else '❌'}")
        
        return results
    
    async def validate_cache_requirements(self) -> Dict[str, bool]:
        """Validate cache against Phase 6.2.2 requirements."""
        logger.info("🎯 Validating cache requirements...")
        
        # Run all cache tests
        memory_results = await self.test_memory_cache_performance()
        eviction_results = await self.test_cache_eviction_policies()
        invalidation_results = await self.test_cache_invalidation()
        concurrent_results = await self.test_concurrent_cache_access()
        
        # Validate requirements
        requirements = {
            "cache_hit_rate_over_80": memory_results.get("hit_rate", 0) > 80,
            "response_time_under_1ms": memory_results.get("p95_get_time", 999) < 1.0,
            "eviction_policies_working": (
                eviction_results.get("lru_eviction_working", False) and
                eviction_results.get("ttl_expiration_working", False)
            ),
            "cache_invalidation_accurate": all(invalidation_results.values()),
            "concurrent_access_safe": concurrent_results.get("hit_consistency", False)
        }
        
        print(f"\n🎯 Cache Requirements Validation:")
        for req, passed in requirements.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {req}: {passed}")
        
        # Store detailed results
        self.test_results = {
            "memory_cache": memory_results,
            "eviction_policies": eviction_results,
            "invalidation": invalidation_results,
            "concurrent_access": concurrent_results,
            "requirements_validation": requirements
        }
        
        return requirements
    
    def generate_cache_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive cache performance report."""
        report = {
            "timestamp": time.time(),
            "test_results": self.test_results,
            "summary": {
                "all_requirements_met": all(self.test_results.get("requirements_validation", {}).values()),
                "cache_grade": "A" if all(self.test_results.get("requirements_validation", {}).values()) else "B"
            }
        }
        
        # Save report
        report_file = Path(__file__).parent / "cache_performance_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📁 Cache performance report saved to: {report_file}")
        return report


async def main():
    """Main cache performance testing function."""
    try:
        logger.info("🚀 Starting cache performance testing...")
        
        tester = CachePerformanceTester()
        requirements = await tester.validate_cache_requirements()
        report = tester.generate_cache_performance_report()
        
        print(f"\n📋 Cache Performance Summary:")
        print(f"✅ All requirements met: {report['summary']['all_requirements_met']}")
        print(f"🎯 Cache grade: {report['summary']['cache_grade']}")
        
        # Exit with appropriate code
        if report['summary']['all_requirements_met']:
            logger.info("✅ Cache performance testing successful!")
            sys.exit(0)
        else:
            logger.warning("⚠️ Some cache requirements not met")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Cache performance testing error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())