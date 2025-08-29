#!/usr/bin/env python3
"""Test that Bot 2 now correctly disposes burden pieces instead of GENERAL_RED"""

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui/backend')

from engine.piece import Piece
from engine.ai_turn_strategy import (
    TurnPlayContext, StrategicPlan, execute_responder_strategy,
    evaluate_hand, generate_strategic_plan
)

# Create Bot 2's exact hand
bot2_hand = [
    Piece("GENERAL_RED"),      # 14 pts - opener
    Piece("CHARIOT_RED"),      # 8 pts - burden
    Piece("HORSE_RED"),        # 6 pts - burden  
    Piece("HORSE_BLACK"),      # 5 pts - combo
    Piece("CHARIOT_BLACK"),    # 7 pts - combo
    Piece("CANNON_RED"),       # 4 pts - reserve
    Piece("CANNON_BLACK")      # 3 pts - combo
]

# Create context
context = TurnPlayContext(
    my_name="Bot 2",
    my_hand=bot2_hand,
    my_captured=0,
    my_declared=4,
    required_piece_count=3,
    turn_number=2,
    pieces_per_player=7,
    am_i_starter=False,
    current_plays=[],
    revealed_pieces=[],
    player_states={
        "Bot 2": {"captured": 0, "declared": 4},
        "Alexanderium": {"captured": 1, "declared": 4},  # Actually needs 3
        "Bot 3": {"captured": 0, "declared": 0},          # Already at target
        "Bot 4": {"captured": 0, "declared": 2}           # Needs 2
    }
)

print("Testing Bot 2's decision with the fix:")
print("=" * 60)

# Generate plan
plan = generate_strategic_plan(bot2_hand, context)
print(f"Target remaining: {plan.target_remaining}")
print(f"Urgency: {plan.urgency_level}")

# Evaluate hand to populate plan details
hand_eval = evaluate_hand(bot2_hand, context, plan)

print(f"\nPlan assignments:")
print(f"  Openers: {[p.kind for p in plan.assigned_openers]}")
print(f"  Combos: {[(t, [p.kind for p in pieces]) for t, pieces in plan.assigned_combos]}")
print(f"  Reserve: {[p.kind for p in plan.reserve_pieces]}")
print(f"  Burden: {[p.kind for p in plan.burden_pieces]}")

# Create dummy hand_eval and constraints for the function call
from engine.ai_turn_strategy import OvercaptureConstraints
constraints = OvercaptureConstraints(
    max_safe_pieces=6,
    avoid_piece_counts=[],
    risky_play_types=[],
    risk_level="none"
)

# Execute responder strategy
pieces_to_play = execute_responder_strategy(plan, context, hand_eval, constraints)

print(f"\nBot 2 would play: {[p.kind for p in pieces_to_play]}")
print(f"Total points: {sum(p.point for p in pieces_to_play)}")

# Verify the fix
expected = ["CHARIOT_RED", "HORSE_RED", "CANNON_RED"]
actual = [p.kind for p in pieces_to_play]

print("\n" + "=" * 60)
if set(actual) == set(expected):
    print("✓ SUCCESS! Bot 2 correctly disposes burden pieces")
    print("  GENERAL_RED is preserved")
    print("  BLACK straight combo is preserved")
else:
    print("✗ FAILED! Bot 2 still has issues")
    print(f"  Expected: {expected}")
    print(f"  Actual: {actual}")
    
# Check specifically what happened
if "GENERAL_RED" in actual:
    print("  ERROR: Still disposing GENERAL_RED!")
if "CANNON_BLACK" in actual or "HORSE_BLACK" in actual or "CHARIOT_BLACK" in actual:
    print("  ERROR: Still breaking up BLACK straight combo!")