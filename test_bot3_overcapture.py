#!/usr/bin/env python3
"""
Test script to reproduce Bot 3's overcapture issue in round 3.
Bot 3 declared 0 but played a strong pair when they should have avoided winning.
"""

import sys
sys.path.append('backend')

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play


def test_bot3_round3_scenario():
    """Test the exact scenario where Bot 3 failed to avoid overcapture"""
    print("Testing Bot 3 Round 3 Overcapture Scenario")
    print("=" * 50)
    
    # Bot 3's actual hand at that moment (from game events)
    bot3_hand = [
        Piece("CHARIOT_BLACK"),  # 7 points
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("CHARIOT_RED"),   # 8 points
        Piece("CHARIOT_RED"),   # 8 points
        Piece("HORSE_BLACK"),    # 5 points
    ]
    
    # Context at that moment
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=bot3_hand,
        my_captured=0,  # Bot 3 had 0 piles
        my_declared=0,  # Bot 3 declared 0
        required_piece_count=2,  # Required to play 2 pieces (pair)
        turn_number=2,
        pieces_per_player=len(bot3_hand),
        am_i_starter=False,  # Bot 4 was leading
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Alexanderium": {"captured": 0, "declared": 3},
            "Bot 2": {"captured": 0, "declared": 5},
            "Bot 3": {"captured": 0, "declared": 0},
            "Bot 4": {"captured": 1, "declared": 6}
        }
    )
    
    # Call the strategic AI
    print(f"\nContext: Bot 3 has {context.my_captured} piles, declared {context.my_declared}")
    print(f"Required to play: {context.required_piece_count} pieces")
    print(f"Hand: {[f'{p.name}({p.point})' for p in bot3_hand]}")
    
    result = choose_strategic_play(bot3_hand, context)
    
    print(f"\nResult: {[f'{p.name}({p.point})' for p in result]}")
    print(f"Total value: {sum(p.point for p in result)}")
    
    # Check if it correctly avoided playing strong pieces
    if sum(p.point for p in result) == 16:  # Two CHARIOTs = 16
        print("\n❌ FAIL: Bot played strong CHARIOT pair (16 points) when at target!")
        print("   This would win the turn and capture 2 piles!")
    else:
        print("\n✅ PASS: Bot correctly avoided playing strong pieces")
    
    return result


def test_simple_overcapture():
    """Test a simple overcapture scenario"""
    print("\n\nTesting Simple Overcapture Scenario")
    print("=" * 50)
    
    hand = [
        Piece("GENERAL_RED"),    # 14 points
        Piece("ADVISOR_BLACK"),  # 11 points
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_RED"),    # 2 points
    ]
    
    context = TurnPlayContext(
        my_name="Test Bot",
        my_hand=hand,
        my_captured=2,
        my_declared=2,  # At target!
        required_piece_count=2,
        turn_number=1,
        pieces_per_player=4,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    print(f"\nContext: Bot has {context.my_captured} piles, declared {context.my_declared}")
    print(f"Required to play: {context.required_piece_count} pieces")
    print(f"Hand: {[f'{p.name}({p.point})' for p in hand]}")
    
    result = choose_strategic_play(hand, context)
    
    print(f"\nResult: {[f'{p.name}({p.point})' for p in result]}")
    print(f"Total value: {sum(p.point for p in result)}")
    
    expected_value = 3  # SOLDIER_BLACK(1) + SOLDIER_RED(2)
    if sum(p.point for p in result) == expected_value:
        print("\n✅ PASS: Bot correctly played weakest pieces")
    else:
        print(f"\n❌ FAIL: Expected value {expected_value}, got {sum(p.point for p in result)}")


if __name__ == "__main__":
    test_bot3_round3_scenario()
    test_simple_overcapture()