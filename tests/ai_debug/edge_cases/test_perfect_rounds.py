#!/usr/bin/env python3
"""
Test Edge Case: Perfect Declaration Rounds
This tests scenarios where players achieve exactly their declared targets
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.ai_debug.fixtures.helpers import run_declaration_test, run_turn_play_test


def test_perfect_declaration_hands():
    """Test hands that are likely to achieve perfect declarations"""
    print("Testing Perfect Declaration Scenarios...")
    print("-" * 50)
    
    perfect_hands = [
        {
            'name': 'Two strong openers (should declare 2)',
            'hand': [
                "GENERAL_BLACK", "GENERAL_RED",  # Two strongest pieces
                "SOLDIER_BLACK", "SOLDIER_RED", "CANNON_BLACK",
                "CANNON_RED", "HORSE_BLACK", "HORSE_RED"
            ],
            'expected_declaration': 2,
            'confidence': 'Very High'
        },
        {
            'name': 'Three openers (should declare 3)',
            'hand': [
                "GENERAL_BLACK", "ADVISOR_RED", "ADVISOR_BLACK",
                "SOLDIER_BLACK", "SOLDIER_RED", "CANNON_BLACK",
                "CANNON_RED", "HORSE_BLACK"
            ],
            'expected_declaration': 3,
            'confidence': 'High'
        },
        {
            'name': 'One opener + strong combo',
            'hand': [
                "GENERAL_BLACK", "SOLDIER_BLACK", "SOLDIER_RED",
                "SOLDIER_BLACK", "CANNON_BLACK", "CANNON_RED",
                "HORSE_BLACK", "HORSE_RED"  # Has THREE_OF_A_KIND
            ],
            'expected_declaration': 2,  # 1 opener + 1 combo
            'confidence': 'High'
        },
        {
            'name': 'Balanced hand with pairs',
            'hand': [
                "ADVISOR_BLACK", "HORSE_BLACK", "HORSE_RED",
                "CHARIOT_BLACK", "CHARIOT_RED", "CANNON_BLACK",
                "CANNON_RED", "SOLDIER_BLACK"  # Multiple pairs
            ],
            'expected_declaration': 2,  # 1 opener + 1 strong pair
            'confidence': 'Medium'
        }
    ]
    
    all_passed = True
    
    for test in perfect_hands:
        print(f"\n{test['name']}:")
        print(f"  Confidence for perfect round: {test['confidence']}")
        
        result = run_declaration_test(
            hand_specs=test['hand'],
            position=0,  # As starter for best control
            previous_declarations=[],
            expected_min=test['expected_declaration'],
            expected_max=test['expected_declaration'] + 1  # Allow slight variation
        )
        
        print(f"  AI declared: {result['declaration']} (expected {test['expected_declaration']})")
        
        if abs(result['declaration'] - test['expected_declaration']) <= 1:
            print("  ✓ PASSED - Declaration reasonable for perfect round")
        else:
            print("  ✗ FAILED - Declaration too far from expected")
            all_passed = False
            
    return all_passed


def test_turn_play_for_perfect_round():
    """Test turn play decisions when aiming for perfect round"""
    print("\n\nTesting Turn Play for Perfect Rounds...")
    print("-" * 50)
    
    scenarios = [
        {
            'name': 'At target - should play weakest',
            'hand': ["GENERAL_BLACK", "ADVISOR_RED", "SOLDIER_BLACK", "CANNON_RED"],
            'my_declared': 2,
            'my_captured': 2,  # Already at target
            'expected_piece': 'weak',  # Should play SOLDIER or CANNON
        },
        {
            'name': 'Need 1 more - should play strong',
            'hand': ["GENERAL_BLACK", "ADVISOR_RED", "SOLDIER_BLACK", "CANNON_RED"],
            'my_declared': 3,
            'my_captured': 2,  # Need 1 more
            'expected_piece': 'strong',  # Should play GENERAL or ADVISOR
        },
        {
            'name': 'Need 2 more with 2 turns left',
            'hand': ["GENERAL_BLACK", "ADVISOR_RED", "HORSE_BLACK", "CANNON_RED"],
            'my_declared': 4,
            'my_captured': 2,  # Need 2 more
            'expected_piece': 'strong',  # Should save weak for later
        },
        {
            'name': 'Perfect pace - balanced play',
            'hand': ["ADVISOR_BLACK", "HORSE_RED", "CHARIOT_BLACK", "CANNON_RED"],
            'my_declared': 3,
            'my_captured': 1,  # On track (1/3 with 6 pieces left)
            'expected_piece': 'medium',  # Can play HORSE or CHARIOT
        }
    ]
    
    all_passed = True
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  Declared: {scenario['my_declared']}, Captured: {scenario['my_captured']}")
        
        result = run_turn_play_test(
            hand_specs=scenario['hand'],
            required_count=1,  # Single piece play
            my_declared=scenario['my_declared'],
            my_captured=scenario['my_captured']
        )
        
        selected_piece = result['selected_play'][0] if result['selected_play'] else None
        
        if selected_piece:
            # Determine if played piece matches expectation
            piece_value = next(p.point for p in run_turn_play_test(scenario['hand'], 1)['selected_play'] 
                             if f"{p.name}_{p.color}" == selected_piece)
            
            if scenario['expected_piece'] == 'weak' and piece_value <= 5:
                assessment = "✓ Correctly played weak piece"
            elif scenario['expected_piece'] == 'strong' and piece_value >= 11:
                assessment = "✓ Correctly played strong piece"
            elif scenario['expected_piece'] == 'medium' and 5 < piece_value < 11:
                assessment = "✓ Correctly played medium piece"
            else:
                assessment = "✗ Did not play expected strength piece"
                all_passed = False
        else:
            assessment = "✗ No piece selected"
            all_passed = False
            
        print(f"  Selected: {selected_piece}")
        print(f"  {assessment}")
        
    return all_passed


if __name__ == "__main__":
    print("="*60)
    print("EDGE CASE TEST: Perfect Declaration Rounds")
    print("="*60)
    
    # Run tests
    test1_passed = test_perfect_declaration_hands()
    test2_passed = test_turn_play_for_perfect_round()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if test1_passed and test2_passed:
        print("✓ ALL TESTS PASSED")
        exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        exit(1)