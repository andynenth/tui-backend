"""
WebSocket Application Layer Contracts

Defines the interfaces for the application layer's WebSocket handling.
These contracts ensure clear boundaries between layers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WebSocketMessage:
    """Standard WebSocket message structure"""

    event: str
    data: Dict[str, Any]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class WebSocketResponse:
    """Standard WebSocket response structure"""

    event: str
    data: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for WebSocket transmission"""
        result = {"event": self.event, "data": self.data}
        if self.error:
            result["error"] = self.error
        return result


class IMessageHandler(ABC):
    """
    Contract for handling WebSocket messages in the application layer.

    This interface defines how the application layer processes incoming
    WebSocket messages and generates responses.
    """

    @abstractmethod
    async def handle_message(
        self, message: WebSocketMessage, context: Dict[str, Any]
    ) -> Optional[WebSocketResponse]:
        """
        Handle an incoming WebSocket message.

        Args:
            message: The incoming WebSocket message
            context: Additional context (room_id, player_id, etc.)

        Returns:
            Response to send back, or None if no response needed
        """
        pass

    @abstractmethod
    def can_handle(self, event: str) -> bool:
        """
        Check if this handler can process the given event.

        Args:
            event: The event name

        Returns:
            True if this handler can process the event
        """
        pass

    @abstractmethod
    def get_supported_events(self) -> List[str]:
        """
        Get list of events this handler supports.

        Returns:
            List of supported event names
        """
        pass


class IMessageRouter(ABC):
    """
    Contract for routing WebSocket messages to appropriate handlers.

    This interface defines how messages are routed within the
    application layer.
    """

    @abstractmethod
    async def route(
        self, message: WebSocketMessage, context: Dict[str, Any]
    ) -> Optional[WebSocketResponse]:
        """
        Route a message to the appropriate handler.

        Args:
            message: The incoming WebSocket message
            context: Additional context

        Returns:
            Response from handler, or error response if no handler found
        """
        pass

    @abstractmethod
    def register_handler(self, handler: IMessageHandler) -> None:
        """
        Register a message handler.

        Args:
            handler: The handler to register
        """
        pass

    @abstractmethod
    def get_handler_for_event(self, event: str) -> Optional[IMessageHandler]:
        """
        Get the handler for a specific event.

        Args:
            event: The event name

        Returns:
            Handler if found, None otherwise
        """
        pass


class IConnectionContext(ABC):
    """
    Contract for managing connection context.

    This interface defines how connection-specific information
    is tracked and accessed.
    """

    @abstractmethod
    def get_player_id(self) -> Optional[str]:
        """Get the player ID for this connection."""
        pass

    @abstractmethod
    def get_room_id(self) -> Optional[str]:
        """Get the room ID for this connection."""
        pass

    @abstractmethod
    def get_connection_id(self) -> str:
        """Get the unique connection ID."""
        pass

    @abstractmethod
    def set_player_info(self, player_id: str, player_name: str) -> None:
        """Set player information for this connection."""
        pass

    @abstractmethod
    def set_room_id(self, room_id: str) -> None:
        """Set the room ID for this connection."""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        pass


class IEventPublisher(ABC):
    """
    Contract for publishing events within the application layer.

    This interface defines how the application layer publishes
    events that may need to be broadcast to other connections.
    """

    @abstractmethod
    async def publish_event(
        self,
        event_name: str,
        data: Dict[str, Any],
        room_id: Optional[str] = None,
        player_ids: Optional[List[str]] = None,
    ) -> None:
        """
        Publish an event.

        Args:
            event_name: Name of the event
            data: Event data
            room_id: Target room (broadcasts to all in room)
            player_ids: Specific players to target
        """
        pass

    @abstractmethod
    async def publish_to_room(
        self,
        room_id: str,
        event_name: str,
        data: Dict[str, Any],
        exclude_player_ids: Optional[List[str]] = None,
    ) -> None:
        """
        Publish an event to all players in a room.

        Args:
            room_id: The room ID
            event_name: Name of the event
            data: Event data
            exclude_player_ids: Players to exclude from broadcast
        """
        pass

    @abstractmethod
    async def publish_to_player(
        self, player_id: str, event_name: str, data: Dict[str, Any]
    ) -> None:
        """
        Publish an event to a specific player.

        Args:
            player_id: The player ID
            event_name: Name of the event
            data: Event data
        """
        pass


class IMessageValidator(ABC):
    """
    Contract for validating WebSocket messages.

    This interface defines how messages are validated before
    processing in the application layer.
    """

    @abstractmethod
    def validate_message(
        self, message: Dict[str, Any]
    ) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Validate a WebSocket message.

        Args:
            message: The raw message to validate

        Returns:
            Tuple of (is_valid, error_message, sanitized_data)
        """
        pass

    @abstractmethod
    def validate_event(self, event: str) -> bool:
        """
        Check if an event name is valid.

        Args:
            event: The event name

        Returns:
            True if event is valid
        """
        pass

    @abstractmethod
    def should_bypass_validation(self, event: str) -> bool:
        """
        Check if validation should be bypassed for an event.

        Args:
            event: The event name

        Returns:
            True if validation should be bypassed
        """
        pass
