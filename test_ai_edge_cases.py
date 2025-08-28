#!/usr/bin/env python3
"""Test edge cases and specific scenarios for AI decision-making"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from test_ai_decision_framework import AIDecisionTester


def test_edge_cases():
    """Test various edge cases"""
    tester = AIDecisionTester()
    
    # Edge Case 1: Overcaptured bot
    tester.add_scenario(
        name="Overcaptured Bot",
        description="Bot declared 2 but captured 4 - should avoid winning more",
        bot_name="Unlucky Bot",
        hand_specs=[
            ("GENERAL_RED", 1),
            ("ADVISOR_RED", 2),
            ("SOLDIER_BLACK", 1)
        ],
        declared=2,
        captured=4,  # Overcaptured!
        required_pieces=2,
        turn_number=3
    )
    
    # Edge Case 2: Last turn with exact requirement
    tester.add_scenario(
        name="Last Turn Exact Win",
        description="Bot needs 1 win on last turn with 1 piece",
        bot_name="Clutch Bot",
        hand_specs=[
            ("GENERAL_RED", 1)
        ],
        declared=3,
        captured=2,
        required_pieces=1,
        turn_number=4
    )
    
    # Edge Case 3: Strong field with weak hand
    tester.add_scenario(
        name="Weak Hand Strong Field",
        description="Bot has weak pieces when others declared high",
        bot_name="Underdog Bot",
        hand_specs=[
            ("SOLDIER_BLACK", 4),
            ("SOLDIER_RED", 2),
            ("CANNON_BLACK", 2)
        ],
        declared=1,
        captured=0,
        required_pieces=3,
        turn_number=1,
        player_states={
            "Strong Bot 1": {"captured": 0, "declared": 7},
            "Strong Bot 2": {"captured": 0, "declared": 6},
            "Underdog Bot": {"captured": 0, "declared": 1},
            "Strong Bot 3": {"captured": 0, "declared": 5}
        }
    )
    
    # Edge Case 4: Multiple high-value pairs
    tester.add_scenario(
        name="Multiple Strong Pairs",
        description="Bot with multiple high-value pairs, declaring 0",
        bot_name="Pair Collector",
        hand_specs=[
            ("ADVISOR_RED", 2),      # 12+12 = 24
            ("ELEPHANT_RED", 2),     # 10+10 = 20
            ("CHARIOT_BLACK", 2),    # 7+7 = 14
            ("SOLDIER_BLACK", 2)     # 1+1 = 2
        ],
        declared=0,
        captured=0,
        required_pieces=4,
        turn_number=1
    )
    
    # Edge Case 5: Starter at target
    tester.add_scenario(
        name="Starter At Target",
        description="Starter who's already at target must lead",
        bot_name="Leading Bot",
        hand_specs=[
            ("GENERAL_BLACK", 1),
            ("ELEPHANT_BLACK", 1),
            ("HORSE_RED", 1),
            ("SOLDIER_BLACK", 2)
        ],
        declared=2,
        captured=2,
        required_pieces=3,
        turn_number=2,
        is_starter=True
    )
    
    # Edge Case 6: Only strong pieces left
    tester.add_scenario(
        name="All Strong Pieces",
        description="Bot with only openers, needs to avoid wins",
        bot_name="Heavy Hand",
        hand_specs=[
            ("GENERAL_RED", 1),    # 14
            ("GENERAL_BLACK", 1),  # 13
            ("ADVISOR_RED", 1),    # 12
            ("ADVISOR_BLACK", 1)   # 11
        ],
        declared=0,
        captured=0,
        required_pieces=2,
        turn_number=3
    )
    
    tester.run_all_scenarios()


def test_specific_bugs():
    """Test specific reported bugs"""
    tester = AIDecisionTester()
    
    # Bug: Bot preserving THREE_OF_A_KIND when declaring 0
    tester.add_scenario(
        name="Zero Declaration with Three of a Kind",
        description="Bot should not preserve THREE_OF_A_KIND when declaring 0",
        bot_name="Triple Bot",
        hand_specs=[
            ("HORSE_RED", 3),        # Three of a kind
            ("CANNON_BLACK", 2),
            ("SOLDIER_RED", 3)
        ],
        declared=0,
        captured=0,
        required_pieces=4,
        turn_number=1
    )
    
    # Bug: Bot with straight at zero declaration
    tester.add_scenario(
        name="Zero Declaration with Straight",
        description="Bot should not preserve STRAIGHT when declaring 0",
        bot_name="Straight Bot",
        hand_specs=[
            ("SOLDIER_BLACK", 1),    # 1
            ("SOLDIER_RED", 1),      # 2
            ("CANNON_BLACK", 1),     # 3
            ("CANNON_RED", 1),       # 4
            ("HORSE_BLACK", 1),      # 5
            ("ELEPHANT_RED", 1),
            ("ADVISOR_BLACK", 2)
        ],
        declared=0,
        captured=0,
        required_pieces=5,
        turn_number=1
    )
    
    tester.run_all_scenarios()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING EDGE CASES")
    print("="*80)
    test_edge_cases()
    
    print("\n\n" + "="*80)
    print("TESTING SPECIFIC BUGS")
    print("="*80)
    test_specific_bugs()