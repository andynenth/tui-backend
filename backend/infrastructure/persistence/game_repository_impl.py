# infrastructure/persistence/game_repository_impl.py
"""
Implementation of the GameRepository interface.
"""

import logging
from typing import Optional, List, Dict, Any
import json
from datetime import datetime
import asyncio

from domain.interfaces.game_repository import GameRepository
from domain.entities.game import Game
from domain.entities.player import Player
from domain.entities.piece import Piece
from domain.value_objects.game_state import GamePhase

logger = logging.getLogger(__name__)


class InMemoryGameRepository(GameRepository):
    """
    In-memory implementation of GameRepository.
    
    This stores games in memory. In production, this would
    be replaced with a database implementation.
    """
    
    def __init__(self):
        self._games: Dict[str, Game] = {}
        self._game_counter = 0
        self._lock = asyncio.Lock()
    
    async def save(self, game: Game) -> None:
        """
        Save or update a game.
        
        Args:
            game: The game to save
        """
        async with self._lock:
            if not hasattr(game, 'id') or not game.id:
                # Generate new ID
                self._game_counter += 1
                game.id = f"game_{self._game_counter}"
            
            # Store game
            self._games[game.id] = game
            
            logger.debug(f"Saved game {game.id}")
    
    async def get(self, game_id: str) -> Optional[Game]:
        """
        Retrieve a game by ID.
        
        Args:
            game_id: The game ID
            
        Returns:
            Game if found, None otherwise
        """
        return self._games.get(game_id)
    
    async def get_by_room_id(self, room_id: str) -> Optional[Game]:
        """
        Retrieve a game by room ID.
        
        This is a simple implementation that searches all games.
        In production, use an index.
        
        Args:
            room_id: The room ID
            
        Returns:
            Game if found, None otherwise
        """
        # In production, maintain a room_id -> game_id index
        for game in self._games.values():
            if hasattr(game, 'room_id') and game.room_id == room_id:
                return game
        return None
    
    async def delete(self, game_id: str) -> bool:
        """
        Delete a game.
        
        Args:
            game_id: The game ID
            
        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if game_id in self._games:
                del self._games[game_id]
                logger.debug(f"Deleted game {game_id}")
                return True
            return False
    
    async def list_active_games(self) -> List[Game]:
        """
        List all active (not finished) games.
        
        Returns:
            List of active games
        """
        return [
            game for game in self._games.values()
            if not game.is_finished()
        ]
    
    async def list_games_by_player(self, player_name: str) -> List[Game]:
        """
        List all games containing a specific player.
        
        Args:
            player_name: The player name
            
        Returns:
            List of games containing the player
        """
        games = []
        for game in self._games.values():
            if any(p.name == player_name for p in game.players):
                games.append(game)
        return games
    
    async def create(self, game: Game) -> str:
        """
        Create a new game and return its ID.
        
        Args:
            game: The game to create
            
        Returns:
            The generated game ID
        """
        async with self._lock:
            self._game_counter += 1
            game_id = f"game_{self._game_counter}"
            game.id = game_id
            self._games[game_id] = game
            
            logger.info(f"Created game {game_id}")
            
            return game_id
    
    async def update_phase(
        self,
        game_id: str,
        new_phase: GamePhase
    ) -> bool:
        """
        Update game phase.
        
        Args:
            game_id: The game ID
            new_phase: The new phase
            
        Returns:
            True if updated
        """
        game = await self.get(game_id)
        if game:
            game.transition_to_phase(new_phase)
            return True
        return False
    
    async def exists(self, game_id: str) -> bool:
        """
        Check if a game exists.
        
        Args:
            game_id: The game ID
            
        Returns:
            True if game exists
        """
        return game_id in self._games
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        active_games = sum(1 for g in self._games.values() if not g.is_finished())
        finished_games = len(self._games) - active_games
        
        return {
            "total_games": len(self._games),
            "active_games": active_games,
            "finished_games": finished_games,
            "game_counter": self._game_counter
        }


class FileBasedGameRepository(GameRepository):
    """
    File-based implementation of GameRepository.
    
    This stores games as JSON files. Useful for development
    and testing with persistence.
    """
    
    def __init__(self, storage_path: str = "./game_data"):
        self._storage_path = storage_path
        self._lock = asyncio.Lock()
        
        # Ensure storage directory exists
        import os
        os.makedirs(storage_path, exist_ok=True)
    
    def _get_game_path(self, game_id: str) -> str:
        """Get file path for a game."""
        return f"{self._storage_path}/{game_id}.json"
    
    def _serialize_game(self, game: Game) -> Dict[str, Any]:
        """Serialize game to JSON-compatible dict."""
        return {
            "id": game.id,
            "room_id": getattr(game, 'room_id', None),
            "round_number": game.round_number,
            "turn_number": game.turn_number,
            "current_phase": game.current_phase.value,
            "max_score": game.max_score,
            "players": [
                {
                    "name": p.name,
                    "total_score": p.total_score,
                    "declared_piles": p.declared_piles,
                    "pile_count": p.pile_count,
                    "pieces": [
                        {"value": piece.value, "suit": piece.suit}
                        for piece in p.pieces
                    ],
                    "is_connected": p.is_connected
                }
                for p in game.players
            ],
            "created_at": datetime.utcnow().isoformat(),
            "is_finished": game.is_finished()
        }
    
    def _deserialize_game(self, data: Dict[str, Any]) -> Game:
        """Deserialize game from JSON dict."""
        # Create players
        players = []
        for player_data in data["players"]:
            player = Player(player_data["name"])
            player._total_score = player_data["total_score"]
            player._declared_piles = player_data.get("declared_piles")
            player._pile_count = player_data["pile_count"]
            player._pieces = [
                Piece(p["value"], p["suit"])
                for p in player_data["pieces"]
            ]
            player._is_connected = player_data.get("is_connected", True)
            players.append(player)
        
        # Create game
        game = Game(players, max_score=data["max_score"])
        game.id = data["id"]
        game._round_number = data["round_number"]
        game._turn_number = data["turn_number"]
        game._current_phase = GamePhase(data["current_phase"])
        
        if data.get("room_id"):
            game.room_id = data["room_id"]
        
        return game
    
    async def save(self, game: Game) -> None:
        """Save game to file."""
        async with self._lock:
            if not hasattr(game, 'id') or not game.id:
                # Generate ID
                import uuid
                game.id = f"game_{uuid.uuid4().hex[:8]}"
            
            # Serialize and save
            game_data = self._serialize_game(game)
            file_path = self._get_game_path(game.id)
            
            with open(file_path, 'w') as f:
                json.dump(game_data, f, indent=2)
            
            logger.debug(f"Saved game {game.id} to {file_path}")
    
    async def get(self, game_id: str) -> Optional[Game]:
        """Load game from file."""
        file_path = self._get_game_path(game_id)
        
        try:
            with open(file_path, 'r') as f:
                game_data = json.load(f)
            
            return self._deserialize_game(game_data)
        except FileNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to load game {game_id}: {str(e)}")
            return None
    
    async def delete(self, game_id: str) -> bool:
        """Delete game file."""
        async with self._lock:
            file_path = self._get_game_path(game_id)
            
            try:
                import os
                os.remove(file_path)
                logger.debug(f"Deleted game {game_id}")
                return True
            except FileNotFoundError:
                return False
    
    # Implement other required methods similar to InMemoryGameRepository
    # but with file operations...