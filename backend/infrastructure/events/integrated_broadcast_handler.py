"""
Integrated broadcast handler that connects events to the WebSocket system.

This handler subscribes to all domain events and converts them to broadcasts
using the event-to-broadcast mapper, maintaining 100% compatibility.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from domain.events.base import DomainEvent, GameEvent
from domain.events.all_events import *
from infrastructure.events.decorators import event_handler
from infrastructure.events.event_broadcast_mapper import event_broadcast_mapper
from infrastructure.events.in_memory_event_bus import get_event_bus

logger = logging.getLogger(__name__)


class IntegratedBroadcastHandler:
    """
    Main handler that converts all domain events to WebSocket broadcasts.

    This class:
    1. Subscribes to all domain events
    2. Maps them to broadcast format using the mapper
    3. Sends broadcasts through the socket manager
    4. Maintains exact message compatibility
    """

    def __init__(self, room_manager: Optional[Any] = None):
        """
        Initialize the broadcast handler.

        Args:
            room_manager: Optional room manager for getting room state
        """
        self.room_manager = room_manager
        self._event_bus = get_event_bus()
        self._initialized = False

        # Track some state for context
        self._player_pieces_count: Dict[str, Dict[str, int]] = (
            {}
        )  # room_id -> player -> count

    def initialize(self):
        """Subscribe to all relevant domain events."""
        if self._initialized:
            return

        # Subscribe as a generic handler for all GameEvents
        self._event_bus.subscribe(GameEvent, self._handle_game_event, priority=50)

        # Subscribe to specific non-game events
        self._event_bus.subscribe(
            PlayerConnected, self._handle_connection_event, priority=50
        )
        self._event_bus.subscribe(
            PlayerDisconnected, self._handle_connection_event, priority=50
        )
        self._event_bus.subscribe(
            ConnectionHeartbeat, self._handle_connection_event, priority=50
        )
        self._event_bus.subscribe(
            RoomListUpdated, self._handle_lobby_event, priority=50
        )
        self._event_bus.subscribe(ErrorOccurred, self._handle_error_event, priority=50)

        self._initialized = True
        logger.info("IntegratedBroadcastHandler initialized")

    async def _handle_game_event(self, event: GameEvent):
        """Handle any game event and convert to broadcast."""
        try:
            # Get context for the event
            context = self._build_context(event)

            # Map the event to broadcast format
            broadcast_info = event_broadcast_mapper.map_event(event, context)

            if not broadcast_info:
                logger.debug(
                    f"No broadcast mapping for event type: {type(event).__name__}"
                )
                return

            # Import here to avoid circular dependency
            from infrastructure.websocket.connection_singleton import broadcast

            # Send the broadcast based on target type
            if broadcast_info["target_type"] == "room" and broadcast_info["target_id"]:
                await broadcast(
                    broadcast_info["target_id"],
                    broadcast_info["event_name"],
                    broadcast_info["data"],
                )
                logger.debug(
                    f"Broadcast {broadcast_info['event_name']} to room {broadcast_info['target_id']}"
                )

            elif broadcast_info["target_type"] == "response":
                # Response events need special handling - they go to specific websocket
                # This will be handled by the adapter layer
                logger.debug(f"Response event {broadcast_info['event_name']} prepared")

            elif broadcast_info["target_type"] == "player":
                # Player-specific events also need adapter support
                logger.debug(
                    f"Player event {broadcast_info['event_name']} for {broadcast_info['target_id']}"
                )

            # Update any tracked state
            self._update_tracked_state(event)

        except Exception as e:
            logger.error(
                f"Error handling game event {type(event).__name__}: {e}", exc_info=True
            )

    async def _handle_connection_event(self, event: DomainEvent):
        """Handle connection events."""
        context = self._build_context(event)
        broadcast_info = event_broadcast_mapper.map_event(event, context)

        if broadcast_info and broadcast_info["target_type"] == "response":
            # Connection events typically send responses, not broadcasts
            logger.debug(f"Connection event {type(event).__name__} handled")

    async def _handle_lobby_event(self, event: DomainEvent):
        """Handle lobby events."""
        from socket_manager import broadcast

        broadcast_info = event_broadcast_mapper.map_event(event, None)

        if broadcast_info and broadcast_info["target_type"] == "lobby":
            # Lobby broadcasts go to all connected clients in lobby
            await broadcast(
                "lobby", broadcast_info["event_name"], broadcast_info["data"]
            )
            logger.debug(f"Lobby broadcast: {broadcast_info['event_name']}")

    async def _handle_error_event(self, event: DomainEvent):
        """Handle error events."""
        logger.error(f"System error event: {event}")

    def _build_context(self, event: DomainEvent) -> Dict[str, Any]:
        """Build context information for event mapping."""
        context = {}

        # Add room state if available and event has room_id
        if hasattr(event, "room_id") and self.room_manager:
            room = self.room_manager.get_room(event.room_id)
            if room:
                context["room_state"] = self._get_room_state_for_broadcast(room)
                context["room_id"] = event.room_id

        # Add pieces played count for turn tracking
        if isinstance(event, PiecesPlayed):
            room_counts = self._player_pieces_count.get(event.room_id, {})
            player_count = room_counts.get(event.player_name, 0)
            context["pieces_played_count"] = player_count + len(event.pieces)

        # Add timestamp
        context["timestamp"] = datetime.utcnow().timestamp()

        return context

    def _get_room_state_for_broadcast(self, room) -> Dict[str, Any]:
        """Convert room object to broadcast format."""
        return {
            "room_id": room.room_id,
            "players": [
                {
                    "name": player.name,
                    "slot": f"P{i+1}",
                    "is_bot": player.is_bot,
                    "connected": player.connected,
                }
                for i, player in enumerate(room.players)
                if player is not None
            ],
            "host_name": room.host.name if room.host else None,
            "started": room.game_started,
            "timestamp": datetime.utcnow().timestamp(),
        }

    def _update_tracked_state(self, event: DomainEvent):
        """Update any state we're tracking for context."""
        # Track pieces played for remaining count
        if isinstance(event, PiecesPlayed):
            if event.room_id not in self._player_pieces_count:
                self._player_pieces_count[event.room_id] = {}

            if event.player_name not in self._player_pieces_count[event.room_id]:
                self._player_pieces_count[event.room_id][event.player_name] = 0

            self._player_pieces_count[event.room_id][event.player_name] += len(
                event.pieces
            )

        # Reset counts on new round
        elif isinstance(event, RoundStarted):
            self._player_pieces_count[event.room_id] = {}

        # Clean up on game end
        elif isinstance(event, GameEnded):
            self._player_pieces_count.pop(event.room_id, None)


# Global instance
_broadcast_handler: Optional[IntegratedBroadcastHandler] = None


def get_broadcast_handler(
    room_manager: Optional["RoomManager"] = None,
) -> IntegratedBroadcastHandler:
    """Get or create the global broadcast handler."""
    global _broadcast_handler

    if _broadcast_handler is None:
        _broadcast_handler = IntegratedBroadcastHandler(room_manager)
        _broadcast_handler.initialize()

    return _broadcast_handler


def reset_broadcast_handler():
    """Reset the broadcast handler (useful for testing)."""
    global _broadcast_handler
    _broadcast_handler = None
