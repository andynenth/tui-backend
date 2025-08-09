#!/usr/bin/env python3
"""
GENERAL_RED Special Cases AI Declaration Tests for V2 Implementation - 9 Scenarios

This module tests the V2 AI's handling of GENERAL_RED (14 points) using the new
strategic approach:
- Hierarchy-based strong combo detection
- Double GENERAL bonus logic (+1 pile room when holding both GENERALs)
- Strategic pile room calculation
- Enhanced combo size sorting

Test Focus:
- V2 game-changing scenarios with GENERAL_RED
- V2 field strength interactions with opener reliability
- V2 combo enablement through GENERAL_RED control
- V2 double GENERAL bonus detection

Total Tests: 9 scenarios (3 game changer + 3 field interaction + 3 combo enablement)
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_general_red_special_v2_scenarios():
    """Get all GENERAL_RED special case test scenarios updated for V2 declaration logic."""
    scenarios = []
    
    # ========================================================================
    # Game Changer Scenarios (3 tests) - V2 Updates
    # ========================================================================
    game_changer_scenarios = [
        ("general_red_v2_01", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
         2, [1, 0], 8, "GENERAL_RED Transforms Hand", False, "V2: GENERAL opener + FOUR_OF_A_KIND + STRAIGHT", DifficultyLevel.BASIC,
         "V2: GENERAL_RED (1) + FOUR_OF_A_KIND BLACK (4) + STRAIGHT RED (3) = 8 piles with hierarchy logic"),
        
        ("general_red_v2_02", "[GENERAL_RED, CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         1, [1], 4, "GENERAL_RED + Combo vs Weak", False, "V2: GENERAL opener + STRAIGHT combo", DifficultyLevel.INTERMEDIATE,
         "V2: GENERAL opener (1) + RED STRAIGHT (3) = 4 piles, weak field enables combo"),
        
        ("general_red_v2_03", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [0, 1, 2], 2, "GENERAL_RED vs Mixed Field", False, "V2: GENERAL + ADVISOR both qualify as openers", DifficultyLevel.ADVANCED,
         "V2: GENERAL_RED (1) + ADVISOR_BLACK (1) = 2 piles, both qualify as strong openers")
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
    # Field Strength Interaction Scenarios (3 tests) - V2 Updates
    # ========================================================================
    field_interaction_scenarios = [
        ("general_red_field_v2_01", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED]",
         2, [0, 0], 1, "GENERAL_RED vs Very Weak Field", False, "V2: GENERAL opener reliable regardless of field", DifficultyLevel.BASIC,
         "V2: GENERAL_RED opener always reliable, weak field doesn't change opener logic"),
        
        ("general_red_field_v2_02", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED]",
         1, [5], 1, "GENERAL_RED vs Very Strong Field", False, "V2: GENERAL opener reliable vs strong field", DifficultyLevel.INTERMEDIATE,
         "V2: GENERAL opener reliable even against strong opponent (5)"),
        
        ("general_red_field_v2_03", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED]",
         2, [2, 3], 1, "GENERAL_RED vs Normal Field", False, "V2: GENERAL opener consistent performance", DifficultyLevel.BASIC,
         "V2: GENERAL opener reliable in normal field [2,3]")
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
    # Combo Enablement Scenarios (3 tests) - V2 Updates
    # ========================================================================
    combo_enablement_scenarios = [
        ("general_red_combo_v2_01", "[GENERAL_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
         2, [1, 2], 4, "GENERAL_RED Enables THREE_OF_A_KIND", False, "V2: GENERAL opener + THREE_OF_A_KIND always strong", DifficultyLevel.INTERMEDIATE,
         "V2: GENERAL opener (1) + THREE_OF_A_KIND RED always strong (3) = 4 piles"),
        
        ("general_red_combo_v2_02", "[GENERAL_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED, SOLDIER_RED, SOLDIER_BLACK, ADVISOR_RED]",
         1, [2], 4, "GENERAL_RED + Weak STRAIGHT", False, "V2: GENERAL + STRAIGHT + ADVISOR openers", DifficultyLevel.ADVANCED,
         "V2: GENERAL (1) + BLACK STRAIGHT (3) + ADVISOR opener possible = 4 total"),
        
        ("general_red_combo_v2_03", "[GENERAL_RED, GENERAL_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED]",
         3, [0, 1, 1], 8, "Double GENERAL + FOUR_OF_A_KIND", False, "V2: Double GENERAL bonus + strong combo", DifficultyLevel.BASIC,
         "V2: GENERAL_RED opener + double GENERAL bonus + FOUR_OF_A_KIND + additional pieces = 8")
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


def test_general_red_special_v2_scenarios(verbose_output, enable_ai_analysis):
    """Test all GENERAL_RED special case V2 scenarios."""
    scenarios = get_general_red_special_v2_scenarios()
    
    # Create a custom execute function that uses V2
    def execute_v2_wrapper(scenario, verbose=False):
        """Wrapper to make V2 executor compatible with run_category_tests."""
        return execute_test_scenario_v2(scenario, verbose)
    
    # Use V2 executor for all tests
    results = []
    for scenario in scenarios:
        result = execute_v2_wrapper(scenario, verbose=verbose_output)
        results.append(result)
    
    # Print category results
    print(f"\n{'='*80}")
    print(f"GENERAL_RED SPECIAL V2 TEST RESULTS")
    print(f"{'='*80}")
    
    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        diff = f" ({result.actual_result - result.scenario.expected:+d})" if not result.passed else ""
        print(f"{status} {result.scenario.scenario_id}: {result.scenario.description}{diff}")
    
    # Validate V2 GENERAL_RED special behavior patterns
    game_changer_results = [r for r in results if r.scenario.subcategory == "game_changer_scenarios"]
    field_interaction_results = [r for r in results if r.scenario.subcategory == "field_strength_interaction"]
    combo_enablement_results = [r for r in results if r.scenario.subcategory == "combo_enablement"]
    
    # V2 game changer scenarios should show transformative power with hierarchy
    game_changer_passed = sum(1 for r in game_changer_results if r.passed)
    assert game_changer_passed >= 2, f"Most V2 game changer scenarios should pass: {game_changer_passed}/3"
    
    # V2 field interaction scenarios test GENERAL_RED reliability across fields
    field_passed = sum(1 for r in field_interaction_results if r.passed)
    assert field_passed >= 2, f"Most V2 field interaction scenarios should pass: {field_passed}/3"
    
    # V2 combo enablement scenarios test hierarchy + double GENERAL bonus
    combo_passed = sum(1 for r in combo_enablement_results if r.passed)
    assert combo_passed >= 2, f"Most V2 combo enablement scenarios should pass: {combo_passed}/3"
    
    print(f"\n🎯 GENERAL_RED SPECIAL V2 SUMMARY: {sum(1 for r in results if r.passed)}/{len(results)} tests passed ({sum(1 for r in results if r.passed)/len(results)*100:.1f}%)")
    
    # Report any failures for V2 analysis
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id} ({r.scenario.subcategory}): Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        print(f"GENERAL_RED special V2 test failures:\n{failure_summary}")


def test_v2_general_red_game_changing_power():
    """Test that V2 GENERAL_RED enables declarations through hierarchy logic."""
    scenarios = get_general_red_special_v2_scenarios()
    
    # Test maximum combo scenario with V2 hierarchy
    max_combo = next((s for s in scenarios if s.scenario_id == "general_red_v2_01"), None)
    assert max_combo is not None
    
    result = execute_test_scenario_v2(max_combo, verbose=False)
    
    # V2 GENERAL_RED should enable high declarations through hierarchy + combo detection
    assert result.actual_result >= 6, \
        f"V2 GENERAL_RED game-changing power failed: expected high declaration, got {result.actual_result}"


def test_v2_general_red_field_strength_adaptation():
    """Test that V2 GENERAL_RED maintains reliability across field strengths."""
    scenarios = get_general_red_special_v2_scenarios()
    
    # Find weak vs strong field scenarios
    weak_field = next((s for s in scenarios if s.scenario_id == "general_red_field_v2_01"), None)
    strong_field = next((s for s in scenarios if s.scenario_id == "general_red_field_v2_02"), None)
    normal_field = next((s for s in scenarios if s.scenario_id == "general_red_field_v2_03"), None)
    
    assert all(s is not None for s in [weak_field, strong_field, normal_field])
    
    # Execute all field strength scenarios
    weak_result = execute_test_scenario_v2(weak_field, verbose=False)
    strong_result = execute_test_scenario_v2(strong_field, verbose=False)
    normal_result = execute_test_scenario_v2(normal_field, verbose=False)
    
    # V2 GENERAL_RED should be reliable across all field types (opener requirement)
    assert all(r.actual_result >= 1 for r in [weak_result, strong_result, normal_result]), \
        f"V2 GENERAL_RED reliability failed: weak={weak_result.actual_result}, strong={strong_result.actual_result}, normal={normal_result.actual_result}"
    
    # V2 opener consistency - should be same across fields (opener-based logic)
    assert weak_result.actual_result == strong_result.actual_result == normal_result.actual_result, \
        f"V2 GENERAL_RED field consistency failed: weak={weak_result.actual_result}, strong={strong_result.actual_result}, normal={normal_result.actual_result}"


def test_v2_general_red_combo_enablement():
    """Test that V2 GENERAL_RED enables combo play through hierarchy logic."""
    scenarios = get_general_red_special_v2_scenarios()
    combo_scenarios = [s for s in scenarios if s.subcategory == "combo_enablement"]
    
    for scenario in combo_scenarios:
        result = execute_test_scenario_v2(scenario, verbose=False)
        
        # V2 GENERAL_RED combo scenarios should achieve significant declarations
        assert result.actual_result >= 2, \
            f"V2 GENERAL_RED combo enablement failed in {scenario.scenario_id}: got {result.actual_result}"
        
        # Should not exceed hand capability constraints
        assert result.actual_result <= 8, \
            f"V2 GENERAL_RED over-declaration in {scenario.scenario_id}: got {result.actual_result}"


def test_v2_double_general_bonus():
    """Test that V2 double GENERAL bonus logic works correctly."""
    scenarios = get_general_red_special_v2_scenarios()
    
    # Test double GENERAL scenario
    double_general = next((s for s in scenarios if s.scenario_id == "general_red_combo_v2_03"), None)
    assert double_general is not None
    
    result = execute_test_scenario_v2(double_general, verbose=False)
    
    # V2 should achieve high declaration through double GENERAL bonus + hierarchy
    assert result.actual_result >= 7, \
        f"V2 double GENERAL bonus failed: expected high declaration, got {result.actual_result}"


def test_v2_general_red_vs_other_openers():
    """Test that V2 GENERAL_RED maintains opener consistency."""
    scenarios = get_general_red_special_v2_scenarios()
    
    # Calculate GENERAL_RED scenario performance
    total_declarations = sum(execute_test_scenario_v2(s, verbose=False).actual_result for s in scenarios)
    avg_declaration = total_declarations / len(scenarios)
    
    # V2 GENERAL_RED scenarios should maintain good average performance
    assert avg_declaration >= 2.0, \
        f"V2 GENERAL_RED average performance too low: {avg_declaration:.1f}"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_general_red_special_v2_scenarios()
    
    print("="*100)
    print("🎯 TESTING GENERAL_RED SPECIAL V2 SCENARIOS")
    print("="*100)
    print(f"Total scenarios: {len(scenarios)}\n")
    
    results = []
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔍 Test {i}/{len(scenarios)}: {scenario.scenario_id}")
        print("="*80)
        print(f"📝 Description: {scenario.description}")
        print(f"🎯 Strategic Focus: {scenario.strategic_focus}")
        print(f"🎲 Position: {scenario.position} ({'Starter' if scenario.is_starter else 'Non-starter'})")
        print(f"📋 Previous Declarations: {scenario.previous_decl}")
        
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
        
        result = execute_test_scenario_v2(scenario, verbose=False)
        results.append(result)
        
        print(f"\n📊 Expected: {scenario.expected}")
        print(f"🤖 Actual: {result.actual_result}")
        if result.passed:
            print("✅ PASSED")
        else:
            print(f"❌ FAILED (difference: {result.actual_result - scenario.expected:+d})")
    
    print("\n" + "="*100)
    print("📊 GENERAL_RED SPECIAL V2 TEST RESULTS SUMMARY")
    print("="*100)
    
    # Group results by pass/fail
    passed_tests = [r for r in results if r.passed]
    failed_tests = [r for r in results if not r.passed]
    
    print(f"\n✅ Passed: {len(passed_tests)}/{len(results)} ({len(passed_tests)/len(results)*100:.1f}%)")
    
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
    
    # Strategic insights for V2
    print("\n🎯 V2 Strategic Insights:")
    
    # Analyze V2 GENERAL_RED performance across field types
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
            print(f"  • V2 GENERAL_RED in {field_type} fields: {avg_decl:.1f} average")
    
    # Analyze V2 combo enablement effectiveness
    combo_results = [r for r in results if r.scenario.subcategory == "combo_enablement"]
    if combo_results:
        avg_combo_declaration = sum(r.actual_result for r in combo_results) / len(combo_results)
        print(f"  • V2 GENERAL_RED combo enablement average: {avg_combo_declaration:.1f}")
    
    # Overall V2 GENERAL_RED performance
    total_declarations = sum(r.actual_result for r in results)
    avg_overall = total_declarations / len(results)
    print(f"  • V2 Overall GENERAL_RED average: {avg_overall:.1f}")
    print(f"  • V2 GENERAL_RED reliability rate: {len(passed_tests)}/{len(results)} ({len(passed_tests)/len(results)*100:.1f}%)")
    
    if failed_tests:
        print(f"\n❌ Failed: {len(failed_tests)}")
        for r in failed_tests:
            diff = r.actual_result - r.scenario.expected
            print(f"   • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d})")
    
    print(f"\n🎯 GENERAL_RED SPECIAL V2 SUMMARY: {len(passed_tests)}/{len(results)} tests passed ({len(passed_tests)/len(results)*100:.1f}%)")
    
    if len(passed_tests) == len(results):
        print("✅ All GENERAL_RED special V2 tests passed!")
    else:
        print("❌ Some tests failed - review V2 implementation")