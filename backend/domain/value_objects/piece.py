"""
Piece value object - Represents a game piece with immutable properties.

This is a pure domain object with no infrastructure dependencies.
"""

from dataclasses import dataclass
from typing import List, Dict, ClassVar


@dataclass(frozen=True)
class Piece:
    """
    Immutable value object representing a game piece.
    
    A piece has a type (name), color, and point value.
    Pieces are compared by their point values.
    """
    kind: str  # Combined identifier, e.g., "GENERAL_RED"
    point: int  # Point value for scoring and comparison
    
    # Class-level constants
    PIECE_POINTS: ClassVar[Dict[str, int]] = {
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
    
    DECK_COMPOSITION: ClassVar[Dict[str, int]] = {
        "GENERAL": 1,   # One of each color
        "SOLDIER": 5,   # Five of each color
        # All others default to 2 of each color
    }
    
    DEFAULT_COUNT: ClassVar[int] = 2
    
    def __post_init__(self):
        """Validate piece on creation."""
        if self.kind not in self.PIECE_POINTS:
            raise ValueError(f"Invalid piece kind: {self.kind}")
        if self.point != self.PIECE_POINTS[self.kind]:
            raise ValueError(f"Invalid point value for {self.kind}: {self.point}")
    
    @classmethod
    def create(cls, kind: str) -> "Piece":
        """
        Factory method to create a piece from its kind.
        
        Args:
            kind: The piece identifier (e.g., "GENERAL_RED")
            
        Returns:
            A new Piece instance
            
        Raises:
            ValueError: If kind is invalid
        """
        if kind not in cls.PIECE_POINTS:
            raise ValueError(f"Invalid piece kind: {kind}")
        return cls(kind=kind, point=cls.PIECE_POINTS[kind])
    
    @property
    def name(self) -> str:
        """Get the piece type name (e.g., "GENERAL", "SOLDIER")."""
        return self.kind.split("_")[0]
    
    @property
    def color(self) -> str:
        """Get the piece color ("RED" or "BLACK")."""
        return self.kind.split("_")[1]
    
    @property
    def is_red(self) -> bool:
        """Check if piece is red."""
        return self.color == "RED"
    
    @property
    def is_black(self) -> bool:
        """Check if piece is black."""
        return self.color == "BLACK"
    
    def beats(self, other: "Piece") -> bool:
        """
        Check if this piece beats another piece.
        
        In standard rules, higher point value wins.
        Special rules (e.g., SOLDIER beats GENERAL) should be
        implemented in the GameRules service.
        
        Args:
            other: The piece to compare against
            
        Returns:
            True if this piece has higher point value
        """
        return self.point > other.point
    
    def __lt__(self, other: "Piece") -> bool:
        """Less than comparison based on point value."""
        return self.point < other.point
    
    def __le__(self, other: "Piece") -> bool:
        """Less than or equal comparison based on point value."""
        return self.point <= other.point
    
    def __gt__(self, other: "Piece") -> bool:
        """Greater than comparison based on point value."""
        return self.point > other.point
    
    def __ge__(self, other: "Piece") -> bool:
        """Greater than or equal comparison based on point value."""
        return self.point >= other.point
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.kind}({self.point})"
    
    def to_dict(self) -> Dict[str, any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary with piece data
        """
        return {
            "kind": self.kind,
            "point": self.point,
            "name": self.name,
            "color": self.color,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "Piece":
        """
        Create piece from dictionary.
        
        Args:
            data: Dictionary with 'kind' and 'point'
            
        Returns:
            New Piece instance
        """
        return cls(kind=data["kind"], point=data["point"])
    
    @classmethod
    def build_deck(cls) -> List["Piece"]:
        """
        Create the full deck of 32 pieces.
        
        Returns:
            List of all pieces in a standard deck
        """
        deck = []
        for kind, point in cls.PIECE_POINTS.items():
            name = kind.split("_")[0]
            count = cls.DECK_COMPOSITION.get(name, cls.DEFAULT_COUNT)
            for _ in range(count):
                deck.append(cls(kind=kind, point=point))
        return deck
    
    @classmethod
    def all_kinds(cls) -> List[str]:
        """Get all valid piece kinds."""
        return list(cls.PIECE_POINTS.keys())
    
    @classmethod
    def get_point_value(cls, kind: str) -> int:
        """
        Get point value for a piece kind.
        
        Args:
            kind: The piece identifier
            
        Returns:
            Point value
            
        Raises:
            ValueError: If kind is invalid
        """
        if kind not in cls.PIECE_POINTS:
            raise ValueError(f"Invalid piece kind: {kind}")
        return cls.PIECE_POINTS[kind]