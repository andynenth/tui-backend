"""
Rate limiting middleware for FastAPI and WebSocket connections.

Provides easy integration of rate limiting into the application.
"""

from typing import Optional, Dict, Any, Callable, List, Union
from datetime import timedelta
import logging
from functools import wraps

from fastapi import Request, Response, HTTPException, WebSocket
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .base import (
    IRateLimiter,
    RateLimitExceeded,
    RateLimitConfig,
    RateLimitScope,
    RateLimitStrategy,
    RateLimitRule,
    CompositeRateLimiter,
)


logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for HTTP rate limiting.

    Features:
    - Multiple rate limiting strategies
    - Configurable key extraction
    - Standard rate limit headers
    - Graceful error handling
    """

    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: IRateLimiter,
        key_extractor: Optional[Callable[[Request], str]] = None,
        exclude_paths: Optional[List[str]] = None,
        cost_extractor: Optional[Callable[[Request], int]] = None,
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            rate_limiter: Rate limiter instance
            key_extractor: Function to extract rate limit key from request
            exclude_paths: Paths to exclude from rate limiting
            cost_extractor: Function to determine request cost
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.key_extractor = key_extractor or self._default_key_extractor
        self.exclude_paths = set(exclude_paths or [])
        self.cost_extractor = cost_extractor or (lambda r: 1)

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        # Check if path is excluded
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Extract key and cost
        try:
            key = self.key_extractor(request)
            cost = self.cost_extractor(request)
        except Exception as e:
            logger.error(f"Error extracting rate limit key: {e}")
            return await call_next(request)

        # Check rate limit
        try:
            result = await self.rate_limiter.check_rate_limit(key, cost)

            if not result.allowed:
                return self._rate_limit_exceeded_response(result)

            # Consume if allowed
            await self.rate_limiter.consume(key, cost)

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            for header, value in result.headers.items():
                response.headers[header] = value

            return response

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request on error
            return await call_next(request)

    def _default_key_extractor(self, request: Request) -> str:
        """Default key extraction - by IP address."""
        # Get IP from X-Forwarded-For or client
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    def _rate_limit_exceeded_response(self, result: Any) -> Response:
        """Create rate limit exceeded response."""
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "retry_after": (
                    result.retry_after.total_seconds() if result.retry_after else None
                ),
            },
            headers=result.headers,
        )


class WebSocketRateLimiter:
    """
    Rate limiter for WebSocket connections.

    Features:
    - Connection-level rate limiting
    - Message-level rate limiting
    - Graceful disconnection on limit
    """

    def __init__(
        self,
        connection_limiter: Optional[IRateLimiter] = None,
        message_limiter: Optional[IRateLimiter] = None,
        key_extractor: Optional[Callable[[WebSocket], str]] = None,
    ):
        """
        Initialize WebSocket rate limiter.

        Args:
            connection_limiter: Limiter for new connections
            message_limiter: Limiter for messages
            key_extractor: Function to extract key from WebSocket
        """
        self.connection_limiter = connection_limiter
        self.message_limiter = message_limiter
        self.key_extractor = key_extractor or self._default_key_extractor

    async def check_connection(self, websocket: WebSocket) -> bool:
        """
        Check if new connection is allowed.

        Returns:
            True if connection allowed, False otherwise
        """
        if not self.connection_limiter:
            return True

        try:
            key = self.key_extractor(websocket)
            result = await self.connection_limiter.check_rate_limit(key)

            if result.allowed:
                await self.connection_limiter.consume(key)

                # Add headers to accept response
                if hasattr(websocket, "headers"):
                    websocket.headers.update(result.headers)

                return True

            # Send close with rate limit info
            await websocket.close(
                code=1008,  # Policy Violation
                reason=f"Rate limit exceeded. Retry after {result.retry_after.total_seconds()}s",
            )
            return False

        except Exception as e:
            logger.error(f"WebSocket connection rate limit error: {e}")
            return True  # Fail open

    async def check_message(self, websocket: WebSocket, message: Any) -> bool:
        """
        Check if message is allowed.

        Returns:
            True if message allowed, False otherwise
        """
        if not self.message_limiter:
            return True

        try:
            key = self.key_extractor(websocket)

            # Calculate message cost based on size/type
            cost = self._calculate_message_cost(message)

            result = await self.message_limiter.check_rate_limit(key, cost)

            if result.allowed:
                await self.message_limiter.consume(key, cost)
                return True

            # Send rate limit notification
            await websocket.send_json(
                {
                    "type": "rate_limit",
                    "error": "Message rate limit exceeded",
                    "retry_after": (
                        result.retry_after.total_seconds()
                        if result.retry_after
                        else None
                    ),
                }
            )

            return False

        except Exception as e:
            logger.error(f"WebSocket message rate limit error: {e}")
            return True  # Fail open

    def _default_key_extractor(self, websocket: WebSocket) -> str:
        """Default key extraction from WebSocket."""
        # Try to get user ID from WebSocket state
        if hasattr(websocket, "state") and hasattr(websocket.state, "user_id"):
            return f"ws_user:{websocket.state.user_id}"

        # Fall back to client IP
        if websocket.client:
            return f"ws_ip:{websocket.client.host}"

        return "ws_unknown"

    def _calculate_message_cost(self, message: Any) -> int:
        """Calculate cost based on message size/complexity."""
        if isinstance(message, dict):
            # Base cost + extra for large messages
            base_cost = 1

            # Add cost for message size
            message_str = str(message)
            size_cost = len(message_str) // 1000  # 1 per KB

            return base_cost + size_cost

        return 1


def rate_limit(limiter: IRateLimiter, key_extractor: Callable[..., str], cost: int = 1):
    """
    Decorator for rate limiting individual endpoints.

    Usage:
        @app.get("/api/expensive")
        @rate_limit(limiter, lambda request: f"user:{request.user.id}", cost=10)
        async def expensive_operation(request: Request):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                request = kwargs.get("request")

            if not request:
                # No request found, skip rate limiting
                return await func(*args, **kwargs)

            # Apply rate limiting
            key = key_extractor(request)
            result = await limiter.check_rate_limit(key, cost)

            if not result.allowed:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers=result.headers,
                )

            await limiter.consume(key, cost)

            # Add headers to response
            response = await func(*args, **kwargs)
            if isinstance(response, Response):
                response.headers.update(result.headers)

            return response

        return wrapper

    return decorator


class RateLimitingStrategy:
    """
    Advanced rate limiting strategy with multiple rules.

    Allows different limits for different user types, endpoints, etc.
    """

    def __init__(self):
        self.rules: List[RateLimitRule] = []
        self.limiters: Dict[str, IRateLimiter] = {}

    def add_rule(
        self,
        name: str,
        limiter: IRateLimiter,
        condition: Callable[[Request], bool],
        priority: int = 0,
    ) -> None:
        """Add a rate limiting rule."""
        rule = RateLimitRule(
            name=name,
            config=None,  # Config in limiter
            condition=condition,
            priority=priority,
        )
        self.rules.append(rule)
        self.limiters[name] = limiter

        # Sort by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    async def get_limiter(self, request: Request) -> Optional[IRateLimiter]:
        """Get appropriate limiter for request."""
        context = self._build_context(request)

        for rule in self.rules:
            if await rule.matches(context):
                return self.limiters.get(rule.name)

        return None

    def _build_context(self, request: Request) -> Dict[str, Any]:
        """Build context from request."""
        context = {
            "path": request.url.path,
            "method": request.method,
            "headers": dict(request.headers),
            "client": request.client,
        }

        # Add user info if available
        if hasattr(request, "user"):
            context["user"] = request.user

        return context


# Pre-built strategies


def create_tiered_rate_limiting(
    basic_config: RateLimitConfig,
    premium_config: RateLimitConfig,
    enterprise_config: RateLimitConfig,
) -> RateLimitingStrategy:
    """
    Create tiered rate limiting strategy.

    Different limits for different user tiers.
    """
    from .token_bucket import TokenBucketRateLimiter

    strategy = RateLimitingStrategy()

    # Basic users
    basic_limiter = TokenBucketRateLimiter(basic_config)
    strategy.add_rule(
        "basic",
        basic_limiter,
        lambda req: getattr(req.user, "tier", "basic") == "basic",
        priority=1,
    )

    # Premium users
    premium_limiter = TokenBucketRateLimiter(premium_config)
    strategy.add_rule(
        "premium",
        premium_limiter,
        lambda req: getattr(req.user, "tier", "basic") == "premium",
        priority=2,
    )

    # Enterprise users
    enterprise_limiter = TokenBucketRateLimiter(enterprise_config)
    strategy.add_rule(
        "enterprise",
        enterprise_limiter,
        lambda req: getattr(req.user, "tier", "basic") == "enterprise",
        priority=3,
    )

    return strategy


def create_endpoint_rate_limiting(
    default_limiter: IRateLimiter, endpoint_configs: Dict[str, IRateLimiter]
) -> RateLimitingStrategy:
    """
    Create endpoint-specific rate limiting.

    Different limits for different API endpoints.
    """
    strategy = RateLimitingStrategy()

    # Add endpoint-specific rules
    for endpoint, limiter in endpoint_configs.items():
        strategy.add_rule(
            f"endpoint_{endpoint}",
            limiter,
            lambda req, ep=endpoint: req.url.path.startswith(ep),
            priority=10,
        )

    # Default rule
    strategy.add_rule("default", default_limiter, lambda req: True, priority=0)

    return strategy
