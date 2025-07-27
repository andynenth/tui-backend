"""
Timeout handling for resilient operations.

Provides timeout enforcement with proper cleanup and cancellation.
"""

from typing import TypeVar, Callable, Optional, Any, Union
from dataclasses import dataclass
from datetime import timedelta
import asyncio
import threading
import time
import signal
import functools
import logging
from contextlib import contextmanager
from enum import Enum


logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Raised when operation times out."""
    
    def __init__(self, timeout: float, operation: Optional[str] = None):
        self.timeout = timeout
        self.operation = operation
        msg = f"Operation timed out after {timeout}s"
        if operation:
            msg = f"{operation} timed out after {timeout}s"
        super().__init__(msg)


class TimeoutStrategy(Enum):
    """Timeout enforcement strategies."""
    THREAD = "thread"      # Thread-based (interrupts)
    SIGNAL = "signal"      # Signal-based (Unix only)
    ASYNC = "async"        # Asyncio-based


@dataclass
class TimeoutConfig:
    """Configuration for timeout handling."""
    timeout: timedelta
    strategy: TimeoutStrategy = TimeoutStrategy.ASYNC
    raise_on_timeout: bool = True
    cleanup_func: Optional[Callable] = None
    
    @property
    def timeout_seconds(self) -> float:
        """Get timeout in seconds."""
        return self.timeout.total_seconds()


T = TypeVar('T')


class TimeoutHandler:
    """
    Handles timeout enforcement for operations.
    
    Supports multiple strategies for different environments.
    """
    
    def __init__(self, config: TimeoutConfig):
        """Initialize timeout handler."""
        self.config = config
        self._check_strategy_support()
    
    def _check_strategy_support(self) -> None:
        """Check if strategy is supported on platform."""
        if self.config.strategy == TimeoutStrategy.SIGNAL:
            if not hasattr(signal, 'SIGALRM'):
                logger.warning(
                    "Signal-based timeout not supported on this platform, "
                    "falling back to thread-based"
                )
                self.config.strategy = TimeoutStrategy.THREAD
    
    def execute(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        Execute function with timeout.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            TimeoutError: If operation times out
        """
        if self.config.strategy == TimeoutStrategy.SIGNAL:
            return self._execute_with_signal(func, *args, **kwargs)
        elif self.config.strategy == TimeoutStrategy.THREAD:
            return self._execute_with_thread(func, *args, **kwargs)
        else:
            raise ValueError(f"Unsupported strategy for sync execution: {self.config.strategy}")
    
    async def execute_async(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> T:
        """
        Execute async function with timeout.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            TimeoutError: If operation times out
        """
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout_seconds
            )
            return result
            
        except asyncio.TimeoutError:
            # Run cleanup if specified
            if self.config.cleanup_func:
                try:
                    if asyncio.iscoroutinefunction(self.config.cleanup_func):
                        await self.config.cleanup_func()
                    else:
                        self.config.cleanup_func()
                except Exception as e:
                    logger.error(f"Cleanup function failed: {e}")
            
            if self.config.raise_on_timeout:
                raise TimeoutError(
                    self.config.timeout_seconds,
                    func.__name__
                )
            return None
    
    def _execute_with_signal(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Execute with signal-based timeout (Unix only)."""
        def timeout_handler(signum, frame):
            raise TimeoutError(
                self.config.timeout_seconds,
                func.__name__
            )
        
        # Set signal handler
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.config.timeout_seconds))
        
        try:
            result = func(*args, **kwargs)
            signal.alarm(0)  # Cancel alarm
            return result
            
        except TimeoutError:
            # Run cleanup if specified
            if self.config.cleanup_func:
                try:
                    self.config.cleanup_func()
                except Exception as e:
                    logger.error(f"Cleanup function failed: {e}")
            
            if self.config.raise_on_timeout:
                raise
            return None
            
        finally:
            signal.alarm(0)  # Ensure alarm is cancelled
            signal.signal(signal.SIGALRM, old_handler)
    
    def _execute_with_thread(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Execute with thread-based timeout."""
        result = [None]
        exception = [None]
        completed = threading.Event()
        
        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
            finally:
                completed.set()
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        
        # Wait for completion or timeout
        if not completed.wait(self.config.timeout_seconds):
            # Timeout occurred
            if self.config.cleanup_func:
                try:
                    self.config.cleanup_func()
                except Exception as e:
                    logger.error(f"Cleanup function failed: {e}")
            
            if self.config.raise_on_timeout:
                raise TimeoutError(
                    self.config.timeout_seconds,
                    func.__name__
                )
            return None
        
        # Check for exception
        if exception[0]:
            raise exception[0]
        
        return result[0]


# Context managers

@contextmanager
def timeout_context(
    seconds: Union[float, timedelta],
    strategy: TimeoutStrategy = TimeoutStrategy.SIGNAL,
    operation: Optional[str] = None
):
    """
    Context manager for timeout enforcement.
    
    Example:
        with timeout_context(5.0):
            # Code that must complete in 5 seconds
            pass
    """
    if isinstance(seconds, timedelta):
        seconds = seconds.total_seconds()
    
    if strategy == TimeoutStrategy.SIGNAL and hasattr(signal, 'SIGALRM'):
        def timeout_handler(signum, frame):
            raise TimeoutError(seconds, operation)
        
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(seconds))
        
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Fallback to no timeout enforcement for sync context
        logger.warning(
            "Timeout context not fully supported in sync mode without signals"
        )
        yield


class AsyncTimeout:
    """Async context manager for timeout enforcement."""
    
    def __init__(
        self,
        timeout: Union[float, timedelta],
        operation: Optional[str] = None
    ):
        """Initialize async timeout."""
        if isinstance(timeout, timedelta):
            timeout = timeout.total_seconds()
        self.timeout = timeout
        self.operation = operation
        self._task = None
    
    async def __aenter__(self):
        """Enter timeout context."""
        loop = asyncio.get_event_loop()
        self._task = asyncio.current_task()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit timeout context."""
        if exc_type is asyncio.CancelledError:
            raise TimeoutError(self.timeout, self.operation)
        return False


# Decorator support

def timeout(
    seconds: Union[float, timedelta],
    strategy: TimeoutStrategy = TimeoutStrategy.ASYNC,
    raise_on_timeout: bool = True,
    cleanup: Optional[Callable] = None
) -> Callable:
    """
    Decorator to add timeout to functions.
    
    Args:
        seconds: Timeout duration
        strategy: Timeout enforcement strategy
        raise_on_timeout: Whether to raise on timeout
        cleanup: Cleanup function to call on timeout
        
    Example:
        @timeout(5.0)
        def slow_operation():
            # Must complete in 5 seconds
            pass
    """
    if isinstance(seconds, (int, float)):
        timeout_duration = timedelta(seconds=seconds)
    else:
        timeout_duration = seconds
    
    config = TimeoutConfig(
        timeout=timeout_duration,
        strategy=strategy,
        raise_on_timeout=raise_on_timeout,
        cleanup_func=cleanup
    )
    
    def decorator(func: Callable) -> Callable:
        handler = TimeoutHandler(config)
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await handler.execute_async(func, *args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                return handler.execute(func, *args, **kwargs)
            return sync_wrapper
    
    return decorator


# Utility functions

def with_timeout(
    func: Callable[..., T],
    timeout: Union[float, timedelta],
    *args,
    **kwargs
) -> T:
    """
    Execute function with timeout.
    
    Convenience function for one-off timeout enforcement.
    """
    if isinstance(timeout, (int, float)):
        timeout = timedelta(seconds=timeout)
    
    config = TimeoutConfig(timeout=timeout)
    handler = TimeoutHandler(config)
    
    return handler.execute(func, *args, **kwargs)


async def with_timeout_async(
    func: Callable[..., Any],
    timeout: Union[float, timedelta],
    *args,
    **kwargs
) -> T:
    """
    Execute async function with timeout.
    
    Convenience function for one-off timeout enforcement.
    """
    if isinstance(timeout, (int, float)):
        timeout = timedelta(seconds=timeout)
    
    config = TimeoutConfig(timeout=timeout, strategy=TimeoutStrategy.ASYNC)
    handler = TimeoutHandler(config)
    
    return await handler.execute_async(func, *args, **kwargs)


class TimeoutPool:
    """
    Pool of timeout handlers for different operation types.
    
    Allows configuring different timeouts for different operations.
    """
    
    def __init__(self):
        """Initialize timeout pool."""
        self._timeouts: dict[str, TimeoutConfig] = {}
        self._default_timeout = TimeoutConfig(timedelta(seconds=30))
    
    def register(
        self,
        operation: str,
        timeout: Union[float, timedelta],
        **kwargs
    ) -> None:
        """Register timeout for operation."""
        if isinstance(timeout, (int, float)):
            timeout = timedelta(seconds=timeout)
        
        self._timeouts[operation] = TimeoutConfig(
            timeout=timeout,
            **kwargs
        )
    
    def get_handler(self, operation: str) -> TimeoutHandler:
        """Get timeout handler for operation."""
        config = self._timeouts.get(operation, self._default_timeout)
        return TimeoutHandler(config)
    
    def execute(
        self,
        operation: str,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """Execute function with operation-specific timeout."""
        handler = self.get_handler(operation)
        return handler.execute(func, *args, **kwargs)
    
    async def execute_async(
        self,
        operation: str,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> T:
        """Execute async function with operation-specific timeout."""
        handler = self.get_handler(operation)
        return await handler.execute_async(func, *args, **kwargs)


# Global timeout pool
_timeout_pool = TimeoutPool()


def register_timeout(
    operation: str,
    timeout: Union[float, timedelta],
    **kwargs
) -> None:
    """Register timeout for operation in global pool."""
    _timeout_pool.register(operation, timeout, **kwargs)


def execute_with_timeout(
    operation: str,
    func: Callable[..., T],
    *args,
    **kwargs
) -> T:
    """Execute function with registered timeout."""
    return _timeout_pool.execute(operation, func, *args, **kwargs)


async def execute_with_timeout_async(
    operation: str,
    func: Callable[..., Any],
    *args,
    **kwargs
) -> T:
    """Execute async function with registered timeout."""
    return await _timeout_pool.execute_async(operation, func, *args, **kwargs)