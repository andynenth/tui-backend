# backend/engine/async_game.py
"""
Async implementation of Game for Phase 3 migration.
This will eventually replace the sync Game class.
"""

import asyncio
import random
import logging
import time
from typing import List, Dict, Optional, Any
from datetime import datetime

from .game import Game
from .piece import Piece
from .player import Player
from .rules import get_play_type, get_valid_declares, is_valid_play
from .scoring import calculate_round_scores
from .turn_resolution import TurnPlay, resolve_turn
from .win_conditions import WinConditionType, get_winners, is_game_over

logger = logging.getLogger(__name__)


class AsyncGame(Game):
    """
    Async version of Game class.
    Inherits from Game to maintain compatibility while adding async methods.
    """

    def __init__(
        self,
        players,
        interface=None,
        win_condition_type=WinConditionType.FIRST_TO_REACH_50,
    ):
        """Initialize AsyncGame with same parameters as Game."""
        super().__init__(players, interface, win_condition_type)

        # Async-specific attributes
        self._game_lock = asyncio.Lock()  # For game state modifications
        self._deal_lock = asyncio.Lock()  # For dealing operations
        self._turn_lock = asyncio.Lock()  # For turn operations
        self._score_lock = asyncio.Lock()  # For score calculations

        # Statistics
        self._async_operations = {"deals": 0, "turns": 0, "scores": 0, "rounds": 0}

        logger.info(f"AsyncGame initialized with {len(players)} players")

    async def deal_pieces(self) -> Dict[str, Any]:
        """
        Async version of deal_pieces.
        Shuffles and deals 32 pieces evenly among the 4 players.

        Returns:
            Dict with deal information

        Future: Will persist deal to database
        """
        async with self._deal_lock:
            start_time = time.time()

            # Use parent's dealing logic
            self._deal_pieces()

            # Prepare result
            result = {
                "success": True,
                "players": {
                    p.name: {
                        "hand": [str(piece) for piece in p.hand],
                        "hand_strength": sum(piece.point for piece in p.hand),
                        "piece_count": len(p.hand),
                    }
                    for p in self.players
                },
                "timestamp": datetime.now().isoformat(),
            }

            self._async_operations["deals"] += 1
            elapsed = (time.time() - start_time) * 1000  # ms

            logger.info(
                f"Dealt pieces to {len(self.players)} players in {elapsed:.2f}ms"
            )

            # Future: await self._persist_deal(result)

            return result

    async def play_turn(
        self, player_name: str, piece_indexes: List[int]
    ) -> Dict[str, Any]:
        """
        Async version of play_turn.
        Handles a player's move, validates it, and resolves the turn if all players have played.

        Args:
            player_name: Name of the player making the move
            piece_indexes: List of indexes of pieces to play

        Returns:
            Dict with turn result

        Future: Will persist turn to database
        """
        async with self._turn_lock:
            start_time = time.time()

            # Use parent's turn logic
            result = super().play_turn(player_name, piece_indexes)

            # Add async-specific data
            result["async"] = True
            result["timestamp"] = datetime.now().isoformat()

            self._async_operations["turns"] += 1
            self.turn_number += 1

            # If round is complete, handle async scoring
            if result.get("round_complete"):
                await self._handle_round_completion(result)

            elapsed = (time.time() - start_time) * 1000  # ms
            logger.info(
                f"Player {player_name} played turn {self.turn_number} in {elapsed:.2f}ms"
            )

            # Future: await self._persist_turn(player_name, piece_indexes, result)

            return result

    async def calculate_scores(self) -> Dict[str, int]:
        """
        Async version of score calculation.
        Calculates and updates scores for the current round.

        Returns:
            Dict mapping player names to their round scores

        Future: Will persist scores to database
        """
        async with self._score_lock:
            start_time = time.time()

            # Calculate scores using parent logic
            round_scores = calculate_round_scores(
                self.players, self.pile_counts, self.redeal_multiplier
            )

            # Update player scores
            for player_name, score in round_scores.items():
                player = self.get_player(player_name)
                player.score += score
                self.round_scores[player_name] = score

            self._async_operations["scores"] += 1

            elapsed = (time.time() - start_time) * 1000  # ms
            logger.info(
                f"Calculated scores for round {self.round_number} in {elapsed:.2f}ms"
            )

            # Future: await self._persist_scores(round_scores)

            return round_scores

    async def start_new_round(self) -> Dict[str, Any]:
        """
        Async version of starting a new round.
        Resets round-specific state and prepares for the next round.

        Returns:
            Dict with new round information

        Future: Will persist round start to database
        """
        async with self._game_lock:
            start_time = time.time()

            # Increment round number
            self.round_number += 1

            # Reset round-specific state
            self.redeal_multiplier = 1
            self.current_turn_plays.clear()
            self.required_piece_count = None
            self.turn_order.clear()
            self.last_turn_winner = None
            self.turn_number = 0
            self.player_declarations.clear()
            self.pile_counts = {p.name: 0 for p in self.players}
            self.round_scores.clear()

            # Reset player states
            for player in self.players:
                player.reset_for_next_round()

            # Deal new pieces
            deal_result = await self.deal_pieces()

            self._async_operations["rounds"] += 1

            result = {
                "success": True,
                "round_number": self.round_number,
                "players": {
                    p.name: {"score": p.score, "hand_count": len(p.hand)}
                    for p in self.players
                },
                "deal_result": deal_result,
                "timestamp": datetime.now().isoformat(),
            }

            elapsed = (time.time() - start_time) * 1000  # ms
            logger.info(f"Started round {self.round_number} in {elapsed:.2f}ms")

            # Future: await self._persist_round_start(result)

            return result

    async def check_game_over(self) -> Optional[Dict[str, Any]]:
        """
        Async version of game over check.
        Checks if the game has ended according to the win condition.

        Returns:
            Dict with game over information if game ended, None otherwise

        Future: Will persist game end to database
        """
        if not self._is_game_over():
            return None

        winners = get_winners(self)
        self.end_time = time.time()

        result = {
            "game_over": True,
            "winners": [w.name for w in winners],
            "final_scores": {p.name: p.score for p in self.players},
            "rounds_played": self.round_number,
            "win_condition": self.win_condition_type.value,
            "duration": self.end_time - self.start_time if self.start_time else 0,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Game ended after {self.round_number} rounds. "
            f"Winners: {result['winners']}"
        )

        # Future: await self._persist_game_end(result)

        return result

    async def execute_redeal_for_player(self, player_name: str) -> Dict[str, Any]:
        """
        Async version of redeal execution.
        Deals new cards to a player who requested redeal.

        Args:
            player_name: Name of the player to redeal for

        Returns:
            Dict with redeal result

        Future: Will persist redeal to database
        """
        async with self._deal_lock:
            # Use parent's redeal logic
            result = super().execute_redeal_for_player(player_name)

            # Add async-specific data
            result["async"] = True
            result["timestamp"] = datetime.now().isoformat()

            logger.info(
                f"Executed redeal for {player_name}. "
                f"New multiplier: {self.redeal_multiplier}"
            )

            # Future: await self._persist_redeal(player_name, result)

            return result

    async def record_player_declaration(
        self, player_name: str, declaration: int
    ) -> Dict[str, Any]:
        """
        Async version of recording player declaration.

        Args:
            player_name: Name of the declaring player
            declaration: Number of piles they declare

        Returns:
            Dict with declaration result

        Future: Will persist declaration to database
        """
        async with self._game_lock:
            # Use parent's declaration logic
            result = super().record_player_declaration(player_name, declaration)

            # Add async-specific data
            result["async"] = True
            result["timestamp"] = datetime.now().isoformat()

            if result["success"]:
                logger.info(
                    f"{player_name} declared {declaration}. "
                    f"Total declared: {result['total_declared']}"
                )

                # Future: await self._persist_declaration(player_name, declaration)

            return result

    async def get_game_state(self) -> Dict[str, Any]:
        """
        Get complete game state asynchronously.

        Returns:
            Dict with complete game state
        """
        async with self._game_lock:
            return {
                "round_number": self.round_number,
                "turn_number": self.turn_number,
                "current_phase": self.current_phase,
                "redeal_multiplier": self.redeal_multiplier,
                "players": {
                    p.name: {
                        "score": p.score,
                        "declared": p.declared,
                        "hand_count": len(p.hand),
                        "pile_count": self.pile_counts.get(p.name, 0),
                        "is_bot": p.is_bot,
                    }
                    for p in self.players
                },
                "declarations": self.player_declarations.copy(),
                "current_player": (
                    self.current_player.name if self.current_player else None
                ),
                "last_turn_winner": (
                    self.last_turn_winner.name if self.last_turn_winner else None
                ),
                "required_piece_count": self.required_piece_count,
                "game_over": self._is_game_over(),
                "async_stats": self._async_operations.copy(),
            }

    async def _handle_round_completion(self, turn_result: Dict[str, Any]) -> None:
        """Handle async operations when a round completes."""
        # Round is already scored in play_turn, just log
        logger.info(
            f"Round {self.round_number} complete. "
            f"Scores: {turn_result.get('round_scores', {})}"
        )

        # Check for game over
        game_over_result = await self.check_game_over()
        if game_over_result:
            turn_result.update(game_over_result)

    # Compatibility methods for migration
    def deal_pieces_sync(self) -> None:
        """Sync wrapper for deal_pieces."""
        asyncio.run(self.deal_pieces())

    def play_turn_sync(
        self, player_name: str, piece_indexes: List[int]
    ) -> Dict[str, Any]:
        """Sync wrapper for play_turn."""
        return asyncio.run(self.play_turn(player_name, piece_indexes))

    def calculate_scores_sync(self) -> Dict[str, int]:
        """Sync wrapper for calculate_scores."""
        return asyncio.run(self.calculate_scores())

    def start_new_round_sync(self) -> Dict[str, Any]:
        """Sync wrapper for start_new_round."""
        return asyncio.run(self.start_new_round())
