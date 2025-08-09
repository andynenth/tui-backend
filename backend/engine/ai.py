# backend/engine/ai.py

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Tuple, Any, Optional, Callable

from backend.engine.rules import get_play_type, is_valid_play

# Strong combo types that starters should prefer over individual openers
STARTER_PREFERRED_COMBOS = [
    "THREE_OF_A_KIND",
    "STRAIGHT", 
    "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT",
    "FIVE_OF_A_KIND",
    "DOUBLE_STRAIGHT"
]

# ------------------------------------------------------------------
# New AI Declaration V2 Constants
# ------------------------------------------------------------------

# Strong combo types - combos that beat PAIR in hierarchy
STRONG_COMBO_TYPES = {
    "THREE_OF_A_KIND",
    "STRAIGHT", 
    "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT",
    "EXTENDED_STRAIGHT_5",
    "FIVE_OF_A_KIND",
    "DOUBLE_STRAIGHT"
}

# Threshold for PAIR to be considered strong (must exceed HORSE_RED pair value)
STRONG_PAIR_THRESHOLD = 12  # HORSE_RED + HORSE_RED = 12 points

# All combo types for reference
ALL_COMBO_TYPES = {
    "PAIR",
    "THREE_OF_A_KIND",
    "STRAIGHT", 
    "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT",
    "EXTENDED_STRAIGHT_5",
    "FIVE_OF_A_KIND",
    "DOUBLE_STRAIGHT"
}

def is_starter_preferred_combo(combo_type: str, pieces: List) -> bool:
    """
    Check if a combo is strong enough for a starter to prefer over individual openers.
    
    Args:
        combo_type: Type of combination
        pieces: List of pieces in the combo
        
    Returns:
        True if the combo should be preferred by starters
    """
    # Always preferred combo types
    if combo_type in STARTER_PREFERRED_COMBOS:
        return True
    
    # High-value pairs (ELEPHANT_BLACK is 9 points)
    if combo_type == "PAIR":
        total_value = sum(p.point for p in pieces)
        # ELEPHANT pairs = 18+ points total
        return total_value >= 18
    
    return False


# ------------------------------------------------------------------
# Strategic AI Declaration System - Data Structures
# ------------------------------------------------------------------
@dataclass
class DeclarationContext:
    """Holds all context needed for strategic declaration decisions."""
    position_in_order: int  # 0-3
    previous_declarations: List[int]  # Length 0-3
    is_starter: bool
    pile_room: int  # Calculated: 8 - sum(previous_declarations)
    field_strength: str  # "weak", "normal", "strong"
    has_general_red: bool
    opponent_patterns: Dict[str, Any]  # Analysis results


# ------------------------------------------------------------------
# Strategic Helper Functions
# ------------------------------------------------------------------
def calculate_pile_room(previous_declarations: List[int]) -> int:
    """
    Calculate maximum piles available in this round.
    
    If the sum of previous declarations exceeds 8, ignore the last declaration
    that caused the overflow.
    
    Strategic Note:
    This approach forces bots to fight against aggressive players who declare
    high values, making the game more competitive. Instead of being locked out
    (declaring 0), later position bots can still compete for piles when early
    players are overly aggressive. This creates tension between:
    - Early players: Can't just declare maximum to block others
    - Later players: Must fight for remaining piles instead of giving up
    
    Examples:
        [2, 4, 4] -> sum=10 > 8, ignore last 4 -> pile_room = 8 - (2+4) = 2
        [4, 5] -> sum=9 > 8, ignore 5 -> pile_room = 8 - 4 = 4
    
    Returns:
        int: Available pile room (0-8)
    """
    if not previous_declarations:
        return 8
    
    total_declared = sum(previous_declarations)
    
    # If total exceeds 8, ignore the last declaration that caused overflow
    if total_declared > 8:
        # Recalculate without the last declaration
        total_declared = sum(previous_declarations[:-1])
    
    return max(0, 8 - total_declared)


def assess_field_strength(previous_declarations: List[int]) -> str:
    """
    Categorize the overall field strength based on declarations.
    
    Returns:
        str: "weak", "normal", or "strong"
    """
    if not previous_declarations:
        return "normal"  # No info yet
        
    avg = sum(previous_declarations) / len(previous_declarations)
    
    if avg <= 2.0:
        return "weak"  # Opponents have poor hands
    elif avg >= 3.5:
        return "strong"  # Opponents have excellent hands
    else:
        return "normal"


def analyze_opponent_patterns(previous_declarations: List[int]) -> Dict:
    """
    Analyze what opponent declarations reveal about their hands.
    
    Returns:
        Dict with:
        - low_declarers: int (count of 0-1 declarations)
        - high_declarers: int (count of 4+ declarations)  
        - combo_opportunity: bool (might opponents play 3+ pieces?)
        - likely_singles_only: bool (all opponents playing singles?)
    """
    low_count = sum(1 for d in previous_declarations if d <= 1)
    high_count = sum(1 for d in previous_declarations if d >= 4)
    
    # If all previous players declared 0-1, they have NO combos
    likely_singles_only = (low_count == len(previous_declarations)) if previous_declarations else False
    
    # Combo opportunity exists if someone might play combos
    combo_opportunity = high_count > 0 or any(d >= 3 for d in previous_declarations)
    
    return {
        'low_declarers': low_count,
        'high_declarers': high_count,
        'combo_opportunity': combo_opportunity,
        'likely_singles_only': likely_singles_only
    }


def evaluate_opener_reliability(piece, field_strength: str) -> float:
    """
    Evaluate how reliable an opener is given field strength.
    
    Returns:
        float: Reliability score (0.0 - 1.0)
    """
    if piece.point >= 13:  # GENERAL
        return 1.0  # Always reliable
    elif piece.point >= 11:  # ADVISOR
        if field_strength == "weak":
            return 1.0  # Very reliable vs weak opponents
        elif field_strength == "normal":
            return 0.85  # Usually reliable
        else:  # strong
            return 0.7  # Might lose to GENERALs
    else:
        return 0.0  # Not an opener


def is_combo_viable_simplified(combo_type: str, pieces: List, has_opener: bool, field_strength: str) -> bool:
    """
    Simplified combo viability rules.
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
        elif combo_type in ["STRAIGHT", "FOUR_OF_A_KIND", "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND"]:
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


def filter_viable_combos(combos: List[Tuple], context: DeclarationContext, 
                        has_reliable_opener: bool) -> List[Tuple]:
    """
    Filter combos to only those that are actually playable.
    
    Args:
        combos: List of (combo_type, pieces) tuples
        context: Declaration context
        has_reliable_opener: Whether hand has 11+ point piece
        
    Returns:
        List of viable combos
    """
    viable = []
    
    for combo_type, pieces in combos:
        combo_size = len(pieces)
        
        # Check 1: Pile room constraint
        if combo_size > context.pile_room:
            continue  # Can't play if not enough room
            
        # Check 2: Playability without control
        if context.is_starter:
            # Starter always has control
            viable.append((combo_type, pieces))
        elif context.has_general_red and context.field_strength in ["weak", "normal"]:
            # GENERAL_RED in weak/normal field provides strong control
            viable.append((combo_type, pieces))
        elif has_reliable_opener and combo_size < 3:
            # Opener helps with small combos (pairs) but not large ones
            viable.append((combo_type, pieces))
        else:
            # Need opportunity from opponents
            if context.opponent_patterns['likely_singles_only']:
                # If all opponents declared 0-1, they have NO combos
                # Only small combos (pairs) might work
                if combo_size < 3:
                    viable.append((combo_type, pieces))
                # ENHANCEMENT: In weak fields, small combos more viable even without opener
                elif combo_size == 3 and context.field_strength == "weak":
                    # Three-piece combos might work in very weak fields, but need higher quality
                    total_points = sum(p.point for p in pieces)
                    if total_points >= 21:  # Higher strength requirement for no-opener scenarios
                        viable.append((combo_type, pieces))
                # Large combos (4+) still have 0% chance - opponents won't play 4+ pieces
            elif context.opponent_patterns['combo_opportunity'] and combo_size >= 3:
                # Some opponents might create opportunity
                # But consider field strength and combo quality
                total_points = sum(p.point for p in pieces)
                
                # Consider field strength and previous declarations
                if context.field_strength == "strong":
                    # Against strong opponents, need exceptional combos
                    if combo_type == "STRAIGHT" and total_points < 24:
                        continue  # Even decent straights won't win
                    elif combo_type == "THREE_OF_A_KIND" and total_points < 15:
                        continue  # Weak THREE_OF_A_KIND won't win
                else:
                    # Normal field strength
                    if combo_type == "STRAIGHT" and total_points < 21:
                        continue  # Weak straight unlikely to win
                    
                    # Special case: single opponent declared 3
                    # They likely have combos and will control turns
                    if len(context.previous_declarations) == 1 and context.previous_declarations[0] == 3:
                        # Only very strong combos have a chance
                        if combo_type == "THREE_OF_A_KIND" and total_points < 12:
                            continue  # Weak THREE_OF_A_KIND won't get opportunity
                    
                viable.append((combo_type, pieces))
    
    return viable


# ------------------------------------------------------------------
# Find all valid combinations from a hand (1 to 6 pieces per combo)
# ------------------------------------------------------------------
def find_all_valid_combos(hand):
    results = []
    for r in range(1, 7):  # Try all combination lengths from 1 to 6
        for combo in combinations(hand, r):
            pieces = list(combo)
            if is_valid_play(pieces):
                play_type = get_play_type(pieces)
                results.append((play_type, pieces))
    return results


# ------------------------------------------------------------------
# New AI Declaration V2 Helper Functions
# ------------------------------------------------------------------

def is_strong_combo(combo_type: str, pieces: List) -> bool:
    """
    Check if a combo qualifies as a strong combo.
    
    A combo is strong if:
    - It's THREE_OF_A_KIND or higher in hierarchy, OR
    - It's a PAIR with total value > 12 (HORSE_RED pair)
    
    Args:
        combo_type: Type of combo (e.g., "PAIR", "STRAIGHT")
        pieces: List of pieces in the combo
        
    Returns:
        True if combo is strong
    """
    # Combos that beat PAIR in hierarchy are always strong
    if combo_type in STRONG_COMBO_TYPES:
        return True
    
    # For PAIR, check if stronger than HORSE_RED pair
    if combo_type == "PAIR":
        total_value = sum(p.point for p in pieces)
        return total_value > STRONG_PAIR_THRESHOLD
    
    return False


def remove_pieces_from_hand(hand: List, pieces_to_remove: List) -> List:
    """
    Remove specific pieces from hand to avoid overlap in play planning.
    
    Args:
        hand: Current hand
        pieces_to_remove: Pieces to remove
        
    Returns:
        New hand with pieces removed
    """
    hand_copy = hand.copy()
    for piece in pieces_to_remove:
        if piece in hand_copy:
            hand_copy.remove(piece)
    return hand_copy


def get_piece_threshold(pile_room: int) -> int:
    """
    Get minimum piece value needed for given pile room.
    More restrictive with less room, more flexible with more room.
    
    Args:
        pile_room: Available pile slots
        
    Returns:
        Minimum piece value threshold
    """
    if pile_room <= 0:
        return float('inf')  # Impossible threshold
    elif pile_room == 1:
        return 13  # >13 (only GENERAL_RED qualifies)
    elif pile_room == 2:
        return 13  # >=13 (GENERAL_BLACK/RED)
    elif pile_room == 3:
        return 12  # >=12 (ADVISOR_RED and up)
    elif pile_room == 4:
        return 12  # >=12 (ADVISOR_RED and up)
    elif pile_room == 5:
        return 11  # >=11 (ADVISOR_BLACK and up)
    else:
        return 11  # >=11 for pile room > 5 (default to standard opener threshold)


def get_individual_strong_pieces(hand: List, pile_room: int) -> List:
    """
    Find individual pieces that meet the threshold for given pile room.
    
    Args:
        hand: Current hand
        pile_room: Available pile room
        
    Returns:
        List of qualifying pieces
    """
    threshold = get_piece_threshold(pile_room)
    
    if pile_room == 1:
        # Special case: pile room 1 requires > 13 (not >=)
        return [p for p in hand if p.point > threshold]
    else:
        return [p for p in hand if p.point >= threshold]


def fit_plays_to_pile_room(play_list: List[Dict], pile_room: int) -> List[Dict]:
    """
    Adjust play list to fit within pile room constraints.
    
    Strategy: Remove lowest value combos first, keep openers if possible.
    
    Args:
        play_list: List of planned plays
        pile_room: Maximum pieces allowed
        
    Returns:
        Adjusted play list that fits pile room
    """
    total_pieces = sum(len(play['pieces']) for play in play_list)
    
    if total_pieces <= pile_room:
        return play_list
    
    # Separate openers and combos
    openers = [p for p in play_list if p['type'] == 'opener']
    combos = [p for p in play_list if p['type'] == 'combo']
    
    # Sort combos by total value (ascending) to remove weakest first
    combos.sort(key=lambda x: sum(p.point for p in x['pieces']))
    
    # Remove combos until we fit
    while total_pieces > pile_room and combos:
        removed = combos.pop(0)  # Remove weakest combo
        total_pieces -= len(removed['pieces'])
    
    # Rebuild play list
    return openers + combos


# ------------------------------------------------------------------
# Strategic Declaration Function - NEW IMPLEMENTATION
# ------------------------------------------------------------------
def choose_declare_strategic(
    hand,
    is_first_player: bool,
    position_in_order: int,
    previous_declarations: list[int],
    must_declare_nonzero: bool,
    verbose: bool = True,
    analysis_callback: Optional[Callable] = None,
) -> int:
    """
    Simplified strategic declaration logic:
    - With opener + combo: declare 1 (control) + combo_size
    - With opener no combo: declare opener_count  
    - No opener: declare based on strong combos only
    """
    # Get bot name for logging (if available)
    bot_name = "Bot" if not hasattr(hand[0], '_bot_name') else getattr(hand[0], '_bot_name', 'Bot')
    
    print(f"\n📢 DECLARATION DECISION for position {position_in_order}")
    print(f"  Hand: {[f'{p.name}({p.point})' for p in hand]}")
    print(f"  Previous declarations: {previous_declarations}")
    print(f"  Must declare non-zero: {must_declare_nonzero}")
    
    # Phase 1: Identify openers (11+ points)
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
    
    print(f"  Openers found: {opener_count} - {[f'{p.name}({p.point})' for p in openers]}")
    print(f"  Field strength: {field_strength}")
    
    # Phase 2: Find all combos
    all_combos = find_all_valid_combos(hand)
    strong_combos = [c for c in all_combos if c[0] in {
        "PAIR", "THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND", 
        "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"
    }]
    print(f"  Found {len(strong_combos)} strong combos")
    
    # Phase 3: Filter viable combos with simplified rules
    viable_combos = []
    for combo_type, pieces in strong_combos:
        if is_combo_viable_simplified(combo_type, pieces, opener_count > 0, field_strength):
            viable_combos.append((combo_type, pieces))
    
    print(f"  Viable combos: {len(viable_combos)}")
    for combo_type, pieces in viable_combos:
        print(f"    - {combo_type}: {[f'{p.name}({p.point})' for p in pieces]}")
    
    # Phase 4: Calculate declaration with simplified logic
    print(f"\n  📊 SIMPLIFIED CALCULATION:")
    
    # Find best combo (largest that fits in 8 pieces)
    best_combo = None
    best_combo_size = 0
    
    # Check for overlap between openers and combos
    opener_pieces = set(openers)
    
    for combo_type, pieces in viable_combos:
        combo_size = len(pieces)
        combo_pieces_set = set(pieces)
        
        # Check if combo uses any opener pieces
        overlap = combo_pieces_set.intersection(opener_pieces)
        
        if overlap and opener_count > 0:
            # Combo overlaps with openers - must choose one or the other
            print(f"    Note: {combo_type} overlaps with openers: {[f'{p.name}({p.point})' for p in overlap]}")
            # For declaration, we can still count it as potential wins, just not both
            if combo_size > best_combo_size:
                best_combo = (combo_type, pieces)
                best_combo_size = combo_size
        else:
            # No overlap - can use both openers and combo
            if opener_count > 0 and (opener_count + combo_size) <= 8:
                if combo_size > best_combo_size:
                    best_combo = (combo_type, pieces)
                    best_combo_size = combo_size
            elif opener_count == 0 and combo_size <= 8:
                if combo_size > best_combo_size:
                    best_combo = (combo_type, pieces)
                    best_combo_size = combo_size
    
    # Calculate declaration
    if best_combo and opener_count > 0:
        # Check for overlap
        combo_pieces_set = set(best_combo[1])
        overlap = combo_pieces_set.intersection(opener_pieces)
        
        if overlap:
            # Must choose between openers OR combo
            # Compare: individual openers vs combo
            openers_in_combo = len(overlap)
            openers_not_in_combo = opener_count - openers_in_combo
            
            # Piles from playing combo vs playing openers separately
            combo_piles = len(best_combo[1])  # Number of pieces = piles captured
            separate_piles = opener_count  # Each opener captures 1 pile
            
            # Starters should prefer strong combos when they have control
            if is_first_player and is_starter_preferred_combo(best_combo[0], best_combo[1]):
                # Starter with strong combo should use it
                score = openers_not_in_combo + combo_piles
                print(f"    Decision: Starter prefers {best_combo[0]} ({combo_piles} piles) + {openers_not_in_combo} free openers = {score}")
            elif separate_piles >= combo_piles:
                score = separate_piles
                print(f"    Decision: {opener_count} openers separately ({separate_piles} piles) > {best_combo[0]} ({combo_piles} piles) = {score}")
            else:
                score = openers_not_in_combo + combo_piles
                print(f"    Decision: {openers_not_in_combo} free openers + {best_combo[0]} ({combo_piles} piles) = {score}")
        else:
            # No overlap - can use all openers + combo
            combo_piles = len(best_combo[1])
            score = opener_count + combo_piles  # All openers + combo piles
            print(f"    Decision: {opener_count} openers + {best_combo[0]} ({combo_piles} piles) = {score}")
    elif opener_count > 0:
        # Has opener(s) but no combo: each opener is a potential win
        score = opener_count
        print(f"    Decision: {opener_count} openers, no viable combos = {score}")
    elif best_combo:
        # No openers but has strong combo
        combo_piles = len(best_combo[1])  # Number of pieces = piles captured
        score = combo_piles
        print(f"    Decision: No openers, but {best_combo[0]} ({combo_piles} piles) = {score}")
    else:
        # Weak hand
        score = 0
        print(f"    Decision: Weak hand, no openers or combos = {score}")
    
    # Phase 4.5: Consider full hand potential (not just best combo)
    # Check if we're underestimating a strong hand
    if len(hand) >= 6 and score < len(hand):
        print(f"\n    🔍 FULL HAND EVALUATION:")
        print(f"    Current score: {score}, but have {len(hand)} pieces total")
        
        # Track which pieces are already accounted for
        accounted_pieces = set()
        
        # Add opener pieces
        accounted_pieces.update(openers)
        
        # Add best combo pieces if any
        if best_combo:
            accounted_pieces.update(best_combo[1])
        
        # Evaluate remaining pieces
        remaining_pieces = [p for p in hand if p not in accounted_pieces]
        if remaining_pieces:
            print(f"    Remaining pieces: {[f'{p.name}({p.point})' for p in remaining_pieces]}")
            
            # Don't count single pieces - only combos provide reliable wins
            strong_remaining = 0
            
            # Also check for additional combos in remaining pieces
            from backend.engine.rules import get_play_type
            additional_combos = 0
            
            # Check for pairs in remaining
            remaining_counts = {}
            for p in remaining_pieces:
                remaining_counts[p.name] = remaining_counts.get(p.name, 0) + 1
            
            for piece_name, count in remaining_counts.items():
                if count >= 2:
                    # Found a pair
                    pair_pieces = [p for p in remaining_pieces if p.name == piece_name][:2]
                    if len(pair_pieces) == 2:
                        # Check if pair is strong enough
                        pair_value = sum(p.point for p in pair_pieces)
                        if (field_strength == "weak" and pair_value >= 10) or \
                           (field_strength == "normal" and pair_value >= 14) or \
                           (field_strength == "strong" and pair_value >= 18):
                            additional_combos += 1
                            print(f"    Found viable PAIR in remaining: {[f'{p.name}({p.point})' for p in pair_pieces]}")
            
            # Update score with additional combo wins only
            additional_wins = additional_combos
            if additional_wins > 0:
                old_score = score
                
                # Add combo wins conservatively
                # Early positions can be slightly more optimistic
                if position_in_order <= 1:
                    score = min(score + additional_wins, 8)
                else:
                    # Later positions add only half to be conservative
                    score = min(score + (additional_wins // 2), 8)
                    
                print(f"    Additional combos: {additional_combos}")
                print(f"    Adjusted score: {old_score} → {score}")
    
    # Phase 5: Handle edge cases
    if score == 0 and field_strength == "weak":
        # In very weak field, might win with decent singles
        decent_singles = sum(1 for p in hand if 7 <= p.point <= 10)
        if decent_singles >= 3:
            score = 1  # Conservative estimate
    
    # Phase 8: Handle forbidden values
    forbidden_declares = set()
    
    # Last player can't make sum = 8
    if position_in_order == 3:
        total_so_far = sum(previous_declarations)
        forbidden = 8 - total_so_far
        if 0 <= forbidden <= 8:
            forbidden_declares.add(forbidden)
    
    # Must declare non-zero rule
    if must_declare_nonzero:
        forbidden_declares.add(0)
    
    # Find best valid alternative if needed
    if score in forbidden_declares:
        valid_options = [d for d in range(0, 9) if d not in forbidden_declares]
        
        # Strategy: Context-aware alternative selection
        if valid_options:
            # Assess hand strength for strategic alternative selection
            hand_strength = "strong" if opener_count >= 2 or len(viable_combos) >= 2 else "weak"
            
            if hand_strength == "strong" and score > 0:
                # Last player should be more conservative
                if position_in_order == 3:
                    # Last player: pick closest option (prefer lower)
                    score = min(valid_options, key=lambda x: abs(x - score))
                else:
                    # Non-last player with strong hand: prefer higher alternatives
                    higher_options = [opt for opt in valid_options if opt > score]
                    if higher_options:
                        score = min(higher_options)  # Closest higher option
                    else:
                        score = min(valid_options, key=lambda x: abs(x - score))
            else:
                # Weak hand or conservative approach - pick closest
                score = min(valid_options, key=lambda x: abs(x - score))
        else:
            # Shouldn't happen, but defensive
            score = 1
    
    # Phase 8b: Pile room constraint removed - declarations should be based on 
    # expected wins from hand strength, not maximum theoretical pile availability
    
    # No need for strategic caps with simplified logic
    
    # Phase 9: Debug output
    print(f"\n  🎯 FINAL DECLARATION: {score}")
    
    if verbose:
        print(f"\n🎯 STRATEGIC DECLARATION ANALYSIS")
        print(f"Position: {position_in_order} (Starter: {is_first_player})")
        print(f"Previous declarations: {previous_declarations}")
        print(f"Field strength: {field_strength}")
        print(f"Openers: {opener_count}")
        print(f"Found {len(strong_combos)} combos, {len(viable_combos)} viable")
        print(f"Final declaration: {score}")
    
    # Phase 10: Optional analysis callback
    if analysis_callback:
        analysis_data = {
            'position_in_order': position_in_order,
            'is_starter': is_first_player,
            'previous_declarations': previous_declarations,
            'field_strength': field_strength,
            'opener_count': opener_count,
            'strong_combos_found': len(strong_combos),
            'viable_combos_count': len(viable_combos),
            'final_decision': score
        }
        analysis_callback(analysis_data)
    
    return score


# ------------------------------------------------------------------
# New AI Declaration V2 Implementation
# ------------------------------------------------------------------
def choose_declare_strategic_v2(
    hand,
    is_first_player: bool,
    position_in_order: int,
    previous_declarations: list[int],
    must_declare_nonzero: bool,
    verbose: bool = True
) -> int:
    """
    New declaration logic with separate starter/non-starter strategies.
    
    Starter Strategy:
    1. Find all strong combos first
    2. Find individual strong pieces
    3. Declaration = total pieces in play list
    
    Non-Starter Strategy:
    1. Find ONE opener first for control
    2. Find strong combos from remaining pieces
    3. Find additional individual pieces
    4. Fit to pile room by removing combos if needed
    5. If no opener found, declare 0
    """
    
    play_list = []
    hand_copy = hand.copy()
    
    if verbose:
        print(f"\n📢 DECLARATION DECISION V2 for position {position_in_order}")
        print(f"  Hand: {[f'{p.name}({p.point})' for p in hand]}")
        print(f"  Previous declarations: {previous_declarations}")
        print(f"  Starter: {is_first_player}")
    
    if is_first_player:
        # =====================================================
        # STARTER LOGIC
        # =====================================================
        if verbose:
            print("\n🎯 STARTER STRATEGY:")
        
        # Step 1: Find strong combos iteratively (re-check after each combo)
        combos_found = 0
        while True:
            all_combos = find_all_valid_combos(hand_copy)
            found_combo = False
            
            for combo_type, pieces in all_combos:
                # Skip single pieces - they're not combos
                if combo_type == "SINGLE":
                    continue
                    
                if is_strong_combo(combo_type, pieces):
                    if verbose:
                        total = sum(p.point for p in pieces)
                        print(f"    Found {combo_type}: {[f'{p.name}({p.point})' for p in pieces]} (total={total})")
                    
                    # Add to play list and remove from hand
                    play_list.append({
                        'type': 'combo',
                        'combo_type': combo_type,
                        'pieces': pieces
                    })
                    hand_copy = remove_pieces_from_hand(hand_copy, pieces)
                    combos_found += 1
                    found_combo = True
                    break  # Re-scan for combos with updated hand
            
            if not found_combo:
                break  # No more strong combos found
        
        if verbose:
            print(f"  Found {combos_found} strong combos")
        
        # Step 2: Calculate pile room
        total_pieces_planned = sum(len(play['pieces']) for play in play_list)
        pile_room_left = 8 - total_pieces_planned
        
        if verbose:
            print(f"  After combos: {total_pieces_planned} pieces planned, {pile_room_left} room left")
        
        # Step 3: Find individual strong pieces
        if pile_room_left > 0:
            # Check pieces with current pile room
            strong_pieces = get_individual_strong_pieces(hand_copy, pile_room_left)
            # Sort by value descending to take best pieces first
            strong_pieces.sort(key=lambda p: p.point, reverse=True)
            
            for piece in strong_pieces:
                if pile_room_left > 0:
                    play_list.append({
                        'type': 'opener',
                        'pieces': [piece]
                    })
                    hand_copy = remove_pieces_from_hand(hand_copy, [piece])
                    pile_room_left -= 1
        
        # Calculate declaration
        declaration = sum(len(play['pieces']) for play in play_list)
        
    else:
        # =====================================================
        # NON-STARTER LOGIC
        # =====================================================
        if verbose:
            print("\n🎯 NON-STARTER STRATEGY:")
        
        # Step 1: Calculate pile room from previous declarations
        pile_room = calculate_pile_room(previous_declarations)
        if verbose:
            print(f"  Pile room available: {pile_room}")
        
        # If no pile room, cannot declare anything
        if pile_room <= 0:
            if verbose:
                print("  No pile room available - declaring 0")
            return 0
        
        # Step 2: Find ONE opener first
        opener = None
        for threshold in [13, 12, 11]:  # Try highest first
            candidates = [p for p in hand_copy if p.point >= threshold]
            if candidates:
                opener = max(candidates, key=lambda p: p.point)
                play_list.append({
                    'type': 'opener',
                    'pieces': [opener]
                })
                hand_copy = remove_pieces_from_hand(hand_copy, [opener])
                if verbose:
                    print(f"  Found opener: {opener.name}({opener.point})")
                break
        
        if not opener:
            if verbose:
                print("  No opener found - declaring 0")
            return 0
        
        # Step 3: Find all strong combos from remaining pieces
        all_combos = find_all_valid_combos(hand_copy)
        for combo_type, pieces in all_combos:
            # Skip single pieces - they're not combos
            if combo_type == "SINGLE":
                continue
            if is_strong_combo(combo_type, pieces):
                play_list.append({
                    'type': 'combo',
                    'combo_type': combo_type,
                    'pieces': pieces
                })
                hand_copy = remove_pieces_from_hand(hand_copy, pieces)
        
        # Step 4: Find additional individual strong pieces
        current_pieces = sum(len(play['pieces']) for play in play_list)
        room_left = pile_room - current_pieces
        
        if room_left > 0:
            # Check pieces with current room left
            strong_pieces = get_individual_strong_pieces(hand_copy, room_left)
            # Sort by value descending to take best pieces first
            strong_pieces.sort(key=lambda p: p.point, reverse=True)
            
            for piece in strong_pieces:
                if room_left > 0:
                    play_list.append({
                        'type': 'opener',
                        'pieces': [piece]
                    })
                    hand_copy = remove_pieces_from_hand(hand_copy, [piece])
                    room_left -= 1
        
        # Step 5: Fit to pile room if needed
        play_list = fit_plays_to_pile_room(play_list, pile_room)
        
        # Calculate declaration
        declaration = sum(len(play['pieces']) for play in play_list)
    
    # =====================================================
    # HANDLE FORBIDDEN VALUES (same for both)
    # =====================================================
    forbidden_declares = set()
    
    # Last player can't make sum = 8
    if position_in_order == 3:
        total_so_far = sum(previous_declarations)
        forbidden = 8 - total_so_far
        if 0 <= forbidden <= 8:
            forbidden_declares.add(forbidden)
    
    # Must declare non-zero rule
    if must_declare_nonzero:
        forbidden_declares.add(0)
    
    # Adjust if needed
    if declaration in forbidden_declares:
        valid_options = [d for d in range(0, 9) if d not in forbidden_declares]
        if valid_options:
            # Pick closest valid option
            declaration = min(valid_options, key=lambda x: abs(x - declaration))
    
    if verbose:
        print(f"\n🎯 FINAL DECLARATION: {declaration}")
        print(f"  Play list has {len(play_list)} plays:")
        for play in play_list:
            if play['type'] == 'combo':
                print(f"    - {play['combo_type']}: {[f'{p.name}({p.point})' for p in play['pieces']]}")
            else:
                print(f"    - Opener: {play['pieces'][0].name}({play['pieces'][0].point})")
    
    return declaration


# ------------------------------------------------------------------
# Decide how many piles the bot should declare at the start of a round
# ------------------------------------------------------------------
def choose_declare(
    hand,
    is_first_player: bool,
    position_in_order: int,
    previous_declarations: list[int],
    must_declare_nonzero: bool,
    verbose: bool = True,
    analysis_callback: Optional[Callable] = None,
) -> int:
    """
    Main declaration function - now uses strategic implementation.
    Maintains backward compatibility with existing API.
    """
    return choose_declare_strategic(
        hand=hand,
        is_first_player=is_first_player,
        position_in_order=position_in_order,
        previous_declarations=previous_declarations,
        must_declare_nonzero=must_declare_nonzero,
        verbose=verbose,
        analysis_callback=analysis_callback
    )


# ------------------------------------------------------------------
# Utility function to check if all pieces in a play exist in hand
# (helps prevent using pieces not actually in the player's hand)
# ------------------------------------------------------------------
def pieces_exist_in_hand(play, hand):
    play_counts = Counter(play)
    hand_counts = Counter(hand)
    return all(play_counts[p] <= hand_counts[p] for p in play)


# ------------------------------------------------------------------
# Choose the best play (set of 1–6 pieces) based on total point value
# ------------------------------------------------------------------
def choose_best_play(hand: list, required_count, verbose: bool = True) -> list:
    best_play = None
    best_score = -1
    best_type = None

    # Determine which sizes of combinations to check
    play_sizes = [required_count] if required_count else range(1, 7)

    for r in play_sizes:
        for combo in combinations(hand, r):
            pieces = list(combo)
            if required_count and len(pieces) != required_count:
                continue  # Skip if the size does not match required count
            if is_valid_play(pieces):
                total = sum(p.point for p in pieces)
                if total > best_score:
                    best_score = total
                    best_play = pieces
                    best_type = get_play_type(pieces)

    # Return best found play
    if best_play:
        if verbose:
            summary = ", ".join(p.name for p in best_play)
            print(f"🤖 BOT chooses to play {best_type} ({best_score} pts): {summary}")
        return best_play

    # Fallback: discard lowest-point pieces if no valid play
    fallback = sorted(hand, key=lambda p: p.point)[: required_count or 1]
    if verbose:
        summary = ", ".join(p.name for p in fallback)
        print(f"🤖 BOT has no valid play. Discards lowest pieces: {summary}")
        print(f"    🔍 Final play: {[p.name for p in fallback]}")
        print(f"    🧠 Hand left: {[p.name for p in hand]}")

    return fallback


# ------------------------------------------------------------------
# Strategic Turn Play with Import Fallback
# ------------------------------------------------------------------
def choose_strategic_play_safe(hand: list, context, verbose: bool = True) -> list:
    """
    Safe wrapper for strategic play that falls back to basic AI if needed.
    
    Args:
        hand: List of pieces in player's hand
        context: TurnPlayContext object (or None for fallback)
        verbose: Whether to print debug info
        
    Returns:
        List of pieces to play
    """
    try:
        # Try to import and use strategic play
        from backend.engine.ai_turn_strategy import choose_strategic_play
        if context and hasattr(context, 'my_name'):
            print(f"🤖 Strategic AI wrapper called for {context.my_name}")
        return choose_strategic_play(hand, context)
    except ImportError:
        # Fallback to basic AI if strategic module not available
        if verbose:
            print("⚠️ Strategic AI module not available, using basic AI")
        
        # Extract required_piece_count from context if available
        required_count = None
        if context and hasattr(context, 'required_piece_count'):
            required_count = context.required_piece_count
            
        return choose_best_play(hand, required_count, verbose)
    except Exception as e:
        # Any other error, fall back to basic AI
        if verbose:
            print(f"⚠️ Error in strategic AI: {e}, using basic AI")
            
        # Extract required_piece_count from context if available
        required_count = None
        if context and hasattr(context, 'required_piece_count'):
            required_count = context.required_piece_count
            
        return choose_best_play(hand, required_count, verbose)
