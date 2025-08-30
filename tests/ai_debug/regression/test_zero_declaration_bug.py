#!/usr/bin/env python3
"""
Regression Test: Zero Declaration with Strong Hand Bug
This test ensures the AI doesn't declare 0 when it has 2+ openers
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.ai_debug.fixtures.helpers import run_declaration_test


def test_zero_declaration_with_openers():
    """Test that AI doesn't declare 0 with strong openers"""
    print("Testing Zero Declaration Bug Fix...")
    print("-" * 50)
    
    test_cases = [
        {
            'name': 'Two Generals (strongest possible)',
            'hand': [
                "GENERAL_BLACK", "GENERAL_RED",
                "SOLDIER_BLACK", "SOLDIER_RED", "CANNON_BLACK",
                "CANNON_RED", "HORSE_BLACK", "HORSE_RED"
            ],
            'min_declaration': 2,
            'description': 'With 2 GENERALs, should declare at least 2'
        },
        {
            'name': 'Three Advisors',
            'hand': [
                "ADVISOR_BLACK", "ADVISOR_RED", "ADVISOR_BLACK",
                "SOLDIER_BLACK", "SOLDIER_RED", "CANNON_BLACK",
                "CANNON_RED", "HORSE_BLACK"
            ],
            'min_declaration': 2,
            'description': 'With 3 ADVISORs, should declare at least 2-3'
        },
        {
            'name': 'Mixed strong openers',
            'hand': [
                "GENERAL_BLACK", "ADVISOR_RED", "ADVISOR_BLACK",
                "CANNON_BLACK", "CANNON_RED", "HORSE_BLACK",
                "HORSE_RED", "SOLDIER_BLACK"
            ],
            'min_declaration': 2,
            'description': 'With 1 GENERAL + 2 ADVISORs, should declare at least 2-3'
        },
        {
            'name': 'Two openers in non-starter position',
            'hand': [
                "ADVISOR_BLACK", "ADVISOR_RED",
                "SOLDIER_BLACK", "SOLDIER_RED", "CANNON_BLACK",
                "CANNON_RED", "HORSE_BLACK", "HORSE_RED"
            ],
            'min_declaration': 1,
            'description': 'Non-starter with 2 ADVISORs should declare at least 1'
        }
    ]
    
    all_passed = True
    failures = []
    
    # Test as starter (position 0)
    print("\nAs STARTER:")
    for test in test_cases[:3]:
        print(f"\n{test['name']}:")
        print(f"  {test['description']}")
        
        result = run_declaration_test(
            hand_specs=test['hand'],
            position=0,  # Starter
            previous_declarations=[],
            expected_min=test['min_declaration']
        )
        
        print(f"  AI declared: {result['declaration']}")
        
        if result['declaration'] >= test['min_declaration']:
            print("  ✓ PASSED - No zero declaration bug")
        else:
            print("  ✗ FAILED - ZERO DECLARATION BUG DETECTED!")
            all_passed = False
            failures.append(f"Starter {test['name']}: declared {result['declaration']}")
            
    # Test as non-starter
    print("\n\nAs NON-STARTER (position 2):")
    for test in test_cases:
        print(f"\n{test['name']}:")
        print(f"  {test['description']}")
        
        result = run_declaration_test(
            hand_specs=test['hand'],
            position=2,
            previous_declarations=[2, 1],  # Normal field
            expected_min=test['min_declaration'] if test == test_cases[3] else test['min_declaration'] - 1
        )
        
        print(f"  AI declared: {result['declaration']}")
        
        min_expected = test['min_declaration'] if test == test_cases[3] else test['min_declaration'] - 1
        
        if result['declaration'] >= min_expected:
            print("  ✓ PASSED - No zero declaration bug")
        else:
            print("  ✗ FAILED - ZERO DECLARATION BUG DETECTED!")
            all_passed = False
            failures.append(f"Non-starter {test['name']}: declared {result['declaration']}")
            
    return all_passed, failures


def test_edge_cases():
    """Test edge cases around the bug fix"""
    print("\n\nTesting Edge Cases...")
    print("-" * 50)
    
    edge_cases = [
        {
            'name': 'Exactly 2 openers with pile room constraint',
            'hand': [
                "ADVISOR_BLACK", "ADVISOR_RED",
                "SOLDIER_BLACK", "SOLDIER_RED", "CANNON_BLACK",
                "CANNON_RED", "HORSE_BLACK", "HORSE_RED"
            ],
            'position': 3,  # Last player
            'previous': [3, 2, 2],  # Sum = 7, can only declare 0 or 2+
            'forbidden': 1,  # Cannot declare 1 (would sum to 8)
            'min_declaration': 2  # Should declare 2+ to avoid 0
        },
        {
            'name': 'Strong hand with zero streak rule',
            'hand': [
                "GENERAL_BLACK", "ADVISOR_RED",
                "SOLDIER_BLACK", "SOLDIER_RED", "CANNON_BLACK",
                "CANNON_RED", "HORSE_BLACK", "HORSE_RED"
            ],
            'must_declare_nonzero': True,
            'min_declaration': 1
        }
    ]
    
    all_passed = True
    
    for test in edge_cases:
        print(f"\n{test['name']}:")
        
        if 'previous' in test:
            result = run_declaration_test(
                hand_specs=test['hand'],
                position=test.get('position', 1),
                previous_declarations=test['previous'],
                expected_min=test['min_declaration']
            )
            print(f"  Previous declarations: {test['previous']}")
            print(f"  Cannot declare: {test.get('forbidden', 'N/A')}")
        else:
            result = run_declaration_test(
                hand_specs=test['hand'],
                position=1,
                previous_declarations=[2],
                must_declare_nonzero=test.get('must_declare_nonzero', False),
                expected_min=test['min_declaration']
            )
            print(f"  Must declare non-zero: {test.get('must_declare_nonzero', False)}")
            
        print(f"  AI declared: {result['declaration']}")
        
        if result['passed']:
            print("  ✓ PASSED")
        else:
            print(f"  ✗ FAILED: {result['message']}")
            all_passed = False
            
    return all_passed


if __name__ == "__main__":
    print("="*60)
    print("REGRESSION TEST: Zero Declaration with Strong Hand Bug")
    print("="*60)
    print("\nThis bug was found 15 times in 5 games during initial testing.")
    print("AI would declare 0 despite having 2-3 openers (GENERAL/ADVISOR).")
    print("="*60)
    
    # Run tests
    test1_passed, failures = test_zero_declaration_with_openers()
    test2_passed = test_edge_cases()
    
    # Summary
    print("\n" + "="*60)
    print("REGRESSION TEST SUMMARY")
    print("="*60)
    
    if test1_passed and test2_passed:
        print("✓ ALL TESTS PASSED - Zero declaration bug appears FIXED")
    else:
        print("✗ REGRESSION DETECTED - Zero declaration bug still present!")
        if failures:
            print("\nFailures:")
            for failure in failures:
                print(f"  - {failure}")
        print("\nThe AI is still declaring 0 with strong hands.")
        print("This bug needs to be fixed in choose_declare_strategic_v2()")
        exit(1)