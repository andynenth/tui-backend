#!/usr/bin/env python3
"""
Regression Test: Combo Preservation Fix

Bug Description:
- Bot 3 declared 0 but preserved ADVISOR_RED pair instead of disposing them
- The AI assigned combos to the plan even when target_remaining was 0

Fix Applied:
- Only preserve combos if target_remaining > 0 (ai_turn_strategy.py line ~631)

Test Scenarios:
1. Bot declaring 0 with strong combo - should dispose combo pieces
2. Bot declaring positive with combo - should preserve combo pieces
"""

from conftest import AIDecisionTester

def test_combo_preservation_regression():
    """Ensure combos are not preserved when declaring 0"""
    tester = AIDecisionTester()
    
    # Original Bug: Bot 3 from room 66042B Round 3
    tester.add_scenario(
        name="Bot 3 Original Bug - Declare 0 with ADVISOR_RED pair",
        description="Should dispose ADVISOR_RED pieces, not preserve them",
        bot_name="Bot 3",
        hand_specs=[
            ("ADVISOR_RED", 2),      # Should be disposed!
            ("ADVISOR_BLACK", 1),
            ("CHARIOT_RED", 1),
            ("CHARIOT_BLACK", 1),
            ("SOLDIER_RED", 1),
            ("SOLDIER_BLACK", 2),
        ],
        declared=0,
        captured=0,
        required_pieces=4,
        turn_number=1
    )
    
    # Contrast case: Same hand but declaring positive
    tester.add_scenario(
        name="Bot Declaring 2 with ADVISOR_RED pair",
        description="Should preserve ADVISOR_RED pair for later use",
        bot_name="Strategic Bot",
        hand_specs=[
            ("ADVISOR_RED", 2),      # Should be preserved!
            ("ADVISOR_BLACK", 1),
            ("CHARIOT_RED", 1),
            ("CHARIOT_BLACK", 1),
            ("SOLDIER_RED", 1),
            ("SOLDIER_BLACK", 2),
        ],
        declared=2,
        captured=0,
        required_pieces=4,
        turn_number=1
    )
    
    # Edge case: Declaring 0 with multiple combo types
    tester.add_scenario(
        name="Declare 0 with Multiple Combos",
        description="Should dispose all combo pieces when declaring 0",
        bot_name="Combo Bot",
        hand_specs=[
            ("ADVISOR_RED", 2),      # Pair
            ("SOLDIER_BLACK", 3),    # Three of a kind
            ("GENERAL_RED", 1),
            ("CANNON_BLACK", 1),
            ("HORSE_RED", 1),
        ],
        declared=0,
        captured=0,
        required_pieces=3,
        turn_number=1
    )
    
    # Capture results by modifying the tester slightly
    test_results = []
    
    # Run scenarios and capture results
    for scenario in tester.scenarios:
        # Run the scenario
        print(f"\n{'*'*60}")
        print(f"Running: {scenario['name']}")
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
        result = tester.analyze_decision(context)
        test_results.append(result)
    
    results = test_results
    
    # Verify expectations
    print("\n" + "="*60)
    print("REGRESSION TEST RESULTS")
    print("="*60)
    
    # Check Bot 3 combo preservation is fixed
    bot3_scenario = results[0] if results else None
    if bot3_scenario:
        plan = bot3_scenario.get('plan', {})
        assigned_combos = plan.get('assigned_combos', [])
        
        # When declaring 0, should NOT assign combos to preserve
        if len(assigned_combos) == 0:
            print("✅ Bot 3 correctly did NOT preserve ADVISOR_RED pair when declaring 0")
            
            # Note: Bot 3 will still PLAY high-value pieces as disposal strategy
            # This is correct behavior - dispose high value burden pieces first
            chosen = bot3_scenario.get('chosen_play', [])
            if any(p.kind == "ADVISOR_RED" for p in chosen):
                print("   (Playing ADVISOR_RED as disposal is correct - high value burden)")
        else:
            print("❌ REGRESSION: Bot 3 assigned combos to preserve when declaring 0!")
            return False
    
    # Check contrast case preserves valuable pieces
    strategic_scenario = results[1] if len(results) > 1 else None
    if strategic_scenario:
        plan = strategic_scenario.get('plan', {})
        assigned_combos = plan.get('assigned_combos', [])
        assigned_openers = plan.get('assigned_openers', [])
        
        # ADVISOR_RED pieces can be preserved either as combo OR as openers
        advisor_preserved = False
        
        # Check if preserved as combo
        if any(combo[0] == "PAIR" and any(p.kind == "ADVISOR_RED" for p in combo[1]) 
               for combo in assigned_combos):
            advisor_preserved = True
            print("✅ Strategic Bot preserved ADVISOR_RED as PAIR combo")
        
        # Check if preserved as openers
        elif any(p.kind == "ADVISOR_RED" for p in assigned_openers):
            advisor_preserved = True
            print("✅ Strategic Bot preserved ADVISOR_RED pieces as openers")
        
        if not advisor_preserved:
            print("❌ ERROR: Strategic Bot should preserve high-value pieces")
            return False
    
    return True

if __name__ == "__main__":
    success = test_combo_preservation_regression()
    exit(0 if success else 1)