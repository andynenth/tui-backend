#!/usr/bin/env python3
"""
Baseline AI Declaration Tests - Original 18 Scenarios

This module contains the original 18 test scenarios that serve as regression tests.
These scenarios must continue to pass to ensure no functionality is broken during
AI improvements and strategic enhancements.

Test Focus:
- Regression validation
- Core AI functionality
- Basic strategic patterns
- Starter vs non-starter behavior
- Field strength assessment
- Combo opportunity detection
- Room constraint handling

Total Tests: 18 scenarios
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_baseline_scenarios():
    """Get all baseline test scenarios (original 18 tests)."""
    
    # Original test data preserved exactly as implemented
    baseline_tests = [
        # Strong hands with opener
        ("baseline_01", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         0, [], 4, "Strong Hand with Opener (As Starter)", True, "Starter advantage with opener + combo"),
        
        ("baseline_02", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [0, 1], 1, "Same Hand, Weak Field", False, "Non-starter in weak field"),
        
        ("baseline_03", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [5, 4], 1, "Same Hand, Strong Field (No Room)", False, "Pile room constraint override"),
        
        # Good combos without opener
        ("baseline_04", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         0, [], 3, "Good Combos, No Opener (Starter)", True, "Starter enables combos without opener"),
        
        ("baseline_05", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [0, 1], 1, "Good Combos, No Opener (Weak Field)", False, "Weak field limits combo opportunity"),
        
        ("baseline_06", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [4, 5], 0, "Good Combos, Strong Field (No Room)", False, "Strong field + no room = zero declaration"),
        
        # Multiple high cards
        ("baseline_07", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 2, "Multiple High Cards (Starter)", True, "Multiple opener assessment"),
        
        ("baseline_08", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [2, 1, 3], 1, "Multiple High Cards (Last Player)", False, "Last player constraint handling"),
        
        # Weak hands
        ("baseline_09", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 1, "Weak Hand (Starter)", True, "Starter advantage with weak hand"),
        
        ("baseline_10", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [0, 0, 1], 2, "Weak Hand (Weak Field)", False, "Weak field enables medium pieces"),
        
        # Strong combo scenarios
        ("baseline_11", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         0, [], 8, "Strong Combos (Starter)", True, "Maximum declaration with multiple combos"),
        
        ("baseline_12", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         1, [5], 0, "Strong Combos (No Control)", False, "Great hand, wrong position"),
        
        # Strategic positioning
        ("baseline_13", "[ADVISOR_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_RED]",
         3, [3, 2, 1], 1, "Strategic Last Player", False, "Last player pile room limitation"),
        
        ("baseline_14", "[ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_RED, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
         1, [3], 1, "Mid-Strength Opener", False, "Single opponent with combos"),
        
        # Complex combo scenarios  
        ("baseline_15", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK]",
         0, [], 6, "Double THREE_OF_A_KIND (Starter)", True, "Multiple combo types as starter"),
        
        ("baseline_16", "[GENERAL_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED]",
         2, [4, 3], 1, "Strong Singles (Limited Room)", False, "Strong opener limited by room"),
        
        # GENERAL_RED scenarios
        ("baseline_17", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
         2, [1, 0], 8, "GENERAL_RED Game Changer", False, "GENERAL_RED transforms strategy"),
        
        ("baseline_18", "[ADVISOR_RED, ADVISOR_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [2, 2, 1], 2, "Last Player Perfect Match", False, "Perfect pile room match as last player"),
    ]
    
    # Convert to TestScenario objects
    scenarios = []
    for scenario_data in baseline_tests:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus = scenario_data
        
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.BASELINE,
            subcategory="regression_test",
            hand_str=hand_str,
            position=position,
            previous_decl=prev_decl,
            expected=expected,
            description=description,
            is_starter=is_starter,
            strategic_focus=focus,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            notes="Original test case for regression validation"
        ))
    
    return scenarios


def test_baseline_scenarios(verbose_output, enable_ai_analysis):
    """Test all baseline scenarios for regression validation."""
    scenarios = get_baseline_scenarios()
    
    results = run_category_tests(
        scenarios=scenarios,
        category_name="BASELINE",
        verbose=verbose_output,
        enable_analysis=enable_ai_analysis
    )
    
    # All baseline tests must pass for regression compliance
    failed_tests = [r for r in results if not r.passed]
    
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        pytest.fail(f"Baseline regression failures detected:\n{failure_summary}")
    
    # Validate specific key scenarios
    key_scenarios = {
        "baseline_01": 4,  # Strong starter
        "baseline_11": 8,  # Maximum combo
        "baseline_17": 8,  # GENERAL_RED
        "baseline_12": 0,  # Position matters
    }
    
    for scenario_id, expected_value in key_scenarios.items():
        scenario_result = next((r for r in results if r.scenario.scenario_id == scenario_id), None)
        assert scenario_result is not None, f"Key scenario {scenario_id} not found"
        assert scenario_result.actual_result == expected_value, \
            f"Key scenario {scenario_id} failed: expected {expected_value}, got {scenario_result.actual_result}"


def test_individual_baseline_scenarios():
    """Individual test methods for each baseline scenario (for detailed pytest output)."""
    scenarios = get_baseline_scenarios()
    
    for scenario in scenarios:
        result = execute_test_scenario(scenario, verbose=False)
        assert result.passed, \
            f"{scenario.scenario_id} failed: expected {scenario.expected}, got {result.actual_result} ({result.actual_result - scenario.expected:+d})"


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_baseline_scenarios()
    results = run_category_tests(scenarios, "BASELINE", verbose=True, enable_analysis=False)
    
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n🎯 BASELINE SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("✅ All baseline tests passed - regression validation successful!")
    else:
        failed = [r for r in results if not r.passed]
        print("❌ Failed baseline tests:")
        for r in failed:
            diff = r.actual_result - r.scenario.expected
            print(f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d})")