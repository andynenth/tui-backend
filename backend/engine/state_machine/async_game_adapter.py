# backend/engine/state_machine/async_game_adapter.py
"""
Adapter to help state machine work with both sync and async Game classes.
Provides unified interface during migration from sync to async.
"""

import asyncio
import logging
from typing import Union, Dict, Any, List, Optional

from backend.engine.game import Game
from backend.engine.async_game import AsyncGame

logger = logging.getLogger(__name__)


class AsyncGameAdapter:
    """
    Adapter that provides async interface for both sync and async Game classes.
    This allows the state machine to use async/await regardless of the underlying game type.
    """
    
    def __init__(self, game: Union[Game, AsyncGame]):
        """
        Initialize adapter with either sync or async game.
        
        Args:
            game: Either a sync Game or AsyncGame instance
        """
        self.game = game
        self.is_async = isinstance(game, AsyncGame)
        
        logger.info(
            f"AsyncGameAdapter initialized with {'async' if self.is_async else 'sync'} game"
        )
    
    # Direct property access (no need for async)
    def __getattr__(self, name):
        """Forward attribute access to underlying game."""
        return getattr(self.game, name)
    
    async def deal_pieces(self) -> Optional[Dict[str, Any]]:
        """
        Deal pieces using appropriate method based on game type.
        
        Returns:
            Dict with deal result for async game, None for sync game
        """
        if self.is_async:
            return await self.game.deal_pieces()
        else:
            # Run sync method without blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.game.deal_pieces)
            # Sync version doesn't return anything, create a basic result
            return {
                "success": True,
                "sync": True,
                "message": "Pieces dealt (sync)"
            }
    
    async def play_turn(self, player_name: str, piece_indexes: List[int]) -> Dict[str, Any]:
        """
        Process a player's turn using appropriate method.
        
        Args:
            player_name: Name of the player
            piece_indexes: Indexes of pieces to play
            
        Returns:
            Dict with turn result
        """
        if self.is_async:
            return await self.game.play_turn(player_name, piece_indexes)
        else:
            # Run sync method without blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                self.game.play_turn, 
                player_name, 
                piece_indexes
            )
    
    async def calculate_scores(self) -> Dict[str, int]:
        """
        Calculate scores using appropriate method.
        
        Returns:
            Dict mapping player names to scores
        """
        if self.is_async:
            return await self.game.calculate_scores()
        else:
            # Sync game calculates scores inline during play_turn
            # Extract current round scores
            round_scores = getattr(self.game, 'round_scores', {})
            if not round_scores:
                # Calculate manually if needed
                from backend.engine.scoring import calculate_round_scores
                round_scores = calculate_round_scores(
                    self.game.players,
                    self.game.pile_counts,
                    self.game.redeal_multiplier
                )
            return round_scores
    
    async def start_new_round(self) -> Dict[str, Any]:
        """
        Start a new round using appropriate method.
        
        Returns:
            Dict with new round information
        """
        if self.is_async:
            return await self.game.start_new_round()
        else:
            # Sync game doesn't have start_new_round, simulate it
            loop = asyncio.get_event_loop()
            
            # Reset round state
            self.game.round_number += 1
            self.game.redeal_multiplier = 1
            self.game.current_turn_plays = []
            self.game.required_piece_count = None
            self.game.turn_order = []
            self.game.last_turn_winner = None
            self.game.turn_number = 0
            self.game.player_declarations = {}
            self.game.pile_counts = {p.name: 0 for p in self.game.players}
            self.game.round_scores = {}
            
            # Reset players
            for player in self.game.players:
                player.reset_for_next_round()
            
            # Deal new pieces
            await loop.run_in_executor(None, self.game.deal_pieces)
            
            return {
                "success": True,
                "sync": True,
                "round_number": self.game.round_number,
                "message": "New round started (sync)"
            }
    
    async def check_game_over(self) -> Optional[Dict[str, Any]]:
        """
        Check if game is over using appropriate method.
        
        Returns:
            Dict with game over info if game ended, None otherwise
        """
        if self.is_async:
            return await self.game.check_game_over()
        else:
            # Use sync game's _is_game_over method
            if not self.game._is_game_over():
                return None
            
            from backend.engine.win_conditions import get_winners
            winners = get_winners(self.game)
            
            return {
                "game_over": True,
                "sync": True,
                "winners": [w.name for w in winners],
                "final_scores": {p.name: p.score for p in self.game.players},
                "rounds_played": self.game.round_number
            }
    
    async def execute_redeal_for_player(self, player_name: str) -> Dict[str, Any]:
        """
        Execute redeal for a player using appropriate method.
        
        Args:
            player_name: Name of the player
            
        Returns:
            Dict with redeal result
        """
        if self.is_async:
            return await self.game.execute_redeal_for_player(player_name)
        else:
            # Run sync method without blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.game.execute_redeal_for_player,
                player_name
            )
    
    async def record_player_declaration(
        self, 
        player_name: str, 
        declaration: int
    ) -> Dict[str, Any]:
        """
        Record player declaration using appropriate method.
        
        Args:
            player_name: Name of the player
            declaration: Number of piles declared
            
        Returns:
            Dict with declaration result
        """
        if self.is_async:
            return await self.game.record_player_declaration(player_name, declaration)
        else:
            # Run sync method without blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self.game.record_player_declaration,
                player_name,
                declaration
            )
    
    async def get_game_state(self) -> Dict[str, Any]:
        """
        Get game state using appropriate method.
        
        Returns:
            Dict with game state
        """
        if self.is_async:
            return await self.game.get_game_state()
        else:
            # Build state dict from sync game
            return {
                "round_number": self.game.round_number,
                "turn_number": self.game.turn_number,
                "current_phase": self.game.current_phase,
                "redeal_multiplier": self.game.redeal_multiplier,
                "players": {
                    p.name: {
                        "score": p.score,
                        "declared": p.declared,
                        "hand_count": len(p.hand),
                        "pile_count": self.game.pile_counts.get(p.name, 0),
                        "is_bot": p.is_bot
                    }
                    for p in self.game.players
                },
                "current_player": (
                    self.game.current_player.name 
                    if self.game.current_player else None
                ),
                "game_over": self.game._is_game_over(),
                "sync": True
            }
    
    # Helper method to check game type
    def is_async_game(self) -> bool:
        """Check if underlying game is async."""
        return self.is_async


# Utility function for easy migration
def wrap_game_for_async(game: Union[Game, AsyncGame]) -> AsyncGameAdapter:
    """
    Wrap a game instance for async usage in state machine.
    
    Args:
        game: Either sync or async game instance
        
    Returns:
        AsyncGameAdapter wrapping the game
    """
    return AsyncGameAdapter(game)


# Example usage in state machine
async def example_state_machine_usage(game: Union[Game, AsyncGame]):
    """Example showing how to use the adapter in state machine."""
    # Wrap the game
    game_adapter = wrap_game_for_async(game)
    
    # Now all operations are async regardless of game type
    await game_adapter.deal_pieces()
    
    # Can still access properties directly
    players = game_adapter.players
    round_number = game_adapter.round_number
    
    # Process turns asynchronously
    result = await game_adapter.play_turn("Player1", [0, 1, 2])
    
    # Check game over
    game_over = await game_adapter.check_game_over()
    if game_over:
        print(f"Game ended! Winners: {game_over['winners']}")