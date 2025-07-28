"""
Connection-related WebSocket adapters.
These adapters bridge WebSocket messages to clean architecture handlers.
"""

from typing import Dict, Any, Optional
import time
from datetime import datetime


class PingAdapter:
    """Adapter for ping/pong WebSocket messages"""
    
    def __init__(self):
        """Initialize ping adapter"""
        pass
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle ping message and return pong response.
        
        Contract requirements:
        - Echo back the timestamp if provided
        - Include server_time
        - Include room_id if in a room
        """
        data = message.get("data", {})
        
        # Build response according to contract
        response = {
            "event": "pong",
            "data": {
                "server_time": time.time()
            }
        }
        
        # Echo timestamp if provided
        if "timestamp" in data:
            response["data"]["timestamp"] = data["timestamp"]
        
        # Include room_id if available
        if room_state and "room_id" in room_state:
            response["data"]["room_id"] = room_state["room_id"]
        elif hasattr(websocket, 'room_id'):
            response["data"]["room_id"] = websocket.room_id
        else:
            response["data"]["room_id"] = None
            
        return response


class ClientReadyAdapter:
    """Adapter for client ready messages"""
    
    def __init__(self, room_manager=None):
        """Initialize with optional room manager dependency"""
        self.room_manager = room_manager
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle client ready message.
        
        Contract requirements:
        - Return room_state_update with current room info
        - May broadcast room_list_update to lobby
        """
        data = message.get("data", {})
        player_name = data.get("player_name")
        
        # If in a room, return room state
        if room_state:
            return {
                "event": "room_state_update",
                "data": {
                    "slots": room_state.get("players", []),
                    "host_name": room_state.get("host_name", "")
                }
            }
        
        # If in lobby, return empty room state
        # (broadcasts would be handled separately)
        return {
            "event": "room_state_update", 
            "data": {
                "slots": [],
                "host_name": ""
            }
        }


class AckAdapter:
    """Adapter for acknowledgment messages"""
    
    def __init__(self):
        """Initialize ack adapter"""
        pass
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Handle acknowledgment message.
        
        Contract requirements:
        - No response expected (ack is one-way)
        """
        # Acknowledgments don't require a response
        # Could log or track for reliability if needed
        data = message.get("data", {})
        sequence = data.get("sequence")
        client_id = data.get("client_id")
        
        # Log acknowledgment if needed
        # logger.debug(f"Received ack: seq={sequence}, client={client_id}")
        
        return None  # No response for ack


class SyncRequestAdapter:
    """Adapter for sync request messages"""
    
    def __init__(self, sync_manager=None):
        """Initialize with optional sync manager dependency"""
        self.sync_manager = sync_manager
    
    async def handle(self, websocket, message: Dict[str, Any], room_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle sync request after disconnect/reconnect.
        
        Contract requirements:
        - Return current game state for the client
        - Include any missed events if possible
        """
        data = message.get("data", {})
        client_id = data.get("client_id")
        
        # For now, return current room state
        # In full implementation, would restore client's exact state
        if room_state:
            return {
                "event": "sync_response",
                "data": {
                    "room_state": room_state,
                    "client_id": client_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        return {
            "event": "sync_response",
            "data": {
                "room_state": None,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
        }