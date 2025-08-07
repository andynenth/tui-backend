#!/usr/bin/env python3
"""
Direct test of AI turn strategy overcapture avoidance.
Run this to verify the feature is working.
"""

import sys
sys.path.append('.')

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play


def test_overcapture_avoidance():
    """Test that bot at target plays weak pieces."""
    print("Testing overcapture avoidance...")
    
    # Create a hand with various pieces
    hand = [
        Piece("GENERAL_RED"),      # 14 points
        Piece("ADVISOR_BLACK"),    # 11 points
        Piece("ELEPHANT_RED"),     # 10 points
        Piece("CANNON_BLACK"),     # 4 points
        Piece("SOLDIER_RED"),      # 2 points
        Piece("SOLDIER_BLACK"),    # 1 point
    ]
    
    # Test 1: Bot at target (should play weak)
    context_at_target = TurnPlayContext(
        my_name="Bot1",
        my_hand=hand,
        my_captured=2,  # At target
        my_declared=2,  # At target
        required_piece_count=2,
        turn_number=3,
        pieces_per_player=6,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={"Bot1": {"captured": 2, "declared": 2}}
    )
    
    result = choose_strategic_play(hand, context_at_target)
    print(f"\nTest 1 - Bot at target (2/2):")
    print(f"  Played: {[f'{p.name}({p.point})' for p in result]}")
    print(f"  Total points: {sum(p.point for p in result)}")
    
    # Verify weakest pieces were played
    assert len(result) == 2, f"Should play 2 pieces, played {len(result)}"
    points = sorted([p.point for p in result])
    assert points == [1, 2], f"Should play weakest pieces (1,2), played {points}"
    print("  ✅ PASSED: Bot correctly played weakest pieces to avoid overcapture")
    
    # Test 2: Bot below target (should play strong)
    context_below_target = TurnPlayContext(
        my_name="Bot1",
        my_hand=hand,
        my_captured=0,  # Below target
        my_declared=2,  # Need 2 more
        required_piece_count=2,
        turn_number=3,
        pieces_per_player=6,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={"Bot1": {"captured": 0, "declared": 2}}
    )
    
    result2 = choose_strategic_play(hand, context_below_target)
    print(f"\nTest 2 - Bot below target (0/2):")
    print(f"  Played: {[f'{p.name}({p.point})' for p in result2]}")
    print(f"  Total points: {sum(p.point for p in result2)}")
    
    # Verify strong pieces were played
    assert len(result2) == 2, f"Should play 2 pieces, played {len(result2)}"
    points2 = sorted([p.point for p in result2], reverse=True)
    assert points2[0] >= 10, f"Should play strong pieces, but strongest was {points2[0]}"
    print("  ✅ PASSED: Bot correctly played strong pieces to win piles")
    
    # Test 3: Bot as starter at target (must play valid combo)
    context_starter = TurnPlayContext(
        my_name="Bot1", 
        my_hand=hand,
        my_captured=1,
        my_declared=1,  # At target
        required_piece_count=None,  # Starter sets the count
        turn_number=5,
        pieces_per_player=6,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={"Bot1": {"captured": 1, "declared": 1}}
    )
    
    result3 = choose_strategic_play(hand, context_starter)
    print(f"\nTest 3 - Bot as starter at target (1/1):")
    print(f"  Played: {[f'{p.name}({p.point})' for p in result3]}")
    print(f"  Total points: {sum(p.point for p in result3)}")
    
    # Verify single weak piece was played
    assert len(result3) == 1, f"Starter should play 1 piece, played {len(result3)}"
    assert result3[0].point <= 2, f"Should play weak piece, played {result3[0].point}"
    print("  ✅ PASSED: Starter bot correctly played single weak piece")
    
    print("\n🎉 All tests passed! Overcapture avoidance is working correctly.")


if __name__ == "__main__":
    test_overcapture_avoidance()