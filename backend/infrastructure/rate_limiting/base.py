"""
Base interfaces and abstractions for rate limiting.

This module provides the foundation for implementing different rate limiting
algorithms and strategies.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import asyncio


class RateLimitAlgorithm(Enum):
    """Available rate limiting algorithms."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(Enum):
    """Scope for rate limiting."""
    GLOBAL = "global"          # Same limit for all
    USER = "user"              # Per-user limits
    IP = "ip"                  # Per-IP limits
    ENDPOINT = "endpoint"      # Per-endpoint limits
    CUSTOM = "custom"          # Custom scope


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    algorithm: RateLimitAlgorithm
    capacity: int                    # Maximum requests/tokens
    refill_rate: float              # Tokens per second (for token bucket)
    window_size: timedelta          # Time window (for window-based)
    scope: RateLimitScope = RateLimitScope.USER
    burst_capacity: Optional[int] = None  # Allow bursts above capacity
    
    def __post_init__(self):
        if self.burst_capacity is None:
            self.burst_capacity = self.capacity


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining: int
    reset_at: datetime
    retry_after: Optional[timedelta] = None
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = self._generate_headers()
    
    def _generate_headers(self) -> Dict[str, str]:
        """Generate standard rate limit headers."""
        headers = {
            'X-RateLimit-Remaining': str(self.remaining),
            'X-RateLimit-Reset': str(int(self.reset_at.timestamp()))
        }
        
        if self.retry_after:
            headers['Retry-After'] = str(int(self.retry_after.total_seconds()))
            
        return headers


class IRateLimiter(ABC):
    """
    Abstract base class for rate limiters.
    
    Provides the interface that all rate limiting implementations must follow.
    """
    
    @abstractmethod
    async def check_rate_limit(
        self,
        key: str,
        cost: int = 1
    ) -> RateLimitResult:
        """
        Check if request is allowed under rate limit.
        
        Args:
            key: Identifier for rate limiting (e.g., user_id, ip)
            cost: Cost of this request (default 1)
            
        Returns:
            RateLimitResult indicating if allowed and remaining capacity
        """
        pass
    
    @abstractmethod
    async def consume(
        self,
        key: str,
        cost: int = 1
    ) -> bool:
        """
        Consume from rate limit if available.
        
        Args:
            key: Identifier for rate limiting
            cost: Cost to consume
            
        Returns:
            True if consumed successfully, False if rate limited
        """
        pass
    
    @abstractmethod
    async def reset(self, key: str) -> None:
        """
        Reset rate limit for a key.
        
        Args:
            key: Identifier to reset
        """
        pass
    
    @abstractmethod
    async def get_stats(self, key: str) -> Dict[str, Any]:
        """
        Get current stats for a key.
        
        Args:
            key: Identifier to check
            
        Returns:
            Dictionary with current state
        """
        pass


class IDistributedRateLimiter(IRateLimiter):
    """Extension for distributed rate limiting."""
    
    @abstractmethod
    async def sync_state(self) -> None:
        """Synchronize state across instances."""
        pass
    
    @abstractmethod
    async def get_global_stats(self) -> Dict[str, Any]:
        """Get aggregated stats across all instances."""
        pass


class RateLimitDecorator:
    """
    Decorator for rate limiting functions.
    
    Provides easy integration of rate limiting into existing code.
    """
    
    def __init__(
        self,
        limiter: IRateLimiter,
        key_extractor: Callable[..., str],
        cost: int = 1,
        on_limited: Optional[Callable] = None
    ):
        """
        Initialize rate limit decorator.
        
        Args:
            limiter: Rate limiter instance
            key_extractor: Function to extract rate limit key from arguments
            cost: Cost of each call
            on_limited: Optional callback when rate limited
        """
        self.limiter = limiter
        self.key_extractor = key_extractor
        self.cost = cost
        self.on_limited = on_limited
    
    def __call__(self, func: Callable) -> Callable:
        """Decorate function with rate limiting."""
        async def wrapper(*args, **kwargs):
            # Extract key
            key = self.key_extractor(*args, **kwargs)
            
            # Check rate limit
            result = await self.limiter.check_rate_limit(key, self.cost)
            
            if not result.allowed:
                if self.on_limited:
                    return await self.on_limited(result, *args, **kwargs)
                else:
                    raise RateLimitExceeded(result)
            
            # Consume and execute
            await self.limiter.consume(key, self.cost)
            return await func(*args, **kwargs)
        
        return wrapper


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, result: RateLimitResult):
        self.result = result
        super().__init__(f"Rate limit exceeded. Retry after {result.retry_after}")


class RateLimitStore(ABC):
    """Abstract storage backend for rate limit data."""
    
    @abstractmethod
    async def get_bucket(self, key: str) -> Optional[Dict[str, Any]]:
        """Get bucket data for a key."""
        pass
    
    @abstractmethod
    async def set_bucket(self, key: str, data: Dict[str, Any], ttl: Optional[timedelta] = None) -> None:
        """Set bucket data for a key."""
        pass
    
    @abstractmethod
    async def increment_counter(self, key: str, increment: int = 1) -> int:
        """Atomically increment a counter."""
        pass
    
    @abstractmethod
    async def add_to_window(self, key: str, timestamp: datetime, count: int = 1) -> None:
        """Add entry to sliding window."""
        pass
    
    @abstractmethod
    async def get_window_sum(self, key: str, start: datetime, end: datetime) -> int:
        """Get sum of entries in time window."""
        pass
    
    @abstractmethod
    async def cleanup_old_entries(self, before: datetime) -> int:
        """Remove old entries to prevent memory growth."""
        pass


class MemoryRateLimitStore(RateLimitStore):
    """In-memory implementation of rate limit store."""
    
    def __init__(self):
        self._buckets: Dict[str, Dict[str, Any]] = {}
        self._windows: Dict[str, List[Tuple[datetime, int]]] = {}
        self._lock = asyncio.Lock()
    
    async def get_bucket(self, key: str) -> Optional[Dict[str, Any]]:
        """Get bucket data for a key."""
        async with self._lock:
            return self._buckets.get(key)
    
    async def set_bucket(self, key: str, data: Dict[str, Any], ttl: Optional[timedelta] = None) -> None:
        """Set bucket data for a key."""
        async with self._lock:
            self._buckets[key] = data
            
            # Simple TTL implementation
            if ttl:
                async def expire():
                    await asyncio.sleep(ttl.total_seconds())
                    async with self._lock:
                        if key in self._buckets and self._buckets[key] == data:
                            del self._buckets[key]
                
                asyncio.create_task(expire())
    
    async def increment_counter(self, key: str, increment: int = 1) -> int:
        """Atomically increment a counter."""
        async with self._lock:
            if key not in self._buckets:
                self._buckets[key] = {'count': 0}
            
            self._buckets[key]['count'] += increment
            return self._buckets[key]['count']
    
    async def add_to_window(self, key: str, timestamp: datetime, count: int = 1) -> None:
        """Add entry to sliding window."""
        async with self._lock:
            if key not in self._windows:
                self._windows[key] = []
            
            self._windows[key].append((timestamp, count))
            
            # Keep sorted by timestamp
            self._windows[key].sort(key=lambda x: x[0])
    
    async def get_window_sum(self, key: str, start: datetime, end: datetime) -> int:
        """Get sum of entries in time window."""
        async with self._lock:
            if key not in self._windows:
                return 0
            
            total = 0
            for timestamp, count in self._windows[key]:
                if start <= timestamp <= end:
                    total += count
            
            return total
    
    async def cleanup_old_entries(self, before: datetime) -> int:
        """Remove old entries to prevent memory growth."""
        async with self._lock:
            removed = 0
            
            # Clean up windows
            for key in list(self._windows.keys()):
                original_len = len(self._windows[key])
                self._windows[key] = [
                    (ts, count) for ts, count in self._windows[key]
                    if ts >= before
                ]
                removed += original_len - len(self._windows[key])
                
                if not self._windows[key]:
                    del self._windows[key]
            
            return removed


class RateLimitStrategy:
    """
    Strategy for applying rate limits.
    
    Determines how rate limits are applied based on context.
    """
    
    def __init__(self):
        self._rules: List[RateLimitRule] = []
    
    def add_rule(self, rule: 'RateLimitRule') -> None:
        """Add a rate limit rule."""
        self._rules.append(rule)
        # Sort by priority
        self._rules.sort(key=lambda r: r.priority, reverse=True)
    
    async def get_applicable_limits(
        self,
        context: Dict[str, Any]
    ) -> List['RateLimitRule']:
        """
        Get applicable rate limit rules for context.
        
        Args:
            context: Request context (user, endpoint, etc.)
            
        Returns:
            List of applicable rules
        """
        applicable = []
        
        for rule in self._rules:
            if await rule.matches(context):
                applicable.append(rule)
                
                # Stop if exclusive rule
                if rule.exclusive:
                    break
        
        return applicable


@dataclass
class RateLimitRule:
    """Defines a rate limiting rule."""
    name: str
    config: RateLimitConfig
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    priority: int = 0
    exclusive: bool = False  # If True, stop checking other rules
    
    async def matches(self, context: Dict[str, Any]) -> bool:
        """Check if rule matches context."""
        if self.condition:
            return self.condition(context)
        return True


class CompositeRateLimiter(IRateLimiter):
    """
    Composite rate limiter that applies multiple limiters.
    
    Useful for applying different limits simultaneously.
    """
    
    def __init__(self, limiters: List[Tuple[str, IRateLimiter]]):
        """
        Initialize composite limiter.
        
        Args:
            limiters: List of (name, limiter) tuples
        """
        self.limiters = limiters
    
    async def check_rate_limit(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check all limiters and return most restrictive."""
        results = []
        
        for name, limiter in self.limiters:
            result = await limiter.check_rate_limit(key, cost)
            results.append((name, result))
        
        # Find most restrictive (not allowed or least remaining)
        most_restrictive = results[0][1]
        
        for name, result in results[1:]:
            if not result.allowed and most_restrictive.allowed:
                most_restrictive = result
            elif result.allowed and most_restrictive.allowed:
                if result.remaining < most_restrictive.remaining:
                    most_restrictive = result
        
        return most_restrictive
    
    async def consume(self, key: str, cost: int = 1) -> bool:
        """Consume from all limiters if all allow."""
        # First check all
        all_allowed = True
        for name, limiter in self.limiters:
            result = await limiter.check_rate_limit(key, cost)
            if not result.allowed:
                all_allowed = False
                break
        
        if not all_allowed:
            return False
        
        # Consume from all
        for name, limiter in self.limiters:
            await limiter.consume(key, cost)
        
        return True
    
    async def reset(self, key: str) -> None:
        """Reset all limiters."""
        for name, limiter in self.limiters:
            await limiter.reset(key)
    
    async def get_stats(self, key: str) -> Dict[str, Any]:
        """Get stats from all limiters."""
        stats = {}
        
        for name, limiter in self.limiters:
            stats[name] = await limiter.get_stats(key)
        
        return stats