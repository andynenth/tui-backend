"""
Tests for the caching infrastructure.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from infrastructure.caching import (
    # Base
    CacheConfig,
    CacheBackend,
    EvictionPolicy,
    CacheKeyBuilder,
    # Implementations
    MemoryCache,
    DistributedCache,
    MockRedisClient,
    # Patterns
    IDataSource,
    CacheAsidePattern,
    WriteThroughPattern,
    WriteBehindPattern,
    RefreshAheadPattern,
    CacheStampede,
    # Strategies
    InvalidationStrategy,
    InvalidationRule,
    SmartInvalidator,
    CacheWarmer,
    warm_frequently_accessed,
)


# Test data source implementation


class TestDataSource(IDataSource):
    """Mock data source for testing."""

    def __init__(self):
        self.data = {}
        self.get_count = 0
        self.save_count = 0
        self.delete_count = 0
        self.delay = 0.01  # Simulate I/O delay

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        self.get_count += 1
        await asyncio.sleep(self.delay)
        return self.data.get(key)

    async def get_many(self, keys: List[str]) -> Dict[str, Dict[str, Any]]:
        self.get_count += len(keys)
        await asyncio.sleep(self.delay)
        return {k: v for k, v in self.data.items() if k in keys}

    async def save(self, key: str, value: Dict[str, Any]) -> None:
        self.save_count += 1
        await asyncio.sleep(self.delay)
        self.data[key] = value

    async def delete(self, key: str) -> bool:
        self.delete_count += 1
        await asyncio.sleep(self.delay)
        if key in self.data:
            del self.data[key]
            return True
        return False


# Tests for MemoryCache


class TestMemoryCache:
    """Test the in-memory cache implementation."""

    @pytest.mark.asyncio
    async def test_basic_operations(self):
        """Test basic cache operations."""
        config = CacheConfig(
            backend=CacheBackend.MEMORY,
            max_size=100,
            eviction_policy=EvictionPolicy.LRU,
        )
        cache = MemoryCache(config)

        # Test set and get
        await cache.set("key1", {"value": 1})
        result = await cache.get("key1")
        assert result == {"value": 1}

        # Test exists
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

        # Test delete
        assert await cache.delete("key1") is True
        assert await cache.get("key1") is None
        assert await cache.delete("nonexistent") is False

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test TTL expiration."""
        config = CacheConfig(
            backend=CacheBackend.MEMORY, default_ttl=timedelta(seconds=0.1)
        )
        cache = MemoryCache(config)

        # Set with TTL
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"

        # Wait for expiration
        await asyncio.sleep(0.2)
        assert await cache.get("key1") is None

        # Test custom TTL
        await cache.set("key2", "value2", ttl=timedelta(seconds=0.5))
        await asyncio.sleep(0.2)
        assert await cache.get("key2") == "value2"  # Still there

        await asyncio.sleep(0.4)
        assert await cache.get("key2") is None  # Now expired

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction policy."""
        config = CacheConfig(
            backend=CacheBackend.MEMORY, max_size=3, eviction_policy=EvictionPolicy.LRU
        )
        cache = MemoryCache(config)

        # Fill cache
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 and key2 to make them more recent
        await cache.get("key1")
        await cache.get("key2")

        # Add new key - should evict key3 (least recently used)
        await cache.set("key4", "value4")

        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") is None  # Evicted
        assert await cache.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_lfu_eviction(self):
        """Test LFU eviction policy."""
        config = CacheConfig(
            backend=CacheBackend.MEMORY, max_size=3, eviction_policy=EvictionPolicy.LFU
        )
        cache = MemoryCache(config)

        # Fill cache
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 and key2 multiple times
        for _ in range(3):
            await cache.get("key1")
        for _ in range(2):
            await cache.get("key2")
        # key3 accessed only once (during set)

        # Add new key - should evict key3 (least frequently used)
        await cache.set("key4", "value4")

        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") is None  # Evicted
        assert await cache.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_batch_operations(self):
        """Test batch operations."""
        cache = MemoryCache()

        # Batch set
        entries = {"key1": "value1", "key2": "value2", "key3": "value3"}
        await cache.set_many(entries)

        # Batch get
        results = await cache.get_many(["key1", "key2", "key4"])
        assert results == {"key1": "value1", "key2": "value2"}

        # Batch delete
        deleted = await cache.delete_many(["key1", "key2", "key4"])
        assert deleted == 2
        assert await cache.get("key1") is None
        assert await cache.get("key3") == "value3"  # Not deleted

    @pytest.mark.asyncio
    async def test_tag_operations(self):
        """Test tag-based operations."""
        cache = MemoryCache()

        # Set with tags
        await cache.set("user:1", {"name": "Alice"}, tags={"users", "active"})
        await cache.set("user:2", {"name": "Bob"}, tags={"users", "active"})
        await cache.set("user:3", {"name": "Charlie"}, tags={"users", "inactive"})

        # Get by tag
        active_users = await cache.get_by_tag("active")
        assert len(active_users) == 2
        assert "user:1" in active_users
        assert "user:2" in active_users

        # Delete by tag
        deleted = await cache.delete_by_tag("inactive")
        assert deleted == 1
        assert await cache.get("user:3") is None

        # Get tags for key
        tags = await cache.get_tags("user:1")
        assert tags == {"users", "active"}

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics."""
        cache = MemoryCache()

        # Perform operations
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss
        await cache.delete("key1")

        stats = await cache.get_stats()
        assert stats["stats"]["hits"] == 1
        assert stats["stats"]["misses"] == 1
        assert stats["stats"]["sets"] == 1
        assert stats["stats"]["deletes"] == 1
        assert stats["hit_rate"] == 0.5


# Tests for DistributedCache


class TestDistributedCache:
    """Test the distributed cache implementation."""

    @pytest.mark.asyncio
    async def test_basic_operations_with_mock(self):
        """Test basic operations with mock Redis client."""
        config = CacheConfig(backend=CacheBackend.REDIS)
        client = MockRedisClient()
        cache = DistributedCache(config, client)

        # Test set and get
        await cache.set("key1", {"value": 1})
        result = await cache.get("key1")
        assert result == {"value": 1}

        # Test exists
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

        # Test delete
        assert await cache.delete("key1") is True
        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_ttl_with_mock(self):
        """Test TTL with mock Redis client."""
        config = CacheConfig(
            backend=CacheBackend.REDIS, default_ttl=timedelta(seconds=1)
        )
        client = MockRedisClient()
        cache = DistributedCache(config, client)

        # Set with default TTL
        await cache.set("key1", "value1")

        # Check TTL is set
        ttl = await client.ttl("cache:key1")
        assert ttl > 0

        # Set with custom TTL
        await cache.set("key2", "value2", ttl=timedelta(seconds=5))
        ttl2 = await client.ttl("cache:key2")
        assert ttl2 > ttl

    @pytest.mark.asyncio
    async def test_atomic_operations(self):
        """Test atomic increment/decrement."""
        config = CacheConfig(backend=CacheBackend.REDIS)
        client = MockRedisClient()
        cache = DistributedCache(config, client)

        # Increment
        result = await cache.increment("counter")
        assert result == 1

        result = await cache.increment("counter", 5)
        assert result == 6

        # Decrement
        result = await cache.decrement("counter", 2)
        assert result == 4

    @pytest.mark.asyncio
    async def test_distributed_lock(self):
        """Test distributed lock functionality."""
        config = CacheConfig(backend=CacheBackend.REDIS)
        client = MockRedisClient()
        cache = DistributedCache(config, client)

        # Acquire lock
        async with await cache.lock("resource", timedelta(seconds=1)) as lock:
            assert lock.acquired is True

            # Try to acquire same lock from another task
            acquired_by_other = False

            async def try_acquire():
                nonlocal acquired_by_other
                try:
                    async with await cache.lock("resource", timedelta(seconds=0.1)):
                        acquired_by_other = True
                except TimeoutError:
                    pass

            await try_acquire()
            assert acquired_by_other is False

        # Lock should be released now
        async with await cache.lock("resource", timedelta(seconds=1)) as lock:
            assert lock.acquired is True


# Tests for Cache Patterns


class TestCachePatterns:
    """Test caching patterns."""

    @pytest.mark.asyncio
    async def test_cache_aside_pattern(self):
        """Test cache-aside pattern."""
        cache = MemoryCache()
        data_source = TestDataSource()
        data_source.data = {"key1": {"value": 1}, "key2": {"value": 2}}

        pattern = CacheAsidePattern(
            cache=cache, data_source=data_source, default_ttl=timedelta(minutes=5)
        )

        # First access - cache miss, load from source
        result = await pattern.get("key1")
        assert result == {"value": 1}
        assert data_source.get_count == 1

        metrics = pattern.get_metrics()
        assert metrics["cache_misses"] == 1
        assert metrics["source_loads"] == 1

        # Second access - cache hit
        result = await pattern.get("key1")
        assert result == {"value": 1}
        assert data_source.get_count == 1  # No additional load

        metrics = pattern.get_metrics()
        assert metrics["cache_hits"] == 1

        # Test batch operations
        results = await pattern.get_many(["key1", "key2", "key3"])
        assert len(results) == 2  # key3 doesn't exist
        assert results["key1"] == {"value": 1}  # From cache
        assert results["key2"] == {"value": 2}  # From source

    @pytest.mark.asyncio
    async def test_write_through_pattern(self):
        """Test write-through pattern."""
        cache = MemoryCache()
        data_source = TestDataSource()

        pattern = WriteThroughPattern(cache=cache, data_source=data_source)

        # Save - should write to both cache and source
        await pattern.save("key1", {"value": 1})

        # Verify in cache
        assert await cache.get("key1") == {"value": 1}

        # Verify in source
        assert data_source.data["key1"] == {"value": 1}
        assert data_source.save_count == 1

        # Delete - should delete from both
        await pattern.delete("key1")
        assert await cache.get("key1") is None
        assert "key1" not in data_source.data

    @pytest.mark.asyncio
    async def test_write_behind_pattern(self):
        """Test write-behind pattern."""
        cache = MemoryCache()
        data_source = TestDataSource()

        pattern = WriteBehindPattern(
            cache=cache, data_source=data_source, batch_size=2, flush_interval=0.1
        )

        await pattern.start()

        try:
            # Save - should write to cache immediately
            await pattern.save("key1", {"value": 1})
            assert await cache.get("key1") == {"value": 1}
            assert data_source.save_count == 0  # Not written to source yet

            # Add another to trigger batch flush
            await pattern.save("key2", {"value": 2})
            await asyncio.sleep(0.05)  # Allow flush
            assert data_source.save_count == 2

            # Test periodic flush
            await pattern.save("key3", {"value": 3})
            await asyncio.sleep(0.2)  # Wait for flush interval
            assert data_source.save_count == 3

        finally:
            await pattern.stop()

    @pytest.mark.asyncio
    async def test_cache_stampede_prevention(self):
        """Test cache stampede prevention."""
        cache = MemoryCache()
        stampede = CacheStampede(cache)

        call_count = 0

        async def slow_loader():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return {"loaded": True}

        # Launch multiple concurrent requests
        tasks = [stampede.get_or_load("key1", slow_loader) for _ in range(5)]

        results = await asyncio.gather(*tasks)

        # All should get the same result
        assert all(r == {"loaded": True} for r in results)

        # But loader should only be called once
        assert call_count == 1


# Tests for Invalidation Strategies


class TestInvalidationStrategies:
    """Test cache invalidation strategies."""

    @pytest.mark.asyncio
    async def test_immediate_invalidation(self):
        """Test immediate invalidation strategy."""
        cache = MemoryCache()
        invalidator = SmartInvalidator(cache)

        # Set up test data
        await cache.set("user:1", {"name": "Alice"})
        await cache.set("user:2", {"name": "Bob"})
        await cache.set("post:1:user:1", {"title": "Post 1"})

        # Add invalidation rule
        rule = InvalidationRule(
            event_type="user_updated",
            strategy=InvalidationStrategy.IMMEDIATE,
            key_pattern="user:{user_id}",
        )
        invalidator.add_rule(rule)

        # Trigger event
        invalidated = await invalidator.handle_event("user_updated", {"user_id": "1"})

        assert invalidated == 1
        assert await cache.get("user:1") is None
        assert await cache.get("user:2") == {"name": "Bob"}  # Not affected

    @pytest.mark.asyncio
    async def test_pattern_invalidation(self):
        """Test pattern-based invalidation."""
        cache = MemoryCache()

        # Mock list_keys method
        cache.list_keys = lambda: ["user:1", "user:2", "post:1", "post:2"]

        invalidator = SmartInvalidator(cache)

        # Set up test data
        await cache.set("user:1", {"name": "Alice"})
        await cache.set("user:2", {"name": "Bob"})
        await cache.set("post:1", {"title": "Post 1"})
        await cache.set("post:2", {"title": "Post 2"})

        # Add pattern rule
        rule = InvalidationRule(
            event_type="users_cleared",
            strategy=InvalidationStrategy.PATTERN,
            key_pattern="user:*",
        )
        invalidator.add_rule(rule)

        # Trigger event
        invalidated = await invalidator.handle_event("users_cleared", {})

        assert invalidated == 2
        assert await cache.get("user:1") is None
        assert await cache.get("user:2") is None
        assert await cache.get("post:1") == {"title": "Post 1"}  # Not affected

    @pytest.mark.asyncio
    async def test_conditional_invalidation(self):
        """Test conditional invalidation."""
        cache = MemoryCache()
        invalidator = SmartInvalidator(cache)

        # Set up test data
        await cache.set("premium:user:1", {"tier": "premium"})
        await cache.set("basic:user:2", {"tier": "basic"})

        # Add conditional rule
        rule = InvalidationRule(
            event_type="subscription_changed",
            strategy=InvalidationStrategy.IMMEDIATE,
            key_pattern="{tier}:user:{user_id}",
            condition=lambda data: data.get("tier") == "premium",
        )
        invalidator.add_rule(rule)

        # Trigger for premium user
        await invalidator.handle_event(
            "subscription_changed", {"user_id": "1", "tier": "premium"}
        )
        assert await cache.get("premium:user:1") is None

        # Trigger for basic user (should not invalidate due to condition)
        await invalidator.handle_event(
            "subscription_changed", {"user_id": "2", "tier": "basic"}
        )
        assert await cache.get("basic:user:2") == {"tier": "basic"}


# Tests for Cache Warming


class TestCacheWarming:
    """Test cache warming strategies."""

    @pytest.mark.asyncio
    async def test_basic_warming(self):
        """Test basic cache warming."""
        cache = MemoryCache()
        warmer = CacheWarmer(cache)

        # Add warming task
        async def load_critical_data(cache):
            await cache.set("config:app", {"version": "1.0"})
            await cache.set("config:features", {"enabled": ["a", "b"]})
            return 2  # Number of entries warmed

        warmer.add_task(name="critical_config", loader=load_critical_data, priority=10)

        # Execute warming
        results = await warmer.warm_up()

        assert results["tasks_executed"] == 1
        assert results["entries_loaded"] == 2
        assert await cache.get("config:app") == {"version": "1.0"}

    @pytest.mark.asyncio
    async def test_warming_with_dependencies(self):
        """Test warming with task dependencies."""
        cache = MemoryCache()
        warmer = CacheWarmer(cache)

        execution_order = []

        async def load_users(cache):
            execution_order.append("users")
            await cache.set("users:count", 100)
            return 1

        async def load_posts(cache):
            execution_order.append("posts")
            # Depends on users being loaded
            count = await cache.get("users:count")
            if count:
                await cache.set("posts:count", count * 10)
                return 1
            return 0

        # Add tasks with dependencies
        warmer.add_task("users", load_users, priority=5)
        warmer.add_task("posts", load_posts, priority=10, depends_on=["users"])

        # Execute warming
        results = await warmer.warm_up()

        assert results["tasks_executed"] == 2
        assert execution_order == ["users", "posts"]  # Correct order
        assert await cache.get("posts:count") == 1000

    @pytest.mark.asyncio
    async def test_frequently_accessed_warming(self):
        """Test warming frequently accessed keys."""
        cache = MemoryCache()

        # Simulate access log
        access_log = [
            "user:1",
            "user:1",
            "user:1",  # 3 times
            "user:2",
            "user:2",  # 2 times
            "user:3",  # 1 time
            "post:1",
            "post:1",  # 2 times
        ]

        # Data source
        async def load_data(key):
            return {"id": key.split(":")[1]}

        # Warm cache
        warmed = await warm_frequently_accessed(cache, access_log, load_data, top_n=2)

        assert warmed == 2
        assert await cache.get("user:1") == {"id": "1"}  # Most frequent
        assert await cache.get("user:2") == {"id": "2"}  # Second most
        assert await cache.get("user:3") is None  # Not in top 2
