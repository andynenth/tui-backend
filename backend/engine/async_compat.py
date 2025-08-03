# backend/engine/async_compat.py
"""
Async compatibility layer for gradual migration from sync to async.
Provides base classes and utilities for smooth transition.
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional, TypeVar, Union
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Type variable for generic return types
T = TypeVar("T")

# Thread pool for running sync code in async context
_thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sync_compat")


def run_sync_in_async(sync_func: Callable[..., T]) -> Callable[..., asyncio.Future[T]]:
    """
    Decorator to run synchronous functions in async context using thread pool.

    Usage:
        @run_sync_in_async
        def sync_function(x, y):
            return x + y

        # Can now be called from async code:
        result = await sync_function(1, 2)
    """

    @functools.wraps(sync_func)
    async def async_wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        # Run sync function in thread pool to avoid blocking
        return await loop.run_in_executor(
            _thread_pool, functools.partial(sync_func, *args, **kwargs)
        )

    return async_wrapper


def create_async_method(
    sync_method: Callable[..., T]
) -> Callable[..., asyncio.Future[T]]:
    """
    Create an async version of a sync method for compatibility.

    Usage:
        class MyClass:
            def sync_method(self, x):
                return x * 2

            async_method = create_async_method(sync_method)
    """

    @functools.wraps(sync_method)
    async def async_method(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        # Bind method to self and run in thread pool
        bound_method = functools.partial(sync_method, self)
        return await loop.run_in_executor(
            _thread_pool, functools.partial(bound_method, *args, **kwargs)
        )

    # Preserve method name with _async suffix
    async_method.__name__ = f"{sync_method.__name__}_async"
    return async_method


class AsyncCompatMixin:
    """
    Mixin class that provides async compatibility helpers.
    Classes can inherit from this to get automatic async versions of methods.
    """

    def __init__(self):
        # Lock for thread-safe operations
        self._async_compat_lock = asyncio.Lock()

    async def _run_sync_method(self, method_name: str, *args, **kwargs):
        """Run a sync method in async context."""
        method = getattr(self, method_name)
        if asyncio.iscoroutinefunction(method):
            # Already async, just call it
            return await method(*args, **kwargs)
        else:
            # Run sync method in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                _thread_pool, functools.partial(method, *args, **kwargs)
            )


class AsyncCompatRoomManager:
    """
    Async-compatible wrapper for RoomManager.
    Provides both sync and async interfaces during migration.
    """

    def __init__(self, sync_room_manager):
        self._sync_manager = sync_room_manager
        self._manager_lock = asyncio.Lock()

    # Async versions of RoomManager methods
    async def create_room(self, host_name: str) -> str:
        """Async version of create_room."""
        async with self._manager_lock:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                _thread_pool, self._sync_manager.create_room, host_name
            )

    async def get_room(self, room_id: str) -> Optional[Any]:
        """Async version of get_room."""
        # get_room is read-only, so no lock needed
        loop = asyncio.get_event_loop()
        room = await loop.run_in_executor(
            _thread_pool, self._sync_manager.get_room, room_id
        )
        # Wrap room in async-compatible wrapper if found
        if room:
            return AsyncCompatRoom(room)
        return None

    async def delete_room(self, room_id: str) -> None:
        """Async version of delete_room."""
        async with self._manager_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                _thread_pool, self._sync_manager.delete_room, room_id
            )

    async def list_rooms(self) -> list:
        """Async version of list_rooms."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_thread_pool, self._sync_manager.list_rooms)

    # Sync compatibility methods (for gradual migration)
    def create_room_sync(self, host_name: str) -> str:
        """Sync wrapper that calls async version."""
        return asyncio.run(self.create_room(host_name))

    def get_room_sync(self, room_id: str) -> Optional[Any]:
        """Sync wrapper that calls async version."""
        return asyncio.run(self.get_room(room_id))


class AsyncCompatRoom:
    """
    Async-compatible wrapper for Room.
    Provides both sync and async interfaces during migration.
    """

    def __init__(self, sync_room):
        self._sync_room = sync_room
        # Use the existing locks from Room if available
        self._join_lock = getattr(sync_room, "_join_lock", asyncio.Lock())
        self._assign_lock = getattr(sync_room, "_assign_lock", asyncio.Lock())
        self._state_lock = getattr(sync_room, "_state_lock", asyncio.Lock())

    # Expose sync room properties
    def __getattr__(self, name):
        """Forward attribute access to sync room."""
        return getattr(self._sync_room, name)

    # Async versions of Room methods
    async def join_room(self, player_name: str) -> int:
        """Async version of join_room."""
        async with self._join_lock:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                _thread_pool, self._sync_room.join_room, player_name
            )

    async def exit_room(self, player_name: str) -> bool:
        """Async version of exit_room."""
        async with self._state_lock:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                _thread_pool, self._sync_room.exit_room, player_name
            )

    async def start_game(self) -> None:
        """Async version of start_game."""
        async with self._state_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(_thread_pool, self._sync_room.start_game)

    async def assign_slot(self, slot: int, name_or_none: Optional[str]) -> None:
        """Async version of assign_slot."""
        async with self._assign_lock:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                _thread_pool, self._sync_room.assign_slot, slot, name_or_none
            )

    # Sync compatibility methods (for code that still expects sync)
    def join_room_sync(self, player_name: str) -> int:
        """Sync wrapper for compatibility."""
        return asyncio.run(self.join_room(player_name))

    def exit_room_sync(self, player_name: str) -> bool:
        """Sync wrapper for compatibility."""
        return asyncio.run(self.exit_room(player_name))

    # Direct access to sync methods when needed
    @property
    def sync_room(self):
        """Access underlying sync room when needed."""
        return self._sync_room


# Utility functions for migration
def ensure_async_room(room: Union[Any, AsyncCompatRoom]) -> AsyncCompatRoom:
    """
    Ensure a room object is async-compatible.
    If already wrapped, return as-is. Otherwise, wrap it.
    """
    if isinstance(room, AsyncCompatRoom):
        return room
    return AsyncCompatRoom(room)


def is_async_compatible(obj: Any) -> bool:
    """Check if an object has async compatibility."""
    return isinstance(obj, (AsyncCompatRoom, AsyncCompatRoomManager))
