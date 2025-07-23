# application/services/room_service.py
"""
Room service orchestrates room-related operations.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from domain.events.player_events import (
    PlayerLeftEvent,
    RoomClosedEvent,
    HostTransferredEvent
)
from domain.interfaces.event_publisher import EventPublisher

from ..interfaces.notification_service import NotificationService


logger = logging.getLogger(__name__)


class RoomInfo:
    """Value object for room information."""
    def __init__(
        self,
        room_id: str,
        join_code: str,
        host_name: str,
        players: List[str],
        max_players: int = 4,
        game_in_progress: bool = False,
        created_at: Optional[datetime] = None
    ):
        self.room_id = room_id
        self.join_code = join_code
        self.host_name = host_name
        self.players = players
        self.max_players = max_players
        self.game_in_progress = game_in_progress
        self.created_at = created_at or datetime.utcnow()
    
    @property
    def player_count(self) -> int:
        return len(self.players)
    
    @property
    def is_full(self) -> bool:
        return self.player_count >= self.max_players


class RoomService:
    """
    Application service for room operations.
    
    This service orchestrates complex room operations that involve
    multiple domain objects and external services.
    """
    
    def __init__(
        self,
        room_repository,  # Will be defined in infrastructure
        game_repository,  # Will be defined in infrastructure
        event_publisher: EventPublisher,
        notification_service: NotificationService
    ):
        self._room_repository = room_repository
        self._game_repository = game_repository
        self._event_publisher = event_publisher
        self._notification_service = notification_service
    
    async def get_room_info(self, room_id: str) -> Optional[RoomInfo]:
        """Get room information."""
        room = await self._room_repository.get(room_id)
        if not room:
            return None
        
        game_in_progress = False
        if room.game_id:
            game = await self._game_repository.get(room.game_id)
            if game and not game.is_finished():
                game_in_progress = True
        
        return RoomInfo(
            room_id=room.id,
            join_code=room.join_code,
            host_name=room.host_name,
            players=room.get_player_names(),
            max_players=room.max_players,
            game_in_progress=game_in_progress,
            created_at=room.created_at
        )
    
    async def get_room_by_join_code(self, join_code: str) -> Optional[RoomInfo]:
        """Get room by join code."""
        room = await self._room_repository.get_by_join_code(join_code)
        if not room:
            return None
        
        return await self.get_room_info(room.id)
    
    async def list_public_rooms(
        self,
        include_full: bool = False,
        include_in_game: bool = False
    ) -> List[RoomInfo]:
        """
        List all public rooms.
        
        Args:
            include_full: Include rooms that are full
            include_in_game: Include rooms with games in progress
            
        Returns:
            List of room information
        """
        rooms = await self._room_repository.list_public_rooms()
        
        room_infos = []
        for room in rooms:
            info = await self.get_room_info(room.id)
            if not info:
                continue
            
            # Apply filters
            if not include_full and info.is_full:
                continue
            if not include_in_game and info.game_in_progress:
                continue
            
            room_infos.append(info)
        
        # Sort by creation time (newest first)
        room_infos.sort(key=lambda r: r.created_at, reverse=True)
        
        return room_infos
    
    async def remove_player(
        self,
        room_id: str,
        player_name: str,
        reason: str = "left"
    ) -> bool:
        """
        Remove a player from a room.
        
        Args:
            room_id: The room ID
            player_name: The player to remove
            reason: Reason for removal (left, kicked, disconnected)
            
        Returns:
            True if player was removed
        """
        room = await self._room_repository.get(room_id)
        if not room:
            return False
        
        if not room.has_player(player_name):
            return False
        
        was_host = room.host_name == player_name
        
        # Remove the player
        room.remove_player(player_name)
        
        # Handle host transfer if needed
        new_host = None
        if was_host and room.player_count() > 0:
            # Transfer host to next player
            new_host = room.get_player_names()[0]
            room.host_name = new_host
            
            await self._event_publisher.publish(
                HostTransferredEvent(
                    room_id=room_id,
                    old_host=player_name,
                    new_host=new_host
                )
            )
        
        # Save the room
        await self._room_repository.save(room)
        
        # Publish player left event
        await self._event_publisher.publish(
            PlayerLeftEvent(
                room_id=room_id,
                player_name=player_name,
                reason=reason,
                player_count=room.player_count()
            )
        )
        
        # Notify remaining players
        notification_data = {
            "player_name": player_name,
            "reason": reason,
            "player_count": room.player_count(),
            "players": room.get_player_names()
        }
        
        if new_host:
            notification_data["new_host"] = new_host
        
        await self._notification_service.notify_room(
            room_id,
            "player_left",
            notification_data
        )
        
        # Close room if empty
        if room.player_count() == 0:
            await self.close_room(room_id)
        
        return True
    
    async def close_room(self, room_id: str) -> None:
        """Close a room."""
        room = await self._room_repository.get(room_id)
        if not room:
            return
        
        # Mark as closed
        room.is_closed = True
        await self._room_repository.save(room)
        
        # Publish room closed event
        await self._event_publisher.publish(
            RoomClosedEvent(
                room_id=room_id,
                reason="empty"
            )
        )
        
        logger.info(f"Room {room_id} closed")
    
    async def update_room_settings(
        self,
        room_id: str,
        settings: Dict[str, Any]
    ) -> bool:
        """
        Update room settings.
        
        Args:
            room_id: The room ID
            settings: New settings
            
        Returns:
            True if settings were updated
        """
        room = await self._room_repository.get(room_id)
        if not room:
            return False
        
        # Update settings
        room.settings.update(settings)
        
        # Save the room
        await self._room_repository.save(room)
        
        # Notify all players
        await self._notification_service.notify_room(
            room_id,
            "settings_updated",
            {
                "settings": room.settings
            }
        )
        
        return True
    
    async def get_player_rooms(self, player_name: str) -> List[RoomInfo]:
        """Get all rooms a player is in."""
        rooms = await self._room_repository.get_player_rooms(player_name)
        
        room_infos = []
        for room in rooms:
            info = await self.get_room_info(room.id)
            if info:
                room_infos.append(info)
        
        return room_infos