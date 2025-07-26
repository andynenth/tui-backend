"""
Unit of Work interface for transaction management.

The Unit of Work pattern ensures that all operations within a use case
are atomic - they either all succeed or all fail together.
"""

from abc import ABC, abstractmethod
from typing import Optional
from .repositories import (
    RoomRepository, 
    GameRepository, 
    PlayerStatsRepository,
    ConnectionRepository,
    MessageQueueRepository
)


class UnitOfWork(ABC):
    """
    Manages a business transaction.
    
    The unit of work tracks all changes made during a business
    operation and ensures they are all committed or rolled back
    together.
    """
    
    # Repository properties
    rooms: RoomRepository
    games: GameRepository
    player_stats: PlayerStatsRepository
    connections: ConnectionRepository
    message_queues: MessageQueueRepository
    
    @abstractmethod
    async def __aenter__(self):
        """Begin the unit of work."""
        return self
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Complete or rollback the unit of work.
        
        If an exception occurred, rollback all changes.
        Otherwise, commit all changes.
        """
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
    
    @abstractmethod
    async def commit(self) -> None:
        """
        Commit all changes in this unit of work.
        
        Makes all changes permanent and visible to other transactions.
        """
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """
        Rollback all changes in this unit of work.
        
        Discards all changes made during this transaction.
        """
        pass
    
    @abstractmethod
    async def savepoint(self, name: str) -> None:
        """
        Create a savepoint within the transaction.
        
        Args:
            name: Name for the savepoint
        """
        pass
    
    @abstractmethod
    async def rollback_to_savepoint(self, name: str) -> None:
        """
        Rollback to a specific savepoint.
        
        Args:
            name: Name of the savepoint to rollback to
        """
        pass