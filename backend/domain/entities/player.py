# backend/domain/entities/player.py

"""
Player Entity - Core domain object
This file should have ZERO external dependencies!
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Player:
    """Represents a player in the game"""
    name: str
    is_bot: bool = False
    score: int = 0
    hand: Optional[List['Piece']] = None
    
    def __post_init__(self):
        """Initialize hand if not provided"""
        if self.hand is None:
            self.hand = []
    
    def add_to_score(self, points: int) -> None:
        """Add points to player's score"""
        self.score += points
    
    def reset_hand(self) -> None:
        """Clear player's hand"""
        self.hand = []
    
    def __str__(self) -> str:
        """String representation"""
        return f"Player({self.name}, bot={self.is_bot}, score={self.score})"


# Quick test to ensure it works
if __name__ == "__main__":
    # Test the entity
    player = Player("Alice", is_bot=False)
    print(f"Created: {player}")
    player.add_to_score(10)
    print(f"After scoring: {player}")
    print("✅ Player entity works!")
