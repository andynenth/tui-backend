# domain/value_objects/play_result.py
"""
Value object representing the result of a play action.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class PlayResult:
    """
    Immutable result of a play action.
    """
    status: str  # "waiting", "resolved", "invalid"
    player: Optional[str] = None
    pieces_played: Optional[int] = None
    next_player: Optional[str] = None
    winner: Optional[str] = None
    pile_count: Optional[int] = None
    error: Optional[str] = None
    
    @property
    def is_turn_complete(self) -> bool:
        """Check if the turn is complete."""
        return self.status == "resolved"
    
    @property
    def is_valid(self) -> bool:
        """Check if the play was valid."""
        return self.status != "invalid"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            k: v for k, v in {
                "status": self.status,
                "player": self.player,
                "pieces_played": self.pieces_played,
                "next_player": self.next_player,
                "winner": self.winner,
                "pile_count": self.pile_count,
                "error": self.error
            }.items() if v is not None
        }