#!/usr/bin/env python3
"""
Final test to verify single opener random timing feature works correctly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play
import random

def test_starter_timing():
    """Test starter random opener timing with statistics"""
    print("\n" + "="*60)
    print("TESTING STARTER OPENER TIMING")
    print("="*60)
    
    total_runs = 200
    forced_singles = 0
    opener_plays = 0
    
    for i in range(total_runs):
        # Create opener-only hand
        hand = [
            Piece("ADVISOR_RED"),     # 12 points - opener
            Piece("SOLDIER_BLACK"),   # 1 point
            Piece("CANNON_BLACK"),    # 3 points  
            Piece("CHARIOT_BLACK"),   # 7 points
            Piece("ELEPHANT_BLACK"),  # 9 points
        ]
        
        # Create starter context (turn 1 for plan formation)
        context = TurnPlayContext(
            my_name="TestBot",
            my_hand=hand,
            my_captured=0,
            my_declared=4,
            required_piece_count=None,  # Starter chooses
            turn_number=1,  # Must be turn 1 for plan formation
            pieces_per_player=5,
            am_i_starter=True,
            current_plays=[],
            revealed_pieces=[],
            player_states={"TestBot": {"captured": 0, "declared": 4}}
        )
        
        # Suppress debug output
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        # Get strategic play
        result = choose_strategic_play(hand, context)
        
        # Restore stdout
        captured_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        # Check results
        if result and len(result) == 1:
            forced_singles += 1
            if result[0].point >= 11:
                opener_plays += 1
        
        # Show sample outputs
        if i < 3 or "randomly forcing singles" in captured_output:
            print(f"\nRun {i+1}:")
            if "randomly forcing singles" in captured_output:
                print("  ✅ Random timing ACTIVATED")
            else:
                print("  ❌ Random timing did not activate") 
            print(f"  Result: {len(result)} pieces - {[(p.name, p.point) for p in result]}")
    
    # Show statistics
    print(f"\n{'='*60}")
    print("STATISTICS:")
    print(f"  Total runs: {total_runs}")
    print(f"  Singles forced: {forced_singles} ({forced_singles/total_runs*100:.1f}%)")
    print(f"  Opener plays: {opener_plays} ({opener_plays/total_runs*100:.1f}%)")
    print(f"  Expected: ~40% (hand size 5)")
    
    # Verify reasonable range
    percentage = forced_singles / total_runs * 100
    if 30 <= percentage <= 50:
        print(f"\n✅ SUCCESS! Rate {percentage:.1f}% is within expected range (30-50%)")
    else:
        print(f"\n❌ FAILURE! Rate {percentage:.1f}% is outside expected range (30-50%)")

def test_responder_timing():
    """Test responder random opener timing"""
    print("\n" + "="*60)
    print("TESTING RESPONDER OPENER TIMING")
    print("="*60)
    
    total_runs = 200
    opener_plays = 0
    
    for i in range(total_runs):
        # Create opener-only hand
        hand = [
            Piece("GENERAL_RED"),     # 14 points - opener
            Piece("SOLDIER_BLACK"),   # 1 point
            Piece("CANNON_BLACK"),    # 3 points  
            Piece("HORSE_BLACK"),     # 5 points
            Piece("CHARIOT_BLACK"),   # 7 points
        ]
        
        # Create responder context (singles required)
        context = TurnPlayContext(
            my_name="TestBot",
            my_hand=hand,
            my_captured=0,
            my_declared=4,
            required_piece_count=1,  # Singles required
            turn_number=1,
            pieces_per_player=5,
            am_i_starter=False,
            current_plays=[{"player": "Starter", "pieces": [Piece("ADVISOR_RED")]}],
            revealed_pieces=[Piece("ADVISOR_RED")],
            player_states={"TestBot": {"captured": 0, "declared": 4}}
        )
        
        # Suppress debug output
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        # Get strategic play
        result = choose_strategic_play(hand, context)
        
        # Restore stdout
        captured_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        # Check if opener was played
        if result and len(result) == 1 and result[0].point >= 11:
            opener_plays += 1
        
        # Show sample outputs
        if i < 3 or ("randomly choosing to play opener" in captured_output and i < 10):
            print(f"\nRun {i+1}:")
            if "randomly choosing to play opener" in captured_output:
                print("  ✅ Random timing ACTIVATED")
            else:
                print("  ❌ Random timing did not activate")
            print(f"  Result: {result[0].name}({result[0].point})")
    
    # Show statistics
    print(f"\n{'='*60}")
    print("STATISTICS:")
    print(f"  Total runs: {total_runs}")
    print(f"  Opener plays: {opener_plays} ({opener_plays/total_runs*100:.1f}%)")
    print(f"  Expected: ~40% (hand size 5)")
    
    # Verify reasonable range
    percentage = opener_plays / total_runs * 100
    if 30 <= percentage <= 50:
        print(f"\n✅ SUCCESS! Rate {percentage:.1f}% is within expected range (30-50%)")
    else:
        print(f"\n❌ FAILURE! Rate {percentage:.1f}% is outside expected range (30-50%)")

def main():
    """Run all tests"""
    print("\nSINGLE OPENER RANDOM TIMING - FINAL VERIFICATION")
    print("=" * 60)
    
    # Set a seed for reproducible testing
    random.seed(12345)
    
    test_starter_timing()
    test_responder_timing()
    
    print("\n" + "="*60)
    print("🎉 TESTING COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    main()