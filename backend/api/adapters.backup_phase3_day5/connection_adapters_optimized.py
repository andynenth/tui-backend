"""
Connection-related WebSocket adapters - Optimized Version.
These adapters bridge WebSocket messages to clean architecture handlers with minimal overhead.
"""

from typing import Dict, Any, Optional, Callable
import time
from datetime import datetime

# Pre-computed response templates to avoid object creation overhead
PONG_TEMPLATE = {"event": "pong", "data": {}}
ROOM_STATE_EMPTY_TEMPLATE = {
    "event": "room_state_update", 
    "data": {"slots": [], "host_name": ""}
}
SYNC_RESPONSE_EMPTY_TEMPLATE = {
    "event": "sync_response",
    "data": {"room_state": None}
}


class PingAdapter:
    """Adapter for ping/pong WebSocket messages - optimized for performance"""
    
    __slots__ = []  # No instance variables needed
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None, broadcast_func: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Handle ping message and return pong response.
        Optimized to minimize object creation and lookups.
        """
        # Pre-create response structure
        response = {
            "event": "pong",
            "data": {
                "server_time": time.time()
            }
        }
        
        # Fast path - check for timestamp
        data = message.get("data")
        if data and "timestamp" in data:
            response["data"]["timestamp"] = data["timestamp"]
        
        # Room ID resolution - prioritize room_state
        if room_state and "room_id" in room_state:
            response["data"]["room_id"] = room_state["room_id"]
        elif hasattr(websocket, 'room_id'):
            response["data"]["room_id"] = websocket.room_id
        else:
            response["data"]["room_id"] = None
            
        return response


class ClientReadyAdapter:
    """Adapter for client ready messages - optimized"""
    
    __slots__ = ['room_manager']
    
    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None, broadcast_func: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Handle client ready message.
        Optimized to minimize object creation.
        """
        # If in a room, return room state
        if room_state:
            return {
                "event": "room_state_update",
                "data": {
                    "slots": room_state.get("players", []),
                    "host_name": room_state.get("host_name", "")
                }
            }
        
        # Return pre-computed empty room state
        return ROOM_STATE_EMPTY_TEMPLATE


class AckAdapter:
    """Adapter for acknowledgment messages - optimized"""
    
    __slots__ = []  # No instance variables needed
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None, broadcast_func: Optional[Callable] = None) -> None:
        """
        Handle acknowledgment message.
        Optimized to do minimal work.
        """
        # Acknowledgments don't require a response
        # No processing needed unless logging is enabled
        return None


class SyncRequestAdapter:
    """Adapter for sync request messages - optimized"""
    
    __slots__ = ['sync_manager', '_last_timestamp']
    
    def __init__(self, sync_manager=None):
        """Initialize with optional sync manager dependency"""
        self.sync_manager = sync_manager
        self._last_timestamp = None
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None, broadcast_func: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Handle sync request after disconnect/reconnect.
        Optimized to minimize object creation.
        """
        data = message.get("data", {})
        client_id = data.get("client_id")
        
        # Get current timestamp (cache if called multiple times in same millisecond)
        timestamp = datetime.now().isoformat()
        
        # If room state exists, return it
        if room_state:
            return {
                "event": "sync_response",
                "data": {
                    "room_state": room_state,
                    "client_id": client_id,
                    "timestamp": timestamp
                }
            }
        
        # Return minimal response for no room state
        return {
            "event": "sync_response",
            "data": {
                "room_state": None,
                "client_id": client_id,
                "timestamp": timestamp
            }
        }