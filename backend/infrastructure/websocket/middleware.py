"""
WebSocket middleware for infrastructure integration.

Provides middleware components that integrate various infrastructure
features with WebSocket connections.
"""

from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
import json
import logging
from dataclasses import dataclass
from contextlib import asynccontextmanager

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from backend.infrastructure.observability import (
    get_logger,
    get_metrics_collector,
    get_tracer,
    CorrelationContext,
    Counter,
    Timer,
    SpanKind
)
from backend.infrastructure.rate_limiting import (
    GameWebSocketRateLimiter,
    create_game_rate_limiter
)
from .connection_manager import ConnectionManager, ConnectionInfo, ConnectionState


logger = logging.getLogger(__name__)


class WebSocketMiddleware(ABC):
    """Base class for WebSocket middleware."""
    
    @abstractmethod
    async def process_connect(
        self,
        websocket: WebSocket,
        connection_info: ConnectionInfo
    ) -> Optional[ConnectionInfo]:
        """
        Process connection establishment.
        
        Returns None to reject connection.
        """
        pass
    
    @abstractmethod
    async def process_message(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process incoming message.
        
        Returns None to block message.
        """
        pass
    
    @abstractmethod
    async def process_send(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process outgoing message.
        
        Returns None to block message.
        """
        pass
    
    @abstractmethod
    async def process_disconnect(
        self,
        connection_info: ConnectionInfo,
        code: int,
        reason: str
    ) -> None:
        """Process disconnection."""
        pass


@dataclass
class MiddlewareContext:
    """Context passed through middleware chain."""
    websocket: WebSocket
    connection_info: ConnectionInfo
    metadata: Dict[str, Any]


class WebSocketInfrastructureMiddleware:
    """
    Composite middleware that integrates all infrastructure features.
    
    Features:
    - Middleware chaining
    - Error handling
    - Context propagation
    """
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        middlewares: Optional[List[WebSocketMiddleware]] = None
    ):
        """
        Initialize infrastructure middleware.
        
        Args:
            connection_manager: Connection manager
            middlewares: List of middleware to apply
        """
        self.connection_manager = connection_manager
        self.middlewares = middlewares or []
    
    def add_middleware(self, middleware: WebSocketMiddleware) -> None:
        """Add middleware to chain."""
        self.middlewares.append(middleware)
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        connection_id: str
    ) -> Optional[ConnectionInfo]:
        """
        Handle new WebSocket connection through middleware.
        
        Returns None if connection rejected.
        """
        # Create initial connection info
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            websocket=websocket,
            state=ConnectionState.CONNECTING
        )
        
        # Process through middleware
        for middleware in self.middlewares:
            try:
                connection_info = await middleware.process_connect(
                    websocket,
                    connection_info
                )
                if connection_info is None:
                    return None
            except Exception as e:
                logger.error(f"Middleware error on connect: {e}")
                return None
        
        # Accept and register connection
        await self.connection_manager.connect(websocket, connection_id)
        
        return connection_info
    
    async def handle_message(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handle incoming message through middleware.
        
        Returns None if message blocked.
        """
        # Process through middleware
        for middleware in self.middlewares:
            try:
                message = await middleware.process_message(
                    connection_info,
                    message
                )
                if message is None:
                    return None
            except Exception as e:
                logger.error(f"Middleware error on message: {e}")
                return None
        
        return message
    
    async def handle_send(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> bool:
        """
        Handle outgoing message through middleware.
        
        Returns False if message blocked.
        """
        # Process through middleware
        for middleware in self.middlewares:
            try:
                message = await middleware.process_send(
                    connection_info,
                    message
                )
                if message is None:
                    return False
            except Exception as e:
                logger.error(f"Middleware error on send: {e}")
                return False
        
        # Send message
        return await self.connection_manager.send_to_connection(
            connection_info.connection_id,
            message
        )
    
    async def handle_disconnect(
        self,
        connection_info: ConnectionInfo,
        code: int = 1000,
        reason: str = "Normal closure"
    ) -> None:
        """Handle disconnection through middleware."""
        # Process through middleware in reverse order
        for middleware in reversed(self.middlewares):
            try:
                await middleware.process_disconnect(
                    connection_info,
                    code,
                    reason
                )
            except Exception as e:
                logger.error(f"Middleware error on disconnect: {e}")
        
        # Disconnect
        await self.connection_manager.disconnect(
            connection_info.connection_id,
            code,
            reason
        )


class ConnectionTrackingMiddleware(WebSocketMiddleware):
    """
    Middleware for tracking connection lifecycle.
    
    Features:
    - Connection state tracking
    - Activity monitoring
    - Connection metadata
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        """Initialize tracking middleware."""
        self.connection_manager = connection_manager
    
    async def process_connect(
        self,
        websocket: WebSocket,
        connection_info: ConnectionInfo
    ) -> Optional[ConnectionInfo]:
        """Track connection establishment."""
        # Add connection metadata
        connection_info.metadata.update({
            'user_agent': websocket.headers.get('user-agent', 'unknown'),
            'origin': websocket.headers.get('origin', 'unknown'),
            'client_ip': websocket.client.host if websocket.client else 'unknown'
        })
        
        logger.info(
            f"WebSocket connection from {connection_info.metadata['client_ip']}"
        )
        
        return connection_info
    
    async def process_message(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Track message activity."""
        # Update activity timestamp
        connection_info.update_activity()
        
        # Track message type
        message_type = message.get('type', 'unknown')
        if 'message_counts' not in connection_info.metadata:
            connection_info.metadata['message_counts'] = {}
        
        connection_info.metadata['message_counts'][message_type] = \
            connection_info.metadata['message_counts'].get(message_type, 0) + 1
        
        return message
    
    async def process_send(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Track outgoing messages."""
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.utcnow().isoformat()
        
        return message
    
    async def process_disconnect(
        self,
        connection_info: ConnectionInfo,
        code: int,
        reason: str
    ) -> None:
        """Track disconnection."""
        duration = (
            datetime.utcnow() - connection_info.connected_at
        ).total_seconds()
        
        logger.info(
            f"WebSocket disconnected after {duration:.1f}s: "
            f"code={code}, reason={reason}"
        )


class RateLimitingMiddleware(WebSocketMiddleware):
    """
    Middleware for rate limiting WebSocket connections.
    
    Features:
    - Per-connection rate limiting
    - Per-player rate limiting
    - Per-room rate limiting
    - Action-based costs
    """
    
    def __init__(
        self,
        rate_limiter: Optional[GameWebSocketRateLimiter] = None
    ):
        """Initialize rate limiting middleware."""
        self.rate_limiter = rate_limiter or create_game_rate_limiter()
    
    async def process_connect(
        self,
        websocket: WebSocket,
        connection_info: ConnectionInfo
    ) -> Optional[ConnectionInfo]:
        """Check connection rate limit."""
        # Check if connection allowed
        allowed = await self.rate_limiter.on_connect(
            connection_info.player_id or "anonymous",
            connection_info.connection_id
        )
        
        if not allowed:
            await websocket.close(
                code=1008,  # Policy violation
                reason="Rate limit exceeded"
            )
            return None
        
        return connection_info
    
    async def process_message(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check message rate limit."""
        # Get action type
        action_type = message.get('type', 'unknown')
        
        # Check rate limit
        allowed = await self.rate_limiter.consume_action(
            connection_info.player_id or "anonymous",
            connection_info.room_id,
            action_type,
            message
        )
        
        if not allowed:
            # Send rate limit error
            error_message = {
                "type": "error",
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please slow down.",
                "retry_after": 1.0
            }
            
            await connection_info.websocket.send_json(error_message)
            return None
        
        return message
    
    async def process_send(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """No rate limiting on outgoing messages."""
        return message
    
    async def process_disconnect(
        self,
        connection_info: ConnectionInfo,
        code: int,
        reason: str
    ) -> None:
        """Clean up rate limiter state."""
        await self.rate_limiter.on_disconnect(connection_info.connection_id)


class ObservabilityMiddleware(WebSocketMiddleware):
    """
    Middleware for observability integration.
    
    Features:
    - Structured logging
    - Metrics collection
    - Distributed tracing
    - Correlation ID tracking
    """
    
    def __init__(self):
        """Initialize observability middleware."""
        self.logger = get_logger(__name__)
        self.metrics = get_metrics_collector()
        self.tracer = get_tracer()
        
        # Metrics
        self.connection_counter = Counter(self.metrics, "websocket.connections")
        self.message_counter = Counter(self.metrics, "websocket.messages")
        self.error_counter = Counter(self.metrics, "websocket.errors")
        self.message_timer = Timer(self.metrics, "websocket.message_duration")
    
    async def process_connect(
        self,
        websocket: WebSocket,
        connection_info: ConnectionInfo
    ) -> Optional[ConnectionInfo]:
        """Add observability context."""
        # Generate correlation ID
        correlation_id = CorrelationContext.generate_correlation_id()
        connection_info.metadata['correlation_id'] = correlation_id
        
        # Start trace span
        span = self.tracer.start_span(
            "websocket.connect",
            kind=SpanKind.SERVER,
            attributes={
                "connection.id": connection_info.connection_id,
                "client.ip": connection_info.metadata.get('client_ip', 'unknown')
            }
        )
        connection_info.metadata['trace_span'] = span
        
        # Log connection
        with CorrelationContext.with_correlation_id(correlation_id):
            self.logger.info(
                "WebSocket connection established",
                connection_id=connection_info.connection_id
            )
        
        # Update metrics
        self.connection_counter.increment()
        
        return connection_info
    
    async def process_message(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Add message observability."""
        correlation_id = connection_info.metadata.get('correlation_id')
        message_type = message.get('type', 'unknown')
        
        # Create message span
        with self.tracer.span(
            f"websocket.message.{message_type}",
            attributes={
                "connection.id": connection_info.connection_id,
                "message.type": message_type
            }
        ) as span:
            # Set correlation context
            with CorrelationContext.with_correlation_id(correlation_id):
                # Log message
                self.logger.debug(
                    f"WebSocket message received: {message_type}",
                    connection_id=connection_info.connection_id
                )
                
                # Update metrics
                self.message_counter.with_tags(
                    message_type=message_type,
                    direction="inbound"
                ).increment()
                
                # Time message processing
                with self.message_timer.time():
                    return message
    
    async def process_send(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Track outgoing messages."""
        message_type = message.get('type', 'unknown')
        
        # Update metrics
        self.message_counter.with_tags(
            message_type=message_type,
            direction="outbound"
        ).increment()
        
        return message
    
    async def process_disconnect(
        self,
        connection_info: ConnectionInfo,
        code: int,
        reason: str
    ) -> None:
        """Clean up observability context."""
        correlation_id = connection_info.metadata.get('correlation_id')
        
        # End trace span
        span = connection_info.metadata.get('trace_span')
        if span:
            span.set_attribute("disconnect.code", code)
            span.set_attribute("disconnect.reason", reason)
            span.end()
        
        # Log disconnection
        with CorrelationContext.with_correlation_id(correlation_id):
            self.logger.info(
                "WebSocket connection closed",
                connection_id=connection_info.connection_id,
                code=code,
                reason=reason
            )
        
        # Update metrics
        self.connection_counter.decrement()


class ErrorHandlingMiddleware(WebSocketMiddleware):
    """
    Middleware for error handling and recovery.
    
    Features:
    - Exception catching
    - Error response formatting
    - Circuit breaking
    - Graceful degradation
    """
    
    def __init__(
        self,
        max_errors: int = 10,
        error_window_seconds: int = 60
    ):
        """
        Initialize error handling middleware.
        
        Args:
            max_errors: Maximum errors before circuit break
            error_window_seconds: Time window for error counting
        """
        self.max_errors = max_errors
        self.error_window_seconds = error_window_seconds
        self._error_counts: Dict[str, List[datetime]] = {}
        self._circuit_broken: Set[str] = set()
        self.logger = get_logger(__name__)
    
    async def process_connect(
        self,
        websocket: WebSocket,
        connection_info: ConnectionInfo
    ) -> Optional[ConnectionInfo]:
        """Check circuit breaker on connect."""
        if connection_info.connection_id in self._circuit_broken:
            await websocket.close(
                code=1011,  # Server error
                reason="Service temporarily unavailable"
            )
            return None
        
        return connection_info
    
    async def process_message(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Handle message processing errors."""
        try:
            # Validate message format
            if not isinstance(message, dict):
                raise ValueError("Message must be a dictionary")
            
            if 'type' not in message:
                raise ValueError("Message must have a 'type' field")
            
            return message
            
        except Exception as e:
            # Record error
            self._record_error(connection_info.connection_id)
            
            # Log error
            self.logger.error(
                f"Error processing message: {e}",
                connection_id=connection_info.connection_id,
                exc_info=True
            )
            
            # Send error response
            error_response = {
                "type": "error",
                "error": "invalid_message",
                "message": str(e),
                "request_id": message.get('id')
            }
            
            await connection_info.websocket.send_json(error_response)
            
            # Check circuit breaker
            if self._should_break_circuit(connection_info.connection_id):
                self._circuit_broken.add(connection_info.connection_id)
                await connection_info.websocket.close(
                    code=1011,
                    reason="Too many errors"
                )
            
            return None
    
    async def process_send(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Ensure safe message sending."""
        try:
            # Ensure message is JSON serializable
            json.dumps(message)
            return message
            
        except Exception as e:
            self.logger.error(
                f"Error serializing message: {e}",
                connection_id=connection_info.connection_id
            )
            
            # Send error notification instead
            return {
                "type": "error",
                "error": "serialization_error",
                "message": "Failed to send message"
            }
    
    async def process_disconnect(
        self,
        connection_info: ConnectionInfo,
        code: int,
        reason: str
    ) -> None:
        """Clean up error tracking."""
        self._error_counts.pop(connection_info.connection_id, None)
        self._circuit_broken.discard(connection_info.connection_id)
    
    def _record_error(self, connection_id: str) -> None:
        """Record an error for a connection."""
        now = datetime.utcnow()
        
        if connection_id not in self._error_counts:
            self._error_counts[connection_id] = []
        
        # Add error timestamp
        self._error_counts[connection_id].append(now)
        
        # Clean old errors
        cutoff = now.timestamp() - self.error_window_seconds
        self._error_counts[connection_id] = [
            ts for ts in self._error_counts[connection_id]
            if ts.timestamp() > cutoff
        ]
    
    def _should_break_circuit(self, connection_id: str) -> bool:
        """Check if circuit should be broken."""
        error_count = len(self._error_counts.get(connection_id, []))
        return error_count >= self.max_errors


class AuthenticationMiddleware(WebSocketMiddleware):
    """
    Middleware for WebSocket authentication.
    
    Features:
    - Token validation
    - Player association
    - Permission checking
    """
    
    def __init__(
        self,
        auth_validator: Optional[Callable] = None
    ):
        """
        Initialize authentication middleware.
        
        Args:
            auth_validator: Function to validate auth tokens
        """
        self.auth_validator = auth_validator
        self.logger = get_logger(__name__)
    
    async def process_connect(
        self,
        websocket: WebSocket,
        connection_info: ConnectionInfo
    ) -> Optional[ConnectionInfo]:
        """Validate initial connection."""
        # Get auth token from query params or headers
        token = websocket.query_params.get('token') or \
                websocket.headers.get('authorization', '').replace('Bearer ', '')
        
        if not token:
            # Allow anonymous connections but mark as unauthenticated
            connection_info.metadata['authenticated'] = False
            return connection_info
        
        # Validate token
        if self.auth_validator:
            try:
                player_info = await self.auth_validator(token)
                connection_info.player_id = player_info['player_id']
                connection_info.metadata['authenticated'] = True
                connection_info.metadata['player_info'] = player_info
                
                self.logger.info(
                    f"WebSocket authenticated for player {player_info['player_id']}"
                )
                
            except Exception as e:
                self.logger.warning(f"WebSocket auth failed: {e}")
                connection_info.metadata['authenticated'] = False
        
        return connection_info
    
    async def process_message(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check message permissions."""
        message_type = message.get('type', 'unknown')
        
        # Check if message requires authentication
        requires_auth = message_type in [
            'create_room',
            'join_room',
            'start_game',
            'play',
            'declare'
        ]
        
        if requires_auth and not connection_info.metadata.get('authenticated'):
            # Send auth error
            error_response = {
                "type": "error",
                "error": "authentication_required",
                "message": "This action requires authentication",
                "request_id": message.get('id')
            }
            
            await connection_info.websocket.send_json(error_response)
            return None
        
        return message
    
    async def process_send(
        self,
        connection_info: ConnectionInfo,
        message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """No filtering on outgoing messages."""
        return message
    
    async def process_disconnect(
        self,
        connection_info: ConnectionInfo,
        code: int,
        reason: str
    ) -> None:
        """No cleanup needed."""
        pass