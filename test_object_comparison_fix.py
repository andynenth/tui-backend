#!/usr/bin/env python3
"""Test the object comparison fix with a scenario that has burden pieces"""

import sys
sys.path.insert(0, '/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, StrategicPlan, execute_responder_strategy,
    evaluate_hand, generate_strategic_plan, OvercaptureConstraints
)

# Create a hand that will have burden pieces
test_hand = [
    Piece("GENERAL_RED"),      # 14 pts - opener
    Piece("ADVISOR_RED"),      # 12 pts - opener
    Piece("ELEPHANT_RED"),     # 10 pts - burden (not opener)
    Piece("CHARIOT_RED"),      # 8 pts - burden
    Piece("HORSE_RED"),        # 6 pts - burden  
    Piece("CANNON_RED"),       # 4 pts - reserve
    Piece("SOLDIER_RED")       # 2 pts - reserve
]

# Create context where bot needs only 2 piles
context = TurnPlayContext(
    my_name="Test Bot",
    my_hand=test_hand,
    my_captured=2,
    my_declared=4,  # Needs 2 more
    required_piece_count=3,
    turn_number=5,
    pieces_per_player=7,
    am_i_starter=False,
    current_plays=[],
    revealed_pieces=[],
    player_states={
        "Test Bot": {"captured": 2, "declared": 4},
        "Player 2": {"captured": 3, "declared": 4},
        "Player 3": {"captured": 0, "declared": 0},
        "Player 4": {"captured": 1, "declared": 2}
    }
)

print("Testing object comparison fix with burden pieces:")
print("=" * 60)

# Generate plan
plan = generate_strategic_plan(test_hand, context)
print(f"Target remaining: {plan.target_remaining}")
print(f"Urgency: {plan.urgency_level}")

# Evaluate hand to populate plan details
hand_eval = evaluate_hand(test_hand, context, plan)

print(f"\nPlan assignments:")
print(f"  Openers: {[p.kind for p in plan.assigned_openers]}")
print(f"  Combos: {[(t, [p.kind for p in pieces]) for t, pieces in plan.assigned_combos]}")
print(f"  Reserve: {[p.kind for p in plan.reserve_pieces]}")
print(f"  Burden: {[p.kind for p in plan.burden_pieces]}")

# Create test to verify object comparison works
print("\nTesting object comparison fix:")

# Simulate the old broken logic
old_burden_in_hand = [p for p in plan.burden_pieces if p in context.my_hand]
print(f"OLD logic (object identity): {len(old_burden_in_hand)} burden pieces found")

# Test the new fixed logic
plan_burden_kinds = {p.kind for p in plan.burden_pieces}
new_burden_in_hand = [p for p in context.my_hand if p.kind in plan_burden_kinds]
print(f"NEW logic (kind comparison): {len(new_burden_in_hand)} burden pieces found")
print(f"Burden pieces found: {[p.kind for p in new_burden_in_hand]}")

# Execute responder strategy
constraints = OvercaptureConstraints(
    max_safe_pieces=6,
    avoid_piece_counts=[],
    risky_play_types=[],
    risk_level="none"
)

pieces_to_play = execute_responder_strategy(plan, context, hand_eval, constraints)

print(f"\nBot would play: {[p.kind for p in pieces_to_play]}")

# Verify the fix
has_burden = any(p.kind in plan_burden_kinds for p in pieces_to_play)
has_opener = any(p in plan.assigned_openers for p in pieces_to_play)

print("\n" + "=" * 60)
if has_burden and not has_opener:
    print("✓ SUCCESS! Object comparison fix works correctly")
    print("  Bot correctly disposes burden pieces")
    print("  Openers are preserved")
else:
    print("✗ FAILED! Still has issues")
    if has_opener:
        print("  ERROR: Disposing openers when burden pieces exist!")
    if not has_burden:
        print("  ERROR: Not disposing burden pieces!")