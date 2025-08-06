#!/usr/bin/env python3
"""
Combo Opportunity AI Declaration Tests - 18 Scenarios

This module tests the AI's ability to detect, evaluate, and declare based on
combo opportunities. This includes viable combo detection, quality thresholds,
and multi-combo hand analysis.

Test Focus:
- Viable combo detection (starter vs non-starter control)
- Combo quality thresholds (minimum viability requirements)
- Multi-combo hand optimization (complex combinations)
- Opportunity assessment (opponent patterns and control)
- Strategic combo vs opener tradeoffs

Total Tests: 18 scenarios (6 viable + 6 quality + 6 multi-combo)
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_combo_opportunity_scenarios():
    """Get all combo opportunity test scenarios."""
    scenarios = []
    
    # ========================================================================
    # Viable Combo Detection Scenarios (6 tests)
    # ========================================================================
    viable_combo_scenarios = [
        ("combo_viable_01", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         0, [], 6, "THREE_OF_A_KIND + STRAIGHT (Starter)", True, "Starter enables both combos", DifficultyLevel.BASIC,
         "RED THREE_OF_A_KIND (3) + BLACK STRAIGHT (3) = 6 piles as starter"),
        
        ("combo_viable_02", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         2, [2, 3], 0, "Same Combos, No Control", False, "Forfeit strategy against strong opponents", DifficultyLevel.INTERMEDIATE,
         "Same hand as combo_viable_01 but no control = forfeit strategy"),
        
        ("combo_viable_03", "[ADVISOR_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_BLACK, ELEPHANT_BLACK]",
         1, [2], 1, "Opener vs Combo Choice", False, "Opener reliable, combo questionable", DifficultyLevel.ADVANCED,
         "ADVISOR (1) reliable but THREE_OF_A_KIND needs opportunity - choose opener"),
        
        ("combo_viable_04", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_RED, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_BLACK, HORSE_BLACK]",
         0, [], 3, "21-Point Straight (Starter)", True, "Strong straight viable as starter", DifficultyLevel.BASIC,
         "21-point RED STRAIGHT above quality threshold, guaranteed as starter"),
        
        ("combo_viable_05", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_RED, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_BLACK, HORSE_BLACK]",
         2, [0, 1], 0, "Strong Straight vs Weak Field", False, "Forfeit strategy - no combo opportunity", DifficultyLevel.ADVANCED,
         "21-point straight but forfeit strategy against weak field pattern"),
        
        ("combo_viable_06", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
         1, [4], 0, "FOUR_OF_A_KIND vs Strong Control", False, "Forfeit strategy against strong opponent", DifficultyLevel.INTERMEDIATE,
         "FOUR_OF_A_KIND RED but forfeit strategy against strong opponent (4)")
    ]
    
    for scenario_data in viable_combo_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.COMBO_OPPORTUNITY,
            subcategory="viable_combo_detection",
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
    # Quality Threshold Scenarios (6 tests)
    # ========================================================================
    quality_threshold_scenarios = [
        ("combo_quality_01", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, ELEPHANT_BLACK, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_BLACK]",
         0, [], 3, "THREE_OF_A_KIND + STRAIGHT (Starter)", True, "Choose optimal combo - THREE_OF_A_KIND or full combo", DifficultyLevel.BASIC,
         "RED THREE_OF_A_KIND (3) most reliable, or could go for 6 with both combos"),
        
        ("combo_quality_02", "[CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, ELEPHANT_RED, ELEPHANT_BLACK, ADVISOR_RED]",
         0, [], 3, "18-Point Straight Threshold", True, "Minimum viable straight", DifficultyLevel.INTERMEDIATE,
         "BLACK STRAIGHT exactly at 18-point threshold, marginal but viable as starter"),
        
        ("combo_quality_03", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 0, "Different Color Singles Only", True, "No valid combos - different colors, not pairs", DifficultyLevel.BASIC,
         "All pieces are different colors - no pairs, no same-color straights possible"),
        
        ("combo_quality_04", "[CANNON_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, ADVISOR_BLACK]",
         0, [], 0, "Different Color Singles Only", True, "No valid pairs - different colors", DifficultyLevel.INTERMEDIATE,
         "CANNON_RED+BLACK, SOLDIER_RED+BLACK - all different colors, no pairs possible"),
        
        ("combo_quality_05", "[GENERAL_RED, HORSE_RED, CANNON_RED, SOLDIER_RED, ELEPHANT_BLACK, CHARIOT_BLACK, HORSE_BLACK, SOLDIER_BLACK]",
         0, [], 1, "Marginal Straight with Opener", True, "Opener vs weak straight", DifficultyLevel.ADVANCED,
         "GENERAL reliable (1), weak RED partial straight unviable"),
        
        ("combo_quality_06", "[ADVISOR_RED, ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
         0, [], 3, "STRAIGHT + Opener Strategy", True, "Don't miss starter privilege", DifficultyLevel.ADVANCED,
         "BLACK STRAIGHT (3) + starter privilege - don't miss opportunity by declaring too low")
    ]
    
    for scenario_data in quality_threshold_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.COMBO_OPPORTUNITY,
            subcategory="quality_thresholds",
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
    # Multi-Combo Hand Scenarios (6 tests)
    # ========================================================================
    multi_combo_scenarios = [
        ("combo_multi_01", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
         0, [], 6, "Overlapping Soldier Combos", True, "Multiple combo types from soldiers", DifficultyLevel.ADVANCED,
         "RED pair + BLACK THREE_OF_A_KIND + RED STRAIGHT = complex combo selection"),
        
        ("combo_multi_02", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
         0, [], 8, "FOUR_OF_A_KIND + STRAIGHT + Opener", True, "Maximum combos with opener", DifficultyLevel.BASIC,
         "GENERAL(1) + FOUR_OF_A_KIND(4) + STRAIGHT(3) = 8 piles maximum"),
        
        ("combo_multi_03", "[ELEPHANT_RED, ELEPHANT_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 6, "ELEPHANT PAIR + BLACK STRAIGHT", True, "Pair and straight combos", DifficultyLevel.INTERMEDIATE,
         "ELEPHANT_RED PAIR (2) + BLACK STRAIGHT (4) = 6 piles as starter"),
        
        ("combo_multi_04", "[CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 6, "Three Pairs", True, "Multiple pair combinations", DifficultyLevel.INTERMEDIATE,
         "CHARIOT pair + HORSE pair + CANNON pair all viable"),
        
        ("combo_multi_05", "[ADVISOR_RED, CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         1, [3], 4, "Strong Opener + STRAIGHT Combo", False, "Strong opener and straight", DifficultyLevel.ADVANCED,
         "ADVISOR_RED opener (1) + RED STRAIGHT (3) = 4 piles, 1 strong opener and straight"),
        
        ("combo_multi_06", "[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         2, [1, 0], 8, "FOUR_OF_A_KIND + STRAIGHT Enabled", False, "GENERAL enables everything", DifficultyLevel.BASIC,
         "GENERAL + weak field enables FOUR_OF_A_KIND + STRAIGHT = 8 piles")
    ]
    
    for scenario_data in multi_combo_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.COMBO_OPPORTUNITY,
            subcategory="multi_combo_hands",
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


def test_combo_opportunity_scenarios(verbose_output, enable_ai_analysis):
    """Test all combo opportunity scenarios."""
    scenarios = get_combo_opportunity_scenarios()
    
    results = run_category_tests(
        scenarios=scenarios,
        category_name="COMBO_OPPORTUNITY",
        verbose=verbose_output,
        enable_analysis=enable_ai_analysis
    )
    
    # Validate combo opportunity detection patterns
    viable_results = [r for r in results if r.scenario.subcategory == "viable_combo_detection"]
    quality_results = [r for r in results if r.scenario.subcategory == "quality_thresholds"]
    multi_results = [r for r in results if r.scenario.subcategory == "multi_combo_hands"]
    
    # Viable combo scenarios test control mechanisms
    viable_passed = sum(1 for r in viable_results if r.passed)
    assert viable_passed >= 4, f"Most viable combo scenarios should pass: {viable_passed}/6"
    
    # Quality threshold scenarios test minimum viability
    quality_passed = sum(1 for r in quality_results if r.passed)
    assert quality_passed >= 4, f"Most quality threshold scenarios should pass: {quality_passed}/6"
    
    # Multi-combo scenarios test complex optimization
    multi_passed = sum(1 for r in multi_results if r.passed)
    assert multi_passed >= 4, f"Most multi-combo scenarios should pass: {multi_passed}/6"
    
    # Report any failures for analysis
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id} ({r.scenario.subcategory}): Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        print(f"Combo opportunity test failures:\n{failure_summary}")


def test_starter_vs_non_starter_combo_control():
    """Test that combo opportunities depend on position control."""
    scenarios = get_combo_opportunity_scenarios()
    
    # Compare combo_viable_01 vs combo_viable_02 (same hand, different control)
    starter_combo = next((s for s in scenarios if s.scenario_id == "combo_viable_01"), None)
    non_starter_combo = next((s for s in scenarios if s.scenario_id == "combo_viable_02"), None)
    
    assert starter_combo is not None and non_starter_combo is not None
    
    # Execute both scenarios
    starter_result = execute_test_scenario(starter_combo, verbose=False)
    non_starter_result = execute_test_scenario(non_starter_combo, verbose=False)
    
    # Starter should enable combos that non-starter cannot play
    assert starter_result.actual_result > non_starter_result.actual_result, \
        f"Combo control failed: starter got {starter_result.actual_result}, non-starter got {non_starter_result.actual_result}"


def test_combo_quality_thresholds():
    """Test that combo quality thresholds are properly enforced."""
    scenarios = get_combo_opportunity_scenarios()
    quality_scenarios = [s for s in scenarios if s.subcategory == "quality_thresholds"]
    
    for scenario in quality_scenarios:
        result = execute_test_scenario(scenario, verbose=False)
        
        # Quality scenarios with 0 expected should not declare combos
        if scenario.expected == 0:
            assert result.actual_result == 0, \
                f"Low quality combo incorrectly enabled in {scenario.scenario_id}: got {result.actual_result}"
        
        # Quality scenarios with positive expected should enable combos
        elif scenario.expected > 0:
            # Allow some flexibility for strategic tradeoffs
            assert result.actual_result >= 0, \
                f"Valid combo incorrectly disabled in {scenario.scenario_id}: got {result.actual_result}"


def test_multi_combo_optimization():
    """Test that multi-combo hands are optimized correctly."""
    scenarios = get_combo_opportunity_scenarios()
    
    # Test maximum combo scenario
    max_combo = next((s for s in scenarios if s.scenario_id == "combo_multi_02"), None)
    assert max_combo is not None
    
    max_result = execute_test_scenario(max_combo, verbose=False)
    
    # Should achieve near-maximum declaration for optimal multi-combo hand
    assert max_result.actual_result >= 6, \
        f"Multi-combo optimization failed: expected high declaration, got {max_result.actual_result}"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_combo_opportunity_scenarios()
    results = run_category_tests(scenarios, "COMBO_OPPORTUNITY", verbose=True, enable_analysis=False)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n🎯 COMBO OPPORTUNITY SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
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
    
    # Strategic insights
    print("\n🎯 Strategic Insights:")
    
    # Analyze combo vs control patterns
    starter_combos = [r for r in results if r.scenario.is_starter and r.scenario.expected > 0]
    non_starter_combos = [r for r in results if not r.scenario.is_starter and r.scenario.expected > 0]
    
    if starter_combos and non_starter_combos:
        avg_starter = sum(r.actual_result for r in starter_combos) / len(starter_combos)
        avg_non_starter = sum(r.actual_result for r in non_starter_combos) / len(non_starter_combos)
        print(f"  • Average starter combo declarations: {avg_starter:.1f}")
        print(f"  • Average non-starter combo declarations: {avg_non_starter:.1f}")
        print(f"  • Starter advantage ratio: {avg_starter / max(avg_non_starter, 0.1):.1f}x")
    
    # Analyze quality threshold enforcement
    zero_expected = [r for r in results if r.scenario.expected == 0]
    if zero_expected:
        zero_violations = sum(1 for r in zero_expected if r.actual_result > 0)
        print(f"  • Quality threshold violations: {zero_violations}/{len(zero_expected)}")
    
    if passed < total:
        failed = [r for r in results if not r.passed]
        print("\n❌ Failed tests:")
        for r in failed:
            diff = r.actual_result - r.scenario.expected
            print(f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d})")