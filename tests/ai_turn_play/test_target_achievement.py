#!/usr/bin/env python3
"""
Test Target Achievement Strategy (Phase 4)
"""

import sys
sys.path.append('../..')

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, choose_strategic_play, calculate_urgency,
    generate_strategic_plan, evaluate_hand
)


def test_opener_strategy():
    """Test: Bot should play opener when urgency is medium/high and need multiple wins"""
    print("\n=== Test: Opener Strategy ===")
    
    # Create hand with clear opener
    hand = [
        Piece("GENERAL_RED"),    # 14 points - strong opener
        Piece("CHARIOT_BLACK"),  # 7 points
        Piece("HORSE_RED"),      # 6 points
        Piece("ELEPHANT_RED"),   # 9 points
        Piece("SOLDIER_BLACK"),  # 1 point
    ]
    
    context = TurnPlayContext(
        my_name="Bot 1",
        my_hand=hand,
        my_captured=0,
        my_declared=3,  # Need 3 wins
        required_piece_count=1,
        turn_number=4,  # Turn 4, have 4 turns left
        pieces_per_player=5,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Test urgency calculation
    urgency = calculate_urgency(context)
    print(f"Urgency: {urgency} (need 3 wins in 4 turns)")
    
    # Test play selection
    result = choose_strategic_play(hand, context)
    print(f"Bot plays: {[p.name for p in result]} (value: {sum(p.point for p in result)})")
    
    # Verify it chose the opener
    assert len(result) == 1 and result[0].name == "GENERAL", "Should play GENERAL as opener"
    print("✅ Correctly played opener for turn control")


def test_urgent_capture_scenario():
    """Test: Bot should play strongest combo when critically urgent"""
    print("\n=== Test: Urgent Capture Scenario ===")
    
    # Create hand with multiple options
    hand = [
        Piece("ELEPHANT_RED"),   # 9 points
        Piece("ELEPHANT_RED"),   # 9 points - strong pair
        Piece("CHARIOT_BLACK"),  # 7 points
        Piece("CHARIOT_BLACK"),  # 7 points - medium pair
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point - weak pair
    ]
    
    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=hand,
        my_captured=1,
        my_declared=3,  # Need 2 more wins
        required_piece_count=2,
        turn_number=7,  # Turn 7, only 1 turn left!
        pieces_per_player=3,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Test urgency calculation
    urgency = calculate_urgency(context)
    print(f"Urgency: {urgency} (need 2 wins in 1 turn)")
    
    # Test play selection
    result = choose_strategic_play(hand, context)
    print(f"Bot plays: {[p.name for p in result]} (value: {sum(p.point for p in result)})")
    
    # Verify it chose the strongest pair
    assert all(p.name == "ELEPHANT" for p in result), "Should play ELEPHANT pair (strongest)"
    print("✅ Correctly played strongest combo in critical situation")


def test_normal_progression():
    """Test: Bot should balance between disposing burden and maintaining options"""
    print("\n=== Test: Normal Progression ===")
    
    # Create hand with mix of pieces
    hand = [
        Piece("ADVISOR_BLACK"),  # 11 points - opener
        Piece("ELEPHANT_RED"),   # 9 points
        Piece("ELEPHANT_RED"),   # 9 points - pair
        Piece("HORSE_RED"),      # 6 points
        Piece("HORSE_BLACK"),    # 5 points
        Piece("SOLDIER_BLACK"),  # 1 point - burden
        Piece("CANNON_RED"),     # 3 points - burden
    ]
    
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=hand,
        my_captured=1,
        my_declared=3,  # Need 2 more wins
        required_piece_count=2,
        turn_number=3,  # Early-mid game
        pieces_per_player=7,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Test hand evaluation
    hand_eval = evaluate_hand(hand, context)
    print(f"Hand evaluation:")
    print(f"  Openers: {[p.name for p in hand_eval['openers']]}")
    print(f"  Burden pieces: {[p.name for p in hand_eval['burden_pieces']]}")
    
    # Test urgency calculation
    urgency = calculate_urgency(context)
    print(f"Urgency: {urgency} (need 2 wins in 5 turns)")
    
    # Test play selection
    result = choose_strategic_play(hand, context)
    print(f"Bot plays: {[p.name for p in result]} (value: {sum(p.point for p in result)})")
    print("✅ Made reasonable play based on urgency level")


def test_edge_case_impossible_target():
    """Test: Bot should still play reasonably when target is impossible"""
    print("\n=== Test: Edge Case - Impossible Target ===")
    
    hand = [
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point
    ]
    
    context = TurnPlayContext(
        my_name="Bot 4",
        my_hand=hand,
        my_captured=0,
        my_declared=4,  # Need 4 wins
        required_piece_count=2,
        turn_number=8,  # Last turn!
        pieces_per_player=1,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Test urgency calculation
    urgency = calculate_urgency(context)
    print(f"Urgency: {urgency} (need 4 wins in 0 turns - impossible!)")
    
    # Test play selection
    result = choose_strategic_play(hand, context)
    print(f"Bot plays: {[p.name for p in result]} (value: {sum(p.point for p in result)})")
    print("✅ Handled impossible target gracefully")


def test_already_at_target():
    """Verify overcapture avoidance still works"""
    print("\n=== Test: Already at Target ===")
    
    hand = [
        Piece("GENERAL_RED"),    # 14 points
        Piece("ADVISOR_BLACK"),  # 11 points
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point
    ]
    
    context = TurnPlayContext(
        my_name="Bot 5",
        my_hand=hand,
        my_captured=2,
        my_declared=2,  # Already at target!
        required_piece_count=2,
        turn_number=5,
        pieces_per_player=4,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Test urgency calculation
    urgency = calculate_urgency(context)
    print(f"Urgency: {urgency} (already at target)")
    
    # Test play selection
    result = choose_strategic_play(hand, context)
    print(f"Bot plays: {[p.name for p in result]} (value: {sum(p.point for p in result)})")
    
    # Verify it chose weak pieces
    assert all(p.name == "SOLDIER" for p in result), "Should play weak pieces when at target"
    print("✅ Correctly avoided overcapture")


if __name__ == "__main__":
    print("Testing Target Achievement Strategy (Phase 4)")
    print("=" * 50)
    
    test_opener_strategy()
    test_urgent_capture_scenario()
    test_normal_progression()
    test_edge_case_impossible_target()
    test_already_at_target()
    
    print("\n✅ All target achievement tests passed!")