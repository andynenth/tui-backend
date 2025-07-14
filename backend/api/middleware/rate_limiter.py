# backend/api/middleware/rate_limiter.py

"""
Rate limiting middleware for FastAPI to prevent abuse and DoS attacks.

Implements token bucket algorithm for flexible rate limiting with:
- Per-IP rate limiting for anonymous requests
- Per-player rate limiting for authenticated requests
- Different limits for different endpoints
- WebSocket connection rate limiting
"""

import time
from collections import defaultdict
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, Request, WebSocket
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimiter:
    """
    Token bucket rate limiter implementation.
    
    Each client gets a bucket with a maximum number of tokens.
    Tokens are replenished at a fixed rate.
    Each request consumes one or more tokens.
    """
    
    def __init__(
        self,
        max_tokens: int = 60,
        refill_rate: float = 1.0,
        time_window: int = 60
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_tokens: Maximum tokens in bucket
            refill_rate: Tokens added per second
            time_window: Time window in seconds for rate calculation
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.time_window = time_window
        self.buckets: Dict[str, Tuple[float, float]] = {}  # key -> (tokens, last_update)
        
    def is_allowed(self, key: str, tokens_required: int = 1) -> Tuple[bool, int]:
        """
        Check if request is allowed and consume tokens.
        
        Args:
            key: Unique identifier (IP, player_id, etc.)
            tokens_required: Number of tokens to consume
            
        Returns:
            Tuple of (allowed, tokens_remaining)
        """
        current_time = time.time()
        
        if key in self.buckets:
            tokens, last_update = self.buckets[key]
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = current_time - last_update
            tokens_to_add = time_elapsed * self.refill_rate
            
            # Update token count (cap at max_tokens)
            tokens = min(self.max_tokens, tokens + tokens_to_add)
        else:
            # New client starts with full bucket
            tokens = self.max_tokens
            
        # Check if enough tokens available
        if tokens >= tokens_required:
            # Consume tokens
            tokens -= tokens_required
            self.buckets[key] = (tokens, current_time)
            return True, int(tokens)
        else:
            # Not enough tokens, update timestamp but don't consume
            self.buckets[key] = (tokens, current_time)
            return False, int(tokens)
            
    def cleanup_old_buckets(self, max_age: int = 3600):
        """
        Remove buckets that haven't been used recently.
        
        Args:
            max_age: Maximum age in seconds before bucket is removed
        """
        current_time = time.time()
        keys_to_remove = []
        
        for key, (_, last_update) in self.buckets.items():
            if current_time - last_update > max_age:
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            del self.buckets[key]


class RateLimitConfig:
    """Configuration for different rate limit tiers."""
    
    # Default limits (requests per minute)
    DEFAULT = {"max_tokens": 60, "refill_rate": 1.0}  # 60 requests/minute
    
    # Specific endpoint limits
    ENDPOINTS = {
        # REST API endpoints
        "/api/rooms": {"max_tokens": 30, "refill_rate": 0.5},  # Create room
        "/api/rooms/{room_id}/join": {"max_tokens": 10, "refill_rate": 0.17},  # Join room
        "/api/rooms/{room_id}/start": {"max_tokens": 5, "refill_rate": 0.08},  # Start game
        
        # WebSocket events (per connection)
        "ws_connect": {"max_tokens": 5, "refill_rate": 0.08},  # 5 connections/minute
        "ws_message": {"max_tokens": 120, "refill_rate": 2.0},  # 120 messages/minute
        "ws_declare": {"max_tokens": 10, "refill_rate": 0.17},  # 10 declarations/minute
        "ws_play": {"max_tokens": 30, "refill_rate": 0.5},  # 30 plays/minute
    }
    
    @classmethod
    def get_config(cls, endpoint: str) -> dict:
        """Get rate limit config for endpoint."""
        return cls.ENDPOINTS.get(endpoint, cls.DEFAULT)


# Global rate limiters
rest_limiter = RateLimiter()
ws_connect_limiter = RateLimiter(**RateLimitConfig.get_config("ws_connect"))
ws_message_limiters: Dict[str, RateLimiter] = {}  # Per-connection limiters


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for REST API rate limiting.
    """
    
    def __init__(self, app, limiter: Optional[RateLimiter] = None):
        super().__init__(app)
        self.limiter = limiter or rest_limiter
        
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for static files and docs
        if request.url.path.startswith(("/static", "/docs", "/openapi.json")):
            return await call_next(request)
            
        # Get client identifier (IP address)
        client_ip = request.client.host
        
        # Get endpoint-specific config
        endpoint_config = RateLimitConfig.get_config(request.url.path)
        
        # Check rate limit
        allowed, tokens_remaining = self.limiter.is_allowed(client_ip)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                },
                headers={
                    "X-RateLimit-Limit": str(endpoint_config["max_tokens"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + 60),
                    "Retry-After": "60"
                }
            )
            
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(endpoint_config["max_tokens"])
        response.headers["X-RateLimit-Remaining"] = str(tokens_remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response


async def check_websocket_rate_limit(
    websocket: WebSocket,
    event_type: str = "ws_message"
) -> Tuple[bool, Optional[str]]:
    """
    Check rate limit for WebSocket events.
    
    Args:
        websocket: WebSocket connection
        event_type: Type of WebSocket event
        
    Returns:
        Tuple of (allowed, error_message)
    """
    # Get client identifier
    client_ip = websocket.client.host
    connection_id = f"{client_ip}:{websocket.client.port}"
    
    # Check connection rate limit for new connections
    if event_type == "ws_connect":
        allowed, _ = ws_connect_limiter.is_allowed(client_ip)
        if not allowed:
            return False, "Too many connections. Please try again later."
    
    # Get or create message limiter for this connection
    if connection_id not in ws_message_limiters:
        config = RateLimitConfig.get_config(event_type)
        ws_message_limiters[connection_id] = RateLimiter(**config)
    
    limiter = ws_message_limiters[connection_id]
    
    # Check message rate limit
    allowed, tokens_remaining = limiter.is_allowed(connection_id)
    
    if not allowed:
        return False, f"Rate limit exceeded for {event_type}. Slow down!"
        
    return True, None


def cleanup_websocket_limiter(websocket: WebSocket):
    """
    Clean up rate limiter for disconnected WebSocket.
    
    Args:
        websocket: WebSocket connection that disconnected
    """
    client_ip = websocket.client.host
    connection_id = f"{client_ip}:{websocket.client.port}"
    
    if connection_id in ws_message_limiters:
        del ws_message_limiters[connection_id]


# Periodic cleanup task (should be scheduled)
async def cleanup_old_rate_limit_buckets():
    """
    Periodic task to clean up old rate limit buckets.
    Should be run every hour.
    """
    rest_limiter.cleanup_old_buckets()
    ws_connect_limiter.cleanup_old_buckets()
    
    # Clean up old WebSocket limiters
    for limiter in ws_message_limiters.values():
        limiter.cleanup_old_buckets()