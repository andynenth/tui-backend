# domain/interfaces/bot_strategy.py
"""
Bot strategy interface for AI decision making.
This decouples the domain from specific AI implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

from ..entities.piece import Piece
from ..entities.player import Player
from ..value_objects.game_state import GameState


@dataclass(frozen=True)
class BotDecision:
    """Value object representing a bot's decision."""
    action_type: str  # "declare", "play", "redeal_response"
    value: any  # The decision value (declaration number, pieces to play, etc.)
    confidence: float  # 0.0 to 1.0 confidence in the decision
    reasoning: Optional[str] = None  # Optional explanation


class BotStrategy(ABC):
    """
    Interface for bot AI strategies.
    
    This allows different AI implementations to be plugged in
    without the domain knowing about the specific algorithms.
    """
    
    @abstractmethod
    async def make_declaration(
        self,
        player: Player,
        game_state: GameState,
        previous_declarations: List[int],
        position_in_order: int
    ) -> BotDecision:
        """
        Decide how many piles to declare.
        
        Args:
            player: The bot player making the decision
            game_state: Current game state
            previous_declarations: Declarations made by previous players
            position_in_order: Bot's position in declaration order
            
        Returns:
            BotDecision with declaration value (0-8)
        """
        pass
    
    @abstractmethod
    async def choose_play(
        self,
        player: Player,
        game_state: GameState,
        current_turn_plays: List[tuple[str, List[Piece]]],
        required_piece_count: Optional[int]
    ) -> BotDecision:
        """
        Choose which pieces to play.
        
        Args:
            player: The bot player making the decision
            game_state: Current game state
            current_turn_plays: Plays already made this turn
            required_piece_count: Required number of pieces (if any)
            
        Returns:
            BotDecision with list of pieces to play
        """
        pass
    
    @abstractmethod
    async def should_accept_redeal(
        self,
        player: Player,
        game_state: GameState,
        current_hand_strength: float
    ) -> BotDecision:
        """
        Decide whether to accept a redeal.
        
        Args:
            player: The bot player making the decision
            game_state: Current game state
            current_hand_strength: Numeric evaluation of hand strength
            
        Returns:
            BotDecision with boolean value (True to accept)
        """
        pass
    
    @abstractmethod
    def evaluate_hand(self, pieces: List[Piece]) -> float:
        """
        Evaluate the strength of a hand.
        
        Args:
            pieces: The pieces to evaluate
            
        Returns:
            Numeric strength value (higher is better)
        """
        pass
    
    @abstractmethod
    def get_difficulty_level(self) -> str:
        """
        Get the difficulty level of this strategy.
        
        Returns:
            One of: "easy", "medium", "hard", "expert"
        """
        pass


class BotStrategyFactory(ABC):
    """
    Factory interface for creating bot strategies.
    
    This allows the application layer to create appropriate
    bot strategies based on configuration or player preferences.
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_available_difficulties(self) -> List[str]:
        """
        Get list of available difficulty levels.
        
        Returns:
            List of difficulty strings
        """
        pass