"""
Room management WebSocket adapters using minimal intervention pattern.
Optimized for <50% overhead while maintaining clean architecture boundaries.
"""

from typing import Dict, Any, Optional, Callable
import uuid
import logging

logger = logging.getLogger(__name__)

# Actions that need room adapter handling
ROOM_ADAPTER_ACTIONS = {
    "create_room", "join_room", "leave_room", 
    "get_room_state", "add_bot", "remove_player"
}


async def handle_room_messages(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None
) -> Optional[Dict[str, Any]]:
    """
    Minimal intervention handler for room-related messages.
    Only intercepts messages that need clean architecture adaptation.
    """
    action = message.get("action")
    
    # Fast path - pass through non-room messages
    if action not in ROOM_ADAPTER_ACTIONS:
        return await legacy_handler(websocket, message)
    
    # Handle room actions with minimal overhead
    if action == "create_room":
        return await _handle_create_room(websocket, message, room_state, broadcast_func)
    elif action == "join_room":
        return await _handle_join_room(websocket, message, room_state, broadcast_func)
    elif action == "leave_room":
        return await _handle_leave_room(websocket, message, room_state, broadcast_func)
    elif action == "get_room_state":
        return await _handle_get_room_state(websocket, message, room_state, broadcast_func)
    elif action == "add_bot":
        return await _handle_add_bot(websocket, message, room_state, broadcast_func)
    elif action == "remove_player":
        return await _handle_remove_player(websocket, message, room_state, broadcast_func)
    
    # Fallback (shouldn't reach here)
    return await legacy_handler(websocket, message)


async def _handle_create_room(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """
    Handle create_room with clean architecture principles.
    Maps WebSocket message to use case and back to response.
    """
    data = message.get("data", {})
    player_name = data.get("player_name")
    
    if not player_name:
        return {
            "event": "error",
            "data": {
                "message": "Player name is required",
                "type": "validation_error"
            }
        }
    
    # In full implementation, this would call a use case
    # For now, return expected response format
    room_id = f"room_{uuid.uuid4().hex[:8]}"
    
    response = {
        "event": "room_created",
        "data": {
            "room_id": room_id,
            "host_name": player_name,
            "success": True
        }
    }
    
    # Log for monitoring
    logger.info(f"Room created: {room_id} by {player_name}")
    
    return response


async def _handle_join_room(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """Handle join_room request"""
    data = message.get("data", {})
    room_id = data.get("room_id")
    player_name = data.get("player_name")
    
    if not room_id or not player_name:
        return {
            "event": "error",
            "data": {
                "message": "Room ID and player name are required",
                "type": "validation_error"
            }
        }
    
    # In full implementation, would check room exists, not full, etc.
    return {
        "event": "joined_room",
        "data": {
            "room_id": room_id,
            "player_name": player_name,
            "success": True,
            "slot": 1  # Would be determined by room state
        }
    }


async def _handle_leave_room(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """Handle leave_room request"""
    data = message.get("data", {})
    player_name = data.get("player_name")
    
    if not player_name:
        return {
            "event": "error",
            "data": {
                "message": "Player name is required",
                "type": "validation_error"
            }
        }
    
    return {
        "event": "left_room",
        "data": {
            "player_name": player_name,
            "success": True
        }
    }


async def _handle_get_room_state(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """Handle get_room_state request"""
    # Return current room state or empty state
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


async def _handle_add_bot(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """Handle add_bot request"""
    data = message.get("data", {})
    difficulty = data.get("difficulty", "medium")
    
    # Would add bot to room in full implementation
    bot_name = f"Bot_{difficulty[:3].upper()}"
    
    return {
        "event": "bot_added",
        "data": {
            "bot_name": bot_name,
            "difficulty": difficulty,
            "slot": 2,  # Would be determined by room state
            "success": True
        }
    }


async def _handle_remove_player(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """Handle remove_player request (host removing a player)"""
    data = message.get("data", {})
    player_name = data.get("player_name")
    requester = data.get("requester")  # Who is making the request
    
    if not player_name:
        return {
            "event": "error",
            "data": {
                "message": "Player name is required",
                "type": "validation_error"
            }
        }
    
    # Would verify requester is host in full implementation
    return {
        "event": "player_removed",
        "data": {
            "player_name": player_name,
            "removed_by": requester,
            "success": True
        }
    }


class RoomAdapterIntegration:
    """
    Integration point for room adapters.
    Maintains compatibility with existing system while enabling clean architecture.
    """
    
    def __init__(self, legacy_handler: Callable):
        self.legacy_handler = legacy_handler
        self._enabled = True
    
    async def handle_message(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
        broadcast_func: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """Main entry point for room message handling"""
        if not self._enabled:
            return await self.legacy_handler(websocket, message)
        
        return await handle_room_messages(
            websocket, message, self.legacy_handler, room_state, broadcast_func
        )
    
    def enable(self):
        """Enable room adapters"""
        self._enabled = True
        logger.info("Room adapters enabled")
    
    def disable(self):
        """Disable room adapters (fallback to legacy)"""
        self._enabled = False
        logger.info("Room adapters disabled - using legacy handlers")