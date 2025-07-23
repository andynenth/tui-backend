# domain/value_objects/turn_play.py
"""
Value object representing a player's turn play.
"""

from dataclasses import dataclass
from typing import List
from ..entities.player import Player
from ..entities.piece import Piece


@dataclass(frozen=True)
class TurnPlay:
    """
    Immutable record of a player's turn.
    """
    player: Player
    pieces: List[Piece]
    play_type: str
    
    @property
    def piece_count(self) -> int:
        """Number of pieces played."""
        return len(self.pieces)
    
    @property
    def total_points(self) -> int:
        """Total point value of pieces played."""
        return sum(piece.point for piece in self.pieces)
    
    def __str__(self) -> str:
        return f"TurnPlay({self.player.name}: {self.piece_count} {self.play_type})"