"""
WebSocket Disconnection Handler
Handles business logic for player disconnections
"""

import logging
from typing import Optional, Dict, Any

from infrastructure.websocket.connection_singleton import broadcast
from infrastructure.dependencies import get_unit_of_work, get_bot_service
from application.services.room_application_service import RoomApplicationService
from api.websocket.connection_manager import connection_manager
from api.websocket.message_queue import message_queue_manager

logger = logging.getLogger(__name__)


class DisconnectHandler:
    """
    Handles business logic when a player disconnects.
    Separated from infrastructure concerns.
    """
    
    async def handle_player_disconnect(
        self,
        connection_info: Optional[Dict[str, Any]],
        room_id: str
    ) -> None:
        """
        Handle player disconnection business logic.
        
        Args:
            connection_info: Connection information dict
            room_id: The room ID
        """
        if not connection_info:
            return
            
        player_name = connection_info.get("player_name")
        if not player_name or room_id == "lobby":
            return
            
        logger.info(
            f"🚪 [ROOM_DEBUG] Processing disconnect for player '{player_name}' "
            f"in room '{room_id}'"
        )
        
        try:
            uow = get_unit_of_work()
            async with uow:
                room = await uow.rooms.get_by_id(room_id)
                
                if not room:
                    logger.warning(f"Room {room_id} not found during disconnect")
                    return
                    
                # Check if game has started
                if room.game and room.game.is_started and not room.game.is_finished:
                    # Game in progress - handle mid-game disconnect
                    await self._handle_ingame_disconnect(
                        room, player_name, uow
                    )
                else:
                    # Pre-game disconnect - treat as leave_room
                    await self._handle_pregame_disconnect(
                        room, player_name, uow
                    )
                    
        except Exception as e:
            logger.error(
                f"Error handling disconnect for {player_name} in room {room_id}: {e}",
                exc_info=True
            )
            
    async def _handle_ingame_disconnect(
        self,
        room: Any,
        player_name: str,
        uow: Any
    ) -> None:
        """
        Handle disconnection during an active game.
        
        Args:
            room: The room entity
            player_name: The disconnecting player's name
            uow: Unit of work
        """
        logger.info(
            f"🎮 [ROOM_DEBUG] Mid-game disconnect detected for '{player_name}' "
            f"in room '{room.id}' (round {room.game.current_round})"
        )
        
        # Find the player
        player = next((p for p in room.players if p.name == player_name), None)
        if not player:
            logger.warning(f"Player {player_name} not found in room {room.id}")
            return
            
        # Mark player as disconnected
        player.is_connected = False
        
        # Check if we need to activate a bot
        if not player.is_bot:
            # Activate bot for disconnected human player
            bot_service = get_bot_service()
            
            # Create bot replacement
            await bot_service.activate_bot_for_player(player.id, room.id)
            
            # Notify other players
            await broadcast(
                room.id,
                "player_replaced_by_bot",
                {
                    "player_name": player_name,
                    "ai_activated": True,
                    "can_reconnect": True,
                    "is_bot": True,
                }
            )
            
            # Check for host migration
            if player.id == room.host_player_id:
                new_host = await self._migrate_host(room)
                if new_host:
                    await broadcast(
                        room.id,
                        "host_changed",
                        {
                            "old_host": player_name,
                            "new_host": new_host,
                            "message": f"{new_host} is now the host",
                        }
                    )
                    
        # Save room changes
        await uow.rooms.save(room)
        await uow.commit()
        
        # Check if all remaining players are bots
        if room.get_human_count() == 0:
            logger.info(
                f"🤖 [ROOM_DEBUG] Room '{room.id}' has no human players, "
                f"status: {room.status.value}"
            )
            
    async def _handle_pregame_disconnect(
        self,
        room: Any,
        player_name: str,
        uow: Any
    ) -> None:
        """
        Handle disconnection before game starts.
        
        Args:
            room: The room entity
            player_name: The disconnecting player's name
            uow: Unit of work
        """
        logger.info(
            f"🚪 [ROOM_DEBUG] Pre-game disconnect detected for player '{player_name}' "
            f"in room '{room.id}'"
        )
        
        # Use room application service to handle leave
        room_service = RoomApplicationService(uow)
        
        # Find player
        player = next((p for p in room.players if p.name == player_name), None)
        if not player:
            return
            
        # Remove player from room
        room.remove_player(player.id)
        
        # Check for host migration
        if player.id == room.host_player_id and room.players:
            new_host_player = room.players[0]
            room.host_player_id = new_host_player.id
            
            await broadcast(
                room.id,
                "host_changed",
                {
                    "old_host": player_name,
                    "new_host": new_host_player.name,
                    "message": f"{new_host_player.name} is now the host",
                }
            )
            
        # Notify room of player leaving
        await broadcast(
            room.id,
            "player_left",
            {
                "player_id": player.id,
                "player_name": player_name,
                "players_count": len(room.players),
                "room_id": room.id,
            }
        )
        
        # Save changes
        await uow.rooms.save(room)
        await uow.commit()
        
        # Delete room if empty
        if not room.players:
            await uow.rooms.delete(room.id)
            await uow.commit()
            logger.info(f"🗑️ [ROOM_DEBUG] Deleted empty room '{room.id}'")
            
    async def _migrate_host(self, room: Any) -> Optional[str]:
        """
        Migrate host to another player.
        
        Args:
            room: The room entity
            
        Returns:
            New host name or None
        """
        # Find a connected human player
        for player in room.players:
            if not player.is_bot and player.is_connected:
                room.host_player_id = player.id
                return player.name
                
        # No connected humans, pick first player
        if room.players:
            room.host_player_id = room.players[0].id
            return room.players[0].name
            
        return None