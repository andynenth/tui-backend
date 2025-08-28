#!/usr/bin/env python3
"""
Regression Test: Opener Assignment Fix

Bug Description:
- Bot 4 declared 4 but only assigned 2 openers to plan
- The other 2 openers (ADVISOR pieces) became burden and were disposed
- This happened because code limited opener assignment to 2 regardless of target

Fix Applied:
- Opener assignment now based on target_remaining (ai_turn_strategy.py line ~598)
- Formula: openers_needed = min(target_remaining, 4, len(all_openers))

Test Scenarios:
1. Bot declaring 4 with 4 openers - should preserve all 4
2. Bot declaring 2 with 4 openers - should preserve 2
3. Bot declaring 6 with 4 openers - should preserve all 4 (capped)
4. Bot declaring 3 with 2 openers - should preserve both
"""

from conftest import AIDecisionTester

def test_opener_assignment_regression():
    """Ensure openers are assigned based on declaration target"""
    tester = AIDecisionTester()
    
    # Original Bug: Bot 4 from room EBA903 Round 2
    tester.add_scenario(
        name="Bot 4 Original Bug - Declare 4 with 4 Openers",
        description="Should preserve all 4 openers when declaring 4",
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
        declared=4,
        captured=0,
        required_pieces=2,
        turn_number=1,
        is_starter=False
    )
    
    # Contrast: Same hand but declaring 2
    tester.add_scenario(
        name="Same Hand Declaring 2",
        description="Should preserve only 2 openers when declaring 2",
        bot_name="Conservative Bot",
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
        declared=2,
        captured=0,
        required_pieces=2,
        turn_number=1,
        is_starter=False
    )
    
    # Edge case: Declaring more than available openers
    tester.add_scenario(
        name="Declare 6 with 4 Openers",
        description="Should preserve all 4 openers (can't preserve more than exist)",
        bot_name="Ambitious Bot",
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
        declared=6,
        captured=0,
        required_pieces=2,
        turn_number=1,
        is_starter=False
    )
    
    # Edge case: Limited openers
    tester.add_scenario(
        name="Declare 3 with 2 Openers",
        description="Should preserve both openers (all available)",
        bot_name="Limited Bot",
        hand_specs=[
            ("ADVISOR_RED", 1),      # 12 points - opener
            ("ADVISOR_BLACK", 1),    # 11 points - opener
            ("ELEPHANT_RED", 1),     # 10 points - NOT opener
            ("CHARIOT_RED", 1),      # 8 points
            ("CHARIOT_BLACK", 1),    # 7 points
            ("CANNON_BLACK", 2),     # 3 points each
            ("SOLDIER_RED", 1),      # 2 points
        ],
        declared=3,
        captured=0,
        required_pieces=2,
        turn_number=1,
        is_starter=False
    )
    
    # Capture results
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
    print("REGRESSION TEST RESULTS")
    print("="*60)
    
    # Check Bot 4 fix
    bot4_result = test_results[0]
    if bot4_result:
        assigned_openers = bot4_result['plan'].get('assigned_openers', [])
        if len(assigned_openers) == 4:
            print("✅ Bot 4 correctly assigned all 4 openers when declaring 4")
            
            # Also check what was played
            chosen = bot4_result['chosen_play']
            if all(p.point < 11 for p in chosen):
                print("   And correctly played non-opener pieces")
            else:
                print("❌ ERROR: Bot 4 still playing openers!")
                return False
        else:
            print(f"❌ REGRESSION: Bot 4 only assigned {len(assigned_openers)} openers instead of 4!")
            return False
    
    # Check conservative bot
    conservative_result = test_results[1]
    if conservative_result:
        assigned_openers = conservative_result['plan'].get('assigned_openers', [])
        if len(assigned_openers) == 2:
            print("✅ Conservative Bot correctly assigned 2 openers when declaring 2")
        else:
            print(f"❌ ERROR: Conservative Bot assigned {len(assigned_openers)} openers instead of 2")
            return False
    
    # Check edge cases
    ambitious_result = test_results[2]
    if ambitious_result:
        assigned_openers = ambitious_result['plan'].get('assigned_openers', [])
        if len(assigned_openers) == 4:
            print("✅ Ambitious Bot correctly capped at 4 available openers")
        else:
            print(f"❌ ERROR: Ambitious Bot assigned {len(assigned_openers)} openers")
            return False
    
    limited_result = test_results[3]
    if limited_result:
        assigned_openers = limited_result['plan'].get('assigned_openers', [])
        if len(assigned_openers) == 2:
            print("✅ Limited Bot correctly assigned all 2 available openers")
        else:
            print(f"❌ ERROR: Limited Bot assigned {len(assigned_openers)} openers")
            return False
    
    return True

if __name__ == "__main__":
    success = test_opener_assignment_regression()
    exit(0 if success else 1)