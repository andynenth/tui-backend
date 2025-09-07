#!/usr/bin/env python3
"""
Test that the basic AI (choose_best_play) now avoids never-win combos
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.piece import Piece
from backend.engine.ai import choose_best_play


def test_basic_ai_avoids_never_win():
    """Test that basic AI avoids never-win combos"""

    print("Testing basic AI with never-win combo avoidance:")
    print("=" * 60)

    # Test 1: Hand with only minimum BLACK straight available
    print("\nTest 1: Hand with only minimum BLACK straight")
    hand1 = [
        Piece("CANNON_BLACK"),  # 3 points
        Piece("HORSE_BLACK"),  # 5 points
        Piece("CHARIOT_BLACK"),  # 7 points
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point
    ]

    # Ask for 3 pieces - should avoid the never-win straight
    result1 = choose_best_play(hand1, 3, verbose=False)
    result1_points = [p.point for p in sorted(result1, key=lambda x: x.point)]
    print(f"  Hand: {[f'{p.name}({p.point})' for p in hand1]}")
    print(f"  Result: {[f'{p.name}({p.point})' for p in result1]}")
    print(f"  Points: {result1_points}")
    print(
        f"  Avoided never-win straight [3,5,7]: {'✓' if result1_points != [3,5,7] else '✗'}"
    )

    # Test 2: Hand with SOLDIER_BLACK pair as only valid play
    print("\nTest 2: Hand with SOLDIER_BLACK pair")
    hand2 = [
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("CANNON_RED"),  # 4 points
        Piece("CHARIOT_RED"),  # 6 points
    ]

    # Ask for 2 pieces - should avoid SOLDIER_BLACK pair if possible
    result2 = choose_best_play(hand2, 2, verbose=False)
    result2_points = sorted([p.point for p in result2])
    print(f"  Hand: {[f'{p.name}({p.point})' for p in hand2]}")
    print(f"  Result: {[f'{p.name}({p.point})' for p in result2]}")
    print(f"  Points: {result2_points}")
    print(f"  Avoided never-win pair [1,1]: {'✓' if result2_points != [1,1] else '✗'}")

    # Test 3: Hand with better alternatives
    print("\nTest 3: Hand with better straight available")
    hand3 = [
        Piece("CANNON_BLACK"),  # 3 points
        Piece("CANNON_RED"),  # 4 points
        Piece("HORSE_BLACK"),  # 5 points
        Piece("CHARIOT_RED"),  # 6 points
        Piece("CHARIOT_BLACK"),  # 7 points
    ]

    # Ask for 3 pieces - should pick the mixed straight [4,5,6] over [3,5,7]
    result3 = choose_best_play(hand3, 3, verbose=False)
    result3_points = sorted([p.point for p in result3])
    print(f"  Hand: {[f'{p.name}({p.point})' for p in hand3]}")
    print(f"  Result: {[f'{p.name}({p.point})' for p in result3]}")
    print(f"  Points: {result3_points}")
    print(f"  Chose better straight: {'✓' if result3_points == [4,5,6] else '✗'}")

    # Test 4: No choice but never-win combo
    print("\nTest 4: No choice but never-win combo")
    hand4 = [
        Piece("CANNON_BLACK"),  # 3 points
        Piece("HORSE_BLACK"),  # 5 points
        Piece("CHARIOT_BLACK"),  # 7 points
    ]

    # Only 3 pieces, all form never-win straight
    result4 = choose_best_play(hand4, 3, verbose=False)
    result4_points = sorted([p.point for p in result4])
    print(f"  Hand: {[f'{p.name}({p.point})' for p in hand4]}")
    print(f"  Result: {[f'{p.name}({p.point})' for p in result4]}")
    print(f"  Points: {result4_points}")
    print(
        f"  Forced to play never-win (no alternative): {'✓' if result4_points == [3,5,7] else '✗'}"
    )


if __name__ == "__main__":
    test_basic_ai_avoids_never_win()
