# domain/services/game_rules.py
"""
Domain service for game rules and play validation.
Pure business logic with no external dependencies.
"""

from typing import List, Set, Tuple
from collections import Counter
from ..entities.piece import Piece


class GameRules:
    """
    Domain service encapsulating game rules and validation logic.
    This is a stateless service containing pure business logic.
    """
    
    # Play type constants
    SINGLE = "SINGLE"
    PAIR = "PAIR"
    THREE_OF_A_KIND = "THREE_OF_A_KIND"
    STRAIGHT = "STRAIGHT"
    FOUR_OF_A_KIND = "FOUR_OF_A_KIND"
    EXTENDED_STRAIGHT = "EXTENDED_STRAIGHT"
    EXTENDED_STRAIGHT_5 = "EXTENDED_STRAIGHT_5"
    FIVE_OF_A_KIND = "FIVE_OF_A_KIND"
    DOUBLE_STRAIGHT = "DOUBLE_STRAIGHT"
    INVALID = "INVALID"
    
    # Priority order (higher index = stronger)
    PLAY_TYPE_PRIORITY = [
        SINGLE,
        PAIR,
        THREE_OF_A_KIND,
        STRAIGHT,
        FOUR_OF_A_KIND,
        EXTENDED_STRAIGHT,
        EXTENDED_STRAIGHT_5,
        FIVE_OF_A_KIND,
        DOUBLE_STRAIGHT,
    ]
    
    # Valid straight groups
    STRAIGHT_GROUPS = [
        ("GENERAL", "ADVISOR", "ELEPHANT"),  # High straight
        ("CHARIOT", "HORSE", "CANNON"),      # Low straight
    ]
    
    @classmethod
    def get_play_type(cls, pieces: List[Piece]) -> str:
        """
        Determine the type of play from a list of pieces.
        
        Args:
            pieces: List of Piece objects to analyze
            
        Returns:
            One of the play type constants or INVALID
        """
        if not pieces:
            return cls.INVALID
        
        count = len(pieces)
        
        # Handle single piece
        if count == 1:
            return cls.SINGLE
        
        # Check color consistency (all pieces must be same color)
        colors = {p.color for p in pieces}
        if len(colors) > 1:
            return cls.INVALID
        
        color = colors.pop()
        
        # Analyze piece names
        names = [p.name for p in pieces]
        name_counts = Counter(names)
        unique_names = set(names)
        
        # Handle different piece counts
        if count == 2:
            return cls._check_pair(name_counts)
        elif count == 3:
            return cls._check_three_pieces(name_counts, unique_names)
        elif count == 4:
            return cls._check_four_pieces(name_counts, unique_names)
        elif count == 5:
            return cls._check_five_pieces(name_counts, unique_names)
        elif count == 6:
            return cls._check_six_pieces(name_counts)
        else:
            return cls.INVALID
    
    @classmethod
    def _check_pair(cls, name_counts: Counter) -> str:
        """Check if pieces form a valid pair."""
        if len(name_counts) == 1 and 2 in name_counts.values():
            return cls.PAIR
        return cls.INVALID
    
    @classmethod
    def _check_three_pieces(cls, name_counts: Counter, unique_names: Set[str]) -> str:
        """Check valid plays for 3 pieces."""
        # Three of a kind (only SOLDIER)
        if len(name_counts) == 1 and "SOLDIER" in name_counts and name_counts["SOLDIER"] == 3:
            return cls.THREE_OF_A_KIND
        
        # Straight (3 different pieces from valid group)
        if len(unique_names) == 3:
            for group in cls.STRAIGHT_GROUPS:
                if unique_names == set(group):
                    return cls.STRAIGHT
        
        return cls.INVALID
    
    @classmethod
    def _check_four_pieces(cls, name_counts: Counter, unique_names: Set[str]) -> str:
        """Check valid plays for 4 pieces."""
        # Four of a kind (only SOLDIER)
        if len(name_counts) == 1 and "SOLDIER" in name_counts and name_counts["SOLDIER"] == 4:
            return cls.FOUR_OF_A_KIND
        
        # Extended straight (3 unique from valid group, 1 duplicate)
        if len(unique_names) == 3:
            for group in cls.STRAIGHT_GROUPS:
                if unique_names.issubset(set(group)):
                    # Check for exactly one duplicate
                    if sorted(name_counts.values()) == [1, 1, 2]:
                        return cls.EXTENDED_STRAIGHT
        
        return cls.INVALID
    
    @classmethod
    def _check_five_pieces(cls, name_counts: Counter, unique_names: Set[str]) -> str:
        """Check valid plays for 5 pieces."""
        # Five of a kind (only SOLDIER)
        if len(name_counts) == 1 and "SOLDIER" in name_counts and name_counts["SOLDIER"] == 5:
            return cls.FIVE_OF_A_KIND
        
        # Extended straight 5 (3 unique from valid group, 2 duplicates)
        if len(unique_names) == 3:
            for group in cls.STRAIGHT_GROUPS:
                if unique_names == set(group):
                    # Valid distributions: [1,1,3] or [1,2,2]
                    counts = sorted(name_counts.values())
                    if counts in [[1, 1, 3], [1, 2, 2]]:
                        return cls.EXTENDED_STRAIGHT_5
        
        return cls.INVALID
    
    @classmethod
    def _check_six_pieces(cls, name_counts: Counter) -> str:
        """Check valid plays for 6 pieces."""
        # Double straight (2 of each in low straight group)
        expected = {"CHARIOT": 2, "HORSE": 2, "CANNON": 2}
        if name_counts == expected:
            return cls.DOUBLE_STRAIGHT
        
        return cls.INVALID
    
    @classmethod
    def is_valid_play(cls, pieces: List[Piece], required_count: int = None) -> bool:
        """
        Check if a play is valid according to game rules.
        
        Args:
            pieces: List of pieces to validate
            required_count: If specified, the exact number of pieces required
            
        Returns:
            True if the play is valid
        """
        # Check piece count requirement
        if required_count is not None and len(pieces) != required_count:
            return False
        
        # Check if play type is valid
        play_type = cls.get_play_type(pieces)
        return play_type != cls.INVALID
    
    @classmethod
    def compare_plays(cls, play1: List[Piece], play2: List[Piece]) -> int:
        """
        Compare two plays to determine which is stronger.
        
        Args:
            play1: First play to compare
            play2: Second play to compare
            
        Returns:
            1 if play1 wins, -1 if play2 wins, 0 if equal
        """
        type1 = cls.get_play_type(play1)
        type2 = cls.get_play_type(play2)
        
        # Invalid plays always lose
        if type1 == cls.INVALID:
            return -1
        if type2 == cls.INVALID:
            return 1
        
        # Compare by play type priority
        priority1 = cls.PLAY_TYPE_PRIORITY.index(type1)
        priority2 = cls.PLAY_TYPE_PRIORITY.index(type2)
        
        if priority1 > priority2:
            return 1
        elif priority1 < priority2:
            return -1
        
        # Same play type - compare by highest piece value
        max1 = max(p.point for p in play1)
        max2 = max(p.point for p in play2)
        
        if max1 > max2:
            return 1
        elif max1 < max2:
            return -1
        else:
            return 0
    
    @classmethod
    def get_valid_declares(cls, player_zero_declares: int) -> List[int]:
        """
        Get valid declaration values based on player's declaration history.
        
        Args:
            player_zero_declares: Number of consecutive zero declarations
            
        Returns:
            List of valid declaration values (0-8)
        """
        base_declares = list(range(9))  # 0 through 8
        
        # Cannot declare zero more than twice in a row
        if player_zero_declares >= 2:
            return base_declares[1:]  # Remove 0
        
        return base_declares
    
    @classmethod
    def is_valid_declaration_total(cls, declarations: List[int], is_last_player: bool) -> bool:
        """
        Check if declaration total is valid.
        
        Args:
            declarations: List of all declarations so far
            is_last_player: Whether this is the last player to declare
            
        Returns:
            True if the total is valid
        """
        total = sum(declarations)
        
        # Last player cannot make total equal 8
        if is_last_player and total == 8:
            return False
        
        # Total cannot exceed 32 (4 players * 8 max)
        if total > 32:
            return False
        
        return True