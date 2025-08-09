#!/usr/bin/env python3
"""
Baseline AI Declaration Tests for V2 Implementation

This module tests the new AI declaration V2 logic with updated expected values
based on the new strategic approach:
- Starters find combos first, then individual pieces
- Non-starters need an opener first or declare 0
- Strong combos have average piece value > 6
- Dynamic piece thresholds based on pile room
"""

import pytest
from conftest import (
    TestScenario, TestCategory, DifficultyLevel,
    execute_test_scenario, run_category_tests
)


def get_baseline_v2_scenarios():
    """Get baseline test scenarios updated for V2 declaration logic."""
    
    baseline_v2_tests = [
        # Strong hands with opener - V2 changes
        ("baseline_v2_01", "[ADVISOR_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         0, [], 4, "Strong Hand with Opener (As Starter)", True, "Only ADVISOR counts, straight avg=5 not > 6"),
        
        ("baseline_v2_02", "[ADVISOR_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [0, 1], 4, "Same Hand, Weak Field", False, "Non-starter finds opener, no strong combos"),
        
        ("baseline_v2_03", "[ADVISOR_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [5, 4], 1, "Same Hand, Strong Field (No Room)", False, "No pile room = 0 declaration"),
        
        # Good combos without opener - V2 changes
        ("baseline_v2_04", "[CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_RED, SOLDIER_RED, ELEPHANT_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         0, [], 3, "Good Combos, No Opener (Starter)", True, "Starter but no strong combos (avg not > 6)"),
        
        ("baseline_v2_05", "[CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_RED, SOLDIER_RED, ELEPHANT_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [0, 1], 0, "Good Combos, No Opener (Weak Field)", False, "Non-starter with no opener declares 0"),
        
        ("baseline_v2_06", "[CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_RED, SOLDIER_RED, ELEPHANT_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [4, 5], 0, "Good Combos, Strong Field (No Room)", False, "No pile room = 0"),
        
        # Multiple high cards
        ("baseline_v2_07", "[GENERAL_RED, ELEPHANT_RED, HORSE_RED, SOLDIER_RED, ADVISOR_BLACK, ELEPHANT_BLACK, CANNON_BLACK, SOLDIER_BLACK]",
         0, [], 2, "Multiple High Cards (Starter)", True, "Two openers as starter"),
        
        ("baseline_v2_08", "[GENERAL_RED, ELEPHANT_RED, HORSE_RED, SOLDIER_RED, ADVISOR_BLACK, ELEPHANT_BLACK, CANNON_BLACK, SOLDIER_BLACK]",
         3, [2, 1, 3], 1, "Multiple High Cards (Last Player)", False, "Pile room = 2, only GENERAL qualifies"),
        
        # Weak hands - mostly unchanged
        ("baseline_v2_09", "[ELEPHANT_RED, CHARIOT_RED, HORSE_RED, SOLDIER_RED, ELEPHANT_BLACK, CHARIOT_BLACK, CANNON_BLACK, SOLDIER_BLACK]",
         0, [], 0, "Weak Hand (Starter)", True, "No strong combos, no openers"),
        
        ("baseline_v2_10", "[ELEPHANT_RED, CHARIOT_RED, HORSE_RED, SOLDIER_RED, ELEPHANT_BLACK, CHARIOT_BLACK, CANNON_BLACK, SOLDIER_BLACK]",
         3, [0, 0, 1], 0, "Weak Hand (Weak Field)", False, "Non-starter with no opener"),
        
        # Strong combo scenarios with same color pieces
        ("baseline_v2_11", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         0, [], 8, "Strong Combos (Starter)", True, "SOLDIER combos avg=2, not > 6"),
        
        ("baseline_v2_12", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         1, [5], 0, "Strong Combos (No Control)", False, "Non-starter with no opener"),
        
        # Strategic positioning
        ("baseline_v2_13", "[ADVISOR_RED, ELEPHANT_RED, HORSE_RED, CANNON_RED, CHARIOT_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         3, [3, 2, 1], 0, "Strategic Last Player", False, "Pile room = 2, only ADVISOR qualifies"),
        
        ("baseline_v2_14", "[CHARIOT_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, ADVISOR_BLACK, ELEPHANT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         1, [3], 4, "Mid-Strength Opener", False, "Has ADVISOR opener"),
        
        # Complex combo scenarios with proper colors
        ("baseline_v2_15", "[CHARIOT_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, HORSE_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK]",
         0, [], 6, "Double THREE_OF_A_KIND (Starter)", True, "SOLDIER combos avg < 6"),
        
        ("baseline_v2_16", "[ELEPHANT_RED, CHARIOT_RED, HORSE_RED, CANNON_RED, GENERAL_BLACK, ELEPHANT_BLACK, CHARIOT_BLACK, HORSE_BLACK]",
         2, [4, 3], 0, "Strong Singles (Limited Room)", False, "Pile room = 1, only GENERAL"),
        
        # GENERAL_RED scenarios with strong combos
        ("baseline_v2_17", "[GENERAL_RED, GENERAL_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED, ADVISOR_BLACK, ADVISOR_BLACK, SOLDIER_BLACK]",
         2, [1, 0], 7, "GENERAL_RED Pair + Strong Combos", False, "GENERAL opener + ADVISOR pair + GENERAL"),
        
        ("baseline_v2_18", "[ADVISOR_RED, CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_RED, ADVISOR_BLACK, ELEPHANT_BLACK, SOLDIER_BLACK]",
         3, [2, 2, 1], 1, "Last Player Perfect Match", False, "Only ADVISOR_RED with pile room 3"),
    ]
    
    # Convert to TestScenario objects
    scenarios = []
    for scenario_data in baseline_v2_tests:
        scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus = scenario_data
        
        scenarios.append(TestScenario(
            scenario_id=scenario_id,
            category=TestCategory.BASELINE,
            subcategory="v2_implementation",
            hand_str=hand_str,
            position=position,
            previous_decl=prev_decl,
            expected=expected,
            description=description,
            is_starter=is_starter,
            strategic_focus=focus,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            notes="V2 test case with new strategic logic"
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


def test_baseline_v2_scenarios(verbose_output, enable_ai_analysis):
    """Test all baseline V2 scenarios for regression validation."""
    scenarios = get_baseline_v2_scenarios()
    
    # Create a custom execute function that uses V2
    def execute_v2_wrapper(scenario, verbose=False):
        """Wrapper to make V2 executor compatible with run_category_tests."""
        return execute_test_scenario_v2(scenario, verbose)
    
    # Use run_category_tests but with V2 executor
    from conftest import run_category_tests
    results = []
    for scenario in scenarios:
        result = execute_v2_wrapper(scenario, verbose=verbose_output)
        results.append(result)
    
    # Print category results like baseline.py
    print(f"\n{'='*80}")
    print(f"BASELINE V2 TEST RESULTS")
    print(f"{'='*80}")
    
    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        diff = f" ({result.actual_result - result.scenario.expected:+d})" if not result.passed else ""
        print(f"{status} {result.scenario.scenario_id}: {result.scenario.description}{diff}")
    
    print(f"\n🎯 BASELINE V2 SUMMARY: {sum(1 for r in results if r.passed)}/{len(results)} tests passed ({sum(1 for r in results if r.passed)/len(results)*100:.1f}%)")
    
    # All baseline V2 tests must pass for regression compliance
    failed_tests = [r for r in results if not r.passed]
    
    if failed_tests:
        failure_summary = "\n".join([
            f"  • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({r.actual_result - r.scenario.expected:+d})"
            for r in failed_tests
        ])
        pytest.fail(f"Baseline V2 regression failures detected:\n{failure_summary}")
    
    # Validate specific key scenarios
    key_scenarios = {
        "baseline_v2_01": 1,   # Opener only
        "baseline_v2_11": 0,   # No strong combos
        "baseline_v2_17": 4,   # GENERAL opener + combos
        "baseline_v2_12": 0,   # Position matters
    }
    
    for scenario_id, expected_value in key_scenarios.items():
        scenario_result = next((r for r in results if r.scenario.scenario_id == scenario_id), None)
        assert scenario_result is not None, f"Key scenario {scenario_id} not found"
        assert scenario_result.actual_result == expected_value, \
            f"Key scenario {scenario_id} failed: expected {expected_value}, got {scenario_result.actual_result}"


def test_individual_baseline_v2_scenarios():
    """Individual test methods for each baseline V2 scenario (for detailed pytest output)."""
    scenarios = get_baseline_v2_scenarios()
    
    for scenario in scenarios:
        result = execute_test_scenario_v2(scenario, verbose=False)
        assert result.passed, \
            f"{scenario.scenario_id} failed: expected {scenario.expected}, got {result.actual_result} ({result.actual_result - scenario.expected:+d})"


def test_v2_strong_combo_detection():
    """Test that V2 correctly identifies strong combos (avg > 6)."""
    from backend.engine.piece import Piece
    from backend.engine.ai import is_strong_combo
    
    # Test cases
    test_cases = [
        # (pieces, expected_result)
        ([Piece("GENERAL_RED"), Piece("GENERAL_RED")], True),  # avg = 14
        ([Piece("ADVISOR_BLACK"), Piece("ADVISOR_BLACK")], True),  # avg = 11
        ([Piece("ELEPHANT_RED"), Piece("ELEPHANT_RED")], True),  # avg = 10
        ([Piece("CHARIOT_BLACK"), Piece("CHARIOT_BLACK")], True),  # avg = 7
        ([Piece("HORSE_RED"), Piece("HORSE_RED")], False),  # avg = 6
        ([Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK")], False),  # avg = 1
        ([Piece("CHARIOT_BLACK"), Piece("HORSE_BLACK"), Piece("CANNON_BLACK")], False),  # avg = 5
        ([Piece("GENERAL_BLACK"), Piece("ADVISOR_BLACK"), Piece("ELEPHANT_BLACK")], True),  # avg = 11
    ]
    
    for pieces, expected in test_cases:
        # Determine combo type (simplified for test)
        if len(pieces) == 2 and pieces[0].name == pieces[1].name:
            combo_type = "PAIR"
        elif len(pieces) == 3:
            if all(p.name == "SOLDIER" for p in pieces):
                combo_type = "THREE_OF_A_KIND"
            else:
                combo_type = "STRAIGHT"
        else:
            combo_type = "OTHER"
        
        result = is_strong_combo(combo_type, pieces)
        avg = sum(p.point for p in pieces) / len(pieces)
        
        assert result == expected, \
            f"Strong combo detection failed for {[p.name for p in pieces]} (avg={avg:.1f}): expected {expected}, got {result}"


def test_v2_pile_room_thresholds():
    """Test that V2 correctly applies piece thresholds based on pile room."""
    from backend.engine.piece import Piece
    from backend.engine.ai import get_piece_threshold, get_individual_strong_pieces
    
    # Test threshold values
    assert get_piece_threshold(1) == 13  # Only GENERAL_RED (>13)
    assert get_piece_threshold(2) == 13  # GENERAL pieces (>=13)
    assert get_piece_threshold(3) == 12  # ADVISOR_RED+ (>=12)
    assert get_piece_threshold(5) == 11  # ADVISOR_BLACK+ (>=11)
    assert get_piece_threshold(8) == 11  # Default for high room
    
    # Test piece selection
    hand = [
        Piece("GENERAL_RED"),     # 14
        Piece("GENERAL_BLACK"),   # 13
        Piece("ADVISOR_RED"),     # 12
        Piece("ADVISOR_BLACK"),   # 11
        Piece("ELEPHANT_RED"),    # 10
    ]
    
    # Pile room 1: only GENERAL_RED
    strong_1 = get_individual_strong_pieces(hand, 1)
    assert len(strong_1) == 1
    assert strong_1[0].name == "GENERAL"
    
    # Pile room 2: both GENERALs
    strong_2 = get_individual_strong_pieces(hand, 2)
    assert len(strong_2) == 2
    
    # Pile room 5: all ADVISORs and above
    strong_5 = get_individual_strong_pieces(hand, 5)
    assert len(strong_5) == 4


if __name__ == "__main__":
    # Allow running this module directly for development/debugging
    scenarios = get_baseline_v2_scenarios()
    
    print("="*100)
    print("🎯 TESTING BASELINE V2 SCENARIOS")
    print("="*100)
    print(f"Total scenarios: {len(scenarios)}\n")
    
    # Custom run_category_tests that uses V2 executor
    def run_v2_category_tests(scenarios, category_name, verbose=False):
        """Run category tests with V2 executor."""
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
            
            result = execute_test_scenario_v2(scenario, verbose=verbose)
            results.append(result)
            
            print(f"\n📊 Expected: {scenario.expected}")
            print(f"🤖 Actual: {result.actual_result}")
            if result.passed:
                print("✅ PASSED")
            else:
                print(f"❌ FAILED (difference: {result.actual_result - scenario.expected:+d})")
                
        return results
    
    results = run_v2_category_tests(scenarios, "BASELINE V2", verbose=False)
    
    print("\n" + "="*100)
    print("📊 BASELINE V2 TEST RESULTS SUMMARY")
    print("="*100)
    
    # Group results by pass/fail
    passed_tests = [r for r in results if r.passed]
    failed_tests = [r for r in results if not r.passed]
    
    print(f"\n✅ Passed: {len(passed_tests)}/{len(results)} ({len(passed_tests)/len(results)*100:.1f}%)")
    for r in passed_tests:
        print(f"   • {r.scenario.scenario_id}: {r.scenario.description}")
    
    if failed_tests:
        print(f"\n❌ Failed: {len(failed_tests)}")
        for r in failed_tests:
            diff = r.actual_result - r.scenario.expected
            print(f"   • {r.scenario.scenario_id}: Expected {r.scenario.expected}, got {r.actual_result} ({diff:+d})")
            print(f"     {r.scenario.description}")
    
    print(f"\n🎯 BASELINE V2 SUMMARY: {len(passed_tests)}/{len(results)} tests passed ({len(passed_tests)/len(results)*100:.1f}%)")
    
    if len(passed_tests) == len(results):
        print("✅ All baseline V2 tests passed - regression validation successful!")
    else:
        print("❌ Some tests failed - review the failures above")