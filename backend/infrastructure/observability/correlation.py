"""
Correlation ID tracking for request tracing across services.

Provides middleware and utilities for managing correlation IDs.
"""

from typing import Optional, Dict, Any, Callable
import uuid
import contextvars
from contextlib import contextmanager
from functools import wraps
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging


# Context variable for correlation ID
_correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


class CorrelationContext:
    """
    Manages correlation ID context.

    Features:
    - Thread-safe context management
    - Automatic ID generation
    - Context propagation
    """

    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get the current correlation ID."""
        return _correlation_id_var.get()

    @staticmethod
    def set_correlation_id(correlation_id: Optional[str]) -> None:
        """Set the correlation ID."""
        _correlation_id_var.set(correlation_id)

    @staticmethod
    def generate_correlation_id() -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())

    @staticmethod
    @contextmanager
    def with_correlation_id(correlation_id: Optional[str] = None):
        """
        Context manager for setting correlation ID.

        Args:
            correlation_id: ID to use (generates one if not provided)

        Example:
            with CorrelationContext.with_correlation_id():
                # All operations here will have the same correlation ID
                process_request()
        """
        if correlation_id is None:
            correlation_id = CorrelationContext.generate_correlation_id()

        token = _correlation_id_var.set(correlation_id)
        try:
            yield correlation_id
        finally:
            _correlation_id_var.reset(token)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware for correlation ID management.

    Features:
    - Extracts correlation ID from headers
    - Generates ID if missing
    - Adds ID to response headers
    - Integrates with logging and tracing
    """

    def __init__(
        self,
        app,
        header_name: str = "X-Correlation-ID",
        generate_if_missing: bool = True,
        propagate_to_response: bool = True,
        log_correlation: bool = True,
    ):
        """
        Initialize correlation middleware.

        Args:
            app: ASGI application
            header_name: Header name for correlation ID
            generate_if_missing: Generate ID if not in request
            propagate_to_response: Add ID to response headers
            log_correlation: Add ID to log context
        """
        super().__init__(app)
        self.header_name = header_name
        self.generate_if_missing = generate_if_missing
        self.propagate_to_response = propagate_to_response
        self.log_correlation = log_correlation

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with correlation ID."""
        # Extract or generate correlation ID
        correlation_id = request.headers.get(self.header_name)

        if not correlation_id and self.generate_if_missing:
            correlation_id = CorrelationContext.generate_correlation_id()

        # Set correlation ID in context
        with CorrelationContext.with_correlation_id(correlation_id):
            # Add to request state for easy access
            request.state.correlation_id = correlation_id

            # Add to logging context if configured
            if self.log_correlation:
                self._add_to_log_context(correlation_id)

            # Process request
            response = await call_next(request)

            # Add to response headers if configured
            if self.propagate_to_response and correlation_id:
                response.headers[self.header_name] = correlation_id

            return response

    def _add_to_log_context(self, correlation_id: str) -> None:
        """Add correlation ID to logging context."""
        # This would integrate with the logging system
        # For now, we'll use standard logging
        logger = logging.getLogger(__name__)
        logger = logging.LoggerAdapter(logger, {"correlation_id": correlation_id})


class WebSocketCorrelationMiddleware:
    """
    WebSocket middleware for correlation ID management.

    Features:
    - Extracts correlation ID from connection params
    - Maintains ID throughout connection
    - Integrates with message handling
    """

    def __init__(
        self, param_name: str = "correlation_id", generate_if_missing: bool = True
    ):
        """
        Initialize WebSocket correlation middleware.

        Args:
            param_name: Query parameter name for correlation ID
            generate_if_missing: Generate ID if not provided
        """
        self.param_name = param_name
        self.generate_if_missing = generate_if_missing

    async def __call__(self, websocket, receive, send):
        """Process WebSocket connection with correlation ID."""
        # Extract from query params
        correlation_id = websocket.query_params.get(self.param_name)

        if not correlation_id and self.generate_if_missing:
            correlation_id = CorrelationContext.generate_correlation_id()

        # Store in connection state
        websocket.state.correlation_id = correlation_id

        # Set context for entire connection
        with CorrelationContext.with_correlation_id(correlation_id):
            # Original receive/send
            await websocket.app(websocket, receive, send)


def with_correlation_id(
    correlation_id: Optional[str] = None, generate: bool = True
) -> Callable:
    """
    Decorator for adding correlation ID to function execution.

    Args:
        correlation_id: Specific ID to use
        generate: Generate ID if not provided

    Example:
        @with_correlation_id()
        async def process_message(message):
            # Function will have correlation ID in context
            logger.info("Processing message")
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cid = correlation_id
            if not cid and generate:
                cid = CorrelationContext.generate_correlation_id()

            with CorrelationContext.with_correlation_id(cid):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cid = correlation_id
            if not cid and generate:
                cid = CorrelationContext.generate_correlation_id()

            with CorrelationContext.with_correlation_id(cid):
                return func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def inject_correlation_id(carrier: Dict[str, Any]) -> None:
    """
    Inject correlation ID into a carrier (e.g., headers).

    Args:
        carrier: Dictionary to inject ID into
    """
    correlation_id = CorrelationContext.get_correlation_id()
    if correlation_id:
        carrier["X-Correlation-ID"] = correlation_id
        carrier["correlation_id"] = correlation_id


def extract_correlation_id(
    carrier: Dict[str, Any], header_names: Optional[list] = None
) -> Optional[str]:
    """
    Extract correlation ID from a carrier.

    Args:
        carrier: Dictionary to extract from
        header_names: List of possible header names

    Returns:
        Correlation ID if found
    """
    if header_names is None:
        header_names = [
            "X-Correlation-ID",
            "X-Correlation-Id",
            "x-correlation-id",
            "correlation_id",
            "correlationId",
        ]

    for name in header_names:
        if name in carrier:
            return str(carrier[name])

    return None


# Convenience functions


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return CorrelationContext.get_correlation_id()


def set_correlation_id(correlation_id: Optional[str]) -> None:
    """Set the correlation ID."""
    CorrelationContext.set_correlation_id(correlation_id)


# Integration with logging


class CorrelationLogFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records.

    Example:
        logger = logging.getLogger(__name__)
        logger.addFilter(CorrelationLogFilter())
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        correlation_id = CorrelationContext.get_correlation_id()
        record.correlation_id = correlation_id or "no-correlation-id"
        return True


class CorrelationLogAdapter(logging.LoggerAdapter):
    """
    Logger adapter that includes correlation ID.

    Example:
        base_logger = logging.getLogger(__name__)
        logger = CorrelationLogAdapter(base_logger)
        logger.info("Processing request")  # Will include correlation ID
    """

    def process(self, msg, kwargs):
        """Add correlation ID to log context."""
        correlation_id = CorrelationContext.get_correlation_id()

        extra = kwargs.get("extra", {})
        extra["correlation_id"] = correlation_id
        kwargs["extra"] = extra

        return msg, kwargs


# Integration with metrics


def add_correlation_tag(tags: Dict[str, str]) -> Dict[str, str]:
    """
    Add correlation ID as a metric tag.

    Args:
        tags: Existing tags

    Returns:
        Tags with correlation ID added
    """
    correlation_id = CorrelationContext.get_correlation_id()
    if correlation_id:
        tags["correlation_id"] = correlation_id
    return tags


# Game-specific correlation


class GameCorrelationContext(CorrelationContext):
    """
    Extended correlation context for game operations.

    Adds game-specific context like room_id, player_id.
    """

    # Additional context variables
    _room_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "room_id", default=None
    )
    _player_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
        "player_id", default=None
    )

    @staticmethod
    def set_game_context(
        room_id: Optional[str] = None, player_id: Optional[str] = None
    ) -> None:
        """Set game-specific context."""
        if room_id is not None:
            GameCorrelationContext._room_id_var.set(room_id)
        if player_id is not None:
            GameCorrelationContext._player_id_var.set(player_id)

    @staticmethod
    def get_game_context() -> Dict[str, Optional[str]]:
        """Get all game context."""
        return {
            "correlation_id": CorrelationContext.get_correlation_id(),
            "room_id": GameCorrelationContext._room_id_var.get(),
            "player_id": GameCorrelationContext._player_id_var.get(),
        }

    @staticmethod
    @contextmanager
    def with_game_context(
        correlation_id: Optional[str] = None,
        room_id: Optional[str] = None,
        player_id: Optional[str] = None,
    ):
        """
        Context manager for game-specific correlation.

        Example:
            with GameCorrelationContext.with_game_context(
                room_id="room123",
                player_id="player456"
            ):
                process_game_action()
        """
        with CorrelationContext.with_correlation_id(correlation_id):
            tokens = []

            if room_id is not None:
                tokens.append(GameCorrelationContext._room_id_var.set(room_id))
            if player_id is not None:
                tokens.append(GameCorrelationContext._player_id_var.set(player_id))

            try:
                yield
            finally:
                for token in tokens:
                    token.var.reset(token)
