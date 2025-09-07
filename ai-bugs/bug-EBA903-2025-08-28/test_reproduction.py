#!/usr/bin/env python3
"""Reproduce bug from room EBA903 - Bot 4 disposing openers"""

import sys
from pathlib import Path

# Add to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.ai_regression.ai_decision_framework import AIDecisionTester

def test_bug():
    """Test the bug scenario - Bot 4 disposing valuable openers"""
    tester = AIDecisionTester()

    # Bot 4's exact scenario from room EBA903 round 2
    tester.add_scenario(
        name="Bug from Room EBA903 - Bot 4 Disposing Openers",
        description="Bot 4 declared 4 but disposed ADVISOR openers instead of preserving them",
        bot_name="Bot 4",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14 points - opener
            ("GENERAL_BLACK", 1),    # 13 points - opener
            ("ADVISOR_RED", 1),      # 12 points - opener
            ("ADVISOR_BLACK", 1),    # 11 points - opener
            ("CHARIOT_RED", 1),      # 8 points
            ("CHARIOT_BLACK", 1),    # 7 points
            ("CANNON_BLACK", 1),     # 3 points
            ("SOLDIER_RED", 1),      # 2 points
        ],
        declared=4,  # Needs 4 wins!
        captured=0,
        required_pieces=2,
        turn_number=1,
        is_starter=False
    )

    # Contrast: Bot declaring 2 with same openers
    tester.add_scenario(
        name="Contrast - Bot Declaring 2",
        description="With only 2 target, assigning 2 openers makes sense",
        bot_name="Smart Bot",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14 points - opener
            ("GENERAL_BLACK", 1),    # 13 points - opener
            ("ADVISOR_RED", 1),      # 12 points - opener
            ("ADVISOR_BLACK", 1),    # 11 points - opener
            ("CHARIOT_RED", 1),      # 8 points
            ("CHARIOT_BLACK", 1),    # 7 points
            ("CANNON_BLACK", 1),     # 3 points
            ("SOLDIER_RED", 1),      # 2 points
        ],
        declared=2,  # Only needs 2 wins
        captured=0,
        required_pieces=2,
        turn_number=1,
        is_starter=False
    )

    tester.run_all_scenarios()

    print("\n" + "="*60)
    print("BUG ANALYSIS")
    print("="*60)
    print("Bot 4 has 4 openers but only assigns 2 to the plan.")
    print("The other 2 (ADVISOR pieces) become 'burden' and get disposed!")
    print("This is illogical when declaring 4 - all 4 openers should be preserved.")

if __name__ == "__main__":
    test_bug()
