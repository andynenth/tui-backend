# backend/api/middleware/rate_limit.py

import asyncio
import time
import logging
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
import hashlib

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Set up structured logging
logger = logging.getLogger(__name__)


# Custom formatter for rate limit logs
class RateLimitLogFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, "rate_limit_data"):
            # Add rate limit specific data to log
            record.msg = f"{record.msg} | {json.dumps(record.rate_limit_data)}"
        return super().format(record)


# Import error codes if available
try:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), "../../../shared"))
    from error_codes import ErrorCode, create_standard_error

    ERROR_CODES_AVAILABLE = True
except ImportError:
    ERROR_CODES_AVAILABLE = False


@dataclass
class RateLimitRule:
    """Defines a rate limiting rule"""

    requests: int  # Number of requests allowed
    window_seconds: int  # Time window in seconds
    burst_multiplier: float = 1.5  # Allow burst traffic up to this multiplier
    block_duration_seconds: int = 60  # How long to block after limit exceeded


@dataclass
class RateLimitStats:
    """Track rate limiting statistics"""

    total_requests: int = 0
    blocked_requests: int = 0
    unique_clients: set = field(default_factory=set)
    last_reset: datetime = field(default_factory=datetime.now)


class RateLimiter:
    """
    Token bucket rate limiter implementation.

    Supports:
    - Per-IP rate limiting
    - Per-route rate limiting
    - WebSocket message rate limiting
    - Burst traffic handling
    - Temporary blocking for repeat offenders
    """

    def __init__(self):
        # Store request timestamps per identifier
        self.requests: Dict[str, deque] = defaultdict(deque)
        # Store blocked clients
        self.blocked_until: Dict[str, float] = {}
        # Statistics
        self.stats: Dict[str, RateLimitStats] = defaultdict(RateLimitStats)
        # Cleanup task
        self._cleanup_task = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Start the cleanup task"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the cleanup task"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self):
        """Periodically clean up old data"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Rate limiter cleanup error: {e}")

    async def _cleanup_old_data(self):
        """Remove old request records and expired blocks"""
        async with self._lock:
            current_time = time.time()

            # Clean up blocked clients
            expired_blocks = [
                client_id
                for client_id, blocked_until in self.blocked_until.items()
                if blocked_until < current_time
            ]
            for client_id in expired_blocks:
                del self.blocked_until[client_id]

            # Clean up old request records (older than 1 hour)
            cutoff_time = current_time - 3600
            for client_id in list(self.requests.keys()):
                # Remove old timestamps
                while (
                    self.requests[client_id]
                    and self.requests[client_id][0] < cutoff_time
                ):
                    self.requests[client_id].popleft()

                # Remove empty deques
                if not self.requests[client_id]:
                    del self.requests[client_id]

    def _get_client_identifier(
        self,
        request: Optional[Request] = None,
        client_ip: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Generate a unique identifier for rate limiting"""
        if user_id:
            return f"user:{user_id}"
        elif client_ip:
            return f"ip:{client_ip}"
        elif request:
            # Extract IP from request
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = request.client.host if request.client else "unknown"
            return f"ip:{client_ip}"
        else:
            return "ip:unknown"

    async def check_rate_limit(
        self, identifier: str, rule: RateLimitRule, route: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if a request should be rate limited.

        Returns:
            Tuple of (allowed, rate_limit_info)
            - allowed: True if request is allowed, False if rate limited
            - rate_limit_info: Dict with rate limit headers/info
        """
        async with self._lock:
            current_time = time.time()

            # Update stats
            stats_key = route or "global"
            self.stats[stats_key].total_requests += 1
            self.stats[stats_key].unique_clients.add(identifier)

            # Check if client is blocked
            if identifier in self.blocked_until:
                if self.blocked_until[identifier] > current_time:
                    self.stats[stats_key].blocked_requests += 1
                    retry_after = int(self.blocked_until[identifier] - current_time)
                    return False, {
                        "retry_after": retry_after,
                        "blocked": True,
                        "reason": "Temporarily blocked due to repeated rate limit violations",
                    }
                else:
                    # Block expired, remove it
                    del self.blocked_until[identifier]

            # Get request history
            request_times = self.requests[identifier]

            # Remove timestamps outside the window
            window_start = current_time - rule.window_seconds
            while request_times and request_times[0] < window_start:
                request_times.popleft()

            # Check rate limit
            request_count = len(request_times)
            max_requests = int(rule.requests * rule.burst_multiplier)

            if request_count >= max_requests:
                # Rate limit exceeded
                self.stats[stats_key].blocked_requests += 1

                # Check for repeat offender (multiple violations in short time)
                recent_requests = sum(1 for t in request_times if t > current_time - 60)
                if recent_requests > rule.requests * 2:
                    # Block the client temporarily
                    self.blocked_until[identifier] = (
                        current_time + rule.block_duration_seconds
                    )

                    # Log repeat offender
                    logger.warning(
                        "Rate limit: Client blocked for repeat violations",
                        extra={
                            "rate_limit_data": {
                                "client_id": identifier,
                                "route": route,
                                "recent_requests": recent_requests,
                                "limit": rule.requests,
                                "block_duration": rule.block_duration_seconds,
                                "event": "client_blocked",
                            }
                        },
                    )

                # Calculate retry after
                oldest_request = request_times[0] if request_times else current_time
                retry_after = int(
                    oldest_request + rule.window_seconds - current_time + 1
                )

                # Log rate limit violation
                logger.info(
                    "Rate limit exceeded",
                    extra={
                        "rate_limit_data": {
                            "client_id": identifier,
                            "route": route,
                            "request_count": request_count,
                            "limit": max_requests,
                            "window": rule.window_seconds,
                            "retry_after": retry_after,
                            "event": "rate_limit_exceeded",
                        }
                    },
                )

                return False, {
                    "retry_after": retry_after,
                    "limit": rule.requests,
                    "window": rule.window_seconds,
                    "current": request_count,
                }

            # Request allowed
            request_times.append(current_time)

            # Calculate remaining requests
            remaining = rule.requests - len(request_times)
            reset_time = int(window_start + rule.window_seconds)

            # Debug logging if enabled
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Rate limit check passed",
                    extra={
                        "rate_limit_data": {
                            "client_id": identifier,
                            "route": route,
                            "request_count": request_count + 1,
                            "limit": rule.requests,
                            "remaining": max(0, remaining),
                            "event": "rate_limit_allowed",
                        }
                    },
                )

            return True, {
                "limit": rule.requests,
                "remaining": max(0, remaining),
                "reset": reset_time,
                "window": rule.window_seconds,
            }

    async def check_websocket_rate_limit(
        self, room_id: str, client_id: str, event_type: str, rule: RateLimitRule
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check rate limit for WebSocket messages.

        Uses a combination of room_id, client_id, and event_type for granular control.
        """
        # Create unique identifier for WebSocket rate limiting
        identifier = f"ws:{room_id}:{client_id}:{event_type}"
        route = f"ws_{event_type}"

        return await self.check_rate_limit(identifier, rule, route)

    def get_stats(self, route: Optional[str] = None) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        if route:
            stats = self.stats.get(route, RateLimitStats())
            return {
                "route": route,
                "total_requests": stats.total_requests,
                "blocked_requests": stats.blocked_requests,
                "unique_clients": len(stats.unique_clients),
                "block_rate": (
                    (stats.blocked_requests / stats.total_requests * 100)
                    if stats.total_requests > 0
                    else 0
                ),
                "last_reset": stats.last_reset.isoformat(),
            }
        else:
            # Return all stats
            all_stats = {}
            for route, stats in self.stats.items():
                all_stats[route] = {
                    "total_requests": stats.total_requests,
                    "blocked_requests": stats.blocked_requests,
                    "unique_clients": len(stats.unique_clients),
                    "block_rate": (
                        (stats.blocked_requests / stats.total_requests * 100)
                        if stats.total_requests > 0
                        else 0
                    ),
                }
            return all_stats


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
        # Start cleanup task
        asyncio.create_task(_rate_limiter.start())
    return _rate_limiter


# Import configuration
try:
    import sys
    import os

    sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
    from config.rate_limits import get_rate_limit_config

    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# Get default rules from configuration or fallback
if CONFIG_AVAILABLE:
    DEFAULT_RULES = get_rate_limit_config().get_rest_api_rules()
else:
    # Fallback to hardcoded values if config not available
    DEFAULT_RULES = {
        # REST API endpoints
        "/api/health": RateLimitRule(requests=60, window_seconds=60),  # 60 req/min
        "/api/health/detailed": RateLimitRule(
            requests=30, window_seconds=60
        ),  # 30 req/min
        "/api/rooms": RateLimitRule(requests=30, window_seconds=60),  # 30 req/min
        "/api/recovery": RateLimitRule(requests=10, window_seconds=60),  # 10 req/min
        # WebSocket events
        "ws_ping": RateLimitRule(requests=120, window_seconds=60),  # 2 per second
        "ws_declare": RateLimitRule(
            requests=10, window_seconds=60
        ),  # 10 declarations/min
        "ws_play": RateLimitRule(requests=30, window_seconds=60),  # 30 plays/min
        "ws_create_room": RateLimitRule(requests=5, window_seconds=60),  # 5 rooms/min
        "ws_join_room": RateLimitRule(requests=10, window_seconds=60),  # 10 joins/min
        "ws_chat": RateLimitRule(requests=30, window_seconds=60),  # 30 messages/min
        # Global fallback
        "global": RateLimitRule(
            requests=100, window_seconds=60, burst_multiplier=2.0
        ),  # 100 req/min with 2x burst
    }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting HTTP requests.

    Features:
    - Per-route rate limiting
    - IP-based client identification
    - Rate limit headers in responses
    - Configurable rules per endpoint
    """

    def __init__(self, app: ASGIApp, rules: Optional[Dict[str, RateLimitRule]] = None):
        super().__init__(app)
        self.rate_limiter = get_rate_limiter()
        self.rules = rules or DEFAULT_RULES

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for certain paths
        if request.url.path.startswith("/ws/"):
            # WebSocket connections handled separately
            return await call_next(request)

        # Get the appropriate rule
        path = request.url.path
        rule = self.rules.get(path)

        # Try to match path prefix
        if not rule:
            for rule_path, rule_obj in self.rules.items():
                if path.startswith(rule_path):
                    rule = rule_obj
                    break

        # Use global rule if no specific rule found
        if not rule:
            rule = self.rules.get(
                "global", RateLimitRule(requests=100, window_seconds=60)
            )

        # Get client identifier
        identifier = self.rate_limiter._get_client_identifier(request)

        # Check rate limit
        allowed, rate_info = await self.rate_limiter.check_rate_limit(
            identifier, rule, path
        )

        if not allowed:
            # Rate limit exceeded
            if ERROR_CODES_AVAILABLE:
                error = create_standard_error(
                    ErrorCode.NETWORK_RATE_LIMITED,
                    "Rate limit exceeded",
                    context={
                        "retry_after": rate_info.get("retry_after", 60),
                        "limit": rate_info.get("limit"),
                        "window": rate_info.get("window"),
                    },
                )
                response_data = error.to_dict()
            else:
                response_data = {
                    "error": "Rate limit exceeded",
                    "retry_after": rate_info.get("retry_after", 60),
                    "message": rate_info.get(
                        "reason", "Too many requests. Please try again later."
                    ),
                }

            return JSONResponse(
                status_code=429,
                content=response_data,
                headers={
                    "Retry-After": str(rate_info.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(rate_info.get("limit", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info.get("reset", 0)),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        if rate_info:
            response.headers["X-RateLimit-Limit"] = str(rate_info.get("limit", 0))
            response.headers["X-RateLimit-Remaining"] = str(
                rate_info.get("remaining", 0)
            )
            response.headers["X-RateLimit-Reset"] = str(rate_info.get("reset", 0))
            response.headers["X-RateLimit-Window"] = str(rate_info.get("window", 0))

        return response


def create_rate_limiter(
    rules: Optional[Dict[str, RateLimitRule]] = None,
) -> RateLimitMiddleware:
    """
    Factory function to create rate limiting middleware.

    Args:
        rules: Optional dictionary of path patterns to RateLimitRule objects

    Returns:
        RateLimitMiddleware instance
    """
    return lambda app: RateLimitMiddleware(app, rules)
