"""
Reconnection service for managing player connection lifecycle.

This service orchestrates the complex process of handling disconnections
and reconnections, including bot activation and message queue management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from domain.entities.player import Player
from domain.entities.game import Game
from domain.entities.connection import PlayerConnection
from domain.entities.message_queue import PlayerQueue
from domain.value_objects import PlayerId, RoomId, ConnectionStatus
from domain.events import PlayerDisconnected, PlayerReconnected
from application.interfaces import UnitOfWork
from application.interfaces.services import (
    EventPublisher,
    NotificationService,
    BotService,
    Logger
)
from application.exceptions import ApplicationException


class ReconnectionService:
    """
    Service for managing player reconnections.
    
    This service handles:
    - Player disconnect detection and bot activation
    - Message queueing for disconnected players
    - Reconnection and state restoration
    - Bot deactivation on player return
    """
    
    def __init__(
        self,
        uow: UnitOfWork,
        event_publisher: EventPublisher,
        notification_service: NotificationService,
        bot_service: BotService,
        logger: Optional[Logger] = None
    ):
        self._uow = uow
        self._event_publisher = event_publisher
        self._notification_service = notification_service
        self._bot_service = bot_service
        self._logger = logger or logging.getLogger(__name__)
    
    async def handle_disconnect(
        self, 
        room_id: str, 
        player_name: str,
        activate_bot: bool = True
    ) -> None:
        """
        Handle player disconnection.
        
        Args:
            room_id: The room ID
            player_name: The player name
            activate_bot: Whether to activate bot replacement
        """
        async with self._uow:
            # Get room and validate
            room = await self._uow.rooms.get_by_id(room_id)
            if not room:
                raise ApplicationException(
                    f"Room {room_id} not found",
                    code="ROOM_NOT_FOUND"
                )
            
            # Find player
            player = room.get_player(player_name)
            if not player:
                raise ApplicationException(
                    f"Player {player_name} not in room",
                    code="PLAYER_NOT_FOUND"
                )
            
            # Check if game is in progress
            game = await self._uow.games.get_by_room_id(room_id)
            game_in_progress = game is not None and not game.is_finished
            
            # Disconnect player
            player.disconnect(room_id, activate_bot and game_in_progress)
            
            # Update connection status
            connection = await self._uow.connections.get(room_id, player_name)
            if connection:
                connection.status = ConnectionStatus.DISCONNECTED
                connection.disconnected_at = datetime.utcnow()
                await self._uow.connections.save(connection)
            
            # Create message queue if game in progress
            if game_in_progress:
                await self._uow.message_queues.create_queue(room_id, player_name)
            
            # Publish event
            event = PlayerDisconnected(
                room_id=room_id,
                player_name=player_name,
                disconnect_time=player.disconnect_time,
                was_bot_activated=player.is_bot and not player.original_is_bot,
                game_in_progress=game_in_progress
            )
            await self._event_publisher.publish_batch([event])
            
            # Bot will take action through existing bot management system
            # The bot service will detect the player is now a bot and schedule actions
            
            # Save room changes
            await self._uow.rooms.save(room)
            
            self._logger.info(
                f"Player {player_name} disconnected from room {room_id}. "
                f"Bot activated: {player.is_bot}, Game in progress: {game_in_progress}"
            )
    
    async def handle_reconnect(
        self,
        room_id: str,
        player_name: str,
        websocket_id: str
    ) -> Dict[str, Any]:
        """
        Handle player reconnection.
        
        Args:
            room_id: The room ID
            player_name: The player name
            websocket_id: New websocket connection ID
            
        Returns:
            Dict containing queued messages and current state
        """
        async with self._uow:
            # Get room and validate
            room = await self._uow.rooms.get_by_id(room_id)
            if not room:
                raise ApplicationException(
                    f"Room {room_id} not found",
                    code="ROOM_NOT_FOUND"
                )
            
            # Find player
            player = room.get_player(player_name)
            if not player:
                raise ApplicationException(
                    f"Player {player_name} not in room",
                    code="PLAYER_NOT_FOUND"
                )
            
            # Reconnect player
            player.reconnect(room_id)
            
            # Update connection
            connection = await self._uow.connections.get(room_id, player_name)
            if not connection:
                connection = PlayerConnection(
                    player_id=PlayerId(player_name),
                    room_id=RoomId(room_id),
                    status=ConnectionStatus.CONNECTED,
                    websocket_id=websocket_id
                )
            else:
                connection.status = ConnectionStatus.CONNECTED
                connection.websocket_id = websocket_id
                connection.reconnected_at = datetime.utcnow()
            
            await self._uow.connections.save(connection)
            
            # Get queued messages
            queued_messages = []
            queue = await self._uow.message_queues.get_queue(room_id, player_name)
            if queue:
                queued_messages = [msg.to_dict() for msg in queue.messages]
                # Clear queue after retrieval
                await self._uow.message_queues.clear_queue(room_id, player_name)
            
            # Get current game state
            game = await self._uow.games.get_by_room_id(room_id)
            current_state = game.to_dict() if game else None
            
            # Publish event
            event = PlayerReconnected(
                room_id=room_id,
                player_name=player_name,
                reconnect_time=datetime.utcnow(),
                was_bot_deactivated=player.original_is_bot != player.is_bot,
                messages_restored=len(queued_messages)
            )
            await self._event_publisher.publish_batch([event])
            
            # Save room changes
            await self._uow.rooms.save(room)
            
            self._logger.info(
                f"Player {player_name} reconnected to room {room_id}. "
                f"Restored {len(queued_messages)} messages"
            )
            
            return {
                "queued_messages": queued_messages,
                "current_state": current_state,
                "room_state": room.to_dict()
            }
    
    async def check_connection_health(self, room_id: str) -> List[Dict[str, Any]]:
        """
        Check health of all connections in a room.
        
        Args:
            room_id: The room ID
            
        Returns:
            List of connection statuses
        """
        async with self._uow:
            connections = await self._uow.connections.list_by_room(room_id)
            
            health_status = []
            for conn in connections:
                status = {
                    "player_name": conn.player_id.value,
                    "status": conn.status.value,
                    "websocket_id": conn.websocket_id,
                    "last_activity": conn.last_activity.isoformat() if conn.last_activity else None
                }
                
                # Check if connection is stale
                if conn.status == ConnectionStatus.CONNECTED and conn.last_activity:
                    time_since_activity = datetime.utcnow() - conn.last_activity
                    if time_since_activity.total_seconds() > 30:  # 30 second timeout
                        status["health"] = "stale"
                    else:
                        status["health"] = "healthy"
                else:
                    status["health"] = "disconnected"
                
                health_status.append(status)
            
            return health_status
    
    async def cleanup_disconnected_players(self, room_id: str, timeout_minutes: int = 10) -> int:
        """
        Clean up players who have been disconnected too long.
        
        Args:
            room_id: The room ID
            timeout_minutes: Minutes before considering player gone
            
        Returns:
            Number of players cleaned up
        """
        async with self._uow:
            room = await self._uow.rooms.get_by_id(room_id)
            if not room:
                return 0
            
            cleaned_up = 0
            cutoff_time = datetime.utcnow()
            
            for player in room.players[:]:  # Copy list to avoid modification during iteration
                if (player.disconnect_time and 
                    not player.is_connected and
                    (cutoff_time - player.disconnect_time).total_seconds() > timeout_minutes * 60):
                    
                    # Remove player from room
                    room.remove_player(player.name)
                    
                    # Clear their message queue
                    await self._uow.message_queues.clear_queue(room_id, player.name)
                    
                    # Remove connection
                    await self._uow.connections.delete(room_id, player.name)
                    
                    cleaned_up += 1
                    
                    self._logger.info(
                        f"Cleaned up disconnected player {player.name} from room {room_id}"
                    )
            
            if cleaned_up > 0:
                await self._uow.rooms.save(room)
            
            return cleaned_up