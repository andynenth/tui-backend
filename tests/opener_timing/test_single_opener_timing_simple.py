#!/usr/bin/env python3
"""
Simplified test script to verify single opener random timing feature works
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play
import random

# Seed for initial consistency
random.seed(42)

def create_simple_hand(has_opener=True, has_combo=False):
    """Create a simple hand for testing"""
    pieces = []
    
    if has_opener:
        pieces.append(Piece("ADVISOR_RED"))  # 12 points - opener
    
    if has_combo:
        # Add a pair
        pieces.append(Piece("SOLDIER_BLACK"))
        pieces.append(Piece("SOLDIER_BLACK"))
    else:
        # Add different single pieces (no combos possible)
        pieces.append(Piece("SOLDIER_BLACK"))  # 1
        pieces.append(Piece("CANNON_BLACK"))   # 3
        pieces.append(Piece("CHARIOT_BLACK"))  # 7
        pieces.append(Piece("ELEPHANT_BLACK")) # 9
    
    return pieces

def test_starter_opener_timing():
    """Test starter random opener timing"""
    print("\n" + "="*60)
    print("TESTING STARTER OPENER TIMING")
    print("="*60)
    
    # Track results
    total_runs = 100
    opener_forces = 0
    
    for i in range(total_runs):
        # Create opener-only hand (has opener, no combos)
        hand = create_simple_hand(has_opener=True, has_combo=False)
        
        # Create starter context
        context = TurnPlayContext(
            my_name="TestBot",
            my_hand=hand,
            my_captured=0,
            my_declared=2,
            required_piece_count=None,  # Starter chooses
            turn_number=1,
            pieces_per_player=7,
            am_i_starter=True,
            current_plays=[],
            revealed_pieces=[],
            player_states={"TestBot": {"captured": 0, "declared": 2}}
        )
        
        # Get strategic play
        result = choose_strategic_play(hand, context)
        
        # Check if single piece was forced
        if result and len(result) == 1:
            opener_forces += 1
            if i < 5:  # Show first few results
                print(f"  Run {i+1}: Forced singles - played {result[0].name}({result[0].point})")
        elif i < 5:
            print(f"  Run {i+1}: Normal strategy - played {len(result)} pieces")
    
    percentage = (opener_forces / total_runs) * 100
    print(f"\nResults: {opener_forces}/{total_runs} forced singles ({percentage:.1f}%)")
    print(f"Expected: ~40% (hand size 5)")
    
    # Verify it's working
    assert 30 <= percentage <= 50, f"Rate {percentage:.1f}% outside expected range!"
    print("✅ STARTER TIMING WORKING!")

def test_responder_opener_timing():
    """Test responder random opener timing"""
    print("\n" + "="*60)
    print("TESTING RESPONDER OPENER TIMING")
    print("="*60)
    
    # Track results
    total_runs = 100
    opener_plays = 0
    
    for i in range(total_runs):
        # Create opener-only hand
        hand = create_simple_hand(has_opener=True, has_combo=False)
        
        # Create responder context (required = 1)
        context = TurnPlayContext(
            my_name="TestBot",
            my_hand=hand,
            my_captured=0,
            my_declared=2,
            required_piece_count=1,  # Singles required
            turn_number=1,
            pieces_per_player=7,
            am_i_starter=False,
            current_plays=[{"player": "Starter", "pieces": [Piece("GENERAL_RED")]}],
            revealed_pieces=[Piece("GENERAL_RED")],
            player_states={"TestBot": {"captured": 0, "declared": 2}}
        )
        
        # Get strategic play
        result = choose_strategic_play(hand, context)
        
        # Check if opener was played
        if result and len(result) == 1 and result[0].point >= 11:
            opener_plays += 1
            if i < 5:  # Show first few results
                print(f"  Run {i+1}: Played opener - {result[0].name}({result[0].point})")
        elif i < 5:
            print(f"  Run {i+1}: Played other - {result[0].name}({result[0].point})")
    
    percentage = (opener_plays / total_runs) * 100
    print(f"\nResults: {opener_plays}/{total_runs} opener plays ({percentage:.1f}%)")
    print(f"Expected: ~40% (hand size 5)")
    
    # Verify it's working
    assert 30 <= percentage <= 50, f"Rate {percentage:.1f}% outside expected range!"
    print("✅ RESPONDER TIMING WORKING!")

def test_with_combos():
    """Test that timing doesn't activate with combos"""
    print("\n" + "="*60)
    print("TESTING WITH COMBOS (should not activate)")
    print("="*60)
    
    # Track results
    total_runs = 50
    singles_count = 0
    
    for i in range(total_runs):
        # Create hand with opener AND combo
        hand = create_simple_hand(has_opener=True, has_combo=True)
        
        # Create starter context
        context = TurnPlayContext(
            my_name="TestBot",
            my_hand=hand,
            my_captured=0,
            my_declared=2,
            required_piece_count=None,
            turn_number=1,
            pieces_per_player=7,
            am_i_starter=True,
            current_plays=[],
            revealed_pieces=[],
            player_states={"TestBot": {"captured": 0, "declared": 2}}
        )
        
        # Get strategic play
        result = choose_strategic_play(hand, context)
        
        if result and len(result) == 1:
            singles_count += 1
    
    percentage = (singles_count / total_runs) * 100
    print(f"\nResults: {singles_count}/{total_runs} singles ({percentage:.1f}%)")
    print(f"Expected: Low % (has combos, so not opener-only)")
    
    # Should be much lower since we have combos
    assert percentage < 20, f"Rate {percentage:.1f}% too high for combo hand!"
    print("✅ COMBO EXCLUSION WORKING!")

def main():
    """Run all tests"""
    print("\nSINGLE OPENER RANDOM TIMING - SIMPLE TEST")
    print("==========================================")
    
    # Test each component
    test_starter_opener_timing()
    test_responder_opener_timing()
    test_with_combos()
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED! Feature is working correctly!")
    print("="*60)

if __name__ == "__main__":
    main()