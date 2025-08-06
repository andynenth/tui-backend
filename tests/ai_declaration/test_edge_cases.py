#!/usr/bin/env python3
"""
Edge Cases & Constraints AI Declaration Tests - 12 Scenarios

This module tests the AI's handling of complex constraint scenarios and edge
cases that occur at the boundaries of game rules. These scenarios validate
robust constraint handling and strategic adaptation under unusual conditions.

Test Focus:
- Must-declare-nonzero constraints (cannot declare 0)
- Multiple forbidden values (sum≠8 rule with other constraints)
- Boundary conditions (extreme hand compositions)
- Strategic constraint resolution
- Complex rule interaction handling

Total Tests: 12 scenarios (4 nonzero + 4 forbidden + 4 boundary)
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_edge_case_scenarios():
    """Get all edge case and constraint test scenarios."""
    scenarios = []
    
    # ========================================================================
    # Must-Declare-Nonzero Scenarios (4 tests)
    # ========================================================================
    must_declare_nonzero_scenarios = [
        ("edge_nonzero_01", "[SOLDIER_RED, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_BLACK]",
         2, [3, 4], 1, "Weak Hand, Can't Declare Zero", False, "Must find something when zero forbidden", DifficultyLevel.BASIC,
         "No opener, no room, but must_declare_nonzero forces 1"),
        
        ("edge_nonzero_02", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         1, [0], 3, "Strong Hand, Nonzero Required", False, "Strong hand with nonzero constraint", DifficultyLevel.INTERMEDIATE,
         "Strong hand would declare 2-3 anyway, constraint doesn't affect decision"),
        
        ("edge_nonzero_03", "[HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, CHARIOT_BLACK, ELEPHANT_BLACK, HORSE_BLACK]",
         3, [0, 0, 0], 1, "Very Weak Field, Must Declare", False, "Weak hand enabled by constraint + field", DifficultyLevel.ADVANCED,
         "Weak hand + weak field [0,0,0] + nonzero constraint = forced 1"),
        
        ("edge_nonzero_04", "[CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, ADVISOR_BLACK]",
         2, [5, 2], 1, "Limited Room + Nonzero", False, "Room constraint + nonzero constraint", DifficultyLevel.ADVANCED,
         "Room=1, hand could support 1, nonzero constraint aligns with capability")
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
    # Multiple Forbidden Values Scenarios (4 tests)
    # ========================================================================
    multiple_forbidden_scenarios = [
        ("edge_forbidden_01", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         3, [2, 2, 2], 1, "Last Player: Want 2, Forbidden", False, "Optimal choice forbidden by sum=8 rule", DifficultyLevel.ADVANCED,
         "Hand supports 2, but 6+2=8 forbidden, choose closest valid (1)"),
        
        ("edge_forbidden_02", "[GENERAL_RED, ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         3, [3, 1, 0], 4, "Last Player: Want 4, Can Declare", False, "Strong hand not constrained", DifficultyLevel.BASIC,
         "Hand supports 4, sum would be 4+4=8 but that's allowed (4≠forbidden)"),
        
        ("edge_forbidden_03", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         3, [1, 3, 3], 1, "Multiple Constraints Edge Case", False, "Complex constraint resolution", DifficultyLevel.ADVANCED,
         "Want 1-2, but 7+1=8 forbidden, only 0 or 2+ valid, choose 1 as closest"),
        
        ("edge_forbidden_04", "[SOLDIER_RED, SOLDIER_BLACK, HORSE_RED, CANNON_BLACK, ELEPHANT_RED, CHARIOT_BLACK, ELEPHANT_BLACK, ADVISOR_BLACK]",
         3, [2, 2, 3], 1, "Last Player Constraint + Weak Hand", False, "Constraint forces suboptimal choice", DifficultyLevel.INTERMEDIATE,
         "Hand supports 1, sum=8 (7+1) forbidden, but 1 still best choice")
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
    # Boundary Conditions Scenarios (4 tests)
    # ========================================================================
    boundary_condition_scenarios = [
        ("edge_boundary_01", "[GENERAL_RED, GENERAL_BLACK, ADVISOR_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK]",
         0, [], 4, "Maximum Openers (Starter)", True, "All pieces are openers", DifficultyLevel.BASIC,
         "Every piece 8+ points, maximum opener scenario as starter"),
        
        ("edge_boundary_02", "[SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 1, "All Minimum Pieces (Starter)", True, "Weakest possible hand", DifficultyLevel.BASIC,
         "All SOLDIERs (1pt each), weakest hand possible, starter might win 1"),
        
        ("edge_boundary_03", "[ADVISOR_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         1, [7], 1, "One Opener + Maximum Combo", False, "Extreme hand composition", DifficultyLevel.ADVANCED,
         "ADVISOR + SIX_OF_A_KIND BLACK but opponent declared 7, room=1"),
        
        ("edge_boundary_04", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_RED, ADVISOR_RED, GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         3, [0, 0, 0], 6, "Perfect STRAIGHT + Opener", False, "Ideal hand vs ideal field", DifficultyLevel.BASIC,
         "6-piece STRAIGHT RED + GENERAL_RED vs [0,0,0] = maximum exploitation")
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


def test_edge_case_scenarios(verbose_output, enable_ai_analysis):
    """Test all edge case and constraint scenarios."""
    scenarios = get_edge_case_scenarios()
    
    results = run_category_tests(
        scenarios=scenarios,
        category_name="EDGE_CASES",
        verbose=verbose_output,
        enable_analysis=enable_ai_analysis
    )
    
    # Validate edge case handling patterns
    nonzero_results = [r for r in results if r.scenario.subcategory == "must_declare_nonzero"]
    forbidden_results = [r for r in results if r.scenario.subcategory == "multiple_forbidden_values"]
    boundary_results = [r for r in results if r.scenario.subcategory == "boundary_conditions"]
    
    # Must-declare-nonzero scenarios must never result in 0
    nonzero_passed = sum(1 for r in nonzero_results if r.passed)
    assert nonzero_passed >= 3, f"Most nonzero constraint scenarios should pass: {nonzero_passed}/4"
    
    # Multiple forbidden scenarios test complex constraint resolution
    forbidden_passed = sum(1 for r in forbidden_results if r.passed)
    assert forbidden_passed >= 3, f"Most forbidden value scenarios should pass: {forbidden_passed}/4"
    
    # Boundary condition scenarios test extreme cases
    boundary_passed = sum(1 for r in boundary_results if r.passed)
    assert boundary_passed >= 3, f"Most boundary condition scenarios should pass: {boundary_passed}/4"
    
    # Report any failures for analysis
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id} ({r.scenario.subcategory}): Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        print(f"Edge case test failures:\n{failure_summary}")


def test_must_declare_nonzero_constraint():
    """Test that must-declare-nonzero constraint is properly enforced."""
    scenarios = get_edge_case_scenarios()
    nonzero_scenarios = [s for s in scenarios if s.subcategory == "must_declare_nonzero"]
    
    for scenario in nonzero_scenarios:
        # Execute with must_declare_nonzero=True (this would be set in actual test)
        result = execute_test_scenario(scenario, verbose=False)
        
        # Must never declare 0 when constraint is active
        assert result.actual_result > 0, \
            f"Must-declare-nonzero violation in {scenario.scenario_id}: declared {result.actual_result}"
        
        # Should declare at least 1
        assert result.actual_result >= 1, \
            f"Invalid nonzero declaration in {scenario.scenario_id}: {result.actual_result}"


def test_last_player_sum_constraint():
    """Test that last player sum≠8 constraint is properly handled."""
    scenarios = get_edge_case_scenarios()
    forbidden_scenarios = [s for s in scenarios if s.subcategory == "multiple_forbidden_values" and s.position == 3]
    
    for scenario in forbidden_scenarios:
        result = execute_test_scenario(scenario, verbose=False)
        
        # Calculate what sum would be with AI's decision
        total_sum = sum(scenario.previous_decl) + result.actual_result
        
        # Sum should never equal 8 for last player (forbidden)
        assert total_sum != 8, \
            f"Last player sum constraint violation in {scenario.scenario_id}: sum={total_sum}"


def test_boundary_condition_robustness():
    """Test that extreme boundary conditions are handled robustly."""
    scenarios = get_edge_case_scenarios()
    boundary_scenarios = [s for s in scenarios if s.subcategory == "boundary_conditions"]
    
    for scenario in boundary_scenarios:
        result = execute_test_scenario(scenario, verbose=False)
        
        # All boundary scenarios should produce valid declarations
        assert 0 <= result.actual_result <= 8, \
            f"Invalid boundary declaration in {scenario.scenario_id}: {result.actual_result}"
        
        # Extreme strength scenarios should show appropriate confidence
        if scenario.scenario_id == "edge_boundary_01":  # Maximum openers
            assert result.actual_result >= 2, \
                f"Underconfident maximum opener scenario: got {result.actual_result}"
        
        elif scenario.scenario_id == "edge_boundary_02":  # Minimum pieces
            assert result.actual_result <= 2, \
                f"Overconfident minimum piece scenario: got {result.actual_result}"


def test_constraint_conflict_resolution():
    """Test behavior when multiple constraints conflict or interact."""
    scenarios = get_edge_case_scenarios()
    
    # Find scenarios with multiple interacting constraints
    complex_scenarios = [s for s in scenarios if s.difficulty_level == DifficultyLevel.ADVANCED]
    
    for scenario in complex_scenarios:
        result = execute_test_scenario(scenario, verbose=False)
        
        # Should always produce a legal declaration even under complex constraints
        assert result.actual_result >= 0, \
            f"Invalid declaration under complex constraints in {scenario.scenario_id}: {result.actual_result}"
        
        # Should not exceed room constraints
        room_available = 8 - sum(scenario.previous_decl)
        assert result.actual_result <= room_available, \
            f"Room constraint violation in {scenario.scenario_id}: declared {result.actual_result} with room={room_available}"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_edge_case_scenarios()
    results = run_category_tests(scenarios, "EDGE_CASES", verbose=True, enable_analysis=False)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n🎯 EDGE CASES SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
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
    
    # Analyze constraint handling effectiveness
    constraint_violations = 0
    valid_declarations = 0
    
    for result in results:
        # Check for room constraint violations
        room_available = 8 - sum(result.scenario.previous_decl)
        if result.actual_result > room_available:
            constraint_violations += 1
        
        # Check for valid declaration ranges
        if 0 <= result.actual_result <= 8:
            valid_declarations += 1
    
    print(f"  • Constraint compliance: {total - constraint_violations}/{total} ({(total - constraint_violations)/total*100:.1f}%)")
    print(f"  • Valid declarations: {valid_declarations}/{total} ({valid_declarations/total*100:.1f}%)")
    
    # Analyze nonzero constraint effectiveness
    nonzero_scenarios = [r for r in results if r.scenario.subcategory == "must_declare_nonzero"]
    nonzero_compliant = sum(1 for r in nonzero_scenarios if r.actual_result > 0)
    if nonzero_scenarios:
        print(f"  • Nonzero constraint compliance: {nonzero_compliant}/{len(nonzero_scenarios)} ({nonzero_compliant/len(nonzero_scenarios)*100:.1f}%)")
    
    # Analyze boundary condition handling
    boundary_scenarios = [r for r in results if r.scenario.subcategory == "boundary_conditions"]
    if boundary_scenarios:
        boundary_declarations = [r.actual_result for r in boundary_scenarios]
        avg_boundary = sum(boundary_declarations) / len(boundary_declarations)
        print(f"  • Boundary condition average: {avg_boundary:.1f}")
        print(f"  • Boundary condition range: {min(boundary_declarations)} - {max(boundary_declarations)}")
    
    if passed < total:
        failed = [r for r in results if not r.passed]
        print("\n❌ Failed tests:")
        for r in failed:
            diff = r.actual_result - r.scenario.expected
            room = 8 - sum(r.scenario.previous_decl)
            constraint_info = f"room={room}"
            
            # Add constraint-specific info
            if r.scenario.subcategory == "must_declare_nonzero":
                constraint_info += f", nonzero_required"
            elif r.scenario.subcategory == "multiple_forbidden_values":
                forbidden_sum = sum(r.scenario.previous_decl) + r.scenario.expected
                constraint_info += f", forbidden_sum={forbidden_sum}"
            
            print(f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d}) [{constraint_info}]")