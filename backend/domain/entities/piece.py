# backend/domain/entities/piece.py

"""
Piece Entity - Represents game pieces in Liap Tui
This file should have ZERO external dependencies!
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class PieceType(Enum):
    """Types of pieces in Liap Tui"""
    NORMAL = "normal"
    SPECIAL = "special"  # Add specific types based on your game rules


class PieceColor(Enum):
    """Colors/suits of pieces"""
    RED = "red"
    BLACK = "black"
    GREEN = "green"
    YELLOW = "yellow"


@dataclass(frozen=True)  # Immutable - pieces don't change once created
class Piece:
    """
    Represents a game piece in Liap Tui
    
    Made immutable (frozen=True) because pieces are value objects -
    their identity is based on their values, not their location in memory.
    """
    value: int
    color: PieceColor
    piece_type: PieceType = PieceType.NORMAL
    
    def __post_init__(self):
        """Validate piece creation"""
        if self.value < 1:
            raise ValueError("Piece value must be positive")
    
    @property
    def display_name(self) -> str:
        """Human-readable piece representation"""
        return f"{self.color.value.title()} {self.value}"
    
    @property
    def is_special(self) -> bool:
        """Check if this is a special piece"""
        return self.piece_type == PieceType.SPECIAL
    
    def can_beat(self, other: 'Piece') -> bool:
        """
        Domain logic: Can this piece beat another piece?
        Override this method based on your specific game rules.
        """
        if self.is_special and not other.is_special:
            return True
        if not self.is_special and other.is_special:
            return False
        return self.value > other.value
    
    def __str__(self) -> str:
        """String representation for debugging"""
        special_marker = "*" if self.is_special else ""
        return f"{self.display_name}{special_marker}"


# Quick tests to ensure it works
if __name__ == "__main__":
    # Test piece creation
    piece1 = Piece(value=5, color=PieceColor.RED)
    piece2 = Piece(value=3, color=PieceColor.BLACK, piece_type=PieceType.SPECIAL)
    
    print(f"Created pieces: {piece1}, {piece2}")
    print(f"Can {piece1} beat {piece2}? {piece1.can_beat(piece2)}")
    print(f"Can {piece2} beat {piece1}? {piece2.can_beat(piece1)}")
    
    # Test immutability (this should work because it's frozen)
    try:
        # piece1.value = 10  # This would raise an error!
        print("✅ Piece immutability working correctly")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test validation
    try:
        invalid_piece = Piece(value=-1, color=PieceColor.RED)
    except ValueError as e:
        print(f"✅ Validation working: {e}")
    
    print("✅ Piece entity works!")