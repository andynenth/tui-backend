"""
Object pooling for memory optimization.

Provides reusable object pools to reduce allocation overhead.
"""

from typing import TypeVar, Generic, Callable, Optional, Any, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import asyncio
import time
import logging
import weakref
from abc import ABC, abstractmethod
from collections import deque


logger = logging.getLogger(__name__)


T = TypeVar("T")


class ObjectFactory(ABC, Generic[T]):
    """Abstract factory for creating and resetting objects."""

    @abstractmethod
    def create(self) -> T:
        """Create a new object."""
        pass

    @abstractmethod
    def reset(self, obj: T) -> None:
        """Reset object to initial state."""
        pass

    @abstractmethod
    def validate(self, obj: T) -> bool:
        """Validate if object is still usable."""
        pass

    @abstractmethod
    def destroy(self, obj: T) -> None:
        """Destroy object and free resources."""
        pass


@dataclass
class ObjectPoolConfig:
    """Configuration for object pool."""

    min_size: int = 0
    max_size: int = 100
    max_idle_time: timedelta = timedelta(minutes=30)
    validation_interval: timedelta = timedelta(minutes=5)
    preload: bool = False
    thread_safe: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.min_size < 0:
            raise ValueError("min_size must be non-negative")
        if self.max_size < self.min_size:
            raise ValueError("max_size must be >= min_size")


@dataclass
class PooledObject:
    """Wrapper for pooled objects."""

    obj: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime = field(default_factory=datetime.utcnow)
    last_validated_at: datetime = field(default_factory=datetime.utcnow)
    use_count: int = 0

    def is_idle_expired(self, max_idle_time: timedelta) -> bool:
        """Check if object has been idle too long."""
        return datetime.utcnow() - self.last_used_at > max_idle_time

    def needs_validation(self, validation_interval: timedelta) -> bool:
        """Check if object needs validation."""
        return datetime.utcnow() - self.last_validated_at > validation_interval

    def mark_used(self) -> None:
        """Mark object as used."""
        self.last_used_at = datetime.utcnow()
        self.use_count += 1


@dataclass
class ObjectPoolStats:
    """Statistics for object pool."""

    total_created: int = 0
    total_destroyed: int = 0
    total_borrows: int = 0
    total_returns: int = 0
    total_validation_failures: int = 0
    current_size: int = 0
    current_available: int = 0
    current_in_use: int = 0
    peak_size: int = 0

    def record_borrow(self) -> None:
        """Record object borrow."""
        self.total_borrows += 1
        self.current_in_use += 1
        self.current_available -= 1

    def record_return(self) -> None:
        """Record object return."""
        self.total_returns += 1
        self.current_in_use -= 1
        self.current_available += 1

    def update_size(self, size: int) -> None:
        """Update pool size."""
        self.current_size = size
        self.peak_size = max(self.peak_size, size)


class ObjectPool(Generic[T]):
    """
    Generic object pool for reusing expensive objects.

    Reduces allocation overhead by maintaining a pool of
    reusable objects that can be borrowed and returned.
    """

    def __init__(
        self, factory: ObjectFactory[T], config: Optional[ObjectPoolConfig] = None
    ):
        """Initialize object pool."""
        self.factory = factory
        self.config = config or ObjectPoolConfig()
        self.stats = ObjectPoolStats()

        # Object storage
        self._available: deque[PooledObject] = deque()
        self._in_use: Dict[int, PooledObject] = {}
        self._all_objects: List[PooledObject] = []

        # Synchronization
        if self.config.thread_safe:
            self._lock = threading.RLock()
        else:
            self._lock = None

        # Preload objects if configured
        if self.config.preload:
            self._preload()

    def _preload(self) -> None:
        """Preload minimum number of objects."""
        for _ in range(self.config.min_size):
            try:
                pooled = self._create_object()
                self._available.append(pooled)
            except Exception as e:
                logger.error(f"Failed to preload object: {e}")

    def _create_object(self) -> PooledObject:
        """Create a new pooled object."""
        obj = self.factory.create()
        pooled = PooledObject(obj)

        self._all_objects.append(pooled)
        self.stats.total_created += 1
        self.stats.update_size(len(self._all_objects))

        return pooled

    def _destroy_object(self, pooled: PooledObject) -> None:
        """Destroy a pooled object."""
        try:
            self.factory.destroy(pooled.obj)
        except Exception as e:
            logger.error(f"Error destroying object: {e}")

        self._all_objects.remove(pooled)
        self.stats.total_destroyed += 1
        self.stats.update_size(len(self._all_objects))

    def _validate_object(self, pooled: PooledObject) -> bool:
        """Validate a pooled object."""
        try:
            is_valid = self.factory.validate(pooled.obj)
            if is_valid:
                pooled.last_validated_at = datetime.utcnow()
            else:
                self.stats.total_validation_failures += 1
            return is_valid
        except Exception as e:
            logger.error(f"Object validation failed: {e}")
            self.stats.total_validation_failures += 1
            return False

    def borrow(self) -> T:
        """
        Borrow an object from the pool.

        Returns:
            Object instance

        Raises:
            RuntimeError: If pool is exhausted
        """
        with self._lock if self._lock else nullcontext():
            # Try to get available object
            while self._available:
                pooled = self._available.popleft()

                # Check if expired
                if pooled.is_idle_expired(self.config.max_idle_time):
                    self._destroy_object(pooled)
                    continue

                # Validate if needed
                if pooled.needs_validation(self.config.validation_interval):
                    if not self._validate_object(pooled):
                        self._destroy_object(pooled)
                        continue

                # Reset and return
                try:
                    self.factory.reset(pooled.obj)
                    pooled.mark_used()
                    self._in_use[id(pooled.obj)] = pooled
                    self.stats.record_borrow()
                    return pooled.obj
                except Exception as e:
                    logger.error(f"Failed to reset object: {e}")
                    self._destroy_object(pooled)
                    continue

            # Create new object if under limit
            if len(self._all_objects) < self.config.max_size:
                try:
                    pooled = self._create_object()
                    pooled.mark_used()
                    self._in_use[id(pooled.obj)] = pooled
                    self.stats.record_borrow()
                    self.stats.current_available = len(self._available)
                    return pooled.obj
                except Exception as e:
                    logger.error(f"Failed to create object: {e}")
                    raise RuntimeError(f"Failed to create object: {e}")

            raise RuntimeError("Object pool exhausted")

    def return_object(self, obj: T) -> None:
        """
        Return an object to the pool.

        Args:
            obj: Object to return
        """
        with self._lock if self._lock else nullcontext():
            obj_id = id(obj)

            # Check if object is from this pool
            if obj_id not in self._in_use:
                logger.warning("Attempted to return unknown object")
                return

            pooled = self._in_use.pop(obj_id)
            self.stats.record_return()

            # Check if should keep object
            if len(self._available) >= self.config.max_size:
                self._destroy_object(pooled)
            else:
                self._available.append(pooled)

            self.stats.current_available = len(self._available)

    def clear(self) -> None:
        """Clear all objects from the pool."""
        with self._lock if self._lock else nullcontext():
            # Destroy all objects
            for pooled in self._all_objects[:]:
                self._destroy_object(pooled)

            self._available.clear()
            self._in_use.clear()
            self.stats.current_available = 0
            self.stats.current_in_use = 0

    def shrink(self) -> int:
        """
        Shrink pool by removing idle objects.

        Returns:
            Number of objects removed
        """
        removed = 0

        with self._lock if self._lock else nullcontext():
            # Remove expired idle objects
            new_available = deque()

            for pooled in self._available:
                if pooled.is_idle_expired(self.config.max_idle_time):
                    self._destroy_object(pooled)
                    removed += 1
                else:
                    new_available.append(pooled)

            self._available = new_available
            self.stats.current_available = len(self._available)

        return removed

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            "config": {
                "min_size": self.config.min_size,
                "max_size": self.config.max_size,
                "max_idle_time": self.config.max_idle_time.total_seconds(),
            },
            "current": {
                "size": self.stats.current_size,
                "available": self.stats.current_available,
                "in_use": self.stats.current_in_use,
            },
            "totals": {
                "created": self.stats.total_created,
                "destroyed": self.stats.total_destroyed,
                "borrows": self.stats.total_borrows,
                "returns": self.stats.total_returns,
                "validation_failures": self.stats.total_validation_failures,
            },
            "peak_size": self.stats.peak_size,
        }

    def __enter__(self):
        """Enter context manager."""
        return self.borrow()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        # Note: requires tracking of borrowed object
        pass


# Common object factories


class ListFactory(ObjectFactory[List]):
    """Factory for list objects."""

    def __init__(self, initial_capacity: int = 10):
        self.initial_capacity = initial_capacity

    def create(self) -> List:
        """Create a new list."""
        return [None] * self.initial_capacity

    def reset(self, obj: List) -> None:
        """Clear the list."""
        obj.clear()

    def validate(self, obj: List) -> bool:
        """Lists are always valid."""
        return True

    def destroy(self, obj: List) -> None:
        """Clear the list."""
        obj.clear()


class DictFactory(ObjectFactory[Dict]):
    """Factory for dictionary objects."""

    def create(self) -> Dict:
        """Create a new dict."""
        return {}

    def reset(self, obj: Dict) -> None:
        """Clear the dict."""
        obj.clear()

    def validate(self, obj: Dict) -> bool:
        """Dicts are always valid."""
        return True

    def destroy(self, obj: Dict) -> None:
        """Clear the dict."""
        obj.clear()


class ByteArrayFactory(ObjectFactory[bytearray]):
    """Factory for bytearray objects."""

    def __init__(self, size: int = 4096):
        self.size = size

    def create(self) -> bytearray:
        """Create a new bytearray."""
        return bytearray(self.size)

    def reset(self, obj: bytearray) -> None:
        """Zero out the bytearray."""
        obj[:] = b"\x00" * len(obj)

    def validate(self, obj: bytearray) -> bool:
        """Check bytearray size."""
        return len(obj) == self.size

    def destroy(self, obj: bytearray) -> None:
        """Clear the bytearray."""
        obj.clear()


# Global pools

_pools: Dict[str, ObjectPool] = {}
_lock = threading.RLock()


def get_pool(
    name: str, factory: ObjectFactory, config: Optional[ObjectPoolConfig] = None
) -> ObjectPool:
    """Get or create a named object pool."""
    with _lock:
        if name not in _pools:
            _pools[name] = ObjectPool(factory, config)
        return _pools[name]


def clear_all_pools() -> None:
    """Clear all object pools."""
    with _lock:
        for pool in _pools.values():
            pool.clear()
        _pools.clear()


# Context manager helper
from contextlib import contextmanager, nullcontext


@contextmanager
def pooled_object(pool: ObjectPool[T]) -> T:
    """
    Context manager for using pooled objects.

    Example:
        with pooled_object(pool) as obj:
            # Use object
            pass
    """
    obj = pool.borrow()
    try:
        yield obj
    finally:
        pool.return_object(obj)


# Async support


class AsyncObjectPool(Generic[T]):
    """Asynchronous object pool implementation."""

    def __init__(
        self, factory: ObjectFactory[T], config: Optional[ObjectPoolConfig] = None
    ):
        """Initialize async object pool."""
        self.factory = factory
        self.config = config or ObjectPoolConfig()
        self.stats = ObjectPoolStats()

        # Object storage
        self._available: asyncio.Queue[PooledObject] = asyncio.Queue()
        self._in_use: Dict[int, PooledObject] = {}
        self._all_objects: List[PooledObject] = []

        # Synchronization
        self._lock = asyncio.Lock()

    async def borrow(self) -> T:
        """Borrow an object from the pool asynchronously."""
        async with self._lock:
            # Try to get available object
            try:
                while not self._available.empty():
                    pooled = await self._available.get()

                    # Validate and reset
                    if self._validate_object(pooled):
                        self.factory.reset(pooled.obj)
                        pooled.mark_used()
                        self._in_use[id(pooled.obj)] = pooled
                        self.stats.record_borrow()
                        return pooled.obj
                    else:
                        self._destroy_object(pooled)
            except asyncio.QueueEmpty:
                pass

            # Create new object if under limit
            if len(self._all_objects) < self.config.max_size:
                pooled = self._create_object()
                pooled.mark_used()
                self._in_use[id(pooled.obj)] = pooled
                self.stats.record_borrow()
                return pooled.obj

            raise RuntimeError("Object pool exhausted")

    async def return_object(self, obj: T) -> None:
        """Return an object to the pool asynchronously."""
        async with self._lock:
            obj_id = id(obj)

            if obj_id not in self._in_use:
                logger.warning("Attempted to return unknown object")
                return

            pooled = self._in_use.pop(obj_id)
            self.stats.record_return()

            # Return to available queue
            await self._available.put(pooled)
