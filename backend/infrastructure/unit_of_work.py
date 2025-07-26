"""
Infrastructure implementation of Unit of Work pattern.

This module provides the concrete implementation of the UnitOfWork
interface defined in the application layer.
"""

from typing import Optional
import logging
from contextlib import asynccontextmanager

from application.interfaces import UnitOfWork as IUnitOfWork
from infrastructure.repositories import (
    InMemoryPlayerStatsRepository,
    InMemoryConnectionRepository,
    InMemoryMessageQueueRepository
)
from infrastructure.repositories.application_room_repository import ApplicationRoomRepository
from infrastructure.repositories.application_game_repository import ApplicationGameRepository

logger = logging.getLogger(__name__)


class InMemoryUnitOfWork(IUnitOfWork):
    """
    In-memory implementation of Unit of Work.
    
    This implementation uses in-memory repositories and simulates
    transactional behavior. In production, this would be replaced
    with database-backed repositories and real transactions.
    """
    
    def __init__(self):
        """Initialize the unit of work with repositories."""
        self._rooms = ApplicationRoomRepository()
        self._games = ApplicationGameRepository()
        self._player_stats = InMemoryPlayerStatsRepository()
        self._connections = InMemoryConnectionRepository()
        self._message_queues = InMemoryMessageQueueRepository()
        self._in_transaction = False
        self._rollback_data = None
        
    @property
    def rooms(self):
        """Get the room repository."""
        return self._rooms
        
    @property
    def games(self):
        """Get the game repository."""
        return self._games
        
    @property
    def player_stats(self):
        """Get the player stats repository."""
        return self._player_stats
    
    @property
    def connections(self):
        """Get the connection repository."""
        return self._connections
    
    @property
    def message_queues(self):
        """Get the message queue repository."""
        return self._message_queues
    
    async def __aenter__(self):
        """Begin a unit of work context."""
        self._in_transaction = True
        # Save current state for potential rollback
        self._rollback_data = {
            'rooms': self._rooms.snapshot(),
            'games': self._games.snapshot(),
            'player_stats': self._player_stats.snapshot(),
            'connections': self._connections.snapshot(),
            'message_queues': self._message_queues.snapshot()
        }
        logger.debug("Unit of work transaction started")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End a unit of work context."""
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
        self._in_transaction = False
        self._rollback_data = None
        
    async def commit(self):
        """Commit the transaction."""
        # In-memory implementation doesn't need explicit commit
        logger.debug("Unit of work committed")
        
    async def rollback(self):
        """Rollback the transaction."""
        if self._rollback_data:
            # Restore previous state
            self._rooms.restore(self._rollback_data['rooms'])
            self._games.restore(self._rollback_data['games'])
            self._player_stats.restore(self._rollback_data['player_stats'])
            self._connections.restore(self._rollback_data['connections'])
            self._message_queues.restore(self._rollback_data['message_queues'])
            logger.debug("Unit of work rolled back")
    
    async def savepoint(self, name: str) -> None:
        """Create a savepoint within the transaction."""
        # In-memory implementation doesn't support savepoints
        logger.debug(f"Savepoint '{name}' created (no-op in memory)")
    
    async def rollback_to_savepoint(self, name: str) -> None:
        """Rollback to a specific savepoint."""
        # In-memory implementation doesn't support savepoints
        logger.debug(f"Rollback to savepoint '{name}' (no-op in memory)")


class DatabaseUnitOfWork(IUnitOfWork):
    """
    Database-backed implementation of Unit of Work.
    
    This is a placeholder for future database integration.
    Would use SQLAlchemy or similar ORM for real implementation.
    """
    
    def __init__(self, session_factory):
        """
        Initialize with database session factory.
        
        Args:
            session_factory: Factory function to create database sessions
        """
        self._session_factory = session_factory
        self._session = None
        self._rooms = None
        self._games = None
        self._player_stats = None
        self._connections = None
        self._message_queues = None
        
    @property
    def rooms(self):
        """Get the room repository."""
        if not self._rooms:
            raise RuntimeError("Unit of work not started")
        return self._rooms
        
    @property
    def games(self):
        """Get the game repository."""
        if not self._games:
            raise RuntimeError("Unit of work not started")
        return self._games
        
    @property
    def player_stats(self):
        """Get the player stats repository."""
        if not self._player_stats:
            raise RuntimeError("Unit of work not started")
        return self._player_stats
    
    @property
    def connections(self):
        """Get the connection repository."""
        if not self._connections:
            raise RuntimeError("Unit of work not started")
        return self._connections
    
    @property
    def message_queues(self):
        """Get the message queue repository."""
        if not self._message_queues:
            raise RuntimeError("Unit of work not started")
        return self._message_queues
    
    async def __aenter__(self):
        """Begin a database transaction."""
        # Would create database session and repositories here
        raise NotImplementedError("Database UoW not yet implemented")
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End the database transaction."""
        # Would handle commit/rollback here
        raise NotImplementedError("Database UoW not yet implemented")
        
    async def commit(self):
        """Commit the database transaction."""
        raise NotImplementedError("Database UoW not yet implemented")
        
    async def rollback(self):
        """Rollback the database transaction."""
        raise NotImplementedError("Database UoW not yet implemented")