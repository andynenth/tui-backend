"""
Repository interfaces for the application layer.

These interfaces define how the application layer accesses domain aggregates.
The actual implementations will be in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from domain.entities.room import Room
from domain.entities.game import Game
from domain.entities.connection import PlayerConnection
from domain.entities.message_queue import PlayerQueue
from domain.value_objects import PlayerId, RoomId


class RoomRepository(ABC):
    """Repository for Room aggregates."""
    
    @abstractmethod
    async def get_by_id(self, room_id: str) -> Optional[Room]:
        """
        Retrieve a room by its ID.
        
        Args:
            room_id: The room's unique identifier
            
        Returns:
            The Room if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_code(self, room_code: str) -> Optional[Room]:
        """
        Retrieve a room by its join code.
        
        Args:
            room_code: The room's join code
            
        Returns:
            The Room if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def save(self, room: Room) -> None:
        """
        Save a room to the repository.
        
        Args:
            room: The room to save
        """
        pass
    
    @abstractmethod
    async def delete(self, room_id: str) -> None:
        """
        Delete a room from the repository.
        
        Args:
            room_id: The room's unique identifier
        """
        pass
    
    @abstractmethod
    async def list_active(self, limit: int = 100) -> List[Room]:
        """
        List active rooms.
        
        Args:
            limit: Maximum number of rooms to return
            
        Returns:
            List of active rooms
        """
        pass
    
    @abstractmethod
    async def find_by_player(self, player_id: str) -> Optional[Room]:
        """
        Find the room a player is currently in.
        
        Args:
            player_id: The player's unique identifier
            
        Returns:
            The Room if found, None otherwise
        """
        pass


class GameRepository(ABC):
    """Repository for Game entities."""
    
    @abstractmethod
    async def get_by_id(self, game_id: str) -> Optional[Game]:
        """
        Retrieve a game by its ID.
        
        Args:
            game_id: The game's unique identifier
            
        Returns:
            The Game if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def save(self, game: Game) -> None:
        """
        Save a game to the repository.
        
        Args:
            game: The game to save
        """
        pass
    
    @abstractmethod
    async def get_by_room_id(self, room_id: str) -> Optional[Game]:
        """
        Get the active game for a room.
        
        Args:
            room_id: The room's unique identifier
            
        Returns:
            The active Game if found, None otherwise
        """
        pass


class PlayerStatsRepository(ABC):
    """Repository for player statistics."""
    
    @abstractmethod
    async def get_stats(self, player_id: str) -> Dict[str, Any]:
        """
        Get statistics for a player.
        
        Args:
            player_id: The player's unique identifier
            
        Returns:
            Dictionary of player statistics
        """
        pass
    
    @abstractmethod
    async def update_stats(self, player_id: str, stats: Dict[str, Any]) -> None:
        """
        Update statistics for a player.
        
        Args:
            player_id: The player's unique identifier
            stats: Statistics to update
        """
        pass
    
    @abstractmethod
    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top players by score.
        
        Args:
            limit: Number of players to return
            
        Returns:
            List of player statistics
        """
        pass


class ConnectionRepository(ABC):
    """Repository for player connections."""
    
    @abstractmethod
    async def get(self, room_id: str, player_name: str) -> Optional[PlayerConnection]:
        """
        Get connection info for a player.
        
        Args:
            room_id: The room ID
            player_name: The player name
            
        Returns:
            PlayerConnection if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def save(self, connection: PlayerConnection) -> None:
        """
        Save connection info.
        
        Args:
            connection: The connection to save
        """
        pass
    
    @abstractmethod
    async def delete(self, room_id: str, player_name: str) -> None:
        """
        Delete connection info.
        
        Args:
            room_id: The room ID
            player_name: The player name
        """
        pass
    
    @abstractmethod
    async def list_by_room(self, room_id: str) -> List[PlayerConnection]:
        """
        List all connections for a room.
        
        Args:
            room_id: The room ID
            
        Returns:
            List of connections
        """
        pass


class MessageQueueRepository(ABC):
    """Repository for message queues."""
    
    @abstractmethod
    async def create_queue(self, room_id: str, player_name: str) -> None:
        """
        Create a message queue for a player.
        
        Args:
            room_id: The room ID
            player_name: The player name
        """
        pass
    
    @abstractmethod
    async def get_queue(self, room_id: str, player_name: str) -> Optional[PlayerQueue]:
        """
        Get message queue for a player.
        
        Args:
            room_id: The room ID
            player_name: The player name
            
        Returns:
            PlayerQueue if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def save_queue(self, queue: PlayerQueue) -> None:
        """
        Save a message queue.
        
        Args:
            queue: The queue to save
        """
        pass
    
    @abstractmethod
    async def clear_queue(self, room_id: str, player_name: str) -> None:
        """
        Clear and delete a message queue.
        
        Args:
            room_id: The room ID
            player_name: The player name
        """
        pass
    
    @abstractmethod
    async def clear_room_queues(self, room_id: str) -> None:
        """
        Clear all queues for a room.
        
        Args:
            room_id: The room ID
        """
        pass