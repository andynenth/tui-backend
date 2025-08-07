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
    
    # For now, delegate to existing logic
    print(f"📈 {context.my_name} below target ({context.my_captured}/{context.my_declared}) - using standard play selection")
    from backend.engine.ai import choose_best_play
    result = choose_best_play(hand, context.required_piece_count)
    
    # Validate result
    if not validate_play_result(result, hand, context):
        print(f"⚠️ Strategic AI: Invalid result from basic play, using fallback")
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