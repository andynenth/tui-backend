#!/usr/bin/env python3
"""
Field Strength AI Declaration Tests - 15 Scenarios

This module tests how the AI adapts its declaration strategy based on the
strength assessment of opponents' previous declarations. Field strength
fundamentally affects piece viability and combo opportunities.

Test Focus:
- Weak field exploitation (medium pieces become viable)
- Strong field caution (aggressive declarations fail)
- Mixed/borderline field assessment
- Field strength impact on combo thresholds
- Strategic adaptation to opponent strength patterns

Total Tests: 15 scenarios (5 weak + 5 strong + 5 mixed)
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_field_strength_scenarios():
    """Get all field strength test scenarios."""
    scenarios = []
    
    # ========================================================================
    # Weak Field Exploitation Scenarios (5 tests) 
    # ========================================================================
    weak_field_scenarios = [
        ("field_weak_01", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         2, [0, 0], 0, "Medium Pieces vs Very Weak Field", False, "Information asymmetry risk", DifficultyLevel.BASIC,
         "Previous [0,0] = P1&P2 very weak, P4 could have monster hand - forfeit strategy"),
        
        ("field_weak_02", "[ADVISOR_RED, CHARIOT_RED, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         1, [1], 1, "Opener in Weak Field", False, "Opener reliable, rest are junk", DifficultyLevel.INTERMEDIATE,
         "ADVISOR reliable but rest of hand are junk pieces"),
        
        ("field_weak_03", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [0, 1, 0], 0, "Weak Combo in Weak Field", False, "Information asymmetry risk", DifficultyLevel.ADVANCED,
         "Same reason as field_weak_01 - P4 could have concentrated strength"),
        
        ("field_weak_04", "[GENERAL_BLACK, CHARIOT_RED, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         2, [0, 1], 1, "Strong Opener vs Weak Field", False, "Opener reliable, rest are junk", DifficultyLevel.BASIC,
         "GENERAL reliable but rest of hand are junk pieces"),
        
        ("field_weak_05", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_RED, ELEPHANT_BLACK]",
         1, [0], 1, "Multiple Medium vs Weak", False, "No opener, ELEPHANTs might capture some", DifficultyLevel.INTERMEDIATE,
         "No opener but ELEPHANT_RED/BLACK could capture some turns with singles")
    ]
    
    for scenario_data in weak_field_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.FIELD_STRENGTH,
            subcategory="weak_field_exploitation",
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
    # Strong Field Caution Scenarios (5 tests)
    # ========================================================================
    strong_field_scenarios = [
        ("field_strong_01", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [4, 5], 0, "Good Hand vs Strong Field", False, "Strong field + pile room = zero", DifficultyLevel.BASIC,
         "Same hand that works elsewhere fails due to strong opponents + no room"),
        
        ("field_strong_02", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         1, [5], 1, "Even GENERAL Cautious vs Strong", False, "Strong field reduces GENERAL reliability", DifficultyLevel.INTERMEDIATE,
         "GENERAL still reliable but field strength affects combo opportunities"),
        
        ("field_strong_03", "[CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_BLACK]",
         2, [3, 4], 0, "18-Point Straight vs Strong Field", False, "Weak combo unviable vs strong opponents", DifficultyLevel.ADVANCED,
         "18-point straight completely unviable - strong opponents will have better"),
        
        ("field_strong_04", "[ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_RED, ELEPHANT_RED]",
         3, [4, 3, 2], 0, "Opener + Combo vs Strong Field", False, "Strong field blocks combo opportunity", DifficultyLevel.INTERMEDIATE,
         "ADVISOR reliable but THREE_OF_A_KIND needs opportunity - strong field prevents"),
        
        ("field_strong_05", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         1, [6], 0, "Medium Pieces vs Strong Field", False, "Strong field makes medium pieces worthless", DifficultyLevel.BASIC,
         "Same pieces that work in weak field become completely unviable vs strong opponents")
    ]
    
    for scenario_data in strong_field_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.FIELD_STRENGTH,
            subcategory="strong_field_caution",
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
    # Mixed/Borderline Field Scenarios (5 tests)
    # ========================================================================
    mixed_field_scenarios = [
        ("field_mixed_01", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         2, [1, 3], 1, "Mixed Field: Weak + Strong", False, "Mixed signals complicate assessment", DifficultyLevel.ADVANCED,
         "One weak (1), one strong (3) opponent - field assessment unclear"),
        
        ("field_mixed_02", "[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_RED, ELEPHANT_RED, ELEPHANT_BLACK]",
         1, [2], 1, "Borderline Normal Field", False, "Opener reliable, ELEPHANTs not reliable", DifficultyLevel.INTERMEDIATE,
         "GENERAL reliable but ELEPHANT pieces not reliable in normal field"),
        
        ("field_mixed_03", "[CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_BLACK]",
         3, [2, 2, 2], 0, "Consistent Normal Field", False, "ELEPHANTs not reliable in normal field", DifficultyLevel.BASIC,
         "ELEPHANT pieces could capture some but not reliable in normal field"),
        
        ("field_mixed_04", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         2, [0, 4], 0, "Extreme Mixed Field", False, "Forfeit strategy against strong P2", DifficultyLevel.ADVANCED,
         "P2 very strong - use forfeit strategy to remove ELEPHANT pieces"),
        
        ("field_mixed_05", "[ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_RED, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED]",
         1, [3], 1, "Single Strong Opponent", False, "One strong opponent affects strategy", DifficultyLevel.INTERMEDIATE,
         "Previous [3] = single strong opponent likely has combos, will control turns")
    ]
    
    for scenario_data in mixed_field_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.FIELD_STRENGTH,
            subcategory="mixed_borderline_fields",
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


def test_field_strength_scenarios(verbose_output, enable_ai_analysis):
    """Test all field strength scenarios."""
    scenarios = get_field_strength_scenarios()
    
    results = run_category_tests(
        scenarios=scenarios,
        category_name="FIELD_STRENGTH",
        verbose=verbose_output,
        enable_analysis=enable_ai_analysis
    )
    
    # Validate field strength adaptation patterns
    weak_results = [r for r in results if r.scenario.subcategory == "weak_field_exploitation"]
    strong_results = [r for r in results if r.scenario.subcategory == "strong_field_caution"]
    mixed_results = [r for r in results if r.scenario.subcategory == "mixed_borderline_fields"]
    
    # Weak field scenarios should generally enable more aggressive declarations
    weak_passed = sum(1 for r in weak_results if r.passed)
    assert weak_passed >= 3, f"Most weak field scenarios should pass: {weak_passed}/5"
    
    # Strong field scenarios should show conservative adaptation
    strong_passed = sum(1 for r in strong_results if r.passed)
    assert strong_passed >= 3, f"Most strong field scenarios should pass: {strong_passed}/5"
    
    # Mixed field scenarios test nuanced assessment
    mixed_passed = sum(1 for r in mixed_results if r.passed)
    assert mixed_passed >= 3, f"Most mixed field scenarios should pass: {mixed_passed}/5"
    
    # Report any failures for analysis
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id} ({r.scenario.subcategory}): Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        print(f"Field strength test failures:\n{failure_summary}")


def test_weak_vs_strong_field_contrast():
    """Test that similar hands show field-strength-based differences."""
    scenarios = get_field_strength_scenarios()
    
    # Find scenarios with similar hands but different field strengths
    weak_medium_pieces = next((s for s in scenarios if s.scenario_id == "field_weak_01"), None)
    strong_medium_pieces = next((s for s in scenarios if s.scenario_id == "field_strong_05"), None)
    
    assert weak_medium_pieces is not None and strong_medium_pieces is not None
    
    # Execute both scenarios
    weak_result = execute_test_scenario(weak_medium_pieces, verbose=False)
    strong_result = execute_test_scenario(strong_medium_pieces, verbose=False)
    
    # Weak field should enable more aggressive declaration than strong field
    assert weak_result.actual_result >= strong_result.actual_result, \
        f"Field strength adaptation failed: weak field got {weak_result.actual_result}, strong field got {strong_result.actual_result}"


def test_field_strength_assessment_logic():
    """Test that field strength is assessed correctly from previous declarations."""
    scenarios = get_field_strength_scenarios()
    
    # Test weak field assessment (should have low average)
    weak_scenarios = [s for s in scenarios if s.subcategory == "weak_field_exploitation"]
    for scenario in weak_scenarios:
        if scenario.previous_decl:
            avg_declaration = sum(scenario.previous_decl) / len(scenario.previous_decl)
            assert avg_declaration <= 1.5, \
                f"Weak field scenario {scenario.scenario_id} has high average: {avg_declaration}"
    
    # Test strong field assessment (should have high average)
    strong_scenarios = [s for s in scenarios if s.subcategory == "strong_field_caution"]
    for scenario in strong_scenarios:
        if scenario.previous_decl:
            avg_declaration = sum(scenario.previous_decl) / len(scenario.previous_decl)
            assert avg_declaration >= 3.0, \
                f"Strong field scenario {scenario.scenario_id} has low average: {avg_declaration}"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_field_strength_scenarios()
    results = run_category_tests(scenarios, "FIELD_STRENGTH", verbose=True, enable_analysis=False)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n🎯 FIELD STRENGTH SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
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
    weak_results = [r for r in results if "weak" in r.scenario.subcategory]
    strong_results = [r for r in results if "strong" in r.scenario.subcategory]
    
    if weak_results and strong_results:
        avg_weak_declaration = sum(r.actual_result for r in weak_results) / len(weak_results)
        avg_strong_declaration = sum(r.actual_result for r in strong_results) / len(strong_results)
        print(f"  • Average weak field declarations: {avg_weak_declaration:.1f}")
        print(f"  • Average strong field declarations: {avg_strong_declaration:.1f}")
        print(f"  • Field adaptation ratio: {avg_weak_declaration / max(avg_strong_declaration, 0.1):.1f}x")
    
    if passed < total:
        failed = [r for r in results if not r.passed]
        print("\n❌ Failed tests:")
        for r in failed:
            diff = r.actual_result - r.scenario.expected
            print(f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d})")