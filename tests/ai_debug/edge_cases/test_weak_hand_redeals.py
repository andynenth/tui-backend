#!/usr/bin/env python3
"""
Test Edge Case: Weak Hand Redeals
This tests the scenario where players have very weak hands (no piece > 9 points)
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.ai_debug.fixtures.helpers import run_declaration_test, create_test_hand


def test_weak_hand_scenarios():
    """Test various weak hand scenarios"""
    print("Testing Weak Hand Scenarios...")
    print("-" * 50)
    
    test_cases = [
        {
            'name': 'Extremely weak hand (highest piece is 6)',
            'hand': [
                "SOLDIER_BLACK", "SOLDIER_RED", "SOLDIER_BLACK",
                "CANNON_BLACK", "CANNON_RED", "HORSE_BLACK",
                "HORSE_RED", "SOLDIER_RED"
            ],
            'expected_max': 1,  # Should declare 0 or 1
        },
        {
            'name': 'Weak hand with one 9-point piece',
            'hand': [
                "ELEPHANT_BLACK", "SOLDIER_RED", "SOLDIER_BLACK",  # Elephant = 9
                "CANNON_BLACK", "CANNON_RED", "HORSE_BLACK",
                "HORSE_RED", "SOLDIER_RED"
            ],
            'expected_max': 2,  # Might declare 0-2
        },
        {
            'name': 'Borderline weak hand (two 8-point pieces)',
            'hand': [
                "CHARIOT_BLACK", "CHARIOT_RED", "SOLDIER_BLACK",  # Chariots = 8 each
                "CANNON_BLACK", "CANNON_RED", "HORSE_BLACK",
                "HORSE_RED", "SOLDIER_RED"
            ],
            'expected_max': 2,  # Could win with pairs
        },
        {
            'name': 'Weak hand but many pairs',
            'hand': [
                "SOLDIER_BLACK", "SOLDIER_RED", "CANNON_BLACK",
                "CANNON_RED", "HORSE_BLACK", "HORSE_RED",
                "SOLDIER_BLACK", "SOLDIER_RED"  # Multiple pairs available
            ],
            'expected_min': 0,
            'expected_max': 3,  # Pairs might win in weak field
        }
    ]
    
    all_passed = True
    
    for test in test_cases:
        print(f"\n{test['name']}:")
        print(f"  Hand pieces: {test['hand'][:4]}...")
        
        result = run_declaration_test(
            hand_specs=test['hand'],
            position=1,
            previous_declarations=[1],  # Weak field
            expected_min=test.get('expected_min', 0),
            expected_max=test['expected_max']
        )
        
        print(f"  AI declared: {result['declaration']}")
        
        if result['passed']:
            print("  ✓ PASSED - Declaration appropriate for weak hand")
        else:
            print(f"  ✗ FAILED: {result['message']}")
            all_passed = False
            
    return all_passed


def test_weak_field_dynamics():
    """Test how AI adapts when all players have weak hands"""
    print("\n\nTesting Weak Field Dynamics...")
    print("-" * 50)
    
    # Moderate hand in a weak field
    moderate_hand = [
        "ELEPHANT_BLACK", "CHARIOT_RED", "HORSE_BLACK",
        "CANNON_BLACK", "CANNON_RED", "HORSE_RED",
        "SOLDIER_BLACK", "SOLDIER_RED"
    ]
    
    scenarios = [
        {
            'name': 'Position 0 - First to declare in weak field',
            'position': 0,
            'previous': [],
            'expected_min': 2,  # Should be optimistic as starter
            'expected_max': 4,
        },
        {
            'name': 'Position 1 - After weak declaration',
            'position': 1,
            'previous': [1],  # First player declared 1
            'expected_min': 1,  # Should recognize weak field
            'expected_max': 3,
        },
        {
            'name': 'Position 2 - Multiple weak declarations',
            'position': 2,
            'previous': [1, 0],  # Very weak field
            'expected_min': 2,  # Should be more aggressive
            'expected_max': 4,
        },
        {
            'name': 'Position 3 - Last in weak field',
            'position': 3,
            'previous': [1, 0, 1],  # Total = 2, cannot declare 6
            'expected_min': 2,
            'expected_max': 5,  # Cannot declare 6 (would sum to 8)
        }
    ]
    
    all_passed = True
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  Previous declarations: {scenario['previous']}")
        
        result = run_declaration_test(
            hand_specs=moderate_hand,
            position=scenario['position'],
            previous_declarations=scenario['previous'],
            expected_min=scenario['expected_min'],
            expected_max=scenario['expected_max']
        )
        
        print(f"  AI declared: {result['declaration']}")
        
        if result['passed']:
            print("  ✓ PASSED")
        else:
            print(f"  ✗ FAILED: {result['message']}")
            all_passed = False
            
    return all_passed


if __name__ == "__main__":
    print("="*60)
    print("EDGE CASE TEST: Weak Hand Scenarios")
    print("="*60)
    
    # Run tests
    test1_passed = test_weak_hand_scenarios()
    test2_passed = test_weak_field_dynamics()
    
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