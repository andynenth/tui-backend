"""
Legacy WebSocket handlers extracted from ws.py.
This allows us to wrap the existing logic and use it as the fallback for the adapter system.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from infrastructure.websocket.broadcast_adapter import broadcast
from shared_instances import shared_room_manager
from api.websocket.connection_manager import connection_manager
from api.websocket.message_queue import message_queue_manager

logger = logging.getLogger(__name__)
room_manager = shared_room_manager


class LegacyWebSocketHandlers:
    """
    Container for all legacy WebSocket event handlers.
    These are the existing implementations that adapters will gradually replace.
    """
    
    def __init__(self):
        self.room_manager = room_manager
        self.connection_manager = connection_manager
        self.message_queue_manager = message_queue_manager
    
    async def handle_message(self, websocket, message: Dict[str, Any], room_id: str) -> Optional[Dict[str, Any]]:
        """
        Main entry point for legacy message handling.
        Routes messages to appropriate legacy handlers based on event_name.
        """
        event_name = message.get("event")
        event_data = message.get("data", {})
        
        # Map event names to handler methods
        handlers = {
            "ping": self.handle_ping,
            "client_ready": self.handle_client_ready,
            "create_room": self.handle_create_room,
            "join_room": self.handle_join_room,
            "leave_room": self.handle_leave_room,
            "get_room_state": self.handle_get_room_state,
            "get_rooms": self.handle_get_rooms,
            "request_room_list": self.handle_request_room_list,
            "add_bot": self.handle_add_bot,
            "remove_player": self.handle_remove_player,
            "start_game": self.handle_start_game,
            "declare": self.handle_declare,
            "play": self.handle_play,
            "play_pieces": self.handle_play_pieces,
            "request_redeal": self.handle_request_redeal,
            "accept_redeal": self.handle_accept_redeal,
            "decline_redeal": self.handle_decline_redeal,
            "redeal_decision": self.handle_redeal_decision,
            "player_ready": self.handle_player_ready,
            "leave_game": self.handle_leave_game,
            # Special handlers that don't follow the pattern
            "ack": self.handle_ack,
            "sync_request": self.handle_sync_request,
        }
        
        handler = handlers.get(event_name)
        if handler:
            return await handler(websocket, event_data, room_id)
        else:
            # Unknown event
            return {
                "event": "error",
                "data": {
                    "message": f"Unknown event: {event_name}",
                    "type": "unknown_event"
                }
            }
    
    async def handle_ping(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle ping/pong heartbeat"""
        return {
            "event": "pong",
            "data": {
                "timestamp": data.get("timestamp"),
                "server_time": asyncio.get_event_loop().time(),
                "room_id": room_id if room_id != "lobby" else None
            }
        }
    
    async def handle_client_ready(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle client ready - placeholder for actual implementation"""
        # This would contain the actual logic from ws.py
        # For now, return a basic response
        if room_id == "lobby":
            available_rooms = await self.room_manager.list_rooms()
            return {
                "event": "room_list_update",
                "data": {
                    "rooms": available_rooms,
                    "timestamp": asyncio.get_event_loop().time()
                }
            }
        else:
            # Room-specific client ready
            room = await self.room_manager.get_room(room_id)
            if room:
                summary = await room.summary()
                return {
                    "event": "room_state_update",
                    "data": {
                        "slots": summary.get("players", []),
                        "host_name": summary.get("host_name", "")
                    }
                }
        
        return None
    
    async def handle_ack(self, websocket, data: Dict[str, Any], room_id: str) -> None:
        """Handle message acknowledgment"""
        # Special case - ack doesn't return a response
        sequence = data.get("sequence")
        client_id = data.get("client_id", "unknown")
        
        if sequence is not None:
            from backend.socket_manager import socket_manager
            await socket_manager.handle_ack(room_id, sequence, client_id)
        
        return None
    
    async def handle_sync_request(self, websocket, data: Dict[str, Any], room_id: str) -> None:
        """Handle sync request"""
        # Special case - handled differently
        client_id = data.get("client_id", "unknown")
        from backend.socket_manager import socket_manager
        await socket_manager.request_client_sync(room_id, websocket, client_id)
        return None
    
    # Placeholder methods for other handlers
    # These would be implemented with the actual logic from ws.py
    
    async def handle_create_room(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle create room - placeholder"""
        # Would contain actual implementation from ws.py
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_join_room(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle join room - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_leave_room(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle leave room - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_get_room_state(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle get room state - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_get_rooms(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle get rooms - placeholder"""
        available_rooms = await self.room_manager.list_rooms()
        return {
            "event": "room_list",
            "data": {
                "rooms": available_rooms,
                "total_count": len(available_rooms),
                "filter_applied": False
            }
        }
    
    async def handle_request_room_list(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle request room list"""
        available_rooms = await self.room_manager.list_rooms()
        return {
            "event": "room_list_update",
            "data": {
                "rooms": available_rooms,
                "timestamp": asyncio.get_event_loop().time(),
                "requested_by": data.get("player_name", "unknown")
            }
        }
    
    async def handle_add_bot(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle add bot - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_remove_player(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle remove player - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_start_game(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle start game - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_declare(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle declare - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_play(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle play - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_play_pieces(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle play pieces - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_request_redeal(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle request redeal - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_accept_redeal(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle accept redeal - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_decline_redeal(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle decline redeal - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_redeal_decision(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle redeal decision - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_player_ready(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle player ready - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")
    
    async def handle_leave_game(self, websocket, data: Dict[str, Any], room_id: str) -> Dict[str, Any]:
        """Handle leave game - placeholder"""
        raise NotImplementedError("Legacy handler not fully implemented")


# Global instance
legacy_handlers = LegacyWebSocketHandlers()