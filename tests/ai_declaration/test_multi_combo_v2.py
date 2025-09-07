#!/usr/bin/env python3
"""
Multi-Combo AI Declaration Tests for V2 Implementation

This module tests the V2 AI's ability to find and play multiple combos
in a single declaration, covering various combo types from PAIR to DOUBLE_STRAIGHT.

Key test areas:
1. Multiple pairs (GENERAL + ADVISOR pairs)
2. THREE_OF_A_KIND combinations
3. STRAIGHT with other combos
4. FOUR_OF_A_KIND + additional combos
5. Greedy vs optimal combo selection
6. Pile room constraints affecting multi-combo play
7. Starter vs non-starter multi-combo behavior
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_multi_combo_v2_scenarios():
    """Get multi-combo test scenarios for V2 declaration logic."""

    multi_combo_tests = [
        # ========================================================================
        # Multiple Pairs Scenarios
        # ========================================================================
        ("multi_combo_01", "[GENERAL_RED, GENERAL_BLACK, ADVISOR_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 6, "Double Strong Pairs (Starter)", True,
         "GENERAL pair (avg=13.5) + ADVISOR pair (avg=11.5) + ELEPHANT pair (avg=9.5)"),

        ("multi_combo_02", "[GENERAL_RED, GENERAL_BLACK, ADVISOR_RED, ADVISOR_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_BLACK]",
         1, [2], 6, "Strong Pairs + STRAIGHT (Non-starter)", False,
         "GENERAL opener + ADVISOR pair + STRAIGHT, pile room allows all"),

        ("multi_combo_03", "[CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 6, "Multiple Weak Pairs (Starter)", True,
         "CHARIOT pair (avg=7.5) + HORSE pair (avg=5.5) both strong"),

        # ========================================================================
        # THREE_OF_A_KIND Combinations
        # ========================================================================
        ("multi_combo_04", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED]",
         0, [], 6, "Double THREE_OF_A_KIND (Starter)", True,
         "Two THREE_OF_A_KIND combos, both weak but playable as starter"),

        ("multi_combo_05", "[ADVISOR_RED, CHARIOT_RED, CHARIOT_RED, CHARIOT_RED, HORSE_BLACK, HORSE_BLACK, HORSE_BLACK, CANNON_BLACK]",
         2, [1, 1], 3, "THREE_OF_A_KIND + Singles (Non-starter)", False,
         "ADVISOR opener + CHARIOT THREE_OF_A_KIND + singles"),

        # ========================================================================
        # STRAIGHT Combinations
        # ========================================================================
        ("multi_combo_06", "[GENERAL_RED, ADVISOR_RED, ELEPHANT_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 6, "Double STRAIGHT (Starter)", True,
         "High STRAIGHT (14+12+10) and low STRAIGHT (7+5+3)"),

        ("multi_combo_07", "[GENERAL_RED, CHARIOT_RED, HORSE_RED, CANNON_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_BLACK]",
         1, [3], 4, "STRAIGHT + Opener (Non-starter)", False,
         "GENERAL opener + STRAIGHT (8+6+4), second STRAIGHT not viable"),

        # ========================================================================
        # FOUR_OF_A_KIND + Other Combos
        # ========================================================================
        ("multi_combo_08", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
         0, [], 7, "FOUR_OF_A_KIND + STRAIGHT (Starter)", True,
         "FOUR_OF_A_KIND soldiers + STRAIGHT"),

        ("multi_combo_09", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, ADVISOR_RED, ADVISOR_BLACK, ELEPHANT_BLACK]",
         2, [2, 1], 6, "FOUR_OF_A_KIND + PAIR (Non-starter)", False,
         "GENERAL opener + SOLDIER FOUR_OF_A_KIND + strong pair"),

        # ========================================================================
        # Complex Greedy vs Optimal Scenarios
        # ========================================================================
        ("multi_combo_10", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, CHARIOT_BLACK]",
         0, [], 6, "Greedy vs Optimal Choice (Starter)", True,
         "Can play all 8 as 4 pairs, or 2 THREE_OF_A_KIND + 2 singles"),

        ("multi_combo_11", "[GENERAL_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
         1, [2], 4, "Optimal Combo Selection (Non-starter)", False,
         "GENERAL + 2 pairs + STRAIGHT better than GENERAL + STRAIGHT + singles"),

        # ========================================================================
        # FIVE_OF_A_KIND Scenarios
        # ========================================================================
        ("multi_combo_12", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, GENERAL_RED, ADVISOR_BLACK, ELEPHANT_BLACK]",
         0, [], 5, "FIVE_OF_A_KIND + Openers (Starter)", True,
         "FIVE_OF_A_KIND soldiers + 2 high cards"),

        # ========================================================================
        # Pile Room Constraint Scenarios
        # ========================================================================
        ("multi_combo_13", "[GENERAL_RED, GENERAL_BLACK, ADVISOR_RED, ADVISOR_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_BLACK]",
         3, [3, 2, 2], 5, "Multi-combo Limited by Pile Room", False,
         "Only pile room 1, so just GENERAL despite having multiple combos"),

        ("multi_combo_14", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
         2, [4, 3], 0, "Combos Exceed Pile Room", False,
         "FOUR_OF_A_KIND + STRAIGHT = 7, but pile room = 1, no opener so 0"),

        # ========================================================================
        # Extended Combos
        # ========================================================================
        ("multi_combo_15", "[CHARIOT_RED, CHARIOT_RED, HORSE_RED, HORSE_RED, CANNON_RED, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 6, "DOUBLE_STRAIGHT Potential (Starter)", True,
         "Can form DOUBLE_STRAIGHT with 6 pieces"),

        # ========================================================================
        # Strategic Multi-Combo Scenarios
        # ========================================================================
        ("multi_combo_16", "[GENERAL_RED, ADVISOR_RED, ADVISOR_BLACK, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         2, [1, 0], 4, "Strong Field Multi-Combo", False,
         "GENERAL + strong ADVISOR pair + ELEPHANT pair despite weak field"),

        ("multi_combo_17", "[CHARIOT_RED, CHARIOT_BLACK, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         0, [], 8, "Multiple Overlapping Combos (Starter)", True,
         "Various pairs and THREE_OF_A_KIND combinations possible"),

        ("multi_combo_18", "[GENERAL_RED, GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         1, [3], 5, "GENERAL Pair + Weak Combos", False,
         "Strong GENERAL pair enables weak THREE_OF_A_KIND play"),
    ]

    # Convert to TestScenario objects
    scenarios = []
    for scenario_data in multi_combo_tests:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus = scenario_data

        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.BASELINE,  # Using baseline category
            subcategory="multi_combo_v2",
            hand_str=hand_str,
            position=position,
            previous_decl=prev_decl,
            expected=expected,
            description=description,
            is_starter=is_starter,
            strategic_focus=focus,
            difficulty_level=DifficultyLevel.ADVANCED,
            notes="Multi-combo V2 test case"
        ))

    return scenarios


def execute_test_scenario_v2(scenario: TestScenario, verbose: bool = False) -> 'TestResult':
    """Execute test scenario using V2 declaration logic."""
    from backend.engine.piece import Piece
    from backend.engine.ai import choose_declare_strategic_v2
    from conftest import TestResult
    import time

    # Parse hand string to create pieces
    hand = []
    parts = scenario.hand_str.replace("[", "").replace("]", "").split(",")
    for part in parts:
        part = part.strip()
        if part:
            # Create piece from name
            hand.append(Piece(part))

    # Execute V2 declaration
    start_time = time.time()
    actual = choose_declare_strategic_v2(
        hand=hand,
        is_first_player=scenario.is_starter,
        position_in_order=scenario.position,
        previous_declarations=scenario.previous_decl,
        must_declare_nonzero=False,
        verbose=verbose
    )
    execution_time = time.time() - start_time

    passed = (actual == scenario.expected)

    return TestResult(
        scenario=scenario,
        actual_result=actual,
        passed=passed,
        execution_time=execution_time
    )


def test_multi_combo_v2_scenarios(verbose_output, enable_ai_analysis):
    """Test all multi-combo V2 scenarios."""
    scenarios = get_multi_combo_v2_scenarios()

    results = []
    for scenario in scenarios:
        result = execute_test_scenario_v2(scenario, verbose=verbose_output)
        results.append(result)

    # Print results
    print(f"\n{'='*80}")
    print(f"MULTI-COMBO V2 TEST RESULTS")
    print(f"{'='*80}")

    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        diff = f" ({result.actual_result - result.scenario.expected:+d})" if not result.passed else ""
        print(f"{status} {result.scenario.scenario_id}: {result.scenario.description}{diff}")

    passed_count = sum(1 for r in results if r.passed)
    total_count = len(results)
    print(f"\n🎯 MULTI-COMBO V2 SUMMARY: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)")

    # Group by subcategories for analysis
    pair_scenarios = [r for r in results if "Pair" in r.scenario.description or "PAIR" in r.scenario.strategic_focus]
    three_kind_scenarios = [r for r in results if "THREE_OF_A_KIND" in r.scenario.description or r.scenario.strategic_focus]
    straight_scenarios = [r for r in results if "STRAIGHT" in r.scenario.description or r.scenario.strategic_focus]
    complex_scenarios = [r for r in results if "Greedy" in r.scenario.description or "Optimal" in r.scenario.description]

    # Report subcategory results
    if pair_scenarios:
        pair_passed = sum(1 for r in pair_scenarios if r.passed)
        print(f"\n📊 Pair Combo Scenarios: {pair_passed}/{len(pair_scenarios)} passed")

    if three_kind_scenarios:
        three_passed = sum(1 for r in three_kind_scenarios if r.passed)
        print(f"📊 THREE_OF_A_KIND Scenarios: {three_passed}/{len(three_kind_scenarios)} passed")

    if straight_scenarios:
        straight_passed = sum(1 for r in straight_scenarios if r.passed)
        print(f"📊 STRAIGHT Scenarios: {straight_passed}/{len(straight_scenarios)} passed")

    if complex_scenarios:
        complex_passed = sum(1 for r in complex_scenarios if r.passed)
        print(f"📊 Complex Selection Scenarios: {complex_passed}/{len(complex_scenarios)} passed")

    # Check for systematic issues
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        print(f"\n❌ Failed Tests Analysis:")
        for r in failed_tests:
            print(f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result}")
            print(f"    Position: {r.scenario.position}, Starter: {r.scenario.is_starter}")
            print(f"    Previous: {r.scenario.previous_decl}")


def test_individual_multi_combo_scenarios():
    """Individual test methods for each multi-combo scenario."""
    scenarios = get_multi_combo_v2_scenarios()

    for scenario in scenarios:
        result = execute_test_scenario_v2(scenario, verbose=False)
        assert result.passed, \
            f"{scenario.scenario_id} failed: expected {scenario.expected}, got {result.actual_result} ({result.actual_result - scenario.expected:+d})"


def test_multi_combo_greedy_vs_optimal():
    """Test that V2 handles greedy vs optimal combo selection appropriately."""
    from backend.engine.piece import Piece
    from backend.engine.ai import choose_declare_strategic_v2

    # Scenario where greedy (largest first) is suboptimal
    # Hand with 4 SOLDIERs + CHARIOT/HORSE/CANNON
    # Greedy: FOUR_OF_A_KIND (4) leaves 3 pieces that can't combo
    # Optimal: STRAIGHT (3) + some soldiers
    hand = [
        Piece("SOLDIER_RED"),
        Piece("SOLDIER_RED"),
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK"),
        Piece("CHARIOT_RED"),
        Piece("HORSE_RED"),
        Piece("CANNON_RED"),
        Piece("ELEPHANT_BLACK")
    ]

    # As a starter, should be able to play combos
    result = choose_declare_strategic_v2(
        hand=hand,
        is_first_player=True,
        position_in_order=0,
        previous_declarations=[],
        must_declare_nonzero=False,
        verbose=False
    )

    # The AI might choose different valid combinations
    # Just verify it declares something reasonable
    assert result >= 3, f"Expected at least 3 pieces declared, got {result}"


def test_pile_room_multi_combo_constraint():
    """Test that multi-combo selections respect pile room constraints."""
    from backend.engine.piece import Piece
    from backend.engine.ai import choose_declare_strategic_v2

    # Hand that could play 8 pieces in combos
    hand = [
        Piece("GENERAL_RED"),
        Piece("GENERAL_BLACK"),
        Piece("ADVISOR_RED"),
        Piece("ADVISOR_BLACK"),
        Piece("CHARIOT_RED"),
        Piece("HORSE_RED"),
        Piece("CANNON_RED"),
        Piece("SOLDIER_BLACK")
    ]

    # But pile room is only 3
    result = choose_declare_strategic_v2(
        hand=hand,
        is_first_player=False,
        position_in_order=2,
        previous_declarations=[3, 2],  # Sum = 5, pile room = 3
        must_declare_nonzero=False,
        verbose=False
    )

    # Should respect pile room constraint
    assert result <= 3, f"Expected at most 3 pieces (pile room), got {result}"
    # Should at least play GENERAL as opener
    assert result >= 1, f"Expected at least 1 piece (GENERAL opener), got {result}"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_multi_combo_v2_scenarios()

    print("="*100)
    print("🎯 TESTING MULTI-COMBO V2 SCENARIOS")
    print("="*100)
    print(f"Total scenarios: {len(scenarios)}\n")

    # Run tests with verbose output
    passed = 0
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔍 Test {i}/{len(scenarios)}: {scenario.scenario_id}")
        print("="*80)
        print(f"📝 Description: {scenario.description}")
        print(f"🎯 Strategic Focus: {scenario.strategic_focus}")
        print(f"🎲 Position: {scenario.position} ({'Starter' if scenario.is_starter else 'Non-starter'})")
        print(f"📋 Previous Declarations: {scenario.previous_decl}")

        # Calculate pile room
        pile_room = 8 - sum(scenario.previous_decl) if scenario.previous_decl else 8
        print(f"📦 Pile Room: {pile_room}")

        # Parse and display hand
        hand_pieces = scenario.hand_str.strip('[]').split(', ')
        print(f"🃏 Hand ({len(hand_pieces)} pieces):")

        # Group by color
        red_pieces = [p for p in hand_pieces if '_RED' in p]
        black_pieces = [p for p in hand_pieces if '_BLACK' in p]

        if red_pieces:
            print(f"   🔴 Red: {', '.join(red_pieces)}")
        if black_pieces:
            print(f"   ⚫ Black: {', '.join(black_pieces)}")

        result = execute_test_scenario_v2(scenario, verbose=True)

        print(f"\n📊 Expected: {scenario.expected}")
        print(f"🤖 Actual: {result.actual_result}")
        if result.passed:
            print("✅ PASSED")
            passed += 1
        else:
            print(f"❌ FAILED (difference: {result.actual_result - scenario.expected:+d})")

    print("\n" + "="*100)
    print(f"🎯 MULTI-COMBO V2 SUMMARY: {passed}/{len(scenarios)} tests passed ({passed/len(scenarios)*100:.1f}%)")

    if passed == len(scenarios):
        print("✅ All multi-combo tests passed!")
    else:
        print(f"❌ {len(scenarios) - passed} tests failed - review the failures above")
