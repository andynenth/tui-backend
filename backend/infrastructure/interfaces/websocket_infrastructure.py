"""
WebSocket Infrastructure Layer Contracts

Defines the interfaces for the infrastructure layer's WebSocket handling.
These contracts ensure the application layer can work with WebSocket
infrastructure without depending on implementation details.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
import asyncio


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""

    connection_id: str
    room_id: str
    connected_at: float
    last_activity: float
    is_active: bool = True


class IWebSocketConnection(ABC):
    """
    Contract for a WebSocket connection.

    This abstracts the actual WebSocket implementation
    (e.g., FastAPI WebSocket, websockets library, etc.)
    """

    @abstractmethod
    async def send_json(self, data: Dict[str, Any]) -> None:
        """
        Send JSON data through the WebSocket.

        Args:
            data: The data to send
        """
        pass

    @abstractmethod
    async def receive_json(self) -> Dict[str, Any]:
        """
        Receive JSON data from the WebSocket.

        Returns:
            The received data
        """
        pass

    @abstractmethod
    async def accept(self) -> None:
        """Accept the WebSocket connection."""
        pass

    @abstractmethod
    async def close(self, code: int = 1000, reason: str = "") -> None:
        """
        Close the WebSocket connection.

        Args:
            code: Close code
            reason: Close reason
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the WebSocket is still connected.

        Returns:
            True if connected
        """
        pass


class IConnectionManager(ABC):
    """
    Contract for managing WebSocket connections.

    This interface defines how connections are tracked and managed
    at the infrastructure level.
    """

    @abstractmethod
    async def register_connection(
        self, connection_id: str, websocket: IWebSocketConnection, room_id: str
    ) -> None:
        """
        Register a new WebSocket connection.

        Args:
            connection_id: Unique connection identifier
            websocket: The WebSocket connection
            room_id: The room this connection belongs to
        """
        pass

    @abstractmethod
    async def unregister_connection(self, connection_id: str) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            connection_id: The connection to unregister
        """
        pass

    @abstractmethod
    def get_connection(self, connection_id: str) -> Optional[IWebSocketConnection]:
        """
        Get a WebSocket connection by ID.

        Args:
            connection_id: The connection ID

        Returns:
            The WebSocket connection if found
        """
        pass

    @abstractmethod
    def get_connections_in_room(self, room_id: str) -> Dict[str, IWebSocketConnection]:
        """
        Get all connections in a room.

        Args:
            room_id: The room ID

        Returns:
            Dictionary of connection_id -> WebSocket
        """
        pass

    @abstractmethod
    def get_connection_info(self, connection_id: str) -> Optional[ConnectionInfo]:
        """
        Get information about a connection.

        Args:
            connection_id: The connection ID

        Returns:
            Connection information if found
        """
        pass


class IBroadcaster(ABC):
    """
    Contract for broadcasting messages to multiple connections.

    This interface defines how messages are broadcast to multiple
    WebSocket connections.
    """

    @abstractmethod
    async def broadcast_to_room(
        self,
        room_id: str,
        message: Dict[str, Any],
        exclude_connections: Optional[set[str]] = None,
    ) -> int:
        """
        Broadcast a message to all connections in a room.

        Args:
            room_id: The room to broadcast to
            message: The message to broadcast
            exclude_connections: Connection IDs to exclude

        Returns:
            Number of connections that received the message
        """
        pass

    @abstractmethod
    async def send_to_connection(
        self, connection_id: str, message: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific connection.

        Args:
            connection_id: The target connection
            message: The message to send

        Returns:
            True if message was sent successfully
        """
        pass

    @abstractmethod
    async def broadcast_to_connections(
        self, connection_ids: set[str], message: Dict[str, Any]
    ) -> int:
        """
        Broadcast a message to specific connections.

        Args:
            connection_ids: The target connections
            message: The message to broadcast

        Returns:
            Number of connections that received the message
        """
        pass


class IWebSocketInfrastructure(ABC):
    """
    Main contract for WebSocket infrastructure.

    This is the primary interface that the application layer
    uses to interact with WebSocket infrastructure.
    """

    @abstractmethod
    async def handle_connection(
        self,
        websocket: Any,  # Raw WebSocket from framework
        room_id: str,
        message_handler: Callable[
            [Dict[str, Any], str], Awaitable[Optional[Dict[str, Any]]]
        ],
    ) -> None:
        """
        Handle a WebSocket connection lifecycle.

        Args:
            websocket: The raw WebSocket connection
            room_id: The room ID for this connection
            message_handler: Callback to handle messages
        """
        pass

    @abstractmethod
    def get_connection_manager(self) -> IConnectionManager:
        """Get the connection manager."""
        pass

    @abstractmethod
    def get_broadcaster(self) -> IBroadcaster:
        """Get the broadcaster."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the infrastructure gracefully."""
        pass


class IMessageQueue(ABC):
    """
    Contract for message queuing.

    This interface defines how messages are queued for
    disconnected players.
    """

    @abstractmethod
    async def queue_message(self, player_id: str, message: Dict[str, Any]) -> None:
        """
        Queue a message for a player.

        Args:
            player_id: The player to queue for
            message: The message to queue
        """
        pass

    @abstractmethod
    async def get_queued_messages(self, player_id: str) -> list[Dict[str, Any]]:
        """
        Get and clear queued messages for a player.

        Args:
            player_id: The player ID

        Returns:
            List of queued messages
        """
        pass

    @abstractmethod
    async def clear_queue(self, player_id: str) -> None:
        """
        Clear all queued messages for a player.

        Args:
            player_id: The player ID
        """
        pass


class IRateLimiter(ABC):
    """
    Contract for rate limiting WebSocket connections.

    This interface defines how rate limiting is applied to
    prevent abuse.
    """

    @abstractmethod
    async def check_rate_limit(
        self, connection_id: str, event: str
    ) -> tuple[bool, Optional[float]]:
        """
        Check if a connection has exceeded rate limits.

        Args:
            connection_id: The connection to check
            event: The event being sent

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        pass

    @abstractmethod
    async def record_event(self, connection_id: str, event: str) -> None:
        """
        Record an event for rate limiting.

        Args:
            connection_id: The connection ID
            event: The event name
        """
        pass

    @abstractmethod
    def get_limits_for_event(self, event: str) -> Dict[str, Any]:
        """
        Get rate limit configuration for an event.

        Args:
            event: The event name

        Returns:
            Rate limit configuration
        """
        pass
