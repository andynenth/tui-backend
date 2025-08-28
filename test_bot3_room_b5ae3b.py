#!/usr/bin/env python3
"""Test Bot 3's AI decision from room B5AE3B"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from test_ai_decision_framework import AIDecisionTester

def test_bot3_room_b5ae3b():
    """Test Bot 3's actual hand from room B5AE3B"""
    tester = AIDecisionTester()
    
    # Bot 3's actual hand from the game
    # Bot 3 declared 0
    tester.add_scenario(
        name="Bot 3 Room B5AE3B - Declared 0",
        description="Bot 3's actual hand - why no three of a kind?",
        bot_name="Bot 3",
        hand_specs=[
            ("ELEPHANT_RED", 1),    # 10 points
            ("ELEPHANT_BLACK", 1),  # 9 points  
            ("HORSE_BLACK", 1),     # 5 points
            ("CANNON_RED", 1),      # 4 points
            ("CANNON_BLACK", 1),    # 3 points
            ("SOLDIER_RED", 2),     # 2 points each
            ("SOLDIER_BLACK", 1),   # 1 point
        ],
        declared=0,
        captured=0,
        required_pieces=1,  # Turn 1, starter (Bot 2) played 1 piece
        turn_number=1
    )
    
    # Also test Bot 2 who has THREE_OF_A_KIND
    tester.add_scenario(
        name="Bot 2 Room B5AE3B - Has THREE_OF_A_KIND",
        description="Bot 2 has 3 SOLDIER_BLACK, declared 5",
        bot_name="Bot 2",
        hand_specs=[
            ("GENERAL_RED", 1),     # 14 points
            ("ADVISOR_RED", 1),     # 12 points
            ("HORSE_RED", 1),       # 6 points
            ("SOLDIER_RED", 2),     # 2 points each
            ("SOLDIER_BLACK", 3),   # 1 point each - THREE OF A KIND!
        ],
        declared=5,
        captured=0,
        required_pieces=1,
        turn_number=1,
        is_starter=True
    )
    
    tester.run_all_scenarios()

if __name__ == "__main__":
    print("="*80)
    print("ROOM B5AE3B ANALYSIS")
    print("="*80)
    print("\nBot 3 declared 0 but doesn't have three of a kind.")
    print("Bot 2 declared 5 and has THREE SOLDIER_BLACK.")
    print("\nLet's trace their AI decisions...\n")
    
    test_bot3_room_b5ae3b()