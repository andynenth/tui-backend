# domain/entities/piece.py
"""
Domain entity for game pieces.
This is a pure domain object with no external dependencies.
"""

from dataclasses import dataclass
from typing import List, Dict


# Domain constants - these belong in the domain layer
PIECE_POINTS: Dict[str, int] = {
    "GENERAL_RED": 14,
    "GENERAL_BLACK": 13,
    "ADVISOR_RED": 12,
    "ADVISOR_BLACK": 11,
    "ELEPHANT_RED": 10,
    "ELEPHANT_BLACK": 9,
    "CHARIOT_RED": 8,
    "CHARIOT_BLACK": 7,
    "HORSE_RED": 6,
    "HORSE_BLACK": 5,
    "CANNON_RED": 4,
    "CANNON_BLACK": 3,
    "SOLDIER_RED": 2,
    "SOLDIER_BLACK": 1,
}


@dataclass(frozen=True)
class Piece:
    """
    Immutable piece entity.
    
    A piece is defined by its kind (e.g., "GENERAL_RED") which
    determines both its type and color.
    """
    kind: str
    
    def __post_init__(self):
        """Validate piece kind on creation."""
        if self.kind not in PIECE_POINTS:
            raise ValueError(f"Invalid piece kind: {self.kind}")
    
    @property
    def point(self) -> int:
        """Get the point value of this piece."""
        return PIECE_POINTS[self.kind]
    
    @property
    def name(self) -> str:
        """Get the piece type name (e.g., "GENERAL", "SOLDIER")."""
        return self.kind.split("_")[0]
    
    @property
    def color(self) -> str:
        """Get the piece color ("RED" or "BLACK")."""
        return self.kind.split("_")[1]
    
    def is_stronger_than(self, other: 'Piece') -> bool:
        """Check if this piece is stronger than another."""
        return self.point > other.point
    
    def __str__(self) -> str:
        return f"{self.kind}({self.point})"
    
    def __repr__(self) -> str:
        return f"Piece('{self.kind}')"
    
    def __eq__(self, other) -> bool:
        """Pieces are equal if they have the same kind."""
        if not isinstance(other, Piece):
            return False
        return self.kind == other.kind
    
    def __hash__(self) -> int:
        """Make piece hashable for use in sets/dicts."""
        return hash(self.kind)
    
    def __lt__(self, other) -> bool:
        """Allow sorting pieces by point value."""
        if not isinstance(other, Piece):
            return NotImplemented
        return self.point < other.point


class PieceDeck:
    """
    Factory for creating a standard deck of pieces.
    This is separated from the Piece entity to maintain single responsibility.
    """
    
    # Piece counts in a standard deck
    PIECE_COUNTS = {
        "GENERAL": 1,   # Only one of each GENERAL
        "SOLDIER": 5,   # Five of each SOLDIER
        # All others default to 2
    }
    
    @classmethod
    def build_standard_deck(cls) -> List[Piece]:
        """
        Create the full deck of 32 pieces according to game rules.
        
        Returns:
            List of 32 Piece objects
        """
        deck = []
        
        for kind in PIECE_POINTS:
            piece_type = kind.split("_")[0]
            count = cls.PIECE_COUNTS.get(piece_type, 2)  # Default to 2
            
            for _ in range(count):
                deck.append(Piece(kind))
        
        return deck
    
    @classmethod
    def build_test_deck(cls, pieces_per_player: int = 8) -> List[Piece]:
        """
        Build a smaller deck for testing.
        
        Args:
            pieces_per_player: Number of pieces each player should get
            
        Returns:
            List of pieces (4 * pieces_per_player total)
        """
        total_needed = 4 * pieces_per_player
        full_deck = cls.build_standard_deck()
        
        if total_needed > len(full_deck):
            raise ValueError(f"Cannot create test deck with {total_needed} pieces")
        
        return full_deck[:total_needed]