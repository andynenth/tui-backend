# domain/interfaces/game_repository.py
"""
Repository interface for game persistence.
This interface belongs to the domain but is implemented by infrastructure.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.game import Game


class GameRepository(ABC):
    """
    Interface for game persistence operations.
    
    This follows the Repository pattern from Domain-Driven Design.
    The interface is defined in the domain layer but implemented
    in the infrastructure layer, allowing the domain to remain
    independent of persistence concerns.
    """
    
    @abstractmethod
    async def save(self, game: Game) -> None:
        """
        Persist a game entity.
        
        Args:
            game: The game to save
            
        Raises:
            RepositoryException: If save fails
        """
        pass
    
    @abstractmethod
    async def get(self, game_id: str) -> Optional[Game]:
        """
        Retrieve a game by ID.
        
        Args:
            game_id: Unique identifier of the game
            
        Returns:
            Game if found, None otherwise
            
        Raises:
            RepositoryException: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_by_room_id(self, room_id: str) -> Optional[Game]:
        """
        Retrieve a game by room ID.
        
        Args:
            room_id: Room identifier associated with the game
            
        Returns:
            Game if found, None otherwise
            
        Raises:
            RepositoryException: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def list_active_games(self) -> List[Game]:
        """
        List all active (not ended) games.
        
        Returns:
            List of active games
            
        Raises:
            RepositoryException: If listing fails
        """
        pass
    
    @abstractmethod
    async def delete(self, game_id: str) -> bool:
        """
        Delete a game.
        
        Args:
            game_id: ID of game to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            RepositoryException: If deletion fails
        """
        pass
    
    @abstractmethod
    async def exists(self, game_id: str) -> bool:
        """
        Check if a game exists.
        
        Args:
            game_id: ID to check
            
        Returns:
            True if exists, False otherwise
            
        Raises:
            RepositoryException: If check fails
        """
        pass


class RepositoryException(Exception):
    """Base exception for repository errors."""
    pass


class GameNotFoundException(RepositoryException):
    """Raised when a requested game is not found."""
    def __init__(self, game_id: str):
        super().__init__(f"Game not found: {game_id}")
        self.game_id = game_id


class DuplicateGameException(RepositoryException):
    """Raised when attempting to create a game with duplicate ID."""
    def __init__(self, game_id: str):
        super().__init__(f"Game already exists: {game_id}")
        self.game_id = game_id