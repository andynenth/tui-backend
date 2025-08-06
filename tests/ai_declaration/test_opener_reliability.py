#!/usr/bin/env python3
"""
Opener Reliability AI Declaration Tests - 15 Scenarios

This module tests the AI's assessment of opener reliability across different
field strengths and piece values. Openers are the foundation of viable
declarations, providing the control needed to play pieces reliably.

Test Focus:
- Strong opener reliability (GENERAL 13-14pts, ADVISOR 11-12pts)
- Marginal opener assessment (ELEPHANT 9-10pts in weak fields)
- No opener scenarios (best available piece strategies)
- Field strength impact on opener effectiveness
- Opener vs combo strategic tradeoffs

Total Tests: 15 scenarios (5 strong + 5 marginal + 5 no opener)
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_opener_reliability_scenarios():
    """Get all opener reliability test scenarios."""
    scenarios = []
    
    # ========================================================================
    # Strong Openers Scenarios (5 tests)
    # ========================================================================
    strong_opener_scenarios = [
        ("opener_strong_01", "[GENERAL_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         2, [2, 1], 2, "GENERAL_RED in Normal Field", False, "GENERAL_RED most reliable opener", DifficultyLevel.BASIC,
         "GENERAL_RED (14pts) reliable in any field, 1.0 opener score"),
        
        ("opener_strong_02", "[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_RED, ELEPHANT_RED]",
         1, [0], 4, "GENERAL_BLACK + Combo in Weak Field", False, "GENERAL enables combo in weak field", DifficultyLevel.INTERMEDIATE,
         "GENERAL_BLACK (13pts) + weak field = very reliable, enables THREE_OF_A_KIND"),
        
        ("opener_strong_03", "[ADVISOR_RED, ADVISOR_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_BLACK]",
         0, [], 2, "Double ADVISOR (Starter)", True, "Multiple strong openers", DifficultyLevel.BASIC,
         "ADVISOR_RED (12pts) + ADVISOR_BLACK (11pts) = 2 strong openers as starter"),
        
        ("opener_strong_04", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         1, [3], 1, "ADVISOR vs Strong Field", False, "ADVISOR reliability vs strong opponents", DifficultyLevel.INTERMEDIATE,
         "ADVISOR_RED (12pts) still reliable vs strong field, reduced to 0.85 score"),
        
        ("opener_strong_05", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         3, [2, 1, 3], 1, "GENERAL_RED Last Player", False, "Strong opener constrained by position", DifficultyLevel.ADVANCED,
         "GENERAL_RED reliable but last player constraint (6+2=8 forbidden)")
    ]
    
    for scenario_data in strong_opener_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.OPENER_RELIABILITY,
            subcategory="strong_openers",
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
    # Marginal Openers Scenarios (5 tests)
    # ========================================================================
    marginal_opener_scenarios = [
        ("opener_marginal_01", "[ELEPHANT_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         2, [0, 1], 2, "ELEPHANT in Weak Field", False, "10-point piece becomes opener in weak field", DifficultyLevel.INTERMEDIATE,
         "ELEPHANT_RED (10pts) not normally opener, but weak field makes it viable"),
        
        ("opener_marginal_02", "[ELEPHANT_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ADVISOR_BLACK, SOLDIER_BLACK]",
         1, [3], 0, "ELEPHANT vs Strong Field", False, "Marginal opener fails vs strong opponents", DifficultyLevel.BASIC,
         "ELEPHANT_BLACK (9pts) unreliable vs strong field, choose safer 0"),
        
        ("opener_marginal_03", "[CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 1, "CHARIOT as Best Piece (Starter)", True, "Marginal opener with starter advantage", DifficultyLevel.INTERMEDIATE,
         "CHARIOT_RED (8pts) not real opener but best piece + starter = 1 pile possible"),
        
        ("opener_marginal_04", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         2, [1, 2], 1, "Multiple Marginal Pieces", False, "Best of marginal pieces", DifficultyLevel.BASIC,
         "ELEPHANT_RED (10pts) best of marginal pieces, normal field = marginally viable"),
        
        ("opener_marginal_05", "[HORSE_RED, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, CHARIOT_BLACK, ELEPHANT_BLACK, ADVISOR_BLACK]",
         3, [0, 0, 1], 2, "ADVISOR_BLACK in Very Weak Field", False, "Strong opener in weak field = highly reliable", DifficultyLevel.ADVANCED,
         "ADVISOR_BLACK (11pts) strong opener + very weak field [0,0,1] = very reliable, expect 2")
    ]
    
    for scenario_data in marginal_opener_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.OPENER_RELIABILITY,
            subcategory="marginal_openers",
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
    # No Opener Scenarios (5 tests)
    # ========================================================================
    no_opener_scenarios = [
        ("opener_none_01", "[CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_BLACK]",
         2, [2, 3], 0, "No Opener vs Normal Field", False, "No reliable pieces vs normal opponents", DifficultyLevel.BASIC,
         "Best piece CHARIOT_RED (8pts), not opener strength, normal field = 0 piles"),
        
        ("opener_none_02", "[HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, ELEPHANT_RED, CHARIOT_BLACK, ELEPHANT_BLACK]",
         3, [0, 0, 1], 2, "No Opener vs Very Weak Field", False, "Weak field enables medium pieces", DifficultyLevel.INTERMEDIATE,
         "No opener but [0,0,1] very weak field makes medium pieces viable"),
        
        ("opener_none_03", "[CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, HORSE_BLACK, ELEPHANT_RED, CHARIOT_BLACK, ELEPHANT_BLACK, HORSE_RED]",
         0, [], 1, "No Opener but Starter", True, "Starter advantage with weak pieces", DifficultyLevel.BASIC,
         "No opener but starter can lead with best piece, might win 1"),
        
        ("opener_none_04", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         1, [4], 0, "Combos Need Opener", False, "Great combo, no opener, strong opponent", DifficultyLevel.ADVANCED,
         "THREE_OF_A_KIND + STRAIGHT but no opener + strong opponent (4) = 0 opportunity"),
        
        ("opener_none_05", "[HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK]",
         2, [1, 1], 1, "No Opener, Weak-Normal Field", False, "Borderline field with no opener", DifficultyLevel.INTERMEDIATE,
         "Weak field [1,1] makes ELEPHANT_RED (10pts) marginally viable")
    ]
    
    for scenario_data in no_opener_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.OPENER_RELIABILITY,
            subcategory="no_opener_scenarios",
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


def test_opener_reliability_scenarios(verbose_output, enable_ai_analysis):
    """Test all opener reliability scenarios."""
    scenarios = get_opener_reliability_scenarios()
    
    results = run_category_tests(
        scenarios=scenarios,
        category_name="OPENER_RELIABILITY",
        verbose=verbose_output,
        enable_analysis=enable_ai_analysis
    )
    
    # Validate opener reliability patterns
    strong_results = [r for r in results if r.scenario.subcategory == "strong_openers"]
    marginal_results = [r for r in results if r.scenario.subcategory == "marginal_openers"]
    no_opener_results = [r for r in results if r.scenario.subcategory == "no_opener_scenarios"]
    
    # Strong opener scenarios should show consistent reliability
    strong_passed = sum(1 for r in strong_results if r.passed)
    assert strong_passed >= 4, f"Most strong opener scenarios should pass: {strong_passed}/5"
    
    # Marginal opener scenarios test field strength sensitivity
    marginal_passed = sum(1 for r in marginal_results if r.passed)
    assert marginal_passed >= 3, f"Most marginal opener scenarios should pass: {marginal_passed}/5"
    
    # No opener scenarios test alternative strategies
    no_opener_passed = sum(1 for r in no_opener_results if r.passed)
    assert no_opener_passed >= 3, f"Most no opener scenarios should pass: {no_opener_passed}/5"
    
    # Report any failures for analysis
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id} ({r.scenario.subcategory}): Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        print(f"Opener reliability test failures:\n{failure_summary}")


def test_opener_strength_classification():
    """Test that opener strength is properly classified by piece points."""
    scenarios = get_opener_reliability_scenarios()
    
    # Find scenarios with known opener classifications
    general_scenario = next((s for s in scenarios if s.scenario_id == "opener_strong_01"), None)
    elephant_scenario = next((s for s in scenarios if s.scenario_id == "opener_marginal_01"), None)
    no_opener_scenario = next((s for s in scenarios if s.scenario_id == "opener_none_01"), None)
    
    assert all(s is not None for s in [general_scenario, elephant_scenario, no_opener_scenario])
    
    # Execute scenarios
    general_result = execute_test_scenario(general_scenario, verbose=False)
    elephant_result = execute_test_scenario(elephant_scenario, verbose=False)
    no_opener_result = execute_test_scenario(no_opener_scenario, verbose=False)
    
    # Strong openers should generally outperform weaker alternatives
    assert general_result.actual_result >= elephant_result.actual_result, \
        f"Strong opener underperformed: GENERAL got {general_result.actual_result}, ELEPHANT got {elephant_result.actual_result}"


def test_field_strength_opener_interaction():
    """Test that field strength affects opener reliability appropriately."""
    scenarios = get_opener_reliability_scenarios()
    
    # Find weak vs strong field scenarios with similar openers
    weak_field = next((s for s in scenarios if s.scenario_id == "opener_marginal_05"), None)  # Very weak field
    strong_field = next((s for s in scenarios if s.scenario_id == "opener_marginal_02"), None)  # Strong field
    
    assert weak_field is not None and strong_field is not None
    
    # Execute both scenarios
    weak_result = execute_test_scenario(weak_field, verbose=False)
    strong_result = execute_test_scenario(strong_field, verbose=False)
    
    # Weak field should enable more aggressive declarations
    assert weak_result.actual_result >= strong_result.actual_result, \
        f"Field strength effect failed: weak field got {weak_result.actual_result}, strong field got {strong_result.actual_result}"


def test_no_opener_fallback_strategies():
    """Test that no-opener scenarios use appropriate fallback strategies."""
    scenarios = get_opener_reliability_scenarios()
    no_opener_scenarios = [s for s in scenarios if s.subcategory == "no_opener_scenarios"]
    
    for scenario in no_opener_scenarios:
        result = execute_test_scenario(scenario, verbose=False)
        
        # No opener scenarios should generally be conservative
        assert result.actual_result >= 0, \
            f"Invalid declaration in no-opener scenario {scenario.scenario_id}: {result.actual_result}"
        
        # Should not declare more than 2 without reliable opener (except starter in very weak field)
        if not scenario.is_starter:
            field_strength = sum(scenario.previous_decl) / len(scenario.previous_decl) if scenario.previous_decl else 2.0
            if field_strength > 1.0:  # Not very weak field
                assert result.actual_result <= 2, \
                    f"Over-aggressive no-opener declaration in {scenario.scenario_id}: {result.actual_result}"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_opener_reliability_scenarios()
    results = run_category_tests(scenarios, "OPENER_RELIABILITY", verbose=True, enable_analysis=False)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n🎯 OPENER RELIABILITY SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
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
    
    # Analyze opener strength vs declarations
    strong_openers = [r for r in results if r.scenario.subcategory == "strong_openers"]
    marginal_openers = [r for r in results if r.scenario.subcategory == "marginal_openers"]
    no_openers = [r for r in results if r.scenario.subcategory == "no_opener_scenarios"]
    
    if strong_openers:
        avg_strong = sum(r.actual_result for r in strong_openers) / len(strong_openers)
        print(f"  • Average strong opener declarations: {avg_strong:.1f}")
    
    if marginal_openers:
        avg_marginal = sum(r.actual_result for r in marginal_openers) / len(marginal_openers)
        print(f"  • Average marginal opener declarations: {avg_marginal:.1f}")
    
    if no_openers:
        avg_no_opener = sum(r.actual_result for r in no_openers) / len(no_openers)
        print(f"  • Average no-opener declarations: {avg_no_opener:.1f}")
    
    # Analyze field strength impact
    field_adaptations = []
    for result in results:
        if result.scenario.previous_decl:
            field_avg = sum(result.scenario.previous_decl) / len(result.scenario.previous_decl)
            field_adaptations.append((field_avg, result.actual_result))
    
    if field_adaptations:
        weak_field_results = [decl for field_avg, decl in field_adaptations if field_avg <= 1.0]
        strong_field_results = [decl for field_avg, decl in field_adaptations if field_avg >= 3.5]
        
        if weak_field_results and strong_field_results:
            avg_weak = sum(weak_field_results) / len(weak_field_results)
            avg_strong = sum(strong_field_results) / len(strong_field_results)
            print(f"  • Field strength adaptation: weak={avg_weak:.1f}, strong={avg_strong:.1f}")
    
    if passed < total:
        failed = [r for r in results if not r.passed]
        print("\n❌ Failed tests:")
        for r in failed:
            diff = r.actual_result - r.scenario.expected
            print(f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d})")