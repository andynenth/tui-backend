"""
In-memory implementation of GameRepository.

This provides a simple in-memory storage for games during development
and testing. In production, this would be replaced with a database-backed
implementation.
"""

from typing import Optional, List, Dict
import logging
from datetime import datetime
from copy import deepcopy

from application.interfaces import GameRepository
from domain.entities.game import Game

logger = logging.getLogger(__name__)


class InMemoryGameRepository(GameRepository):
    """
    In-memory implementation of the game repository.
    
    Stores games in memory using dictionaries for fast access.
    """
    
    def __init__(self):
        """Initialize empty storage."""
        self._games: Dict[str, Game] = {}  # room_id -> Game
        self._games_by_id: Dict[str, Game] = {}  # game_id -> Game (for compatibility)
        
    async def get_by_id(self, game_id: str) -> Optional[Game]:
        """
        Get a game by its ID.
        
        Args:
            game_id: The game identifier
            
        Returns:
            The game if found, None otherwise
        """
        # First try to find by game_id if we've assigned one
        game = self._games_by_id.get(game_id)
        if game:
            logger.debug(f"Retrieved game by ID {game_id}")
            return deepcopy(game)
        
        # Otherwise try to find by room_id (treating game_id as room_id)
        game = self._games.get(game_id)
        if game:
            logger.debug(f"Retrieved game by room ID {game_id}")
        return deepcopy(game) if game else None
    
    async def get_by_room_id(self, room_id: str) -> Optional[Game]:
        """
        Get the active game for a room.
        
        Args:
            room_id: The room identifier
            
        Returns:
            The active game if found, None otherwise
        """
        game = self._games.get(room_id)
        return deepcopy(game) if game else None
    
    async def save(self, game: Game) -> None:
        """
        Save or update a game.
        
        Args:
            game: The game to save
        """
        room_id = game.room_id
        
        # Store the game by room_id
        self._games[room_id] = deepcopy(game)
        
        # Also store by a synthetic game_id for compatibility
        game_id = f"game_{room_id}"
        self._games_by_id[game_id] = self._games[room_id]
        
        logger.debug(f"Saved game for room {room_id}")
    
    async def get_active_games(self) -> List[Game]:
        """
        Get all active games.
        
        Returns:
            List of active games
        """
        active_games = []
        for game in self._games.values():
            if not game.is_over:
                active_games.append(deepcopy(game))
        
        logger.debug(f"Found {len(active_games)} active games")
        return active_games
    
    async def get_games_by_player(self, player_id: str) -> List[Game]:
        """
        Get all games that include a specific player.
        
        Args:
            player_id: The player identifier
            
        Returns:
            List of games including the player
        """
        player_games = []
        for game in self._games.values():
            for player in game.players:
                if player.name == player_id:  # Using name as ID
                    player_games.append(deepcopy(game))
                    break
        
        logger.debug(f"Found {len(player_games)} games for player {player_id}")
        return player_games
    
    async def cleanup_old_games(self, before_date: datetime) -> int:
        """
        Remove games older than the specified date.
        
        Args:
            before_date: Remove games created before this date
            
        Returns:
            Number of games removed
        """
        to_remove = []
        
        for game_id, game in self._games.items():
            # Check if game is old and completed
            if game.is_over:
                # Would check game.created_at if it existed
                to_remove.append(game_id)
        
        # Remove old games
        for game_id in to_remove:
            if game_id in self._games:
                game = self._games.pop(game_id)
                # Also remove from games_by_id
                synthetic_id = f"game_{game_id}"
                if synthetic_id in self._games_by_id:
                    del self._games_by_id[synthetic_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old games")
        return len(to_remove)
    
    def snapshot(self) -> Dict[str, any]:
        """Create a snapshot of current state for rollback."""
        return {
            'games': deepcopy(self._games),
            'games_by_id': deepcopy(self._games_by_id)
        }
    
    def restore(self, snapshot: Dict[str, any]) -> None:
        """Restore from a snapshot."""
        self._games = snapshot['games']
        self._games_by_id = snapshot.get('games_by_id', {})