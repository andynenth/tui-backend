"""
Bulkhead pattern implementation for resource isolation.

Prevents resource exhaustion by isolating resources into separate pools.
"""

from typing import TypeVar, Generic, Callable, Optional, Any, Dict, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager, contextmanager
from enum import Enum
import asyncio
import threading
import time
import logging
from abc import ABC, abstractmethod
import queue


logger = logging.getLogger(__name__)


class BulkheadFullError(Exception):
    """Raised when bulkhead is at capacity."""

    pass


class BulkheadTimeoutError(Exception):
    """Raised when waiting for bulkhead times out."""

    pass


class IsolationLevel(Enum):
    """Isolation levels for bulkhead."""

    THREAD = "thread"  # Thread pool isolation
    SEMAPHORE = "semaphore"  # Semaphore isolation
    QUEUE = "queue"  # Queue-based isolation


@dataclass
class BulkheadConfig:
    """Configuration for bulkhead."""

    max_concurrent: int = 10
    max_queue_size: int = 100
    timeout: Optional[timedelta] = timedelta(seconds=30)
    isolation_level: IsolationLevel = IsolationLevel.SEMAPHORE
    name: str = "default"

    def __post_init__(self):
        """Validate configuration."""
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        if self.max_queue_size < 0:
            raise ValueError("max_queue_size must be non-negative")


@dataclass
class BulkheadStats:
    """Statistics for bulkhead usage."""

    total_calls: int = 0
    successful_calls: int = 0
    rejected_calls: int = 0
    timeout_calls: int = 0
    active_calls: int = 0
    queued_calls: int = 0
    total_wait_time: float = 0.0
    max_wait_time: float = 0.0

    def record_call(self) -> None:
        """Record call attempt."""
        self.total_calls += 1

    def record_success(self, wait_time: float = 0.0) -> None:
        """Record successful call."""
        self.successful_calls += 1
        self.total_wait_time += wait_time
        self.max_wait_time = max(self.max_wait_time, wait_time)

    def record_rejection(self) -> None:
        """Record rejected call."""
        self.rejected_calls += 1

    def record_timeout(self) -> None:
        """Record timeout."""
        self.timeout_calls += 1

    def get_rejection_rate(self) -> float:
        """Get rejection rate."""
        if self.total_calls == 0:
            return 0.0
        return self.rejected_calls / self.total_calls

    def get_average_wait_time(self) -> float:
        """Get average wait time."""
        if self.successful_calls == 0:
            return 0.0
        return self.total_wait_time / self.successful_calls


T = TypeVar("T")


class Bulkhead(ABC, Generic[T]):
    """
    Abstract base class for bulkhead implementations.

    Provides resource isolation to prevent cascading failures.
    """

    def __init__(self, config: BulkheadConfig):
        """Initialize bulkhead."""
        self.config = config
        self.stats = BulkheadStats()
        self._shutdown = False

    @abstractmethod
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire resource from bulkhead."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Release resource back to bulkhead."""
        pass

    @abstractmethod
    async def acquire_async(self, timeout: Optional[float] = None) -> bool:
        """Acquire resource asynchronously."""
        pass

    @abstractmethod
    async def release_async(self) -> None:
        """Release resource asynchronously."""
        pass

    @abstractmethod
    def get_active_count(self) -> int:
        """Get number of active executions."""
        pass

    @abstractmethod
    def get_queue_size(self) -> int:
        """Get current queue size."""
        pass

    def is_full(self) -> bool:
        """Check if bulkhead is at capacity."""
        return self.get_active_count() >= self.config.max_concurrent

    def shutdown(self) -> None:
        """Shutdown bulkhead."""
        self._shutdown = True

    def get_stats(self) -> Dict[str, Any]:
        """Get bulkhead statistics."""
        return {
            "name": self.config.name,
            "max_concurrent": self.config.max_concurrent,
            "max_queue_size": self.config.max_queue_size,
            "active_calls": self.get_active_count(),
            "queued_calls": self.get_queue_size(),
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "rejected_calls": self.stats.rejected_calls,
            "timeout_calls": self.stats.timeout_calls,
            "rejection_rate": self.stats.get_rejection_rate(),
            "average_wait_time": self.stats.get_average_wait_time(),
            "max_wait_time": self.stats.max_wait_time,
        }


class SemaphoreBulkhead(Bulkhead[T]):
    """
    Semaphore-based bulkhead implementation.

    Uses semaphores for lightweight resource limiting.
    """

    def __init__(self, config: BulkheadConfig):
        """Initialize semaphore bulkhead."""
        super().__init__(config)
        self._semaphore = threading.BoundedSemaphore(config.max_concurrent)
        self._async_semaphore = asyncio.BoundedSemaphore(config.max_concurrent)
        self._queue = queue.Queue(maxsize=config.max_queue_size)
        self._active_count = 0
        self._lock = threading.Lock()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Acquire resource from bulkhead."""
        if self._shutdown:
            raise RuntimeError("Bulkhead is shutdown")

        self.stats.record_call()

        # Check queue capacity
        if self._queue.qsize() >= self.config.max_queue_size:
            self.stats.record_rejection()
            raise BulkheadFullError(f"Bulkhead '{self.config.name}' queue is full")

        # Use configured timeout if not specified
        if timeout is None and self.config.timeout:
            timeout = self.config.timeout.total_seconds()

        start_time = time.time()

        # Try to acquire semaphore
        acquired = self._semaphore.acquire(blocking=True, timeout=timeout)

        if not acquired:
            self.stats.record_timeout()
            raise BulkheadTimeoutError(
                f"Timeout waiting for bulkhead '{self.config.name}'"
            )

        wait_time = time.time() - start_time
        self.stats.record_success(wait_time)

        with self._lock:
            self._active_count += 1
            self.stats.active_calls = self._active_count

        return True

    def release(self) -> None:
        """Release resource back to bulkhead."""
        self._semaphore.release()

        with self._lock:
            self._active_count -= 1
            self.stats.active_calls = self._active_count

    async def acquire_async(self, timeout: Optional[float] = None) -> bool:
        """Acquire resource asynchronously."""
        if self._shutdown:
            raise RuntimeError("Bulkhead is shutdown")

        self.stats.record_call()

        # Use configured timeout if not specified
        if timeout is None and self.config.timeout:
            timeout = self.config.timeout.total_seconds()

        start_time = time.time()

        try:
            # Try to acquire semaphore with timeout
            if timeout:
                await asyncio.wait_for(self._async_semaphore.acquire(), timeout=timeout)
            else:
                await self._async_semaphore.acquire()

            wait_time = time.time() - start_time
            self.stats.record_success(wait_time)

            with self._lock:
                self._active_count += 1
                self.stats.active_calls = self._active_count

            return True

        except asyncio.TimeoutError:
            self.stats.record_timeout()
            raise BulkheadTimeoutError(
                f"Timeout waiting for bulkhead '{self.config.name}'"
            )

    async def release_async(self) -> None:
        """Release resource asynchronously."""
        self._async_semaphore.release()

        with self._lock:
            self._active_count -= 1
            self.stats.active_calls = self._active_count

    def get_active_count(self) -> int:
        """Get number of active executions."""
        return self._active_count

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()


class ThreadPoolBulkhead(Bulkhead[T]):
    """
    Thread pool-based bulkhead implementation.

    Uses dedicated thread pool for complete isolation.
    """

    def __init__(self, config: BulkheadConfig):
        """Initialize thread pool bulkhead."""
        super().__init__(config)
        from concurrent.futures import ThreadPoolExecutor

        self._executor = ThreadPoolExecutor(
            max_workers=config.max_concurrent,
            thread_name_prefix=f"bulkhead-{config.name}",
        )
        self._futures: set = set()
        self._lock = threading.Lock()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        """Not used for thread pool bulkhead."""
        raise NotImplementedError("Use submit() for thread pool bulkhead")

    def release(self) -> None:
        """Not used for thread pool bulkhead."""
        raise NotImplementedError("Use submit() for thread pool bulkhead")

    async def acquire_async(self, timeout: Optional[float] = None) -> bool:
        """Not used for thread pool bulkhead."""
        raise NotImplementedError("Use submit_async() for thread pool bulkhead")

    async def release_async(self) -> None:
        """Not used for thread pool bulkhead."""
        raise NotImplementedError("Use submit_async() for thread pool bulkhead")

    def submit(self, func: Callable[..., T], *args, **kwargs) -> Any:
        """Submit function to thread pool."""
        if self._shutdown:
            raise RuntimeError("Bulkhead is shutdown")

        self.stats.record_call()

        # Check if at capacity
        with self._lock:
            active_count = len([f for f in self._futures if not f.done()])
            if active_count >= self.config.max_concurrent:
                self.stats.record_rejection()
                raise BulkheadFullError(
                    f"Thread pool bulkhead '{self.config.name}' is at capacity"
                )

        # Submit to executor
        future = self._executor.submit(func, *args, **kwargs)

        with self._lock:
            self._futures.add(future)
            # Clean up completed futures
            self._futures = {f for f in self._futures if not f.done()}

        self.stats.record_success()
        return future

    def get_active_count(self) -> int:
        """Get number of active executions."""
        with self._lock:
            return len([f for f in self._futures if not f.done()])

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._executor._work_queue.qsize()

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown thread pool."""
        super().shutdown()
        self._executor.shutdown(wait=wait)


# Context managers for bulkhead usage


@contextmanager
def bulkhead_guard(bulkhead: Bulkhead, timeout: Optional[float] = None):
    """
    Context manager for bulkhead-protected execution.

    Example:
        with bulkhead_guard(bulkhead):
            # Protected code
            pass
    """
    bulkhead.acquire(timeout)
    try:
        yield bulkhead
    finally:
        bulkhead.release()


@asynccontextmanager
async def bulkhead_guard_async(bulkhead: Bulkhead, timeout: Optional[float] = None):
    """
    Async context manager for bulkhead-protected execution.

    Example:
        async with bulkhead_guard_async(bulkhead):
            # Protected async code
            pass
    """
    await bulkhead.acquire_async(timeout)
    try:
        yield bulkhead
    finally:
        await bulkhead.release_async()


# Decorator support


def bulkhead(
    config: Optional[BulkheadConfig] = None,
    name: Optional[str] = None,
    max_concurrent: int = 10,
    timeout: Optional[float] = None,
) -> Callable:
    """
    Decorator to apply bulkhead pattern to functions.

    Args:
        config: Bulkhead configuration
        name: Bulkhead name
        max_concurrent: Maximum concurrent executions
        timeout: Timeout in seconds

    Example:
        @bulkhead(max_concurrent=5)
        def protected_function():
            # Function body
            pass
    """
    if config is None:
        config = BulkheadConfig(
            name=name or "decorator",
            max_concurrent=max_concurrent,
            timeout=timedelta(seconds=timeout) if timeout else None,
        )

    bulkhead_instance = SemaphoreBulkhead(config)

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                async with bulkhead_guard_async(bulkhead_instance):
                    return await func(*args, **kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                with bulkhead_guard(bulkhead_instance):
                    return func(*args, **kwargs)

            return sync_wrapper

    return decorator


# Bulkhead registry


class BulkheadRegistry:
    """Registry for managing multiple bulkheads."""

    def __init__(self):
        """Initialize registry."""
        self._bulkheads: Dict[str, Bulkhead] = {}
        self._lock = threading.RLock()

    def create(
        self,
        name: str,
        config: Optional[BulkheadConfig] = None,
        isolation_level: IsolationLevel = IsolationLevel.SEMAPHORE,
    ) -> Bulkhead:
        """Create and register a bulkhead."""
        with self._lock:
            if name in self._bulkheads:
                return self._bulkheads[name]

            if config is None:
                config = BulkheadConfig(name=name)

            if isolation_level == IsolationLevel.SEMAPHORE:
                bulkhead = SemaphoreBulkhead(config)
            elif isolation_level == IsolationLevel.THREAD:
                bulkhead = ThreadPoolBulkhead(config)
            else:
                raise ValueError(f"Unsupported isolation level: {isolation_level}")

            self._bulkheads[name] = bulkhead
            return bulkhead

    def get(self, name: str) -> Optional[Bulkhead]:
        """Get bulkhead by name."""
        return self._bulkheads.get(name)

    def get_all(self) -> Dict[str, Bulkhead]:
        """Get all bulkheads."""
        return self._bulkheads.copy()

    def shutdown_all(self, wait: bool = True) -> None:
        """Shutdown all bulkheads."""
        with self._lock:
            for bulkhead in self._bulkheads.values():
                if isinstance(bulkhead, ThreadPoolBulkhead):
                    bulkhead.shutdown(wait=wait)
                else:
                    bulkhead.shutdown()

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all bulkheads."""
        return {
            name: bulkhead.get_stats() for name, bulkhead in self._bulkheads.items()
        }


# Global registry
_registry = BulkheadRegistry()


def get_bulkhead(
    name: str,
    config: Optional[BulkheadConfig] = None,
    isolation_level: IsolationLevel = IsolationLevel.SEMAPHORE,
) -> Bulkhead:
    """Get or create bulkhead from global registry."""
    return _registry.create(name, config, isolation_level)


def get_all_bulkheads() -> Dict[str, Bulkhead]:
    """Get all registered bulkheads."""
    return _registry.get_all()


def shutdown_all_bulkheads(wait: bool = True) -> None:
    """Shutdown all bulkheads."""
    _registry.shutdown_all(wait=wait)
