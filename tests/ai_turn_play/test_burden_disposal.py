# tests/ai_turn_play/test_burden_disposal.py
"""
Test burden piece identification and disposal strategy.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, StrategicPlan, identify_burden_pieces,
    generate_strategic_plan, execute_starter_strategy
)


def test_burden_identification_basic():
    """Test basic burden piece identification."""
    print("\n=== Testing Basic Burden Identification ===\n")
    
    # Hand with mix of useful and burden pieces
    hand = [
        Piece("GENERAL_RED"),      # 14 - strong opener
        Piece("ADVISOR_BLACK"),    # 11 - strong opener
        Piece("CHARIOT_RED"),      # 8 - decent
        Piece("CHARIOT_BLACK"),    # 7 - decent
        Piece("SOLDIER_RED"),      # 2 - weak
        Piece("SOLDIER_BLACK"),    # 1 - weakest
    ]
    
    # Valid combos: pair of chariots, singles
    valid_combos = [
        ("PAIR", [Piece("CHARIOT_RED"), Piece("CHARIOT_BLACK")]),
        ("SINGLE", [Piece("GENERAL_RED")]),
        ("SINGLE", [Piece("ADVISOR_BLACK")]),
        ("SINGLE", [Piece("CHARIOT_RED")]),
        ("SINGLE", [Piece("CHARIOT_BLACK")]),
        ("SINGLE", [Piece("SOLDIER_RED")]),
        ("SINGLE", [Piece("SOLDIER_BLACK")]),
    ]
    
    # Need 2 more piles
    plan = StrategicPlan(
        target_remaining=2,
        valid_combos=valid_combos,
        opener_pieces=[hand[0], hand[1]],  # GENERAL and ADVISOR
        urgency_level="low"
    )
    
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=1,
        my_declared=3,
        required_piece_count=None,
        turn_number=2,
        pieces_per_player=6,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    burden_pieces = identify_burden_pieces(hand, plan, context)
    
    print(f"Hand: {[str(p) for p in hand]}")
    print(f"Target remaining: {plan.target_remaining}")
    print(f"Burden pieces: {[str(p) for p in burden_pieces]}")
    
    # Soldiers should be burdens (weak singles when we need 2 captures)
    assert any(p.name == "SOLDIER" for p in burden_pieces), "Weak soldiers should be burdens"
    print("✅ Correctly identified weak singles as burdens")


def test_burden_disposal_when_at_target():
    """Test that all pieces are burdens when at target."""
    print("\n=== Testing Burden Disposal at Target ===\n")
    
    hand = [
        Piece("GENERAL_RED"),
        Piece("CANNON_BLACK"),
        Piece("SOLDIER_RED"),
    ]
    
    # At target (0 remaining)
    plan = StrategicPlan(
        target_remaining=0,
        valid_combos=[],
        opener_pieces=[hand[0]],
        urgency_level="none"
    )
    
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=2,
        my_declared=2,
        required_piece_count=1,
        turn_number=3,
        pieces_per_player=3,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    burden_pieces = identify_burden_pieces(hand, plan, context)
    
    print(f"At target: {context.my_captured}/{context.my_declared}")
    print(f"All pieces are burdens: {len(burden_pieces) == len(hand)}")
    
    assert len(burden_pieces) == len(hand), "All pieces should be burdens at target"
    print("✅ All pieces correctly identified as burdens when at target")


def test_burden_disposal_strategy():
    """Test that starter strategy disposes burden pieces."""
    print("\n=== Testing Burden Disposal in Starter Strategy ===\n")
    
    # Hand with clear burden pieces
    hand = [
        Piece("GENERAL_RED"),      # 14 - opener
        Piece("ADVISOR_BLACK"),    # 11 - opener  
        Piece("HORSE_RED"),        # 6
        Piece("HORSE_BLACK"),      # 5
        Piece("CANNON_RED"),       # 4
        Piece("SOLDIER_RED"),      # 2 - burden
        Piece("SOLDIER_BLACK"),    # 1 - burden
    ]
    
    # Need 2 more, have pair of horses
    valid_combos = [
        ("PAIR", [hand[2], hand[3]]),  # Horses - useful
        ("SINGLE", [hand[0]]),         # GENERAL - useful
        ("SINGLE", [hand[1]]),         # ADVISOR - useful
        ("SINGLE", [hand[4]]),         # CANNON
        ("SINGLE", [hand[5]]),         # SOLDIER_RED
        ("SINGLE", [hand[6]]),         # SOLDIER_BLACK
    ]
    
    plan = StrategicPlan(
        target_remaining=2,
        valid_combos=valid_combos,
        opener_pieces=[hand[0], hand[1]],
        urgency_level="low"  # Low urgency allows burden disposal
    )
    
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=1,
        my_declared=3,
        required_piece_count=None,  # We're starter, can choose
        turn_number=2,
        pieces_per_player=7,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Execute starter strategy
    result = execute_starter_strategy(plan, context)
    
    print(f"Strategy result: {[str(p) for p in result]}")
    print(f"Pieces played: {len(result)}")
    
    # Should dispose of weak pieces
    assert all(p.point <= 3 for p in result), "Should play weak burden pieces"
    print("✅ Starter strategy correctly disposes burden pieces")


def test_no_burden_disposal_when_urgent():
    """Test that burden disposal is skipped when urgency is high."""
    print("\n=== Testing No Burden Disposal When Urgent ===\n")
    
    hand = [
        Piece("GENERAL_RED"),      # 14
        Piece("SOLDIER_RED"),      # 2
        Piece("SOLDIER_BLACK"),    # 1
    ]
    
    valid_combos = [
        ("SINGLE", [hand[0]]),
        ("SINGLE", [hand[1]]),
        ("SINGLE", [hand[2]]),
    ]
    
    # High urgency - need to win turns
    plan = StrategicPlan(
        target_remaining=3,
        valid_combos=valid_combos,
        opener_pieces=[hand[0]],
        urgency_level="critical"  # Critical urgency
    )
    
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=0,
        my_declared=3,
        required_piece_count=None,
        turn_number=6,  # Late in round
        pieces_per_player=3,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    result = execute_starter_strategy(plan, context)
    
    print(f"Critical urgency result: {[str(p) for p in result]}")
    
    # Should play strong piece to win, not dispose burdens
    assert result[0].point >= 11, "Should play strong piece when critical"
    print("✅ Skips burden disposal when urgency is critical")


def test_burden_disposal_with_combos():
    """Test burden identification with various combo types."""
    print("\n=== Testing Burden Disposal with Combos ===\n")
    
    hand = [
        Piece("CHARIOT_RED"),      # 8
        Piece("CHARIOT_BLACK"),    # 7
        Piece("HORSE_RED"),        # 6
        Piece("HORSE_BLACK"),      # 5
        Piece("CANNON_RED"),       # 4
        Piece("CANNON_BLACK"),     # 3
        Piece("SOLDIER_RED"),      # 2
        Piece("SOLDIER_BLACK"),    # 1
    ]
    
    # Need 3 piles, have pairs and triple
    valid_combos = [
        ("PAIR", [hand[0], hand[1]]),    # Chariots - 2 piles
        ("PAIR", [hand[2], hand[3]]),    # Horses - 2 piles
        ("TRIPLE", [hand[4], hand[5], hand[6]]),  # Cannons+Soldier - 3 piles
        # Singles omitted for brevity
    ]
    
    plan = StrategicPlan(
        target_remaining=3,
        valid_combos=valid_combos,
        opener_pieces=[],
        urgency_level="medium"
    )
    
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=0,
        my_declared=3,
        required_piece_count=None,
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    burden_pieces = identify_burden_pieces(hand, plan, context)
    
    print(f"Target remaining: {plan.target_remaining}")
    print(f"Useful combos can capture: 2+2+3 = 7 piles (more than needed)")
    print(f"Burden pieces: {[str(p) for p in burden_pieces]}")
    
    # SOLDIER_BLACK not in triple should be burden
    soldier_black = hand[7]
    assert soldier_black in burden_pieces, "Unused soldier should be burden"
    print("✅ Correctly identifies pieces not in useful combos")


if __name__ == "__main__":
    print("Testing Burden Disposal Logic...\n")
    
    test_burden_identification_basic()
    test_burden_disposal_when_at_target()
    test_burden_disposal_strategy()
    test_no_burden_disposal_when_urgent()
    test_burden_disposal_with_combos()
    
    print("\n✅ All burden disposal tests passed!")