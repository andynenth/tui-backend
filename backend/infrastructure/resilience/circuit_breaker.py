"""
Circuit breaker pattern implementation for fault tolerance.

Prevents cascading failures by stopping calls to failing services.
"""

from typing import TypeVar, Generic, Callable, Optional, Any, Dict, List
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
import threading
from contextlib import contextmanager
import logging
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: timedelta = timedelta(seconds=60)
    expected_exception: type = Exception
    exclude_exceptions: List[type] = field(default_factory=list)
    success_threshold: int = 1  # Successes needed to close from half-open
    timeout: Optional[timedelta] = None  # Call timeout
    
    def should_count_exception(self, exception: Exception) -> bool:
        """Check if exception should count as failure."""
        # Excluded exceptions don't count
        for excluded in self.exclude_exceptions:
            if isinstance(exception, excluded):
                return False
        
        # Count if it's the expected exception or a subclass
        return isinstance(exception, self.expected_exception)


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: List[tuple] = field(default_factory=list)
    
    def record_success(self) -> None:
        """Record successful call."""
        self.total_calls += 1
        self.successful_calls += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_success_time = datetime.utcnow()
    
    def record_failure(self) -> None:
        """Record failed call."""
        self.total_calls += 1
        self.failed_calls += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = datetime.utcnow()
    
    def record_rejection(self) -> None:
        """Record rejected call."""
        self.rejected_calls += 1
    
    def reset_counts(self) -> None:
        """Reset consecutive counts."""
        self.consecutive_failures = 0
        self.consecutive_successes = 0
    
    def get_failure_rate(self) -> float:
        """Get failure rate."""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls


T = TypeVar('T')


class CircuitBreaker(Generic[T]):
    """
    Circuit breaker implementation.
    
    Protects against cascading failures by monitoring call failures
    and temporarily blocking calls when failure threshold is exceeded.
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """Initialize circuit breaker."""
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._state_lock = threading.RLock()
        self._half_open_lock = threading.Lock()
        
        # Callbacks
        self._on_state_change: List[Callable] = []
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    @property
    def state(self) -> CircuitState:
        """Get current state."""
        with self._state_lock:
            # Check if should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
            
            return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting calls)."""
        return self.state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing)."""
        return self.state == CircuitState.HALF_OPEN
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function fails
        """
        if self.is_open:
            self._stats.record_rejection()
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN"
            )
        
        # For half-open state, only allow one call at a time
        if self.is_half_open:
            if not self._half_open_lock.acquire(blocking=False):
                self._stats.record_rejection()
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is HALF_OPEN and busy"
                )
            
            try:
                return self._execute_call(func, *args, **kwargs)
            finally:
                self._half_open_lock.release()
        else:
            return self._execute_call(func, *args, **kwargs)
    
    async def call_async(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> T:
        """
        Execute async function through circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function fails
        """
        if self.is_open:
            self._stats.record_rejection()
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN"
            )
        
        # For half-open state, only allow one call at a time
        if self.is_half_open:
            # Use asyncio lock for async context
            if not hasattr(self, '_async_half_open_lock'):
                self._async_half_open_lock = asyncio.Lock()
            
            try:
                await self._async_half_open_lock.acquire()
                return await self._execute_call_async(func, *args, **kwargs)
            finally:
                self._async_half_open_lock.release()
        else:
            return await self._execute_call_async(func, *args, **kwargs)
    
    def _execute_call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute synchronous call with monitoring."""
        try:
            # Apply timeout if configured
            if self.config.timeout:
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError(
                        f"Call timed out after {self.config.timeout.total_seconds()}s"
                    )
                
                # Set timeout
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(self.config.timeout.total_seconds()))
                
                try:
                    result = func(*args, **kwargs)
                finally:
                    # Cancel timeout
                    signal.alarm(0)
            else:
                result = func(*args, **kwargs)
            
            # Record success
            self._on_success()
            return result
            
        except Exception as e:
            # Record failure if applicable
            if self.config.should_count_exception(e):
                self._on_failure()
            raise
    
    async def _execute_call_async(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> T:
        """Execute asynchronous call with monitoring."""
        try:
            # Apply timeout if configured
            if self.config.timeout:
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout.total_seconds()
                )
            else:
                result = await func(*args, **kwargs)
            
            # Record success
            self._on_success()
            return result
            
        except Exception as e:
            # Record failure if applicable
            if self.config.should_count_exception(e):
                self._on_failure()
            raise
    
    def _on_success(self) -> None:
        """Handle successful call."""
        with self._state_lock:
            self._stats.record_success()
            
            if self._state == CircuitState.HALF_OPEN:
                if self._stats.consecutive_successes >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        with self._state_lock:
            self._stats.record_failure()
            
            if self._state == CircuitState.CLOSED:
                if self._stats.consecutive_failures >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt reset from OPEN state."""
        if not self._stats.last_failure_time:
            return True
        
        time_since_failure = datetime.utcnow() - self._stats.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state."""
        if self._state == new_state:
            return
        
        old_state = self._state
        self._state = new_state
        self._stats.state_changes.append((
            datetime.utcnow(),
            old_state,
            new_state
        ))
        
        # Reset counts on state change
        if new_state == CircuitState.CLOSED:
            self._stats.reset_counts()
        
        logger.info(
            f"Circuit breaker '{self.name}' transitioned from "
            f"{old_state.value} to {new_state.value}"
        )
        
        # Notify callbacks
        for callback in self._on_state_change:
            try:
                callback(self, old_state, new_state)
            except Exception as e:
                logger.error(f"State change callback error: {e}")
    
    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._state_lock:
            self._transition_to(CircuitState.CLOSED)
            self._stats.reset_counts()
    
    def open(self) -> None:
        """Manually open circuit breaker."""
        with self._state_lock:
            self._transition_to(CircuitState.OPEN)
    
    def on_state_change(self, callback: Callable) -> None:
        """Register state change callback."""
        self._on_state_change.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        with self._state_lock:
            return {
                'name': self.name,
                'state': self._state.value,
                'total_calls': self._stats.total_calls,
                'successful_calls': self._stats.successful_calls,
                'failed_calls': self._stats.failed_calls,
                'rejected_calls': self._stats.rejected_calls,
                'failure_rate': self._stats.get_failure_rate(),
                'consecutive_failures': self._stats.consecutive_failures,
                'consecutive_successes': self._stats.consecutive_successes,
                'last_failure_time': self._stats.last_failure_time.isoformat()
                    if self._stats.last_failure_time else None,
                'last_success_time': self._stats.last_success_time.isoformat()
                    if self._stats.last_success_time else None,
                'state_changes': [
                    {
                        'timestamp': ts.isoformat(),
                        'from': old.value,
                        'to': new.value
                    }
                    for ts, old, new in self._stats.state_changes[-10:]
                ]
            }
    
    @contextmanager
    def guard(self):
        """Context manager for guarded execution."""
        if self.is_open:
            self._stats.record_rejection()
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN"
            )
        
        # For half-open, use lock
        if self.is_half_open:
            if not self._half_open_lock.acquire(blocking=False):
                self._stats.record_rejection()
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is HALF_OPEN and busy"
                )
            
            try:
                yield self
            except Exception as e:
                if self.config.should_count_exception(e):
                    self._on_failure()
                raise
            else:
                self._on_success()
            finally:
                self._half_open_lock.release()
        else:
            try:
                yield self
            except Exception as e:
                if self.config.should_count_exception(e):
                    self._on_failure()
                raise
            else:
                self._on_success()


# Decorator support

def circuit_breaker(
    name: Optional[str] = None,
    config: Optional[CircuitBreakerConfig] = None
) -> Callable:
    """
    Decorator to apply circuit breaker to function.
    
    Args:
        name: Circuit breaker name (defaults to function name)
        config: Circuit breaker configuration
        
    Example:
        @circuit_breaker(name="external_api")
        def call_api():
            # API call
            pass
    """
    def decorator(func: Callable) -> Callable:
        cb_name = name or f"{func.__module__}.{func.__name__}"
        breaker = CircuitBreaker(cb_name, config)
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                return await breaker.call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                return breaker.call(func, *args, **kwargs)
            return sync_wrapper
    
    return decorator


# Circuit breaker registry

class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        """Initialize registry."""
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def register(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Register a circuit breaker."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)
    
    def get_all(self) -> Dict[str, CircuitBreaker]:
        """Get all circuit breakers."""
        return self._breakers.copy()
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all breakers."""
        return {
            name: breaker.get_stats()
            for name, breaker in self._breakers.items()
        }


# Global registry
_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Get or create circuit breaker from global registry."""
    return _registry.register(name, config)


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all registered circuit breakers."""
    return _registry.get_all()


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers."""
    _registry.reset_all()