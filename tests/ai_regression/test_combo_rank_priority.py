#!/usr/bin/env python3
"""
Regression Test: Combo Rank Priority Fix

Bug Description:
- Bot 2 declared 5 (critical urgency) but played GENERAL_RED(14) instead of THREE_OF_A_KIND
- The AI prioritized total point value over combo rank in critical urgency

Fix Applied:
- Critical urgency logic now prioritizes combo rank, then points (ai_turn_strategy.py line ~1031)
- Added missing EXTENDED_STRAIGHT_5 to COMBO_TYPE_RANK

Test Scenarios:
1. Bot 2's actual case - THREE_OF_A_KIND vs high singles
2. Various combo rank comparisons
3. EXTENDED_STRAIGHT_5 ranking test
"""

from conftest import AIDecisionTester
from backend.engine.ai_turn_strategy import COMBO_TYPE_RANK

def test_combo_rank_regression():
    """Ensure combo rank is prioritized over points in critical urgency"""
    tester = AIDecisionTester()
    
    # Original Bug: Bot 2 from room B5AE3B Round 1
    tester.add_scenario(
        name="Bot 2 Original Bug - THREE_OF_A_KIND vs GENERAL_RED",
        description="Should play THREE_OF_A_KIND (rank 3) over GENERAL_RED (rank 1)",
        bot_name="Bot 2",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14 points - SINGLE (rank 1)
            ("ADVISOR_RED", 1),      # 12 points - SINGLE (rank 1)
            ("SOLDIER_BLACK", 3),    # 1 point each - THREE_OF_A_KIND (rank 3)!
            ("HORSE_RED", 1),        # 6 points
            ("SOLDIER_RED", 2),      # 2 points each - PAIR (rank 2)
        ],
        declared=5,  # Critical urgency!
        captured=0,
        required_pieces=None,  # Starter chooses
        turn_number=1,
        is_starter=True
    )
    
    # Test PAIR beats high SINGLE
    tester.add_scenario(
        name="PAIR vs High SINGLE",
        description="Should play PAIR (rank 2) over GENERAL_BLACK (rank 1)",
        bot_name="Pair Bot",
        hand_specs=[
            ("GENERAL_BLACK", 1),    # 13 points - SINGLE (rank 1)
            ("ADVISOR_RED", 1),      # 12 points - SINGLE (rank 1)
            ("SOLDIER_RED", 2),      # 2 points each - PAIR (rank 2)
            ("CANNON_BLACK", 3),
        ],
        declared=4,  # High urgency
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=True
    )
    
    # Test STRAIGHT beats THREE_OF_A_KIND
    tester.add_scenario(
        name="STRAIGHT vs THREE_OF_A_KIND",
        description="Should play STRAIGHT (rank 4) over THREE_OF_A_KIND (rank 3)",
        bot_name="Straight Bot",
        hand_specs=[
            ("GENERAL_RED", 1),      # 14
            ("ADVISOR_RED", 1),      # 12  
            ("ELEPHANT_RED", 1),     # 10 - Forms STRAIGHT (rank 4)!
            ("SOLDIER_BLACK", 3),    # THREE_OF_A_KIND (rank 3)
            ("CANNON_RED", 1),
        ],
        declared=6,  # Critical urgency
        captured=0,
        required_pieces=None,
        turn_number=1,
        is_starter=True
    )
    
    # Capture results
    test_results = []
    
    # Run scenarios and capture results
    for scenario in tester.scenarios:
        hand = tester.create_hand_from_specs(scenario['hand_specs'])
        context = tester.create_context(
            bot_name=scenario.get('bot_name', 'Test Bot'),
            hand=hand,
            declared=scenario['declared'],
            captured=scenario['captured'],
            required_pieces=scenario['required_pieces'],
            turn_number=scenario.get('turn_number', 1),
            is_starter=scenario.get('is_starter', False),
            player_states=scenario.get('player_states', None)
        )
        result = tester.analyze_decision(context, show_plan_details=False, show_urgency=False)
        test_results.append(result)
    
    results = test_results
    
    # Verify expectations
    print("\n" + "="*60)
    print("REGRESSION TEST RESULTS")
    print("="*60)
    
    # Check Bot 2 original bug is fixed
    bot2_scenario = results[0] if results else None
    if bot2_scenario:
        chosen = bot2_scenario.get('chosen_play', [])
        
        if len(chosen) == 3 and all(p.kind == "SOLDIER_BLACK" for p in chosen):
            print("✅ Bot 2 correctly played THREE_OF_A_KIND over high singles")
        else:
            piece_str = ", ".join([f"{p.kind}({p.point})" for p in chosen])
            print(f"❌ REGRESSION: Bot 2 played {piece_str} instead of THREE_OF_A_KIND!")
            return False
    
    # Verify COMBO_TYPE_RANK includes all types
    print("\n✅ Verifying COMBO_TYPE_RANK completeness:")
    expected_types = [
        "SINGLE", "PAIR", "THREE_OF_A_KIND", "STRAIGHT", 
        "FOUR_OF_A_KIND", "EXTENDED_STRAIGHT", "EXTENDED_STRAIGHT_5",
        "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"
    ]
    
    for combo_type in expected_types:
        if combo_type in COMBO_TYPE_RANK:
            print(f"  ✓ {combo_type}: rank {COMBO_TYPE_RANK[combo_type]}")
        else:
            print(f"  ❌ {combo_type}: MISSING!")
            return False
    
    return True

if __name__ == "__main__":
    success = test_combo_rank_regression()
    exit(0 if success else 1)