#!/usr/bin/env python3
"""
Test overcapture avoidance with the new responder strategy.
This creates a scenario where Bot 2 is at target (2/2) and should avoid overcapture.
"""

import sys
from pathlib import Path
from typing import List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play


def test_overcapture_scenario():
    """Test Bot 2 at target (2/2) as responder"""
    print("="*60)
    print("TESTING OVERCAPTURE AVOIDANCE WITH NEW STRATEGY")
    print("="*60)
    
    # Bot 2's remaining hand after some turns
    bot2_hand = [
        Piece("ADVISOR_BLACK"),     # 11 - opener
        Piece("SOLDIER_RED"),       # 2
        Piece("SOLDIER_RED"),       # 2
        Piece("ADVISOR_RED")        # 12 - opener
    ]
    
    # Create context where Bot 2 is at target
    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=bot2_hand,
        my_captured=2,  # AT TARGET!
        my_declared=2,  # Declared 2
        required_piece_count=2,  # Need to play 2 pieces
        turn_number=5,
        pieces_per_player=4,
        am_i_starter=False,  # Responder
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Alexanderium": {"captured": 1, "declared": 3},
            "Bot 2": {"captured": 2, "declared": 2},
            "Bot 3": {"captured": 0, "declared": 1},
            "Bot 4": {"captured": 1, "declared": 1}
        }
    )
    
    print(f"\nScenario: Bot 2 is at target (2/2) and must play 2 pieces as responder")
    print(f"Hand: {[f'{p.name}({p.point})' for p in bot2_hand]}")
    print(f"\nCalling choose_strategic_play()...")
    
    # Call strategic play
    pieces_to_play = choose_strategic_play(bot2_hand, context)
    
    print(f"\nRESULT: Bot 2 played {[f'{p.name}({p.point})' for p in pieces_to_play]}")
    print(f"Total value: {sum(p.point for p in pieces_to_play)} points")
    
    # Verify it played weak pieces
    if all(p.name == "SOLDIER" for p in pieces_to_play):
        print("\n✅ SUCCESS: Bot 2 correctly played weak SOLDIER pieces to avoid overcapture!")
    else:
        print("\n❌ FAILURE: Bot 2 did not play the weakest pieces!")


def test_overcapture_as_starter():
    """Test Bot 3 at target (1/1) as starter"""
    print("\n" + "="*60)
    print("TESTING OVERCAPTURE AS STARTER")
    print("="*60)
    
    # Bot 3's remaining hand
    bot3_hand = [
        Piece("HORSE_BLACK"),       # 5
        Piece("HORSE_BLACK"),       # 5
        Piece("GENERAL_BLACK"),     # 13
        Piece("HORSE_RED")          # 6
    ]
    
    # Create context where Bot 3 is at target and is starter
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=bot3_hand,
        my_captured=1,  # AT TARGET!
        my_declared=1,  # Declared 1
        required_piece_count=1,  # Need to play 1 piece
        turn_number=6,
        pieces_per_player=3,
        am_i_starter=True,  # Starter - must play valid combo
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Alexanderium": {"captured": 2, "declared": 3},
            "Bot 2": {"captured": 2, "declared": 2},
            "Bot 3": {"captured": 1, "declared": 1},
            "Bot 4": {"captured": 1, "declared": 1}
        }
    )
    
    print(f"\nScenario: Bot 3 is at target (1/1) and must play 1 piece as starter")
    print(f"Hand: {[f'{p.name}({p.point})' for p in bot3_hand]}")
    print(f"\nCalling choose_strategic_play()...")
    
    # Call strategic play
    pieces_to_play = choose_strategic_play(bot3_hand, context)
    
    print(f"\nRESULT: Bot 3 played {[f'{p.name}({p.point})' for p in pieces_to_play]}")
    print(f"Total value: {sum(p.point for p in pieces_to_play)} points")
    
    # Verify it played a weak piece
    if pieces_to_play[0].point <= 6:
        print("\n✅ SUCCESS: Bot 3 correctly played a weak piece to avoid overcapture!")
    else:
        print("\n❌ FAILURE: Bot 3 played a strong piece!")


if __name__ == "__main__":
    test_overcapture_scenario()
    test_overcapture_as_starter()
    
    print("\n" + "="*60)
    print("OVERCAPTURE AVOIDANCE TESTS COMPLETE")
    print("="*60)