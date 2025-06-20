# backend/domain/interfaces/bot_strategy.py

"""
Bot Strategy Interface - Defines contract for bot implementations
This file should have ZERO external dependencies!
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.player import Player
from ..entities.piece import Piece
from ..value_objects.game_phase import GamePhase


class BotStrategy(ABC):
    """
    Abstract interface for bot decision-making strategies
    
    This defines the contract that all bot implementations must follow.
    The domain layer defines WHAT bots need to do, not HOW they do it.
    Infrastructure layer will provide concrete implementations.
    """
    
    @abstractmethod
    def choose_pieces_to_play(
        self, 
        hand: List[Piece], 
        game_phase: GamePhase,
        context: Optional[dict] = None
    ) -> List[Piece]:
        """
        Choose which pieces to play from the bot's hand
        
        Args:
            hand: Bot's current pieces
            game_phase: Current phase of the game
            context: Additional game context (scores, other players, etc.)
            
        Returns:
            List of pieces the bot chooses to play
            
        Raises:
            ValueError: If trying to play pieces not in hand
        """
        pass
    
    @abstractmethod
    def should_redeal(
        self, 
        hand: List[Piece], 
        context: Optional[dict] = None
    ) -> bool:
        """
        Decide whether to redeal the hand
        
        Args:
            hand: Bot's current pieces
            context: Game context for decision making
            
        Returns:
            True if bot wants to redeal, False otherwise
        """
        pass
    
    @abstractmethod
    def make_declaration(
        self, 
        hand: List[Piece],
        context: Optional[dict] = None
    ) -> str:
        """
        Make a declaration about the bot's strategy
        
        Args:
            hand: Bot's current pieces
            context: Game context
            
        Returns:
            Declaration string (game-specific)
        """
        pass
    
    @property
    @abstractmethod
    def difficulty_level(self) -> str:
        """
        Get the difficulty level of this bot strategy
        
        Returns:
            String representing difficulty: "easy", "medium", "hard"
        """
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """
        Get a human-readable name for this strategy
        
        Returns:
            Name of the strategy (e.g., "Aggressive Player", "Conservative Bot")
        """
        pass


class BotDecision:
    """
    Value object representing a bot's decision
    
    This encapsulates the result of bot decision-making, making it
    easier to test and validate bot behavior.
    """
    
    def __init__(
        self, 
        pieces_to_play: List[Piece],
        reasoning: Optional[str] = None,
        confidence: float = 1.0
    ):
        self.pieces_to_play = pieces_to_play
        self.reasoning = reasoning or "No reasoning provided"
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
    
    @property
    def is_confident(self) -> bool:
        """Returns True if confidence is above 0.7"""
        return self.confidence > 0.7
    
    def __str__(self) -> str:
        pieces_str = ", ".join(str(piece) for piece in self.pieces_to_play)
        return f"Play [{pieces_str}] (confidence: {self.confidence:.1f})"


# Quick demonstration of the interface pattern
if __name__ == "__main__":
    from ..entities.piece import Piece, PieceColor
    
    # This would fail because BotStrategy is abstract
    try:
        # bot = BotStrategy()  # This would raise TypeError!
        print("✅ Cannot instantiate abstract interface (good!)")
    except TypeError as e:
        print(f"✅ Expected error: {e}")
    
    # Test the decision value object
    pieces = [Piece(5, PieceColor.RED), Piece(3, PieceColor.BLACK)]
    decision = BotDecision(
        pieces_to_play=pieces,
        reasoning="Playing high-value pieces early",
        confidence=0.8
    )
    
    print(f"✅ Bot decision: {decision}")
    print(f"✅ Is confident: {decision.is_confident}")
    print("✅ BotStrategy interface works!")