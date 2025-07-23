# api/websocket/room_handler.py
"""
Clean WebSocket handler for room operations.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket

from application.commands import (
    UpdateRoomSettingsCommand,
    KickPlayerCommand,
    TransferHostCommand,
    CloseRoomCommand
)

from ..dependencies import get_container

logger = logging.getLogger(__name__)


class RoomWebSocketHandler:
    """
    Handles WebSocket operations for room management.
    
    This handler manages:
    - Room settings updates
    - Player management (kick, transfer host)
    - Room lifecycle (close)
    """
    
    def __init__(self):
        self._container = get_container()
    
    async def handle_room_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        player_name: str,
        room_id: str
    ) -> Dict[str, Any]:
        """
        Handle room-specific events.
        
        Args:
            event_type: Type of event
            payload: Event data
            player_name: Current player name
            room_id: Current room ID
            
        Returns:
            Response data
        """
        try:
            # Update room settings
            if event_type == "update_settings":
                command = UpdateRoomSettingsCommand(
                    room_id=room_id,
                    player_name=player_name,
                    settings=payload.get("settings", {})
                )
                result = await self._container.command_bus.execute(command)
                
                return {
                    "success": result.success,
                    "error": result.error if not result.success else None
                }
            
            # Kick player
            elif event_type == "kick_player":
                command = KickPlayerCommand(
                    room_id=room_id,
                    requesting_player=player_name,
                    player_to_kick=payload.get("player_name", "")
                )
                result = await self._container.command_bus.execute(command)
                
                return {
                    "success": result.success,
                    "error": result.error if not result.success else None
                }
            
            # Transfer host
            elif event_type == "transfer_host":
                command = TransferHostCommand(
                    room_id=room_id,
                    current_host=player_name,
                    new_host=payload.get("new_host", "")
                )
                result = await self._container.command_bus.execute(command)
                
                return {
                    "success": result.success,
                    "error": result.error if not result.success else None
                }
            
            # Close room
            elif event_type == "close_room":
                command = CloseRoomCommand(
                    room_id=room_id,
                    requesting_player=player_name
                )
                result = await self._container.command_bus.execute(command)
                
                return {
                    "success": result.success,
                    "error": result.error if not result.success else None
                }
            
            # Get room info
            elif event_type == "get_room_info":
                room_info = await self._container.room_service.get_room_info(room_id)
                
                if room_info:
                    return {
                        "success": True,
                        "room": {
                            "room_id": room_info.room_id,
                            "join_code": room_info.join_code,
                            "host_name": room_info.host_name,
                            "players": room_info.players,
                            "player_count": room_info.player_count,
                            "max_players": room_info.max_players,
                            "game_in_progress": room_info.game_in_progress
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Room not found"
                    }
            
            # List rooms
            elif event_type == "list_rooms":
                rooms = await self._container.room_service.list_public_rooms(
                    include_full=payload.get("include_full", False),
                    include_in_game=payload.get("include_in_game", False)
                )
                
                return {
                    "success": True,
                    "rooms": [
                        {
                            "room_id": r.room_id,
                            "join_code": r.join_code,
                            "host_name": r.host_name,
                            "player_count": r.player_count,
                            "max_players": r.max_players,
                            "game_in_progress": r.game_in_progress
                        }
                        for r in rooms
                    ]
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown room event: {event_type}"
                }
                
        except Exception as e:
            logger.error(f"Error handling room event {event_type}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Internal error: {str(e)}"
            }