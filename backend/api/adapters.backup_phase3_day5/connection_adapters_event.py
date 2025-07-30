"""
Event-based connection adapters.

These adapters publish domain events instead of directly returning responses,
enabling complete decoupling from infrastructure concerns.
"""

from typing import Dict, Any, Optional
import time
from datetime import datetime

# Import domain events
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from domain.events.all_events import ConnectionHeartbeat, ClientReady, EventMetadata
from infrastructure.events.in_memory_event_bus import get_event_bus


class PingAdapterEvent:
    """Event-based adapter for ping/pong WebSocket messages"""

    def __init__(self):
        """Initialize ping adapter"""
        self.event_bus = get_event_bus()

    async def handle(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle ping message by publishing ConnectionHeartbeat event.

        The event will be converted to a pong response by the broadcast handler.
        """
        data = message.get("data", {})

        # Extract websocket ID (this would come from the websocket object)
        websocket_id = getattr(websocket, "id", str(id(websocket)))

        # Create metadata
        metadata = EventMetadata(
            user_id=getattr(websocket, "player_id", None),
            correlation_id=message.get("correlation_id"),
        )

        # Publish the event
        event = ConnectionHeartbeat(
            websocket_id=websocket_id,
            client_timestamp=data.get("timestamp"),
            server_timestamp=time.time(),
            metadata=metadata,
        )

        await self.event_bus.publish(event)

        # For now, still return the response for compatibility
        # This will be removed once the event system is fully integrated
        response = {"event": "pong", "data": {"server_time": time.time()}}

        if "timestamp" in data:
            response["data"]["timestamp"] = data["timestamp"]

        if room_state and "room_id" in room_state:
            response["data"]["room_id"] = room_state["room_id"]
        elif hasattr(websocket, "room_id"):
            response["data"]["room_id"] = websocket.room_id
        else:
            response["data"]["room_id"] = None

        return response


class ClientReadyAdapterEvent:
    """Event-based adapter for client ready messages"""

    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()

    async def handle(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle client ready message by publishing ClientReady event.
        """
        data = message.get("data", {})
        player_name = data.get("player_name")

        # Only publish event if we have the necessary data
        if player_name and room_state and room_state.get("room_id"):
            metadata = EventMetadata(
                user_id=getattr(websocket, "player_id", None),
                correlation_id=message.get("correlation_id"),
            )

            event = ClientReady(
                room_id=room_state["room_id"],
                player_id=getattr(websocket, "player_id", str(id(websocket))),
                player_name=player_name,
                metadata=metadata,
            )

            await self.event_bus.publish(event)

        # Still return response for compatibility
        if room_state:
            return {
                "event": "room_state_update",
                "data": {
                    "slots": room_state.get("players", []),
                    "host_name": room_state.get("host_name", ""),
                },
            }

        return {"event": "room_state_update", "data": {"slots": [], "host_name": ""}}


class AckAdapterEvent:
    """Event-based adapter for acknowledgment messages"""

    def __init__(self):
        """Initialize ack adapter"""
        self.event_bus = get_event_bus()

    async def handle(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Handle acknowledgment message.

        Acks don't typically generate events, they're just confirmations.
        """
        # Acknowledgments don't need to publish events
        # They're just confirmations that a message was received
        return None


class SyncRequestAdapterEvent:
    """Event-based adapter for sync request messages"""

    def __init__(self, room_manager=None, game_state_machine=None):
        """Initialize with dependencies"""
        self.room_manager = room_manager
        self.game_state_machine = game_state_machine
        self.event_bus = get_event_bus()

    async def handle(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle sync request by returning current state.

        Sync requests are queries, not commands, so they don't generate events.
        """
        data = message.get("data", {})

        # Build sync response with current state
        response = {
            "event": "sync_response",
            "data": {
                "room_state": room_state or {},
                "client_id": data.get("client_id"),
                "timestamp": datetime.utcnow().timestamp(),
            },
        }

        # Add game state if available
        if room_state and "game_state" in room_state:
            response["data"]["game_state"] = room_state["game_state"]

        return response


# Feature flag to use event-based adapters
USE_EVENT_ADAPTERS = False


# Factory functions to get the appropriate adapter
def get_ping_adapter():
    """Get ping adapter based on feature flag."""
    if USE_EVENT_ADAPTERS:
        return PingAdapterEvent()
    else:
        from .connection_adapters import PingAdapter

        return PingAdapter()


def get_client_ready_adapter(room_manager=None):
    """Get client ready adapter based on feature flag."""
    if USE_EVENT_ADAPTERS:
        return ClientReadyAdapterEvent(room_manager)
    else:
        from .connection_adapters import ClientReadyAdapter

        return ClientReadyAdapter(room_manager)


def get_ack_adapter():
    """Get ack adapter based on feature flag."""
    if USE_EVENT_ADAPTERS:
        return AckAdapterEvent()
    else:
        from .connection_adapters import AckAdapter

        return AckAdapter()


def get_sync_request_adapter(room_manager=None, game_state_machine=None):
    """Get sync request adapter based on feature flag."""
    if USE_EVENT_ADAPTERS:
        return SyncRequestAdapterEvent(room_manager, game_state_machine)
    else:
        from .connection_adapters import SyncRequestAdapter

        return SyncRequestAdapter(room_manager, game_state_machine)
