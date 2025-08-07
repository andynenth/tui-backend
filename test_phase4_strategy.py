#!/usr/bin/env python3
"""
Test Phase 4: Target Achievement Strategy implementation
"""

import sys
sys.path.append('.')

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, choose_strategic_play, evaluate_hand, 
    calculate_urgency, generate_strategic_plan
)


def test_urgency_calculation():
    """Test urgency calculation logic"""
    print("\n=== Testing Urgency Calculation ===")
    
    # Test 1: Critical urgency (need every turn)
    context = TurnPlayContext(
        my_name="Bot 1",
        my_hand=[],
        my_captured=0,
        my_declared=3,
        required_piece_count=2,
        turn_number=5,  # 3 turns remaining
        pieces_per_player=3,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    urgency = calculate_urgency(context)
    print(f"Test 1 - Need 3 piles in 3 turns: {urgency} (expected: critical)")
    
    # Test 2: High urgency 
    context.my_declared = 2
    urgency = calculate_urgency(context)
    print(f"Test 2 - Need 2 piles in 3 turns: {urgency} (expected: high)")
    
    # Test 3: Low urgency
    context.turn_number = 2  # 6 turns remaining
    context.my_declared = 2
    urgency = calculate_urgency(context)
    print(f"Test 3 - Need 2 piles in 6 turns: {urgency} (expected: low)")
    
    # Test 4: Already at target
    context.my_captured = 2
    urgency = calculate_urgency(context)
    print(f"Test 4 - Already at target: {urgency} (expected: none)")


def test_hand_evaluation():
    """Test hand evaluation and categorization"""
    print("\n=== Testing Hand Evaluation ===")
    
    # Create a test hand with various pieces
    hand = [
        Piece("GENERAL_RED"),    # 14 points - opener
        Piece("ADVISOR_BLACK"),  # 11 points - opener
        Piece("ELEPHANT_RED"),   # 9 points
        Piece("ELEPHANT_RED"),   # 9 points - pair
        Piece("SOLDIER_BLACK"),  # 1 point - burden
        Piece("SOLDIER_BLACK"),  # 1 point - burden
        Piece("CHARIOT_BLACK"),  # 7 points
        Piece("HORSE_RED")       # 6 points
    ]
    
    context = TurnPlayContext(
        my_name="Bot 1",
        my_hand=hand,
        my_captured=0,
        my_declared=3,
        required_piece_count=2,
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    hand_eval = evaluate_hand(hand, context)
    
    print(f"Openers ({len(hand_eval['openers'])}): {[p.name for p in hand_eval['openers']]}")
    print(f"Burden pieces ({len(hand_eval['burden_pieces'])}): {[p.name for p in hand_eval['burden_pieces']]}")
    print(f"Combo pieces ({len(hand_eval['combo_pieces'])}): {[p.name for p in hand_eval['combo_pieces']]}")
    print(f"Total valid combos: {len(hand_eval['all_valid_combos'])}")


def test_starter_strategies():
    """Test different starter strategy scenarios"""
    print("\n=== Testing Starter Strategies ===")
    
    # Scenario 1: Critical urgency - should play strong combo
    print("\n--- Scenario 1: Critical Urgency ---")
    hand = [
        Piece("GENERAL_RED"),    # 14 points
        Piece("ADVISOR_BLACK"),  # 11 points
        Piece("ELEPHANT_RED"),   # 9 points
        Piece("ELEPHANT_RED"),   # 9 points
    ]
    
    context = TurnPlayContext(
        my_name="Bot 1",
        my_hand=hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=2,
        turn_number=7,  # Last turn!
        pieces_per_player=2,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    result = choose_strategic_play(hand, context)
    print(f"Critical urgency play: {[p.name for p in result]} (value: {sum(p.point for p in result)})")
    
    # Scenario 2: Low urgency with burden pieces - should dispose burden
    print("\n--- Scenario 2: Low Urgency with Burdens ---")
    hand = [
        Piece("GENERAL_RED"),    # 14 points - opener
        Piece("SOLDIER_BLACK"),  # 1 point - burden
        Piece("SOLDIER_BLACK"),  # 1 point - burden
        Piece("ELEPHANT_RED"),   # 9 points
        Piece("ELEPHANT_RED"),   # 9 points
        Piece("HORSE_RED"),      # 6 points
    ]
    
    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=2,
        turn_number=2,  # Early game
        pieces_per_player=6,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    result = choose_strategic_play(hand, context)
    print(f"Low urgency play: {[p.name for p in result]} (value: {sum(p.point for p in result)})")
    
    # Scenario 3: Medium urgency with opener - should play opener
    print("\n--- Scenario 3: Medium Urgency with Opener ---")
    hand = [
        Piece("GENERAL_RED"),    # 14 points - opener
        Piece("ELEPHANT_RED"),   # 9 points
        Piece("CHARIOT_BLACK"),  # 7 points
        Piece("HORSE_RED"),      # 6 points
    ]
    
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=hand,
        my_captured=1,
        my_declared=3,
        required_piece_count=1,
        turn_number=5,  # Mid-game
        pieces_per_player=4,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    result = choose_strategic_play(hand, context)
    print(f"Medium urgency play: {[p.name for p in result]} (value: {sum(p.point for p in result)})")


def test_overcapture_still_works():
    """Verify overcapture avoidance still works with Phase 4"""
    print("\n=== Testing Overcapture Avoidance Still Works ===")
    
    hand = [
        Piece("GENERAL_RED"),    # 14 points
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point
    ]
    
    context = TurnPlayContext(
        my_name="Bot 4",
        my_hand=hand,
        my_captured=2,
        my_declared=2,  # At target!
        required_piece_count=2,
        turn_number=6,
        pieces_per_player=3,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    result = choose_strategic_play(hand, context)
    print(f"At target play: {[p.name for p in result]} (value: {sum(p.point for p in result)})")
    print("✅ Should play weak pieces to avoid overcapture")


if __name__ == "__main__":
    print("Testing Phase 4: Target Achievement Strategy")
    print("=" * 50)
    
    test_urgency_calculation()
    test_hand_evaluation()
    test_starter_strategies()
    test_overcapture_still_works()
    
    print("\n✅ Phase 4 testing complete!")