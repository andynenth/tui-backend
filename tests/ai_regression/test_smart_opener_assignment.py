#!/usr/bin/env python3
"""
Regression Test: Smart Opener Assignment

Bug Description:
- AI assigns openers based on target_remaining without considering secured wins from combos
- This causes over-reservation of opener pieces when combos are available

Fix Applied:
- Count secured wins from non-opener combos first
- Formula: openers_needed = max(0, target_remaining - secured_wins)
- Applied to all branches in form_execution_plan()

Test Scenarios:
1. Target 3 with 1 combo - should assign 2 openers (not hard-coded 2)
2. Target 3 with 0 combos - should assign 3 openers (not hard-coded 2)
3. Target 4 with THREE_OF_A_KIND - should assign 3 openers (not 4)
4. Target 5 with 2 combos - should assign 3 openers
"""

from conftest import AIDecisionTester

def test_smart_opener_assignment():
    """Ensure openers are assigned based on secured wins from combos"""
    tester = AIDecisionTester()

    # Scenario 1: Target 3 with THREE_OF_A_KIND combo
    tester.add_scenario(
        name="Target 3 with THREE_OF_A_KIND",
        description="Should assign 2 openers (3 target - 1 secured win)",
        bot_name="Smart Bot 1",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14 points - opener
            ("ADVISOR_BLACK", 1),    # 11 points - opener
            ("ELEPHANT_RED", 1),     # 10 points - NOT opener
            ("SOLDIER_BLACK", 3),    # 1 each - THREE_OF_A_KIND combo!
            ("CHARIOT_RED", 1),      # 8 points
            ("HORSE_BLACK", 1),      # 5 points
        ],
        declared=3,
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=False
    )

    # Scenario 2: Target 3 with NO combos
    tester.add_scenario(
        name="Target 3 with NO combos",
        description="Should assign 3 openers (3 target - 0 secured wins)",
        bot_name="Smart Bot 2",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14 points - opener
            ("ADVISOR_RED", 1),      # 12 points - opener
            ("ADVISOR_BLACK", 1),    # 11 points - opener
            ("CHARIOT_RED", 1),      # 8 points
            ("HORSE_BLACK", 1),      # 5 points
            ("CANNON_RED", 1),       # 4 points
            ("CANNON_BLACK", 1),     # 3 points
            ("SOLDIER_BLACK", 1),    # 1 point
        ],
        declared=3,
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=False
    )

    # Scenario 3: Target 4 with THREE_OF_A_KIND
    tester.add_scenario(
        name="Target 4 with THREE_OF_A_KIND",
        description="Should assign 3 openers (4 target - 1 secured win)",
        bot_name="Bot 4 Fixed",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14 points - opener
            ("GENERAL_BLACK", 1),    # 13 points - opener
            ("ADVISOR_RED", 1),      # 12 points - opener
            ("ADVISOR_BLACK", 1),    # 11 points - opener
            ("SOLDIER_BLACK", 3),    # 1 each - THREE_OF_A_KIND combo!
            ("CHARIOT_RED", 1),      # 8 points
        ],
        declared=4,
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=False
    )

    # Scenario 4: Target 5 with TWO viable combos
    tester.add_scenario(
        name="Target 5 with 2 combos (non-opener)",
        description="Should assign 3 openers (5 target - 2 secured wins)",
        bot_name="Multi-Combo Bot",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14 points - opener
            ("GENERAL_BLACK", 1),    # 13 points - opener
            ("ADVISOR_RED", 1),      # 12 points - opener
            ("ADVISOR_BLACK", 1),    # 11 points - opener
            ("CHARIOT_BLACK", 2),    # 7 each - PAIR combo!
            ("SOLDIER_BLACK", 3),    # 1 each - THREE_OF_A_KIND combo!
        ],
        declared=5,
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=False
    )

    # Scenario 5: Target 2 with 2 combos (more combos than needed)
    tester.add_scenario(
        name="Target 2 with 2 combos",
        description="Should assign 0 openers (2 target - 2 secured wins = 0)",
        bot_name="Combo Rich Bot",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14 points - opener
            ("ADVISOR_BLACK", 1),    # 11 points - opener
            ("CHARIOT_BLACK", 2),    # 7 each - PAIR combo!
            ("SOLDIER_BLACK", 3),    # 1 each - THREE_OF_A_KIND combo!
            ("CANNON_RED", 1),       # 4 points
        ],
        declared=2,
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=False
    )

    # Run all scenarios and check results
    test_results = []
    for scenario in tester.scenarios:
        hand = tester.create_hand_from_specs(scenario['hand_specs'])
        context = tester.create_context(
            bot_name=scenario.get('bot_name', 'Test Bot'),
            hand=hand,
            declared=scenario['declared'],
            captured=scenario['captured'],
            required_pieces=scenario['required_pieces'],
            turn_number=scenario.get('turn_number', 1),
            is_starter=scenario.get('is_starter', False)
        )
        result = tester.analyze_decision(context, show_plan_details=True, show_urgency=False)
        test_results.append(result)

    # Verify expectations
    print("\n" + "="*60)
    print("SMART OPENER ASSIGNMENT TEST RESULTS")
    print("="*60)

    all_passed = True

    # Check Scenario 1: Target 3 with 1 combo
    result1 = test_results[0]
    if result1:
        assigned_openers = len(result1['plan'].get('assigned_openers', []))
        expected_openers = 2  # 3 target - 1 secured win
        if assigned_openers == expected_openers:
            print(f"✅ Target 3 with THREE_OF_A_KIND: correctly assigned {assigned_openers} openers")
        else:
            print(f"❌ Target 3 with THREE_OF_A_KIND: assigned {assigned_openers} openers, expected {expected_openers}")
            all_passed = False

    # Check Scenario 2: Target 3 with 0 combos
    result2 = test_results[1]
    if result2:
        assigned_openers = len(result2['plan'].get('assigned_openers', []))
        expected_openers = 3  # 3 target - 0 secured wins
        if assigned_openers == expected_openers:
            print(f"✅ Target 3 with NO combos: correctly assigned {assigned_openers} openers")
        else:
            print(f"❌ Target 3 with NO combos: assigned {assigned_openers} openers, expected {expected_openers}")
            all_passed = False

    # Check Scenario 3: Target 4 with 1 combo
    result3 = test_results[2]
    if result3:
        assigned_openers = len(result3['plan'].get('assigned_openers', []))
        expected_openers = 3  # 4 target - 1 secured win
        if assigned_openers == expected_openers:
            print(f"✅ Target 4 with THREE_OF_A_KIND: correctly assigned {assigned_openers} openers")
        else:
            print(f"❌ Target 4 with THREE_OF_A_KIND: assigned {assigned_openers} openers, expected {expected_openers}")
            all_passed = False

    # Check Scenario 4: Target 5 with 2 combos
    result4 = test_results[3]
    if result4:
        assigned_openers = len(result4['plan'].get('assigned_openers', []))
        expected_openers = 3  # 5 target - 2 secured wins
        if assigned_openers == expected_openers:
            print(f"✅ Target 5 with 2 combos: correctly assigned {assigned_openers} openers")
        else:
            print(f"❌ Target 5 with 2 combos: assigned {assigned_openers} openers, expected {expected_openers}")
            all_passed = False

    # Check Scenario 5: Target 2 with 2 combos (edge case)
    result5 = test_results[4]
    if result5:
        assigned_openers = len(result5['plan'].get('assigned_openers', []))
        expected_openers = 0  # 2 target - 2 secured wins = 0
        if assigned_openers == expected_openers:
            print(f"✅ Target 2 with 2 combos: correctly assigned {assigned_openers} openers")
        else:
            print(f"❌ Target 2 with 2 combos: assigned {assigned_openers} openers, expected {expected_openers}")
            all_passed = False

    return all_passed

if __name__ == "__main__":
    success = test_smart_opener_assignment()
    exit(0 if success else 1)