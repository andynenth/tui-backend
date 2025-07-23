# domain/entities/player.py
"""
Domain entity for Player.
Pure domain logic without infrastructure concerns.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from ..entities.piece import Piece


@dataclass
class Player:
    """
    Player entity representing a game participant.
    
    This is a pure domain entity with no infrastructure dependencies.
    Connection tracking and UI concerns (avatar color) should be handled
    by the application layer.
    """
    
    # Core identity
    name: str
    is_bot: bool = False
    
    # Game state - made private to enforce encapsulation
    _hand: List[Piece] = field(default_factory=list, init=False)
    _score: int = field(default=0, init=False)
    _declared: int = field(default=0, init=False)
    _captured_piles: int = field(default=0, init=False)
    _zero_declares_in_a_row: int = field(default=0, init=False)
    
    # Game statistics
    _turns_won: int = field(default=0, init=False)
    _perfect_rounds: int = field(default=0, init=False)
    
    # Properties for read-only access
    @property
    def hand(self) -> List[Piece]:
        """Get a copy of the player's hand to prevent external modification."""
        return list(self._hand)
    
    @property
    def score(self) -> int:
        return self._score
    
    @property
    def declared(self) -> int:
        return self._declared
    
    @property
    def captured_piles(self) -> int:
        return self._captured_piles
    
    @property
    def zero_declares_in_a_row(self) -> int:
        return self._zero_declares_in_a_row
    
    @property
    def turns_won(self) -> int:
        return self._turns_won
    
    @property
    def perfect_rounds(self) -> int:
        return self._perfect_rounds
    
    # Domain methods
    def has_red_general(self) -> bool:
        """
        Check if the player has the RED GENERAL piece.
        This determines who starts the first round.
        """
        return any(p.name == "GENERAL" and p.color == "RED" for p in self._hand)
    
    def has_weak_hand(self) -> bool:
        """
        Check if player has a weak hand (no piece > 9 points).
        """
        if not self._hand:
            return False
        return max(piece.point for piece in self._hand) <= 9
    
    def can_declare_zero(self) -> bool:
        """
        Check if player is allowed to declare zero.
        Players cannot declare zero more than twice in a row.
        """
        return self._zero_declares_in_a_row < 2
    
    # State modification methods
    def add_pieces_to_hand(self, pieces: List[Piece]) -> None:
        """Add pieces to player's hand."""
        self._hand.extend(pieces)
    
    def remove_pieces_from_hand(self, piece_indices: List[int]) -> List[Piece]:
        """
        Remove pieces from hand by indices.
        Returns the removed pieces.
        Raises ValueError if indices are invalid.
        """
        if not all(0 <= idx < len(self._hand) for idx in piece_indices):
            raise ValueError("Invalid piece indices")
        
        # Sort indices in reverse order to remove from end first
        sorted_indices = sorted(piece_indices, reverse=True)
        removed_pieces = []
        
        for idx in sorted_indices:
            removed_pieces.append(self._hand.pop(idx))
        
        # Return in original order
        removed_pieces.reverse()
        return removed_pieces
    
    def record_declaration(self, value: int) -> None:
        """
        Record player's pile declaration.
        Updates zero declaration tracking.
        """
        if value < 0 or value > 8:
            raise ValueError(f"Invalid declaration value: {value}")
        
        self._declared = value
        
        if value == 0:
            self._zero_declares_in_a_row += 1
        else:
            self._zero_declares_in_a_row = 0
    
    def add_score(self, points: int) -> None:
        """Add points to player's total score."""
        if points < 0:
            raise ValueError("Cannot add negative points")
        self._score += points
    
    def increment_turns_won(self) -> None:
        """Increment the count of turns won."""
        self._turns_won += 1
    
    def increment_perfect_rounds(self) -> None:
        """Increment the count of perfect rounds."""
        self._perfect_rounds += 1
    
    def set_captured_piles(self, count: int) -> None:
        """Set the number of piles captured this round."""
        if count < 0:
            raise ValueError("Captured piles cannot be negative")
        self._captured_piles = count
    
    def reset_for_next_round(self) -> None:
        """
        Reset player state for the next round.
        Preserves cumulative statistics and zero declaration tracking.
        """
        self._declared = 0
        self._captured_piles = 0
        self._hand.clear()
    
    def __str__(self) -> str:
        return f"{self.name} - {self._score} pts"
    
    def __repr__(self) -> str:
        return f"Player(name='{self.name}', score={self._score}, is_bot={self.is_bot})"