"""
Rate limiting infrastructure for protecting against abuse.

This module provides:
- Multiple rate limiting algorithms (token bucket, sliding window)
- Distributed rate limiting support
- WebSocket-specific rate limiting
- Middleware for easy integration
- Adaptive rate limiting based on context
"""

from datetime import timedelta

from .base import (
    # Enums
    RateLimitAlgorithm,
    RateLimitScope,
    
    # Configuration
    RateLimitConfig,
    RateLimitResult,
    RateLimitRule,
    
    # Interfaces
    IRateLimiter,
    IDistributedRateLimiter,
    
    # Stores
    RateLimitStore,
    MemoryRateLimitStore,
    
    # Utilities
    RateLimitDecorator,
    RateLimitExceeded,
    RateLimitStrategy,
    CompositeRateLimiter
)

from .token_bucket import (
    TokenBucketRateLimiter,
    OptimizedTokenBucket,
    AdaptiveTokenBucket
)

from .sliding_window import (
    SlidingWindowRateLimiter,
    OptimizedSlidingWindow,
    SlidingWindowLog,
    CircularBuffer
)

from .distributed import (
    RedisRateLimitStore,
    DistributedTokenBucket,
    DistributedSlidingWindow,
    ConsistentHashRateLimiter
)

from .middleware import (
    RateLimitMiddleware,
    WebSocketRateLimiter,
    rate_limit,
    RateLimitingStrategy,
    create_tiered_rate_limiting,
    create_endpoint_rate_limiting
)

from .websocket_limiter import (
    GameActionCost,
    GameWebSocketRateLimiter,
    AdaptiveGameRateLimiter,
    ConnectionInfo
)

__all__ = [
    # Base
    'RateLimitAlgorithm',
    'RateLimitScope',
    'RateLimitConfig',
    'RateLimitResult',
    'RateLimitRule',
    'IRateLimiter',
    'IDistributedRateLimiter',
    'RateLimitStore',
    'MemoryRateLimitStore',
    'RateLimitDecorator',
    'RateLimitExceeded',
    'RateLimitStrategy',
    'CompositeRateLimiter',
    
    # Token Bucket
    'TokenBucketRateLimiter',
    'OptimizedTokenBucket',
    'AdaptiveTokenBucket',
    
    # Sliding Window
    'SlidingWindowRateLimiter',
    'OptimizedSlidingWindow',
    'SlidingWindowLog',
    'CircularBuffer',
    
    # Distributed
    'RedisRateLimitStore',
    'DistributedTokenBucket',
    'DistributedSlidingWindow',
    'ConsistentHashRateLimiter',
    
    # Middleware
    'RateLimitMiddleware',
    'WebSocketRateLimiter',
    'rate_limit',
    'RateLimitingStrategy',
    'create_tiered_rate_limiting',
    'create_endpoint_rate_limiting',
    
    # Game-specific
    'GameActionCost',
    'GameWebSocketRateLimiter',
    'AdaptiveGameRateLimiter',
    'ConnectionInfo'
]


# Convenience factory functions

def create_rate_limiter(
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET,
    capacity: int = 100,
    window_size: timedelta = None,
    refill_rate: float = 1.0
) -> IRateLimiter:
    """
    Create a rate limiter with sensible defaults.
    
    Args:
        algorithm: Which algorithm to use
        capacity: Maximum requests/tokens
        window_size: Time window (for window-based algorithms)
        refill_rate: Tokens per second (for token bucket)
        
    Returns:
        Configured rate limiter
    """
    from datetime import timedelta
    
    if algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
        config = RateLimitConfig(
            algorithm=algorithm,
            capacity=capacity,
            refill_rate=refill_rate,
            window_size=window_size or timedelta(minutes=1)
        )
        return TokenBucketRateLimiter(config)
    
    elif algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
        config = RateLimitConfig(
            algorithm=algorithm,
            capacity=capacity,
            refill_rate=refill_rate,
            window_size=window_size or timedelta(minutes=1)
        )
        return SlidingWindowRateLimiter(config)
    
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def create_game_rate_limiter(
    player_limit: int = 60,
    room_limit: int = 300,
    adaptive: bool = True
) -> GameWebSocketRateLimiter:
    """
    Create a rate limiter configured for game WebSocket.
    
    Args:
        player_limit: Requests per minute per player
        room_limit: Requests per minute per room
        adaptive: Whether to use adaptive limits
        
    Returns:
        Configured game rate limiter
    """
    from datetime import timedelta
    
    if adaptive:
        return AdaptiveGameRateLimiter(base_multiplier=1.0)
    
    # Player limiter - token bucket for burst support
    player_config = RateLimitConfig(
        algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
        capacity=player_limit,
        refill_rate=player_limit / 60.0,  # Per second
        burst_capacity=player_limit * 2
    )
    player_limiter = TokenBucketRateLimiter(player_config)
    
    # Room limiter - sliding window for accurate limiting
    room_config = RateLimitConfig(
        algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
        capacity=room_limit,
        window_size=timedelta(minutes=1),
        refill_rate=0  # Not used for sliding window
    )
    room_limiter = SlidingWindowRateLimiter(room_config)
    
    return GameWebSocketRateLimiter(
        player_limiter=player_limiter,
        room_limiter=room_limiter
    )