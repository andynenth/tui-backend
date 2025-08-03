# backend/engine/async_bot_strategy.py
"""
Async bot decision making strategies for improved performance.
This module provides async interfaces for bot AI decisions.
"""

import asyncio
import random
import time
from typing import List, Optional, Dict, Any
import logging

from .piece import Piece
from .player import Player
from . import ai

logger = logging.getLogger(__name__)


class AsyncBotStrategy:
    """
    Async wrapper for bot AI decision making.
    Provides non-blocking AI decisions for better concurrency.
    """

    def __init__(self):
        """Initialize async bot strategy."""
        self._decision_cache = {}  # Cache recent decisions
        self._cache_ttl = 2.0  # Cache time-to-live in seconds

    async def choose_declaration(
        self,
        hand: List[Piece],
        is_first_player: bool,
        position_in_order: int,
        previous_declarations: List[int],
        must_declare_nonzero: bool = False,
        verbose: bool = False,
    ) -> int:
        """
        Async version of declaration choice.
        Runs the CPU-intensive AI decision in a thread pool.

        Args:
            hand: Player's current hand
            is_first_player: Whether this is the first player to declare
            position_in_order: Player's position in declaration order
            previous_declarations: List of previous player declarations
            must_declare_nonzero: Whether player must declare non-zero
            verbose: Whether to log decision process

        Returns:
            Number of piles to declare
        """
        start_time = time.time()

        # Run AI decision in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        declaration = await loop.run_in_executor(
            None,
            ai.choose_declare,
            hand,
            is_first_player,
            position_in_order,
            previous_declarations,
            must_declare_nonzero,
            verbose,
        )

        elapsed = (time.time() - start_time) * 1000
        logger.debug(f"Async declaration choice took {elapsed:.2f}ms")

        return declaration

    async def choose_best_play(
        self,
        hand: List[Piece],
        required_count: Optional[int] = None,
        verbose: bool = True,
    ) -> List[Piece]:
        """
        Async version of play choice.
        Runs the CPU-intensive AI decision in a thread pool.

        Args:
            hand: Player's current hand
            required_count: Required number of pieces to play
            verbose: Whether to log decision process

        Returns:
            List of pieces to play
        """
        start_time = time.time()

        # Run AI decision in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        pieces = await loop.run_in_executor(
            None, ai.choose_best_play, hand, required_count, verbose
        )

        elapsed = (time.time() - start_time) * 1000
        logger.debug(f"Async play choice took {elapsed:.2f}ms")

        return pieces

    async def should_accept_redeal(
        self,
        hand: List[Piece],
        round_number: int,
        current_score: int,
        opponent_scores: Dict[str, int],
    ) -> bool:
        """
        Async decision for whether to accept a redeal.

        Args:
            hand: Player's current hand
            round_number: Current round number
            current_score: Bot's current score
            opponent_scores: Opponents' scores

        Returns:
            True to accept redeal, False to decline
        """
        # Simple strategy for now - can be enhanced with AI
        # Calculate hand strength
        hand_strength = sum(p.point for p in hand)
        max_piece = max((p.point for p in hand), default=0)

        # More likely to accept redeal if:
        # - Hand is very weak (no piece > 9)
        # - Behind in score late in game
        # - Hand strength is below average

        if max_piece <= 9:
            # Weak hand, usually accept
            accept_probability = 0.8
        elif hand_strength < 60:  # Below average (32 pieces, 248 total points)
            accept_probability = 0.6
        else:
            accept_probability = 0.3

        # Adjust based on game state
        if round_number > 10:
            # Late game - be more conservative if winning
            max_opponent_score = max(opponent_scores.values(), default=0)
            if current_score > max_opponent_score + 10:
                accept_probability *= 0.5  # Less likely to risk when ahead

        # Add some randomness
        decision = random.random() < accept_probability

        logger.info(
            f"Redeal decision: hand_strength={hand_strength}, "
            f"max_piece={max_piece}, accept={decision}"
        )

        return decision

    async def simulate_concurrent_decisions(
        self, bot_hands: Dict[str, List[Piece]], decision_type: str = "declare"
    ) -> Dict[str, Any]:
        """
        Simulate multiple bot decisions concurrently.
        Useful for performance testing.

        Args:
            bot_hands: Mapping of bot names to their hands
            decision_type: Type of decision to make ("declare" or "play")

        Returns:
            Dict mapping bot names to their decisions
        """
        tasks = []
        bot_names = list(bot_hands.keys())

        if decision_type == "declare":
            for i, (bot_name, hand) in enumerate(bot_hands.items()):
                task = self.choose_declaration(
                    hand=hand,
                    is_first_player=(i == 0),
                    position_in_order=i,
                    previous_declarations=[],
                    must_declare_nonzero=False,
                    verbose=False,
                )
                tasks.append(task)
        else:  # play
            for bot_name, hand in bot_hands.items():
                task = self.choose_best_play(
                    hand=hand, required_count=None, verbose=False
                )
                tasks.append(task)

        # Run all decisions concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        elapsed = (time.time() - start_time) * 1000

        logger.info(
            f"Concurrent {decision_type} decisions for {len(bot_hands)} bots "
            f"completed in {elapsed:.2f}ms"
        )

        return dict(zip(bot_names, results))


# Global instance for reuse
async_bot_strategy = AsyncBotStrategy()
