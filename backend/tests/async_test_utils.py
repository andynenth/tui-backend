# backend/tests/async_test_utils.py
"""
Async test utilities and fixtures for testing async compatibility layer.
"""

import asyncio
import functools
import pytest
from typing import Any, Callable, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from engine.room import Room
from engine.room_manager import RoomManager
from engine.async_compat import AsyncCompatRoom, AsyncCompatRoomManager


# Pytest fixtures for async testing
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_room_manager():
    """Create an async-compatible room manager for testing."""
    sync_manager = RoomManager()
    async_manager = AsyncCompatRoomManager(sync_manager)
    return async_manager


@pytest.fixture
async def async_room():
    """Create an async-compatible room for testing."""
    sync_room = Room("TEST123", "TestHost")
    async_room = AsyncCompatRoom(sync_room)
    return async_room


@pytest.fixture
def mock_broadcast_callback():
    """Create a mock broadcast callback for testing."""
    return AsyncMock()


# Async test helpers
class AsyncTestHelper:
    """Helper class for async testing."""

    @staticmethod
    async def wait_for_condition(
        condition_func: Callable[[], bool], timeout: float = 5.0, interval: float = 0.1
    ) -> bool:
        """
        Wait for a condition to become true.

        Args:
            condition_func: Function that returns True when condition is met
            timeout: Maximum time to wait in seconds
            interval: Check interval in seconds

        Returns:
            bool: True if condition was met, False if timeout
        """
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if condition_func():
                return True
            await asyncio.sleep(interval)
        return False

    @staticmethod
    async def run_concurrent_operations(
        *operations: Callable[[], Any], max_concurrent: Optional[int] = None
    ) -> list:
        """
        Run multiple async operations concurrently.

        Args:
            operations: Async functions to run
            max_concurrent: Maximum concurrent operations (None for unlimited)

        Returns:
            list: Results from all operations
        """
        if max_concurrent:
            # Use semaphore to limit concurrency
            semaphore = asyncio.Semaphore(max_concurrent)

            async def limited_operation(op):
                async with semaphore:
                    return await op()

            tasks = [limited_operation(op) for op in operations]
        else:
            tasks = [op() for op in operations]

        return await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    async def assert_no_deadlock(async_func: Callable, timeout: float = 1.0):
        """
        Assert that an async function doesn't deadlock.

        Args:
            async_func: Async function to test
            timeout: Maximum time to wait

        Raises:
            asyncio.TimeoutError: If function doesn't complete in time
        """
        await asyncio.wait_for(async_func(), timeout=timeout)


# Decorators for async testing
def async_test(timeout: float = 10.0):
    """
    Decorator for async test methods with timeout.

    Usage:
        @async_test(timeout=5.0)
        async def test_something():
            await some_async_operation()
    """

    def decorator(test_func):
        @functools.wraps(test_func)
        async def wrapper(*args, **kwargs):
            try:
                await asyncio.wait_for(test_func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                pytest.fail(f"Test {test_func.__name__} timed out after {timeout}s")

        return wrapper

    return decorator


def with_async_timeout(timeout: float = 5.0):
    """
    Context manager for async operations with timeout.

    Usage:
        async with with_async_timeout(2.0):
            await some_operation()
    """

    class AsyncTimeout:
        def __init__(self, timeout):
            self.timeout = timeout
            self._task = None

        async def __aenter__(self):
            self._task = asyncio.current_task()
            loop = asyncio.get_event_loop()
            self._handle = loop.call_later(self.timeout, self._cancel_task)
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            self._handle.cancel()

        def _cancel_task(self):
            if self._task and not self._task.done():
                self._task.cancel()

    return AsyncTimeout(timeout)


# Mock factories for testing
class AsyncMockFactory:
    """Factory for creating async mocks."""

    @staticmethod
    def create_async_room_manager():
        """Create a mock async room manager."""
        mock = MagicMock(spec=AsyncCompatRoomManager)
        mock.create_room = AsyncMock(return_value="MOCK123")
        mock.get_room = AsyncMock(return_value=None)
        mock.delete_room = AsyncMock()
        mock.list_rooms = AsyncMock(return_value=[])
        return mock

    @staticmethod
    def create_async_room():
        """Create a mock async room."""
        mock = MagicMock(spec=AsyncCompatRoom)
        mock.join_room = AsyncMock(return_value=0)
        mock.exit_room = AsyncMock(return_value=False)
        mock.start_game = AsyncMock()
        mock.assign_slot = AsyncMock()
        mock.room_id = "MOCK123"
        mock.host_name = "MockHost"
        mock.started = False
        mock.players = [None, None, None, None]
        return mock


# Assertion helpers
class AsyncAssertions:
    """Async-specific assertions for testing."""

    @staticmethod
    async def assert_called_once_async(mock: AsyncMock, *args, **kwargs):
        """Assert an async mock was called exactly once with specific args."""
        mock.assert_called_once_with(*args, **kwargs)
        # Ensure the call actually completed
        assert mock.call_count == 1

    @staticmethod
    async def assert_concurrent_safety(async_func: Callable, num_concurrent: int = 10):
        """
        Assert that a function is safe for concurrent execution.

        Args:
            async_func: Function to test
            num_concurrent: Number of concurrent executions
        """
        results = await asyncio.gather(
            *[async_func() for _ in range(num_concurrent)], return_exceptions=True
        )

        # Check no exceptions occurred
        exceptions = [r for r in results if isinstance(r, Exception)]
        if exceptions:
            pytest.fail(f"Concurrent execution failed: {exceptions}")

        # Check all results are valid (not None, etc.)
        assert all(r is not None for r in results)


# Example test showing usage
async def test_example_async_compatibility():
    """Example test demonstrating async test utilities."""
    # Create async room manager
    sync_manager = RoomManager()
    async_manager = AsyncCompatRoomManager(sync_manager)

    # Test room creation
    room_id = await async_manager.create_room("TestHost")
    assert room_id is not None
    assert len(room_id) == 6

    # Test room retrieval
    room = await async_manager.get_room(room_id)
    assert room is not None
    assert isinstance(room, AsyncCompatRoom)
    assert room.host_name == "TestHost"

    # Test concurrent operations
    helper = AsyncTestHelper()

    async def join_player(player_num):
        return await room.join_room(f"Player{player_num}")

    # Join 3 players concurrently
    results = await helper.run_concurrent_operations(
        lambda: join_player(1), lambda: join_player(2), lambda: join_player(3)
    )

    # Verify all joined successfully
    assert all(isinstance(r, int) for r in results)
    assert len(set(results)) == 3  # All got different slots
