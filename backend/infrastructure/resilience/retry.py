"""
Retry mechanism with exponential backoff and jitter.

Provides resilient retry logic for transient failures.
"""

from typing import TypeVar, Callable, Optional, List, Any, Union
from dataclasses import dataclass, field
from datetime import timedelta
import asyncio
import time
import random
import logging
from functools import wraps
from enum import Enum


logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry backoff strategies."""

    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, last_exception: Exception, attempts: int):
        self.last_exception = last_exception
        self.attempts = attempts
        super().__init__(
            f"Retry exhausted after {attempts} attempts. "
            f"Last error: {last_exception}"
        )


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    initial_delay: timedelta = timedelta(seconds=1)
    max_delay: timedelta = timedelta(seconds=60)
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_range: float = 0.1  # ±10% jitter
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL

    # Exceptions to retry
    retry_on: List[type] = field(default_factory=lambda: [Exception])
    # Exceptions to not retry
    dont_retry_on: List[type] = field(default_factory=list)

    # Callbacks
    on_retry: Optional[Callable] = None
    on_success: Optional[Callable] = None
    on_exhausted: Optional[Callable] = None

    def should_retry(self, exception: Exception) -> bool:
        """Check if exception should trigger retry."""
        # Don't retry if in exclusion list
        for exc_type in self.dont_retry_on:
            if isinstance(exception, exc_type):
                return False

        # Retry if in inclusion list
        for exc_type in self.retry_on:
            if isinstance(exception, exc_type):
                return True

        return False

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for attempt number."""
        if self.strategy == RetryStrategy.FIXED:
            delay = self.initial_delay.total_seconds()

        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay.total_seconds() * attempt

        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay.total_seconds() * (
                self.exponential_base ** (attempt - 1)
            )

        elif self.strategy == RetryStrategy.FIBONACCI:
            # Fibonacci sequence
            a, b = 1, 1
            for _ in range(attempt - 1):
                a, b = b, a + b
            delay = self.initial_delay.total_seconds() * a

        else:
            delay = self.initial_delay.total_seconds()

        # Apply max delay cap
        delay = min(delay, self.max_delay.total_seconds())

        # Apply jitter
        if self.jitter:
            jitter_amount = delay * self.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)  # Ensure non-negative


@dataclass
class RetryStats:
    """Statistics for retry operations."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_attempts: int = 0
    total_delay_seconds: float = 0.0

    def record_success(self, attempts: int, total_delay: float) -> None:
        """Record successful call."""
        self.total_calls += 1
        self.successful_calls += 1
        self.total_attempts += attempts
        self.total_delay_seconds += total_delay

    def record_failure(self, attempts: int, total_delay: float) -> None:
        """Record failed call."""
        self.total_calls += 1
        self.failed_calls += 1
        self.total_attempts += attempts
        self.total_delay_seconds += total_delay

    def get_average_attempts(self) -> float:
        """Get average attempts per call."""
        if self.total_calls == 0:
            return 0.0
        return self.total_attempts / self.total_calls

    def get_success_rate(self) -> float:
        """Get success rate."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls


T = TypeVar("T")


class Retry:
    """
    Retry mechanism with configurable backoff strategies.

    Supports synchronous and asynchronous operations with
    exponential backoff, jitter, and comprehensive statistics.
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry mechanism."""
        self.config = config or RetryConfig()
        self.stats = RetryStats()

    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RetryExhaustedError: If all retries fail
        """
        last_exception = None
        total_delay = 0.0

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                # Execute function
                result = func(*args, **kwargs)

                # Success callback
                if self.config.on_success:
                    self.config.on_success(attempt, result)

                # Record stats
                self.stats.record_success(attempt, total_delay)

                return result

            except Exception as e:
                last_exception = e

                # Check if should retry
                if not self.config.should_retry(e):
                    self.stats.record_failure(attempt, total_delay)
                    raise

                # Check if exhausted
                if attempt >= self.config.max_attempts:
                    break

                # Calculate delay
                delay = self.config.calculate_delay(attempt)
                total_delay += delay

                # Retry callback
                if self.config.on_retry:
                    self.config.on_retry(attempt, e, delay)

                logger.warning(
                    f"Retry attempt {attempt}/{self.config.max_attempts} "
                    f"failed: {e}. Retrying in {delay:.2f}s..."
                )

                # Sleep before retry
                time.sleep(delay)

        # All retries exhausted
        self.stats.record_failure(self.config.max_attempts, total_delay)

        # Exhausted callback
        if self.config.on_exhausted:
            self.config.on_exhausted(last_exception, self.config.max_attempts)

        raise RetryExhaustedError(last_exception, self.config.max_attempts)

    async def execute_async(self, func: Callable[..., Any], *args, **kwargs) -> T:
        """
        Execute async function with retry logic.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RetryExhaustedError: If all retries fail
        """
        last_exception = None
        total_delay = 0.0

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Success callback
                if self.config.on_success:
                    if asyncio.iscoroutinefunction(self.config.on_success):
                        await self.config.on_success(attempt, result)
                    else:
                        self.config.on_success(attempt, result)

                # Record stats
                self.stats.record_success(attempt, total_delay)

                return result

            except Exception as e:
                last_exception = e

                # Check if should retry
                if not self.config.should_retry(e):
                    self.stats.record_failure(attempt, total_delay)
                    raise

                # Check if exhausted
                if attempt >= self.config.max_attempts:
                    break

                # Calculate delay
                delay = self.config.calculate_delay(attempt)
                total_delay += delay

                # Retry callback
                if self.config.on_retry:
                    if asyncio.iscoroutinefunction(self.config.on_retry):
                        await self.config.on_retry(attempt, e, delay)
                    else:
                        self.config.on_retry(attempt, e, delay)

                logger.warning(
                    f"Retry attempt {attempt}/{self.config.max_attempts} "
                    f"failed: {e}. Retrying in {delay:.2f}s..."
                )

                # Sleep before retry
                await asyncio.sleep(delay)

        # All retries exhausted
        self.stats.record_failure(self.config.max_attempts, total_delay)

        # Exhausted callback
        if self.config.on_exhausted:
            if asyncio.iscoroutinefunction(self.config.on_exhausted):
                await self.config.on_exhausted(last_exception, self.config.max_attempts)
            else:
                self.config.on_exhausted(last_exception, self.config.max_attempts)

        raise RetryExhaustedError(last_exception, self.config.max_attempts)

    def get_stats(self) -> dict:
        """Get retry statistics."""
        return {
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "failed_calls": self.stats.failed_calls,
            "success_rate": self.stats.get_success_rate(),
            "average_attempts": self.stats.get_average_attempts(),
            "total_delay_seconds": self.stats.total_delay_seconds,
        }


# Decorator support


def retry(
    max_attempts: int = 3,
    initial_delay: Union[float, timedelta] = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retry_on: Optional[List[type]] = None,
    dont_retry_on: Optional[List[type]] = None,
    **kwargs,
) -> Callable:
    """
    Decorator to add retry logic to functions.

    Args:
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay (seconds or timedelta)
        strategy: Backoff strategy
        retry_on: Exception types to retry
        dont_retry_on: Exception types to not retry
        **kwargs: Additional config options

    Example:
        @retry(max_attempts=5, initial_delay=2.0)
        def flaky_operation():
            # May fail transiently
            pass
    """
    # Convert delay to timedelta
    if isinstance(initial_delay, (int, float)):
        initial_delay = timedelta(seconds=initial_delay)

    # Create config
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        strategy=strategy,
        retry_on=retry_on or [Exception],
        dont_retry_on=dont_retry_on or [],
        **kwargs,
    )

    def decorator(func: Callable) -> Callable:
        retry_instance = Retry(config)

        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await retry_instance.execute_async(func, *args, **kwargs)

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return retry_instance.execute(func, *args, **kwargs)

            return sync_wrapper

    return decorator


# Convenience functions


def exponential_backoff_retry(
    func: Callable[..., T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    *args,
    **kwargs,
) -> T:
    """
    Execute function with exponential backoff retry.

    Convenience function for common retry pattern.
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=timedelta(seconds=initial_delay),
        max_delay=timedelta(seconds=max_delay),
        exponential_base=exponential_base,
        strategy=RetryStrategy.EXPONENTIAL,
    )

    retry_instance = Retry(config)
    return retry_instance.execute(func, *args, **kwargs)


async def exponential_backoff_retry_async(
    func: Callable[..., Any],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    *args,
    **kwargs,
) -> T:
    """
    Execute async function with exponential backoff retry.

    Convenience function for common retry pattern.
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=timedelta(seconds=initial_delay),
        max_delay=timedelta(seconds=max_delay),
        exponential_base=exponential_base,
        strategy=RetryStrategy.EXPONENTIAL,
    )

    retry_instance = Retry(config)
    return await retry_instance.execute_async(func, *args, **kwargs)


# Retry policy presets


class RetryPolicies:
    """Common retry policy configurations."""

    @staticmethod
    def aggressive() -> RetryConfig:
        """Aggressive retry for critical operations."""
        return RetryConfig(
            max_attempts=10,
            initial_delay=timedelta(milliseconds=100),
            max_delay=timedelta(seconds=30),
            exponential_base=1.5,
            jitter=True,
        )

    @staticmethod
    def standard() -> RetryConfig:
        """Standard retry for most operations."""
        return RetryConfig(
            max_attempts=3,
            initial_delay=timedelta(seconds=1),
            max_delay=timedelta(seconds=10),
            exponential_base=2.0,
            jitter=True,
        )

    @staticmethod
    def conservative() -> RetryConfig:
        """Conservative retry for rate-limited operations."""
        return RetryConfig(
            max_attempts=3,
            initial_delay=timedelta(seconds=5),
            max_delay=timedelta(seconds=60),
            exponential_base=3.0,
            jitter=True,
        )

    @staticmethod
    def linear() -> RetryConfig:
        """Linear backoff for predictable delays."""
        return RetryConfig(
            max_attempts=5,
            initial_delay=timedelta(seconds=2),
            strategy=RetryStrategy.LINEAR,
            jitter=False,
        )
