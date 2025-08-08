#!/usr/bin/env python3
"""
Debug test to see why opener timing isn't working
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play
import random

# Don't seed so we can see random behavior
# random.seed(42)

def test_with_debug():
    """Test with full debug output"""
    print("\nTEST: Opener-only hand scenario")
    print("="*60)
    
    # Create opener-only hand (opener + singles, no combos)
    hand = [
        Piece("ADVISOR_RED"),     # 12 points - opener
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("CANNON_BLACK"),    # 3 points  
        Piece("CHARIOT_BLACK"),   # 7 points
        Piece("ELEPHANT_BLACK"),  # 9 points
    ]
    
    print(f"Hand: {[(p.name, p.point) for p in hand]}")
    print(f"Has opener (>=11 pts): YES - ADVISOR(12)")
    print(f"Valid combos possible: NO (all different pieces)")
    
    # Create starter context
    context = TurnPlayContext(
        my_name="TestBot",
        my_hand=hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=None,  # Starter chooses
        turn_number=1,
        pieces_per_player=5,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={"TestBot": {"captured": 0, "declared": 2}}
    )
    
    print("\nCalling choose_strategic_play...")
    print("-"*60)
    
    # Get strategic play - this will show all debug output
    result = choose_strategic_play(hand, context)
    
    print("-"*60)
    print(f"\nRESULT: Played {len(result)} pieces")
    print(f"Pieces: {[(p.name, p.point) for p in result]}")
    
    if len(result) == 1 and result[0].point >= 11:
        print("✅ OPENER TIMING ACTIVATED!")
    else:
        print("❌ Opener timing did not activate")

if __name__ == "__main__":
    # Run a few times to see if random timing works
    for i in range(5):
        print(f"\n{'='*80}")
        print(f"RUN {i+1}")
        print(f"{'='*80}")
        test_with_debug()