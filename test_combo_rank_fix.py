#!/usr/bin/env python3
"""Test that combo rank is prioritized over points in critical urgency"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from test_ai_decision_framework import AIDecisionTester

def test_combo_rank_scenarios():
    """Test various scenarios where combo rank should beat points"""
    tester = AIDecisionTester()
    
    # Scenario 1: Bot 2's actual case - THREE_OF_A_KIND vs high singles
    tester.add_scenario(
        name="THREE_OF_A_KIND vs High Singles",
        description="Should play THREE_OF_A_KIND despite low points",
        bot_name="Bot 2",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14 points - SINGLE
            ("ADVISOR_RED", 1),      # 12 points - SINGLE
            ("SOLDIER_BLACK", 3),    # 1 point each - THREE_OF_A_KIND!
            ("HORSE_RED", 1),        # 6 points
            ("SOLDIER_RED", 2),      # 2 points each - PAIR
        ],
        declared=5,  # Critical urgency!
        captured=0,
        required_pieces=None,  # Starter
        turn_number=1,
        is_starter=True
    )
    
    # Scenario 2: PAIR vs higher point SINGLE
    tester.add_scenario(
        name="PAIR vs High SINGLE",
        description="Should play PAIR over higher-point SINGLE",
        bot_name="Test Bot",
        hand_specs=[
            ("GENERAL_BLACK", 1),    # 13 points - SINGLE
            ("ADVISOR_RED", 1),      # 12 points - SINGLE
            ("SOLDIER_RED", 2),      # 2 points each - PAIR
            ("CANNON_BLACK", 3),     # 3 points each
        ],
        declared=4,  # High urgency
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=True
    )
    
    # Scenario 3: STRAIGHT vs higher-point combos
    tester.add_scenario(
        name="STRAIGHT vs Lower Rank Combos",
        description="Should play STRAIGHT over THREE_OF_A_KIND",
        bot_name="Straight Player",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14
            ("ADVISOR_RED", 1),      # 12  
            ("ELEPHANT_RED", 1),     # 10 - Forms STRAIGHT!
            ("SOLDIER_BLACK", 3),    # THREE_OF_A_KIND
            ("CANNON_RED", 1),
            ("CANNON_BLACK", 1),
        ],
        declared=6,  # Critical urgency
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=True
    )
    
    # Scenario 4: Multiple combos with different ranks
    tester.add_scenario(
        name="Multiple Combo Types",
        description="Should prioritize by rank: FOUR > STRAIGHT > THREE > PAIR",
        bot_name="Combo Master",
        hand_specs=[
            ("SOLDIER_BLACK", 4),    # FOUR_OF_A_KIND! (rank 5)
            ("CHARIOT_RED", 1),      # 8
            ("HORSE_RED", 1),        # 6
            ("CANNON_RED", 1),       # 4 - Forms STRAIGHT (rank 4)
            ("ADVISOR_RED", 2),      # 12 each - PAIR (rank 2)
        ],
        declared=7,  # Critical urgency
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=True
    )
    
    tester.run_all_scenarios()

def test_edge_cases():
    """Test edge cases for combo ranking"""
    tester = AIDecisionTester()
    
    # Edge case: EXTENDED_STRAIGHT_5 (newly added rank)
    tester.add_scenario(
        name="EXTENDED_STRAIGHT_5 Test",
        description="Test newly added EXTENDED_STRAIGHT_5 rank",
        bot_name="Extended Bot",
        hand_specs=[
            ("GENERAL_RED", 2),      # 14 each
            ("ADVISOR_RED", 2),      # 12 each
            ("ELEPHANT_RED", 1),     # 10 - Forms EXTENDED_STRAIGHT_5!
            ("SOLDIER_BLACK", 3),    # THREE_OF_A_KIND
        ],
        declared=8,  # Maximum urgency
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=True
    )
    
    tester.run_all_scenarios()

if __name__ == "__main__":
    print("="*80)
    print("TESTING COMBO RANK PRIORITIZATION FIX")
    print("="*80)
    print("\nCombo ranks should be prioritized over point values in critical urgency.")
    print("Expected behavior: Higher rank combos beat lower rank combos.\n")
    
    test_combo_rank_scenarios()
    
    print("\n\n" + "="*80)
    print("TESTING EDGE CASES")
    print("="*80)
    test_edge_cases()