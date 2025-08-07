# tests/ai_turn_play/test_target_achievement.py
"""
Tests for AI target achievement strategies.

Tests that AI makes strategic decisions to reach their declared pile target.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, StrategicPlan, 
    choose_strategic_play, generate_strategic_plan, execute_starter_strategy
)


def test_opener_strategy():
    """Test that AI plays opener when it needs multiple piles."""
    # Create hand with strong opener
    hand = [
        Piece("GENERAL_RED"),     # 14 points - opener
        Piece("ADVISOR_BLACK"),   # 11 points - opener
        Piece("HORSE_RED"),       # 6 points
        Piece("HORSE_RED"),       # 6 points - can make pair
        Piece("SOLDIER_BLACK"),   # 1 point
    ]
    
    # Context: need 3 more piles, am starter
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=1,
        my_declared=4,  # Need 3 more
        required_piece_count=None,  # Starter sets count
        turn_number=2,
        pieces_per_player=5,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Test strategic play
    result = choose_strategic_play(hand, context)
    
    # Should play single opener (GENERAL_RED)
    assert len(result) == 1, f"Expected 1 piece (opener), got {len(result)}"
    assert result[0].point >= 11, f"Expected opener (11+ points), got {result[0].point} points"
    
    print("✅ Test 1 passed: AI plays opener to control next turn")


def test_urgent_capture_scenario():
    """Test that AI plays combo immediately when urgency is critical."""
    # Create hand with three-of-a-kind
    hand = [
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK"),   # 1 point - THREE_OF_A_KIND
        Piece("CANNON_RED"),      # 4 points
        Piece("HORSE_BLACK"),     # 5 points
    ]
    
    # Context: need 3 piles, only 3 pieces left (critical!)
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=0,
        my_declared=3,  # Need 3 piles
        required_piece_count=None,  # Starter
        turn_number=6,  # Late in round
        pieces_per_player=3,  # Only 3 pieces left!
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Test
    result = choose_strategic_play(hand, context)
    
    # Should play THREE_OF_A_KIND to capture 3 piles
    assert len(result) == 3, f"Expected 3 pieces (THREE_OF_A_KIND), got {len(result)}"
    assert all(p.name == "SOLDIER" for p in result), "Expected all SOLDIERs"
    
    print("✅ Test 2 passed: AI plays combo immediately in critical situation")


def test_normal_progression():
    """Test normal play when not urgent."""
    # Create varied hand
    hand = [
        Piece("ADVISOR_RED"),     # 12 points
        Piece("ELEPHANT_BLACK"),  # 9 points
        Piece("CHARIOT_RED"),     # 8 points
        Piece("CANNON_BLACK"),    # 3 points
        Piece("SOLDIER_RED"),     # 2 points
        Piece("SOLDIER_BLACK"),   # 1 point
    ]
    
    # Context: need 2 piles, have plenty of time
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=1,
        my_declared=3,  # Need 2 more
        required_piece_count=2,  # Must play 2
        turn_number=2,
        pieces_per_player=6,
        am_i_starter=False,  # Not starter
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # For now, should delegate to classic AI
    result = choose_strategic_play(hand, context)
    assert len(result) == 2, f"Expected 2 pieces, got {len(result)}"
    
    print("✅ Test 3 passed: Normal progression handled")


def test_urgency_levels():
    """Test that urgency is calculated correctly."""
    hand = [Piece("SOLDIER_BLACK") for _ in range(5)]
    
    # Test 1: Already at target
    context1 = TurnPlayContext(
        my_hand=hand, my_captured=3, my_declared=3,
        required_piece_count=1, turn_number=1, pieces_per_player=5,
        am_i_starter=False, current_plays=[], revealed_pieces=[], player_states={}
    )
    plan1 = generate_strategic_plan(hand, context1)
    assert plan1.urgency_level == "none", f"Expected 'none', got {plan1.urgency_level}"
    
    # Test 2: Critical urgency
    context2 = TurnPlayContext(
        my_hand=hand, my_captured=0, my_declared=5,
        required_piece_count=1, turn_number=1, pieces_per_player=5,
        am_i_starter=False, current_plays=[], revealed_pieces=[], player_states={}
    )
    plan2 = generate_strategic_plan(hand, context2)
    assert plan2.urgency_level == "critical", f"Expected 'critical', got {plan2.urgency_level}"
    
    # Test 3: Low urgency
    context3 = TurnPlayContext(
        my_hand=hand, my_captured=0, my_declared=1,
        required_piece_count=1, turn_number=1, pieces_per_player=8,
        am_i_starter=False, current_plays=[], revealed_pieces=[], player_states={}
    )
    plan3 = generate_strategic_plan(hand, context3)
    assert plan3.urgency_level == "low", f"Expected 'low', got {plan3.urgency_level}"
    
    print("✅ Test 4 passed: Urgency levels calculated correctly")


def test_plan_generation():
    """Test strategic plan generation."""
    hand = [
        Piece("GENERAL_RED"),     # Opener
        Piece("ADVISOR_RED"),     # Opener
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK"),   # Can make pair
        Piece("CANNON_RED"),
    ]
    
    context = TurnPlayContext(
        my_hand=hand, my_captured=0, my_declared=3,
        required_piece_count=None, turn_number=1, pieces_per_player=5,
        am_i_starter=True, current_plays=[], revealed_pieces=[], player_states={}
    )
    
    plan = generate_strategic_plan(hand, context)
    
    # Check plan contents
    assert plan.target_remaining == 3, f"Expected 3 remaining, got {plan.target_remaining}"
    assert len(plan.opener_pieces) == 2, f"Expected 2 openers, got {len(plan.opener_pieces)}"
    assert len(plan.valid_combos) > 0, "Expected some valid combos"
    
    # Should find at least: singles, SOLDIER pair
    combo_types = [combo[0] for combo in plan.valid_combos]
    assert "SINGLE" in combo_types, "Should find singles"
    assert "PAIR" in combo_types, "Should find SOLDIER pair"
    
    print("✅ Test 5 passed: Plan generation works correctly")


if __name__ == "__main__":
    print("Testing target achievement strategies...\n")
    
    test_opener_strategy()
    test_urgent_capture_scenario()
    test_normal_progression()
    test_urgency_levels()
    test_plan_generation()
    
    print("\n✅ All target achievement tests passed!")