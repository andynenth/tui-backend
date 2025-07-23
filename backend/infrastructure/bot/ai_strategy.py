# infrastructure/bot/ai_strategy.py
"""
AI strategy implementations for bot players.
"""

import logging
from typing import List, Optional
import random
from dataclasses import dataclass

from domain.interfaces.bot_strategy import (
    BotStrategy,
    BotStrategyFactory,
    BotDecision
)
from domain.entities.player import Player
from domain.entities.piece import Piece
from domain.value_objects.game_state import GameState
from domain.services.game_rules import GameRules

logger = logging.getLogger(__name__)


class EasyBotStrategy(BotStrategy):
    """
    Easy difficulty bot strategy.
    Makes random but valid moves.
    """
    
    async def make_declaration(
        self,
        player: Player,
        game_state: GameState,
        previous_declarations: List[int],
        position_in_order: int
    ) -> BotDecision:
        """Make a random valid declaration."""
        # Easy bot just picks a random number 0-8
        # avoiding the total of 8 if possible
        total_so_far = sum(previous_declarations)
        remaining_players = 4 - len(previous_declarations) - 1  # -1 for self
        
        # Generate valid options
        valid_declarations = []
        for i in range(9):  # 0-8
            future_total = total_so_far + i
            # Check if this leaves room for others to not sum to 8
            if remaining_players == 0 or future_total + remaining_players * 8 != 8:
                valid_declarations.append(i)
        
        # If no valid options, just pick any
        if not valid_declarations:
            valid_declarations = list(range(9))
        
        declaration = random.choice(valid_declarations)
        
        return BotDecision(
            action_type="declare",
            value=declaration,
            confidence=0.3,  # Low confidence for easy bot
            reasoning=f"Random choice from {len(valid_declarations)} options"
        )
    
    async def choose_play(
        self,
        player: Player,
        game_state: GameState,
        current_turn_plays: List[tuple[str, List[Piece]]],
        required_piece_count: Optional[int]
    ) -> BotDecision:
        """Choose random valid pieces to play."""
        pieces = player.pieces
        
        if not pieces:
            return BotDecision(
                action_type="play",
                value=[],
                confidence=1.0,
                reasoning="No pieces to play"
            )
        
        # Determine valid play counts
        if required_piece_count:
            play_counts = [required_piece_count]
        else:
            play_counts = list(range(1, min(7, len(pieces) + 1)))
        
        # Pick random count
        count = random.choice(play_counts)
        
        # Pick random pieces
        selected_indices = random.sample(range(len(pieces)), count)
        selected_pieces = [pieces[i] for i in selected_indices]
        
        # Validate it's a legal play
        play_type = GameRules.get_play_type(selected_pieces)
        if play_type == "invalid":
            # Just play first piece if invalid
            selected_indices = [0]
        
        return BotDecision(
            action_type="play",
            value=selected_indices,
            confidence=0.3,
            reasoning=f"Random play of {len(selected_indices)} pieces"
        )
    
    async def should_accept_redeal(
        self,
        player: Player,
        game_state: GameState,
        current_hand_strength: float
    ) -> BotDecision:
        """Randomly decide on redeal."""
        # Easy bot accepts redeal 70% of the time
        accept = random.random() < 0.7
        
        return BotDecision(
            action_type="redeal_response",
            value=accept,
            confidence=0.5,
            reasoning="Random decision"
        )
    
    def evaluate_hand(self, pieces: List[Piece]) -> float:
        """Simple hand evaluation."""
        if not pieces:
            return 0.0
        
        # Just use average piece value
        return sum(p.value for p in pieces) / len(pieces) / 20.0
    
    def get_difficulty_level(self) -> str:
        """Get difficulty level."""
        return "easy"


class MediumBotStrategy(BotStrategy):
    """
    Medium difficulty bot strategy.
    Makes reasonable moves with some strategy.
    """
    
    async def make_declaration(
        self,
        player: Player,
        game_state: GameState,
        previous_declarations: List[int],
        position_in_order: int
    ) -> BotDecision:
        """Make a strategic declaration based on hand strength."""
        # Evaluate hand strength
        hand_strength = self.evaluate_hand(player.pieces)
        
        # Stronger hands declare fewer piles
        if hand_strength > 0.7:
            base_declaration = random.choice([0, 1, 2])
        elif hand_strength > 0.4:
            base_declaration = random.choice([2, 3, 4])
        else:
            base_declaration = random.choice([4, 5, 6])
        
        # Adjust based on what others declared
        total_so_far = sum(previous_declarations)
        avg_declaration = total_so_far / len(previous_declarations) if previous_declarations else 4
        
        # If others are declaring low, we might want to declare higher
        if avg_declaration < 3:
            base_declaration = min(8, base_declaration + 1)
        
        # Ensure total doesn't equal 8
        remaining_players = 4 - len(previous_declarations) - 1
        if remaining_players == 0 and total_so_far + base_declaration == 8:
            # Adjust to avoid total of 8
            if base_declaration > 0:
                base_declaration -= 1
            else:
                base_declaration += 1
        
        return BotDecision(
            action_type="declare",
            value=base_declaration,
            confidence=0.6,
            reasoning=f"Strategic choice based on hand strength {hand_strength:.2f}"
        )
    
    async def choose_play(
        self,
        player: Player,
        game_state: GameState,
        current_turn_plays: List[tuple[str, List[Piece]]],
        required_piece_count: Optional[int]
    ) -> BotDecision:
        """Choose pieces strategically."""
        pieces = player.pieces
        
        if not pieces:
            return BotDecision(
                action_type="play",
                value=[],
                confidence=1.0,
                reasoning="No pieces to play"
            )
        
        # Sort pieces by value
        indexed_pieces = [(i, p) for i, p in enumerate(pieces)]
        indexed_pieces.sort(key=lambda x: x[1].value)
        
        # If required count, try to play lowest values
        if required_piece_count:
            selected_indices = [idx for idx, _ in indexed_pieces[:required_piece_count]]
            return BotDecision(
                action_type="play",
                value=selected_indices,
                confidence=0.7,
                reasoning=f"Playing {required_piece_count} lowest pieces"
            )
        
        # Otherwise, look for good plays
        # Try to make pairs, triples, etc.
        value_groups = {}
        for idx, piece in indexed_pieces:
            if piece.value not in value_groups:
                value_groups[piece.value] = []
            value_groups[piece.value].append(idx)
        
        # Look for multiples
        for value, indices in value_groups.items():
            if len(indices) >= 2:
                # Play a pair or triple
                count = min(len(indices), 3)
                return BotDecision(
                    action_type="play",
                    value=indices[:count],
                    confidence=0.8,
                    reasoning=f"Playing {count} pieces of value {value}"
                )
        
        # No multiples, play single low piece
        return BotDecision(
            action_type="play",
            value=[indexed_pieces[0][0]],
            confidence=0.6,
            reasoning="Playing single lowest piece"
        )
    
    async def should_accept_redeal(
        self,
        player: Player,
        game_state: GameState,
        current_hand_strength: float
    ) -> BotDecision:
        """Decide based on hand strength."""
        # Accept if hand is weak
        accept = current_hand_strength < 0.3
        
        return BotDecision(
            action_type="redeal_response",
            value=accept,
            confidence=0.8,
            reasoning=f"Hand strength {current_hand_strength:.2f}"
        )
    
    def evaluate_hand(self, pieces: List[Piece]) -> float:
        """Evaluate hand considering high cards and pairs."""
        if not pieces:
            return 0.0
        
        score = 0.0
        
        # High cards are good
        high_cards = sum(1 for p in pieces if p.value >= 15)
        score += high_cards * 0.2
        
        # Pairs/multiples are good
        value_counts = {}
        for piece in pieces:
            value_counts[piece.value] = value_counts.get(piece.value, 0) + 1
        
        multiples = sum(1 for count in value_counts.values() if count >= 2)
        score += multiples * 0.3
        
        # Average value factor
        avg_value = sum(p.value for p in pieces) / len(pieces)
        score += (avg_value / 20.0) * 0.5
        
        return min(1.0, score)
    
    def get_difficulty_level(self) -> str:
        """Get difficulty level."""
        return "medium"


class SimpleBotStrategyFactory(BotStrategyFactory):
    """
    Factory for creating bot strategies.
    """
    
    def create_strategy(self, difficulty: str) -> BotStrategy:
        """
        Create a bot strategy for the given difficulty.
        
        Args:
            difficulty: One of "easy", "medium", "hard", "expert"
            
        Returns:
            BotStrategy implementation
            
        Raises:
            ValueError: If difficulty is not recognized
        """
        if difficulty == "easy":
            return EasyBotStrategy()
        elif difficulty == "medium":
            return MediumBotStrategy()
        elif difficulty == "hard":
            # For now, use medium for hard
            return MediumBotStrategy()
        elif difficulty == "expert":
            # For now, use medium for expert
            return MediumBotStrategy()
        else:
            raise ValueError(f"Unknown difficulty: {difficulty}")
    
    def get_available_difficulties(self) -> List[str]:
        """Get list of available difficulty levels."""
        return ["easy", "medium", "hard", "expert"]