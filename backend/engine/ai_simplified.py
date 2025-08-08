# backend/engine/ai_simplified.py
"""
Simplified AI declaration logic that better matches actual game strategy.
Key principle: Openers provide control to play combos, or are individual wins without combos.
"""

from typing import List, Tuple
from backend.engine.piece import Piece
from backend.engine.rules import get_play_type, is_valid_play


def find_valid_combos(hand: List[Piece]) -> List[Tuple[str, List[Piece]]]:
    """Find all valid multi-piece combinations in hand."""
    combos = []
    
    # Check pairs
    for i in range(len(hand)):
        for j in range(i + 1, len(hand)):
            pieces = [hand[i], hand[j]]
            if is_valid_play(pieces):
                play_type = get_play_type(pieces)
                if play_type == "PAIR":
                    combos.append((play_type, pieces))
    
    # Check three of a kind
    for i in range(len(hand)):
        for j in range(i + 1, len(hand)):
            for k in range(j + 1, len(hand)):
                pieces = [hand[i], hand[j], hand[k]]
                if is_valid_play(pieces):
                    play_type = get_play_type(pieces)
                    if play_type in ["THREE_OF_A_KIND", "STRAIGHT"]:
                        combos.append((play_type, pieces))
    
    # Could add 4+ piece combos here if needed
    
    return combos


def is_combo_viable_simple(combo_type: str, pieces: List[Piece], has_opener: bool, field_strength: str) -> bool:
    """
    Determine if a combo is viable with simplified rules.
    Key insight: Having an opener dramatically increases combo viability.
    """
    total_points = sum(p.point for p in pieces)
    
    if has_opener:
        # With opener control, most combos are viable
        if combo_type == "PAIR":
            # In weak field, any pair works. In normal field, need decent pair
            if field_strength == "weak":
                return True
            else:
                return total_points >= 10  # HORSE pair (5+5) or better
        elif combo_type == "THREE_OF_A_KIND":
            return True  # Any THREE_OF_A_KIND works with opener control
        elif combo_type in ["STRAIGHT", "FOUR_OF_A_KIND", "EXTENDED_STRAIGHT"]:
            return True  # Strong combos always viable with control
    else:
        # Without opener control, need exceptional combos
        if combo_type == "PAIR":
            return total_points >= 18  # ELEPHANT pair or better
        elif combo_type == "THREE_OF_A_KIND":
            return total_points >= 12  # Average 4+ per piece
        elif combo_type in ["STRAIGHT", "FOUR_OF_A_KIND"]:
            return total_points >= 20  # Strong straight/four
            
    return False


def choose_declare_simplified(
    hand: List[Piece],
    position_in_order: int,
    previous_declarations: List[int],
    must_declare_nonzero: bool = False,
    verbose: bool = True
) -> int:
    """
    Simplified declaration logic:
    1. If has opener(s) + combo: declare 1 (control) + combo_size
    2. If has opener(s) no combo: declare opener_count
    3. If no opener: declare based on strong combos only
    """
    # Identify openers (11+ points)
    openers = [p for p in hand if p.point >= 11]
    opener_count = len(openers)
    
    # Assess field strength
    if not previous_declarations:
        field_strength = "normal"
    else:
        avg = sum(previous_declarations) / len(previous_declarations)
        if avg <= 1.5:
            field_strength = "weak"
        elif avg >= 3.0:
            field_strength = "strong"
        else:
            field_strength = "normal"
    
    if verbose:
        print(f"\n📢 SIMPLIFIED DECLARATION LOGIC")
        print(f"  Hand: {[f'{p.name}({p.point})' for p in hand]}")
        print(f"  Openers found: {opener_count} - {[f'{p.name}({p.point})' for p in openers]}")
        print(f"  Field strength: {field_strength}")
    
    # Find all combos
    all_combos = find_valid_combos(hand)
    
    # Filter for viable combos
    viable_combos = []
    for combo_type, pieces in all_combos:
        if is_combo_viable_simple(combo_type, pieces, opener_count > 0, field_strength):
            viable_combos.append((combo_type, pieces))
    
    if verbose:
        print(f"  Viable combos: {len(viable_combos)}")
        for combo_type, pieces in viable_combos:
            print(f"    - {combo_type}: {[f'{p.name}({p.point})' for p in pieces]}")
    
    # Find best combo (largest that fits in 8 pieces)
    best_combo = None
    best_combo_size = 0
    
    for combo_type, pieces in viable_combos:
        combo_size = len(pieces)
        # Check if we can fit opener + combo in 8 pieces
        if opener_count > 0 and (1 + combo_size) <= 8:
            if combo_size > best_combo_size:
                best_combo = (combo_type, pieces)
                best_combo_size = combo_size
        elif opener_count == 0 and combo_size <= 8:
            if combo_size > best_combo_size:
                best_combo = (combo_type, pieces)
                best_combo_size = combo_size
    
    # Calculate declaration
    if best_combo and opener_count > 0:
        # Has opener(s) + combo: declare 1 (control) + combo_size
        declaration = 1 + best_combo_size
        if verbose:
            print(f"  Decision: Opener control (1) + {best_combo[0]} ({best_combo_size}) = {declaration}")
    elif opener_count > 0:
        # Has opener(s) but no combo: each opener is a potential win
        declaration = opener_count
        if verbose:
            print(f"  Decision: {opener_count} openers, no viable combos = {declaration}")
    elif best_combo:
        # No openers but has strong combo
        declaration = best_combo_size
        if verbose:
            print(f"  Decision: No openers, but {best_combo[0]} ({best_combo_size}) = {declaration}")
    else:
        # Weak hand
        declaration = 0
        if verbose:
            print(f"  Decision: Weak hand, no openers or combos = {declaration}")
    
    # Handle forbidden values
    if position_in_order == 3:  # Last player
        total_so_far = sum(previous_declarations)
        if declaration == 8 - total_so_far:
            # Can't make sum = 8
            if declaration > 0:
                declaration = declaration - 1
            else:
                declaration = 1
    
    if must_declare_nonzero and declaration == 0:
        declaration = 1
    
    if verbose:
        print(f"  FINAL DECLARATION: {declaration}")
    
    return declaration


def test_simplified_logic():
    """Test the simplified logic with Round 1 hands."""
    print("="*60)
    print("TESTING SIMPLIFIED DECLARATION LOGIC")
    print("="*60)
    
    # Bot 2's hand
    bot2_hand = [
        Piece("CHARIOT_BLACK"),     # 7
        Piece("ADVISOR_BLACK"),     # 11 - opener
        Piece("SOLDIER_RED"),       # 2
        Piece("SOLDIER_RED"),       # 2
        Piece("SOLDIER_RED"),       # 2
        Piece("CANNON_RED"),        # 4
        Piece("CHARIOT_RED"),       # 8
        Piece("ADVISOR_RED")        # 12 - opener
    ]
    
    print("\nBot 2 test:")
    result = choose_declare_simplified(bot2_hand, 1, [3], verbose=True)
    print(f"Expected: 4, Got: {result}")
    
    # Bot 3's hand
    bot3_hand = [
        Piece("SOLDIER_BLACK"),     # 1
        Piece("HORSE_BLACK"),       # 5
        Piece("HORSE_BLACK"),       # 5
        Piece("ELEPHANT_BLACK"),    # 9
        Piece("GENERAL_BLACK"),     # 13 - opener
        Piece("HORSE_RED"),         # 6
        Piece("CHARIOT_RED"),       # 8
        Piece("ELEPHANT_RED")       # 10
    ]
    
    print("\nBot 3 test:")
    result = choose_declare_simplified(bot3_hand, 2, [3, 2], verbose=True)
    print(f"Expected: 3 (or 1 if pair not viable), Got: {result}")
    
    # Bot 4's hand
    bot4_hand = [
        Piece("SOLDIER_BLACK"),     # 1
        Piece("SOLDIER_BLACK"),     # 1
        Piece("CANNON_BLACK"),      # 3
        Piece("CHARIOT_BLACK"),     # 7
        Piece("ELEPHANT_BLACK"),    # 9
        Piece("ADVISOR_BLACK"),     # 11 - opener
        Piece("SOLDIER_RED"),       # 2
        Piece("SOLDIER_RED")        # 2
    ]
    
    print("\nBot 4 test:")
    result = choose_declare_simplified(bot4_hand, 3, [3, 2, 1], verbose=True)
    print(f"Expected: 0 or 1, Got: {result}")


if __name__ == "__main__":
    test_simplified_logic()