"""
HandStrength value object - represents the strength of a player's hand.

This is an immutable value object that encapsulates hand evaluation logic.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple

from domain.value_objects.piece import Piece


@dataclass(frozen=True)
class HandStrength:
    """
    Immutable value object representing the strength of a hand.

    Used to evaluate hands for weak hand detection and general strength comparison.
    """

    pieces: tuple[Piece, ...]
    total_points: int
    highest_piece_value: int
    is_weak: bool
    piece_distribution: tuple[tuple[str, int], ...]  # (piece_kind, count)

    @classmethod
    def calculate(cls, pieces: List[Piece]) -> "HandStrength":
        """
        Factory method to calculate hand strength from pieces.

        Args:
            pieces: List of pieces in the hand

        Returns:
            HandStrength instance
        """
        if not pieces:
            return cls(
                pieces=tuple(),
                total_points=0,
                highest_piece_value=0,
                is_weak=True,
                piece_distribution=tuple(),
            )

        # Calculate total points
        total_points = sum(p.point for p in pieces)

        # Find highest piece value
        highest_piece_value = max(p.point for p in pieces)

        # Check if weak (no piece > 9 points)
        is_weak = all(p.point <= 9 for p in pieces)

        # Calculate piece distribution
        distribution: Dict[str, int] = {}
        for piece in pieces:
            distribution[piece.kind] = distribution.get(piece.kind, 0) + 1

        # Sort by count (descending) then by piece name
        sorted_distribution = sorted(distribution.items(), key=lambda x: (-x[1], x[0]))

        return cls(
            pieces=tuple(sorted(pieces, key=lambda p: p.point, reverse=True)),
            total_points=total_points,
            highest_piece_value=highest_piece_value,
            is_weak=is_weak,
            piece_distribution=tuple(sorted_distribution),
        )

    @property
    def piece_count(self) -> int:
        """Get total number of pieces."""
        return len(self.pieces)

    @property
    def average_value(self) -> float:
        """Get average piece value."""
        if self.piece_count == 0:
            return 0.0
        return self.total_points / self.piece_count

    def has_piece(self, piece_kind: str) -> bool:
        """Check if hand contains a specific piece kind."""
        return any(p.kind == piece_kind for p in self.pieces)

    def count_piece_type(self, piece_name: str) -> int:
        """Count pieces of a specific type (e.g., 'SOLDIER')."""
        return sum(1 for p in self.pieces if p.kind.startswith(piece_name))

    def get_strongest_pieces(self, count: int) -> List[Piece]:
        """Get the N strongest pieces in the hand."""
        return list(self.pieces[:count])

    def get_weakest_pieces(self, count: int) -> List[Piece]:
        """Get the N weakest pieces in the hand."""
        return (
            list(self.pieces[-count:])
            if count <= len(self.pieces)
            else list(self.pieces)
        )

    def compare_to(self, other: "HandStrength") -> int:
        """
        Compare to another hand strength.

        Args:
            other: Another HandStrength to compare

        Returns:
            1 if this hand is stronger, -1 if weaker, 0 if equal
        """
        if self.total_points > other.total_points:
            return 1
        elif self.total_points < other.total_points:
            return -1
        else:
            # Equal points - compare highest pieces
            if self.highest_piece_value > other.highest_piece_value:
                return 1
            elif self.highest_piece_value < other.highest_piece_value:
                return -1
            else:
                return 0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "pieces": [p.kind for p in self.pieces],
            "total_points": self.total_points,
            "highest_piece_value": self.highest_piece_value,
            "is_weak": self.is_weak,
            "piece_count": self.piece_count,
            "average_value": self.average_value,
            "distribution": dict(self.piece_distribution),
        }

    def get_summary(self) -> str:
        """Get human-readable summary of hand strength."""
        weak_str = " (WEAK)" if self.is_weak else ""
        return (
            f"Hand strength: {self.total_points} points, "
            f"{self.piece_count} pieces, "
            f"highest: {self.highest_piece_value}{weak_str}"
        )


@dataclass(frozen=True)
class HandComparison:
    """
    Immutable value object representing the comparison of multiple hands.

    Used for analyzing relative hand strengths in a game.
    """

    player_hands: tuple[tuple[str, HandStrength], ...]  # (player_name, strength)
    strongest_player: str
    weakest_player: str
    weak_hand_players: tuple[str, ...]

    @classmethod
    def compare_hands(cls, player_hands: Dict[str, List[Piece]]) -> "HandComparison":
        """
        Factory method to compare multiple hands.

        Args:
            player_hands: Map of player names to their pieces

        Returns:
            HandComparison instance
        """
        if not player_hands:
            raise ValueError("Cannot compare empty hands")

        # Calculate strength for each hand
        strengths: List[Tuple[str, HandStrength]] = []
        for player_name, pieces in player_hands.items():
            strength = HandStrength.calculate(pieces)
            strengths.append((player_name, strength))

        # Sort by strength (strongest first)
        sorted_strengths = sorted(
            strengths,
            key=lambda x: (x[1].total_points, x[1].highest_piece_value),
            reverse=True,
        )

        # Find weak hand players
        weak_players = [name for name, strength in sorted_strengths if strength.is_weak]

        return cls(
            player_hands=tuple(sorted_strengths),
            strongest_player=sorted_strengths[0][0],
            weakest_player=sorted_strengths[-1][0],
            weak_hand_players=tuple(weak_players),
        )

    def get_player_strength(self, player_name: str) -> HandStrength:
        """Get strength for specific player."""
        for name, strength in self.player_hands:
            if name == player_name:
                return strength
        raise ValueError(f"Player {player_name} not found")

    def get_rank(self, player_name: str) -> int:
        """Get rank of player (1 = strongest)."""
        for i, (name, _) in enumerate(self.player_hands):
            if name == player_name:
                return i + 1
        raise ValueError(f"Player {player_name} not found")

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "rankings": [
                {"rank": i + 1, "player": name, "strength": strength.to_dict()}
                for i, (name, strength) in enumerate(self.player_hands)
            ],
            "strongest_player": self.strongest_player,
            "weakest_player": self.weakest_player,
            "weak_hand_players": list(self.weak_hand_players),
        }
