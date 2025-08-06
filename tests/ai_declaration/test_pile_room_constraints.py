#!/usr/bin/env python3
"""
Pile Room Constraints AI Declaration Tests - 12 Scenarios

This module tests how the AI handles pile room constraints - the fundamental
limitation that total declarations cannot exceed 8 piles per round. This
affects strategic planning and forces tradeoffs between hand capability
and available room.

Test Focus:
- Zero pile room scenarios (total = 8, must declare 0)
- Limited room scenarios (constrained declarations)
- Room vs hand capability mismatches
- Strategic room utilization and planning
- Constraint-driven declaration adjustments

Total Tests: 12 scenarios (4 zero + 4 limited + 4 mismatch)
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_pile_room_constraint_scenarios():
    """Get all pile room constraint test scenarios."""
    scenarios = []
    
    # ========================================================================
    # Zero Pile Room Scenarios (4 tests)
    # ========================================================================
    zero_room_scenarios = [
        ("room_zero_01", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [4, 2, 2], 0, "Strong Hand, No Room", False, "Even great hand constrained by zero room", DifficultyLevel.BASIC,
         "Previous total = 8, pile room = 0, hand strength irrelevant"),
        
        ("room_zero_02", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         2, [5, 3], 0, "Maximum Combos, No Room", False, "Perfect combos blocked by room", DifficultyLevel.INTERMEDIATE,
         "FIVE_OF_A_KIND + STRAIGHT but no room = 0 regardless of hand"),
        
        ("room_zero_03", "[CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         1, [8], 0, "Impossible Opponent Declaration", False, "Room calculation edge case", DifficultyLevel.ADVANCED,
         "Opponent declared 8 (impossible but defensive handling)"),
        
        ("room_zero_04", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
         3, [3, 3, 2], 0, "Exact Room Limit", False, "Room calculation at boundary", DifficultyLevel.BASIC,
         "Previous total = 8, exactly at room limit")
    ]
    
    for scenario_data in zero_room_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.PILE_ROOM_CONSTRAINTS,
            subcategory="zero_pile_room",
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
    # Limited Room Scenarios (4 tests)
    # ========================================================================
    limited_room_scenarios = [
        ("room_limited_01", "[GENERAL_RED, ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         2, [4, 3], 1, "Opener + Combo vs Room=1", False, "Must choose opener OR combo", DifficultyLevel.ADVANCED,
         "GENERAL(1) + THREE_OF_A_KIND(3) but room=1, choose reliable opener"),
        
        ("room_limited_02", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK, ADVISOR_RED, ELEPHANT_RED]",
         3, [3, 2, 1], 2, "Room=2, Want Straight+Opener", False, "Perfect room match", DifficultyLevel.BASIC,
         "ADVISOR(1) + weak STRAIGHT needs room=4, but only 2 available, choose opener only"),
        
        ("room_limited_03", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_BLACK]",
         1, [6], 2, "Multiple Pairs, Room=2", False, "Room matches capability", DifficultyLevel.INTERMEDIATE,
         "Two pairs available, room=2 matches perfectly"),
        
        ("room_limited_04", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [2, 2, 1], 1, "Pairs + Room Constraint", False, "Room limits pair combinations", DifficultyLevel.INTERMEDIATE,
         "ELEPHANT pair potential but room=3, limited by lack of opener/control")
    ]
    
    for scenario_data in limited_room_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.PILE_ROOM_CONSTRAINTS,
            subcategory="limited_room",
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
    # Room vs Hand Mismatch Scenarios (4 tests)
    # ========================================================================
    mismatch_scenarios = [
        ("room_mismatch_01", "[ADVISOR_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_RED, CHARIOT_RED, HORSE_RED, CANNON_RED]",
         3, [1, 1, 1], 5, "Hand=7, Room=5", False, "More capability than room", DifficultyLevel.ADVANCED,
         "ADVISOR(1) + THREE_OF_A_KIND(3) + STRAIGHT(3) = 7 capability, room=5"),
        
        ("room_mismatch_02", "[GENERAL_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_BLACK]",
         2, [1, 2], 1, "Hand=1, Room=5", False, "Less capability than room", DifficultyLevel.BASIC,
         "Only GENERAL reliable, room=5 but can only achieve 1 pile safely"),
        
        ("room_mismatch_03", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, CHARIOT_BLACK, HORSE_BLACK]",
         1, [2], 0, "FIVE_OF_A_KIND, Room=6", False, "Perfect combo blocked by position", DifficultyLevel.INTERMEDIATE,
         "FIVE_OF_A_KIND(5) fits in room=6, but non-starter position blocks opportunity"),
        
        ("room_mismatch_04", "[CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         2, [1, 1], 0, "Three Pairs, Room=6", False, "Multiple combos need opportunity", DifficultyLevel.ADVANCED,
         "Three pairs = 6 piles exactly matches room=6, but [1,1] = singles-only opponents")
    ]
    
    for scenario_data in mismatch_scenarios:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.PILE_ROOM_CONSTRAINTS,
            subcategory="room_hand_mismatch",
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


def test_pile_room_constraint_scenarios(verbose_output, enable_ai_analysis):
    """Test all pile room constraint scenarios."""
    scenarios = get_pile_room_constraint_scenarios()
    
    results = run_category_tests(
        scenarios=scenarios,
        category_name="PILE_ROOM_CONSTRAINTS",
        verbose=verbose_output,
        enable_analysis=enable_ai_analysis
    )
    
    # Validate room constraint handling patterns
    zero_results = [r for r in results if r.scenario.subcategory == "zero_pile_room"]
    limited_results = [r for r in results if r.scenario.subcategory == "limited_room"]
    mismatch_results = [r for r in results if r.scenario.subcategory == "room_hand_mismatch"]
    
    # Zero room scenarios must always result in 0 declarations
    zero_passed = sum(1 for r in zero_results if r.passed)
    assert zero_passed == len(zero_results), f"All zero room scenarios must pass: {zero_passed}/{len(zero_results)}"
    
    # Limited room scenarios test constraint optimization
    limited_passed = sum(1 for r in limited_results if r.passed)
    assert limited_passed >= 3, f"Most limited room scenarios should pass: {limited_passed}/4"
    
    # Mismatch scenarios test strategic adaptation
    mismatch_passed = sum(1 for r in mismatch_results if r.passed)
    assert mismatch_passed >= 3, f"Most mismatch scenarios should pass: {mismatch_passed}/4"
    
    # Report any failures for analysis
    failed_tests = [r for r in results if not r.passed]
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id} ({r.scenario.subcategory}): Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        print(f"Pile room constraint test failures:\n{failure_summary}")


def test_zero_room_absolute_constraint():
    """Test that zero room always results in 0 declaration regardless of hand strength."""
    scenarios = get_pile_room_constraint_scenarios()
    zero_room_scenarios = [s for s in scenarios if s.subcategory == "zero_pile_room"]
    
    for scenario in zero_room_scenarios:
        # Verify room calculation is correct
        room_available = 8 - sum(scenario.previous_decl)
        assert room_available <= 0, f"Zero room scenario {scenario.scenario_id} has room > 0: {room_available}"
        
        # Execute test
        result = execute_test_scenario(scenario, verbose=False)
        
        # Must always declare 0 when no room available
        assert result.actual_result == 0, \
            f"Zero room violation in {scenario.scenario_id}: declared {result.actual_result} with room={room_available}"


def test_room_calculation_accuracy():
    """Test that room calculations are accurate across all scenarios."""
    scenarios = get_pile_room_constraint_scenarios()
    
    for scenario in scenarios:
        room_available = 8 - sum(scenario.previous_decl)
        
        # Execute test to get AI decision
        result = execute_test_scenario(scenario, verbose=False)
        
        # AI decision must not exceed available room
        assert result.actual_result <= room_available, \
            f"Room constraint violation in {scenario.scenario_id}: declared {result.actual_result} with room={room_available}"
        
        # AI decision must not be negative
        assert result.actual_result >= 0, \
            f"Negative declaration in {scenario.scenario_id}: {result.actual_result}"


def test_strategic_room_utilization():
    """Test that the AI makes strategic use of available room."""
    scenarios = get_pile_room_constraint_scenarios()
    
    # Find scenario with perfect room match
    perfect_match = next((s for s in scenarios if s.scenario_id == "room_limited_03"), None)
    assert perfect_match is not None
    
    result = execute_test_scenario(perfect_match, verbose=False)
    
    # Should utilize room efficiently when hand matches available room
    room_available = 8 - sum(perfect_match.previous_decl)
    utilization_rate = result.actual_result / room_available if room_available > 0 else 0
    
    # Should use significant portion of available room when capability exists
    assert utilization_rate >= 0.5, \
        f"Poor room utilization in {perfect_match.scenario_id}: used {result.actual_result}/{room_available} ({utilization_rate:.1%})"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_pile_room_constraint_scenarios()
    results = run_category_tests(scenarios, "PILE_ROOM_CONSTRAINTS", verbose=True, enable_analysis=False)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n🎯 PILE ROOM CONSTRAINTS SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
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
    
    # Analyze room utilization efficiency
    room_utilization_data = []
    for result in results:
        room_available = 8 - sum(result.scenario.previous_decl)
        if room_available > 0:
            utilization = result.actual_result / room_available
            room_utilization_data.append(utilization)
    
    if room_utilization_data:
        avg_utilization = sum(room_utilization_data) / len(room_utilization_data)
        print(f"  • Average room utilization: {avg_utilization:.1%}")
        print(f"  • Room utilization range: {min(room_utilization_data):.1%} - {max(room_utilization_data):.1%}")
    
    # Analyze constraint compliance
    constraint_violations = 0
    for result in results:
        room_available = 8 - sum(result.scenario.previous_decl)
        if result.actual_result > room_available:
            constraint_violations += 1
    
    print(f"  • Constraint violations: {constraint_violations}/{total}")
    
    if passed < total:
        failed = [r for r in results if not r.passed]
        print("\n❌ Failed tests:")
        for r in failed:
            diff = r.actual_result - r.scenario.expected
            room = 8 - sum(r.scenario.previous_decl)
            print(f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d}) [room={room}]")