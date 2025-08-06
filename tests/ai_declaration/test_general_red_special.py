#!/usr/bin/env python3
"""
GENERAL_RED Special Cases AI Declaration Tests - 9 Scenarios

This module tests the AI's handling of GENERAL_RED (14 points), the most powerful
piece in the game. GENERAL_RED fundamentally changes strategic calculation by
providing guaranteed control and enabling combos that would otherwise be
impossible to play.

Test Focus:
- Game-changing scenarios (GENERAL_RED transforms weak hands)
- Field strength interactions (performance across all field types)
- Combo enablement (GENERAL_RED allows reliable combo play)
- Strategic maximization (optimal GENERAL_RED utilization)
- Control mechanisms (starter-like behavior in any position)

Total Tests: 9 scenarios (3 game changer + 3 field interaction + 3 combo enablement)
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_general_red_special_scenarios():
    """Get all GENERAL_RED special case test scenarios."""
    scenarios = []
    
    # ========================================================================
    # Game Changer Scenarios (3 tests)
    # ========================================================================
    game_changer_scenarios = [
        ("general_red_01", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
         2, [1, 0], 8, "GENERAL_RED Transforms Hand", False, "GENERAL_RED enables maximum declaration", DifficultyLevel.BASIC,
         "GENERAL_RED + weak field enables FOUR_OF_A_KIND + STRAIGHT = 8 piles"),
        
        ("general_red_02", "[GENERAL_RED, CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         1, [1], 4, "GENERAL_RED + Combo vs Weak", False, "Game changer makes combos viable", DifficultyLevel.INTERMEDIATE,
         "GENERAL_RED acts like starter, enables STRAIGHT in weak field"),
        
        ("general_red_03", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [0, 1, 2], 3, "GENERAL_RED vs Mixed Field", False, "Strong piece works in any field", DifficultyLevel.ADVANCED,
         "GENERAL_RED + ADVISOR_BLACK reliable regardless of field strength")
    ]
    
    for scenario_data in game_changer_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.GENERAL_RED_SPECIAL,
            subcategory="game_changer_scenarios",
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
    # Field Strength Interaction Scenarios (3 tests)
    # ========================================================================
    field_interaction_scenarios = [
        ("general_red_field_01", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED]",
         2, [0, 0], 2, "GENERAL_RED vs Very Weak Field", False, "Overkill in very weak field", DifficultyLevel.BASIC,
         "GENERAL_RED + very weak field = guaranteed, but hand only supports 2 piles"),
        
        ("general_red_field_02", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED]",
         1, [5], 1, "GENERAL_RED vs Very Strong Field", False, "Even GENERAL_RED limited by strong field", DifficultyLevel.INTERMEDIATE,
         "GENERAL_RED reliable but strong opponent (5) will control, limits combo opportunities"),
        
        ("general_red_field_03", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED]",
         2, [2, 3], 1, "GENERAL_RED vs Normal Field", False, "Standard GENERAL_RED performance", DifficultyLevel.BASIC,
         "GENERAL_RED reliable in normal field, but no special advantages")
    ]
    
    for scenario_data in field_interaction_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.GENERAL_RED_SPECIAL,
            subcategory="field_strength_interaction",
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
    # Combo Enablement Scenarios (3 tests)
    # ========================================================================
    combo_enablement_scenarios = [
        ("general_red_combo_01", "[GENERAL_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
         2, [1, 2], 4, "GENERAL_RED Enables THREE_OF_A_KIND", False, "Control enables combo play", DifficultyLevel.INTERMEDIATE,
         "GENERAL_RED provides control to play THREE_OF_A_KIND reliably"),
        
        ("general_red_combo_02", "[GENERAL_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED, SOLDIER_RED, SOLDIER_BLACK, ADVISOR_RED]",
         1, [2], 2, "GENERAL_RED + Weak STRAIGHT", False, "Enables marginal combos", DifficultyLevel.ADVANCED,
         "GENERAL_RED makes weak 18-point STRAIGHT viable through control"),
        
        ("general_red_combo_03", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED]",
         3, [0, 1, 1], 6, "GENERAL_RED + FIVE_OF_A_KIND", False, "Maximum combo enablement", DifficultyLevel.BASIC,
         "GENERAL_RED + weak field enables FIVE_OF_A_KIND (5) + opener (1) = 6")
    ]
    
    for scenario_data in combo_enablement_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.GENERAL_RED_SPECIAL,
            subcategory="combo_enablement",
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


def test_general_red_special_scenarios(verbose_output, enable_ai_analysis):
    """Test all GENERAL_RED special case scenarios."""
    scenarios = get_general_red_special_scenarios()
    
    results = run_category_tests(
        scenarios=scenarios,
        category_name="GENERAL_RED_SPECIAL",
        verbose=verbose_output,
        enable_analysis=enable_ai_analysis
    )
    
    # Validate GENERAL_RED special behavior patterns
    game_changer_results = [r for r in results if r.scenario.subcategory == "game_changer_scenarios"]
    field_interaction_results = [r for r in results if r.scenario.subcategory == "field_strength_interaction"]
    combo_enablement_results = [r for r in results if r.scenario.subcategory == "combo_enablement"]
    
    # Game changer scenarios should show transformative power
    game_changer_passed = sum(1 for r in game_changer_results if r.passed)
    assert game_changer_passed >= 2, f"Most game changer scenarios should pass: {game_changer_passed}/3"
    
    # Field interaction scenarios test GENERAL_RED across all field types
    field_passed = sum(1 for r in field_interaction_results if r.passed)
    assert field_passed >= 2, f"Most field interaction scenarios should pass: {field_passed}/3"
    
    # Combo enablement scenarios test control mechanisms
    combo_passed = sum(1 for r in combo_enablement_results if r.passed)
    assert combo_passed >= 2, f"Most combo enablement scenarios should pass: {combo_passed}/3"
    
    # Report any failures for analysis
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id} ({r.scenario.subcategory}): Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        print(f"GENERAL_RED special test failures:\n{failure_summary}")


def test_general_red_game_changing_power():
    """Test that GENERAL_RED enables declarations that would otherwise be impossible."""
    scenarios = get_general_red_special_scenarios()
    
    # Test maximum combo scenario
    max_combo = next((s for s in scenarios if s.scenario_id == "general_red_01"), None)
    assert max_combo is not None
    
    result = execute_test_scenario(max_combo, verbose=False)
    
    # GENERAL_RED should enable near-maximum declarations
    assert result.actual_result >= 6, \
        f"GENERAL_RED game-changing power failed: expected high declaration, got {result.actual_result}"


def test_general_red_field_strength_adaptation():
    """Test that GENERAL_RED adapts appropriately to different field strengths."""
    scenarios = get_general_red_special_scenarios()
    
    # Find weak vs strong field scenarios
    weak_field = next((s for s in scenarios if s.scenario_id == "general_red_field_01"), None)
    strong_field = next((s for s in scenarios if s.scenario_id == "general_red_field_02"), None)
    normal_field = next((s for s in scenarios if s.scenario_id == "general_red_field_03"), None)
    
    assert all(s is not None for s in [weak_field, strong_field, normal_field])
    
    # Execute all field strength scenarios
    weak_result = execute_test_scenario(weak_field, verbose=False)
    strong_result = execute_test_scenario(strong_field, verbose=False)
    normal_result = execute_test_scenario(normal_field, verbose=False)
    
    # GENERAL_RED should be reliable across all field types
    assert all(r.actual_result >= 1 for r in [weak_result, strong_result, normal_result]), \
        f"GENERAL_RED reliability failed: weak={weak_result.actual_result}, strong={strong_result.actual_result}, normal={normal_result.actual_result}"
    
    # Weak field should generally allow more aggressive declarations than strong field
    assert weak_result.actual_result >= strong_result.actual_result, \
        f"GENERAL_RED field adaptation failed: weak={weak_result.actual_result}, strong={strong_result.actual_result}"


def test_general_red_combo_enablement():
    """Test that GENERAL_RED enables combo play through control mechanisms."""
    scenarios = get_general_red_special_scenarios()
    combo_scenarios = [s for s in scenarios if s.subcategory == "combo_enablement"]
    
    for scenario in combo_scenarios:
        result = execute_test_scenario(scenario, verbose=False)
        
        # GENERAL_RED combo scenarios should achieve significant declarations
        assert result.actual_result >= 2, \
            f"GENERAL_RED combo enablement failed in {scenario.scenario_id}: got {result.actual_result}"
        
        # Should not exceed hand capability constraints
        assert result.actual_result <= 8, \
            f"GENERAL_RED over-declaration in {scenario.scenario_id}: got {result.actual_result}"


def test_general_red_vs_other_openers():
    """Test that GENERAL_RED outperforms other openers consistently."""
    # This would require comparing with similar scenarios from other test files
    # For now, just validate that GENERAL_RED scenarios achieve good results
    scenarios = get_general_red_special_scenarios()
    
    total_declarations = sum(execute_test_scenario(s, verbose=False).actual_result for s in scenarios)
    avg_declaration = total_declarations / len(scenarios)
    
    # GENERAL_RED scenarios should average higher than typical opener scenarios
    assert avg_declaration >= 2.0, \
        f"GENERAL_RED average performance too low: {avg_declaration:.1f}"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_general_red_special_scenarios()
    results = run_category_tests(scenarios, "GENERAL_RED_SPECIAL", verbose=True, enable_analysis=False)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n🎯 GENERAL_RED SPECIAL SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
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
    
    # Analyze GENERAL_RED performance across field types
    field_performance = {}
    for result in results:
        if result.scenario.subcategory == "field_strength_interaction":
            field_avg = sum(result.scenario.previous_decl) / len(result.scenario.previous_decl) if result.scenario.previous_decl else 2.0
            
            if field_avg <= 1.0:
                field_type = "weak"
            elif field_avg >= 3.5:
                field_type = "strong"
            else:
                field_type = "normal"
            
            if field_type not in field_performance:
                field_performance[field_type] = []
            field_performance[field_type].append(result.actual_result)
    
    for field_type, declarations in field_performance.items():
        if declarations:
            avg_decl = sum(declarations) / len(declarations)
            print(f"  • GENERAL_RED in {field_type} fields: {avg_decl:.1f} average")
    
    # Analyze combo enablement effectiveness
    combo_results = [r for r in results if r.scenario.subcategory == "combo_enablement"]
    if combo_results:
        avg_combo_declaration = sum(r.actual_result for r in combo_results) / len(combo_results)
        print(f"  • GENERAL_RED combo enablement average: {avg_combo_declaration:.1f}")
    
    # Overall GENERAL_RED performance
    total_declarations = sum(r.actual_result for r in results)
    avg_overall = total_declarations / len(results)
    print(f"  • Overall GENERAL_RED average: {avg_overall:.1f}")
    print(f"  • GENERAL_RED reliability rate: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed < total:
        failed = [r for r in results if not r.passed]
        print("\n❌ Failed tests:")
        for r in failed:
            diff = r.actual_result - r.scenario.expected
            field_strength = sum(r.scenario.previous_decl) / len(r.scenario.previous_decl) if r.scenario.previous_decl else 2.0
            print(f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d}) [field={field_strength:.1f}]")