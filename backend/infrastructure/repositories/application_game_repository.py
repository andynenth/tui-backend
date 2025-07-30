"""
Application layer game repository implementation.

This wraps the domain repository to provide the application layer interface.
"""

from typing import Optional, List, Dict
from copy import deepcopy

from application.interfaces.repositories import GameRepository as IGameRepository
from domain.entities.game import Game
from .in_memory_game_repository import InMemoryGameRepository


class ApplicationGameRepository(IGameRepository):
    """
    Adapter that implements the application repository interface
    using the domain repository.
    """

    def __init__(self):
        self._domain_repo = InMemoryGameRepository()
        self._snapshot_data = None

    async def get_by_id(self, game_id: str) -> Optional[Game]:
        """Get game by ID."""
        return await self._domain_repo.get_by_id(game_id)

    async def save(self, game: Game) -> None:
        """Save a game."""
        await self._domain_repo.save(game)

    async def get_by_room_id(self, room_id: str) -> Optional[Game]:
        """Get active game for a room."""
        return await self._domain_repo.get_by_room_id(room_id)

    def snapshot(self) -> Dict:
        """Create a snapshot for rollback."""
        return self._domain_repo.snapshot()

    def restore(self, snapshot: Dict) -> None:
        """Restore from snapshot."""
        self._domain_repo.restore(snapshot)
