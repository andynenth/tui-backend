"""
TurnResolution domain service - handles turn resolution logic.

This is a pure domain service with no infrastructure dependencies.
Determines the winner of each turn based on played pieces.
"""

from typing import List, Optional, Dict
from dataclasses import dataclass

from domain.value_objects.piece import Piece
from domain.entities.player import Player
from domain.services.game_rules import GameRules


@dataclass(frozen=True)
class TurnPlay:
    """Value object representing a player's play in a turn."""
    player_name: str
    pieces: List[Piece]
    play_type: str
    total_points: int
    
    @classmethod
    def create(cls, player_name: str, pieces: List[Piece]) -> "TurnPlay":
        """
        Factory method to create a TurnPlay.
        
        Args:
            player_name: Name of the player
            pieces: List of pieces played
            
        Returns:
            TurnPlay instance
        """
        play_type = GameRules.identify_play_type(pieces)
        total_points = sum(p.point for p in pieces)
        
        return cls(
            player_name=player_name,
            pieces=pieces,
            play_type=play_type,
            total_points=total_points
        )
    
    def is_valid(self) -> bool:
        """Check if this play is valid."""
        return self.play_type != "INVALID"
    
    def beats(self, other: "TurnPlay") -> bool:
        """
        Check if this play beats another play.
        
        Args:
            other: Another TurnPlay to compare against
            
        Returns:
            True if this play wins, False otherwise
        """
        # Different play types cannot be compared
        if self.play_type != other.play_type:
            return False
        
        # Invalid plays always lose
        if not self.is_valid() or not other.is_valid():
            return False
        
        # Use GameRules to compare
        result = GameRules.compare_plays(self.pieces, other.pieces)
        return result == 1  # 1 means first play wins
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "player_name": self.player_name,
            "pieces": [p.kind for p in self.pieces],
            "play_type": self.play_type,
            "total_points": self.total_points,
            "is_valid": self.is_valid()
        }


@dataclass(frozen=True)
class TurnResult:
    """Value object representing the result of a complete turn."""
    turn_number: int
    plays: List[TurnPlay]
    winner_name: Optional[str]
    winning_play: Optional[TurnPlay]
    pile_awarded: bool
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "turn_number": self.turn_number,
            "plays": [play.to_dict() for play in self.plays],
            "winner_name": self.winner_name,
            "winning_play": self.winning_play.to_dict() if self.winning_play else None,
            "pile_awarded": self.pile_awarded
        }
    
    def get_play_summary(self) -> Dict[str, List[str]]:
        """Get summary of what each player played."""
        return {
            play.player_name: [p.kind for p in play.pieces]
            for play in self.plays
        }


class TurnResolutionService:
    """
    Domain service for resolving turns.
    
    Determines the winner of a turn based on the plays made by all players.
    """
    
    @staticmethod
    def resolve_turn(
        plays: List[TurnPlay],
        turn_number: int,
        required_piece_count: Optional[int] = None
    ) -> TurnResult:
        """
        Resolve a complete turn and determine the winner.
        
        Args:
            plays: List of TurnPlay objects from all players
            turn_number: Current turn number
            required_piece_count: If set, all plays must have this many pieces
            
        Returns:
            TurnResult with winner information
        """
        # Validate piece counts if required
        if required_piece_count is not None:
            valid_plays = [
                play for play in plays 
                if len(play.pieces) == required_piece_count and play.is_valid()
            ]
        else:
            valid_plays = [play for play in plays if play.is_valid()]
        
        # No valid plays means no winner
        if not valid_plays:
            return TurnResult(
                turn_number=turn_number,
                plays=plays,
                winner_name=None,
                winning_play=None,
                pile_awarded=False
            )
        
        # Find the winning play
        winner = valid_plays[0]
        for play in valid_plays[1:]:
            if play.beats(winner):
                winner = play
        
        return TurnResult(
            turn_number=turn_number,
            plays=plays,
            winner_name=winner.player_name,
            winning_play=winner,
            pile_awarded=True
        )
    
    @staticmethod
    def validate_turn_plays(
        plays: List[TurnPlay],
        required_piece_count: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Validate all plays in a turn.
        
        Args:
            plays: List of plays to validate
            required_piece_count: If set, all plays must have this many pieces
            
        Returns:
            Dict mapping player names to validation errors (empty string if valid)
        """
        validation_results = {}
        
        for play in plays:
            if not play.is_valid():
                validation_results[play.player_name] = f"Invalid play type: {play.play_type}"
            elif required_piece_count and len(play.pieces) != required_piece_count:
                validation_results[play.player_name] = (
                    f"Must play {required_piece_count} pieces, played {len(play.pieces)}"
                )
            else:
                validation_results[play.player_name] = ""  # Valid
        
        return validation_results
    
    @staticmethod
    def get_turn_summary(result: TurnResult) -> str:
        """
        Get a human-readable summary of the turn result.
        
        Args:
            result: TurnResult to summarize
            
        Returns:
            Summary string
        """
        if not result.winner_name:
            return f"Turn {result.turn_number}: No winner (no valid plays)"
        
        winner_play = result.winning_play
        pieces_str = ", ".join(p.kind for p in winner_play.pieces)
        
        return (
            f"Turn {result.turn_number}: {result.winner_name} wins with "
            f"{winner_play.play_type} ({pieces_str}) - {winner_play.total_points} points"
        )
    
    @staticmethod
    def calculate_turn_statistics(results: List[TurnResult]) -> Dict[str, any]:
        """
        Calculate statistics from multiple turn results.
        
        Args:
            results: List of TurnResult objects
            
        Returns:
            Dict with statistics
        """
        stats = {
            "total_turns": len(results),
            "turns_with_winner": 0,
            "turns_without_winner": 0,
            "wins_by_player": {},
            "play_type_frequency": {},
            "average_winning_points": 0
        }
        
        total_winning_points = 0
        
        for result in results:
            if result.winner_name:
                stats["turns_with_winner"] += 1
                stats["wins_by_player"][result.winner_name] = (
                    stats["wins_by_player"].get(result.winner_name, 0) + 1
                )
                
                play_type = result.winning_play.play_type
                stats["play_type_frequency"][play_type] = (
                    stats["play_type_frequency"].get(play_type, 0) + 1
                )
                
                total_winning_points += result.winning_play.total_points
            else:
                stats["turns_without_winner"] += 1
        
        if stats["turns_with_winner"] > 0:
            stats["average_winning_points"] = (
                total_winning_points / stats["turns_with_winner"]
            )
        
        return stats