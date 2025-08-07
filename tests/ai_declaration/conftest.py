#!/usr/bin/env python3
"""
Shared fixtures and utilities for AI declaration tests.

This module provides all the common functionality needed across the different
test category files, including data structures, parsing functions, and test execution.
"""

import sys
import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from enum import Enum
import pytest

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare


# ============================================================================
# Data Structures & Enums
# ============================================================================

class TestCategory(Enum):
    BASELINE = "baseline"
    POSITION_STRATEGY = "position_strategy"
    FIELD_STRENGTH = "field_strength"
    COMBO_OPPORTUNITY = "combo_opportunity" 
    PILE_ROOM_CONSTRAINTS = "pile_room_constraints"
    OPENER_RELIABILITY = "opener_reliability"
    GENERAL_RED_SPECIAL = "general_red_special"
    EDGE_CASES = "edge_cases"


class DifficultyLevel(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class TestScenario:
    """Enhanced test scenario with comprehensive metadata."""
    scenario_id: str
    category: TestCategory
    subcategory: str
    hand_str: str
    position: int
    previous_decl: List[int]
    expected: int
    description: str
    is_starter: bool
    strategic_focus: str  # What this test validates
    difficulty_level: DifficultyLevel
    notes: Optional[str] = None


@dataclass
class TestResult:
    """Individual test result with detailed analysis."""
    scenario: TestScenario
    actual_result: int
    passed: bool
    execution_time: float = 0.0
    ai_analysis: Optional[Dict] = None


# ============================================================================
# Utility Functions
# ============================================================================

def create_piece(name: str, color: str) -> Piece:
    """Create a piece from name and color."""
    # Extract base name (remove color suffix if present)
    base_name = name.replace("_RED", "").replace("_BLACK", "")
    
    # Create the kind string
    kind = f"{base_name}_{color}"
    
    return Piece(kind)


def parse_hand(hand_str: str) -> List[Piece]:
    """Parse hand string into list of pieces."""
    pieces = []
    
    # Handle special notations like SOLDIER×4
    parts = hand_str.replace("[", "").replace("]", "").split(",")
    
    for part in parts:
        part = part.strip()
        if "×" in part or "x" in part:
            # Handle multiplied pieces
            piece_part, count_part = part.replace("×", "x").split("x")
            count = int(count_part)
            base_name = piece_part.strip()
            
            # Determine color from name or default
            if "_RED" in base_name:
                color = "RED"
            elif "_BLACK" in base_name:
                color = "BLACK"
            else:
                # Default color pattern for multiple pieces
                color = "RED" if "RED" in hand_str else "BLACK"
            
            for _ in range(count):
                pieces.append(create_piece(base_name, color))
        else:
            # Single piece
            if "_" in part:
                name = part.strip()
                color = "RED" if "RED" in name else "BLACK"
            else:
                # Infer color from context
                name = part.strip()
                color = "RED"  # Default
            
            pieces.append(create_piece(name, color))
    
    return pieces


def execute_test_scenario(scenario: TestScenario, 
                         enable_analysis: bool = False,
                         verbose: bool = True) -> TestResult:
    """Execute a single test scenario and return detailed results."""
    if verbose:
        print(f"\n{'='*80}")
        print(f"🎯 {scenario.category.value.upper()}: {scenario.description}")
        print(f"{'='*80}")
        print(f"ID: {scenario.scenario_id}")
        print(f"Focus: {scenario.strategic_focus}")
        print(f"Difficulty: {scenario.difficulty_level.value}")
    
    # Parse hand
    hand = parse_hand(scenario.hand_str)
    
    if verbose:
        # Print scenario context with pieces ordered by color then rank
        def sort_pieces_by_color_and_rank(pieces):
            """Sort pieces by color (RED first), then by point value (highest first)."""
            return sorted(pieces, key=lambda p: (p.color != "RED", -p.point))
        
        sorted_hand = sort_pieces_by_color_and_rank(hand)
        hand_summary = ", ".join(f"{piece.kind}" for piece in sorted_hand)
        print(f"🃏 Bot's Hand: [{hand_summary}]")
        print(f"📊 Position: {scenario.position} ({'Starter' if scenario.is_starter else 'Non-starter'})")
        print(f"📋 Previous Declarations: {scenario.previous_decl}")
        
        if scenario.notes:
            print(f"📝 Notes: {scenario.notes}")
    
    # Analysis capture setup (if enabled)
    analysis_data = None
    def capture_analysis_callback(data):
        nonlocal analysis_data
        analysis_data = data
    
    # Execute the AI decision
    import time
    start_time = time.time()
    
    # Determine if this is a must_declare_nonzero scenario
    must_declare_nonzero = scenario.subcategory == "must_declare_nonzero"
    
    actual_result = choose_declare(
        hand=hand,
        is_first_player=scenario.is_starter,
        position_in_order=scenario.position,
        previous_declarations=scenario.previous_decl,
        must_declare_nonzero=must_declare_nonzero,
        verbose=verbose,
        analysis_callback=capture_analysis_callback if enable_analysis else None
    )
    
    execution_time = time.time() - start_time
    
    # Check result
    passed = actual_result == scenario.expected
    
    if verbose:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n🎯 Expected: {scenario.expected}")
        print(f"🤖 Actual:   {actual_result}")
        print(f"📊 Result:   {status}")
        
        if not passed:
            print(f"⚠️  Difference: {actual_result - scenario.expected:+d}")
    
    return TestResult(
        scenario=scenario,
        actual_result=actual_result,
        passed=passed,
        execution_time=execution_time,
        ai_analysis=analysis_data
    )


def run_category_tests(scenarios: List[TestScenario],
                      category_name: str,
                      verbose: bool = True,
                      enable_analysis: bool = False) -> List[TestResult]:
    """Run all tests in a category and return results."""
    if verbose:
        print(f"\n{'='*100}")
        print(f"🎯 TESTING CATEGORY: {category_name.upper()}")
        print(f"{'='*100}")
        print(f"Total scenarios: {len(scenarios)}")
    
    results = []
    passed_count = 0
    
    for i, scenario in enumerate(scenarios, 1):
        if verbose:
            print(f"\n🔍 Test {i}/{len(scenarios)}: {scenario.scenario_id}")
        
        result = execute_test_scenario(scenario, enable_analysis, verbose)
        results.append(result)
        
        if result.passed:
            passed_count += 1
    
    # Category summary
    if verbose:
        success_rate = (passed_count / len(scenarios)) * 100
        print(f"\n{'='*100}")
        print(f"📊 CATEGORY SUMMARY: {category_name.upper()}")
        print(f"{'='*100}")
        print(f"✅ Passed: {passed_count}/{len(scenarios)} ({success_rate:.1f}%)")
        print(f"❌ Failed: {len(scenarios) - passed_count}")
        
        # List failed tests
        failed_tests = [r for r in results if not r.passed]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for result in failed_tests:
                diff = result.actual_result - result.scenario.expected
                print(f"  • {result.scenario.scenario_id}: Expected {result.scenario.expected}, got {result.actual_result} ({diff:+d})")
    
    return results


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def verbose_output():
    """Fixture to control verbose output in tests."""
    return True

@pytest.fixture 
def enable_ai_analysis():
    """Fixture to control whether AI analysis is captured."""
    return False