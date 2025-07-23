# api/websocket/endpoints.py
"""
WebSocket endpoints using clean architecture.
"""

import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .game_handler import GameWebSocketHandler
from .room_handler import RoomWebSocketHandler
from ..dependencies import get_container

logger = logging.getLogger(__name__)

# Create router
websocket_router = APIRouter()


class UnifiedWebSocketHandler:
    """
    Unified handler that routes to specific handlers.
    """
    
    def __init__(self):
        self._game_handler = GameWebSocketHandler()
        self._room_handler = RoomWebSocketHandler()
        self._container = get_container()
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        room_id: Optional[str] = None
    ):
        """
        Handle a WebSocket connection with unified routing.
        """
        await websocket.accept()
        
        player_id = None
        player_name = None
        current_room_id = room_id
        
        try:
            while True:
                data = await websocket.receive_json()
                
                event_type = data.get("type")
                payload = data.get("data", {})
                
                # Determine handler based on event type
                if event_type in ["create_room", "join_room", "leave_room", 
                                  "start_game", "declare", "play", 
                                  "add_bot", "remove_bot"]:
                    # Game events
                    result = await self._game_handler._handle_event(
                        event_type,
                        payload,
                        player_id,
                        player_name,
                        current_room_id
                    )
                    
                    # Update connection info if needed
                    if event_type in ["join_room", "create_room"] and result.get("success"):
                        player_name = payload.get("player_name")
                        player_id = result.get("player_id", player_name)
                        current_room_id = result.get("room_id")
                        
                        # Register connection
                        await self._container.connection_manager.register_connection(
                            connection=websocket,
                            player_id=player_id,
                            player_name=player_name,
                            room_id=current_room_id
                        )
                    elif event_type == "leave_room" and result.get("success"):
                        current_room_id = None
                
                elif event_type in ["update_settings", "kick_player", 
                                   "transfer_host", "close_room", 
                                   "get_room_info", "list_rooms"]:
                    # Room events
                    result = await self._room_handler.handle_room_event(
                        event_type,
                        payload,
                        player_name,
                        current_room_id
                    )
                
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown event type: {event_type}"
                    }
                
                # Send response
                await websocket.send_json({
                    "type": f"{event_type}_response",
                    "data": result
                })
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for {player_name or 'unknown'}")
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}", exc_info=True)
            try:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": str(e)}
                })
            except:
                pass
        finally:
            # Clean up connection
            if player_id:
                await self._container.connection_manager.unregister_connection(websocket)
            
            # Handle player disconnect
            if player_name and current_room_id:
                # Mark player as disconnected
                try:
                    await self._container.room_service.remove_player(
                        current_room_id,
                        player_name,
                        reason="disconnected"
                    )
                except Exception as e:
                    logger.error(f"Error handling disconnect: {str(e)}")


# Create handler instance
unified_handler = UnifiedWebSocketHandler()


@websocket_router.websocket("/ws/lobby")
async def websocket_lobby(websocket: WebSocket):
    """
    WebSocket endpoint for lobby operations.
    """
    await unified_handler.handle_connection(websocket, room_id=None)


@websocket_router.websocket("/ws/{room_id}")
async def websocket_room(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for room-specific operations.
    """
    await unified_handler.handle_connection(websocket, room_id=room_id)