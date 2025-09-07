#!/usr/bin/env python3
"""
Test Edge Case: All Players Declare Zero
This tests the scenario where all players have weak hands and want to declare 0
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.ai_debug.fixtures.helpers import run_declaration_test, create_test_hand


def test_all_zero_declarations():
    """Test when all players try to declare 0"""
    print("Testing All Zero Declarations Scenario...")
    print("-" * 50)

    # Weak hand with no openers
    weak_hand = [
        "SOLDIER_BLACK", "SOLDIER_RED", "SOLDIER_BLACK",
        "CANNON_BLACK", "CANNON_RED", "HORSE_BLACK",
        "CHARIOT_BLACK", "ELEPHANT_BLACK"
    ]

    test_cases = [
        {
            'name': 'Position 0 - First to declare 0',
            'position': 0,
            'previous_declarations': [],
            'expected_min': 0,
            'expected_max': 1,  # Should declare 0 or 1 with weak hand
        },
        {
            'name': 'Position 1 - Second player, first declared 0',
            'position': 1,
            'previous_declarations': [0],
            'expected_min': 0,
            'expected_max': 1,
        },
        {
            'name': 'Position 2 - Third player, both declared 0',
            'position': 2,
            'previous_declarations': [0, 0],
            'expected_min': 0,
            'expected_max': 1,
        },
        {
            'name': 'Position 3 - Last player, all declared 0',
            'position': 3,
            'previous_declarations': [0, 0, 0],
            'expected_min': 1,  # Cannot declare 0 (would make sum 0)
            'expected_max': 8,  # Can declare anything but 0
        },
    ]

    all_passed = True

    for test in test_cases:
        print(f"\n{test['name']}:")
        print(f"  Previous declarations: {test['previous_declarations']}")

        result = run_declaration_test(
            hand_specs=weak_hand,
            position=test['position'],
            previous_declarations=test['previous_declarations'],
            expected_min=test['expected_min'],
            expected_max=test['expected_max']
        )

        print(f"  AI declared: {result['declaration']}")

        if result['passed']:
            print("  ✓ PASSED")
        else:
            print(f"  ✗ FAILED: {result['message']}")
            all_passed = False

    # Test with zero streak rule
    print("\n\nTesting with Zero Streak Rule (must declare non-zero):")
    print("-" * 50)

    result = run_declaration_test(
        hand_specs=weak_hand,
        position=1,
        previous_declarations=[3],
        must_declare_nonzero=True,
        expected_min=1,  # Must declare at least 1
        expected_max=5   # But not too high with weak hand
    )

    print(f"AI declared: {result['declaration']} (must be non-zero)")

    if result['passed']:
        print("✓ PASSED - Correctly avoided zero declaration")
    else:
        print(f"✗ FAILED: {result['message']}")
        all_passed = False

    return all_passed


def test_strategic_zero_declaration():
    """Test strategic zero declaration with different hand strengths"""
    print("\n\nTesting Strategic Zero Declarations...")
    print("-" * 50)

    test_hands = [
        {
            'name': 'Very weak hand (no pieces > 6)',
            'hand': [
                "SOLDIER_BLACK", "SOLDIER_RED", "CANNON_BLACK",
                "CANNON_RED", "HORSE_BLACK", "HORSE_RED",
                "SOLDIER_BLACK", "SOLDIER_RED"
            ],
            'expected_declaration': 0
        },
        {
            'name': 'Medium hand (one opener)',
            'hand': [
                "ADVISOR_BLACK", "SOLDIER_RED", "CANNON_BLACK",
                "CANNON_RED", "HORSE_BLACK", "HORSE_RED",
                "CHARIOT_BLACK", "ELEPHANT_BLACK"
            ],
            'expected_declaration': 1  # Should declare at least 1
        },
        {
            'name': 'Strong hand (multiple openers)',
            'hand': [
                "GENERAL_BLACK", "ADVISOR_RED", "ADVISOR_BLACK",
                "CANNON_RED", "HORSE_BLACK", "HORSE_RED",
                "CHARIOT_BLACK", "ELEPHANT_BLACK"
            ],
            'expected_declaration': 2  # Should declare at least 2
        }
    ]

    all_passed = True

    for test in test_hands:
        print(f"\n{test['name']}:")
        print(f"  Hand: {test['hand'][:4]}...")  # Show first 4 pieces

        result = run_declaration_test(
            hand_specs=test['hand'],
            position=1,
            previous_declarations=[2],
            expected_min=test['expected_declaration'],
            expected_max=test['expected_declaration'] + 2
        )

        print(f"  AI declared: {result['declaration']} (expected ~{test['expected_declaration']})")

        if result['declaration'] >= test['expected_declaration']:
            print("  ✓ PASSED - Declaration matches hand strength")
        else:
            print(f"  ✗ FAILED - Under-declared with this hand")
            all_passed = False

    return all_passed


if __name__ == "__main__":
    print("="*60)
    print("EDGE CASE TEST: All Zero Declarations")
    print("="*60)

    # Run tests
    test1_passed = test_all_zero_declarations()
    test2_passed = test_strategic_zero_declaration()

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
