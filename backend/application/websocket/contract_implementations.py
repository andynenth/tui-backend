"""
Contract Implementations for Application Layer WebSocket Handling

Implements the application layer contracts using existing components.
"""

from typing import Dict, Any, Optional, List
import logging

from application.interfaces.websocket_contracts import (
    IMessageHandler,
    IMessageRouter,
    IConnectionContext,
    IEventPublisher,
    IMessageValidator,
    WebSocketMessage,
    WebSocketResponse,
)
from application.websocket.use_case_dispatcher import UseCaseDispatcher, DispatchContext
from application.websocket.message_router import MessageRouter
from application.websocket.websocket_config import websocket_config
from api.validation.websocket_validators import validate_websocket_message
from infrastructure.websocket.connection_singleton import broadcast

logger = logging.getLogger(__name__)


class UseCaseMessageHandler(IMessageHandler):
    """Message handler that delegates to use case dispatcher"""

    def __init__(self):
        self.dispatcher = UseCaseDispatcher()
        self._supported_events = set(websocket_config.use_case_events)

    async def handle_message(
        self, message: WebSocketMessage, context: Dict[str, Any]
    ) -> Optional[WebSocketResponse]:
        """Handle an incoming WebSocket message"""
        # Create dispatch context
        dispatch_context = DispatchContext(
            websocket=context.get("websocket"),
            room_id=context.get("room_id", ""),
            room_state=context.get("room_state"),
            player_id=context.get("player_id"),
            player_name=context.get("player_name"),
        )

        # Dispatch to use case
        response = await self.dispatcher.dispatch(
            message.event, message.data, dispatch_context
        )

        if response:
            return WebSocketResponse(
                event=response.get("event", ""),
                data=response.get("data", {}),
                success=response.get("success", True),
                error=response.get("error"),
            )

        return None

    def can_handle(self, event: str) -> bool:
        """Check if this handler can process the given event"""
        return event in self._supported_events

    def get_supported_events(self) -> List[str]:
        """Get list of events this handler supports"""
        return list(self._supported_events)


class ApplicationMessageRouter(IMessageRouter):
    """Application layer message router"""

    def __init__(self):
        self._handlers: Dict[str, IMessageHandler] = {}
        self._default_handler: Optional[IMessageHandler] = None

        # Register default use case handler
        self.register_handler(UseCaseMessageHandler())

    async def route(
        self, message: WebSocketMessage, context: Dict[str, Any]
    ) -> Optional[WebSocketResponse]:
        """Route a message to the appropriate handler"""
        # Find handler for event
        handler = self.get_handler_for_event(message.event)

        if handler:
            try:
                return await handler.handle_message(message, context)
            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)
                return WebSocketResponse(
                    event="error",
                    data={
                        "message": f"Failed to handle {message.event}",
                        "type": "handler_error",
                    },
                    success=False,
                    error=str(e),
                )

        # No handler found
        return WebSocketResponse(
            event="error",
            data={
                "message": f"No handler for event: {message.event}",
                "type": "no_handler",
            },
            success=False,
        )

    def register_handler(self, handler: IMessageHandler) -> None:
        """Register a message handler"""
        for event in handler.get_supported_events():
            self._handlers[event] = handler
            logger.debug(f"Registered handler for event: {event}")

    def get_handler_for_event(self, event: str) -> Optional[IMessageHandler]:
        """Get the handler for a specific event"""
        return self._handlers.get(event, self._default_handler)


class WebSocketConnectionContext(IConnectionContext):
    """Implementation of connection context"""

    def __init__(self, connection_id: str, room_id: str = ""):
        self.connection_id = connection_id
        self.room_id = room_id
        self.player_id: Optional[str] = None
        self.player_name: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def get_player_id(self) -> Optional[str]:
        """Get the player ID for this connection"""
        return self.player_id

    def get_room_id(self) -> Optional[str]:
        """Get the room ID for this connection"""
        return self.room_id

    def get_connection_id(self) -> str:
        """Get the unique connection ID"""
        return self.connection_id

    def set_player_info(self, player_id: str, player_name: str) -> None:
        """Set player information for this connection"""
        self.player_id = player_id
        self.player_name = player_name

    def set_room_id(self, room_id: str) -> None:
        """Set the room ID for this connection"""
        self.room_id = room_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "connection_id": self.connection_id,
            "room_id": self.room_id,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "metadata": self.metadata,
        }


class ApplicationEventPublisher(IEventPublisher):
    """Event publisher using existing broadcast infrastructure"""

    async def publish_event(
        self,
        event_name: str,
        data: Dict[str, Any],
        room_id: Optional[str] = None,
        player_ids: Optional[List[str]] = None,
    ) -> None:
        """Publish an event"""
        if room_id:
            await self.publish_to_room(room_id, event_name, data)
        elif player_ids:
            for player_id in player_ids:
                await self.publish_to_player(player_id, event_name, data)

    async def publish_to_room(
        self,
        room_id: str,
        event_name: str,
        data: Dict[str, Any],
        exclude_player_ids: Optional[List[str]] = None,
    ) -> None:
        """Publish an event to all players in a room"""
        # Use legacy broadcast for now
        await broadcast(room_id, event_name, data)

        # TODO: Implement exclude_player_ids when infrastructure supports it
        if exclude_player_ids:
            logger.warning("exclude_player_ids not yet implemented in broadcast")

    async def publish_to_player(
        self, player_id: str, event_name: str, data: Dict[str, Any]
    ) -> None:
        """Publish an event to a specific player"""
        # TODO: Implement player-specific messaging
        logger.warning(f"Player-specific messaging not yet implemented for {player_id}")
        # For now, we can't send to specific players without room context


class ApplicationMessageValidator(IMessageValidator):
    """Message validator using existing validation"""

    def validate_message(
        self, message: Dict[str, Any]
    ) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Validate a WebSocket message"""
        # Check if validation should be bypassed
        event = message.get("event", "")
        if self.should_bypass_validation(event):
            # Bypass validation for migrated events
            return True, None, message.get("data", {})

        # Use legacy validation
        return validate_websocket_message(message)

    def validate_event(self, event: str) -> bool:
        """Check if an event name is valid"""
        # Check if it's a known use case event
        if event in websocket_config.use_case_events:
            return True

        # Check legacy validation
        from api.validation.websocket_validators import WebSocketMessageValidator

        return event in WebSocketMessageValidator.ALLOWED_EVENTS

    def should_bypass_validation(self, event: str) -> bool:
        """Check if validation should be bypassed for an event"""
        return websocket_config.should_bypass_validation(event)


# Factory functions
def create_message_handler() -> IMessageHandler:
    """Create the default message handler"""
    return UseCaseMessageHandler()


def create_message_router() -> IMessageRouter:
    """Create the default message router"""
    return ApplicationMessageRouter()


def create_event_publisher() -> IEventPublisher:
    """Create the default event publisher"""
    return ApplicationEventPublisher()


def create_message_validator() -> IMessageValidator:
    """Create the default message validator"""
    return ApplicationMessageValidator()


def create_connection_context(
    connection_id: str, room_id: str = ""
) -> IConnectionContext:
    """Create a connection context"""
    return WebSocketConnectionContext(connection_id, room_id)
