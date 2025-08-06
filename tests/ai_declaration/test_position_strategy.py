#!/usr/bin/env python3
"""
Position Strategy AI Declaration Tests - 12 Scenarios

This module tests how the AI adapts its declaration strategy based on position
in the turn order. Position fundamentally affects control mechanisms and
strategic opportunities.

Test Focus:
- Starter advantages and control mechanisms
- Non-starter adaptation to position constraints
- Last player constraint handling (sum≠8 rule)
- Position-dependent combo viability
- Strategic timing considerations

Total Tests: 12 scenarios (4 starter + 4 non-starter + 4 last player)
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_position_strategy_scenarios():
    """Get all position strategy test scenarios."""
    scenarios = []
    
    # ========================================================================
    # Starter Advantage Scenarios (4 tests)
    # ========================================================================
    starter_scenarios = [
        ("pos_starter_01", "[CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 1, "Starter Enables Weak Straight", True, "Starter makes weak combo viable", DifficultyLevel.BASIC,
         "18-point straight becomes playable as starter"),
        
        ("pos_starter_02", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_BLACK]",
         0, [], 1, "Starter with Multiple Pairs", True, "Multiple small combos as starter", DifficultyLevel.INTERMEDIATE,
         "Two pairs (4 piles total) only viable as starter"),
        
        ("pos_starter_03", "[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED]",
         0, [], 7, "Starter: Opener + Combo", True, "Optimal opener-combo combination", DifficultyLevel.BASIC,
         "GENERAL (1) + THREE_OF_A_KIND (3) = 4 piles guaranteed"),
        
        ("pos_starter_04", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         0, [], 6, "Starter with Medium Singles", True, "Starter advantage with borderline pieces", DifficultyLevel.INTERMEDIATE,
         "ELEPHANTs might win as starter, others too weak")
    ]
    
    for scenario_data in starter_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.POSITION_STRATEGY,
            subcategory="starter_advantage",
            hand_str=hand_str,
            position=position,
            previous_decl=prev_decl,
            expected=expected,
            description=description,
            is_starter=is_starter,
            strategic_focus=focus,
            difficulty_level=difficulty,
            notes=notes
        ))
    
    # ========================================================================
    # Non-Starter Adaptation Scenarios (4 tests)
    # ========================================================================
    non_starter_scenarios = [
        ("pos_nonstarter_01", "[CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         2, [2, 3], 0, "Same Weak Straight, No Control", False, "Non-starter makes combo unviable", DifficultyLevel.BASIC,
         "Same hand as pos_starter_01, but non-starter = no combo opportunity"),
        
        ("pos_nonstarter_02", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_BLACK]",
         1, [4], 0, "Pairs Without Control", False, "Multiple combos need control", DifficultyLevel.INTERMEDIATE,
         "Strong opponent (4) will control - pairs become unplayable"),
        
        ("pos_nonstarter_03", "[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED]",
         2, [2, 3], 3, "Non-starter: Opener Only", False, "Combo unviable without control", DifficultyLevel.INTERMEDIATE,
         "GENERAL reliable (1), but THREE_OF_A_KIND needs opportunity"),
        
        ("pos_nonstarter_04", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         1, [3], 0, "Medium Singles, No Control", False, "Non-starter with medium pieces", DifficultyLevel.BASIC,
         "Same hand as pos_starter_04, but opponent controls = 0 piles")
    ]
    
    for scenario_data in non_starter_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.POSITION_STRATEGY,
            subcategory="non_starter_adaptation",
            hand_str=hand_str,
            position=position,
            previous_decl=prev_decl,
            expected=expected,
            description=description,
            is_starter=is_starter,
            strategic_focus=focus,
            difficulty_level=difficulty,
            notes=notes
        ))
    
    # ========================================================================
    # Last Player Constraint Scenarios (4 tests)
    # ========================================================================
    last_player_scenarios = [
        ("pos_last_01", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         3, [3, 2, 1], 1, "Last Player: Forced High Declaration", False, "Cannot declare 2, forced to 3", DifficultyLevel.ADVANCED,
         "Wants 2 piles, but 6+2=8 forbidden, must declare 3"),
        
        ("pos_last_02", "[SOLDIER_RED, SOLDIER_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         3, [2, 3, 2], 0, "Last Player: Forced Zero", False, "Cannot declare 1, only 0 viable", DifficultyLevel.BASIC,
         "Wants 1 pile, but 7+1=8 forbidden, forced to 0"),
        
        ("pos_last_03", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [1, 1, 4], 1, "Last Player: Multiple Constraints", False, "2 works, but close to constraint", DifficultyLevel.ADVANCED,
         "Could declare 2 (6+2≠8), good match for hand strength"),
        
        ("pos_last_04", "[ADVISOR_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         3, [4, 3, 0], 0, "Last Player: Conservative Choice", False, "Under-declare due to constraint pressure", DifficultyLevel.INTERMEDIATE,
         "Could declare 1 (7+1≠8), but complex constraint environment")
    ]
    
    for scenario_data in last_player_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.POSITION_STRATEGY,
            subcategory="last_player_constraints",
            hand_str=hand_str,
            position=position,
            previous_decl=prev_decl,
            expected=expected,
            description=description,
            is_starter=is_starter,
            strategic_focus=focus,
            difficulty_level=difficulty,
            notes=notes
        ))
    
    return scenarios


def test_position_strategy_scenarios(verbose_output, enable_ai_analysis):
    """Test all position strategy scenarios."""
    scenarios = get_position_strategy_scenarios()
    
    results = run_category_tests(
        scenarios=scenarios,
        category_name="POSITION_STRATEGY",
        verbose=verbose_output,
        enable_analysis=enable_ai_analysis
    )
    
    # Validate key strategic patterns
    starter_results = [r for r in results if r.scenario.subcategory == "starter_advantage"]
    non_starter_results = [r for r in results if r.scenario.subcategory == "non_starter_adaptation"]
    last_player_results = [r for r in results if r.scenario.subcategory == "last_player_constraints"]
    
    # All starter scenarios should show advantage over non-starter equivalents
    starter_passed = sum(1 for r in starter_results if r.passed)
    assert starter_passed >= 3, f"Most starter scenarios should pass: {starter_passed}/4"
    
    # Non-starter scenarios should show position adaptation
    non_starter_passed = sum(1 for r in non_starter_results if r.passed)
    assert non_starter_passed >= 3, f"Most non-starter scenarios should pass: {non_starter_passed}/4"
    
    # Last player scenarios test constraint handling
    last_player_passed = sum(1 for r in last_player_results if r.passed)
    assert last_player_passed >= 3, f"Most last player scenarios should pass: {last_player_passed}/4"
    
    # Report any failures for analysis
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id} ({r.scenario.subcategory}): Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        print(f"Position strategy test failures:\n{failure_summary}")


def test_starter_vs_non_starter_comparison():
    """Test that identical hands show position-based differences."""
    scenarios = get_position_strategy_scenarios()
    
    # Compare pos_starter_01 vs pos_nonstarter_01 (same hand, different positions)
    starter_result = next((r for r in scenarios if r.scenario_id == "pos_starter_01"), None)
    non_starter_result = next((r for r in scenarios if r.scenario_id == "pos_nonstarter_01"), None)
    
    assert starter_result is not None and non_starter_result is not None
    
    # Execute both scenarios
    starter_test = execute_test_scenario(starter_result, verbose=False)
    non_starter_test = execute_test_scenario(non_starter_result, verbose=False)
    
    # Starter should declare more than non-starter for same hand
    assert starter_test.actual_result >= non_starter_test.actual_result, \
        f"Starter advantage failed: starter got {starter_test.actual_result}, non-starter got {non_starter_test.actual_result}"


def test_last_player_constraint_compliance():
    """Test that last player scenarios properly handle sum≠8 constraint."""
    scenarios = get_position_strategy_scenarios()
    last_player_scenarios = [s for s in scenarios if s.subcategory == "last_player_constraints"]
    
    for scenario in last_player_scenarios:
        result = execute_test_scenario(scenario, verbose=False)
        
        # Calculate what sum would be with AI's decision
        total_sum = sum(scenario.previous_decl) + result.actual_result
        
        # Sum should never equal 8 (forbidden for last player)
        assert total_sum != 8, \
            f"Last player constraint violation in {scenario.scenario_id}: sum={total_sum} (forbidden)"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_position_strategy_scenarios()
    results = run_category_tests(scenarios, "POSITION_STRATEGY", verbose=True, enable_analysis=False)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n🎯 POSITION STRATEGY SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    # Category breakdown
    categories = {}
    for result in results:
        cat = result.scenario.subcategory
        if cat not in categories:
            categories[cat] = {'passed': 0, 'total': 0}
        categories[cat]['total'] += 1
        if result.passed:
            categories[cat]['passed'] += 1
    
    print("\n📊 Subcategory Breakdown:")
    for cat, stats in categories.items():
        rate = stats['passed'] / stats['total'] * 100
        print(f"  • {cat}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
    
    if passed < total:
        failed = [r for r in results if not r.passed]
        print("\n❌ Failed tests:")
        for r in failed:
            diff = r.actual_result - r.scenario.expected
            print(f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d})")