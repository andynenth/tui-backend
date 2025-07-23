# application/interfaces/notification_service.py
"""
Notification service interface for the application layer.
This abstracts how notifications are sent to players.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class NotificationType(Enum):
    """Types of notifications that can be sent."""
    GAME_EVENT = "game_event"
    PLAYER_ACTION = "player_action"
    SYSTEM_MESSAGE = "system_message"
    ERROR = "error"
    INFO = "info"


@dataclass
class Notification:
    """Value object representing a notification."""
    type: NotificationType
    event: str
    data: Dict[str, Any]
    targets: List[str]  # List of player IDs or "all"
    room_id: Optional[str] = None
    priority: str = "normal"  # "low", "normal", "high"


class NotificationService(ABC):
    """
    Interface for sending notifications to players.
    
    This abstracts the actual transport mechanism (WebSocket, push notifications, etc.)
    from the application layer.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def is_player_connected(self, player_id: str) -> bool:
        """
        Check if a player is currently connected.
        
        Args:
            player_id: The player to check
            
        Returns:
            True if the player is connected
        """
        pass
    
    @abstractmethod
    async def get_connected_players(self, room_id: str) -> List[str]:
        """
        Get list of connected players in a room.
        
        Args:
            room_id: The room to check
            
        Returns:
            List of connected player IDs
        """
        pass