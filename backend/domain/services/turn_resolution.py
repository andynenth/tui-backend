# domain/services/turn_resolution.py
"""
Domain service for resolving turns and determining winners.
Pure business logic for turn resolution.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass

from ..entities.piece import Piece
from ..entities.player import Player
from .game_rules import GameRules


@dataclass(frozen=True)
class TurnResult:
    """
    Immutable result of turn resolution.
    Contains the winning player and all plays made.
    """
    winner: Optional[str]  # Player name who won, None if no valid plays
    winning_pieces: Optional[List[Piece]]
    total_pieces_played: int
    play_type: Optional[str]
    
    @property
    def has_winner(self) -> bool:
        """Check if the turn had a winner."""
        return self.winner is not None


class TurnResolutionService:
    """
    Domain service for resolving turns and determining winners.
    This service contains the business logic for comparing plays
    and determining turn outcomes.
    """
    
    @classmethod
    def resolve_turn(
        cls,
        plays: List[Tuple[str, List[Piece]]]
    ) -> TurnResult:
        """
        Resolve a turn by comparing all plays and determining the winner.
        
        Args:
            plays: List of tuples (player_name, pieces_played)
            
        Returns:
            TurnResult with winner information
        """
        if not plays:
            return TurnResult(
                winner=None,
                winning_pieces=None,
                total_pieces_played=0,
                play_type=None
            )
        
        # Find the strongest play
        winner_name = None
        winning_pieces = None
        winning_play_type = None
        
        for player_name, pieces in plays:
            # Skip invalid plays
            play_type = GameRules.get_play_type(pieces)
            if play_type == GameRules.INVALID:
                continue
            
            # First valid play or compare with current winner
            if winner_name is None:
                winner_name = player_name
                winning_pieces = pieces
                winning_play_type = play_type
            else:
                comparison = GameRules.compare_plays(winning_pieces, pieces)
                if comparison < 0:  # Current play is stronger
                    winner_name = player_name
                    winning_pieces = pieces
                    winning_play_type = play_type
        
        # Calculate total pieces played
        total_pieces = sum(len(pieces) for _, pieces in plays)
        
        return TurnResult(
            winner=winner_name,
            winning_pieces=winning_pieces,
            total_pieces_played=total_pieces,
            play_type=winning_play_type
        )
    
    @classmethod
    def determine_required_piece_count(
        cls,
        first_play: List[Piece]
    ) -> Optional[int]:
        """
        Determine the required piece count for subsequent plays.
        
        In some game variants, all players must play the same number
        of pieces as the first player.
        
        Args:
            first_play: The pieces played by the first player
            
        Returns:
            Required piece count, or None if any count is allowed
        """
        if not first_play:
            return None
        
        # Check if the play type requires matching piece count
        play_type = GameRules.get_play_type(first_play)
        
        # For certain play types, all players must match the count
        if play_type in [
            GameRules.SINGLE,
            GameRules.PAIR,
            GameRules.THREE_OF_A_KIND,
            GameRules.FOUR_OF_A_KIND,
            GameRules.FIVE_OF_A_KIND
        ]:
            return len(first_play)
        
        # For complex plays, matching might be optional
        return None
    
    @classmethod
    def calculate_turn_strength(cls, pieces: List[Piece]) -> int:
        """
        Calculate a numeric strength value for a play.
        Used for AI decision making and analysis.
        
        Args:
            pieces: The pieces in the play
            
        Returns:
            Numeric strength value (higher is stronger)
        """
        play_type = GameRules.get_play_type(pieces)
        
        if play_type == GameRules.INVALID:
            return 0
        
        # Base strength from play type priority
        type_strength = GameRules.PLAY_TYPE_PRIORITY.index(play_type) * 1000
        
        # Add strength from highest piece
        piece_strength = max(p.point for p in pieces) if pieces else 0
        
        return type_strength + piece_strength
    
    @classmethod
    def find_winning_play(
        cls,
        plays: List[Tuple[str, List[Piece]]]
    ) -> Optional[Tuple[str, List[Piece]]]:
        """
        Find the winning play from a list of plays.
        
        Args:
            plays: List of tuples (player_name, pieces)
            
        Returns:
            Tuple of (winner_name, winning_pieces) or None
        """
        result = cls.resolve_turn(plays)
        
        if result.winner and result.winning_pieces:
            return (result.winner, result.winning_pieces)
        
        return None
    
    @classmethod
    def validate_turn_sequence(
        cls,
        plays: List[Tuple[str, List[Piece]]],
        required_count: Optional[int] = None
    ) -> List[bool]:
        """
        Validate each play in a turn sequence.
        
        Args:
            plays: List of plays to validate
            required_count: Required piece count (if any)
            
        Returns:
            List of booleans indicating validity of each play
        """
        validations = []
        
        for _, pieces in plays:
            is_valid = GameRules.is_valid_play(pieces, required_count)
            validations.append(is_valid)
        
        return validations