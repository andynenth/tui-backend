"""
GameRules domain service - encapsulates game rules and validation logic.

This is a pure domain service with no infrastructure dependencies.
All methods are stateless and work with domain entities/value objects.
"""

from typing import List, Set, Dict, Optional
from collections import Counter

from domain.value_objects.piece import Piece
from domain.entities.player import Player


class PlayType:
    """Enumeration of valid play types in order of strength."""
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
    PRIORITY_ORDER = [
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


class GameRules:
    """
    Domain service for game rules and validation.
    
    This service encapsulates all game rules including:
    - Play type identification
    - Play validation
    - Play comparison
    - Declaration rules
    - Weak hand detection
    """
    
    # Valid straight groups
    STRAIGHT_GROUP_1 = {"GENERAL", "ADVISOR", "ELEPHANT"}
    STRAIGHT_GROUP_2 = {"CHARIOT", "HORSE", "CANNON"}
    
    @staticmethod
    def identify_play_type(pieces: List[Piece]) -> str:
        """
        Identify the type of play from a list of pieces.
        
        Args:
            pieces: List of Piece objects to analyze
            
        Returns:
            PlayType constant (e.g., PlayType.PAIR, PlayType.STRAIGHT)
        """
        count = len(pieces)
        
        if count == 1:
            return PlayType.SINGLE
        
        if count == 2 and GameRules._is_pair(pieces):
            return PlayType.PAIR
        
        if count == 3:
            if GameRules._is_three_of_a_kind(pieces):
                return PlayType.THREE_OF_A_KIND
            elif GameRules._is_straight(pieces):
                return PlayType.STRAIGHT
        
        if count == 4:
            if GameRules._is_four_of_a_kind(pieces):
                return PlayType.FOUR_OF_A_KIND
            elif GameRules._is_extended_straight(pieces):
                return PlayType.EXTENDED_STRAIGHT
        
        if count == 5:
            if GameRules._is_five_of_a_kind(pieces):
                return PlayType.FIVE_OF_A_KIND
            elif GameRules._is_extended_straight_5(pieces):
                return PlayType.EXTENDED_STRAIGHT_5
        
        if count == 6 and GameRules._is_double_straight(pieces):
            return PlayType.DOUBLE_STRAIGHT
        
        return PlayType.INVALID
    
    @staticmethod
    def is_valid_play(pieces: List[Piece]) -> bool:
        """Check if a combination of pieces forms a valid play."""
        return GameRules.identify_play_type(pieces) != PlayType.INVALID
    
    @staticmethod
    def _is_pair(pieces: List[Piece]) -> bool:
        """Check if two pieces form a valid pair."""
        if len(pieces) != 2:
            return False
        p1, p2 = pieces
        # Extract name and color from piece kind (e.g., "GENERAL_RED" -> "GENERAL", "RED")
        name1, color1 = p1.kind.rsplit('_', 1)
        name2, color2 = p2.kind.rsplit('_', 1)
        return name1 == name2 and color1 == color2
    
    @staticmethod
    def _is_three_of_a_kind(pieces: List[Piece]) -> bool:
        """Check if three pieces form a valid three-of-a-kind."""
        if len(pieces) != 3:
            return False
        
        names_colors = [p.kind.rsplit('_', 1) for p in pieces]
        names = [nc[0] for nc in names_colors]
        colors = [nc[1] for nc in names_colors]
        
        # All must be SOLDIERs of the same color
        return all(name == "SOLDIER" for name in names) and len(set(colors)) == 1
    
    @staticmethod
    def _is_straight(pieces: List[Piece]) -> bool:
        """Check if three pieces form a valid straight."""
        if len(pieces) != 3:
            return False
        
        names_colors = [p.kind.rsplit('_', 1) for p in pieces]
        names = set(nc[0] for nc in names_colors)
        colors = [nc[1] for nc in names_colors]
        
        # All same color and valid group
        return (len(set(colors)) == 1 and 
                (names == GameRules.STRAIGHT_GROUP_1 or names == GameRules.STRAIGHT_GROUP_2))
    
    @staticmethod
    def _is_four_of_a_kind(pieces: List[Piece]) -> bool:
        """Check if four pieces form a valid four-of-a-kind."""
        if len(pieces) != 4:
            return False
        
        names_colors = [p.kind.rsplit('_', 1) for p in pieces]
        names = [nc[0] for nc in names_colors]
        colors = [nc[1] for nc in names_colors]
        
        # All must be SOLDIERs of the same color
        return all(name == "SOLDIER" for name in names) and len(set(colors)) == 1
    
    @staticmethod
    def _is_extended_straight(pieces: List[Piece]) -> bool:
        """Check if four pieces form a valid extended straight."""
        if len(pieces) != 4:
            return False
        
        names_colors = [p.kind.rsplit('_', 1) for p in pieces]
        names = [nc[0] for nc in names_colors]
        colors = [nc[1] for nc in names_colors]
        
        # All same color
        if len(set(colors)) != 1:
            return False
        
        # Check if all names are from same group
        name_set = set(names)
        if not (name_set.issubset(GameRules.STRAIGHT_GROUP_1) or 
                name_set.issubset(GameRules.STRAIGHT_GROUP_2)):
            return False
        
        # Must have exactly 3 unique names with distribution [1, 1, 2]
        counter = Counter(names)
        return len(counter) == 3 and sorted(counter.values()) == [1, 1, 2]
    
    @staticmethod
    def _is_extended_straight_5(pieces: List[Piece]) -> bool:
        """Check if five pieces form a valid 5-piece extended straight."""
        if len(pieces) != 5:
            return False
        
        names_colors = [p.kind.rsplit('_', 1) for p in pieces]
        names = [nc[0] for nc in names_colors]
        colors = [nc[1] for nc in names_colors]
        
        # All same color
        if len(set(colors)) != 1:
            return False
        
        # Check if all names are from same group
        name_set = set(names)
        if not (name_set.issubset(GameRules.STRAIGHT_GROUP_1) or 
                name_set.issubset(GameRules.STRAIGHT_GROUP_2)):
            return False
        
        # Must have exactly 3 unique names with distribution [1, 2, 2]
        counter = Counter(names)
        return len(counter) == 3 and sorted(counter.values()) == [1, 2, 2]
    
    @staticmethod
    def _is_five_of_a_kind(pieces: List[Piece]) -> bool:
        """Check if five pieces form a valid five-of-a-kind."""
        if len(pieces) != 5:
            return False
        
        names_colors = [p.kind.rsplit('_', 1) for p in pieces]
        names = [nc[0] for nc in names_colors]
        colors = [nc[1] for nc in names_colors]
        
        # All must be SOLDIERs of the same color
        return all(name == "SOLDIER" for name in names) and len(set(colors)) == 1
    
    @staticmethod
    def _is_double_straight(pieces: List[Piece]) -> bool:
        """Check if six pieces form a valid double straight."""
        if len(pieces) != 6:
            return False
        
        names_colors = [p.kind.rsplit('_', 1) for p in pieces]
        names = [nc[0] for nc in names_colors]
        colors = [nc[1] for nc in names_colors]
        
        # All same color
        if len(set(colors)) != 1:
            return False
        
        # Must have exactly 2 of each: CHARIOT, HORSE, CANNON
        counter = Counter(names)
        return (set(counter.keys()) == {"CHARIOT", "HORSE", "CANNON"} and 
                all(count == 2 for count in counter.values()))
    
    @staticmethod
    def compare_plays(play1: List[Piece], play2: List[Piece]) -> int:
        """
        Compare two plays to determine which is stronger.
        
        Args:
            play1: First list of Piece objects
            play2: Second list of Piece objects
            
        Returns:
            1 if play1 wins, 2 if play2 wins, 0 if tie, -1 if invalid comparison
        """
        type1 = GameRules.identify_play_type(play1)
        type2 = GameRules.identify_play_type(play2)
        
        # Cannot compare different play types
        if type1 != type2:
            return -1
        
        # Invalid plays cannot be compared
        if type1 == PlayType.INVALID:
            return -1
        
        # Special comparison for extended straights
        if type1 in [PlayType.EXTENDED_STRAIGHT, PlayType.EXTENDED_STRAIGHT_5]:
            sum1 = GameRules._core_sum(play1)
            sum2 = GameRules._core_sum(play2)
        else:
            # Standard comparison: total point values
            sum1 = sum(p.point for p in play1)
            sum2 = sum(p.point for p in play2)
        
        if sum1 > sum2:
            return 1
        elif sum2 > sum1:
            return 2
        else:
            return 0
    
    @staticmethod
    def _core_sum(pieces: List[Piece]) -> int:
        """
        Calculate core sum for extended straights.
        
        Only counts the top 3 highest-value unique piece types.
        """
        seen_kinds = set()
        total = 0
        
        # Sort by point value (descending)
        for piece in sorted(pieces, key=lambda p: p.point, reverse=True):
            name = piece.kind.rsplit('_', 1)[0]
            if name not in seen_kinds:
                seen_kinds.add(name)
                total += piece.point
                if len(seen_kinds) == 3:
                    break
        
        return total
    
    @staticmethod
    def get_valid_declarations(
        player: Player,
        declared_total: int,
        is_last_to_declare: bool
    ) -> List[int]:
        """
        Get valid declaration values for a player.
        
        Rules:
        - Players can declare 0-8 piles
        - Total of all declarations must NOT equal 8
        - If declared 0 for 2 consecutive rounds, must declare at least 1
        
        Args:
            player: Player making the declaration
            declared_total: Sum of declarations made by other players
            is_last_to_declare: Whether this is the last player to declare
            
        Returns:
            List of valid declaration values
        """
        options = list(range(0, 9))  # 0 through 8
        
        # Last player cannot make total equal 8
        if is_last_to_declare:
            forbidden = 8 - declared_total
            if 0 <= forbidden <= 8 and forbidden in options:
                options.remove(forbidden)
        
        # Force non-zero if player has declared 0 twice in a row
        if player.stats.zero_declares_in_a_row >= 2:
            options = [opt for opt in options if opt > 0]
        
        return options
    
    @staticmethod
    def has_weak_hand(pieces: List[Piece]) -> bool:
        """
        Check if a hand is weak (no piece worth more than 9 points).
        
        Args:
            pieces: List of pieces in the hand
            
        Returns:
            True if hand is weak, False otherwise
        """
        return all(piece.point <= 9 for piece in pieces)
    
    @staticmethod
    def calculate_hand_strength(pieces: List[Piece]) -> int:
        """Calculate total point value of a hand."""
        return sum(piece.point for piece in pieces)
    
    @staticmethod
    def is_play_type_stronger(type1: str, type2: str) -> bool:
        """
        Check if type1 is stronger than type2.
        
        Args:
            type1: First play type
            type2: Second play type
            
        Returns:
            True if type1 is stronger, False otherwise
        """
        try:
            index1 = PlayType.PRIORITY_ORDER.index(type1)
            index2 = PlayType.PRIORITY_ORDER.index(type2)
            return index1 > index2
        except ValueError:
            return False