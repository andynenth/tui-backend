# infrastructure/websocket/notification_adapter.py
"""
WebSocket implementation of the NotificationService interface.
"""

import logging
from typing import Dict, Any, List, Optional
import asyncio

from application.interfaces.notification_service import (
    NotificationService,
    Notification,
    NotificationType
)

logger = logging.getLogger(__name__)


class WebSocketNotificationAdapter(NotificationService):
    """
    Adapts WebSocket infrastructure to the NotificationService interface.
    
    This allows the application layer to send notifications without
    knowing about WebSocket implementation details.
    """
    
    def __init__(self, connection_manager, broadcast_service):
        """
        Initialize the adapter.
        
        Args:
            connection_manager: Manages WebSocket connections
            broadcast_service: Handles broadcasting to connections
        """
        self._connection_manager = connection_manager
        self._broadcast_service = broadcast_service
    
    async def notify_room(
        self,
        room_id: str,
        event_type: str,
        data: Dict[str, Any],
        exclude_players: Optional[List[str]] = None
    ) -> None:
        """
        Send a notification to all players in a room.
        
        Args:
            room_id: The room to notify
            event_type: Type of event (e.g., "phase_change", "turn_played")
            data: Event data to send
            exclude_players: Optional list of player IDs to exclude
        """
        try:
            await self._broadcast_service.broadcast_to_room(
                room_id=room_id,
                event_type=event_type,
                data=data,
                exclude_players=exclude_players or []
            )
            
            logger.debug(
                f"Notified room {room_id} with event {event_type}"
            )
        except Exception as e:
            logger.error(
                f"Failed to notify room {room_id}: {str(e)}",
                exc_info=True
            )
            # Don't raise - notifications are best effort
    
    async def notify_player(
        self,
        player_id: str,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Send a notification to a specific player.
        
        Args:
            player_id: The player to notify
            event_type: Type of event
            data: Event data to send
        """
        try:
            connection = self._connection_manager.get_connection(player_id)
            if connection:
                await self._broadcast_service.send_to_connection(
                    connection=connection,
                    event_type=event_type,
                    data=data
                )
                
                logger.debug(
                    f"Notified player {player_id} with event {event_type}"
                )
            else:
                logger.warning(
                    f"Player {player_id} not connected for notification"
                )
        except Exception as e:
            logger.error(
                f"Failed to notify player {player_id}: {str(e)}",
                exc_info=True
            )
    
    async def notify_players(
        self,
        player_ids: List[str],
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Send a notification to multiple specific players.
        
        Args:
            player_ids: List of players to notify
            event_type: Type of event
            data: Event data to send
        """
        # Use asyncio.gather for concurrent notifications
        tasks = [
            self.notify_player(player_id, event_type, data)
            for player_id in player_ids
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast(
        self,
        notification: Notification
    ) -> None:
        """
        Send a notification based on a Notification object.
        
        This is a more flexible method that accepts a full
        notification specification.
        
        Args:
            notification: The notification to send
        """
        # Convert notification type to event type string
        event_type = notification.event
        
        # Add notification metadata to data
        data = {
            **notification.data,
            "_notification_type": notification.type.value,
            "_priority": notification.priority
        }
        
        # Handle different target types
        if "all" in notification.targets:
            # Broadcast to all connected clients
            if notification.room_id:
                await self.notify_room(
                    notification.room_id,
                    event_type,
                    data
                )
            else:
                # Global broadcast
                await self._broadcast_service.broadcast_global(
                    event_type=event_type,
                    data=data
                )
        else:
            # Send to specific players
            await self.notify_players(
                notification.targets,
                event_type,
                data
            )
    
    async def is_player_connected(self, player_id: str) -> bool:
        """
        Check if a player is currently connected.
        
        Args:
            player_id: The player to check
            
        Returns:
            True if the player is connected
        """
        return self._connection_manager.is_connected(player_id)
    
    async def get_connected_players(self, room_id: str) -> List[str]:
        """
        Get list of connected players in a room.
        
        Args:
            room_id: The room to check
            
        Returns:
            List of connected player IDs
        """
        return self._connection_manager.get_room_connections(room_id)