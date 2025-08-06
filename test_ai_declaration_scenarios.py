#!/usr/bin/env python3
"""
Comprehensive AI Declaration Test Suite - Scenario-Based Framework

This module provides systematic testing of AI declaration strategy across all major
strategic scenarios, organized by category for better coverage and maintainability.

Test Categories:
- Position Strategy: Starter vs Non-starter behaviors
- Field Strength Response: Weak/Strong/Mixed field adaptations  
- Combo Opportunity Analysis: Viable combo detection and filtering
- Pile Room Constraints: Zero room, limited room, room mismatches
- Opener Reliability: Strong/marginal/no opener scenarios
- GENERAL_RED Special Cases: Game-changing scenarios
- Edge Cases & Constraints: Complex rule interactions

Total Tests: ~93 comprehensive scenarios vs original 18 examples
"""

import sys
import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable
from enum import Enum

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare


# ============================================================================
# Data Structures & Enums
# ============================================================================

class TestCategory(Enum):
    POSITION_STRATEGY = "position_strategy"
    FIELD_STRENGTH = "field_strength"
    COMBO_OPPORTUNITY = "combo_opportunity" 
    PILE_ROOM_CONSTRAINTS = "pile_room_constraints"
    OPENER_RELIABILITY = "opener_reliability"
    GENERAL_RED_SPECIAL = "general_red_special"
    EDGE_CASES = "edge_cases"
    BASELINE = "baseline"  # Original 18 tests


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


@dataclass 
class CategoryResults:
    """Results for an entire test category."""
    category: TestCategory
    total_tests: int
    passed: int
    failed: int
    results: List[TestResult]
    
    @property
    def success_rate(self) -> float:
        return (self.passed / self.total_tests) * 100 if self.total_tests > 0 else 0.0


@dataclass
class ComprehensiveReport:
    """Complete test suite results."""
    category_results: Dict[TestCategory, CategoryResults]
    total_tests: int
    total_passed: int
    total_failed: int
    baseline_maintained: bool  # All original 18 tests still pass
    
    @property
    def overall_success_rate(self) -> float:
        return (self.total_passed / self.total_tests) * 100 if self.total_tests > 0 else 0.0


# ============================================================================
# Utility Functions (from original test file)
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
    
    # Execute AI decision
    import time
    start_time = time.time()
    
    result = choose_declare(
        hand=hand,
        is_first_player=scenario.is_starter,
        position_in_order=scenario.position,
        previous_declarations=scenario.previous_decl,
        must_declare_nonzero=False,
        verbose=verbose,
        analysis_callback=capture_analysis_callback if enable_analysis else None
    )
    
    execution_time = time.time() - start_time
    
    # Check result
    passed = result == scenario.expected
    status = "✅ PASS" if passed else "❌ FAIL"
    
    if verbose:
        print(f"\nExpected: {scenario.expected}, Got: {result} - {status}")
        if not passed:
            print(f"⚠️  FAILURE in {scenario.strategic_focus}")
    
    return TestResult(
        scenario=scenario,
        actual_result=result,
        passed=passed,
        execution_time=execution_time,
        ai_analysis=analysis_data
    )


# ============================================================================
# Test Suite Class
# ============================================================================

class AIDeclarationTestSuite:
    """Comprehensive test suite for AI declaration strategy."""
    
    def __init__(self):
        self.scenarios: Dict[TestCategory, List[TestScenario]] = {}
        self._load_all_scenarios()
    
    def _load_all_scenarios(self):
        """Load all test scenarios organized by category."""
        # Initialize category containers
        for category in TestCategory:
            self.scenarios[category] = []
        
        # Load scenarios for each category
        self._load_baseline_scenarios()      # Original 18 tests
        self._load_position_strategy_scenarios()   # Position-based strategy
        self._load_field_strength_scenarios()      # Field strength responses  
        self._load_combo_opportunity_scenarios()   # Combo analysis
        self._load_pile_room_constraint_scenarios() # Room limitations
        self._load_opener_reliability_scenarios()  # Opener variations
        self._load_general_red_scenarios()         # GENERAL_RED special cases
        self._load_edge_case_scenarios()          # Complex constraints
    
    def _load_baseline_scenarios(self):
        """Load original 18 test scenarios for regression testing."""
        baseline_tests = [
            # Preserved from original test_ai_declaration.py
            ("baseline_01", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
             0, [], 4, "Strong Hand with Opener (As Starter)", True, "Starter advantage with opener + combo"),
            
            ("baseline_02", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
             2, [0, 1], 1, "Same Hand, Weak Field", False, "Non-starter in weak field"),
            
            ("baseline_03", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
             2, [5, 4], 0, "Same Hand, Strong Field (No Room)", False, "Pile room constraint override"),
            
            ("baseline_04", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
             0, [], 3, "Good Combos, No Opener (Starter)", True, "Starter enables combos without opener"),
            
            ("baseline_05", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
             2, [0, 1], 1, "Good Combos, No Opener (Weak Field)", False, "Weak field limits combo opportunity"),
            
            ("baseline_06", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
             2, [4, 5], 0, "Good Combos, Strong Field (No Room)", False, "Strong field + no room = zero declaration"),
            
            ("baseline_07", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             0, [], 2, "Multiple High Cards (Starter)", True, "Multiple opener assessment"),
            
            ("baseline_08", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             3, [2, 1, 3], 1, "Multiple High Cards (Last Player)", False, "Last player constraint handling"),
            
            ("baseline_09", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             0, [], 1, "Weak Hand (Starter)", True, "Starter advantage with weak hand"),
            
            ("baseline_10", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             3, [0, 0, 1], 2, "Weak Hand (Weak Field)", False, "Weak field enables medium pieces"),
            
            ("baseline_11", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
             0, [], 8, "Strong Combos (Starter)", True, "Maximum declaration with multiple combos"),
            
            ("baseline_12", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
             1, [5], 0, "Strong Combos (No Control)", False, "Great hand, wrong position"),
            
            ("baseline_13", "[ADVISOR_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_RED]",
             3, [3, 2, 1], 1, "Strategic Last Player", False, "Last player pile room limitation"),
            
            ("baseline_14", "[ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_RED, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
             1, [3], 1, "Mid-Strength Opener", False, "Single opponent with combos"),
            
            ("baseline_15", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK]",
             0, [], 6, "Double THREE_OF_A_KIND (Starter)", True, "Multiple combo types as starter"),
            
            ("baseline_16", "[GENERAL_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED]",
             2, [4, 3], 1, "Strong Singles (Limited Room)", False, "Strong opener limited by room"),
            
            ("baseline_17", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
             2, [1, 0], 5, "GENERAL_RED Game Changer", False, "GENERAL_RED transforms strategy"),
            
            ("baseline_18", "[ADVISOR_RED, ADVISOR_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             3, [2, 2, 1], 2, "Last Player Perfect Match", False, "Perfect pile room match as last player"),
        ]
        
        for i, (scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus) in enumerate(baseline_tests):
            self.scenarios[TestCategory.BASELINE].append(TestScenario(
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
    
    def _load_position_strategy_scenarios(self):
        """Load position-based strategy test scenarios."""
        # Starter Advantage scenarios (4 tests)
        starter_scenarios = [
            ("pos_starter_01", "[CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             0, [], 1, "Starter Enables Weak Straight", True, "Starter makes weak combo viable", DifficultyLevel.BASIC,
             "18-point straight becomes playable as starter"),
            
            ("pos_starter_02", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_BLACK]",
             0, [], 1, "Starter with Multiple Pairs", True, "Multiple small combos as starter", DifficultyLevel.INTERMEDIATE,
             "Two pairs (4 piles total) only viable as starter"),
            
            ("pos_starter_03", "[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED]",
             0, [], 7, "Starter: Opener + Combo", True, "Optimal opener-combo combination", DifficultyLevel.BASIC,
             "GENERAL (1) + THREE_OF_A_KIND (3) = 4 piles guaranteed"),
            
            ("pos_starter_04", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
             0, [], 6, "Starter with Medium Singles", True, "Starter advantage with borderline pieces", DifficultyLevel.INTERMEDIATE,
             "ELEPHANTs might win as starter, others too weak")
        ]
        
        for scenario_data in starter_scenarios:
            scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
            self.scenarios[TestCategory.POSITION_STRATEGY].append(TestScenario(
                scenario_id=scenario_id,
                category=TestCategory.POSITION_STRATEGY,
                subcategory="starter_advantage",
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
        
        # Non-Starter Adaptation scenarios (4 tests)  
        non_starter_scenarios = [
            ("pos_nonstarter_01", "[CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             2, [2, 3], 0, "Same Weak Straight, No Control", False, "Non-starter makes combo unviable", DifficultyLevel.BASIC,
             "Same hand as pos_starter_01, but non-starter = no combo opportunity"),
            
            ("pos_nonstarter_02", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_BLACK]",
             1, [4], 0, "Pairs Without Control", False, "Multiple combos need control", DifficultyLevel.INTERMEDIATE,
             "Strong opponent (4) will control - pairs become unplayable"),
            
            ("pos_nonstarter_03", "[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED]",
             2, [2, 3], 3, "Non-starter: Opener Only", False, "Combo unviable without control", DifficultyLevel.INTERMEDIATE,
             "GENERAL reliable (1), but THREE_OF_A_KIND needs opportunity"),
            
            ("pos_nonstarter_04", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
             1, [3], 0, "Medium Singles, No Control", False, "Non-starter with medium pieces", DifficultyLevel.BASIC,
             "Same hand as pos_starter_04, but opponent controls = 0 piles")
        ]
        
        for scenario_data in non_starter_scenarios:
            scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
            self.scenarios[TestCategory.POSITION_STRATEGY].append(TestScenario(
                scenario_id=scenario_id,
                category=TestCategory.POSITION_STRATEGY,
                subcategory="non_starter_adaptation",
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
        
        # Last Player Constraint scenarios (4 tests)
        last_player_scenarios = [
            ("pos_last_01", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
             3, [3, 2, 1], 1, "Last Player: Forced High Declaration", False, "Cannot declare 2, forced to 3", DifficultyLevel.ADVANCED,
             "Wants 2 piles, but 6+2=8 forbidden, must declare 3"),
            
            ("pos_last_02", "[SOLDIER_RED, SOLDIER_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
             3, [2, 3, 2], 0, "Last Player: Forced Zero", False, "Cannot declare 1, only 0 viable", DifficultyLevel.BASIC,
             "Wants 1 pile, but 7+1=8 forbidden, forced to 0"),
            
            ("pos_last_03", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             3, [1, 1, 4], 1, "Last Player: Multiple Constraints", False, "2 works, but close to constraint", DifficultyLevel.ADVANCED,
             "Could declare 2 (6+2≠8), good match for hand strength"),
            
            ("pos_last_04", "[ADVISOR_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
             3, [4, 3, 0], 0, "Last Player: Conservative Choice", False, "Under-declare due to constraint pressure", DifficultyLevel.INTERMEDIATE,
             "Could declare 1 (7+1≠8), but complex constraint environment")
        ]
        
        for scenario_data in last_player_scenarios:
            scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
            self.scenarios[TestCategory.POSITION_STRATEGY].append(TestScenario(
                scenario_id=scenario_id,
                category=TestCategory.POSITION_STRATEGY,
                subcategory="last_player_constraints",
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
    
    # Placeholder methods for other categories - will be implemented in subsequent tasks
    def _load_field_strength_scenarios(self):
        """Load field strength response scenarios."""
        # Weak Field Exploitation scenarios (5 tests)
        weak_field_scenarios = [
            ("field_weak_01", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
             2, [0, 0], 3, "Medium Pieces vs Very Weak Field", False, "Weak field enables medium pieces", DifficultyLevel.BASIC,
             "Previous [0,0] = opponents have terrible hands, medium pieces become viable"),
            
            ("field_weak_02", "[ADVISOR_RED, CHARIOT_RED, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
             1, [1], 2, "Opener in Weak Field", False, "Weak field boosts opener reliability", DifficultyLevel.INTERMEDIATE,
             "ADVISOR becomes very reliable in weak field (1.0 score vs normal 0.85)"),
            
            ("field_weak_03", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             3, [0, 1, 0], 2, "Weak Combo in Weak Field", False, "18-point straight might work in weak field", DifficultyLevel.ADVANCED,
             "Normally unviable 18-point straight becomes consideration in very weak field"),
            
            ("field_weak_04", "[GENERAL_BLACK, CHARIOT_RED, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
             2, [0, 1], 2, "Strong Opener vs Weak Field", False, "GENERAL dominates weak field", DifficultyLevel.BASIC,
             "GENERAL + weak field = very reliable, can afford aggressive declaration"),
            
            ("field_weak_05", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, ELEPHANT_RED, ELEPHANT_BLACK]",
             1, [0], 3, "Multiple Medium vs Weak", False, "Multiple medium pieces in weak field", DifficultyLevel.INTERMEDIATE,
             "No opener but multiple 6-10 point pieces can win vs weak opponents")
        ]
        
        for scenario_data in weak_field_scenarios:
            scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
            self.scenarios[TestCategory.FIELD_STRENGTH].append(TestScenario(
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
        
        # Strong Field Caution scenarios (5 tests)
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
            self.scenarios[TestCategory.FIELD_STRENGTH].append(TestScenario(
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
        
        # Mixed/Borderline Field scenarios (5 tests)
        mixed_field_scenarios = [
            ("field_mixed_01", "[ADVISOR_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
             2, [1, 3], 1, "Mixed Field: Weak + Strong", False, "Mixed signals complicate assessment", DifficultyLevel.ADVANCED,
             "One weak (1), one strong (3) opponent - field assessment unclear"),
            
            ("field_mixed_02", "[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_RED, ELEPHANT_RED, ELEPHANT_BLACK]",
             1, [2], 2, "Borderline Normal Field", False, "Normal field with strong opener", DifficultyLevel.INTERMEDIATE,
             "Previous [2] = borderline normal field, GENERAL should be reliable"),
            
            ("field_mixed_03", "[CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_BLACK]",
             3, [2, 2, 2], 1, "Consistent Normal Field", False, "All opponents similar strength", DifficultyLevel.BASIC,
             "Previous [2,2,2] = consistent normal field, weak combo marginal"),
            
            ("field_mixed_04", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]",
             2, [0, 4], 1, "Extreme Mixed Field", False, "Very weak + very strong opponent", DifficultyLevel.ADVANCED,
             "Previous [0,4] = extreme difference, strategy unclear"),
            
            ("field_mixed_05", "[ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_RED, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED]",
             1, [3], 1, "Single Strong Opponent", False, "One strong opponent affects strategy", DifficultyLevel.INTERMEDIATE,
             "Previous [3] = single strong opponent likely has combos, will control turns")
        ]
        
        for scenario_data in mixed_field_scenarios:
            scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
            self.scenarios[TestCategory.FIELD_STRENGTH].append(TestScenario(
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
    
    def _load_combo_opportunity_scenarios(self):
        """Load combo opportunity analysis scenarios."""
        # Viable Combo Detection scenarios (6 tests)
        viable_combo_scenarios = [
            ("combo_viable_01", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
             0, [], 6, "THREE_OF_A_KIND + STRAIGHT (Starter)", True, "Starter enables both combos", DifficultyLevel.BASIC,
             "RED THREE_OF_A_KIND (3) + BLACK STRAIGHT (3) = 6 piles as starter"),
            
            ("combo_viable_02", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
             2, [2, 3], 0, "Same Combos, No Control", False, "Non-starter makes combos unviable", DifficultyLevel.INTERMEDIATE,
             "Same hand as combo_viable_01 but no control = 0 piles"),
            
            ("combo_viable_03", "[ADVISOR_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_BLACK, ELEPHANT_BLACK]",
             1, [2], 1, "Opener vs Combo Choice", False, "Opener reliable, combo questionable", DifficultyLevel.ADVANCED,
             "ADVISOR (1) reliable but THREE_OF_A_KIND needs opportunity - choose opener"),
            
            ("combo_viable_04", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_RED, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_BLACK, HORSE_BLACK]",
             0, [], 3, "21-Point Straight (Starter)", True, "Strong straight viable as starter", DifficultyLevel.BASIC,
             "21-point RED STRAIGHT above quality threshold, guaranteed as starter"),
            
            ("combo_viable_05", "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_RED, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_BLACK, HORSE_BLACK]",
             2, [0, 1], 0, "Strong Straight vs Weak Field", False, "Even strong combo needs opportunity", DifficultyLevel.ADVANCED,
             "21-point straight but [0,1] = no combo opportunity from opponents"),
            
            ("combo_viable_06", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
             1, [4], 0, "FOUR_OF_A_KIND vs Strong Control", False, "Great combo, wrong position", DifficultyLevel.INTERMEDIATE,
             "FOUR_OF_A_KIND RED but opponent (4) will control turns")
        ]
        
        for scenario_data in viable_combo_scenarios:
            scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
            self.scenarios[TestCategory.COMBO_OPPORTUNITY].append(TestScenario(
                scenario_id=scenario_id,
                category=TestCategory.COMBO_OPPORTUNITY,
                subcategory="viable_combo_detection",
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
        
        # Quality Threshold scenarios (6 tests)
        quality_threshold_scenarios = [
            ("combo_quality_01", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, ELEPHANT_BLACK, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_BLACK]",
             0, [], 6, "THREE_OF_A_KIND + STRAIGHT (Starter)", True, "Both combos viable as starter", DifficultyLevel.BASIC,
             "RED THREE_OF_A_KIND (3) + BLACK STRAIGHT (3) = 6 piles as starter"),
            
            ("combo_quality_02", "[CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, ELEPHANT_RED, ELEPHANT_BLACK, ADVISOR_RED]",
             0, [], 3, "18-Point Straight Threshold", True, "Minimum viable straight", DifficultyLevel.INTERMEDIATE,
             "BLACK STRAIGHT exactly at 18-point threshold, marginal but viable as starter"),
            
            ("combo_quality_03", "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             0, [], 0, "Different Color Singles Only", True, "No valid pairs - different colors", DifficultyLevel.BASIC,
             "ELEPHANT_RED+BLACK, CHARIOT_RED+BLACK, HORSE_RED+BLACK - all different colors, no pairs possible"),
            
            ("combo_quality_04", "[CANNON_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, ADVISOR_BLACK]",
             0, [], 0, "Different Color Singles Only", True, "No valid pairs - different colors", DifficultyLevel.INTERMEDIATE,
             "CANNON_RED+BLACK, SOLDIER_RED+BLACK - all different colors, no pairs possible"),
            
            ("combo_quality_05", "[GENERAL_RED, HORSE_RED, CANNON_RED, SOLDIER_RED, ELEPHANT_BLACK, CHARIOT_BLACK, HORSE_BLACK, SOLDIER_BLACK]",
             0, [], 1, "Marginal Straight with Opener", True, "Opener vs weak straight", DifficultyLevel.ADVANCED,
             "GENERAL reliable (1), weak RED partial straight unviable"),
            
            ("combo_quality_06", "[ADVISOR_RED, ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
             0, [], 4, "STRAIGHT + Opener Strategy", True, "Starter enables combo + opener", DifficultyLevel.ADVANCED,
             "BLACK STRAIGHT (3) + ADVISOR_RED opener (1) = 4 piles, forfeit ADVISOR_BLACK + ELEPHANT_BLACK")
        ]
        
        for scenario_data in quality_threshold_scenarios:
            scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
            self.scenarios[TestCategory.COMBO_OPPORTUNITY].append(TestScenario(
                scenario_id=scenario_id,
                category=TestCategory.COMBO_OPPORTUNITY,
                subcategory="quality_thresholds",
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
        
        # Multi-Combo Hand scenarios (6 tests) 
        multi_combo_scenarios = [
            ("combo_multi_01", "[SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
             0, [], 6, "Overlapping Soldier Combos", True, "Multiple combo types from soldiers", DifficultyLevel.ADVANCED,
             "RED pair + BLACK THREE_OF_A_KIND + RED STRAIGHT = complex combo selection"),
            
            ("combo_multi_02", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
             0, [], 8, "FOUR_OF_A_KIND + STRAIGHT + Opener", True, "Maximum combos with opener", DifficultyLevel.BASIC,
             "GENERAL(1) + FOUR_OF_A_KIND(4) + STRAIGHT(3) = 8 piles maximum"),
            
            ("combo_multi_03", "[ELEPHANT_RED, ELEPHANT_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             0, [], 5, "ELEPHANT PAIR + BLACK STRAIGHT", True, "Pair and straight combos", DifficultyLevel.INTERMEDIATE,
             "ELEPHANT_RED PAIR (2) + BLACK STRAIGHT (3) = 5 piles as starter"),
            
            ("combo_multi_04", "[CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
             0, [], 6, "Three Pairs", True, "Multiple pair combinations", DifficultyLevel.INTERMEDIATE,
             "CHARIOT pair + HORSE pair + CANNON pair all viable"),
            
            ("combo_multi_05", "[ADVISOR_RED, CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
             1, [3], 4, "Strong Opener + STRAIGHT Combo", False, "Opener enables straight opportunity", DifficultyLevel.ADVANCED,
             "ADVISOR_RED opener (1) + RED STRAIGHT (3) = 4 piles, opener creates control"),
            
            ("combo_multi_06", "[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
             2, [1, 0], 8, "FOUR_OF_A_KIND + STRAIGHT Enabled", False, "GENERAL enables everything", DifficultyLevel.BASIC,
             "GENERAL + weak field enables FOUR_OF_A_KIND + STRAIGHT = 8 piles")
        ]
        
        for scenario_data in multi_combo_scenarios:
            scenario_id, hand_str, position, prev_decl, expected, description, is_starter, focus, difficulty, notes = scenario_data
            self.scenarios[TestCategory.COMBO_OPPORTUNITY].append(TestScenario(
                scenario_id=scenario_id,
                category=TestCategory.COMBO_OPPORTUNITY,
                subcategory="multi_combo_hands",
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
    
    def _load_pile_room_constraint_scenarios(self):
        """Load pile room constraint scenarios."""
        # Zero Pile Room scenarios (4 tests)
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
            self.scenarios[TestCategory.PILE_ROOM_CONSTRAINTS].append(TestScenario(
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
        
        # Limited Room scenarios (4 tests)
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
            self.scenarios[TestCategory.PILE_ROOM_CONSTRAINTS].append(TestScenario(
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
        
        # Room vs Hand Mismatch scenarios (4 tests)
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
            self.scenarios[TestCategory.PILE_ROOM_CONSTRAINTS].append(TestScenario(
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
    
    def _load_opener_reliability_scenarios(self):
        """Load opener reliability scenarios."""
        # Strong Openers scenarios (5 tests)
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
            self.scenarios[TestCategory.OPENER_RELIABILITY].append(TestScenario(
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
        
        # Marginal Openers scenarios (5 tests)
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
            self.scenarios[TestCategory.OPENER_RELIABILITY].append(TestScenario(
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
        
        # No Opener scenarios (5 tests)
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
            self.scenarios[TestCategory.OPENER_RELIABILITY].append(TestScenario(
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
    
    def _load_general_red_scenarios(self):
        """Load GENERAL_RED special case scenarios."""
        # Game Changer scenarios (3 tests)
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
            self.scenarios[TestCategory.GENERAL_RED_SPECIAL].append(TestScenario(
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
        
        # Field Strength Interaction scenarios (3 tests)
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
            self.scenarios[TestCategory.GENERAL_RED_SPECIAL].append(TestScenario(
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
        
        # Combo Enablement scenarios (3 tests)
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
            self.scenarios[TestCategory.GENERAL_RED_SPECIAL].append(TestScenario(
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
    
    def _load_edge_case_scenarios(self):
        """Load edge case and constraint scenarios."""
        # Must-Declare-Nonzero scenarios (4 tests)
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
            self.scenarios[TestCategory.EDGE_CASES].append(TestScenario(
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
        
        # Multiple Forbidden Values scenarios (4 tests)
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
            self.scenarios[TestCategory.EDGE_CASES].append(TestScenario(
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
        
        # Boundary Conditions scenarios (4 tests)
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
            self.scenarios[TestCategory.EDGE_CASES].append(TestScenario(
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
    
    # ========================================================================
    # Test Execution Methods
    # ========================================================================
    
    def run_baseline_tests(self, verbose: bool = True) -> CategoryResults:
        """Run all baseline tests (original 18) to ensure no regression."""
        if verbose:
            print(f"\n🔄 Running BASELINE Tests (Regression Validation)")
            print(f"{'='*80}")
        
        results = []
        for scenario in self.scenarios[TestCategory.BASELINE]:
            result = execute_test_scenario(scenario, verbose=verbose)
            results.append(result)
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        category_result = CategoryResults(
            category=TestCategory.BASELINE,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            results=results
        )
        
        if verbose:
            self._print_category_summary(category_result)
        
        return category_result
    
    def run_position_strategy_tests(self, verbose: bool = True) -> CategoryResults:
        """Run all position strategy tests."""
        if verbose:
            print(f"\n🎯 Running POSITION STRATEGY Tests")
            print(f"{'='*80}")
        
        results = []
        for scenario in self.scenarios[TestCategory.POSITION_STRATEGY]:
            result = execute_test_scenario(scenario, verbose=verbose)
            results.append(result)
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        category_result = CategoryResults(
            category=TestCategory.POSITION_STRATEGY,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            results=results
        )
        
        if verbose:
            self._print_category_summary(category_result)
        
        return category_result
    
    def run_field_strength_tests(self, verbose: bool = True) -> CategoryResults:
        """Run all field strength response tests."""
        if verbose:
            print(f"\n🌡️ Running FIELD STRENGTH RESPONSE Tests")
            print(f"{'='*80}")
        
        results = []
        for scenario in self.scenarios[TestCategory.FIELD_STRENGTH]:
            result = execute_test_scenario(scenario, verbose=verbose)
            results.append(result)
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        category_result = CategoryResults(
            category=TestCategory.FIELD_STRENGTH,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            results=results
        )
        
        if verbose:
            self._print_category_summary(category_result)
        
        return category_result
    
    def run_combo_opportunity_tests(self, verbose: bool = True) -> CategoryResults:
        """Run all combo opportunity analysis tests."""
        if verbose:
            print(f"\n🎲 Running COMBO OPPORTUNITY ANALYSIS Tests")
            print(f"{'='*80}")
        
        results = []
        for scenario in self.scenarios[TestCategory.COMBO_OPPORTUNITY]:
            result = execute_test_scenario(scenario, verbose=verbose)
            results.append(result)
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        category_result = CategoryResults(
            category=TestCategory.COMBO_OPPORTUNITY,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            results=results
        )
        
        if verbose:
            self._print_category_summary(category_result)
        
        return category_result
    
    def run_pile_room_constraint_tests(self, verbose: bool = True) -> CategoryResults:
        """Run all pile room constraint tests."""
        if verbose:
            print(f"\n📦 Running PILE ROOM CONSTRAINTS Tests")
            print(f"{'='*80}")
        
        results = []
        for scenario in self.scenarios[TestCategory.PILE_ROOM_CONSTRAINTS]:
            result = execute_test_scenario(scenario, verbose=verbose)
            results.append(result)
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        category_result = CategoryResults(
            category=TestCategory.PILE_ROOM_CONSTRAINTS,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            results=results
        )
        
        if verbose:
            self._print_category_summary(category_result)
        
        return category_result
    
    def run_opener_reliability_tests(self, verbose: bool = True) -> CategoryResults:
        """Run all opener reliability tests."""
        if verbose:
            print(f"\n🎖️ Running OPENER RELIABILITY Tests")
            print(f"{'='*80}")
        
        results = []
        for scenario in self.scenarios[TestCategory.OPENER_RELIABILITY]:
            result = execute_test_scenario(scenario, verbose=verbose)
            results.append(result)
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        category_result = CategoryResults(
            category=TestCategory.OPENER_RELIABILITY,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            results=results
        )
        
        if verbose:
            self._print_category_summary(category_result)
        
        return category_result
    
    def run_general_red_tests(self, verbose: bool = True) -> CategoryResults:
        """Run all GENERAL_RED special case tests."""
        if verbose:
            print(f"\n👑 Running GENERAL_RED SPECIAL CASES Tests")
            print(f"{'='*80}")
        
        results = []
        for scenario in self.scenarios[TestCategory.GENERAL_RED_SPECIAL]:
            result = execute_test_scenario(scenario, verbose=verbose)
            results.append(result)
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        category_result = CategoryResults(
            category=TestCategory.GENERAL_RED_SPECIAL,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            results=results
        )
        
        if verbose:
            self._print_category_summary(category_result)
        
        return category_result
    
    def run_edge_case_tests(self, verbose: bool = True) -> CategoryResults:
        """Run all edge case and constraint tests."""
        if verbose:
            print(f"\n⚡ Running EDGE CASES & CONSTRAINTS Tests")
            print(f"{'='*80}")
        
        results = []
        for scenario in self.scenarios[TestCategory.EDGE_CASES]:
            result = execute_test_scenario(scenario, verbose=verbose)
            results.append(result)
        
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        category_result = CategoryResults(
            category=TestCategory.EDGE_CASES,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            results=results
        )
        
        if verbose:
            self._print_category_summary(category_result)
        
        return category_result
    
    def run_all_scenarios(self, verbose: bool = True) -> ComprehensiveReport:
        """Run all test scenarios and generate comprehensive report."""
        if verbose:
            print(f"\n🚀 AI DECLARATION TEST SUITE - COMPREHENSIVE ANALYSIS")
            print(f"{'='*80}")
        
        category_results = {}
        
        # Run baseline tests first (regression validation)
        baseline_results = self.run_baseline_tests(verbose)
        category_results[TestCategory.BASELINE] = baseline_results
        
        # Run position strategy tests
        position_results = self.run_position_strategy_tests(verbose)
        category_results[TestCategory.POSITION_STRATEGY] = position_results
        
        # Run field strength tests
        field_results = self.run_field_strength_tests(verbose)
        category_results[TestCategory.FIELD_STRENGTH] = field_results
        
        # Run combo opportunity tests
        combo_results = self.run_combo_opportunity_tests(verbose)
        category_results[TestCategory.COMBO_OPPORTUNITY] = combo_results
        
        # Run pile room constraint tests
        room_results = self.run_pile_room_constraint_tests(verbose)
        category_results[TestCategory.PILE_ROOM_CONSTRAINTS] = room_results
        
        # Run opener reliability tests
        opener_results = self.run_opener_reliability_tests(verbose)
        category_results[TestCategory.OPENER_RELIABILITY] = opener_results
        
        # Run GENERAL_RED special case tests
        general_red_results = self.run_general_red_tests(verbose)
        category_results[TestCategory.GENERAL_RED_SPECIAL] = general_red_results
        
        # Run edge case and constraint tests
        edge_results = self.run_edge_case_tests(verbose)
        category_results[TestCategory.EDGE_CASES] = edge_results
        
        # Calculate totals
        total_tests = sum(cr.total_tests for cr in category_results.values())
        total_passed = sum(cr.passed for cr in category_results.values())
        total_failed = sum(cr.failed for cr in category_results.values())
        
        # Check if baseline maintained
        baseline_maintained = baseline_results.failed == 0
        
        report = ComprehensiveReport(
            category_results=category_results,
            total_tests=total_tests,
            total_passed=total_passed,
            total_failed=total_failed,
            baseline_maintained=baseline_maintained
        )
        
        if verbose:
            self._print_comprehensive_summary(report)
        
        return report
    
    def _print_category_summary(self, result: CategoryResults):
        """Print summary for a single category."""
        print(f"\n📊 {result.category.value.upper()} SUMMARY:")
        print(f"   Tests: {result.total_tests}")
        print(f"   Passed: {result.passed} ✅")
        print(f"   Failed: {result.failed} ❌")
        print(f"   Success Rate: {result.success_rate:.1f}%")
        
        if result.failed > 0:
            print(f"   Failed Tests:")
            for test_result in result.results:
                if not test_result.passed:
                    print(f"     - {test_result.scenario.scenario_id}: {test_result.scenario.description}")
    
    def _print_comprehensive_summary(self, report: ComprehensiveReport):
        """Print comprehensive test suite summary."""
        print(f"\n🏆 COMPREHENSIVE TEST RESULTS")
        print(f"{'='*80}")
        print(f"Total Tests: {report.total_tests}")
        print(f"Total Passed: {report.total_passed} ✅")
        print(f"Total Failed: {report.total_failed} ❌")
        print(f"Overall Success Rate: {report.overall_success_rate:.1f}%")
        print(f"Baseline Maintained: {'✅ YES' if report.baseline_maintained else '❌ NO'}")
        
        print(f"\n📋 BY CATEGORY:")
        for category, results in report.category_results.items():
            status = "✅" if results.failed == 0 else "❌"
            print(f"   {status} {category.value}: {results.passed}/{results.total_tests} ({results.success_rate:.1f}%)")
        
        if not report.baseline_maintained:
            print(f"\n⚠️  REGRESSION DETECTED: Baseline tests failed!")
            print(f"   Review baseline failures before proceeding with new scenarios.")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main test suite execution."""
    suite = AIDeclarationTestSuite()
    
    print("AI Declaration Test Suite - Scenario-Based Framework")
    print("=" * 80)
    print(f"Loaded Scenarios:")
    for category in TestCategory:
        count = len(suite.scenarios[category])
        print(f"  {category.value}: {count} tests")
    
    # Run comprehensive test suite
    report = suite.run_all_scenarios(verbose=True)
    
    # Return appropriate exit code
    return 0 if report.baseline_maintained and report.total_failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)