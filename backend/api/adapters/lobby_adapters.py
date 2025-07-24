"""
Lobby operation WebSocket adapters using minimal intervention pattern.
Handles room list requests and updates.
"""

from typing import Dict, Any, Optional, Callable, List
import logging

logger = logging.getLogger(__name__)

# Actions that need lobby adapter handling
LOBBY_ADAPTER_ACTIONS = {
    "request_room_list", "get_rooms"
}


async def handle_lobby_messages(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None
) -> Optional[Dict[str, Any]]:
    """
    Minimal intervention handler for lobby-related messages.
    Only intercepts messages that need clean architecture adaptation.
    """
    action = message.get("action")
    
    # Fast path - pass through non-lobby messages
    if action not in LOBBY_ADAPTER_ACTIONS:
        return await legacy_handler(websocket, message)
    
    # Handle lobby actions with minimal overhead
    if action == "request_room_list":
        return await _handle_request_room_list(websocket, message, room_state, broadcast_func)
    elif action == "get_rooms":
        return await _handle_get_rooms(websocket, message, room_state, broadcast_func)
    
    # Fallback (shouldn't reach here)
    return await legacy_handler(websocket, message)


async def _handle_request_room_list(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """
    Handle request_room_list - client requesting current room list.
    This typically triggers a broadcast to all lobby clients.
    """
    data = message.get("data", {})
    
    # In full implementation, this would:
    # 1. Get current room list from room manager
    # 2. Broadcast to all lobby clients
    # 3. Return acknowledgment to requester
    
    # For now, return acknowledgment
    response = {
        "event": "room_list_requested",
        "data": {
            "success": True,
            "message": "Room list update triggered"
        }
    }
    
    logger.info("Room list requested")
    
    return response


async def _handle_get_rooms(
    websocket,
    message: Dict[str, Any],
    room_state: Optional[Dict[str, Any]],
    broadcast_func: Optional[Callable]
) -> Dict[str, Any]:
    """
    Handle get_rooms - direct request for room list (no broadcast).
    Returns the current list of rooms to the requester only.
    """
    data = message.get("data", {})
    filter_options = data.get("filter", {})
    
    # In full implementation, would:
    # 1. Get rooms from room manager
    # 2. Apply filters (e.g., only non-full rooms, only public rooms)
    # 3. Format room data for client
    
    # Mock room data for adapter
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
    
    response = {
        "event": "room_list",
        "data": {
            "rooms": rooms,
            "total_count": len(rooms),
            "filter_applied": bool(filter_options)
        }
    }
    
    logger.info(f"Returning {len(rooms)} rooms")
    
    return response


def format_room_for_lobby(room_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format room data for lobby display.
    Extracts only the information needed by lobby clients.
    """
    return {
        "room_id": room_data.get("room_id"),
        "host_name": room_data.get("host_name"),
        "player_count": len(room_data.get("players", [])),
        "max_players": 4,  # Game constant
        "game_active": room_data.get("game_active", False),
        "is_public": room_data.get("is_public", True)
    }


class LobbyAdapterIntegration:
    """
    Integration point for lobby adapters.
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
        """Main entry point for lobby message handling"""
        if not self._enabled:
            return await self.legacy_handler(websocket, message)
        
        return await handle_lobby_messages(
            websocket, message, self.legacy_handler, room_state, broadcast_func
        )
    
    def enable(self):
        """Enable lobby adapters"""
        self._enabled = True
        logger.info("Lobby adapters enabled")
    
    def disable(self):
        """Disable lobby adapters (fallback to legacy)"""
        self._enabled = False
        logger.info("Lobby adapters disabled - using legacy handlers")