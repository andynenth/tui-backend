"""
Common caching patterns implementation.

This module provides reusable patterns like cache-aside, write-through,
and write-behind for consistent caching strategies.
"""

import asyncio
from typing import TypeVar, Generic, Callable, Optional, Dict, Any, List, Set
from datetime import timedelta
from abc import ABC, abstractmethod
import hashlib
import json

from .base import ICache, CacheKeyBuilder, CacheInvalidator


T = TypeVar("T")


class IDataSource(ABC, Generic[T]):
    """Interface for data sources that can be cached."""

    @abstractmethod
    async def get(self, key: str) -> Optional[T]:
        """Get data from source."""
        pass

    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple items from source."""
        pass

    @abstractmethod
    async def save(self, key: str, value: T) -> None:
        """Save data to source."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete data from source."""
        pass


class CacheAsidePattern(Generic[T]):
    """
    Implements the cache-aside (lazy loading) pattern.

    1. Check cache for data
    2. If miss, load from data source
    3. Update cache with loaded data
    4. Return data
    """

    def __init__(
        self,
        cache: ICache[T],
        data_source: IDataSource[T],
        key_builder: Optional[CacheKeyBuilder] = None,
        default_ttl: Optional[timedelta] = None,
        tags_fn: Optional[Callable[[str, T], Set[str]]] = None,
    ):
        """
        Initialize cache-aside pattern.

        Args:
            cache: Cache implementation
            data_source: Data source implementation
            key_builder: Optional key builder for consistent keys
            default_ttl: Default TTL for cached items
            tags_fn: Function to generate tags for items
        """
        self.cache = cache
        self.data_source = data_source
        self.key_builder = key_builder or CacheKeyBuilder()
        self.default_ttl = default_ttl
        self.tags_fn = tags_fn

        # Metrics
        self._metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "source_loads": 0,
            "errors": 0,
        }

    async def get(self, key: str) -> Optional[T]:
        """Get item using cache-aside pattern."""
        cache_key = self.key_builder.build(key)

        # Try cache first
        cached_value = await self.cache.get(cache_key)
        if cached_value is not None:
            self._metrics["cache_hits"] += 1
            return cached_value

        self._metrics["cache_misses"] += 1

        # Load from source
        try:
            value = await self.data_source.get(key)
            self._metrics["source_loads"] += 1

            if value is not None:
                # Update cache
                tags = self.tags_fn(key, value) if self.tags_fn else None
                await self.cache.set(cache_key, value, ttl=self.default_ttl, tags=tags)

            return value

        except Exception as e:
            self._metrics["errors"] += 1
            raise

    async def get_many(self, keys: List[str]) -> Dict[str, T]:
        """Get multiple items using cache-aside pattern."""
        results = {}
        cache_keys = {key: self.key_builder.build(key) for key in keys}

        # Check cache for all keys
        cache_results = await self.cache.get_many(list(cache_keys.values()))

        # Separate hits and misses
        missing_keys = []
        for key, cache_key in cache_keys.items():
            if cache_key in cache_results:
                results[key] = cache_results[cache_key]
                self._metrics["cache_hits"] += 1
            else:
                missing_keys.append(key)
                self._metrics["cache_misses"] += 1

        # Load missing from source
        if missing_keys:
            try:
                source_results = await self.data_source.get_many(missing_keys)
                self._metrics["source_loads"] += len(source_results)

                # Update cache and results
                cache_updates = {}
                for key, value in source_results.items():
                    results[key] = value
                    cache_key = cache_keys[key]
                    cache_updates[cache_key] = value

                if cache_updates:
                    await self.cache.set_many(cache_updates, ttl=self.default_ttl)

            except Exception as e:
                self._metrics["errors"] += 1
                raise

        return results

    async def invalidate(self, key: str) -> None:
        """Invalidate cached item."""
        cache_key = self.key_builder.build(key)
        await self.cache.delete(cache_key)

    async def invalidate_many(self, keys: List[str]) -> None:
        """Invalidate multiple cached items."""
        cache_keys = [self.key_builder.build(key) for key in keys]
        await self.cache.delete_many(cache_keys)

    def get_metrics(self) -> Dict[str, Any]:
        """Get pattern metrics."""
        total_requests = self._metrics["cache_hits"] + self._metrics["cache_misses"]
        hit_rate = (
            self._metrics["cache_hits"] / total_requests if total_requests > 0 else 0
        )

        return {**self._metrics, "hit_rate": hit_rate, "total_requests": total_requests}


class WriteThroughPattern(Generic[T]):
    """
    Implements the write-through caching pattern.

    1. Write to cache and data source simultaneously
    2. Ensures cache is always consistent with source
    3. Higher write latency but better consistency
    """

    def __init__(
        self,
        cache: ICache[T],
        data_source: IDataSource[T],
        key_builder: Optional[CacheKeyBuilder] = None,
        default_ttl: Optional[timedelta] = None,
    ):
        self.cache = cache
        self.data_source = data_source
        self.key_builder = key_builder or CacheKeyBuilder()
        self.default_ttl = default_ttl

    async def save(self, key: str, value: T) -> None:
        """Save using write-through pattern."""
        cache_key = self.key_builder.build(key)

        # Write to both cache and source
        await asyncio.gather(
            self.cache.set(cache_key, value, ttl=self.default_ttl),
            self.data_source.save(key, value),
        )

    async def delete(self, key: str) -> bool:
        """Delete using write-through pattern."""
        cache_key = self.key_builder.build(key)

        # Delete from both cache and source
        results = await asyncio.gather(
            self.cache.delete(cache_key),
            self.data_source.delete(key),
            return_exceptions=True,
        )

        # Return true if either succeeded
        return any(r for r in results if isinstance(r, bool) and r)


class WriteBehindPattern(Generic[T]):
    """
    Implements the write-behind (write-back) caching pattern.

    1. Write to cache immediately
    2. Asynchronously write to data source later
    3. Lower write latency but eventual consistency
    """

    def __init__(
        self,
        cache: ICache[T],
        data_source: IDataSource[T],
        key_builder: Optional[CacheKeyBuilder] = None,
        default_ttl: Optional[timedelta] = None,
        batch_size: int = 100,
        flush_interval: float = 5.0,
    ):
        self.cache = cache
        self.data_source = data_source
        self.key_builder = key_builder or CacheKeyBuilder()
        self.default_ttl = default_ttl
        self.batch_size = batch_size
        self.flush_interval = flush_interval

        # Write buffer
        self._write_buffer: Dict[str, T] = {}
        self._delete_buffer: Set[str] = set()
        self._buffer_lock = asyncio.Lock()

        # Background flush task
        self._flush_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start background flush task."""
        if not self._flush_task:
            self._flush_task = asyncio.create_task(self._flush_worker())

    async def stop(self) -> None:
        """Stop background flush task and flush remaining."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Final flush
        await self._flush_buffers()

    async def save(self, key: str, value: T) -> None:
        """Save using write-behind pattern."""
        cache_key = self.key_builder.build(key)

        # Write to cache immediately
        await self.cache.set(cache_key, value, ttl=self.default_ttl)

        # Buffer for async write
        async with self._buffer_lock:
            self._write_buffer[key] = value
            self._delete_buffer.discard(key)

            # Flush if buffer is full
            if len(self._write_buffer) >= self.batch_size:
                await self._flush_buffers()

    async def delete(self, key: str) -> bool:
        """Delete using write-behind pattern."""
        cache_key = self.key_builder.build(key)

        # Delete from cache immediately
        cache_deleted = await self.cache.delete(cache_key)

        # Buffer for async delete
        async with self._buffer_lock:
            self._delete_buffer.add(key)
            self._write_buffer.pop(key, None)

        return cache_deleted

    async def _flush_worker(self) -> None:
        """Background worker to flush buffers periodically."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_buffers()

            except asyncio.CancelledError:
                break
            except Exception:
                # Log error and continue
                await asyncio.sleep(1)

    async def _flush_buffers(self) -> None:
        """Flush write and delete buffers to data source."""
        async with self._buffer_lock:
            if not self._write_buffer and not self._delete_buffer:
                return

            writes = dict(self._write_buffer)
            deletes = set(self._delete_buffer)

            self._write_buffer.clear()
            self._delete_buffer.clear()

        # Perform writes
        for key, value in writes.items():
            try:
                await self.data_source.save(key, value)
            except Exception:
                # Re-buffer on error
                async with self._buffer_lock:
                    self._write_buffer[key] = value

        # Perform deletes
        for key in deletes:
            try:
                await self.data_source.delete(key)
            except Exception:
                # Re-buffer on error
                async with self._buffer_lock:
                    self._delete_buffer.add(key)


class RefreshAheadPattern(Generic[T]):
    """
    Implements the refresh-ahead caching pattern.

    Proactively refreshes cache entries before they expire
    to maintain consistent performance.
    """

    def __init__(
        self,
        cache: ICache[T],
        data_source: IDataSource[T],
        key_builder: Optional[CacheKeyBuilder] = None,
        ttl: timedelta = timedelta(minutes=5),
        refresh_threshold: float = 0.8,  # Refresh when 80% of TTL passed
    ):
        self.cache = cache
        self.data_source = data_source
        self.key_builder = key_builder or CacheKeyBuilder()
        self.ttl = ttl
        self.refresh_threshold = refresh_threshold

        # Track access patterns
        self._access_times: Dict[str, datetime] = {}
        self._refresh_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start background refresh task."""
        if not self._refresh_task:
            self._refresh_task = asyncio.create_task(self._refresh_worker())

    async def stop(self) -> None:
        """Stop background refresh task."""
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

    async def get(self, key: str) -> Optional[T]:
        """Get with refresh-ahead pattern."""
        cache_key = self.key_builder.build(key)

        # Track access
        from datetime import datetime

        self._access_times[key] = datetime.utcnow()

        # Get from cache
        value = await self.cache.get(cache_key)

        if value is None:
            # Load from source
            value = await self.data_source.get(key)
            if value is not None:
                await self.cache.set(cache_key, value, ttl=self.ttl)

        return value

    async def _refresh_worker(self) -> None:
        """Background worker to refresh cache entries."""
        refresh_interval = self.ttl.total_seconds() * (1 - self.refresh_threshold)

        while True:
            try:
                await asyncio.sleep(refresh_interval)

                # Find keys to refresh
                from datetime import datetime

                now = datetime.utcnow()
                threshold = now - (self.ttl * self.refresh_threshold)

                keys_to_refresh = [
                    key
                    for key, last_access in self._access_times.items()
                    if last_access > threshold
                ]

                # Refresh in batches
                for i in range(0, len(keys_to_refresh), 10):
                    batch = keys_to_refresh[i : i + 10]
                    await self._refresh_batch(batch)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)

    async def _refresh_batch(self, keys: List[str]) -> None:
        """Refresh a batch of keys."""
        # Load from source
        values = await self.data_source.get_many(keys)

        # Update cache
        cache_updates = {}
        for key, value in values.items():
            if value is not None:
                cache_key = self.key_builder.build(key)
                cache_updates[cache_key] = value

        if cache_updates:
            await self.cache.set_many(cache_updates, ttl=self.ttl)


class CacheStampede:
    """
    Prevents cache stampede (thundering herd) problem.

    When a popular cache entry expires, ensures only one request
    refreshes it while others wait.
    """

    def __init__(self, cache: ICache, lock_timeout: timedelta = timedelta(seconds=30)):
        self.cache = cache
        self.lock_timeout = lock_timeout
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock_creation_lock = asyncio.Lock()

    async def get_or_load(
        self, key: str, loader: Callable[[], T], ttl: Optional[timedelta] = None
    ) -> Optional[T]:
        """Get from cache or load with stampede protection."""
        # Try cache first
        value = await self.cache.get(key)
        if value is not None:
            return value

        # Get or create lock for this key
        async with self._lock_creation_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            lock = self._locks[key]

        # Acquire lock with timeout
        try:
            async with asyncio.wait_for(
                lock.acquire(), self.lock_timeout.total_seconds()
            ):
                # Double-check cache (another thread might have loaded it)
                value = await self.cache.get(key)
                if value is not None:
                    return value

                # Load and cache
                value = await loader()
                if value is not None:
                    await self.cache.set(key, value, ttl=ttl)

                return value

        except asyncio.TimeoutError:
            # Timeout waiting for lock, return None or raise
            return None
        finally:
            # Clean up lock if no longer needed
            async with self._lock_creation_lock:
                if key in self._locks and not self._locks[key].locked():
                    del self._locks[key]
