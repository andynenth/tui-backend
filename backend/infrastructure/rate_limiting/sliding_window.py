"""
Sliding window rate limiting algorithm implementation.

The sliding window algorithm provides more accurate rate limiting by
tracking the exact timestamp of each request.
"""

import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from collections import deque
import bisect

from .base import (
    IRateLimiter,
    RateLimitConfig,
    RateLimitResult,
    RateLimitStore,
    MemoryRateLimitStore,
    RateLimitAlgorithm,
)


class SlidingWindowRateLimiter(IRateLimiter):
    """
    Sliding window rate limiter implementation.

    How it works:
    - Tracks exact timestamp of each request
    - Counts requests within the sliding time window
    - More accurate than fixed window but uses more memory
    - Provides smooth rate limiting without window boundaries
    """

    def __init__(self, config: RateLimitConfig, store: Optional[RateLimitStore] = None):
        """
        Initialize sliding window rate limiter.

        Args:
            config: Rate limit configuration
            store: Storage backend (defaults to memory)
        """
        if config.algorithm != RateLimitAlgorithm.SLIDING_WINDOW:
            raise ValueError(
                f"Expected SLIDING_WINDOW algorithm, got {config.algorithm}"
            )

        self.config = config
        self.store = store or MemoryRateLimitStore()

        # Cleanup task for old entries
        self._cleanup_task = asyncio.create_task(self._cleanup_worker())

    async def check_rate_limit(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check if request is allowed under rate limit."""
        now = datetime.utcnow()
        window_start = now - self.config.window_size

        # Get request count in window
        count = await self.store.get_window_sum(key, window_start, now)

        # Check if adding this request would exceed limit
        allowed = (count + cost) <= self.config.capacity
        remaining = max(0, self.config.capacity - count - (cost if not allowed else 0))

        # Reset time is when the oldest request in window expires
        reset_at = now + self.config.window_size

        # Calculate retry after if not allowed
        retry_after = None
        if not allowed:
            # Find when enough old requests expire
            # Simplified: assume uniform distribution
            requests_to_expire = (count + cost) - self.config.capacity
            retry_seconds = (
                requests_to_expire / count
            ) * self.config.window_size.total_seconds()
            retry_after = timedelta(seconds=retry_seconds)

        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after,
        )

    async def consume(self, key: str, cost: int = 1) -> bool:
        """Consume from rate limit if available."""
        result = await self.check_rate_limit(key, cost)

        if result.allowed:
            # Add request to window
            now = datetime.utcnow()
            await self.store.add_to_window(key, now, cost)
            return True

        return False

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        # Clear window by setting to empty
        # Implementation depends on store
        now = datetime.utcnow()
        window_start = now - self.config.window_size - timedelta(seconds=1)
        await self.store.cleanup_old_entries(window_start)

    async def get_stats(self, key: str) -> Dict[str, Any]:
        """Get current stats for a key."""
        now = datetime.utcnow()
        window_start = now - self.config.window_size

        count = await self.store.get_window_sum(key, window_start, now)

        return {
            "algorithm": "sliding_window",
            "current_count": count,
            "capacity": self.config.capacity,
            "window_size": self.config.window_size.total_seconds(),
            "window_start": window_start.isoformat(),
            "window_end": now.isoformat(),
        }

    async def _cleanup_worker(self) -> None:
        """Background worker to clean up old entries."""
        cleanup_interval = max(60, self.config.window_size.total_seconds() / 10)

        while True:
            try:
                await asyncio.sleep(cleanup_interval)

                # Clean entries older than window
                cutoff = (
                    datetime.utcnow() - self.config.window_size - timedelta(minutes=1)
                )
                removed = await self.store.cleanup_old_entries(cutoff)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)

    async def shutdown(self) -> None:
        """Shutdown rate limiter and cleanup."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class OptimizedSlidingWindow(IRateLimiter):
    """
    Optimized sliding window using circular buffer.

    Features:
    - Fixed memory usage
    - O(1) operations for most cases
    - Approximate counting for efficiency
    """

    def __init__(
        self,
        config: RateLimitConfig,
        store: Optional[RateLimitStore] = None,
        buckets: int = 60,
    ):
        """
        Initialize optimized sliding window.

        Args:
            config: Rate limit configuration
            store: Storage backend
            buckets: Number of sub-windows for approximation
        """
        self.config = config
        self.store = store or MemoryRateLimitStore()
        self.buckets = buckets

        # Calculate bucket duration
        self.bucket_duration = config.window_size.total_seconds() / buckets

        # In-memory circular buffers per key
        self._buffers: Dict[str, CircularBuffer] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check rate limit using circular buffer."""
        async with self._lock:
            buffer = self._get_or_create_buffer(key)

            now = datetime.utcnow()
            count = buffer.get_count(now)

            allowed = (count + cost) <= self.config.capacity
            remaining = max(
                0, self.config.capacity - count - (cost if not allowed else 0)
            )

            reset_at = now + self.config.window_size

            retry_after = None
            if not allowed:
                # Estimate retry time
                overflow = (count + cost) - self.config.capacity
                retry_buckets = overflow / (count / self.buckets) if count > 0 else 1
                retry_after = timedelta(seconds=retry_buckets * self.bucket_duration)

            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
            )

    async def consume(self, key: str, cost: int = 1) -> bool:
        """Consume using circular buffer."""
        async with self._lock:
            buffer = self._get_or_create_buffer(key)

            now = datetime.utcnow()
            count = buffer.get_count(now)

            if (count + cost) <= self.config.capacity:
                buffer.add(now, cost)
                return True

            return False

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        async with self._lock:
            if key in self._buffers:
                del self._buffers[key]

    async def get_stats(self, key: str) -> Dict[str, Any]:
        """Get current stats for a key."""
        async with self._lock:
            buffer = self._get_or_create_buffer(key)
            now = datetime.utcnow()
            count = buffer.get_count(now)

            return {
                "algorithm": "sliding_window_optimized",
                "current_count": count,
                "capacity": self.config.capacity,
                "window_size": self.config.window_size.total_seconds(),
                "buckets": self.buckets,
                "bucket_duration": self.bucket_duration,
            }

    def _get_or_create_buffer(self, key: str) -> "CircularBuffer":
        """Get or create circular buffer for key."""
        if key not in self._buffers:
            self._buffers[key] = CircularBuffer(self.buckets, self.bucket_duration)
        return self._buffers[key]


class CircularBuffer:
    """Circular buffer for efficient sliding window."""

    def __init__(self, size: int, bucket_duration: float):
        self.size = size
        self.bucket_duration = bucket_duration
        self.buffer = [0] * size
        self.last_update = datetime.utcnow()
        self.current_bucket = 0

    def add(self, timestamp: datetime, count: int) -> None:
        """Add count to appropriate bucket."""
        self._rotate_to(timestamp)
        self.buffer[self.current_bucket] += count

    def get_count(self, timestamp: datetime) -> int:
        """Get total count in window."""
        self._rotate_to(timestamp)
        return sum(self.buffer)

    def _rotate_to(self, timestamp: datetime) -> None:
        """Rotate buffer to current time."""
        elapsed = (timestamp - self.last_update).total_seconds()
        buckets_passed = int(elapsed / self.bucket_duration)

        if buckets_passed > 0:
            # Clear passed buckets
            for i in range(min(buckets_passed, self.size)):
                self.current_bucket = (self.current_bucket + 1) % self.size
                self.buffer[self.current_bucket] = 0

            self.last_update = timestamp


class SlidingWindowLog(IRateLimiter):
    """
    Sliding window log implementation with exact timestamps.

    Most accurate but most memory intensive approach.
    """

    def __init__(self, config: RateLimitConfig, store: Optional[RateLimitStore] = None):
        """Initialize sliding window log."""
        self.config = config
        self.store = store or MemoryRateLimitStore()

        # In-memory logs for performance
        self._logs: Dict[str, deque] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check rate limit using exact log."""
        async with self._lock:
            log = self._get_or_create_log(key)

            now = datetime.utcnow()
            window_start = now - self.config.window_size

            # Remove old entries
            while log and log[0][0] < window_start:
                log.popleft()

            # Count requests in window
            count = sum(c for _, c in log)

            allowed = (count + cost) <= self.config.capacity
            remaining = max(
                0, self.config.capacity - count - (cost if not allowed else 0)
            )

            # Calculate exact reset time
            if log:
                reset_at = log[0][0] + self.config.window_size
            else:
                reset_at = now + self.config.window_size

            # Calculate exact retry time
            retry_after = None
            if not allowed and log:
                # Find when enough requests expire
                cumulative = 0
                needed = (count + cost) - self.config.capacity

                for ts, c in log:
                    cumulative += c
                    if cumulative >= needed:
                        retry_after = ts + self.config.window_size - now
                        break

            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
            )

    async def consume(self, key: str, cost: int = 1) -> bool:
        """Consume from rate limit if available."""
        async with self._lock:
            result = await self.check_rate_limit(key, cost)

            if result.allowed:
                log = self._get_or_create_log(key)
                log.append((datetime.utcnow(), cost))
                return True

            return False

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        async with self._lock:
            if key in self._logs:
                self._logs[key].clear()

    async def get_stats(self, key: str) -> Dict[str, Any]:
        """Get current stats for a key."""
        async with self._lock:
            log = self._get_or_create_log(key)

            now = datetime.utcnow()
            window_start = now - self.config.window_size

            # Count current requests
            count = sum(c for ts, c in log if ts >= window_start)

            return {
                "algorithm": "sliding_window_log",
                "current_count": count,
                "capacity": self.config.capacity,
                "window_size": self.config.window_size.total_seconds(),
                "log_entries": len(log),
                "oldest_entry": log[0][0].isoformat() if log else None,
            }

    def _get_or_create_log(self, key: str) -> deque:
        """Get or create log for key."""
        if key not in self._logs:
            self._logs[key] = deque()
        return self._logs[key]
