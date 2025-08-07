# backend/engine/ai_turn_strategy.py
"""
Strategic AI turn play system for achieving declared pile targets.

This module implements sophisticated decision-making for AI players to:
- Capture exactly their declared number of piles
- Avoid overcapturing when at target
- Make strategic decisions as starter or responder
- Adapt plans based on game state
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

from backend.engine.piece import Piece
from backend.engine.rules import get_play_type, is_valid_play


@dataclass
class TurnPlayContext:
    """Complete game state context for strategic turn decisions."""
    
    # Player's current state
    my_hand: List[Piece]        # Current pieces in hand
    my_captured: int            # Piles already captured this round
    my_declared: int            # Target pile count for this round
    
    # Turn information
    required_piece_count: Optional[int]  # Number of pieces required this turn
    turn_number: int                     # Current turn number in round
    pieces_per_player: int               # Remaining pieces per player
    am_i_starter: bool                   # Am I leading this turn?
    
    # Other players' information
    current_plays: List[Dict]            # This turn's plays so far
    revealed_pieces: List[Piece]         # All face-up played pieces this round
    player_states: Dict[str, Dict]       # All players' captured/declared status


@dataclass 
class StrategicPlan:
    """Strategic plan for achieving declared pile target."""
    
    target_remaining: int                        # Piles still needed (declared - captured)
    valid_combos: List[Tuple[str, List[Piece]]] # All valid plays: (play_type, pieces)
    opener_pieces: List[Piece]                   # High-value pieces (point >= 11)
    urgency_level: str                           # "low", "medium", "high", "critical"


def choose_strategic_play(hand: List[Piece], context: TurnPlayContext) -> List[Piece]:
    """
    Main strategic decision function for AI turn play.
    
    Args:
        hand: Current pieces in hand
        context: Complete game state context
        
    Returns:
        List of pieces to play this turn
    """
    # Priority 1: Check for disruption opportunity
    disruption_play = check_opponent_disruption(hand, context)
    if disruption_play:
        print(f"🚫 Playing disruption to prevent opponent bonus!")
        return disruption_play
    
    # Priority 2: Check if at declared target - must avoid overcapture
    if context.my_captured == context.my_declared:
        return avoid_overcapture_strategy(hand, context)
    
    # Generate strategic plan
    plan = generate_strategic_plan(hand, context)
    
    # If we're the starter, use starter strategy
    if context.am_i_starter:
        return execute_starter_strategy(plan, context)
    
    # Otherwise use responder strategy
    return execute_responder_strategy(plan, context)


def avoid_overcapture_strategy(hand: List[Piece], context: TurnPlayContext) -> List[Piece]:
    """
    Strategy when already at declared target - must not win any turns.
    
    Args:
        hand: Current pieces in hand
        context: Game state context
        
    Returns:
        Weakest possible pieces to avoid winning
    """
    required_count = context.required_piece_count or 1
    
    # Sort pieces by point value (ascending) to get weakest first
    sorted_pieces = sorted(hand, key=lambda p: p.point)
    
    # Take the weakest N pieces
    weakest_pieces = sorted_pieces[:required_count]
    
    # Check if these form a valid combination (only matters if we're starter)
    if context.am_i_starter and required_count > 1:
        # If we're starter and this isn't a valid combo, it will forfeit (good!)
        # But let's at least try to find a weak valid combo first
        from backend.engine.ai import find_all_valid_combos
        all_combos = find_all_valid_combos(hand)
        
        # Filter to combos of the required size
        sized_combos = [(play_type, pieces) for play_type, pieces in all_combos 
                        if len(pieces) == required_count]
        
        if sized_combos:
            # Find the weakest valid combo
            weakest_combo = min(sized_combos, 
                               key=lambda x: sum(p.point for p in x[1]))
            return weakest_combo[1]
    
    # Return weakest pieces (may forfeit if invalid, which is fine)
    return weakest_pieces


def generate_strategic_plan(hand: List[Piece], context: TurnPlayContext) -> StrategicPlan:
    """
    Generate a strategic plan to achieve declared pile target.
    
    Analyzes hand and game state to create a plan including:
    - Target remaining (how many more piles needed)
    - Valid combinations available
    - Opener pieces for turn control
    - Urgency level based on remaining turns
    
    Args:
        hand: Current pieces in hand
        context: Game state context
        
    Returns:
        StrategicPlan with analysis and options
    """
    # Calculate piles still needed
    target_remaining = context.my_declared - context.my_captured
    
    # Find all valid combinations
    from backend.engine.ai import find_all_valid_combos
    valid_combos = find_all_valid_combos(hand)
    
    # Identify opener pieces (11+ points)
    opener_pieces = [p for p in hand if p.point >= 11]
    
    # Assess urgency based on pieces remaining and target
    # We have 8 pieces total, each turn uses some pieces
    turns_remaining = context.pieces_per_player  # Rough estimate
    
    if target_remaining == 0:
        urgency_level = "none"  # Already at target
    elif target_remaining >= turns_remaining:
        urgency_level = "critical"  # Need to win almost every turn
    elif target_remaining >= turns_remaining * 0.75:
        urgency_level = "high"  # Need to win most turns
    elif target_remaining >= turns_remaining * 0.5:
        urgency_level = "medium"  # Need to win about half
    else:
        urgency_level = "low"  # Plenty of time
    
    return StrategicPlan(
        target_remaining=target_remaining,
        valid_combos=valid_combos,
        opener_pieces=opener_pieces,
        urgency_level=urgency_level
    )


def identify_burden_pieces(hand: List[Piece], plan: StrategicPlan, context: TurnPlayContext) -> List[Piece]:
    """
    Identify pieces that don't contribute to achieving declared target.
    
    Burden pieces are:
    - Not part of any winning combination that helps reach target
    - Too weak to win turns on their own when we need captures
    - Singles when we need to capture multiple piles efficiently
    
    Args:
        hand: Current pieces in hand
        plan: Strategic plan with valid combos and targets
        context: Current game context
        
    Returns:
        List of burden pieces to dispose of
    """
    if plan.target_remaining == 0:
        # At target - all pieces are burdens to avoid winning
        return hand.copy()
    
    # Track pieces that are useful for reaching target
    useful_pieces = set()
    
    # Consider all valid combos that could help reach target
    for play_type, pieces in plan.valid_combos:
        combo_size = len(pieces)
        
        # Skip combos larger than what we need
        if combo_size > plan.target_remaining:
            continue
            
        # This combo could help - mark pieces as useful
        for piece in pieces:
            useful_pieces.add(piece)
    
    # Identify burden pieces not in any useful combo
    burden_pieces = []
    
    for piece in hand:
        if piece not in useful_pieces:
            burden_pieces.append(piece)
        elif plan.target_remaining > 1 and piece.point <= 3 and piece in useful_pieces:
            # Weak singles (≤3 points) are burdens when we need multiple captures
            # They're unlikely to win turns on their own
            # Only mark as burden if it's ONLY in single combos, not pairs/triples
            in_multi_piece_combo = False
            for play_type, combo_pieces in plan.valid_combos:
                if piece in combo_pieces and len(combo_pieces) > 1:
                    in_multi_piece_combo = True
                    break
            
            if not in_multi_piece_combo and piece not in burden_pieces:
                burden_pieces.append(piece)
    
    return burden_pieces


def execute_starter_strategy(plan: StrategicPlan, context: TurnPlayContext) -> List[Piece]:
    """
    Execute strategy when we're the turn starter (leading).
    
    As starter, we control the piece count for this turn. Decision priority:
    1. If urgency critical AND have combo that captures needed piles: play it
    2. If have reliable opener AND target_remaining > 1: play opener to control next turn
    3. Otherwise: play weakest valid combination or burden pieces
    
    Args:
        plan: Strategic plan with available options
        context: Current game state
        
    Returns:
        List of pieces to play
    """
    required_count = context.required_piece_count
    
    # Critical urgency: Need to capture piles NOW
    if plan.urgency_level == "critical" and plan.target_remaining > 0:
        # Look for combos that would capture exactly what we need
        # Sort by size descending to prefer larger captures when critical
        sorted_combos = sorted(plan.valid_combos, key=lambda x: len(x[1]), reverse=True)
        
        for play_type, pieces in sorted_combos:
            if len(pieces) <= plan.target_remaining:
                # This combo would help us reach target
                # As starter, we can choose any count, so play this combo
                print(f"🎯 CRITICAL: Playing {play_type} to capture {len(pieces)} piles")
                return pieces
    
    # Check for burden disposal opportunity first (low urgency only)
    if plan.urgency_level == "low" and plan.target_remaining > 0:
        burden_pieces = identify_burden_pieces(context.my_hand, plan, context)
        
        if burden_pieces:
            # As starter, we can set the count to dispose burden pieces
            if required_count is None:
                # Prefer disposing 1-2 pieces at a time
                burden_count = min(len(burden_pieces), 2)
                required_count = burden_count
            
            # If we have enough burden pieces for required count
            if len(burden_pieces) >= required_count:
                # Sort by points to play weakest first
                sorted_burdens = sorted(burden_pieces, key=lambda p: p.point)
                pieces_to_play = sorted_burdens[:required_count]
                print(f"🗑️ Disposing burden pieces: {[str(p) for p in pieces_to_play]}")
                return pieces_to_play
    
    # Have opener and still need multiple piles (medium/high urgency)
    if plan.opener_pieces and plan.target_remaining > 1 and plan.urgency_level != "low":
        # Play single opener to control next turn
        if required_count is None or required_count == 1:
            opener = max(plan.opener_pieces, key=lambda p: p.point)
            print(f"🎯 Playing opener {opener} to control next turn")
            return [opener]
    
    # Medium urgency burden disposal (less aggressive than low urgency)
    if plan.urgency_level == "medium" and plan.target_remaining > 0:
        burden_pieces = identify_burden_pieces(context.my_hand, plan, context)
        
        if burden_pieces:
            # As starter, we can set the count to dispose burden pieces
            if required_count is None:
                # Prefer disposing 1-2 pieces at a time
                burden_count = min(len(burden_pieces), 2)
                required_count = burden_count
            
            # If we have enough burden pieces for required count
            if len(burden_pieces) >= required_count:
                # Sort by points to play weakest first
                sorted_burdens = sorted(burden_pieces, key=lambda p: p.point)
                pieces_to_play = sorted_burdens[:required_count]
                print(f"🗑️ Disposing burden pieces: {[str(p) for p in pieces_to_play]}")
                return pieces_to_play
    
    # Default: Play weakest valid combination
    # This helps dispose of burden pieces while staying in the game
    if required_count is None:
        # We set the count - prefer small plays to conserve pieces
        required_count = 1
    
    # Find weakest valid combo of required size
    sized_combos = [(play_type, pieces) for play_type, pieces in plan.valid_combos 
                    if len(pieces) == required_count]
    
    if sized_combos:
        # Play weakest valid combo
        weakest_combo = min(sized_combos, key=lambda x: sum(p.point for p in x[1]))
        print(f"🎯 Playing weakest {weakest_combo[0]} as starter")
        return weakest_combo[1]
    
    # No valid combo - play weakest pieces (will forfeit)
    sorted_hand = sorted(context.my_hand, key=lambda p: p.point)
    weakest = sorted_hand[:required_count]
    print(f"🎯 No valid combo, playing weakest {required_count} pieces")
    return weakest


def execute_responder_strategy(plan: StrategicPlan, context: TurnPlayContext) -> List[Piece]:
    """
    Execute strategy when we're responding to another player's lead.
    
    As responder, we must play the required piece count. Decision priority:
    1. If urgency critical AND can win turn that helps: try to win
    2. If at target (target_remaining == 0): avoid winning
    3. If current winner would hurt us: try to beat them
    4. Otherwise: play based on urgency and opportunity
    
    Args:
        plan: Strategic plan with available options
        context: Current game state with current_plays info
        
    Returns:
        List of pieces to play
    """
    required_count = context.required_piece_count or 1
    
    # Find current winning play
    current_winner = None
    winning_pieces = None
    if context.current_plays:
        # Find the winning play so far
        from backend.engine.rules import compare_plays
        
        for play_info in context.current_plays:
            if play_info.get('pieces'):
                pieces = play_info['pieces']
                if current_winner is None:
                    current_winner = play_info
                    winning_pieces = pieces
                else:
                    # Compare this play with current winner
                    comparison = compare_plays(pieces, winning_pieces)
                    if comparison == 1:  # This play beats current winner
                        current_winner = play_info
                        winning_pieces = pieces
    
    # If at target, must avoid winning
    if plan.target_remaining == 0:
        return avoid_overcapture_strategy(context.my_hand, context)
    
    # Critical urgency: Try to win if possible
    if plan.urgency_level == "critical" and plan.target_remaining > 0:
        # Find our best combo of required size
        sized_combos = [(play_type, pieces) for play_type, pieces in plan.valid_combos 
                        if len(pieces) == required_count]
        
        if sized_combos and winning_pieces:
            # Check if we can beat current winner
            from backend.engine.rules import compare_plays
            
            for play_type, pieces in sized_combos:
                if compare_plays(pieces, winning_pieces) == 1:
                    print(f"🎯 CRITICAL: Playing {play_type} to beat current winner and capture {len(pieces)} piles")
                    return pieces
        
        # Can't beat current winner but still critical - play our best anyway
        if sized_combos:
            best_combo = max(sized_combos, key=lambda x: sum(p.point for p in x[1]))
            print(f"🎯 CRITICAL: Playing best {best_combo[0]} (can't beat current winner)")
            return best_combo[1]
    
    # Normal urgency: Decide based on whether winning helps us
    if winning_pieces and plan.target_remaining > 0:
        # Check if we should try to win
        should_try_to_win = False
        
        # High urgency: Usually try to win
        if plan.urgency_level in ["high", "medium"]:
            should_try_to_win = True
        
        # Low urgency: Only win if it's easy/cheap
        elif plan.urgency_level == "low":
            # Check if we have a natural winning combo (not forcing it)
            sized_combos = [(play_type, pieces) for play_type, pieces in plan.valid_combos 
                            if len(pieces) == required_count]
            
            if sized_combos:
                from backend.engine.rules import compare_plays
                # Check if our weakest valid combo can win
                weakest_combo = min(sized_combos, key=lambda x: sum(p.point for p in x[1]))
                if compare_plays(weakest_combo[1], winning_pieces) == 1:
                    should_try_to_win = True  # Can win cheaply
        
        if should_try_to_win:
            # Try to find a winning play
            sized_combos = [(play_type, pieces) for play_type, pieces in plan.valid_combos 
                            if len(pieces) == required_count]
            
            if sized_combos:
                from backend.engine.rules import compare_plays
                
                # Find weakest combo that can win
                winning_combos = []
                for play_type, pieces in sized_combos:
                    if compare_plays(pieces, winning_pieces) == 1:
                        winning_combos.append((play_type, pieces))
                
                if winning_combos:
                    # Play weakest winning combo
                    weakest_winner = min(winning_combos, key=lambda x: sum(p.point for p in x[1]))
                    print(f"🎯 Playing {weakest_winner[0]} to win turn (need {plan.target_remaining} more piles)")
                    return weakest_winner[1]
    
    # Default: Play weakest valid combo or weakest pieces
    sized_combos = [(play_type, pieces) for play_type, pieces in plan.valid_combos 
                    if len(pieces) == required_count]
    
    if sized_combos:
        weakest_combo = min(sized_combos, key=lambda x: sum(p.point for p in x[1]))
        print(f"🎯 Playing weakest {weakest_combo[0]} as responder")
        return weakest_combo[1]
    
    # No valid combo - play weakest pieces
    sorted_hand = sorted(context.my_hand, key=lambda p: p.point)
    weakest = sorted_hand[:required_count]
    print(f"🎯 No valid combo, playing weakest {required_count} pieces as responder")
    return weakest


def check_opponent_disruption(hand: List[Piece], context: TurnPlayContext) -> Optional[List[Piece]]:
    """
    Check if any opponent would reach their declared target this turn.
    
    Strategy: If an opponent who is currently winning would transition from
    captured < declared to captured = declared, try to disrupt them.
    
    Args:
        hand: Bot's current hand
        context: Current game context with player states and current plays
        
    Returns:
        List of pieces to play for disruption, or None if no disruption needed
    """
    # Get piles at stake this turn
    piles_at_stake = context.required_piece_count or 1
    
    # Find disruption targets (opponents who would reach target)
    disruption_targets = []
    my_state = {'captured': context.my_captured, 'declared': context.my_declared}
    
    for player_name, state in context.player_states.items():
        captured = state.get('captured', 0)
        declared = state.get('declared', 0)
        
        # Skip if this is us (compare state values)
        if captured == context.my_captured and declared == context.my_declared:
            continue
            
        # Check if they would reach target this turn
        if captured < declared and captured + piles_at_stake == declared:
            disruption_targets.append({
                'player': player_name,
                'captured': captured,
                'declared': declared,
                'bonus_value': declared + 5  # Points they'd get
            })
    
    if not disruption_targets:
        return None  # No disruption opportunities
    
    # Find current winner
    current_winner = find_current_winner(context.current_plays)
    if not current_winner:
        return None  # No one to disrupt (we might be first to play)
    
    # Check if current winner is a disruption target
    winner_name = current_winner['player'].name if hasattr(current_winner['player'], 'name') else str(current_winner['player'])
    
    for target in disruption_targets:
        if target['player'] == winner_name:
            # This is our disruption target!
            print(f"🎯 Disruption opportunity: {winner_name} would reach {target['declared']}/{target['declared']} (bonus: {target['bonus_value']} pts)")
            
            # Find weakest pieces that can beat them
            disruption_pieces = find_disruption_play(hand, current_winner['pieces'], piles_at_stake)
            if disruption_pieces:
                print(f"🚫 Disrupting with: {[str(p) for p in disruption_pieces]}")
            return disruption_pieces
    
    return None  # Current winner is not a disruption target


def find_current_winner(current_plays: List[Dict]) -> Optional[Dict]:
    """Find who's currently winning this turn."""
    if not current_plays:
        return None
        
    winner = None
    winning_pieces = None
    
    for play_info in current_plays:
        if play_info.get('pieces'):
            pieces = play_info['pieces']
            if winner is None:
                winner = play_info
                winning_pieces = pieces
            else:
                # Import here to avoid circular imports
                from backend.engine.rules import compare_plays
                if compare_plays(pieces, winning_pieces) == 1:
                    winner = play_info
                    winning_pieces = pieces
    
    return winner


def find_disruption_play(hand: List[Piece], pieces_to_beat: List[Piece], required_count: int) -> Optional[List[Piece]]:
    """Find weakest valid combo that beats the target."""
    from backend.engine.ai import find_all_valid_combos
    from backend.engine.rules import compare_plays
    
    valid_combos = find_all_valid_combos(hand)
    sized_combos = [(play_type, pieces) for play_type, pieces in valid_combos 
                    if len(pieces) == required_count]
    
    # Find combos that can win
    winning_combos = []
    for play_type, pieces in sized_combos:
        if compare_plays(pieces, pieces_to_beat) == 1:
            winning_combos.append((play_type, pieces))
    
    if not winning_combos:
        return None  # Can't beat them
    
    # Return weakest winning combo
    weakest = min(winning_combos, key=lambda x: sum(p.point for p in x[1]))
    return weakest[1]