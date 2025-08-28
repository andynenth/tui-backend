#!/usr/bin/env python3
"""Detailed trace of Bot 3's decision to keep ADVISOR_REDs"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, get_overcapture_constraints, generate_strategic_plan,
    execute_responder_strategy, evaluate_hand
)

def main():
    # Bot 3's hand in Turn 1
    hand = [
        Piece("ADVISOR_RED"),     # 12 points
        Piece("ADVISOR_RED"),     # 12 points
        Piece("ADVISOR_BLACK"),   # 11 points
        Piece("CHARIOT_RED"),     # 8 points
        Piece("CHARIOT_BLACK"),   # 7 points
        Piece("SOLDIER_RED"),     # 2 points
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK"),   # 1 point
    ]
    
    print("Bot 3's Hand:")
    for p in hand:
        print(f"  - {p.kind}: {p.point} points")
    
    # Create context
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=hand,
        my_captured=0,
        my_declared=0,
        required_piece_count=4,
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Alexanderium": {"captured": 0, "declared": 7},
            "Bot 2": {"captured": 0, "declared": 0},
            "Bot 3": {"captured": 0, "declared": 0},
            "Bot 4": {"captured": 0, "declared": 0}
        }
    )
    
    print(f"\nBot 3 Status: captured={context.my_captured}, declared={context.my_declared}")
    print(f"Required pieces: {context.required_piece_count}")
    
    # Get overcapture constraints
    constraints = get_overcapture_constraints(context)
    print(f"\nOvercapture Constraints:")
    print(f"  - Risk level: {constraints.risk_level}")
    print(f"  - Max safe pieces: {constraints.max_safe_pieces}")
    print(f"  - Avoid piece counts: {constraints.avoid_piece_counts}")
    
    # Generate strategic plan
    plan = generate_strategic_plan(hand, context)
    print(f"\nStrategic Plan:")
    print(f"  - Target remaining: {plan.target_remaining}")
    print(f"  - Urgency: {plan.urgency_level}")
    print(f"  - Valid combos: {len(plan.valid_combos)}")
    
    # Print all valid combos
    print("\nAll valid combos found:")
    for combo_type, pieces in plan.valid_combos:
        piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
        total = sum(p.point for p in pieces)
        print(f"  - {combo_type}: {piece_str} = {total} pts")
    
    # Evaluate hand
    hand_eval = evaluate_hand(hand, context, plan)
    
    # Execute responder strategy
    print("\nExecuting responder strategy...")
    chosen = execute_responder_strategy(plan, context, hand_eval, constraints)
    
    if chosen:
        chosen_str = "+".join([f"{p.kind}({p.point})" for p in chosen])
        total = sum(p.point for p in chosen)
        print(f"\nFinal choice: {chosen_str} = {total} pts")
        
        # Check if ADVISOR_REDs were kept
        advisor_reds_in_hand = [p for p in hand if p.kind == "ADVISOR_RED"]
        advisor_reds_played = [p for p in chosen if p.kind == "ADVISOR_RED"]
        print(f"\nADVISOR_RED preservation:")
        print(f"  - In hand: {len(advisor_reds_in_hand)}")
        print(f"  - Played: {len(advisor_reds_played)}")
        print(f"  - Kept: {len(advisor_reds_in_hand) - len(advisor_reds_played)}")

if __name__ == "__main__":
    main()