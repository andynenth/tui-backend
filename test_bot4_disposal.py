#!/usr/bin/env python3
"""Test Bot 4's decision to dispose GENERAL_RED + ADVISOR_RED when declaring 4"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from tests.ai_regression.ai_decision_framework import AIDecisionTester

def test_bot4_round2():
    """Test Bot 4's actual scenario from room EBA903 round 2"""
    tester = AIDecisionTester()
    
    # Bot 4's exact hand from round 2
    tester.add_scenario(
        name="Bot 4 Room EBA903 Round 2 - Declared 4",
        description="Bot 4 disposed GENERAL_RED(14) + ADVISOR_RED(12) when declaring 4",
        bot_name="Bot 4",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14 points
            ("GENERAL_BLACK", 1),    # 13 points
            ("ADVISOR_RED", 1),      # 12 points
            ("ADVISOR_BLACK", 1),    # 11 points
            ("CHARIOT_RED", 1),      # 8 points
            ("CHARIOT_BLACK", 1),    # 7 points
            ("CANNON_BLACK", 1),     # 3 points
            ("SOLDIER_RED", 1),      # 2 points
        ],
        declared=4,
        captured=0,
        required_pieces=2,  # Turn 1, starter (human) played 2 pieces
        turn_number=1,
        is_starter=False,  # Bot 4 is responder
        player_states={
            "Alexanderium": {"captured": 0, "declared": 2},
            "Bot 2": {"captured": 0, "declared": 0},
            "Bot 3": {"captured": 0, "declared": 1},
            "Bot 4": {"captured": 0, "declared": 4}
        }
    )
    
    tester.run_all_scenarios()

if __name__ == "__main__":
    print("="*80)
    print("ROOM EBA903 ROUND 2 ANALYSIS")
    print("="*80)
    print("\nBot 4 declared 4 (needs 4 wins) but disposed:")
    print("- GENERAL_RED(14)")
    print("- ADVISOR_RED(12)")
    print("\nThis seems counterintuitive - why dispose strongest pieces?")
    print("Let's trace the AI decision...\n")
    
    test_bot4_round2()