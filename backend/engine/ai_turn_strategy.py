# backend/engine/ai_turn_strategy.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import random
from backend.engine.piece import Piece
from backend.engine.rules import get_play_type, is_valid_play
from backend.engine.ai import assess_field_strength


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
    # New fields for role-based planning
    assigned_openers: List[Piece] = field(default_factory=list)
    assigned_combos: List[Tuple[str, List[Piece]]] = field(default_factory=list)
    reserve_pieces: List[Piece] = field(default_factory=list)
    burden_pieces: List[Piece] = field(default_factory=list)
    main_plan_size: int = 0
    plan_impossible: bool = False


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
    hand_eval = evaluate_hand(hand, context, plan)
    
    # Log strategic context
    print(f"📊 {context.my_name} - Urgency: {plan.urgency_level}, Target remaining: {plan.target_remaining}, "
          f"Openers: {len(hand_eval['openers'])}, Burden pieces: {len(hand_eval['burden_pieces'])}")
    
    # Check if plan is broken and urgency is not none
    if plan.plan_impossible and plan.urgency_level != "none":
        print(f"💥 {context.my_name}: Plan broken - switching to aggressive capture")
        result = execute_aggressive_capture(hand, context.required_piece_count)
    # Execute appropriate strategy based on role
    elif context.am_i_starter:
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

def evaluate_hand(hand: List[Piece], context: TurnPlayContext, plan: StrategicPlan) -> Dict:
    """
    Evaluate and categorize pieces in the hand based on strategic plan.
    
    Args:
        hand: Bot's current hand
        context: Game context
        plan: Strategic plan with role assignments
        
    Returns:
        Dict with categorized pieces based on plan roles
    """
    # Find all valid combinations
    from backend.engine.ai import find_all_valid_combos
    valid_combos = find_all_valid_combos(hand)
    
    # Check if we need to form plan (turn 1)
    if context.turn_number == 1 and not plan.assigned_openers:
        # Form initial plan
        plan_dict = form_execution_plan(hand, context, valid_combos)
        if plan_dict:
            # Update plan object with assignments
            plan.assigned_openers = plan_dict['assigned_openers']
            plan.assigned_combos = plan_dict['assigned_combos']
            plan.reserve_pieces = plan_dict['reserve_pieces']
            plan.burden_pieces = plan_dict['burden_pieces']
            plan.main_plan_size = plan_dict['main_plan_size']
    
    # Return plan-based categorization
    return {
        'openers': plan.assigned_openers,
        'burden_pieces': plan.burden_pieces,
        'combo_pieces': [p for combo_type, pieces in plan.assigned_combos for p in pieces],
        'all_valid_combos': valid_combos,
        'reserve_pieces': plan.reserve_pieces
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


def get_field_strength_from_players(player_states: Dict[str, Dict]) -> str:
    """
    Assess field strength based on opponent declarations.
    
    Args:
        player_states: Dictionary of player states with 'declared' values
        
    Returns:
        Field strength: "weak", "normal", or "strong"
    """
    # Extract opponent declarations (excluding self)
    declarations = []
    for player_name, state in player_states.items():
        if 'declared' in state:
            declarations.append(state['declared'])
    
    # Use the assess_field_strength function from ai.py
    return assess_field_strength(declarations)


def is_combo_viable(combo_type: str, pieces: List[Piece], field_strength: str) -> bool:
    """
    Determine if a combo should be considered viable for winning.
    
    Args:
        combo_type: Type of combination (PAIR, THREE_OF_A_KIND, etc.)
        pieces: The pieces in the combination
        field_strength: Current field strength ("weak", "normal", "strong")
        
    Returns:
        True if combo is likely to win, False otherwise
    """
    # Strong combos are always viable
    if combo_type in ["THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND", 
                      "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"]:
        return True
    
    # For pairs, viability depends on strength and field
    if combo_type == "PAIR":
        total_points = sum(p.point for p in pieces)
        
        if field_strength == "weak":
            return total_points >= 10  # HORSE pair (5+5) or better
        elif field_strength == "normal":
            return total_points >= 14  # CHARIOT pair (7+7) or better
        else:  # strong
            return total_points >= 18  # ELEPHANT pair (9+9) or better
    
    # Single pieces are never considered winning combos
    return False


def form_execution_plan(hand: List[Piece], context: TurnPlayContext, valid_combos: List[Tuple]) -> Dict:
    """
    Form a specific execution plan assigning roles to pieces.
    
    Args:
        hand: Bot's current hand
        context: Game context including turn number and declarations
        valid_combos: All valid combinations found in hand
        
    Returns:
        Dict with assigned roles for each piece category
    """
    # Only form plan on turn 1 when we know required piece count
    if context.turn_number != 1:
        return None
    
    # Get field strength
    field_strength = get_field_strength_from_players(context.player_states)
    
    # Filter combos for viability
    viable_combos = []
    for combo_type, pieces in valid_combos:
        if is_combo_viable(combo_type, pieces, field_strength):
            viable_combos.append((combo_type, pieces))
    
    # Calculate how many piles we need to win
    target_remaining = context.my_declared - context.my_captured
    
    # Assign openers based on target
    all_openers = [p for p in hand if p.point >= 11]
    if target_remaining <= 1:
        assigned_openers = []  # Don't need openers
    elif target_remaining <= 3:
        assigned_openers = all_openers[:1]  # Take strongest opener
    else:
        assigned_openers = all_openers[:2]  # Take up to 2 openers
    
    # Sort openers by value descending
    assigned_openers.sort(key=lambda p: p.point, reverse=True)
    
    # Assign viable combos to plan
    assigned_combos = viable_combos
    
    # Calculate pieces used in plan
    pieces_in_plan = set(assigned_openers)
    for combo_type, pieces in assigned_combos:
        pieces_in_plan.update(pieces)
    
    # Reserve 1-2 weakest pieces (point <= 4)
    weak_pieces = [p for p in hand if p.point <= 4 and p not in pieces_in_plan]
    weak_pieces.sort(key=lambda p: p.point)  # Sort ascending
    reserve_pieces = weak_pieces[:2]  # Take up to 2 weakest
    pieces_in_plan.update(reserve_pieces)
    
    # Everything else is burden
    burden_pieces = [p for p in hand if p not in pieces_in_plan]
    # Sort burden by value descending (dispose high value first)
    burden_pieces.sort(key=lambda p: p.point, reverse=True)
    
    # Calculate main plan size
    main_plan_size = len(assigned_openers)
    for combo_type, pieces in assigned_combos:
        main_plan_size += len(pieces)
    
    return {
        'assigned_openers': assigned_openers,
        'assigned_combos': assigned_combos,
        'reserve_pieces': reserve_pieces,
        'burden_pieces': burden_pieces,
        'main_plan_size': main_plan_size,
        'field_strength': field_strength
    }


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
    
    # Create plan with default values (will be populated in evaluate_hand on turn 1)
    plan = StrategicPlan(
        target_remaining=target_remaining,
        valid_combos=valid_combos,
        opener_pieces=opener_pieces,
        urgency_level=urgency_level
    )
    
    # Check if plan is still possible (after turn 1)
    if context.turn_number > 1 and plan.main_plan_size > 0:
        # Check if we still have all our plan pieces
        current_hand_size = len(context.my_hand)
        if current_hand_size < plan.main_plan_size:
            plan.plan_impossible = True
            print(f"⚠️ {context.my_name}: Plan impossible - lost key pieces")
    
    return plan


def execute_aggressive_capture(hand: List[Piece], required_count: int) -> List[Piece]:
    """
    Execute aggressive capture strategy when plan is broken.
    Play strongest possible combinations to maximize win chances.
    
    Args:
        hand: Current hand
        required_count: Number of pieces required
        
    Returns:
        List of pieces to play (strongest possible)
    """
    from backend.engine.ai import find_all_valid_combos
    
    # Find all valid combinations
    all_combos = find_all_valid_combos(hand)
    
    # Filter for required size
    valid_of_size = [(combo_type, pieces) for combo_type, pieces in all_combos 
                     if len(pieces) == required_count]
    
    if valid_of_size:
        # Get strongest combination
        strongest_combo = max(valid_of_size, key=lambda x: sum(p.point for p in x[1]))
        print(f"⚡ Aggressive capture: playing strongest combo {strongest_combo[0]} "
              f"(value={sum(p.point for p in strongest_combo[1])})")
        return strongest_combo[1]
    
    # Fallback: return strongest pieces of required count
    sorted_hand = sorted(hand, key=lambda p: p.point, reverse=True)
    return sorted_hand[:required_count]


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
    
    # Opener timing logic based on plan type
    # Check if plan is opener-only
    opener_only_plan = len(plan.assigned_combos) == 0
    
    if context.required_piece_count == 1 and plan.assigned_openers:
        if opener_only_plan:
            # Opener-only plan: play more freely throughout the game
            hand_size = len(context.my_hand)
            if hand_size >= 6:
                chance = 0.35  # 35% chance early
            elif hand_size >= 4:
                chance = 0.40  # 40% chance mid-game
            else:
                chance = 0.50  # 50% chance late game
                
            if random.random() < chance:
                print(f"👑 {context.my_name} (opener-only plan) plays opener randomly: {plan.assigned_openers[0].name}")
                return [plan.assigned_openers[0]]
        else:
            # Mixed plan: protect combos
            if len(context.my_hand) > plan.main_plan_size:
                if random.random() < 0.3:  # 30% chance
                    print(f"👑 {context.my_name} plays opener for turn control: {plan.assigned_openers[0].name}")
                    return [plan.assigned_openers[0]]
    elif context.required_piece_count == 2 and len(plan.assigned_openers) >= 2:
        # Double opener logic (same protection logic applies)
        if len(context.my_hand) > plan.main_plan_size:
            if random.random() < 0.3:  # 30% chance
                print(f"👑 {context.my_name} plays double opener: {[p.name for p in plan.assigned_openers[:2]]}")
                return plan.assigned_openers[:2]
    
    # Low urgency AND have burden pieces: dispose of them
    if plan.urgency_level in ["low", "medium"] and plan.burden_pieces:
        # Sort burden by value descending (dispose high value first)
        sorted_burden = sorted(plan.burden_pieces, key=lambda p: -p.point)
        burden_count = min(required, len(sorted_burden))
        if burden_count == required:
            burden_play = sorted_burden[:required]
            # Check if this is a valid play for starter
            if is_valid_play(burden_play):
                print(f"🗑️ {context.my_name} disposes burden pieces (high value first): {[f'{p.name}({p.point})' for p in burden_play]}")
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