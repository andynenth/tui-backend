#!/usr/bin/env python3
"""
Regression test for zero streak declaration fix.

This test ensures that when a bot has declared 0 for 2 consecutive rounds,
the AI respects the must_declare_nonzero=True parameter and declares at least 1.

Bug: AI was returning 0 early when no pile room or no opener found,
bypassing the forbidden value checking logic.

Fix: Changed early returns to set declaration = 0 but continue to
forbidden value checking which enforces must_declare_nonzero.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare

def test_must_declare_nonzero_with_no_pile_room():
    """Test that bot declares 1 even with no pile room when must_declare_nonzero=True"""

    # Create a weak hand with no openers
    test_hand = [
        Piece("SOLDIER_RED"),      # 2 pts
        Piece("SOLDIER_RED"),      # 2 pts
        Piece("SOLDIER_BLACK"),    # 1 pts
        Piece("SOLDIER_BLACK"),    # 1 pts
        Piece("CANNON_BLACK"),     # 3 pts
        Piece("CANNON_RED"),       # 4 pts
        Piece("HORSE_BLACK"),      # 5 pts
        Piece("HORSE_RED")         # 6 pts
    ]

    # Simulate scenario where previous players declared 8 total (no pile room)
    previous_declarations = [3, 3, 2]  # Total = 8

    # Bot has zero streak and must declare non-zero
    declaration = choose_declare(
        hand=test_hand,
        is_first_player=False,
        position_in_order=3,
        previous_declarations=previous_declarations,
        must_declare_nonzero=True,
        verbose=True
    )

    assert declaration >= 1, f"Bot with zero streak must declare at least 1, got {declaration}"
    print(f"✅ Test passed: Bot correctly declared {declaration} (>= 1) with no pile room")
    return True


def test_must_declare_nonzero_with_no_opener():
    """Test that bot declares 1 when no opener found but must_declare_nonzero=True"""

    # Create a weak hand with no pieces >= 11 points
    test_hand = [
        Piece("SOLDIER_RED"),      # 2 pts
        Piece("SOLDIER_RED"),      # 2 pts
        Piece("SOLDIER_BLACK"),    # 1 pts
        Piece("SOLDIER_BLACK"),    # 1 pts
        Piece("CANNON_BLACK"),     # 3 pts
        Piece("CANNON_RED"),       # 4 pts
        Piece("HORSE_BLACK"),      # 5 pts
        Piece("ELEPHANT_BLACK")    # 9 pts (still not an opener)
    ]

    # Some pile room available but no strong pieces
    previous_declarations = [2, 2, 1]  # Total = 5, room = 3

    # Bot has zero streak and must declare non-zero
    declaration = choose_declare(
        hand=test_hand,
        is_first_player=False,
        position_in_order=3,
        previous_declarations=previous_declarations,
        must_declare_nonzero=True,
        verbose=True
    )

    assert declaration >= 1, f"Bot with zero streak must declare at least 1, got {declaration}"
    print(f"✅ Test passed: Bot correctly declared {declaration} (>= 1) with no opener")
    return True


def test_last_player_with_forbidden_sum_and_zero_streak():
    """Test that last player avoids both forbidden sum AND respects zero streak rule"""

    # Create a decent hand
    test_hand = [
        Piece("GENERAL_RED"),      # 14 pts - opener
        Piece("ADVISOR_RED"),      # 12 pts - opener
        Piece("ELEPHANT_RED"),     # 10 pts
        Piece("CHARIOT_RED"),      # 8 pts
        Piece("HORSE_RED"),        # 6 pts
        Piece("CANNON_RED"),       # 4 pts
        Piece("SOLDIER_RED"),      # 2 pts
        Piece("SOLDIER_RED")       # 2 pts
    ]

    # Previous declarations sum to 7, so can't declare 1 (would make 8)
    previous_declarations = [3, 2, 2]  # Total = 7

    # Bot has zero streak and must declare non-zero
    # So bot can't declare 0 (zero streak) or 1 (forbidden sum)
    declaration = choose_declare(
        hand=test_hand,
        is_first_player=False,
        position_in_order=3,
        previous_declarations=previous_declarations,
        must_declare_nonzero=True,
        verbose=True
    )

    assert declaration >= 2, f"Bot must declare at least 2 (avoiding 0 and 1), got {declaration}"
    assert declaration != 1, f"Bot must not declare 1 (would make sum 8)"
    print(f"✅ Test passed: Bot correctly declared {declaration} (avoiding both 0 and 1)")
    return True


if __name__ == "__main__":
    print("Running zero streak declaration fix tests...")
    print("=" * 60)

    success = True

    # Test 1: No pile room scenario
    try:
        test_must_declare_nonzero_with_no_pile_room()
    except AssertionError as e:
        print(f"❌ Test 1 failed: {e}")
        success = False

    print()

    # Test 2: No opener scenario
    try:
        test_must_declare_nonzero_with_no_opener()
    except AssertionError as e:
        print(f"❌ Test 2 failed: {e}")
        success = False

    print()

    # Test 3: Combined forbidden scenarios
    try:
        test_last_player_with_forbidden_sum_and_zero_streak()
    except AssertionError as e:
        print(f"❌ Test 3 failed: {e}")
        success = False

    print("=" * 60)
    if success:
        print("✅ All zero streak tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)