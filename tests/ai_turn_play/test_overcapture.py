# tests/ai_turn_play/test_overcapture.py
"""
Tests for overcapture avoidance strategy.

When AI has already captured their declared number of piles,
they must avoid winning any more turns.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play, avoid_overcapture_strategy


def test_avoid_overcapture_when_at_target():
    """Test that AI plays weakest pieces when at declared target."""
    # Create test hand
    hand = [
        Piece("GENERAL_RED"),     # 14 points
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK")    # 1 point
    ]
    
    # Create context where player is at target
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=2,
        my_declared=2,  # At target!
        required_piece_count=2,
        turn_number=3,
        pieces_per_player=3,
        am_i_starter=False,  # Not starter, so any pieces are fine
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Test strategic play
    result = choose_strategic_play(hand, context)
    
    # Should return the two SOLDIER_BLACK pieces (weakest)
    assert len(result) == 2, f"Expected 2 pieces, got {len(result)}"
    assert all(p.name == "SOLDIER" and p.color == "BLACK" for p in result), \
        f"Expected SOLDIER_BLACK pieces, got {[str(p) for p in result]}"
    
    print("✅ Test 1 passed: AI avoids strong pieces when at target")


def test_avoid_overcapture_as_starter():
    """Test that AI finds weakest valid combo when starter at target."""
    # Create test hand with valid pairs
    hand = [
        Piece("GENERAL_RED"),     # 14 points
        Piece("GENERAL_RED"),     # 14 points - can make strong pair
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK"),   # 1 point - can make weak pair
        Piece("CANNON_RED")       # 4 points
    ]
    
    # Create context where player is starter and at target
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=3,
        my_declared=3,  # At target!
        required_piece_count=2,
        turn_number=2,
        pieces_per_player=5,
        am_i_starter=True,  # Starter must play valid combo
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Test avoid overcapture strategy directly
    result = avoid_overcapture_strategy(hand, context)
    
    # Should return SOLDIER_BLACK pair (weakest valid combo)
    assert len(result) == 2, f"Expected 2 pieces, got {len(result)}"
    assert all(p.name == "SOLDIER" and p.color == "BLACK" for p in result), \
        f"Expected SOLDIER_BLACK pair, got {[str(p) for p in result]}"
    
    print("✅ Test 2 passed: AI plays weakest valid combo as starter")


def test_plays_weakest_valid_combo_when_available():
    """Test that AI plays weakest valid combo when available, even if strong."""
    # Create hand that forms a STRAIGHT
    hand = [
        Piece("GENERAL_RED"),     # 14 points
        Piece("ADVISOR_RED"),     # 12 points
        Piece("ELEPHANT_RED"),    # 10 points - These 3 form a STRAIGHT
        Piece("CHARIOT_BLACK"),   # 7 points
        Piece("HORSE_BLACK")      # 5 points
    ]
    
    # Context: need to play 3 pieces, at target
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=4,
        my_declared=4,  # At target!
        required_piece_count=3,
        turn_number=2,
        pieces_per_player=5,
        am_i_starter=True,  # Starter must play valid combo
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Test
    result = avoid_overcapture_strategy(hand, context)
    
    # Should return the STRAIGHT (only valid 3-piece combo)
    assert len(result) == 3, f"Expected 3 pieces, got {len(result)}"
    # The STRAIGHT is GENERAL-ADVISOR-ELEPHANT
    piece_names = sorted([p.name for p in result])
    expected_names = sorted(["GENERAL", "ADVISOR", "ELEPHANT"])
    assert piece_names == expected_names, \
        f"Expected STRAIGHT pieces, got {piece_names}"
    
    print("✅ Test 3 passed: AI plays valid combo (even if strong) when starter")


def test_single_piece_at_target():
    """Test single piece play when at target."""
    hand = [
        Piece("GENERAL_RED"),     # 14 points
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("CANNON_RED")       # 4 points
    ]
    
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=5,
        my_declared=5,  # At target!
        required_piece_count=1,
        turn_number=6,
        pieces_per_player=3,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    result = choose_strategic_play(hand, context)
    
    # Should play SOLDIER_BLACK (weakest)
    assert len(result) == 1, f"Expected 1 piece, got {len(result)}"
    assert result[0].name == "SOLDIER" and result[0].color == "BLACK", \
        f"Expected SOLDIER_BLACK, got {result[0]}"
    
    print("✅ Test 4 passed: AI plays weakest single piece when at target")


if __name__ == "__main__":
    print("Testing overcapture avoidance strategies...\n")
    
    test_avoid_overcapture_when_at_target()
    test_avoid_overcapture_as_starter()
    test_plays_weakest_valid_combo_when_available()
    test_single_piece_at_target()
    
    print("\n✅ All overcapture avoidance tests passed!")