"""
Metrics Integration for WebSocket

Provides decorators and utilities to integrate metrics collection
into the WebSocket message handling flow.
"""

import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union
import asyncio
import logging

from infrastructure.monitoring.websocket_metrics import metrics_collector

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def track_event(event_name: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator to track WebSocket event metrics.

    Args:
        event_name: Override event name (if not provided, uses function name)

    Example:
        @track_event("create_room")
        async def handle_create_room(data: dict) -> dict:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Determine event name
            name = event_name or func.__name__

            # Start timing
            start_time = await metrics_collector.record_event_start(name)

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Record success
                await metrics_collector.record_event_end(name, start_time, success=True)

                return result

            except Exception as e:
                # Record failure
                error_type = type(e).__name__
                await metrics_collector.record_event_end(
                    name, start_time, success=False, error_type=error_type
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async metrics
            # Log a warning and execute without metrics
            logger.warning(f"Sync function {func.__name__} called with @track_event")
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class MetricsContext:
    """Context manager for tracking metrics within a scope"""

    def __init__(self, event_name: str):
        self.event_name = event_name
        self.start_time: Optional[float] = None
        self.success = True
        self.error_type: Optional[str] = None

    async def __aenter__(self):
        """Enter the context and start timing"""
        self.start_time = await metrics_collector.record_event_start(self.event_name)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and record metrics"""
        if exc_type is not None:
            self.success = False
            self.error_type = exc_type.__name__

        await metrics_collector.record_event_end(
            self.event_name, self.start_time, self.success, self.error_type
        )

        # Don't suppress exceptions
        return False

    def mark_error(self, error_type: str):
        """Manually mark the operation as failed"""
        self.success = False
        self.error_type = error_type


async def track_message_flow(
    event_type: str, message: Dict[str, Any], handler: Callable, **handler_kwargs
) -> Optional[Dict[str, Any]]:
    """
    Track the complete flow of a WebSocket message.

    Args:
        event_type: The event type being handled
        message: The incoming message
        handler: The handler function
        **handler_kwargs: Additional arguments for the handler

    Returns:
        The handler's response
    """
    # Record message received
    await metrics_collector.record_message_received(event_type, message)

    # Track event execution
    async with MetricsContext(event_type) as ctx:
        try:
            response = await handler(**handler_kwargs)

            # Record message sent if there's a response
            if response:
                await metrics_collector.record_message_sent(
                    response.get("event", event_type), response
                )

            return response

        except Exception as e:
            logger.error(f"Error handling {event_type}: {e}")
            raise


class WebSocketMetricsMiddleware:
    """
    Middleware for automatic metrics collection in WebSocket handling.

    This can be integrated into the message router or WebSocket endpoint.
    """

    def __init__(self, next_handler: Callable):
        self.next_handler = next_handler

    async def __call__(
        self, message: Dict[str, Any], context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Process message with metrics tracking"""
        event_type = message.get("event", "unknown")

        # Record message received
        await metrics_collector.record_message_received(event_type, message)

        # Track event execution
        start_time = await metrics_collector.record_event_start(event_type)

        try:
            # Call next handler
            response = await self.next_handler(message, context)

            # Record success
            await metrics_collector.record_event_end(
                event_type, start_time, success=True
            )

            # Record message sent if there's a response
            if response:
                await metrics_collector.record_message_sent(
                    response.get("event", event_type), response
                )

            return response

        except Exception as e:
            # Record failure
            await metrics_collector.record_event_end(
                event_type, start_time, success=False, error_type=type(e).__name__
            )
            raise


def create_metrics_wrapped_handler(handler: Callable) -> Callable:
    """
    Wrap a message handler with metrics collection.

    Args:
        handler: The original handler function

    Returns:
        A wrapped handler that collects metrics
    """

    @functools.wraps(handler)
    async def wrapped_handler(message: Dict[str, Any], context: Dict[str, Any]):
        middleware = WebSocketMetricsMiddleware(handler)
        return await middleware(message, context)

    return wrapped_handler


# Connection tracking utilities


async def track_connection(connection_id: str, room_id: str):
    """Track a new WebSocket connection"""
    await metrics_collector.record_connection(connection_id, room_id)


async def track_disconnection(
    connection_id: str, room_id: str, connection_start: float
):
    """Track a WebSocket disconnection"""
    await metrics_collector.record_disconnection(
        connection_id, room_id, connection_start
    )


async def track_broadcast(room_id: str, event_type: str, recipient_count: int):
    """Track a broadcast message"""
    await metrics_collector.record_broadcast(room_id, event_type, recipient_count)


# Export commonly used items
__all__ = [
    "track_event",
    "MetricsContext",
    "track_message_flow",
    "WebSocketMetricsMiddleware",
    "create_metrics_wrapped_handler",
    "track_connection",
    "track_disconnection",
    "track_broadcast",
    "metrics_collector",
]
