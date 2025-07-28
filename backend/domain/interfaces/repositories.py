"""
Repository interfaces for the domain layer.

These interfaces define the contracts that infrastructure must implement
to provide persistence for domain entities.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from domain.entities.room import Room
from domain.entities.game import Game
from domain.entities.player import Player


class RoomRepository(ABC):
    """
    Interface for Room aggregate persistence.
    
    The infrastructure layer must provide an implementation
    that handles storage and retrieval of Room aggregates.
    """
    
    @abstractmethod
    async def save(self, room: Room) -> None:
        """
        Save or update a room.
        
        Args:
            room: Room aggregate to persist
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, room_id: str) -> Optional[Room]:
        """
        Find a room by its ID.
        
        Args:
            room_id: Unique room identifier
            
        Returns:
            Room if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Room]:
        """
        Get all rooms.
        
        Returns:
            List of all rooms
        """
        pass
    
    @abstractmethod
    async def find_by_player_name(self, player_name: str) -> Optional[Room]:
        """
        Find a room containing a specific player.
        
        Args:
            player_name: Name of the player
            
        Returns:
            Room containing the player, None if not found
        """
        pass
    
    @abstractmethod
    async def delete(self, room_id: str) -> bool:
        """
        Delete a room.
        
        Args:
            room_id: ID of room to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists(self, room_id: str) -> bool:
        """
        Check if a room exists.
        
        Args:
            room_id: ID to check
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def list_active(self, limit: int = 100) -> List[Room]:
        """
        Get list of active rooms (not completed/abandoned).
        
        Args:
            limit: Maximum number of rooms to return
            
        Returns:
            List of active rooms
        """
        pass
    
    @abstractmethod
    async def find_by_player(self, player_id: str) -> Optional[Room]:
        """
        Find a room containing a player by ID.
        
        Args:
            player_id: ID of the player (e.g., "room123_p0")
            
        Returns:
            Room containing the player, None if not found
        """
        pass
    
    async def get_by_id(self, room_id: str) -> Optional[Room]:
        """
        Alias for find_by_id for consistency with use cases.
        
        Args:
            room_id: Unique room identifier
            
        Returns:
            Room if found, None otherwise
        """
        return await self.find_by_id(room_id)


class GameRepository(ABC):
    """
    Interface for Game entity persistence.
    
    Note: In many cases, Games are persisted as part of the Room aggregate.
    This interface is for cases where Games need separate persistence.
    """
    
    @abstractmethod
    async def save(self, game: Game) -> None:
        """
        Save or update a game.
        
        Args:
            game: Game entity to persist
        """
        pass
    
    @abstractmethod
    async def find_by_room_id(self, room_id: str) -> Optional[Game]:
        """
        Find a game by its room ID.
        
        Args:
            room_id: Room ID associated with the game
            
        Returns:
            Game if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_active_games(self) -> List[Game]:
        """
        Find all active (not completed) games.
        
        Returns:
            List of active games
        """
        pass
    
    @abstractmethod
    async def find_completed_games_by_player(
        self, 
        player_name: str,
        limit: int = 10
    ) -> List[Game]:
        """
        Find completed games for a player.
        
        Args:
            player_name: Player to search for
            limit: Maximum number of games to return
            
        Returns:
            List of completed games
        """
        pass


class PlayerStatsRepository(ABC):
    """
    Interface for player statistics persistence.
    
    Provides long-term storage of player statistics
    across multiple games.
    """
    
    @abstractmethod
    async def save_stats(self, player_name: str, stats: Dict) -> None:
        """
        Save or update player statistics.
        
        Args:
            player_name: Player identifier
            stats: Statistics dictionary
        """
        pass
    
    @abstractmethod
    async def get_stats(self, player_name: str) -> Optional[Dict]:
        """
        Get statistics for a player.
        
        Args:
            player_name: Player identifier
            
        Returns:
            Statistics dictionary if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_leaderboard(
        self,
        stat_name: str = "total_score",
        limit: int = 10
    ) -> List[Dict]:
        """
        Get leaderboard for a specific statistic.
        
        Args:
            stat_name: Statistic to rank by
            limit: Number of entries to return
            
        Returns:
            List of player stats ordered by the specified stat
        """
        pass
    
    @abstractmethod
    async def increment_stat(
        self,
        player_name: str,
        stat_name: str,
        amount: int = 1
    ) -> None:
        """
        Increment a specific statistic.
        
        Args:
            player_name: Player identifier
            stat_name: Name of statistic to increment
            amount: Amount to increment by
        """
        pass