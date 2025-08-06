#!/usr/bin/env python3
"""
Test script for AI declaration strategic implementation.
Tests all 18 examples from AI_DECLARATION_EXAMPLES.md
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare


def create_piece(name: str, color: str) -> Piece:
    """Create a piece from name and color."""
    # Extract base name (remove color suffix if present)
    base_name = name.replace("_RED", "").replace("_BLACK", "")
    
    # Create the kind string
    kind = f"{base_name}_{color}"
    
    return Piece(kind)


def parse_hand(hand_str: str) -> list:
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


def test_example(example_num: int, hand_str: str, position: int, 
                 previous_decl: list, expected: int, description: str,
                 is_starter: bool = False, enable_analysis: bool = False):
    """
    Test a single example with optional analysis capture.
    
    Args:
        example_num: Test case number
        hand_str: String representation of hand pieces
        position: Position in turn order (0-3)
        previous_decl: Previous player declarations
        expected: Expected AI decision
        description: Test case description
        is_starter: Whether this player starts the round
        enable_analysis: Whether to capture and return analysis data
        
    Returns:
        bool: Test passed (backward compatibility)
        or tuple: (bool, AIDecisionAnalysis) when analysis enabled
    """
    print(f"\n{'='*60}")
    print(f"Example {example_num}: {description}")
    print(f"{'='*60}")
    
    # Parse hand
    hand = parse_hand(hand_str)
    
    # Print bot's hand with pieces ordered by color then rank
    def sort_pieces_by_color_and_rank(pieces):
        """Sort pieces by color (RED first), then by point value (highest first)."""
        return sorted(pieces, key=lambda p: (p.color != "RED", -p.point))
    
    sorted_hand = sort_pieces_by_color_and_rank(hand)
    hand_summary = ", ".join(f"{piece.kind}" for piece in sorted_hand)
    print(f"🃏 Bot's Hand: [{hand_summary}]")
    print(f"📊 Position: {position} ({'Starter' if is_starter else 'Non-starter'})")
    print(f"📋 Previous Declarations: {previous_decl}")
    
    # Analysis capture setup (if enabled)
    analysis_data = None
    captured_verbose_output = []
    
    def capture_analysis_callback(data):
        """Callback to capture AI analysis data."""
        nonlocal analysis_data
        analysis_data = data
    
    def capture_verbose_output(text):
        """Capture verbose output for analysis parsing."""
        captured_verbose_output.append(text)
    
    # Temporarily redirect print if analysis is enabled
    original_print = print
    if enable_analysis:
        def analysis_print(*args, **kwargs):
            # Store output for analysis
            output = ' '.join(str(arg) for arg in args)
            captured_verbose_output.append(output)
            # Still print normally
            original_print(*args, **kwargs)
        
        # Temporarily replace print function
        import builtins
        builtins.print = analysis_print
    
    try:
        # Call AI with optional analysis callback
        result = choose_declare(
            hand=hand,
            is_first_player=is_starter,
            position_in_order=position,
            previous_declarations=previous_decl,
            must_declare_nonzero=False,
            verbose=True,
            analysis_callback=capture_analysis_callback if enable_analysis else None
        )
    finally:
        # Restore original print function
        if enable_analysis:
            builtins.print = original_print
    
    # Check result
    status = "✅ PASS" if result == expected else "❌ FAIL"
    print(f"\nExpected: {expected}, Got: {result} - {status}")
    
    test_passed = result == expected
    
    # Generate analysis if requested
    if enable_analysis and analysis_data:
        # Combine captured verbose output into single string
        verbose_output = '\n'.join(captured_verbose_output)
        
        # Import analysis functions
        from backend.engine.ai_analysis import capture_ai_decision_data
        
        # Create comprehensive analysis
        analysis = capture_ai_decision_data(
            hand=hand,
            position_in_order=position,
            is_starter=is_starter,
            previous_declarations=previous_decl,
            decision_type='declare',
            verbose_output=verbose_output,
            final_result=result,
            expected_result=expected,
            test_scenario=f"Example {example_num}: {description}",
            must_declare_nonzero=False
        )
        
        return test_passed, analysis
    
    return test_passed


def run_all_tests():
    """Run all 18 test examples."""
    tests = [
        # Example 1
        (1, "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         0, [], 4, "Strong Hand with Opener (As Starter)", True),
        
        # Example 2
        (2, "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [0, 1], 1, "Same Hand, Weak Field", False),
        
        # Example 3
        (3, "[ADVISOR_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [5, 4], 0, "Same Hand, Strong Field (No Room)", False),
        
        # Example 4
        (4, "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         0, [], 3, "Good Combos, No Opener (Starter)", True),
        
        # Example 5
        (5, "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [0, 1], 1, "Good Combos, No Opener (Weak Field)", False),
        
        # Example 6
        (6, "[CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK]",
         2, [4, 5], 0, "Good Combos, Strong Field (No Room)", False),
        
        # Example 7
        (7, "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 2, "Multiple High Cards (Starter)", True),
        
        # Example 8
        (8, "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [2, 1, 3], 1, "Multiple High Cards (Last Player)", False),
        
        # Example 9
        (9, "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         0, [], 1, "Weak Hand (Starter)", True),
        
        # Example 10
        (10, "[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [0, 0, 1], 2, "Weak Hand (Weak Field)", False),
        
        # Example 11
        (11, "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         0, [], 8, "Strong Combos (Starter)", True),
        
        # Example 12
        (12, "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]",
         1, [5], 0, "Strong Combos (No Control)", False),
        
        # Example 13
        (13, "[ADVISOR_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_RED]",
         3, [3, 2, 1], 1, "Strategic Last Player", False),
        
        # Example 14
        (14, "[ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_RED, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
         1, [3], 1, "Mid-Strength Opener", False),
        
        # Example 15
        (15, "[SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_BLACK]",
         0, [], 6, "Double THREE_OF_A_KIND (Starter)", True),
        
        # Example 16
        (16, "[GENERAL_BLACK, ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED]",
         2, [4, 3], 1, "Strong Singles (Limited Room)", False),
        
        # Example 17
        (17, "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
         2, [1, 0], 5, "GENERAL_RED Game Changer", False),
        
        # Example 18
        (18, "[ADVISOR_RED, ADVISOR_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [2, 2, 1], 2, "Last Player Perfect Match", False),
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test_example(*test):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)