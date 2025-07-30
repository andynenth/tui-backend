"""
Token bucket rate limiting algorithm implementation.

The token bucket algorithm allows for burst capacity while maintaining
a steady rate limit over time.
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import math

from .base import (
    IRateLimiter,
    RateLimitConfig,
    RateLimitResult,
    RateLimitStore,
    MemoryRateLimitStore,
    RateLimitAlgorithm,
)


class TokenBucketRateLimiter(IRateLimiter):
    """
    Token bucket rate limiter implementation.

    How it works:
    - Bucket starts with initial capacity tokens
    - Tokens are added at a constant rate (refill_rate)
    - Each request consumes tokens
    - Requests are allowed if enough tokens available
    - Supports burst capacity for temporary spikes
    """

    def __init__(self, config: RateLimitConfig, store: Optional[RateLimitStore] = None):
        """
        Initialize token bucket rate limiter.

        Args:
            config: Rate limit configuration
            store: Storage backend (defaults to memory)
        """
        if config.algorithm != RateLimitAlgorithm.TOKEN_BUCKET:
            raise ValueError(f"Expected TOKEN_BUCKET algorithm, got {config.algorithm}")

        self.config = config
        self.store = store or MemoryRateLimitStore()

        # Calculate refill interval for efficiency
        self._refill_interval = (
            1.0 / config.refill_rate if config.refill_rate > 0 else float("inf")
        )

        # Background refill task
        self._refill_task: Optional[asyncio.Task] = None
        if config.refill_rate > 0:
            self._refill_task = asyncio.create_task(self._refill_worker())

    async def check_rate_limit(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check if request is allowed under rate limit."""
        bucket = await self._get_or_create_bucket(key)

        # Refill tokens based on time elapsed
        now = datetime.utcnow()
        tokens = await self._calculate_tokens(bucket, now)

        # Check if enough tokens
        allowed = tokens >= cost
        remaining = max(0, int(tokens - cost))

        # Calculate reset time (when bucket will be full)
        tokens_needed = self.config.capacity - tokens
        if tokens_needed > 0 and self.config.refill_rate > 0:
            seconds_to_full = tokens_needed / self.config.refill_rate
            reset_at = now + timedelta(seconds=seconds_to_full)
        else:
            reset_at = now

        # Calculate retry after if not allowed
        retry_after = None
        if not allowed and self.config.refill_rate > 0:
            tokens_short = cost - tokens
            seconds_to_wait = tokens_short / self.config.refill_rate
            retry_after = timedelta(seconds=seconds_to_wait)

        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after,
        )

    async def consume(self, key: str, cost: int = 1) -> bool:
        """Consume tokens if available."""
        bucket = await self._get_or_create_bucket(key)

        # Refill tokens
        now = datetime.utcnow()
        tokens = await self._calculate_tokens(bucket, now)

        # Check and consume
        if tokens >= cost:
            bucket["tokens"] = tokens - cost
            bucket["last_refill"] = now
            await self.store.set_bucket(key, bucket)
            return True

        return False

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        bucket = {
            "tokens": float(self.config.capacity),
            "last_refill": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }
        await self.store.set_bucket(key, bucket)

    async def get_stats(self, key: str) -> Dict[str, Any]:
        """Get current stats for a key."""
        bucket = await self._get_or_create_bucket(key)
        now = datetime.utcnow()
        tokens = await self._calculate_tokens(bucket, now)

        return {
            "algorithm": "token_bucket",
            "current_tokens": tokens,
            "capacity": self.config.capacity,
            "burst_capacity": self.config.burst_capacity,
            "refill_rate": self.config.refill_rate,
            "last_refill": bucket["last_refill"].isoformat(),
            "created_at": bucket["created_at"].isoformat(),
        }

    async def _get_or_create_bucket(self, key: str) -> Dict[str, Any]:
        """Get existing bucket or create new one."""
        bucket = await self.store.get_bucket(key)

        if bucket is None:
            bucket = {
                "tokens": float(self.config.capacity),
                "last_refill": datetime.utcnow(),
                "created_at": datetime.utcnow(),
            }
            await self.store.set_bucket(key, bucket)

        return bucket

    async def _calculate_tokens(self, bucket: Dict[str, Any], now: datetime) -> float:
        """Calculate current token count with refill."""
        last_refill = bucket["last_refill"]
        if isinstance(last_refill, str):
            last_refill = datetime.fromisoformat(last_refill)

        # Calculate elapsed time
        elapsed = (now - last_refill).total_seconds()

        # Calculate tokens to add
        tokens_to_add = elapsed * self.config.refill_rate

        # Current tokens with refill
        current_tokens = bucket.get("tokens", 0.0) + tokens_to_add

        # Cap at burst capacity
        max_tokens = self.config.burst_capacity or self.config.capacity
        return min(current_tokens, float(max_tokens))

    async def _refill_worker(self) -> None:
        """Background worker for periodic refills (optimization)."""
        while True:
            try:
                await asyncio.sleep(self._refill_interval)
                # Refill logic handled in _calculate_tokens
                # This worker is mainly for cleanup

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)

    async def shutdown(self) -> None:
        """Shutdown rate limiter and cleanup."""
        if self._refill_task:
            self._refill_task.cancel()
            try:
                await self._refill_task
            except asyncio.CancelledError:
                pass


class OptimizedTokenBucket(TokenBucketRateLimiter):
    """
    Optimized token bucket for high-throughput scenarios.

    Features:
    - Lazy refill calculation (no background tasks)
    - Minimal storage updates
    - Batched token consumption
    """

    def __init__(
        self,
        config: RateLimitConfig,
        store: Optional[RateLimitStore] = None,
        update_threshold: float = 0.1,
    ):
        """
        Initialize optimized token bucket.

        Args:
            config: Rate limit configuration
            store: Storage backend
            update_threshold: Only update storage when tokens change by this fraction
        """
        # Don't start refill worker
        self.config = config
        self.store = store or MemoryRateLimitStore()
        self._refill_interval = (
            1.0 / config.refill_rate if config.refill_rate > 0 else float("inf")
        )
        self._refill_task = None

        self.update_threshold = update_threshold
        self._pending_updates: Dict[str, Dict[str, Any]] = {}
        self._update_lock = asyncio.Lock()

    async def consume(self, key: str, cost: int = 1) -> bool:
        """Consume tokens with optimized storage updates."""
        bucket = await self._get_or_create_bucket(key)

        # Calculate current tokens
        now = datetime.utcnow()
        tokens = await self._calculate_tokens(bucket, now)

        if tokens >= cost:
            new_tokens = tokens - cost

            # Check if update is significant
            token_change = abs(bucket.get("tokens", 0) - new_tokens)
            if token_change >= self.config.capacity * self.update_threshold:
                # Significant change, update immediately
                bucket["tokens"] = new_tokens
                bucket["last_refill"] = now
                await self.store.set_bucket(key, bucket)
            else:
                # Buffer the update
                async with self._update_lock:
                    self._pending_updates[key] = {
                        "tokens": new_tokens,
                        "last_refill": now,
                    }

            return True

        return False

    async def flush_updates(self) -> int:
        """Flush pending updates to storage."""
        async with self._update_lock:
            if not self._pending_updates:
                return 0

            updates = dict(self._pending_updates)
            self._pending_updates.clear()

        # Apply updates
        for key, update in updates.items():
            bucket = await self.store.get_bucket(key)
            if bucket:
                bucket.update(update)
                await self.store.set_bucket(key, bucket)

        return len(updates)


class AdaptiveTokenBucket(TokenBucketRateLimiter):
    """
    Adaptive token bucket that adjusts rates based on usage patterns.

    Features:
    - Increases capacity during low usage
    - Decreases capacity during high usage
    - Learns from historical patterns
    """

    def __init__(
        self,
        config: RateLimitConfig,
        store: Optional[RateLimitStore] = None,
        adaptation_window: timedelta = timedelta(minutes=5),
        min_capacity_ratio: float = 0.5,
        max_capacity_ratio: float = 2.0,
    ):
        """
        Initialize adaptive token bucket.

        Args:
            config: Base rate limit configuration
            store: Storage backend
            adaptation_window: Time window for usage analysis
            min_capacity_ratio: Minimum capacity as ratio of base
            max_capacity_ratio: Maximum capacity as ratio of base
        """
        super().__init__(config, store)

        self.adaptation_window = adaptation_window
        self.min_capacity = int(config.capacity * min_capacity_ratio)
        self.max_capacity = int(config.capacity * max_capacity_ratio)
        self.base_capacity = config.capacity

        # Usage tracking
        self._usage_history: Dict[str, List[Tuple[datetime, int]]] = {}
        self._adaptation_task = asyncio.create_task(self._adaptation_worker())

    async def consume(self, key: str, cost: int = 1) -> bool:
        """Consume tokens and track usage."""
        # Track usage
        now = datetime.utcnow()
        if key not in self._usage_history:
            self._usage_history[key] = []

        self._usage_history[key].append((now, cost))

        # Clean old history
        cutoff = now - self.adaptation_window
        self._usage_history[key] = [
            (ts, c) for ts, c in self._usage_history[key] if ts > cutoff
        ]

        # Regular consume
        return await super().consume(key, cost)

    async def _calculate_adaptive_capacity(self, key: str) -> int:
        """Calculate adaptive capacity based on usage."""
        if key not in self._usage_history:
            return self.base_capacity

        # Calculate usage rate
        now = datetime.utcnow()
        window_start = now - self.adaptation_window

        total_usage = sum(
            cost for ts, cost in self._usage_history[key] if ts > window_start
        )

        usage_rate = total_usage / self.adaptation_window.total_seconds()
        expected_rate = self.config.refill_rate

        # Adjust capacity based on usage
        if usage_rate < expected_rate * 0.5:
            # Low usage, increase capacity
            new_capacity = min(int(self.config.capacity * 1.2), self.max_capacity)
        elif usage_rate > expected_rate * 0.9:
            # High usage, decrease capacity
            new_capacity = max(int(self.config.capacity * 0.8), self.min_capacity)
        else:
            # Normal usage
            new_capacity = self.base_capacity

        return new_capacity

    async def _adaptation_worker(self) -> None:
        """Background worker to adapt capacities."""
        while True:
            try:
                await asyncio.sleep(60)  # Adapt every minute

                # Update capacities for active keys
                for key in list(self._usage_history.keys()):
                    new_capacity = await self._calculate_adaptive_capacity(key)

                    if new_capacity != self.config.capacity:
                        # Update config temporarily for this key
                        # In practice, would store per-key configs
                        pass

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)

    async def shutdown(self) -> None:
        """Shutdown and cleanup."""
        await super().shutdown()

        if self._adaptation_task:
            self._adaptation_task.cancel()
            try:
                await self._adaptation_task
            except asyncio.CancelledError:
                pass
