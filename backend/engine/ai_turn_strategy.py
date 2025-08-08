# backend/engine/ai_turn_strategy.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import random
from backend.engine.piece import Piece
from backend.engine.rules import get_play_type, is_valid_play
from backend.engine.ai import assess_field_strength, is_starter_preferred_combo


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
# Overcapture Avoidance Constraint System
# ------------------------------------------------------------------
@dataclass
class OvercaptureConstraints:
    """Constraints to avoid capturing too many piles."""
    max_safe_pieces: int  # Maximum pieces that can be played safely
    avoid_piece_counts: List[int]  # Piece counts that would cause overcapture
    risky_play_types: List[str]  # Play types likely to win and cause overcapture
    risk_level: str  # "none", "low", "medium", "high"


def get_overcapture_constraints(context: TurnPlayContext) -> OvercaptureConstraints:
    """
    Calculate constraints to avoid overcapture based on current game state.
    
    Args:
        context: Game context with capture/declaration info
        
    Returns:
        OvercaptureConstraints object with safety limits
    """
    piles_needed = context.my_declared - context.my_captured
    current_hand_size = len(context.my_hand)
    
    # No constraints if already over target or target is 0
    if piles_needed <= 0 or context.my_declared == 0:
        return OvercaptureConstraints(
            max_safe_pieces=current_hand_size,
            avoid_piece_counts=[],
            risky_play_types=[],
            risk_level="none"
        )
    
    # Calculate safe piece counts
    max_safe_pieces = piles_needed
    avoid_piece_counts = list(range(piles_needed + 1, 7))  # 1-6 pieces possible
    
    # Determine risk level
    if piles_needed >= current_hand_size:
        risk_level = "none"  # No risk, need to win many turns
    elif piles_needed >= current_hand_size * 0.75:
        risk_level = "low"
    elif piles_needed >= current_hand_size * 0.5:
        risk_level = "medium"
    else:
        risk_level = "high"  # Very close to target
    
    # Identify risky play types based on field strength
    field_strength = get_field_strength_from_players(context.player_states)
    
    # Always risky multi-piece plays when close to target
    risky_play_types = []
    if piles_needed < 3:
        risky_play_types.extend(["THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND", 
                                "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"])
    if piles_needed < 2:
        risky_play_types.append("PAIR")
    
    # In weak fields, even small combos might win
    if field_strength == "weak" and piles_needed < current_hand_size * 0.5:
        if "PAIR" not in risky_play_types:
            risky_play_types.append("PAIR")
    
    return OvercaptureConstraints(
        max_safe_pieces=max_safe_pieces,
        avoid_piece_counts=avoid_piece_counts,
        risky_play_types=risky_play_types,
        risk_level=risk_level
    )


def is_play_risky_for_overcapture(pieces: List[Piece], constraints: OvercaptureConstraints, 
                                  field_strength: str) -> bool:
    """
    Check if a play is likely to win and cause overcapture.
    
    Args:
        pieces: Pieces to play
        constraints: Overcapture constraints
        field_strength: Current field strength assessment
        
    Returns:
        True if play is risky for overcapture
    """
    # Check piece count constraint
    if len(pieces) in constraints.avoid_piece_counts:
        return True
    
    # Check play type constraint
    play_type = get_play_type(pieces)
    if play_type in constraints.risky_play_types:
        return True
    
    # Additional checks for high-value plays in weak fields
    if constraints.risk_level in ["medium", "high"] and field_strength == "weak":
        total_value = sum(p.point for p in pieces)
        avg_value = total_value / len(pieces)
        
        # High average value plays are risky in weak fields
        if avg_value >= 7:  # Above CHARIOT_BLACK value
            return True
    
    return False


def filter_plays_by_constraints(valid_plays: List[Tuple[str, List[Piece]]], 
                               constraints: OvercaptureConstraints,
                               field_strength: str) -> List[Tuple[str, List[Piece]]]:
    """
    Filter valid plays to exclude those that risk overcapture.
    
    Args:
        valid_plays: List of (play_type, pieces) tuples
        constraints: Overcapture constraints
        field_strength: Current field strength
        
    Returns:
        Filtered list of safe plays
    """
    if constraints.risk_level == "none":
        return valid_plays
    
    safe_plays = []
    for play_type, pieces in valid_plays:
        if not is_play_risky_for_overcapture(pieces, constraints, field_strength):
            safe_plays.append((play_type, pieces))
    
    return safe_plays


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
    
    # Log the decision context with debug information
    print(f"\n🎯 Strategic AI Decision Process for {context.my_name}")
    print(f"  📊 Status: captured={context.my_captured}, declared={context.my_declared}")
    print(f"  🎮 Turn {context.turn_number}, required pieces={context.required_piece_count}")
    print(f"  🃏 Hand size: {len(hand)} pieces")
    print(f"  👥 Starter: {'YES' if context.am_i_starter else 'NO'}")
    
    # Additional debug logging for starter detection
    print(f"\n🎯 STRATEGIC PLAY DEBUG for {context.my_name}:")
    print(f"  - Is starter: {context.am_i_starter}")
    print(f"  - Turn number: {context.turn_number}")
    print(f"  - Required pieces: {context.required_piece_count}")
    
    # Calculate overcapture constraints
    constraints = get_overcapture_constraints(context)
    
    if constraints.risk_level != "none":
        print(f"\n⚠️ OVERCAPTURE RISK DETECTED - Level: {constraints.risk_level}")
        print(f"  Piles needed: {context.my_declared - context.my_captured}")
        print(f"  Max safe pieces: {constraints.max_safe_pieces}")
        print(f"  Avoid piece counts: {constraints.avoid_piece_counts}")
        print(f"  Risky play types: {constraints.risky_play_types}")
    
    # Phase 4: Target Achievement Strategy
    piles_needed = context.my_declared - context.my_captured
    if piles_needed > 0:
        print(f"📈 {context.my_name} needs {piles_needed} more pile(s) - using strategic play with constraints")
    else:
        print(f"🎯 {context.my_name} at/above target - minimizing wins")
    
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
        result = execute_aggressive_capture(hand, context.required_piece_count, constraints)
    # Execute appropriate strategy based on role
    elif context.am_i_starter:
        result = execute_starter_strategy(plan, context, hand_eval, constraints)
    else:
        # Responder strategy: dispose of burden pieces
        result = execute_responder_strategy(plan, context, hand_eval, constraints)
    
    # Validate result
    if not validate_play_result(result, hand, context):
        print(f"⚠️ Strategic AI: Invalid result, using fallback")
        # Fallback: return minimum required pieces
        if context.required_piece_count and context.required_piece_count <= len(hand):
            return hand[:context.required_piece_count]
        return [hand[0]] if hand else []
    
    # Log final decision with piece values
    pieces_with_values = [f"{p.name}({p.point})" for p in result]
    print(f"\n🎲 {context.my_name} decides to play: {pieces_with_values}")
    
    return result


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
    
    print(f"\n📋 FORMING EXECUTION PLAN for {context.my_name}")
    print(f"  Hand: {[f'{p.name}({p.point})' for p in hand]}")
    print(f"  Target: {context.my_declared} piles, Currently captured: {context.my_captured}")
    
    # Get field strength
    field_strength = get_field_strength_from_players(context.player_states)
    print(f"  Field strength: {field_strength}")
    
    # Log all valid combos found
    print(f"  Valid combos found: {len(valid_combos)}")
    for combo_type, pieces in valid_combos:
        print(f"    - {combo_type}: {[f'{p.name}({p.point})' for p in pieces]} (value={sum(p.point for p in pieces)})")
    
    # Filter combos for viability
    viable_combos = []
    for combo_type, pieces in valid_combos:
        if is_combo_viable(combo_type, pieces, field_strength):
            viable_combos.append((combo_type, pieces))
    
    print(f"  Viable combos (can win in {field_strength} field): {len(viable_combos)}")
    for combo_type, pieces in viable_combos:
        print(f"    - {combo_type}: {[f'{p.name}({p.point})' for p in pieces]}")
    
    # Calculate how many piles we need to win
    target_remaining = context.my_declared - context.my_captured
    print(f"  Piles needed to win: {target_remaining}")
    
    # Assign openers based on target
    all_openers = [p for p in hand if p.point >= 11]
    print(f"  Openers available: {[f'{p.name}({p.point})' for p in all_openers]}")
    
    # Debug logging for opener assignment
    print(f"  🎯 Opener Assignment Debug:")
    print(f"    - All openers found: {[f'{p.name}({p.point})' for p in all_openers]}")
    print(f"    - Target remaining: {target_remaining}")
    print(f"    - Has viable combos: {len(viable_combos) > 0}")
    
    if target_remaining <= 0:
        assigned_openers = []  # Already at/above target
        print(f"  → Assigning 0 openers (already at target)")
    elif target_remaining == 1:
        # Even with 1 pile needed, keep 1 opener for control
        assigned_openers = all_openers[:1] if all_openers else []
        print(f"  → Assigning {len(assigned_openers)} opener for {target_remaining} pile (control)")
    elif target_remaining == 2:
        # For 2 piles, take up to 2 openers
        assigned_openers = all_openers[:2] if len(all_openers) >= 2 else all_openers
        print(f"  → Assigning {len(assigned_openers)} opener(s) for {target_remaining} piles")
    elif target_remaining == 3:
        # For 3 piles, take 1-2 openers (leave room for combos)
        assigned_openers = all_openers[:2] if len(all_openers) >= 2 else all_openers
        print(f"  → Assigning {len(assigned_openers)} opener(s) for {target_remaining} piles")
    else:
        # For 4+ piles, take up to 2 openers
        assigned_openers = all_openers[:2]  # Take up to 2 openers
        print(f"  → Assigning {len(assigned_openers)} openers for {target_remaining} piles")
    
    print(f"    - Assigned openers: {[f'{p.name}({p.point})' for p in assigned_openers]}")
    
    # Sort openers by value descending
    assigned_openers.sort(key=lambda p: p.point, reverse=True)
    
    # Check for overlap between openers and combos
    assigned_combos = []
    pieces_in_plan = set(assigned_openers)
    
    for combo_type, pieces in viable_combos:
        # Check if combo pieces overlap with already assigned pieces
        combo_pieces_set = set(pieces)
        overlap = combo_pieces_set.intersection(pieces_in_plan)
        
        if overlap:
            print(f"    ⚠️ {combo_type} overlaps with assigned pieces: {[f'{p.name}({p.point})' for p in overlap]}")
            
            # For starters with strong combos, prefer the combo over individual openers
            if context.am_i_starter and is_starter_preferred_combo(combo_type, pieces):
                # Remove overlapping openers from plan and use combo instead
                overlapping_openers = [p for p in assigned_openers if p in overlap]
                if overlapping_openers:
                    print(f"    → Starter prefers {combo_type} over individual openers")
                    # Remove overlapping openers
                    for opener in overlapping_openers:
                        assigned_openers.remove(opener)
                        pieces_in_plan.remove(opener)
                    # Add the combo
                    assigned_combos.append((combo_type, pieces))
                    pieces_in_plan.update(pieces)
                    continue
            
            # Skip combos that use already assigned opener pieces
            continue
        else:
            assigned_combos.append((combo_type, pieces))
            pieces_in_plan.update(pieces)
    
    # Reserve 1-2 weakest pieces (point <= 4)
    weak_pieces = [p for p in hand if p.point <= 4 and p not in pieces_in_plan]
    weak_pieces.sort(key=lambda p: p.point)  # Sort ascending
    reserve_pieces = weak_pieces[:2]  # Take up to 2 weakest
    pieces_in_plan.update(reserve_pieces)
    
    print(f"  Weak pieces (<=4 pts): {[f'{p.name}({p.point})' for p in weak_pieces]}")
    print(f"  → Reserving {len(reserve_pieces)} weak pieces for overcapture avoidance")
    
    # Everything else is burden
    burden_pieces = [p for p in hand if p not in pieces_in_plan]
    # Sort burden by value descending (dispose high value first)
    burden_pieces.sort(key=lambda p: p.point, reverse=True)
    
    print(f"  Burden pieces (not in winning plan): {[f'{p.name}({p.point})' for p in burden_pieces]}")
    
    # Calculate main plan size
    main_plan_size = len(assigned_openers)
    for combo_type, pieces in assigned_combos:
        main_plan_size += len(pieces)
    
    print(f"\n  📊 FINAL PLAN SUMMARY:")
    print(f"    - Openers: {[f'{p.name}({p.point})' for p in assigned_openers]}")
    print(f"    - Viable combos: {len(assigned_combos)}")
    for combo_type, pieces in assigned_combos:
        print(f"      • {combo_type}: {[f'{p.name}({p.point})' for p in pieces]}")
    print(f"    - Reserve pieces: {[f'{p.name}({p.point})' for p in reserve_pieces]}")
    print(f"    - Burden pieces: {[f'{p.name}({p.point})' for p in burden_pieces]}")
    print(f"    - Main plan size: {main_plan_size} pieces")
    
    # Print the main plan pieces
    print(f"\n  🎯 MAIN WINNING PLAN (Target: {target_remaining} piles):")
    piles_accounted = 0
    if assigned_openers:
        for opener in assigned_openers:
            piles_accounted += 1
            print(f"    Play #{piles_accounted}: {opener.name}({opener.point}) [OPENER] → hope to capture 1 pile")
    if assigned_combos:
        for combo_type, pieces in assigned_combos:
            pieces_count = len(pieces)
            print(f"    Play #{piles_accounted + 1}: {combo_type} {[f'{p.name}({p.point})' for p in pieces]} → hope to capture {pieces_count} piles")
            piles_accounted += pieces_count
    
    if piles_accounted < target_remaining:
        print(f"    ⚠️ Plan only accounts for {piles_accounted}/{target_remaining} piles needed")
    
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


def execute_aggressive_capture(hand: List[Piece], required_count: int, 
                             constraints: OvercaptureConstraints) -> List[Piece]:
    """
    Execute aggressive capture strategy when plan is broken.
    Play strongest possible combinations to maximize win chances, but respect constraints.
    
    Args:
        hand: Current hand
        required_count: Number of pieces required
        constraints: Overcapture avoidance constraints
        
    Returns:
        List of pieces to play (strongest possible within constraints)
    """
    from backend.engine.ai import find_all_valid_combos
    
    # Find all valid combinations
    all_combos = find_all_valid_combos(hand)
    
    # Filter for required size
    valid_of_size = [(combo_type, pieces) for combo_type, pieces in all_combos 
                     if len(pieces) == required_count]
    
    if valid_of_size:
        # Check constraints if risk level is high
        if constraints.risk_level in ["medium", "high"]:
            print(f"⚠️ Aggressive capture with overcapture risk - filtering safe combos")
            field_strength = "normal"  # Default assumption for aggressive play
            safe_combos = [(t, p) for t, p in valid_of_size 
                          if not is_play_risky_for_overcapture(p, constraints, field_strength)]
            
            if safe_combos:
                # Get strongest safe combination
                strongest_combo = max(safe_combos, key=lambda x: sum(p.point for p in x[1]))
                print(f"⚡ Aggressive capture: playing strongest SAFE combo {strongest_combo[0]} "
                      f"(value={sum(p.point for p in strongest_combo[1])})")
                return strongest_combo[1]
            else:
                print(f"⚠️ No safe combos available - playing weakest risky combo")
                # If no safe combos, play weakest risky one
                weakest_combo = min(valid_of_size, key=lambda x: sum(p.point for p in x[1]))
                return weakest_combo[1]
        else:
            # No constraints, play strongest
            strongest_combo = max(valid_of_size, key=lambda x: sum(p.point for p in x[1]))
            print(f"⚡ Aggressive capture: playing strongest combo {strongest_combo[0]} "
                  f"(value={sum(p.point for p in strongest_combo[1])})")
            return strongest_combo[1]
    
    # Fallback: return strongest pieces of required count
    sorted_hand = sorted(hand, key=lambda p: p.point, reverse=True)
    return sorted_hand[:required_count]


def execute_responder_strategy(plan: StrategicPlan, context: TurnPlayContext, hand_eval: Dict,
                             constraints: OvercaptureConstraints) -> List[Piece]:
    """
    Execute strategy when responding (not leading the turn) with overcapture constraints.
    Primary goal: Dispose of pieces in priority order:
    1. Burden pieces (highest value first)
    2. Reserve pieces (if necessary)
    3. Openers (only as last resort)
    
    Args:
        plan: Strategic plan
        context: Game context
        hand_eval: Hand evaluation from evaluate_hand()
        constraints: Overcapture avoidance constraints
        
    Returns:
        List of pieces to play
    """
    required = context.required_piece_count or 1
    
    print(f"\n🎯 RESPONDER STRATEGY for {context.my_name} (Turn {context.turn_number})")
    print(f"  Current hand: {[f'{p.name}({p.point})' for p in context.my_hand]}")
    print(f"  Required pieces: {required}")
    print(f"  Urgency: {plan.urgency_level}, Target remaining: {plan.target_remaining}")
    print(f"  Overcapture risk: {constraints.risk_level}")
    
    # Critical urgency: need to win remaining turns
    if plan.urgency_level == "critical" and plan.target_remaining > 0:
        print(f"  💥 CRITICAL URGENCY - must try to win!")
        # Try to find any valid combination
        from backend.engine.ai import find_all_valid_combos
        all_combos = find_all_valid_combos(context.my_hand)
        valid_of_size = [(combo_type, pieces) for combo_type, pieces in all_combos 
                         if len(pieces) == required]
        
        if valid_of_size:
            # Get strongest valid combination
            best_combo = max(valid_of_size, key=lambda x: sum(p.point for p in x[1]))
            print(f"  ⚡ Playing strongest valid combo: {[p.name for p in best_combo[1]]}")
            return best_combo[1]
    
    # Build disposal priority list: burden -> reserve -> openers (last resort)
    disposal_candidates = []
    
    # Priority 1: Burden pieces (highest value first)
    burden_in_hand = [p for p in plan.burden_pieces if p in context.my_hand]
    burden_in_hand.sort(key=lambda p: p.point, reverse=True)
    disposal_candidates.extend(burden_in_hand)
    
    # Priority 2: Reserve pieces (if we need more)
    if len(disposal_candidates) < required and plan.reserve_pieces:
        reserve_in_hand = [p for p in plan.reserve_pieces if p in context.my_hand]
        # Sort reserve pieces by value descending (dispose higher value first)
        reserve_in_hand.sort(key=lambda p: p.point, reverse=True)
        disposal_candidates.extend(reserve_in_hand)
    
    # Priority 3: Openers (only as absolute last resort)
    if len(disposal_candidates) < required and plan.assigned_openers:
        openers_in_hand = [p for p in plan.assigned_openers if p in context.my_hand]
        # Sort openers by value ascending (keep strongest openers if possible)
        openers_in_hand.sort(key=lambda p: p.point)
        disposal_candidates.extend(openers_in_hand)
    
    # Priority 4: Combo pieces (should never reach here in a well-formed plan)
    if len(disposal_candidates) < required and plan.assigned_combos:
        combo_pieces_in_hand = []
        for combo_type, pieces in plan.assigned_combos:
            combo_pieces_in_hand.extend([p for p in pieces if p in context.my_hand])
        # Remove duplicates
        combo_pieces_in_hand = list(set(combo_pieces_in_hand))
        combo_pieces_in_hand.sort(key=lambda p: p.point)
        disposal_candidates.extend(combo_pieces_in_hand)
    
    # Priority 5: Any remaining pieces not in plan
    if len(disposal_candidates) < required:
        all_plan_pieces = set()
        if plan.assigned_openers:
            all_plan_pieces.update(plan.assigned_openers)
        if plan.assigned_combos:
            for combo_type, pieces in plan.assigned_combos:
                all_plan_pieces.update(pieces)
        if plan.reserve_pieces:
            all_plan_pieces.update(plan.reserve_pieces)
        if plan.burden_pieces:
            all_plan_pieces.update(plan.burden_pieces)
        
        other_pieces = [p for p in context.my_hand if p not in all_plan_pieces]
        other_pieces.sort(key=lambda p: p.point, reverse=True)
        disposal_candidates.extend(other_pieces)
    
    # Debug output
    print(f"  🗑️ DISPOSAL PRIORITY:")
    print(f"    1. Burden pieces: {[f'{p.name}({p.point})' for p in burden_in_hand]}")
    if plan.reserve_pieces:
        reserve_in_hand = [p for p in plan.reserve_pieces if p in context.my_hand]
        print(f"    2. Reserve pieces: {[f'{p.name}({p.point})' for p in reserve_in_hand]}")
    if plan.assigned_openers:
        openers_in_hand = [p for p in plan.assigned_openers if p in context.my_hand]
        print(f"    3. Openers (last resort): {[f'{p.name}({p.point})' for p in openers_in_hand]}")
    
    # Special handling for high overcapture risk
    if constraints.risk_level in ["medium", "high"] and required in constraints.avoid_piece_counts:
        print(f"  🛡️ High overcapture risk - required count {required} would cause overcapture")
        print(f"  Seeking weak non-matching pieces to minimize win chance")
        
        # Try to select pieces that won't form strong combinations
        # Prefer different types/colors to avoid accidental combos
        selected_pieces = []
        used_names = set()
        
        # First pass: try to get different piece types
        for p in disposal_candidates:
            if len(selected_pieces) < required and p.name not in used_names:
                selected_pieces.append(p)
                used_names.add(p.name)
        
        # Second pass: fill remaining slots
        for p in disposal_candidates:
            if len(selected_pieces) < required and p not in selected_pieces:
                selected_pieces.append(p)
        
        if len(selected_pieces) >= required:
            pieces_to_play = selected_pieces[:required]
            print(f"  🎯 Selected non-matching pieces to avoid combos: {[f'{p.name}({p.point})' for p in pieces_to_play]}")
            total_value = sum(p.point for p in pieces_to_play)
            print(f"  Total value: {total_value} pts (minimized)")
            return pieces_to_play
    
    # Take required number from disposal candidates
    if len(disposal_candidates) >= required:
        pieces_to_play = disposal_candidates[:required]
        
        # Describe what we're disposing
        disposal_description = []
        burden_count = len([p for p in pieces_to_play if p in burden_in_hand])
        if burden_count > 0:
            disposal_description.append(f"{burden_count} burden")
        
        reserve_count = len([p for p in pieces_to_play if p in (plan.reserve_pieces or [])])
        if reserve_count > 0:
            disposal_description.append(f"{reserve_count} reserve")
            
        opener_count = len([p for p in pieces_to_play if p in (plan.assigned_openers or [])])
        if opener_count > 0:
            disposal_description.append(f"{opener_count} opener (last resort!)")
        
        total_value = sum(p.point for p in pieces_to_play)
        print(f"  🗑️ DISPOSING {' + '.join(disposal_description)}: {[f'{p.name}({p.point})' for p in pieces_to_play]}")
        print(f"  Total value: {total_value} pts")
        return pieces_to_play
    else:
        # Shouldn't happen with a well-formed plan
        print(f"  ⚠️ ERROR: Not enough pieces to dispose!")
        print(f"    - Need: {required} pieces")
        print(f"    - Have: {len(disposal_candidates)} total candidates")
        # Return what we have
        return disposal_candidates


def execute_starter_strategy(plan: StrategicPlan, context: TurnPlayContext, hand_eval: Dict, 
                           constraints: OvercaptureConstraints) -> List[Piece]:
    """
    Execute strategy when leading the turn with overcapture constraints.
    
    Args:
        plan: Strategic plan
        context: Game context
        hand_eval: Hand evaluation from evaluate_hand()
        constraints: Overcapture avoidance constraints
        
    Returns:
        List of pieces to play
    """
    # Since we're the starter, we need to choose how many pieces to play
    # Consider constraints when choosing piece count
    if context.required_piece_count is None:  # We're setting the count
        # Check if we're at or above target (negative piles needed)
        piles_needed = context.my_declared - context.my_captured
        
        if piles_needed <= 0:
            # At or above target - minimize pieces played
            required = 1
            print(f"  🛡️ At/above target - choosing minimum 1 piece")
        elif constraints.risk_level != "none":
            # Below target but at risk - prefer playing safe piece counts
            max_safe = constraints.max_safe_pieces
            if max_safe >= 1:
                required = min(max_safe, len(context.my_hand), 6)  # Cap at 6
            else:
                required = 1  # At least play 1
            print(f"  🛡️ Applying constraints: choosing to play {required} pieces (max safe: {max_safe})")
        else:
            required = 1  # Default for starters
    else:
        required = context.required_piece_count
    
    print(f"\n🎮 STARTER STRATEGY for {context.my_name} (Turn {context.turn_number})")
    print(f"  Current hand: {[f'{p.name}({p.point})' for p in context.my_hand]}")
    print(f"  Required pieces: {required}")
    print(f"  Urgency: {plan.urgency_level}, Target remaining: {plan.target_remaining}")
    print(f"  Overcapture risk: {constraints.risk_level}")
    
    # Critical urgency: need to win remaining turns
    if plan.urgency_level == "critical" and plan.target_remaining > 0:
        # Find strongest valid combination of required size
        best_combo = None
        best_value = 0
        
        print(f"  💥 CRITICAL URGENCY - must win turns!")
        for combo_type, pieces in plan.valid_combos:
            if len(pieces) == required:
                combo_value = sum(p.point for p in pieces)
                print(f"    Checking {combo_type}: {[f'{p.name}({p.point})' for p in pieces]} = {combo_value} pts")
                if combo_value > best_value:
                    best_value = combo_value
                    best_combo = pieces
        
        if best_combo:
            print(f"  ⚡ Playing strongest combo (value={best_value}): {[p.name for p in best_combo]}")
            return best_combo
    
    # Opener timing logic based on plan type
    # Check if plan is opener-only
    opener_only_plan = len(plan.assigned_combos) == 0
    
    # Debug logging for opener timing
    print(f"\n🎲 OPENER TIMING CHECK for {context.my_name}:")
    print(f"  - Required piece count: {context.required_piece_count}")
    print(f"  - Has assigned openers: {len(plan.assigned_openers) if plan.assigned_openers else 0}")
    if plan.assigned_openers:
        print(f"  - Assigned openers: {[f'{p.name}({p.point})' for p in plan.assigned_openers]}")
    print(f"  - Opener-only plan: {opener_only_plan}")
    print(f"  - Hand size: {len(context.my_hand)}")
    
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
            
            # Generate random value and log it
            random_value = random.random()
            print(f"  - Random value: {random_value:.3f} vs threshold: {chance:.3f}")
            print(f"  - Will play opener: {random_value < chance}")
                
            if random_value < chance:
                print(f"👑 {context.my_name} (opener-only plan) plays opener randomly: {plan.assigned_openers[0].name}")
                return [plan.assigned_openers[0]]
        else:
            # Mixed plan: protect combos
            print(f"  - Mixed plan check: hand_size ({len(context.my_hand)}) > main_plan_size ({plan.main_plan_size})")
            if len(context.my_hand) > plan.main_plan_size:
                # Generate random value and log it
                random_value = random.random()
                print(f"  - Random value: {random_value:.3f} vs threshold: 0.3")
                print(f"  - Will play opener: {random_value < 0.3}")
                
                if random_value < 0.3:  # 30% chance
                    print(f"👑 {context.my_name} plays opener for turn control: {plan.assigned_openers[0].name}")
                    return [plan.assigned_openers[0]]
    
    # Check if we have an assigned combo that matches required pieces
    if plan.assigned_combos:
        field_strength = get_field_strength_from_players(context.player_states)
        for combo_type, pieces in plan.assigned_combos:
            if len(pieces) == required:
                # Check if all pieces are still in hand
                all_in_hand = all(p in context.my_hand for p in pieces)
                if all_in_hand:
                    # Check if this combo is risky for overcapture
                    if is_play_risky_for_overcapture(pieces, constraints, field_strength):
                        print(f"  ⚠️ Skipping {combo_type} - risky for overcapture")
                        continue
                    print(f"🎯 {context.my_name} plays assigned {combo_type}: {[f'{p.name}({p.point})' for p in pieces]}")
                    return pieces
    
    # Low urgency AND have burden pieces: dispose of them
    if plan.urgency_level in ["low", "medium"] and plan.burden_pieces:
        print(f"  🗑️ Considering burden disposal ({len(plan.burden_pieces)} burden pieces)")
        # Sort burden by value descending (dispose high value first)
        sorted_burden = sorted(plan.burden_pieces, key=lambda p: -p.point)
        print(f"    Burden pieces sorted by value: {[f'{p.name}({p.point})' for p in sorted_burden]}")
        
        burden_count = min(required, len(sorted_burden))
        if burden_count == required:
            burden_play = sorted_burden[:required]
            print(f"    Trying to play {burden_count} burden pieces: {[f'{p.name}({p.point})' for p in burden_play]}")
            # Check if this is a valid play for starter
            if is_valid_play(burden_play):
                print(f"  🗑️ DISPOSING burden pieces (high value first): {[f'{p.name}({p.point})' for p in burden_play]}")
                return burden_play
            else:
                print(f"    ❌ Burden pieces don't form valid play for starter")
    
    # Default: play random pieces that are not part of combos
    # Collect pieces that are disposable (not in main plan)
    pieces_in_plan = set()
    
    # Add opener pieces to protected set
    if plan.assigned_openers:
        pieces_in_plan.update(plan.assigned_openers)
    
    # Add combo pieces to protected set
    for combo_type, pieces in plan.assigned_combos:
        pieces_in_plan.update(pieces)
    
    # Find disposable pieces (burden + reserve + any not in plan)
    disposable_pieces = []
    
    # First priority: burden pieces
    if plan.burden_pieces:
        burden_in_hand = [p for p in plan.burden_pieces if p in context.my_hand and p not in pieces_in_plan]
        disposable_pieces.extend(burden_in_hand)
    
    # Second priority: reserve pieces
    if plan.reserve_pieces:
        reserve_in_hand = [p for p in plan.reserve_pieces if p in context.my_hand and p not in pieces_in_plan]
        disposable_pieces.extend(reserve_in_hand)
    
    # Third priority: any piece not in plan
    other_pieces = [p for p in context.my_hand if p not in pieces_in_plan and p not in disposable_pieces]
    disposable_pieces.extend(other_pieces)
    
    # Special handling for high overcapture risk
    if constraints.risk_level in ["medium", "high"]:
        print(f"  🛡️ High overcapture risk - seeking weak valid combinations")
        field_strength = get_field_strength_from_players(context.player_states)
        
        # Try to find weakest valid combination
        from itertools import combinations
        valid_combos = []
        
        # Check all possible combinations of required size
        for combo in combinations(context.my_hand, required):
            combo_list = list(combo)
            if is_valid_play(combo_list):
                # Check if this combo is safe
                if not is_play_risky_for_overcapture(combo_list, constraints, field_strength):
                    total_value = sum(p.point for p in combo_list)
                    valid_combos.append((combo_list, total_value))
        
        if valid_combos:
            # Sort by value ascending (weakest first)
            valid_combos.sort(key=lambda x: x[1])
            weakest_combo = valid_combos[0][0]
            print(f"  🎯 Playing weakest safe combo (value={valid_combos[0][1]}): {[f'{p.name}({p.point})' for p in weakest_combo]}")
            return weakest_combo
    
    print(f"  🎲 Selecting random play from disposable pieces")
    print(f"    Disposable pieces: {[f'{p.name}({p.point})' for p in disposable_pieces]}")
    
    if len(disposable_pieces) >= required:
        # Randomly select required pieces
        import random
        selected_pieces = random.sample(disposable_pieces, required)
        
        # For starter, check if this forms a valid play
        if is_valid_play(selected_pieces):
            print(f"  🎯 {context.my_name} plays random disposable pieces: {[f'{p.name}({p.point})' for p in selected_pieces]}")
            return selected_pieces
        else:
            # Try to find a valid combination from disposable pieces
            print(f"    Random selection not valid for starter, trying to find valid combo...")
            from itertools import combinations
            for combo in combinations(disposable_pieces, required):
                if is_valid_play(list(combo)):
                    print(f"  🎯 {context.my_name} plays valid disposable combo: {[f'{p.name}({p.point})' for p in combo]}")
                    return list(combo)
    
    # Last resort: play any required pieces from hand
    print(f"  ⚠️ Not enough disposable pieces, playing from full hand")
    if required <= len(context.my_hand):
        selected = random.sample(context.my_hand, required)
        print(f"  🎯 {context.my_name} plays random pieces: {[f'{p.name}({p.point})' for p in selected]}")
        return selected
    
    # Absolute fallback
    from backend.engine.ai import choose_best_play
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