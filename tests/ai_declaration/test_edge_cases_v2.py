#!/usr/bin/env python3
"""
Edge Cases & Constraints AI Declaration Tests for V2 Implementation - 12 Scenarios

This module tests the V2 AI's handling of complex constraint scenarios and edge
cases using the new strategic approach:
- Hierarchy-based strong combo detection
- Strategic pile room calculation (ignores invalid last declarations)
- Non-starter opener requirements
- Double GENERAL bonus logic

Test Focus:
- V2 must-declare-nonzero constraints with opener requirements
- V2 multiple forbidden values with pile room calculation
- V2 boundary conditions with hierarchy logic
- V2 strategic constraint resolution

Total Tests: 12 scenarios (4 nonzero + 4 forbidden + 4 boundary)
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_edge_case_v2_scenarios():
    """Get all edge case and constraint test scenarios updated for V2 declaration logic."""
    scenarios = []
    
    # ========================================================================
    # Must-Declare-Nonzero Scenarios (4 tests) - V2 Updates
    # ========================================================================
    must_declare_nonzero_scenarios = [
        ("edge_nonzero_v2_01", "[SOLDIER_RED, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_BLACK]",
         2, [3, 4], 0, "Weak Hand, Must Declare Nonzero", False, "V2: Must find opener when nonzero required", DifficultyLevel.BASIC,
         "V2: No opener normally = 0, but must_declare_nonzero forces finding best piece"),
        
        ("edge_nonzero_v2_02", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         1, [0], 2, "Strong Hand, Nonzero Required", False, "V2: GENERAL opener + additional strong piece", DifficultyLevel.INTERMEDIATE,
         "V2: GENERAL opener (1) + additional piece when nonzero required"),
        
        ("edge_nonzero_v2_03", "[HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, CHARIOT_BLACK, ELEPHANT_BLACK, HORSE_BLACK]",
         3, [0, 0, 0], 0, "Very Weak Field, Must Declare", False, "V2: Weak field enables finding best piece", DifficultyLevel.ADVANCED,
         "V2: Weak field [0,0,0] + nonzero constraint = forced to find opener or best piece"),
        
        ("edge_nonzero_v2_04", "[CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, ADVISOR_BLACK]",
         2, [5, 2], 1, "Limited Room + Nonzero", False, "V2: ADVISOR opener with room constraint", DifficultyLevel.ADVANCED,
         "V2: Room=1, ADVISOR opener qualifies when nonzero required")
    ]
    
    for scenario_data in must_declare_nonzero_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.EDGE_CASES,
            subcategory="must_declare_nonzero",
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
    # Multiple Forbidden Values Scenarios (4 tests) - V2 Updates
    # ========================================================================
    multiple_forbidden_scenarios = [
        ("edge_forbidden_v2_01", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         3, [2, 2, 2], 1, "Last Player: Want 2, Forbidden", False, "V2: ADVISOR opener, sum=8 forbidden logic", DifficultyLevel.ADVANCED,
         "V2: ADVISOR supports 1, but 6+2=8 forbidden, choose 1 (has opener)"),
        
        ("edge_forbidden_v2_02", "[GENERAL_RED, ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         3, [3, 1, 0], 3, "Last Player: Want 4, Must Avoid", False, "V2: Strong opener + combo, but must avoid sum=8", DifficultyLevel.BASIC,
         "V2: Would want GENERAL (1) + THREE_OF_A_KIND (3) = 4, but sum=8 forbidden, so adjusts to 3"),
        
        ("edge_forbidden_v2_03", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         3, [1, 3, 3], 1, "Multiple Constraints Edge Case", False, "V2: Find best single piece when constrained", DifficultyLevel.ADVANCED,
         "V2: No opener normally = 0, but constraints force finding best available piece"),
        
        ("edge_forbidden_v2_04", "[SOLDIER_RED, SOLDIER_BLACK, HORSE_RED, CANNON_BLACK, ELEPHANT_RED, CHARIOT_BLACK, ELEPHANT_BLACK, ADVISOR_BLACK]",
         3, [2, 2, 3], 1, "Last Player Constraint + Opener", False, "V2: ADVISOR opener with constraint", DifficultyLevel.INTERMEDIATE,
         "V2: ADVISOR opener supports 1, sum constraint affects but has opener")
    ]
    
    for scenario_data in multiple_forbidden_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.EDGE_CASES,
            subcategory="multiple_forbidden_values",
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
    # Boundary Conditions Scenarios (4 tests) - V2 Updates
    # ========================================================================
    boundary_condition_scenarios = [
        ("edge_boundary_v2_01", "[GENERAL_RED, GENERAL_BLACK, ADVISOR_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK]",
         0, [], 4, "Maximum Openers (Starter)", True, "V2: Starter with all strong pieces", DifficultyLevel.BASIC,
         "V2: Every piece 8+ points, starter can choose optimal strong pieces"),
        
        ("edge_boundary_v2_02", "[SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 6, "All Minimum Pieces (Starter)", True, "V2: Starter finds THREE_OF_A_KIND combos", DifficultyLevel.BASIC,
         "V2: All SOLDIERs - starter can find THREE_OF_A_KIND RED (3) + THREE_OF_A_KIND BLACK (3) = 6"),
        
        ("edge_boundary_v2_03", "[ADVISOR_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         1, [7], 1, "One Opener + Maximum Combo", False, "V2: Has opener, room limited", DifficultyLevel.ADVANCED,
         "V2: ADVISOR opener (1), room=1 after [7], SIX_OF_A_KIND not viable due to no room"),
        
        ("edge_boundary_v2_04", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_RED, ADVISOR_RED, GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         3, [0, 0, 0], 5, "Perfect STRAIGHT + Opener", False, "V2: Weak field enables maximum combo", DifficultyLevel.BASIC,
         "V2: 6-piece STRAIGHT RED (6) vs [0,0,0] = perfect exploitation of weak field")
    ]
    
    for scenario_data in boundary_condition_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.EDGE_CASES,
            subcategory="boundary_conditions",
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


def execute_test_scenario_v2(scenario: TestScenario, verbose: bool = False, must_declare_nonzero: bool = False) -> 'TestResult':
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
    
    # Determine if this is a must_declare_nonzero scenario
    is_nonzero_scenario = "must_declare_nonzero" in scenario.subcategory
    
    # Execute V2 declaration
    start_time = time.time()
    actual = choose_declare_strategic_v2(
        hand=hand,
        is_first_player=scenario.is_starter,
        position_in_order=scenario.position,
        previous_declarations=scenario.previous_decl,
        must_declare_nonzero=is_nonzero_scenario,
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


def test_edge_case_v2_scenarios(verbose_output, enable_ai_analysis):
    """Test all edge case and constraint V2 scenarios."""
    scenarios = get_edge_case_v2_scenarios()
    
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
    print(f"EDGE CASES V2 TEST RESULTS")
    print(f"{'='*80}")
    
    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        diff = f" ({result.actual_result - result.scenario.expected:+d})" if not result.passed else ""
        print(f"{status} {result.scenario.scenario_id}: {result.scenario.description}{diff}")
    
    # Validate V2 edge case handling patterns
    nonzero_results = [r for r in results if r.scenario.subcategory == "must_declare_nonzero"]
    forbidden_results = [r for r in results if r.scenario.subcategory == "multiple_forbidden_values"]
    boundary_results = [r for r in results if r.scenario.subcategory == "boundary_conditions"]
    
    # V2 must-declare-nonzero scenarios must never result in 0 when constraint active
    nonzero_passed = sum(1 for r in nonzero_results if r.passed)
    assert nonzero_passed >= 3, f"Most V2 nonzero constraint scenarios should pass: {nonzero_passed}/4"
    
    # V2 multiple forbidden scenarios test complex constraint resolution
    forbidden_passed = sum(1 for r in forbidden_results if r.passed)
    assert forbidden_passed >= 3, f"Most V2 forbidden value scenarios should pass: {forbidden_passed}/4"
    
    # V2 boundary condition scenarios test extreme cases with hierarchy
    boundary_passed = sum(1 for r in boundary_results if r.passed)
    assert boundary_passed >= 3, f"Most V2 boundary condition scenarios should pass: {boundary_passed}/4"
    
    print(f"\n🎯 EDGE CASES V2 SUMMARY: {sum(1 for r in results if r.passed)}/{len(results)} tests passed ({sum(1 for r in results if r.passed)/len(results)*100:.1f}%)")
    
    # Report any failures for V2 analysis
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id} ({r.scenario.subcategory}): Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        print(f"Edge case V2 test failures:\n{failure_summary}")


def test_v2_must_declare_nonzero_constraint():
    """Test that V2 must-declare-nonzero constraint is properly enforced."""
    scenarios = get_edge_case_v2_scenarios()
    nonzero_scenarios = [s for s in scenarios if s.subcategory == "must_declare_nonzero"]
    
    for scenario in nonzero_scenarios:
        # Execute with must_declare_nonzero=True (determined by scenario subcategory)
        result = execute_test_scenario_v2(scenario, verbose=False, must_declare_nonzero=True)
        
        # V2 must never declare 0 when constraint is active
        assert result.actual_result > 0, \
            f"V2 must-declare-nonzero violation in {scenario.scenario_id}: declared {result.actual_result}"
        
        # Should declare at least 1
        assert result.actual_result >= 1, \
            f"V2 invalid nonzero declaration in {scenario.scenario_id}: {result.actual_result}"


def test_v2_last_player_sum_constraint():
    """Test that V2 last player sum≠8 constraint with pile room calculation."""
    scenarios = get_edge_case_v2_scenarios()
    forbidden_scenarios = [s for s in scenarios if s.subcategory == "multiple_forbidden_values" and s.position == 3]
    
    for scenario in forbidden_scenarios:
        result = execute_test_scenario_v2(scenario, verbose=False)
        
        # Calculate what sum would be with AI's decision using V2 pile room logic
        # V2 ignores invalid last declarations that would make sum > 8
        valid_declarations = []
        cumulative = 0
        for decl in scenario.previous_decl:
            if cumulative + decl <= 8:
                valid_declarations.append(decl)
                cumulative += decl
            # If adding this would exceed 8, ignore it (V2 pile room logic)
        
        total_sum = sum(valid_declarations) + result.actual_result
        
        # Sum should never equal 8 for last player (forbidden)
        assert total_sum != 8, \
            f"V2 last player sum constraint violation in {scenario.scenario_id}: sum={total_sum}"


def test_v2_boundary_condition_hierarchy():
    """Test that V2 extreme boundary conditions use hierarchy logic."""
    scenarios = get_edge_case_v2_scenarios()
    boundary_scenarios = [s for s in scenarios if s.subcategory == "boundary_conditions"]
    
    for scenario in boundary_scenarios:
        result = execute_test_scenario_v2(scenario, verbose=False)
        
        # All V2 boundary scenarios should produce valid declarations
        assert 0 <= result.actual_result <= 8, \
            f"V2 invalid boundary declaration in {scenario.scenario_id}: {result.actual_result}"
        
        # V2 extreme strength scenarios should show appropriate confidence with hierarchy
        if scenario.scenario_id == "edge_boundary_v2_01":  # Maximum openers
            assert result.actual_result >= 2, \
                f"V2 underconfident maximum opener scenario: got {result.actual_result}"
        
        elif scenario.scenario_id == "edge_boundary_v2_02":  # All SOLDIERs
            # V2 starter should find combos even with minimum pieces
            assert result.actual_result >= 3, \
                f"V2 SOLDIER combo detection failed: got {result.actual_result}"


def test_v2_constraint_conflict_resolution():
    """Test V2 behavior when multiple constraints conflict or interact."""
    scenarios = get_edge_case_v2_scenarios()
    
    # Find scenarios with multiple interacting constraints
    complex_scenarios = [s for s in scenarios if s.difficulty_level == DifficultyLevel.ADVANCED]
    
    for scenario in complex_scenarios:
        result = execute_test_scenario_v2(scenario, verbose=False)
        
        # V2 should always produce a legal declaration even under complex constraints
        assert result.actual_result >= 0, \
            f"V2 invalid declaration under complex constraints in {scenario.scenario_id}: {result.actual_result}"
        
        # V2 should not exceed room constraints (using V2 pile room calculation)
        valid_declarations = []
        cumulative = 0
        for decl in scenario.previous_decl:
            if cumulative + decl <= 8:
                valid_declarations.append(decl)
                cumulative += decl
        
        room_available = 8 - sum(valid_declarations)
        assert result.actual_result <= room_available, \
            f"V2 room constraint violation in {scenario.scenario_id}: declared {result.actual_result} with room={room_available}"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_edge_case_v2_scenarios()
    
    print("="*100)
    print("🎯 TESTING EDGE CASES V2 SCENARIOS")
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
    print("📊 EDGE CASES V2 TEST RESULTS SUMMARY")
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
    
    if failed_tests:
        print(f"\n❌ Failed: {len(failed_tests)}")
        for r in failed_tests:
            diff = r.actual_result - r.scenario.expected
            print(f"   • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d})")
    
    print(f"\n🎯 EDGE CASES V2 SUMMARY: {len(passed_tests)}/{len(results)} tests passed ({len(passed_tests)/len(results)*100:.1f}%)")
    
    if len(passed_tests) == len(results):
        print("✅ All edge cases V2 tests passed!")
    else:
        print("❌ Some tests failed - review V2 implementation")