"""
Distributed rate limiting implementation.

Provides rate limiting across multiple application instances using
shared storage backends like Redis.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import hashlib

from .base import (
    IRateLimiter,
    IDistributedRateLimiter,
    RateLimitConfig,
    RateLimitResult,
    RateLimitStore,
    RateLimitAlgorithm,
)
from .token_bucket import TokenBucketRateLimiter
from .sliding_window import SlidingWindowRateLimiter


class RedisRateLimitStore(RateLimitStore):
    """Rate limit store implementation using Redis."""

    def __init__(self, redis_client: Any, key_prefix: str = "ratelimit"):
        """
        Initialize Redis store.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for all keys
        """
        self.redis = redis_client
        self.key_prefix = key_prefix

    def _make_key(self, key: str) -> str:
        """Create full Redis key."""
        return f"{self.key_prefix}:{key}"

    async def get_bucket(self, key: str) -> Optional[Dict[str, Any]]:
        """Get bucket data from Redis."""
        redis_key = self._make_key(f"bucket:{key}")
        data = await self.redis.get(redis_key)

        if data:
            bucket = json.loads(data)
            # Convert timestamps
            if "last_refill" in bucket:
                bucket["last_refill"] = datetime.fromisoformat(bucket["last_refill"])
            if "created_at" in bucket:
                bucket["created_at"] = datetime.fromisoformat(bucket["created_at"])
            return bucket

        return None

    async def set_bucket(
        self, key: str, data: Dict[str, Any], ttl: Optional[timedelta] = None
    ) -> None:
        """Set bucket data in Redis."""
        redis_key = self._make_key(f"bucket:{key}")

        # Convert timestamps for JSON
        bucket_data = data.copy()
        if "last_refill" in bucket_data and isinstance(
            bucket_data["last_refill"], datetime
        ):
            bucket_data["last_refill"] = bucket_data["last_refill"].isoformat()
        if "created_at" in bucket_data and isinstance(
            bucket_data["created_at"], datetime
        ):
            bucket_data["created_at"] = bucket_data["created_at"].isoformat()

        serialized = json.dumps(bucket_data)

        if ttl:
            await self.redis.set(redis_key, serialized, ex=int(ttl.total_seconds()))
        else:
            await self.redis.set(redis_key, serialized)

    async def increment_counter(self, key: str, increment: int = 1) -> int:
        """Atomically increment counter in Redis."""
        redis_key = self._make_key(f"counter:{key}")

        if increment == 1:
            return await self.redis.incr(redis_key)
        else:
            return await self.redis.incrby(redis_key, increment)

    async def add_to_window(
        self, key: str, timestamp: datetime, count: int = 1
    ) -> None:
        """Add entry to sliding window using Redis sorted set."""
        redis_key = self._make_key(f"window:{key}")

        # Use timestamp as score
        score = timestamp.timestamp()

        # Create unique member (timestamp + random)
        member = f"{score}:{count}:{hash(timestamp)}"

        await self.redis.zadd(redis_key, {member: score})

        # Set expiry on the key
        await self.redis.expire(redis_key, 3600)  # 1 hour expiry

    async def get_window_sum(self, key: str, start: datetime, end: datetime) -> int:
        """Get sum of entries in time window from Redis."""
        redis_key = self._make_key(f"window:{key}")

        # Get entries in score range
        start_score = start.timestamp()
        end_score = end.timestamp()

        entries = await self.redis.zrangebyscore(
            redis_key, start_score, end_score, withscores=False
        )

        # Sum counts from member format
        total = 0
        for entry in entries:
            try:
                # Extract count from member format
                parts = entry.split(":")
                if len(parts) >= 2:
                    total += int(parts[1])
            except (ValueError, IndexError):
                continue

        return total

    async def cleanup_old_entries(self, before: datetime) -> int:
        """Remove old entries from Redis."""
        # Find all window keys
        pattern = self._make_key("window:*")
        keys = await self.redis.keys(pattern)

        removed = 0
        before_score = before.timestamp()

        for key in keys:
            # Remove old entries from sorted set
            count = await self.redis.zremrangebyscore(key, "-inf", before_score)
            removed += count

        return removed


class DistributedTokenBucket(TokenBucketRateLimiter, IDistributedRateLimiter):
    """
    Distributed token bucket implementation.

    Uses Redis or similar for shared state across instances.
    """

    def __init__(
        self,
        config: RateLimitConfig,
        store: RateLimitStore,
        instance_id: Optional[str] = None,
    ):
        """
        Initialize distributed token bucket.

        Args:
            config: Rate limit configuration
            store: Distributed storage backend
            instance_id: Unique identifier for this instance
        """
        super().__init__(config, store)
        self.instance_id = instance_id or self._generate_instance_id()

        # Local cache for performance
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(seconds=1)  # Short TTL for consistency

    async def consume(self, key: str, cost: int = 1) -> bool:
        """
        Consume tokens with distributed coordination.

        Uses optimistic concurrency control for performance.
        """
        # Try local cache first for read
        cached = self._get_cached_bucket(key)
        if cached and cached["tokens"] >= cost:
            # Optimistically consume from cache
            cached["tokens"] -= cost

            # Update distributed state
            success = await self._distributed_consume(key, cost)
            if not success:
                # Rollback cache
                cached["tokens"] += cost
                self._invalidate_cache(key)
            return success

        # Fallback to distributed check
        return await super().consume(key, cost)

    async def _distributed_consume(self, key: str, cost: int) -> bool:
        """Consume tokens with distributed locking."""
        # Simplified: In production, use Redis scripts or transactions
        bucket = await self._get_or_create_bucket(key)

        now = datetime.utcnow()
        tokens = await self._calculate_tokens(bucket, now)

        if tokens >= cost:
            bucket["tokens"] = tokens - cost
            bucket["last_refill"] = now
            await self.store.set_bucket(key, bucket)
            return True

        return False

    async def sync_state(self) -> None:
        """Synchronize state across instances."""
        # Clear local cache to force refresh
        self._local_cache.clear()

    async def get_global_stats(self) -> Dict[str, Any]:
        """Get aggregated stats across all instances."""
        # This would aggregate from all instances
        # For now, return local stats
        return {
            "instance_id": self.instance_id,
            "cached_keys": len(self._local_cache),
            "algorithm": "distributed_token_bucket",
        }

    def _get_cached_bucket(self, key: str) -> Optional[Dict[str, Any]]:
        """Get bucket from local cache if fresh."""
        if key in self._local_cache:
            cached = self._local_cache[key]
            if datetime.utcnow() - cached["cached_at"] < self._cache_ttl:
                return cached["bucket"]
        return None

    def _cache_bucket(self, key: str, bucket: Dict[str, Any]) -> None:
        """Cache bucket locally."""
        self._local_cache[key] = {
            "bucket": bucket.copy(),
            "cached_at": datetime.utcnow(),
        }

    def _invalidate_cache(self, key: str) -> None:
        """Invalidate local cache for key."""
        self._local_cache.pop(key, None)

    def _generate_instance_id(self) -> str:
        """Generate unique instance ID."""
        import socket
        import os

        hostname = socket.gethostname()
        pid = os.getpid()
        return hashlib.md5(f"{hostname}:{pid}".encode()).hexdigest()[:8]


class DistributedSlidingWindow(SlidingWindowRateLimiter, IDistributedRateLimiter):
    """
    Distributed sliding window implementation.

    Uses shared storage for window entries.
    """

    def __init__(
        self, config: RateLimitConfig, store: RateLimitStore, sync_interval: float = 1.0
    ):
        """
        Initialize distributed sliding window.

        Args:
            config: Rate limit configuration
            store: Distributed storage backend
            sync_interval: How often to sync with distributed state
        """
        super().__init__(config, store)
        self.sync_interval = sync_interval

        # Local buffer for batching
        self._pending_writes: Dict[str, List[Tuple[datetime, int]]] = {}
        self._write_lock = asyncio.Lock()

        # Sync task
        self._sync_task = asyncio.create_task(self._sync_worker())

    async def consume(self, key: str, cost: int = 1) -> bool:
        """Consume with buffered writes."""
        # Check distributed state
        result = await self.check_rate_limit(key, cost)

        if result.allowed:
            # Buffer the write
            async with self._write_lock:
                if key not in self._pending_writes:
                    self._pending_writes[key] = []

                self._pending_writes[key].append((datetime.utcnow(), cost))

            # Async flush if buffer is large
            if len(self._pending_writes[key]) > 10:
                asyncio.create_task(self._flush_writes(key))

            return True

        return False

    async def sync_state(self) -> None:
        """Synchronize state across instances."""
        await self._flush_all_writes()

    async def get_global_stats(self) -> Dict[str, Any]:
        """Get aggregated stats across all instances."""
        await self._flush_all_writes()

        # Count total entries across all keys
        # This is expensive and should be cached
        total_entries = 0
        active_keys = 0

        # In production, use Redis SCAN instead
        # For now, return estimates
        return {
            "algorithm": "distributed_sliding_window",
            "estimated_active_keys": active_keys,
            "estimated_total_entries": total_entries,
            "pending_writes": sum(
                len(writes) for writes in self._pending_writes.values()
            ),
        }

    async def _sync_worker(self) -> None:
        """Background worker to sync writes."""
        while True:
            try:
                await asyncio.sleep(self.sync_interval)
                await self._flush_all_writes()

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)

    async def _flush_writes(self, key: str) -> None:
        """Flush pending writes for a key."""
        async with self._write_lock:
            if key not in self._pending_writes:
                return

            writes = self._pending_writes.pop(key)

        # Batch write to distributed store
        for timestamp, count in writes:
            await self.store.add_to_window(key, timestamp, count)

    async def _flush_all_writes(self) -> None:
        """Flush all pending writes."""
        async with self._write_lock:
            keys = list(self._pending_writes.keys())

        for key in keys:
            await self._flush_writes(key)

    async def shutdown(self) -> None:
        """Shutdown and flush pending writes."""
        await super().shutdown()

        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush_all_writes()


class ConsistentHashRateLimiter(IDistributedRateLimiter):
    """
    Distributed rate limiter using consistent hashing.

    Distributes rate limit state across multiple nodes for scalability.
    """

    def __init__(self, nodes: List[IRateLimiter], virtual_nodes: int = 150):
        """
        Initialize consistent hash rate limiter.

        Args:
            nodes: List of rate limiter nodes
            virtual_nodes: Number of virtual nodes per physical node
        """
        self.nodes = nodes
        self.virtual_nodes = virtual_nodes

        # Build hash ring
        self._ring: Dict[int, IRateLimiter] = {}
        self._sorted_keys: List[int] = []
        self._build_ring()

    def _build_ring(self) -> None:
        """Build consistent hash ring."""
        for i, node in enumerate(self.nodes):
            for j in range(self.virtual_nodes):
                key = self._hash(f"node{i}:vnode{j}")
                self._ring[key] = node

        self._sorted_keys = sorted(self._ring.keys())

    def _hash(self, key: str) -> int:
        """Hash key to integer."""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def _get_node(self, key: str) -> IRateLimiter:
        """Get node responsible for key."""
        if not self._ring:
            raise ValueError("No nodes available")

        key_hash = self._hash(key)

        # Find first node with hash >= key_hash
        idx = 0
        for i, node_hash in enumerate(self._sorted_keys):
            if node_hash >= key_hash:
                idx = i
                break

        return self._ring[self._sorted_keys[idx]]

    async def check_rate_limit(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check rate limit on appropriate node."""
        node = self._get_node(key)
        return await node.check_rate_limit(key, cost)

    async def consume(self, key: str, cost: int = 1) -> bool:
        """Consume from appropriate node."""
        node = self._get_node(key)
        return await node.consume(key, cost)

    async def reset(self, key: str) -> None:
        """Reset on appropriate node."""
        node = self._get_node(key)
        await node.reset(key)

    async def get_stats(self, key: str) -> Dict[str, Any]:
        """Get stats from appropriate node."""
        node = self._get_node(key)
        stats = await node.get_stats(key)
        stats["node"] = self.nodes.index(node)
        return stats

    async def sync_state(self) -> None:
        """Sync all nodes."""
        tasks = []
        for node in self.nodes:
            if hasattr(node, "sync_state"):
                tasks.append(node.sync_state())

        if tasks:
            await asyncio.gather(*tasks)

    async def get_global_stats(self) -> Dict[str, Any]:
        """Get stats from all nodes."""
        all_stats = []

        for i, node in enumerate(self.nodes):
            if hasattr(node, "get_global_stats"):
                stats = await node.get_global_stats()
            else:
                stats = {"node_id": i}

            all_stats.append(stats)

        return {
            "algorithm": "consistent_hash",
            "total_nodes": len(self.nodes),
            "virtual_nodes": self.virtual_nodes,
            "node_stats": all_stats,
        }
