# backend/engine/ai_turn_strategy.py

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from backend.engine.piece import Piece
from backend.engine.rules import get_play_type, is_valid_play


# ------------------------------------------------------------------
# Strategic AI Turn Play System - Data Structures
# ------------------------------------------------------------------
@dataclass
class TurnPlayContext:
    """Holds all context needed for strategic turn play decisions."""
    my_name: str  # Bot's name for self-identification
    my_hand: List[Piece]  # Current bot hand
    my_captured: int  # Piles already captured
    my_declared: int  # Target pile count
    required_piece_count: Optional[int]  # From game state
    turn_number: int  # Current turn in round
    pieces_per_player: int  # Remaining pieces per player
    am_i_starter: bool  # Leading this turn?
    current_plays: List[Dict]  # This turn's plays so far
    revealed_pieces: List[Piece]  # All face-up played pieces
    player_states: Dict[str, Dict]  # All players' captured/declared


@dataclass
class StrategicPlan:
    """Strategic plan for achieving turn play objectives."""
    target_remaining: int  # Piles still needed (declared - captured)
    valid_combos: List[Tuple[str, List[Piece]]]  # All valid plays
    opener_pieces: List[Piece]  # Pieces with point >= 11
    urgency_level: str  # "low", "medium", "high", "critical"


# ------------------------------------------------------------------
# Core Decision Function
# ------------------------------------------------------------------
def choose_strategic_play(hand: List[Piece], context: TurnPlayContext) -> List[Piece]:
    """
    Main strategic decision function for turn play with defensive validation.
    
    Args:
        hand: Bot's current hand
        context: All game state information
        
    Returns:
        List of pieces to play
    """
    # Defensive check: validate inputs
    if not hand:
        print(f"⚠️ Strategic AI: Empty hand provided")
        return []
    
    if not context:
        print(f"⚠️ Strategic AI: No context provided, falling back to basic play")
        from backend.engine.ai import choose_best_play
        return choose_best_play(hand, None)
    
    # Defensive check: validate context fields
    if not hasattr(context, 'my_captured') or not hasattr(context, 'my_declared'):
        print(f"⚠️ Strategic AI: Invalid context, falling back to basic play")
        from backend.engine.ai import choose_best_play
        return choose_best_play(hand, context.required_piece_count if hasattr(context, 'required_piece_count') else None)
    
    # Log the decision context
    print(f"🎯 Strategic AI for {context.my_name}: captured={context.my_captured}, declared={context.my_declared}, required={context.required_piece_count}")
    
    # Check if at declared target
    if context.my_captured == context.my_declared:
        print(f"🛡️ {context.my_name} is at target ({context.my_captured}/{context.my_declared}) - activating overcapture avoidance")
        result = avoid_overcapture_strategy(hand, context)
        
        # Validate result
        if not validate_play_result(result, hand, context):
            print(f"⚠️ Strategic AI: Invalid result from overcapture strategy, falling back")
            from backend.engine.ai import choose_best_play
            return choose_best_play(hand, context.required_piece_count)
        
        # Log the decision
        play_value = sum(p.point for p in result)
        print(f"🎲 {context.my_name} plays weak pieces (value={play_value}) to avoid overcapture: {[p.name for p in result]}")
        return result
    
    # Phase 4: Target Achievement Strategy
    print(f"📈 {context.my_name} below target ({context.my_captured}/{context.my_declared}) - using target achievement strategy")
    
    # Generate strategic plan
    plan = generate_strategic_plan(hand, context)
    
    # Evaluate hand
    hand_eval = evaluate_hand(hand, context)
    
    # Log strategic context
    print(f"📊 {context.my_name} - Urgency: {plan.urgency_level}, Target remaining: {plan.target_remaining}, "
          f"Openers: {len(hand_eval['openers'])}, Burden pieces: {len(hand_eval['burden_pieces'])}")
    
    # Execute appropriate strategy based on role
    if context.am_i_starter:
        result = execute_starter_strategy(plan, context, hand_eval)
    else:
        # For now, responder uses basic AI (Phase 5 will implement responder strategy)
        print(f"🎯 {context.my_name} as responder - using basic play selection for now")
        from backend.engine.ai import choose_best_play
        result = choose_best_play(hand, context.required_piece_count)
    
    # Validate result
    if not validate_play_result(result, hand, context):
        print(f"⚠️ Strategic AI: Invalid result, using fallback")
        # Fallback: return minimum required pieces
        if context.required_piece_count and context.required_piece_count <= len(hand):
            return hand[:context.required_piece_count]
        return [hand[0]] if hand else []
    
    return result


# ------------------------------------------------------------------
# Overcapture Avoidance Strategy
# ------------------------------------------------------------------
def avoid_overcapture_strategy(hand: List[Piece], context: TurnPlayContext) -> List[Piece]:
    """
    Strategy to avoid winning piles when already at declared target.
    
    Args:
        hand: Bot's current hand
        context: Game context
        
    Returns:
        Weakest possible play to avoid winning
    """
    # Defensive check: validate hand
    if not hand:
        print(f"⚠️ Overcapture strategy: Empty hand")
        return []
    
    required = context.required_piece_count if context else None
    
    if required is None:
        # If no required count set yet, play single weakest piece
        weakest = min(hand, key=lambda p: p.point)
        return [weakest]
    
    # Defensive check: validate required count
    if required <= 0:
        print(f"⚠️ Overcapture strategy: Invalid required count {required}")
        return [min(hand, key=lambda p: p.point)]
    
    if required > len(hand):
        print(f"⚠️ Overcapture strategy: Required {required} but only {len(hand)} pieces in hand")
        # Return all pieces if we don't have enough
        return list(hand)
    
    # Sort pieces by point value ascending (weakest first)
    sorted_hand = sorted(hand, key=lambda p: p.point)
    
    # Try to find a valid combination of weak pieces
    if required <= len(sorted_hand):
        # Take the weakest N pieces
        weak_pieces = sorted_hand[:required]
        
        # Check if this forms a valid play (only matters for starter)
        if context and context.am_i_starter:
            if is_valid_play(weak_pieces):
                return weak_pieces
            else:
                # Try to find valid weak combination for starter
                # This is a simple approach - could be enhanced
                print(f"⚠️ Overcapture strategy: Weak pieces not valid for starter, trying alternatives")
        else:
            # Non-starter can play any pieces
            return weak_pieces
    
    # If no valid combination found, just return weakest pieces (will forfeit)
    return sorted_hand[:required]


# ------------------------------------------------------------------
# Phase 4: Target Achievement Strategy Functions
# ------------------------------------------------------------------

def evaluate_hand(hand: List[Piece], context: TurnPlayContext) -> Dict:
    """
    Evaluate and categorize pieces in the hand.
    
    Args:
        hand: Bot's current hand
        context: Game context
        
    Returns:
        Dict with categorized pieces:
        - openers: List of pieces with point >= 11
        - burden_pieces: Pieces that don't contribute to winning combos
        - combo_pieces: Pieces that form valid winning combinations
    """
    # Find all valid combinations
    from backend.engine.ai import find_all_valid_combos
    valid_combos = find_all_valid_combos(hand)
    
    # Identify opener pieces (11+ points)
    openers = identify_opener_pieces(hand)
    
    # Find pieces that appear in winning combinations
    pieces_in_combos = set()
    combo_pieces = []
    
    for combo_type, pieces in valid_combos:
        # Consider pairs, three-of-a-kind, straights as winning combos
        if combo_type in ["PAIR", "THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND", 
                         "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"]:
            pieces_in_combos.update(pieces)
            combo_pieces.extend(pieces)
    
    # Remove duplicates from combo_pieces
    combo_pieces = list(set(combo_pieces))
    
    # Identify burden pieces (not in any winning combo and not openers)
    burden_pieces = identify_burden_pieces(hand, valid_combos)
    
    return {
        'openers': openers,
        'burden_pieces': burden_pieces,
        'combo_pieces': combo_pieces,
        'all_valid_combos': valid_combos
    }


def identify_opener_pieces(hand: List[Piece]) -> List[Piece]:
    """
    Filter pieces with point >= 11 and sort by reliability.
    
    Args:
        hand: List of pieces
        
    Returns:
        List of opener pieces sorted by point value descending
    """
    openers = [p for p in hand if p.point >= 11]
    # Sort by point value descending for reliability ranking
    return sorted(openers, key=lambda p: p.point, reverse=True)


def identify_burden_pieces(hand: List[Piece], valid_combos: List[Tuple]) -> List[Piece]:
    """
    Find pieces that don't appear in any valid winning combination.
    
    Args:
        hand: List of pieces
        valid_combos: All valid combinations from the hand
        
    Returns:
        List of burden pieces
    """
    # Track which pieces appear in winning combos
    pieces_in_winning_combos = set()
    
    for combo_type, pieces in valid_combos:
        # Only consider combinations that can actually win turns
        if combo_type in ["PAIR", "THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND",
                         "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"]:
            pieces_in_winning_combos.update(pieces)
    
    # Burden pieces are those not in any winning combo
    burden_pieces = [p for p in hand if p not in pieces_in_winning_combos]
    
    # Sort by point value ascending (weakest first for disposal)
    return sorted(burden_pieces, key=lambda p: p.point)


def calculate_urgency(context: TurnPlayContext) -> str:
    """
    Calculate urgency level based on turns remaining and piles needed.
    
    Args:
        context: Game context
        
    Returns:
        Urgency level: "none", "low", "medium", "high", "critical"
    """
    turns_remaining = 8 - context.turn_number
    piles_needed = context.my_declared - context.my_captured
    
    if piles_needed == 0:
        return "none"  # Already at target
    elif piles_needed < 0:
        return "none"  # Already exceeded target
    elif turns_remaining <= 0:
        return "critical"  # No turns left
    elif piles_needed >= turns_remaining:
        return "critical"  # Need to win every turn
    elif piles_needed >= turns_remaining * 0.75:
        return "high"  # Need to win most turns
    elif piles_needed >= turns_remaining * 0.5:
        return "medium"  # Need to win half the turns
    else:
        return "low"  # Have cushion for strategic play


def generate_strategic_plan(hand: List[Piece], context: TurnPlayContext) -> StrategicPlan:
    """
    Generate a strategic plan for achieving target piles.
    
    Args:
        hand: Bot's current hand
        context: Game context
        
    Returns:
        StrategicPlan with target analysis and valid plays
    """
    # Calculate target remaining
    target_remaining = context.my_declared - context.my_captured
    
    # Find all valid combinations
    from backend.engine.ai import find_all_valid_combos
    valid_combos = find_all_valid_combos(hand)
    
    # Identify openers
    opener_pieces = identify_opener_pieces(hand)
    
    # Assess urgency
    urgency_level = calculate_urgency(context)
    
    # Create and return plan
    return StrategicPlan(
        target_remaining=target_remaining,
        valid_combos=valid_combos,
        opener_pieces=opener_pieces,
        urgency_level=urgency_level
    )


def execute_starter_strategy(plan: StrategicPlan, context: TurnPlayContext, hand_eval: Dict) -> List[Piece]:
    """
    Execute strategy when leading the turn.
    
    Args:
        plan: Strategic plan
        context: Game context
        hand_eval: Hand evaluation from evaluate_hand()
        
    Returns:
        List of pieces to play
    """
    required = context.required_piece_count or 1
    
    # Critical urgency: need to win remaining turns
    if plan.urgency_level == "critical" and plan.target_remaining > 0:
        # Find strongest valid combination of required size
        best_combo = None
        best_value = 0
        
        for combo_type, pieces in plan.valid_combos:
            if len(pieces) == required:
                combo_value = sum(p.point for p in pieces)
                if combo_value > best_value:
                    best_value = combo_value
                    best_combo = pieces
        
        if best_combo:
            print(f"⚡ {context.my_name} (critical urgency) plays strong combo: {[p.name for p in best_combo]}")
            return best_combo
    
    # Have reliable opener AND still need wins
    if plan.opener_pieces and plan.target_remaining > 1:
        # Check if we can play opener(s) with required count
        if required == 1 and plan.opener_pieces:
            print(f"👑 {context.my_name} plays opener for turn control: {plan.opener_pieces[0].name}")
            return [plan.opener_pieces[0]]
        elif required == 2 and len(plan.opener_pieces) >= 2:
            print(f"👑 {context.my_name} plays double opener: {[p.name for p in plan.opener_pieces[:2]]}")
            return plan.opener_pieces[:2]
    
    # Low urgency AND have burden pieces: dispose of them
    if plan.urgency_level in ["low", "medium"] and hand_eval['burden_pieces']:
        burden_count = min(required, len(hand_eval['burden_pieces']))
        if burden_count == required:
            burden_play = hand_eval['burden_pieces'][:required]
            # Check if this is a valid play for starter
            if is_valid_play(burden_play):
                print(f"🗑️ {context.my_name} disposes burden pieces: {[p.name for p in burden_play]}")
                return burden_play
            else:
                print(f"📝 {context.my_name} burden pieces don't form valid play, trying other options")
    
    # Default: play weakest valid combination
    from backend.engine.ai import choose_best_play
    # For starter, we want weakest valid play, not strongest
    # Sort combos by total value ascending
    valid_of_size = [(combo_type, pieces) for combo_type, pieces in plan.valid_combos 
                     if len(pieces) == required]
    
    if valid_of_size:
        # Get weakest valid combination
        weakest_combo = min(valid_of_size, key=lambda x: sum(p.point for p in x[1]))
        print(f"🎯 {context.my_name} plays weakest valid combo: {[p.name for p in weakest_combo[1]]}")
        return weakest_combo[1]
    
    # Fallback to basic AI
    return choose_best_play(context.my_hand, required)


# ------------------------------------------------------------------
# Validation Helper
# ------------------------------------------------------------------
def validate_play_result(result: List[Piece], hand: List[Piece], context: TurnPlayContext) -> bool:
    """
    Validate that the AI's chosen play is legal.
    
    Args:
        result: The pieces chosen to play
        hand: The player's hand
        context: Game context
        
    Returns:
        True if the play is valid, False otherwise
    """
    # Check result is not None and is a list
    if result is None or not isinstance(result, list):
        print(f"⚠️ Validation: Result is not a list")
        return False
    
    # Check all pieces in result are actually in hand
    for piece in result:
        if piece not in hand:
            print(f"⚠️ Validation: Piece {piece} not in hand")
            return False
    
    # Check piece count matches requirement (if set)
    if context and context.required_piece_count is not None:
        if len(result) != context.required_piece_count:
            print(f"⚠️ Validation: Expected {context.required_piece_count} pieces, got {len(result)}")
            return False
    
    # For starter, check if play is valid
    if context and context.am_i_starter and result:
        if not is_valid_play(result):
            print(f"⚠️ Validation: Starter play is not valid")
            return False
    
    return True