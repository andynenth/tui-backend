# backend/services/cached_game_recovery.py

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.engine.game import Game
from backend.engine.player import Player
from backend.services.cached_event_store import CachedEventStore
from backend.services.game_cache import CachedGameState

logger = logging.getLogger(__name__)


class CachedGameRecoveryService:
    """
    Game recovery service with cache integration.
    
    Phase 4 of database optimization - Provides fast game recovery
    by leveraging the cache for active games.
    
    Features:
    - Priority loading from cache for active games
    - Fallback to database for cache misses
    - Automatic cache population on recovery
    - Maintains compatibility with existing recovery interface
    """
    
    def __init__(self, cached_store: CachedEventStore):
        """
        Initialize recovery service.
        
        Args:
            cached_store: CachedEventStore instance
        """
        self.cached_store = cached_store
        self._recovery_count = 0
        self._cache_hits = 0
        self._db_recoveries = 0
        
        logger.info("CachedGameRecoveryService initialized")
    
    async def recover_game(self, room_id: str) -> Optional[Game]:
        """
        Recover a game from cache or database.
        
        Args:
            room_id: Room identifier
            
        Returns:
            Recovered Game instance or None
        """
        logger.info(f"Attempting to recover game for room {room_id}")
        self._recovery_count += 1
        
        # Get game state (from cache or database)
        state = await self.cached_store.get_game_state(room_id)
        if not state:
            logger.warning(f"No game state found for room {room_id}")
            return None
        
        # Check if this was a cache hit
        cache_metrics = self.cached_store.cache.get_metrics()
        if cache_metrics["hits"] > self._cache_hits:
            self._cache_hits = cache_metrics["hits"]
            logger.info(f"Recovered game from cache for room {room_id}")
        else:
            self._db_recoveries += 1
            logger.info(f"Recovered game from database for room {room_id}")
        
        # Reconstruct game from state
        game = await self._reconstruct_game(state)
        
        if game:
            logger.info(
                f"Successfully recovered game for room {room_id} "
                f"(round {game.round_number}, phase {game.current_phase})"
            )
        
        return game
    
    async def _reconstruct_game(self, state: Dict[str, Any]) -> Optional[Game]:
        """
        Reconstruct a Game instance from saved state.
        
        Args:
            state: Game state dictionary
            
        Returns:
            Reconstructed Game instance
        """
        try:
            # Create players
            players = []
            for player_data in state.get("players", []):
                player = Player(
                    name=player_data.get("player_name", player_data.get("name", "")),
                    is_bot=player_data.get("player_type", "ai") == "ai"
                )
                
                # Set player score if available
                if "scores" in state and player.name in state["scores"]:
                    player.score = state["scores"][player.name]
                
                players.append(player)
            
            if len(players) != 4:
                logger.error(f"Invalid player count: {len(players)}")
                return None
            
            # Create game
            game = Game(players)
            
            # Restore game state
            game.round_number = state.get("round_number", 1)
            game.current_phase = state.get("current_phase", "WAITING")
            
            # Restore phase-specific data
            if game.current_phase == "PREPARATION":
                await self._restore_preparation_phase(game, state)
            elif game.current_phase == "DECLARATION":
                await self._restore_declaration_phase(game, state)
            elif game.current_phase == "TURN":
                await self._restore_turn_phase(game, state)
            elif game.current_phase == "SCORING":
                await self._restore_scoring_phase(game, state)
            
            return game
            
        except Exception as e:
            logger.error(f"Failed to reconstruct game: {e}")
            return None
    
    async def _restore_preparation_phase(self, game: Game, state: Dict[str, Any]) -> None:
        """Restore preparation phase state."""
        phase_data = state.get("phase_data", {})
        
        # Restore dealt hands if available
        hands = phase_data.get("hands", {})
        for player in game.players:
            if player.name in hands:
                # Convert hand data to pieces
                # This would need the actual piece reconstruction logic
                pass
        
        # Set starter
        starter_name = phase_data.get("starter")
        if starter_name:
            for i, player in enumerate(game.players):
                if player.name == starter_name:
                    game.round_starter = i
                    break
    
    async def _restore_declaration_phase(self, game: Game, state: Dict[str, Any]) -> None:
        """Restore declaration phase state."""
        phase_data = state.get("phase_data", {})
        
        # Restore hands
        await self._restore_preparation_phase(game, state)
        
        # Restore declarations
        declarations = phase_data.get("declarations", {})
        game.declarations = declarations
        
        for player in game.players:
            if player.name in declarations:
                player.declared = declarations[player.name]
    
    async def _restore_turn_phase(self, game: Game, state: Dict[str, Any]) -> None:
        """Restore turn phase state."""
        phase_data = state.get("phase_data", {})
        
        # Restore declarations first
        await self._restore_declaration_phase(game, state)
        
        # Restore turn state
        game.turn_number = phase_data.get("turn_number", 1)
        game.current_player_index = phase_data.get("current_player_index", 0)
        
        # Restore captured piles
        captured = phase_data.get("captured_piles", {})
        for player in game.players:
            if player.name in captured:
                player.captured_piles = captured[player.name]
        
        # Restore turn history
        turn_history = phase_data.get("turn_history", [])
        if turn_history:
            game.turn_history_this_round = turn_history
    
    async def _restore_scoring_phase(self, game: Game, state: Dict[str, Any]) -> None:
        """Restore scoring phase state."""
        phase_data = state.get("phase_data", {})
        
        # Restore turn phase data first
        await self._restore_turn_phase(game, state)
        
        # Apply round scores
        round_scores = phase_data.get("round_scores", {})
        for player in game.players:
            if player.name in round_scores:
                # Score is already set from main state
                pass
    
    async def save_game_state(
        self,
        room_id: str,
        game: Game,
        phase_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save game state to cache.
        
        Args:
            room_id: Room identifier
            game: Game instance to save
            phase_data: Additional phase-specific data
        """
        # Build state from game
        state = {
            "room_id": room_id,
            "status": "active" if game.current_phase != "GAME_OVER" else "completed",
            "players": [
                {
                    "player_name": p.name,
                    "player_type": "ai" if p.is_bot else "human"
                }
                for p in game.players
            ],
            "round_number": game.round_number,
            "current_phase": game.current_phase,
            "phase_data": phase_data or {},
            "scores": {p.name: p.score for p in game.players},
            "started_at": datetime.now().isoformat()
        }
        
        # Add phase-specific data
        if game.current_phase == "DECLARATION":
            state["phase_data"]["declarations"] = getattr(game, "declarations", {})
        elif game.current_phase == "TURN":
            state["phase_data"]["turn_number"] = getattr(game, "turn_number", 1)
            state["phase_data"]["current_player_index"] = getattr(game, "current_player_index", 0)
            state["phase_data"]["captured_piles"] = {
                p.name: getattr(p, "captured_piles", 0) for p in game.players
            }
        
        # Save to cache
        await self.cached_store.cache.set(room_id, state)
        logger.debug(f"Saved game state to cache for room {room_id}")
    
    async def get_cached_game_state(self, room_id: str) -> Optional[CachedGameState]:
        """
        Get a CachedGameState wrapper for convenient updates.
        
        Args:
            room_id: Room identifier
            
        Returns:
            CachedGameState or None
        """
        return await self.cached_store.get_cached_game_state(room_id)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get recovery service metrics."""
        cache_hit_rate = self._cache_hits / self._recovery_count if self._recovery_count > 0 else 0.0
        
        return {
            "total_recoveries": self._recovery_count,
            "cache_hits": self._cache_hits,
            "db_recoveries": self._db_recoveries,
            "cache_hit_rate": cache_hit_rate
        }