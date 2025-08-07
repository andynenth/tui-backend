# backend/engine/ai.py

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Tuple, Any, Optional, Callable

from backend.engine.rules import get_play_type, is_valid_play


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
    
    Returns:
        int: Available pile room (0-8)
    """
    total_declared = sum(previous_declarations)
    # Handle edge case where sum > 8 (shouldn't happen but defensive)
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
    
    if avg <= 1.0:
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
    Strategic declaration logic implementing all principles from strategy guide.
    """
    # Phase 1: Build context
    context = DeclarationContext(
        position_in_order=position_in_order,
        previous_declarations=previous_declarations,
        is_starter=is_first_player,
        pile_room=calculate_pile_room(previous_declarations),
        field_strength=assess_field_strength(previous_declarations),
        has_general_red=any(p.name == "GENERAL" and p.point == 14 for p in hand),
        opponent_patterns=analyze_opponent_patterns(previous_declarations)
    )
    
    # Phase 2: Find and filter combos
    all_combos = find_all_valid_combos(hand)
    strong_combos = [c for c in all_combos if c[0] in {
        "THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND", 
        "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"
    }]
    
    # Remove overlapping THREE_OF_A_KIND if FOUR_OF_A_KIND or FIVE_OF_A_KIND exists
    has_four_kind = any(c[0] == "FOUR_OF_A_KIND" for c in strong_combos)
    has_five_kind = any(c[0] == "FIVE_OF_A_KIND" for c in strong_combos)
    
    if has_five_kind or has_four_kind:
        # Filter out THREE_OF_A_KIND that overlap with larger kinds
        filtered_combos = []
        for combo_type, pieces in strong_combos:
            if combo_type == "THREE_OF_A_KIND":
                # Check if all pieces are SOLDIERs (the overlapping case)
                if all(p.name == "SOLDIER" for p in pieces):
                    continue  # Skip overlapping THREE_OF_A_KIND
            filtered_combos.append((combo_type, pieces))
        strong_combos = filtered_combos
    
    # Phase 3: Evaluate openers
    opener_score = 0
    has_reliable_opener = False
    opener_count = 0
    for piece in hand:
        if piece.point >= 11:
            reliability = evaluate_opener_reliability(piece, context.field_strength)
            if reliability > 0:
                has_reliable_opener = True
                opener_count += 1
                opener_score += reliability
    
    # Phase 3b: Apply multi-opener synergy bonus
    if opener_count >= 2:
        # Multiple premium openers provide strategic flexibility
        # Slightly higher bonus to ensure rounding works correctly
        synergy_bonus = 0.6 if opener_count == 2 else 0.8 if opener_count == 3 else 1.0
        opener_score += synergy_bonus
    
    # Phase 4: Filter viable combos
    viable_combos = filter_viable_combos(
        strong_combos, context, has_reliable_opener
    )
    
    # Phase 5: Calculate base score
    score = 0
    
    # Add piles from viable combos (but respect 8-piece limit)
    total_pieces_used = 0
    sorted_combos = sorted(viable_combos, key=lambda x: len(x[1]), reverse=True)  # Largest first
    
    # Special case: if we have GENERAL_RED and strong combos, be more aggressive
    if context.has_general_red and any(c[0] in ["FOUR_OF_A_KIND", "FIVE_OF_A_KIND"] for c in viable_combos):
        # GENERAL_RED enables ALL viable combos due to guaranteed control
        for combo_type, pieces in sorted_combos:
            combo_size = len(pieces)
            if total_pieces_used + combo_size > 8:
                continue  # Can't use this combo, would exceed 8 pieces
                
            total_pieces_used += combo_size
            
            if combo_type == "THREE_OF_A_KIND" or combo_type == "STRAIGHT":
                score += 3
            elif combo_type == "FOUR_OF_A_KIND" or combo_type == "EXTENDED_STRAIGHT":
                score += 4
            elif combo_type == "FIVE_OF_A_KIND":
                score += 5
            elif combo_type == "SIX_OF_A_KIND":
                score += 6
    else:
        # Normal case: try to use all combos
        for combo_type, pieces in sorted_combos:
            combo_size = len(pieces)
            if total_pieces_used + combo_size > 8:
                continue  # Can't use this combo, would exceed 8 pieces
                
            total_pieces_used += combo_size
            
            if combo_type in ["THREE_OF_A_KIND", "STRAIGHT"]:
                score += 3
            elif combo_type in ["FOUR_OF_A_KIND", "EXTENDED_STRAIGHT"]:
                score += 4
            elif combo_type in ["FIVE_OF_A_KIND", "EXTENDED_STRAIGHT_5"]:
                score += 5
            elif combo_type == "DOUBLE_STRAIGHT":
                score += 6
    
    # Add opener piles (round to nearest integer)
    score += round(opener_score)
    
    # Phase 5b: Consider singles in weak fields or as starter
    if score == 0:
        if context.field_strength == "weak":
            # Count decent singles that might win in weak field
            decent_singles = sum(1 for p in hand if 7 <= p.point <= 10)
            if decent_singles >= 3:
                score = 2  # Can win with multiple medium pieces in very weak field
            elif decent_singles > 0:
                score = 1  # Conservative estimate
        elif context.is_starter:
            # As starter, might win with best piece
            best_piece = max((p.point for p in hand), default=0)
            if best_piece >= 9:
                score = 1  # Starter can lead with best piece
    
    # Phase 6: Apply GENERAL_RED game changer
    if context.has_general_red and context.field_strength == "weak":
        # Check for very weak field (dominance scenario)
        if context.previous_declarations:
            avg_declaration = sum(context.previous_declarations) / len(context.previous_declarations)
            if avg_declaration <= 0.5:
                # Very weak field - GENERAL_RED enables secondary pieces (9-10 points)
                secondary_pieces = sum(1 for p in hand if 9 <= p.point <= 10)
                if secondary_pieces > 0 and score < secondary_pieces + 1:
                    # Add piles for secondary pieces that become viable with GENERAL_RED dominance
                    # But don't exceed what we already have from combos
                    score = max(score, min(secondary_pieces + 1, context.pile_room))
    
    # Phase 7: Initial constraints
    # Valid range (but not pile room yet - that comes after forbidden value handling)
    score = max(0, min(score, 8))
    
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
            hand_strength = "strong" if opener_score >= 2.0 or len(viable_combos) >= 2 else "weak"
            
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
    
    # Phase 8c: Apply strategic reasonableness caps for boundary conditions
    # Detect extreme hands and apply appropriate caps
    all_pieces_values = [p.point for p in hand]
    
    # Check for extreme boundary conditions
    min_piece_value = min(all_pieces_values)
    max_piece_value = max(all_pieces_values)
    avg_piece_value = sum(all_pieces_values) / len(all_pieces_values)
    
    # Perfect opener hand (minimum piece value ≥8 points)
    if min_piece_value >= 8:
        # Even with all strong pieces, be realistic
        strategic_cap = 5 if context.is_starter else 4
        score = min(score, strategic_cap)
    
    # Weakest possible hand (maximum piece value ≤2 points)
    elif max_piece_value <= 2:
        # Very weak hand should be conservative
        strategic_cap = 2 if context.is_starter else 1
        score = min(score, strategic_cap)
    
    # Phase 9: Debug output
    if verbose:
        print(f"\n🎯 STRATEGIC DECLARATION ANALYSIS")
        print(f"Position: {position_in_order} (Starter: {context.is_starter})")
        print(f"Previous declarations: {previous_declarations}")
        print(f"Pile room: {context.pile_room}")
        print(f"Field strength: {context.field_strength}")
        print(f"Has GENERAL_RED: {context.has_general_red}")
        print(f"Combo opportunity: {context.opponent_patterns['combo_opportunity']}")
        print(f"Found {len(strong_combos)} combos, {len(viable_combos)} viable")
        print(f"Opener score: {opener_score}")
        print(f"Final declaration: {score}")
    
    # Phase 10: Optional analysis callback
    if analysis_callback:
        analysis_data = {
            'position_in_order': position_in_order,
            'is_starter': context.is_starter,
            'previous_declarations': previous_declarations,
            'pile_room': context.pile_room,
            'field_strength': context.field_strength,
            'has_general_red': context.has_general_red,
            'combo_opportunity': context.opponent_patterns['combo_opportunity'],
            'strong_combos_found': len(strong_combos),
            'viable_combos_count': len(viable_combos),
            'opener_score': opener_score,
            'final_decision': score
        }
        analysis_callback(analysis_data)
    
    return score


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
