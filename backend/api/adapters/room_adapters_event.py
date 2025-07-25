"""
Event-based room adapters.

These adapters publish domain events instead of directly returning responses,
enabling complete decoupling from infrastructure concerns.
"""

from typing import Dict, Any, Optional
import uuid
import logging

# Import domain events
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.domain.events.all_events import (
    RoomCreated, PlayerJoinedRoom, PlayerLeftRoom,
    BotAdded, PlayerRemoved, InvalidActionAttempted,
    EventMetadata
)
from backend.infrastructure.events.in_memory_event_bus import get_event_bus
from .adapter_event_config import should_adapter_use_events, is_adapter_in_shadow_mode

logger = logging.getLogger(__name__)


class CreateRoomAdapterEvent:
    """Event-based adapter for room creation"""
    
    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle create_room by publishing RoomCreated event.
        """
        data = message.get("data", {})
        player_name = data.get("player_name")
        
        if not player_name:
            # Publish error event
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                room_id="",  # No room yet
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                player_name="unknown",
                action_type="create_room",
                reason="Player name is required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            # Still return error for compatibility
            return {
                "event": "error",
                "data": {
                    "message": "Player name is required",
                    "type": "validation_error"
                }
            }
        
        # Generate room ID
        room_id = f"room_{uuid.uuid4().hex[:8]}"
        
        # Create metadata
        metadata = EventMetadata(
            user_id=getattr(websocket, 'player_id', None),
            correlation_id=message.get('correlation_id')
        )
        
        # Publish the event
        event = RoomCreated(
            room_id=room_id,
            host_id=getattr(websocket, 'player_id', str(id(websocket))),
            host_name=player_name,
            metadata=metadata
        )
        
        await self.event_bus.publish(event)
        
        # For now, still return the response for compatibility
        return {
            "event": "room_created",
            "data": {
                "room_id": room_id,
                "host_name": player_name,
                "success": True
            }
        }


class JoinRoomAdapterEvent:
    """Event-based adapter for joining rooms"""
    
    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle join_room by publishing PlayerJoinedRoom event.
        """
        data = message.get("data", {})
        room_id = data.get("room_id")
        player_name = data.get("player_name")
        
        if not room_id or not player_name:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                room_id=room_id or "",
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                player_name="unknown",
                action_type="join_room",
                reason="Room ID and player name are required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Room ID and player name are required",
                    "type": "validation_error"
                }
            }
        
        # Create metadata
        metadata = EventMetadata(
            user_id=getattr(websocket, 'player_id', None),
            correlation_id=message.get('correlation_id')
        )
        
        # Determine slot (would come from room manager in real implementation)
        slot = 1  # Placeholder
        
        # Publish the event
        event = PlayerJoinedRoom(
            room_id=room_id,
            player_id=getattr(websocket, 'player_id', str(id(websocket))),
            player_name=player_name,
            player_slot=f"P{slot}",
            metadata=metadata
        )
        
        await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "joined_room",
            "data": {
                "room_id": room_id,
                "player_name": player_name,
                "success": True,
                "slot": slot
            }
        }


class LeaveRoomAdapterEvent:
    """Event-based adapter for leaving rooms"""
    
    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle leave_room by publishing PlayerLeftRoom event.
        """
        data = message.get("data", {})
        player_name = data.get("player_name")
        
        if not player_name:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="leave_room",
                reason="Player name is required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Player name is required",
                    "type": "validation_error"
                }
            }
        
        # Get room ID from room state or websocket
        room_id = None
        if room_state:
            room_id = room_state.get("room_id")
        elif hasattr(websocket, 'room_id'):
            room_id = websocket.room_id
        
        if room_id:
            # Create metadata
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            # Publish the event
            event = PlayerLeftRoom(
                room_id=room_id,
                player_name=player_name,
                metadata=metadata
            )
            
            await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "left_room",
            "data": {
                "player_name": player_name,
                "success": True
            }
        }


class GetRoomStateAdapterEvent:
    """Event-based adapter for getting room state"""
    
    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle get_room_state request.
        
        This is a query, not a command, so it doesn't generate events.
        """
        # Queries don't generate events
        if room_state:
            return {
                "event": "room_state",
                "data": room_state
            }
        
        return {
            "event": "room_state",
            "data": {
                "slots": [],
                "host_name": None,
                "game_active": False
            }
        }


class AddBotAdapterEvent:
    """Event-based adapter for adding bots"""
    
    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle add_bot by publishing BotAdded event.
        """
        data = message.get("data", {})
        difficulty = data.get("difficulty", "medium")
        
        # Get room ID
        room_id = None
        if room_state:
            room_id = room_state.get("room_id")
        elif hasattr(websocket, 'room_id'):
            room_id = websocket.room_id
        
        if not room_id:
            return {
                "event": "error",
                "data": {
                    "message": "Must be in a room to add bots",
                    "type": "validation_error"
                }
            }
        
        # Generate bot name
        bot_name = f"Bot_{difficulty[:3].upper()}"
        slot = 2  # Would be determined by room state
        
        # Create metadata
        metadata = EventMetadata(
            user_id=getattr(websocket, 'player_id', None),
            correlation_id=message.get('correlation_id')
        )
        
        # Publish the event
        event = BotAdded(
            room_id=room_id,
            bot_id=f"bot_{uuid.uuid4().hex[:8]}",
            bot_name=bot_name,
            player_slot=f"P{slot}",
            added_by_id=getattr(websocket, 'player_id', str(id(websocket))),
            added_by_name="unknown",  # Would get from room state
            metadata=metadata
        )
        
        await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "bot_added",
            "data": {
                "bot_name": bot_name,
                "difficulty": difficulty,
                "slot": slot,
                "success": True
            }
        }


class RemovePlayerAdapterEvent:
    """Event-based adapter for removing players"""
    
    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
        self.event_bus = get_event_bus()
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle remove_player by publishing PlayerRemoved event.
        """
        data = message.get("data", {})
        player_name = data.get("player_name")
        requester = data.get("requester")
        
        if not player_name:
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            error_event = InvalidActionAttempted(
                player_id=getattr(websocket, 'player_id', str(id(websocket))),
                action="remove_player",
                reason="Player name is required",
                metadata=metadata
            )
            await self.event_bus.publish(error_event)
            
            return {
                "event": "error",
                "data": {
                    "message": "Player name is required",
                    "type": "validation_error"
                }
            }
        
        # Get room ID
        room_id = None
        if room_state:
            room_id = room_state.get("room_id")
        elif hasattr(websocket, 'room_id'):
            room_id = websocket.room_id
        
        if room_id:
            # Create metadata
            metadata = EventMetadata(
                user_id=getattr(websocket, 'player_id', None),
                correlation_id=message.get('correlation_id')
            )
            
            # Publish the event
            event = PlayerRemoved(
                room_id=room_id,
                removed_player_id=player_name,  # Using name as ID for now
                removed_player_name=player_name,
                removed_player_slot="unknown",  # Need to get from room state
                removed_by_id=requester or "host",
                removed_by_name=requester or "host",
                metadata=metadata
            )
            
            await self.event_bus.publish(event)
        
        # Still return response for compatibility
        return {
            "event": "player_removed",
            "data": {
                "player_name": player_name,
                "removed_by": requester,
                "success": True
            }
        }


# Factory functions to get the appropriate adapter based on config
def get_create_room_adapter(room_manager=None):
    """Get create room adapter based on feature flag."""
    if should_adapter_use_events("create_room"):
        return CreateRoomAdapterEvent(room_manager)
    else:
        from .room_adapters import _handle_create_room
        return _handle_create_room


def get_join_room_adapter(room_manager=None):
    """Get join room adapter based on feature flag."""
    if should_adapter_use_events("join_room"):
        return JoinRoomAdapterEvent(room_manager)
    else:
        from .room_adapters import _handle_join_room
        return _handle_join_room


def get_leave_room_adapter(room_manager=None):
    """Get leave room adapter based on feature flag."""
    if should_adapter_use_events("leave_room"):
        return LeaveRoomAdapterEvent(room_manager)
    else:
        from .room_adapters import _handle_leave_room
        return _handle_leave_room


def get_room_state_adapter(room_manager=None):
    """Get room state adapter based on feature flag."""
    if should_adapter_use_events("get_room_state"):
        return GetRoomStateAdapterEvent(room_manager)
    else:
        from .room_adapters import _handle_get_room_state
        return _handle_get_room_state


def get_add_bot_adapter(room_manager=None):
    """Get add bot adapter based on feature flag."""
    if should_adapter_use_events("add_bot"):
        return AddBotAdapterEvent(room_manager)
    else:
        from .room_adapters import _handle_add_bot
        return _handle_add_bot


def get_remove_player_adapter(room_manager=None):
    """Get remove player adapter based on feature flag."""
    if should_adapter_use_events("remove_player"):
        return RemovePlayerAdapterEvent(room_manager)
    else:
        from .room_adapters import _handle_remove_player
        return _handle_remove_player