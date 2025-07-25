"""
Event-based lobby adapters.

These adapters publish domain events instead of directly returning responses,
enabling complete decoupling from infrastructure concerns.
"""

from typing import Dict, Any, Optional, List
import logging

# Import domain events
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.domain.events.all_events import (
    RoomListRequested, RoomListUpdated, EventMetadata
)
from backend.infrastructure.events.in_memory_event_bus import get_event_bus
from .adapter_event_config import should_adapter_use_events

logger = logging.getLogger(__name__)


class RequestRoomListAdapterEvent:
    """Event-based adapter for requesting room list"""
    
    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle request_room_list by publishing RoomListRequested event.
        
        This will trigger a RoomListUpdated event to be published,
        which gets broadcast to all lobby clients.
        """
        data = message.get("data", {})
        
        # Create metadata
        metadata = EventMetadata(
            user_id=getattr(websocket, 'player_id', None),
            correlation_id=message.get('correlation_id')
        )
        
        # Publish the event
        event = RoomListRequested(
            requester_id=getattr(websocket, 'player_id', str(id(websocket))),
            metadata=metadata
        )
        
        await self.event_bus.publish(event)
        
        # In a full event-driven system, we might not return anything
        # For compatibility, return acknowledgment
        return {
            "event": "room_list_requested",
            "data": {
                "success": True,
                "message": "Room list update triggered"
            }
        }


class GetRoomsAdapterEvent:
    """Event-based adapter for getting rooms (direct query)"""
    
    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle get_rooms request.
        
        This is a query, not a command, so it doesn't generate events.
        It returns data directly to the requester.
        """
        data = message.get("data", {})
        filter_options = data.get("filter", {})
        
        # In full implementation, would get rooms from room manager
        # For now, use mock data
        mock_rooms = [
            {
                "room_id": "room_abc123",
                "host_name": "Alice",
                "player_count": 2,
                "max_players": 4,
                "game_active": False,
                "is_public": True
            },
            {
                "room_id": "room_def456",
                "host_name": "Bob",
                "player_count": 4,
                "max_players": 4,
                "game_active": True,
                "is_public": True
            }
        ]
        
        # Apply basic filtering
        rooms = mock_rooms
        if filter_options.get("available_only"):
            rooms = [r for r in rooms if r["player_count"] < r["max_players"]]
        if filter_options.get("not_in_game"):
            rooms = [r for r in rooms if not r["game_active"]]
        
        # For queries, we still return direct responses
        return {
            "event": "room_list",
            "data": {
                "rooms": rooms,
                "total_count": len(rooms),
                "filter_applied": bool(filter_options)
            }
        }


class RoomListUpdateHandler:
    """
    Handler that listens for room state changes and publishes
    RoomListUpdated events when the lobby needs to be notified.
    """
    
    def __init__(self, room_manager=None):
        """Initialize with room manager dependency"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()
    
    async def on_room_change(self, room_id: str):
        """
        Called when a room state changes (player joins/leaves, game starts, etc).
        Publishes RoomListUpdated event for lobby clients.
        """
        if not self.room_manager:
            return
        
        # Get current room list
        rooms = self._get_room_list()
        
        # Create metadata
        metadata = EventMetadata()
        
        # Publish the event
        event = RoomListUpdated(
            rooms=rooms,
            metadata=metadata
        )
        
        await self.event_bus.publish(event)
    
    def _get_room_list(self) -> List[Dict[str, Any]]:
        """Get formatted room list from room manager."""
        if not self.room_manager:
            return []
        
        # This would get actual rooms from room manager
        # For now, return mock data
        return [
            {
                "room_id": "room_abc123",
                "host_name": "Alice",
                "player_count": 2,
                "max_players": 4,
                "game_active": False,
                "is_public": True
            }
        ]


# Factory functions to get the appropriate adapter based on config
def get_request_room_list_adapter(room_manager=None):
    """Get request room list adapter based on feature flag."""
    if should_adapter_use_events("request_room_list"):
        return RequestRoomListAdapterEvent(room_manager)
    else:
        from .lobby_adapters import _handle_request_room_list
        return _handle_request_room_list


def get_rooms_adapter(room_manager=None):
    """Get rooms adapter based on feature flag."""
    if should_adapter_use_events("get_rooms"):
        return GetRoomsAdapterEvent(room_manager)
    else:
        from .lobby_adapters import _handle_get_rooms
        return _handle_get_rooms