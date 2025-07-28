"""
WebSocket-based notification service implementation.

This module provides a concrete implementation of the NotificationService
interface that sends notifications via WebSocket.
"""

import logging
from typing import Dict, Any, List, Optional

from application.interfaces import NotificationService
from infrastructure.websocket.connection_singleton import broadcast
from infrastructure.feature_flags import get_feature_flags

logger = logging.getLogger(__name__)


class WebSocketNotificationService(NotificationService):
    """
    Notification service that sends notifications via WebSocket.
    
    This implementation uses the existing WebSocket infrastructure
    to deliver real-time notifications to clients.
    """
    
    def __init__(self):
        """Initialize the notification service."""
        self._feature_flags = get_feature_flags()
        self._sent_count = 0
        self._error_count = 0
        
    async def notify_player(
        self,
        player_id: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a notification to a specific player.
        
        Args:
            player_id: Target player's ID
            message: Notification message
            data: Additional notification data
        """
        try:
            # Use player_id as channel for player-specific messages
            notification_data = {
                'message': message,
                'data': data or {}
            }
            await broadcast(player_id, "notification", notification_data)
            self._sent_count += 1
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Failed to notify player {player_id}: {e}")
    
    async def notify_room(
        self,
        room_id: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a notification to all players in a room.
        
        Args:
            room_id: Target room's ID
            message: Notification message
            data: Additional notification data
        """
        try:
            notification_data = {
                'message': message,
                'data': data or {}
            }
            await broadcast(room_id, "notification", notification_data)
            self._sent_count += 1
            logger.debug(f"Sent notification to room {room_id}: {message}")
            
        except Exception as e:
            self._error_count += 1
            logger.error(f"Failed to notify room {room_id}: {e}")
    
    async def notify_players(
        self,
        player_ids: List[str],
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a notification to multiple specific players.
        
        Args:
            player_ids: List of player IDs to notify
            message: Notification message
            data: Additional notification data
        """
        for player_id in player_ids:
            await self.notify_player(player_id, message, data)