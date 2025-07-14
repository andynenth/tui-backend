# backend/engine/rules.py
# ------------------------------
# Available Play Types
# ------------------------------
# SINGLE              → 1 piece
# PAIR                → 2 of the same name and color
# THREE_OF_A_KIND     → 3 SOLDIERs of the same color
# STRAIGHT            → 3 of a valid group (GENERAL–ELEPHANT or CHARIOT–CANNON), same color
# FOUR_OF_A_KIND      → 4 SOLDIERs of the same color
# EXTENDED_STRAIGHT   → 4 of a valid group, same color, with 1 duplicate (e.g., 2 HORSEs)
# EXTENDED_STRAIGHT_5 → 5 of a valid group, same color, with 2 duplicates (3 unique names only)
# FIVE_OF_A_KIND      → 5 SOLDIERs of the same color
# DOUBLE_STRAIGHT     → 2 CHARIOTs, 2 HORSEs, 2 CANNONs (same color)

from collections import Counter

# -------------------------------------------------
# Priority order of play types (used for comparison)
# Higher index = stronger hand
# -------------------------------------------------
PLAY_TYPE_PRIORITY = [
    "SINGLE",
    "PAIR",
    "THREE_OF_A_KIND",
    "STRAIGHT",
    "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT",
    "EXTENDED_STRAIGHT_5",
    "FIVE_OF_A_KIND",
    "DOUBLE_STRAIGHT",
]


# -------------------------------------------------
# Determine the type of a given play
# -------------------------------------------------
def get_play_type(pieces):
    """
    Determine the type of play from a list of pieces.
    
    Analyzes the combination of pieces to identify valid play types
    according to game rules.
    
    Args:
        pieces: List of Piece objects to analyze
        
    Returns:
        str: One of: 'SINGLE', 'PAIR', 'THREE_OF_A_KIND', 'STRAIGHT',
             'FOUR_OF_A_KIND', 'EXTENDED_STRAIGHT', 'FIVE_OF_A_KIND',
             'EXTENDED_STRAIGHT_5', 'DOUBLE_STRAIGHT', or 'INVALID'
    """
    if len(pieces) == 1:
        return "SINGLE"
    if len(pieces) == 2 and is_pair(pieces):
        return "PAIR"
    if len(pieces) == 3:
        if is_three_of_a_kind(pieces):
            return "THREE_OF_A_KIND"
        elif is_straight(pieces):
            return "STRAIGHT"
    if len(pieces) == 4:
        if is_four_of_a_kind(pieces):
            return "FOUR_OF_A_KIND"
        elif is_extended_straight(pieces):
            return "EXTENDED_STRAIGHT"
    if len(pieces) == 5:
        if is_five_of_a_kind(pieces):
            return "FIVE_OF_A_KIND"
        elif is_extended_straight_5(pieces):
            return "EXTENDED_STRAIGHT_5"
    if len(pieces) == 6 and is_double_straight(pieces):
        return "DOUBLE_STRAIGHT"

    return "INVALID"


# -------------------------------------------------
# Check if the play is valid
# -------------------------------------------------
def is_valid_play(pieces):
    """
    Check if a combination of pieces forms a valid play.
    
    A play is valid if it matches one of the recognized play types
    in the game rules.
    
    Args:
        pieces: List of Piece objects to validate
        
    Returns:
        bool: True if the play is valid, False otherwise
    """
    return get_play_type(pieces) != "INVALID"


# -------------------------------------------------
# Validation functions for each type
# -------------------------------------------------


def is_pair(pieces):
    """
    Check if two pieces form a valid pair (same name and color).
    
    Args:
        pieces: List of exactly 2 Piece objects
        
    Returns:
        bool: True if pieces form a pair, False otherwise
    """
    return pieces[0].name == pieces[1].name and pieces[0].color == pieces[1].color


def is_three_of_a_kind(pieces):
    """
    Check if three pieces form a valid three-of-a-kind (all soldiers of same color).
    
    Args:
        pieces: List of exactly 3 Piece objects
        
    Returns:
        bool: True if pieces form three-of-a-kind, False otherwise
    """
    return all(p.name == "SOLDIER" and p.color == pieces[0].color for p in pieces)


def is_straight(pieces):
    """
    Check if three pieces form a valid straight.
    
    Valid straights are:
    - GENERAL, ADVISOR, ELEPHANT (same color)
    - CHARIOT, HORSE, CANNON (same color)
    
    Args:
        pieces: List of exactly 3 Piece objects
        
    Returns:
        bool: True if pieces form a straight, False otherwise
    """
    names = [p.name for p in pieces]
    valid_groups = [{"GENERAL", "ADVISOR", "ELEPHANT"}, {"CHARIOT", "HORSE", "CANNON"}]
    return all(p.color == pieces[0].color for p in pieces) and any(
        set(names) == group for group in valid_groups
    )


def is_four_of_a_kind(pieces):
    """
    Check if four pieces form a valid four-of-a-kind (all soldiers of same color).
    
    Args:
        pieces: List of exactly 4 Piece objects
        
    Returns:
        bool: True if pieces form four-of-a-kind, False otherwise
    """
    return all(p.name == "SOLDIER" and p.color == pieces[0].color for p in pieces)


def is_extended_straight(pieces):
    """
    Check if four pieces form a valid extended straight.
    
    An extended straight requires:
    - 4 pieces from the same group (GENERAL-ADVISOR-ELEPHANT or CHARIOT-HORSE-CANNON)
    - All pieces must be the same color
    - Exactly one piece type must be duplicated (e.g., 2 HORSEs, 1 CHARIOT, 1 CANNON)
    
    Args:
        pieces: List of exactly 4 Piece objects
        
    Returns:
        bool: True if pieces form an extended straight, False otherwise
    """
    color = pieces[0].color
    names = [p.name for p in pieces]
    counter = Counter(names)

    for group in [{"GENERAL", "ADVISOR", "ELEPHANT"}, {"CHARIOT", "HORSE", "CANNON"}]:
        if all(n in group for n in names) and all(p.color == color for p in pieces):
            if any(v == 2 for v in counter.values()):  # Must have a duplicate
                return True
    return False


def is_extended_straight_5(pieces):
    """
    Check if five pieces form a valid 5-piece extended straight.
    
    A 5-piece extended straight requires:
    - 5 pieces from a valid group (GENERAL-ADVISOR-ELEPHANT or CHARIOT-HORSE-CANNON)
    - All pieces must be the same color
    - Exactly two piece types must be duplicated
    - Distribution must be 2-2-1 (e.g., 2 HORSEs, 2 CANNONs, 1 CHARIOT)
    
    Args:
        pieces: List of exactly 5 Piece objects
        
    Returns:
        bool: True if pieces form a 5-piece extended straight, False otherwise
    """
    if len(pieces) != 5:
        return False

    color = pieces[0].color
    names = [p.name for p in pieces]
    counter = Counter(names)
    name_set = set(names)

    valid_groups = [{"GENERAL", "ADVISOR", "ELEPHANT"}, {"CHARIOT", "HORSE", "CANNON"}]

    return (
        all(p.color == color for p in pieces)
        and any(name_set.issubset(group) for group in valid_groups)
        and sorted(counter.values()) == [1, 2, 2]  # Exactly two duplicated piece types
    )


def is_five_of_a_kind(pieces):
    """
    Check if five pieces form a valid five-of-a-kind.
    
    All five pieces must be SOLDIERs of the same color.
    
    Args:
        pieces: List of exactly 5 Piece objects
        
    Returns:
        bool: True if pieces form five-of-a-kind, False otherwise
    """
    return all(p.name == "SOLDIER" and p.color == pieces[0].color for p in pieces)


def is_double_straight(pieces):
    """
    Check if six pieces form a valid double straight.
    
    A double straight is the strongest play type and requires:
    - Exactly 6 pieces
    - 2 CHARIOTs, 2 HORSEs, 2 CANNONs
    - All pieces must be the same color
    
    Args:
        pieces: List of Piece objects (should be exactly 6)
        
    Returns:
        bool: True if pieces form a double straight, False otherwise
    """
    if len(pieces) != 6:
        return False

    if not all(p.color == pieces[0].color for p in pieces):
        return False

    names = [p.name for p in pieces]
    counter = Counter(names)
    return set(counter.keys()) == {"CHARIOT", "HORSE", "CANNON"} and all(
        v == 2 for v in counter.values()
    )


# -------------------------------------------------
# Compare two plays of the same type
# -------------------------------------------------


def compare_plays(p1, p2):
    """
    Compare two plays to determine which is stronger.
    
    Compares plays based on type priority and piece values.
    Different play types have different comparison rules.
    
    For EXTENDED_STRAIGHT and EXTENDED_STRAIGHT_5, compares only
    the top 3 highest-value unique piece types. For other types,
    compares total point values.
    
    Args:
        p1: First list of Piece objects
        p2: Second list of Piece objects
        
    Returns:
        int: 1 if p1 wins, 2 if p2 wins, 0 if tie, -1 if invalid comparison
    """

    type1 = get_play_type(p1)
    type2 = get_play_type(p2)

    if type1 != type2:
        return -1  # Cannot compare different play types

    if type1 in ["EXTENDED_STRAIGHT", "EXTENDED_STRAIGHT_5"]:
        # Compare based only on top 3 highest-value unique piece types
        def core_sum(pieces):
            names_seen = set()
            total = 0
            for p in sorted(pieces, key=lambda x: -x.point):
                if p.name not in names_seen:
                    names_seen.add(p.name)
                    total += p.point
                if len(names_seen) == 3:
                    break
            return total

        sum1 = core_sum(p1)
        sum2 = core_sum(p2)
    else:
        # Other types: compare total point values
        sum1 = sum(p.point for p in p1)
        sum2 = sum(p.point for p in p2)

    if sum1 > sum2:
        return 1
    elif sum2 > sum1:
        return 2
    else:
        return 0


# -------------------------------------------------
# Determine valid declaration options for a player
# -------------------------------------------------


def get_valid_declares(player, declared_total, is_last):
    """
    Determine valid declaration values for a player.
    
    Enforces game rules for pile declarations:
    - Players can declare 0-8 piles they plan to win
    - Total sum of all declarations must NOT equal exactly 8
    - If a player declared 0 for 2 consecutive rounds, they must declare ≥1
    
    Args:
        player: Player object (or hand for simplified version)
        declared_total: Sum of declarations made by other players
        is_last: Whether this is the last player to declare
        
    Returns:
        list: Valid declaration values the player can choose
    """
    max_pile = 8
    options = list(range(0, max_pile + 1))

    if is_last:
        # Prevent total from equaling exactly 8
        forbidden = 8 - declared_total
        if forbidden in options:
            options.remove(forbidden)

    if player.zero_declares_in_a_row >= 2:
        # Force player to choose at least 1 if they declared 0 for 2 consecutive rounds
        options = [i for i in options if i > 0]

    return options
