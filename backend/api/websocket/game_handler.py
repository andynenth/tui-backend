# api/websocket/game_handler.py
"""
Clean WebSocket handler for game operations.
Uses application layer commands and use cases.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

from application.commands import (
    CreateRoomCommand,
    JoinRoomCommand,
    LeaveRoomCommand,
    StartGameCommand,
    DeclareCommand,
    PlayTurnCommand,
    AddBotCommand,
    RemoveBotCommand
)

from ..dependencies import get_container

logger = logging.getLogger(__name__)


class GameWebSocketHandler:
    """
    Handles WebSocket connections for game operations.
    
    This handler:
    - Receives WebSocket messages
    - Converts them to commands
    - Executes through command bus
    - Returns results to client
    """
    
    def __init__(self):
        self._container = get_container()
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        room_id: Optional[str] = None
    ):
        """
        Handle a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            room_id: Optional room ID for direct room connection
        """
        await websocket.accept()
        
        player_id = None
        player_name = None
        
        try:
            # Handle messages
            while True:
                data = await websocket.receive_json()
                
                event_type = data.get("type")
                payload = data.get("data", {})
                
                # Route to appropriate handler
                result = await self._handle_event(
                    event_type,
                    payload,
                    player_id,
                    player_name,
                    room_id
                )
                
                # Update player info if needed
                if event_type in ["join_room", "create_room"] and result.get("success"):
                    player_name = payload.get("player_name")
                    player_id = result.get("player_id", player_name)
                    
                    # Register connection
                    await self._container.connection_manager.register_connection(
                        connection=websocket,
                        player_id=player_id,
                        player_name=player_name,
                        room_id=result.get("room_id", room_id)
                    )
                
                # Send response
                await websocket.send_json({
                    "type": f"{event_type}_response",
                    "data": result
                })
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for {player_name or 'unknown'}")
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)}
            })
        finally:
            # Clean up connection
            if player_id:
                await self._container.connection_manager.unregister_connection(websocket)
    
    async def _handle_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str],
        player_name: Optional[str],
        room_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Handle a specific event type.
        
        Args:
            event_type: Type of event
            payload: Event data
            player_id: Current player ID
            player_name: Current player name
            room_id: Current room ID
            
        Returns:
            Response data
        """
        try:
            # Create room
            if event_type == "create_room":
                command = CreateRoomCommand(
                    host_name=payload.get("player_name", ""),
                    room_settings=payload.get("settings", {})
                )
                result = await self._container.command_bus.execute(command)
                
                if result.success:
                    return {
                        "success": True,
                        "room_id": result.value.room_id,
                        "join_code": result.value.join_code,
                        "player_id": player_id or payload.get("player_name")
                    }
                else:
                    return {"success": False, "error": result.error}
            
            # Join room
            elif event_type == "join_room":
                # Determine room ID from join code or direct ID
                target_room_id = payload.get("room_id") or room_id
                join_code = payload.get("join_code")
                
                if join_code and not target_room_id:
                    # Look up room by join code
                    room_info = await self._container.room_service.get_room_by_join_code(
                        join_code
                    )
                    if room_info:
                        target_room_id = room_info.room_id
                    else:
                        return {"success": False, "error": "Invalid join code"}
                
                command = JoinRoomCommand(
                    room_id=target_room_id,
                    player_name=payload.get("player_name", ""),
                    player_token=payload.get("token")
                )
                result = await self._container.command_bus.execute(command)
                
                if result.success:
                    return {
                        "success": True,
                        "room_id": target_room_id,
                        "player_count": result.value.player_count,
                        "game_in_progress": result.value.game_in_progress,
                        "player_id": player_id or payload.get("player_name")
                    }
                else:
                    return {"success": False, "error": result.error}
            
            # Leave room
            elif event_type == "leave_room":
                if not player_name or not room_id:
                    return {"success": False, "error": "Not in a room"}
                
                command = LeaveRoomCommand(
                    room_id=room_id,
                    player_name=player_name
                )
                result = await self._container.command_bus.execute(command)
                
                return {
                    "success": result.success,
                    "error": result.error if not result.success else None
                }
            
            # Start game
            elif event_type == "start_game":
                if not player_name or not room_id:
                    return {"success": False, "error": "Not in a room"}
                
                command = StartGameCommand(
                    room_id=room_id,
                    requesting_player=player_name
                )
                result = await self._container.command_bus.execute(command)
                
                if result.success:
                    return {
                        "success": True,
                        "game_id": result.value.game_id,
                        "players": result.value.players
                    }
                else:
                    return {"success": False, "error": result.error}
            
            # Declare
            elif event_type == "declare":
                if not player_name or not room_id:
                    return {"success": False, "error": "Not in a room"}
                
                command = DeclareCommand(
                    room_id=room_id,
                    player_name=player_name,
                    declaration=payload.get("value", 0)
                )
                result = await self._container.command_bus.execute(command)
                
                if result.success:
                    return {
                        "success": True,
                        "declaration": result.value.declaration,
                        "declarations_complete": result.value.declarations_complete,
                        "remaining_players": result.value.remaining_players
                    }
                else:
                    return {"success": False, "error": result.error}
            
            # Play turn
            elif event_type == "play":
                if not player_name or not room_id:
                    return {"success": False, "error": "Not in a room"}
                
                command = PlayTurnCommand(
                    room_id=room_id,
                    player_name=player_name,
                    piece_indices=payload.get("pieces", [])
                )
                result = await self._container.command_bus.execute(command)
                
                if result.success:
                    return {
                        "success": True,
                        "turn_number": result.value.turn_number,
                        "pieces_played": result.value.pieces_played,
                        "play_type": result.value.play_type
                    }
                else:
                    return {"success": False, "error": result.error}
            
            # Add bot
            elif event_type == "add_bot":
                if not player_name or not room_id:
                    return {"success": False, "error": "Not in a room"}
                
                command = AddBotCommand(
                    room_id=room_id,
                    requesting_player=player_name,
                    bot_name=payload.get("bot_name", "Bot"),
                    difficulty=payload.get("difficulty", "medium")
                )
                result = await self._container.command_bus.execute(command)
                
                return {
                    "success": result.success,
                    "error": result.error if not result.success else None
                }
            
            # Remove bot
            elif event_type == "remove_bot":
                if not player_name or not room_id:
                    return {"success": False, "error": "Not in a room"}
                
                command = RemoveBotCommand(
                    room_id=room_id,
                    requesting_player=player_name,
                    bot_name=payload.get("bot_name", "")
                )
                result = await self._container.command_bus.execute(command)
                
                return {
                    "success": result.success,
                    "error": result.error if not result.success else None
                }
            
            # Unknown event
            else:
                return {
                    "success": False,
                    "error": f"Unknown event type: {event_type}"
                }
                
        except Exception as e:
            logger.error(f"Error handling {event_type}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Internal error: {str(e)}"
            }