#!/usr/bin/env python3
"""
Regression test for object comparison fix in responder disposal strategy.

This test ensures that the disposal strategy correctly identifies pieces
by comparing piece.kind instead of object identity.

Bug: The disposal strategy was using `if p in context.my_hand` which
compared object identity. Since plan pieces and hand pieces were different
objects (even with same kind), this always failed, causing incorrect disposal.

Fix: Compare by piece.kind instead of object identity.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, StrategicPlan, execute_responder_strategy,
    evaluate_hand, generate_strategic_plan, OvercaptureConstraints
)

def test_responder_disposal_with_burden_pieces():
    """Test that responder correctly disposes burden pieces when they exist."""

    # Create a hand with clear role assignments
    test_hand = [
        Piece("GENERAL_RED"),      # 14 pts - will be opener
        Piece("ADVISOR_RED"),      # 12 pts - will be opener
        Piece("ELEPHANT_RED"),     # 10 pts - will be burden
        Piece("CHARIOT_RED"),      # 8 pts - will be burden
        Piece("HORSE_RED"),        # 6 pts - will be burden
        Piece("CANNON_RED"),       # 4 pts - will be reserve
        Piece("SOLDIER_RED")       # 2 pts - will be reserve
    ]

    # Context where bot needs 2 piles (so 2 openers are enough)
    context = TurnPlayContext(
        my_name="Test Bot",
        my_hand=test_hand,
        my_captured=2,
        my_declared=4,  # Target = 4, captured = 2, so needs 2 more
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

    # Generate and evaluate plan
    plan = generate_strategic_plan(test_hand, context)
    hand_eval = evaluate_hand(test_hand, context, plan)

    # Verify plan assignments
    # With 1 combo as secured win, bot only needs 1 opener for 2 total wins
    assert len(plan.assigned_openers) >= 1, f"Expected at least 1 opener, got {len(plan.assigned_openers)}"
    assert len(plan.burden_pieces) >= 2, f"Expected at least 2 burden pieces, got {len(plan.burden_pieces)}"

    # Get burden piece kinds
    burden_kinds = {p.kind for p in plan.burden_pieces}

    # Execute responder strategy
    constraints = OvercaptureConstraints(
        max_safe_pieces=6,
        avoid_piece_counts=[],
        risky_play_types=[],
        risk_level="none"
    )

    pieces_to_play = execute_responder_strategy(plan, context, hand_eval, constraints)

    # Verify disposal
    assert len(pieces_to_play) == 3, f"Should play 3 pieces, got {len(pieces_to_play)}"

    # Check that burden pieces are disposed
    played_kinds = {p.kind for p in pieces_to_play}
    burden_disposed = played_kinds.intersection(burden_kinds)
    assert len(burden_disposed) >= 2, f"Should dispose at least 2 burden pieces, disposed {burden_disposed}"

    # Check that openers are NOT disposed
    opener_kinds = {p.kind for p in plan.assigned_openers}
    openers_disposed = played_kinds.intersection(opener_kinds)
    assert len(openers_disposed) == 0, f"Should not dispose openers, but disposed {openers_disposed}"

    print("✅ Test passed: Responder correctly disposes burden pieces")
    return True


def test_empty_burden_scenario():
    """Test behavior when all pieces are assigned (no burden pieces)."""

    # Create Bot 2's scenario - all pieces will be assigned
    test_hand = [
        Piece("GENERAL_RED"),      # Opener
        Piece("CHARIOT_RED"),      # Combo 1
        Piece("HORSE_RED"),        # Combo 1
        Piece("CANNON_RED"),       # Combo 1
        Piece("CHARIOT_BLACK"),    # Combo 2
        Piece("HORSE_BLACK"),      # Combo 2
        Piece("CANNON_BLACK")      # Combo 2
    ]

    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=test_hand,
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
            "Player 2": {"captured": 1, "declared": 4},
            "Player 3": {"captured": 0, "declared": 0},
            "Player 4": {"captured": 0, "declared": 2}
        }
    )

    # Generate and evaluate plan
    plan = generate_strategic_plan(test_hand, context)
    hand_eval = evaluate_hand(test_hand, context, plan)

    # Verify all pieces are assigned (no burden)
    assert len(plan.burden_pieces) == 0, f"Expected 0 burden pieces, got {len(plan.burden_pieces)}"

    # Execute responder strategy
    constraints = OvercaptureConstraints(
        max_safe_pieces=6,
        avoid_piece_counts=[],
        risky_play_types=[],
        risk_level="none"
    )

    pieces_to_play = execute_responder_strategy(plan, context, hand_eval, constraints)

    # Should still return 3 pieces even with no burden
    assert len(pieces_to_play) == 3, f"Should play 3 pieces, got {len(pieces_to_play)}"

    print("✅ Test passed: Responder handles empty burden scenario")
    return True


if __name__ == "__main__":
    print("Running object comparison regression tests...")
    print("=" * 60)

    success = True

    # Test 1: Normal scenario with burden pieces
    try:
        test_responder_disposal_with_burden_pieces()
    except AssertionError as e:
        print(f"❌ Test 1 failed: {e}")
        success = False

    # Test 2: Edge case with no burden pieces
    try:
        test_empty_burden_scenario()
    except AssertionError as e:
        print(f"❌ Test 2 failed: {e}")
        success = False

    print("=" * 60)
    if success:
        print("✅ All object comparison tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
