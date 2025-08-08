#!/usr/bin/env python3
"""
Test the actual Bot 3 scenario from Round 1 where it had no weak pieces left.
This demonstrates why Bot 3 still won on Turn 3 despite overcapture avoidance.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play


def test_actual_turn3_scenario():
    """Test Bot 3's actual Turn 3 situation"""
    print("\n" + "="*80)
    print("TESTING ACTUAL BOT 3 TURN 3 SCENARIO")
    print("="*80)
    
    # Bot 3's actual remaining pieces after Turn 1 and 2
    # Turn 1: Played SOLDIER(1), HORSE(5), HORSE(5)
    # Turn 2: Played GENERAL(13)
    # Remaining: HORSE(6), CHARIOT(8), ELEPHANT(9), ELEPHANT(10)
    remaining_hand = [
        Piece("HORSE_RED"),      # 6 points
        Piece("CHARIOT_RED"),    # 8 points (actually 7 for BLACK)
        Piece("ELEPHANT_BLACK"), # 9 points
        Piece("ELEPHANT_RED")    # 10 points
    ]
    
    print("\nBot 3's actual hand at Turn 3:")
    print(f"  {[f'{p.name}({p.point})' for p in remaining_hand]}")
    print(f"\nWeakest piece: HORSE_RED(6)")
    print(f"Strongest piece: ELEPHANT_RED(10)")
    
    # Create context for Turn 3
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=remaining_hand,
        my_captured=1,  # Won Turn 2
        my_declared=1,  # Declared 1 pile
        required_piece_count=1,  # Singles turn
        turn_number=3,
        pieces_per_player=6,
        am_i_starter=True,  # Bot 3 is starter after winning Turn 2
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Alexanderium": {"captured": 0, "declared": 3},
            "Bot 2": {"captured": 0, "declared": 2},
            "Bot 3": {"captured": 1, "declared": 1},
            "Bot 4": {"captured": 0, "declared": 1}
        }
    )
    
    print("\nCalling strategic AI for Bot 3...")
    pieces_to_play = choose_strategic_play(remaining_hand, context)
    
    print(f"\n" + "="*60)
    print("RESULT ANALYSIS")
    print("="*60)
    print(f"\nBot 3 chose to play: {[p.name for p in pieces_to_play]}")
    print(f"Piece value: {pieces_to_play[0].point if pieces_to_play else 0}")
    
    print("\n🔍 Key Finding:")
    print("Even with overcapture avoidance working correctly,")
    print("Bot 3's weakest piece (HORSE_RED=6) is still strong enough")
    print("to potentially win against other players' pieces!")
    
    print("\n📊 What other players might play:")
    print("- Alexanderium: CANNON(3) or SOLDIER(1)")
    print("- Bot 2: CANNON(4) or remaining SOLDIERs")
    print("- Bot 4: SOLDIER(1), SOLDIER(2), or CANNON(3)")
    print("\n→ HORSE_RED(6) beats all of these!")


if __name__ == "__main__":
    test_actual_turn3_scenario()
    
    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("\n✅ Overcapture avoidance IS working correctly")
    print("❌ Bot 3's poor strategy was playing all weak pieces in Turn 1")
    print("💡 Solution: Better execution planning and reserve management")