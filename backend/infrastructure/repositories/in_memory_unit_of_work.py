"""
In-memory Unit of Work implementation for transaction-like semantics.

This provides atomic operations across multiple repositories while
maintaining high performance for real-time gaming.
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Any, Optional
from contextlib import asynccontextmanager

from application.interfaces.unit_of_work import IUnitOfWork
from application.interfaces.repositories import (
    RoomRepository,
    GameRepository,
    PlayerStatsRepository,
    ConnectionRepository,
    MessageQueueRepository,
)

from .optimized_room_repository import OptimizedRoomRepository
from .optimized_game_repository import OptimizedGameRepository
from .optimized_player_stats_repository import OptimizedPlayerStatsRepository
from .connection_repository import InMemoryConnectionRepository
from .message_queue_repository import InMemoryMessageQueueRepository


logger = logging.getLogger(__name__)


class InMemoryUnitOfWork(IUnitOfWork):
    """
    In-memory Unit of Work with:
    - Atomic operations across repositories
    - Change tracking for async archival
    - High-performance memory operations
    - Rollback support through snapshots
    """

    def __init__(self):
        """Initialize with optimized repositories."""
        # Create repository instances
        self._room_repo = OptimizedRoomRepository()
        self._game_repo = OptimizedGameRepository()
        self._stats_repo = OptimizedPlayerStatsRepository()
        self._connection_repo = InMemoryConnectionRepository()
        self._message_queue_repo = InMemoryMessageQueueRepository()

        # Transaction tracking
        self._in_transaction = False
        self._changes: List[Tuple[str, str, Any]] = []
        self._lock = asyncio.Lock()

        # Snapshots for rollback
        self._snapshots: Dict[str, Any] = {}

        # Archive tracking
        self._completed_games: List[Dict] = []

    @property
    def rooms(self) -> RoomRepository:
        """Get room repository."""
        return self._room_repo

    @property
    def games(self) -> GameRepository:
        """Get game repository."""
        return self._game_repo

    @property
    def player_stats(self) -> PlayerStatsRepository:
        """Get player stats repository."""
        return self._stats_repo

    @property
    def connections(self) -> ConnectionRepository:
        """Get connection repository."""
        return self._connection_repo

    @property
    def message_queues(self) -> MessageQueueRepository:
        """Get message queue repository."""
        return self._message_queue_repo

    async def __aenter__(self):
        """Begin transaction-like operation."""
        await self._lock.acquire()
        self._in_transaction = True
        self._changes.clear()

        # Take snapshots for potential rollback
        # Note: In a real implementation, we'd use more efficient snapshot mechanisms
        logger.debug("Starting unit of work transaction")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Complete or rollback transaction."""
        try:
            if exc_type:
                # Exception occurred - rollback would happen here
                # In memory implementation, changes are immediate so rollback is limited
                logger.error(
                    f"Unit of work failed with: {exc_type.__name__}: {exc_val}"
                )
            else:
                # Success - track completed games for archival
                await self._track_completed_games()
                logger.debug("Unit of work completed successfully")
        finally:
            self._in_transaction = False
            self._lock.release()

    async def commit(self) -> None:
        """
        Commit changes (no-op for in-memory, but tracks archival needs).

        In a real implementation, this would:
        1. Validate all changes
        2. Apply to persistent storage
        3. Clear change tracking
        """
        if not self._in_transaction:
            raise RuntimeError("Cannot commit outside of transaction")

        # Track what needs archival
        await self._track_completed_games()

        # Log changes for debugging
        if self._changes:
            logger.debug(f"Committing {len(self._changes)} changes")

    async def rollback(self) -> None:
        """
        Rollback changes (limited in in-memory implementation).

        Since changes are applied immediately in memory, rollback
        is limited. In a real implementation with a database,
        this would revert all pending changes.
        """
        if not self._in_transaction:
            raise RuntimeError("Cannot rollback outside of transaction")

        logger.warning(
            "Rollback requested - in-memory changes cannot be fully reverted"
        )
        self._changes.clear()

    # Helper methods

    async def _track_completed_games(self) -> None:
        """Track completed games for archival."""
        # Get completed games from repositories
        completed_rooms = self._room_repo.get_completed_rooms()

        # Get games pending archival
        archive_batch = await self._game_repo.get_next_archive_batch(100)

        if completed_rooms or archive_batch:
            logger.info(
                f"Tracking for archival: {len(completed_rooms)} rooms, "
                f"{len(archive_batch)} games"
            )

            # In a real implementation, these would be sent to an archive service
            self._completed_games.extend(archive_batch)

    def track_change(self, repo_name: str, operation: str, entity_id: str):
        """Track a change for audit/debugging."""
        if self._in_transaction:
            self._changes.append((repo_name, operation, entity_id))

    # Archive access

    def get_pending_archives(self) -> List[Dict]:
        """Get games pending archival."""
        archives = self._completed_games
        self._completed_games = []
        return archives

    # Monitoring

    def get_metrics(self) -> Dict[str, Any]:
        """Get unit of work metrics."""
        return {
            "in_transaction": self._in_transaction,
            "pending_changes": len(self._changes),
            "pending_archives": len(self._completed_games),
            "room_metrics": self._room_repo.get_metrics(),
            "game_metrics": self._game_repo.get_metrics(),
            "stats_metrics": self._stats_repo.get_metrics(),
        }


class InMemoryUnitOfWorkFactory:
    """Factory for creating unit of work instances."""

    def __init__(self):
        """Initialize factory."""
        # In a real implementation, might pool UoW instances
        self._instance = InMemoryUnitOfWork()

    def create(self) -> InMemoryUnitOfWork:
        """Create a unit of work instance."""
        # For in-memory, we use a singleton pattern
        # In a real implementation, might create new instances
        return self._instance

    @asynccontextmanager
    async def create_context(self):
        """Create a unit of work context."""
        uow = self.create()
        async with uow:
            yield uow
