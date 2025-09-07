#!/usr/bin/env python3
"""
Debug the basic AI never-win combo avoidance
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.piece import Piece
from backend.engine.ai import (
    choose_best_play,
    is_never_win_combo_basic,
    get_play_type,
    is_valid_play,
)
from itertools import combinations


def debug_hand(hand, required_count):
    """Debug all possible plays for a hand"""

    print(f"\nDebugging hand with {len(hand)} pieces, required={required_count}")
    print(f"Hand: {[f'{p.name}({p.point})' for p in hand]}")
    print("-" * 60)

    valid_plays = []
    never_win_plays = []

    for combo in combinations(hand, required_count):
        pieces = list(combo)
        if is_valid_play(pieces):
            play_type = get_play_type(pieces)
            total = sum(p.point for p in pieces)
            is_never_win = is_never_win_combo_basic(play_type, pieces)

            play_info = {
                "pieces": pieces,
                "type": play_type,
                "total": total,
                "is_never_win": is_never_win,
                "points": sorted([p.point for p in pieces]),
            }

            if is_never_win:
                never_win_plays.append(play_info)
            else:
                valid_plays.append(play_info)

    print(f"Valid plays (not never-win):")
    for play in sorted(valid_plays, key=lambda x: x["total"], reverse=True):
        print(f"  {play['type']:15} points={play['points']} total={play['total']}")

    print(f"\nNever-win plays:")
    for play in never_win_plays:
        print(f"  {play['type']:15} points={play['points']} total={play['total']}")

    # Now call choose_best_play
    result = choose_best_play(hand, required_count, verbose=False)
    result_type = get_play_type(result)
    result_total = sum(p.point for p in result)
    result_points = sorted([p.point for p in result])

    print(f"\nchose_best_play result:")
    print(f"  Type: {result_type}")
    print(f"  Points: {result_points}")
    print(f"  Total: {result_total}")
    print(f"  Is never-win: {is_never_win_combo_basic(result_type, result)}")


# Test cases
print("Debug Basic AI Never-Win Avoidance")
print("=" * 60)

# Test 1: Hand with straight options
hand1 = [
    Piece("CANNON_BLACK"),  # 3 points
    Piece("CANNON_RED"),  # 4 points
    Piece("HORSE_BLACK"),  # 5 points
    Piece("CHARIOT_RED"),  # 8 points
    Piece("CHARIOT_BLACK"),  # 7 points
]
debug_hand(hand1, 3)

# Test 2: Another test case
hand2 = [
    Piece("SOLDIER_BLACK"),  # 1 point
    Piece("SOLDIER_BLACK"),  # 1 point
    Piece("CANNON_RED"),  # 4 points
    Piece("CHARIOT_RED"),  # 8 points
]
debug_hand(hand2, 2)
