#!/usr/bin/env python3
"""Test the improved overcapture avoidance system"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, OvercaptureConstraints, 
    get_overcapture_constraints, choose_strategic_play
)

def test_constraint_calculation():
    """Test constraint calculation at various capture/declare ratios"""
    print("="*60)
    print("TESTING CONSTRAINT CALCULATION")
    print("="*60)
    
    test_cases = [
        # (captured, declared, expected_max_safe, expected_risk_level)
        (0, 3, 3, "high"),      # Need 3, have 8 pieces - high risk
        (1, 3, 2, "high"),      # Need 2, have 7+ pieces - high risk  
        (2, 3, 1, "high"),      # Need 1, have 6+ pieces - high risk
        (3, 3, 5, "none"),      # At target - no risk, max_safe = hand_size
        (0, 5, 5, "medium"),    # Need 5, have 8 pieces - medium risk
        (2, 5, 3, "medium"),    # Need 3, have 6+ pieces - medium risk
        (4, 5, 1, "high"),      # Need 1, have 4+ pieces - high risk
        (0, 1, 1, "high"),      # Need 1, have 8 pieces - high risk (close to target)
        (1, 1, 8, "none"),      # At target - no risk, max_safe = hand_size  
        (0, 0, 8, "none"),      # Declared 0 - no risk, max_safe = hand_size
    ]
    
    for captured, declared, expected_max, expected_risk in test_cases:
        # Create a simple context
        context = TurnPlayContext(
            my_name="TestBot",
            my_hand=[Piece("SOLDIER_BLACK") for _ in range(8 - captured)],  # Simulate pieces used
            my_captured=captured,
            my_declared=declared,
            required_piece_count=None,
            turn_number=captured + 1,  # Rough estimate
            pieces_per_player=8,
            am_i_starter=True,
            current_plays=[],
            revealed_pieces=[],
            player_states={"TestBot": {"captured": captured, "declared": declared}}
        )
        
        constraints = get_overcapture_constraints(context)
        
        print(f"\nTest: {captured}/{declared} (need {declared - captured})")
        print(f"  Max safe pieces: {constraints.max_safe_pieces} (expected: {expected_max})")
        print(f"  Risk level: {constraints.risk_level} (expected: {expected_risk})")
        print(f"  Avoid counts: {constraints.avoid_piece_counts}")
        print(f"  Risky plays: {constraints.risky_play_types}")
        
        # Validate (adjust expected max_safe for "none" risk cases based on actual hand size)
        if expected_risk == "none":
            expected_max = len(context.my_hand)
        assert constraints.max_safe_pieces == expected_max, f"Max safe mismatch: got {constraints.max_safe_pieces}, expected {expected_max}"
        assert constraints.risk_level == expected_risk, f"Risk level mismatch: got {constraints.risk_level}, expected {expected_risk}"


def test_starter_at_target():
    """Test that starter at target chooses minimum pieces"""
    print("\n" + "="*60)
    print("TESTING STARTER AT TARGET")
    print("="*60)
    
    # Alexanderium at 3/3 as starter
    hand = [
        Piece("SOLDIER_BLACK"),    # 1
        Piece("SOLDIER_BLACK"),    # 1  
        Piece("CANNON_BLACK"),     # 3
        Piece("CANNON_RED"),       # 4
        Piece("HORSE_RED")         # 6
    ]
    
    context = TurnPlayContext(
        my_name="Alexanderium",
        my_hand=hand,
        my_captured=3,
        my_declared=3,
        required_piece_count=None,  # Starter chooses
        turn_number=2,
        pieces_per_player=5,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Alexanderium": {"captured": 3, "declared": 3},
            "Bot 2": {"captured": 0, "declared": 5},
            "Bot 3": {"captured": 0, "declared": 3},
            "Bot 4": {"captured": 0, "declared": 1}
        }
    )
    
    print(f"\nScenario: Alexanderium at 3/3 as starter")
    print(f"Hand: {[f'{p.name}({p.point})' for p in hand]}")
    
    # Get strategic play
    result = choose_strategic_play(hand, context)
    
    print(f"\nResult: Played {len(result)} pieces - {[f'{p.name}({p.point})' for p in result]}")
    assert len(result) == 1, "Starter at target should play minimum 1 piece"


def test_responder_overcapture_risk():
    """Test responder avoiding combinations when at overcapture risk"""
    print("\n" + "="*60)
    print("TESTING RESPONDER OVERCAPTURE AVOIDANCE")
    print("="*60)
    
    # Bot 4 at 0/1, required to play 2 pieces
    hand = [
        Piece("SOLDIER_BLACK"),    # 1
        Piece("SOLDIER_BLACK"),    # 1
        Piece("ADVISOR_BLACK"),    # 11
        Piece("SOLDIER_RED"),      # 2
        Piece("SOLDIER_RED")       # 2
    ]
    
    context = TurnPlayContext(
        my_name="Bot 4",
        my_hand=hand,
        my_captured=0,
        my_declared=1,
        required_piece_count=2,  # Required by starter
        turn_number=2,
        pieces_per_player=5,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Alexanderium": {"captured": 3, "declared": 3},
            "Bot 2": {"captured": 0, "declared": 5},
            "Bot 3": {"captured": 0, "declared": 3},
            "Bot 4": {"captured": 0, "declared": 1}
        }
    )
    
    print(f"\nScenario: Bot 4 at 0/1, required to play 2 pieces")
    print(f"Hand: {[f'{p.name}({p.point})' for p in hand]}")
    
    # Get strategic play
    result = choose_strategic_play(hand, context)
    
    print(f"\nResult: Played {[f'{p.name}({p.point})' for p in result]}")
    
    # Check if it avoided playing matching pieces
    piece_names = [p.name for p in result]
    if len(piece_names) == 2 and piece_names[0] == piece_names[1]:
        print("  ⚠️ Played a PAIR - might win!")
    else:
        print("  ✅ Avoided playing matching pieces")


def test_starter_near_target():
    """Test starter choosing safe piece counts when near target"""
    print("\n" + "="*60)
    print("TESTING STARTER NEAR TARGET")  
    print("="*60)
    
    # Bot at 2/3 as starter
    hand = [
        Piece("SOLDIER_BLACK"),    # 1
        Piece("CANNON_BLACK"),     # 3
        Piece("HORSE_BLACK"),      # 5
        Piece("CHARIOT_BLACK"),    # 7
        Piece("ELEPHANT_BLACK")    # 9
    ]
    
    context = TurnPlayContext(
        my_name="TestBot",
        my_hand=hand,
        my_captured=2,
        my_declared=3,
        required_piece_count=None,  # Starter chooses
        turn_number=3,
        pieces_per_player=5,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "TestBot": {"captured": 2, "declared": 3},
            "Bot 2": {"captured": 1, "declared": 2}
        }
    )
    
    print(f"\nScenario: Bot at 2/3 as starter (needs 1 pile)")
    print(f"Hand: {[f'{p.name}({p.point})' for p in hand]}")
    
    # Get strategic play
    result = choose_strategic_play(hand, context)
    
    print(f"\nResult: Played {len(result)} pieces - {[f'{p.name}({p.point})' for p in result]}")
    print(f"Analysis: Playing {len(result)} pieces would capture {len(result)} piles")
    
    # Should play 1 piece since max_safe_pieces = 1
    assert len(result) == 1, "Should play max 1 piece to avoid overcapture"


if __name__ == "__main__":
    test_constraint_calculation()
    test_starter_at_target()
    test_responder_overcapture_risk()
    test_starter_near_target()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)