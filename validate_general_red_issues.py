#!/usr/bin/env python3

"""
Detailed validation of GENERAL_RED strategic issues.
This script analyzes the specific logic gaps in AI declaration for GENERAL_RED scenarios.
"""

from backend.engine.ai import (
    choose_declare_strategic, DeclarationContext, calculate_pile_room,
    assess_field_strength, analyze_opponent_patterns, find_all_valid_combos,
    filter_viable_combos, evaluate_opener_reliability
)
from backend.engine.piece import Piece


def parse_hand(hand_str):
    """Parse hand string to pieces."""
    hand_str = hand_str.strip('[]')
    piece_names = [name.strip(' "\'') for name in hand_str.split(',')]
    return [Piece(name) for name in piece_names]


def deep_analyze_scenario(scenario_id, hand_str, position, prev_decl, expected, notes):
    """Deep analysis of a specific scenario's strategic logic."""
    print(f"\n{'='*60}")
    print(f"DEEP ANALYSIS: {scenario_id}")
    print(f"{'='*60}")
    
    hand = parse_hand(hand_str)
    hand_display = [f"{p.kind}({p.point})" for p in hand]
    
    # Build context manually to match AI logic
    context = DeclarationContext(
        position_in_order=position,
        previous_declarations=prev_decl,
        is_starter=(position == 0),
        pile_room=calculate_pile_room(prev_decl),
        field_strength=assess_field_strength(prev_decl),
        has_general_red=any(p.name == "GENERAL" and p.point == 14 for p in hand),
        opponent_patterns=analyze_opponent_patterns(prev_decl)
    )
    
    print(f"Hand: {hand_display}")
    print(f"Context: pos={position}, prev_decl={prev_decl}")
    print(f"Pile room: {context.pile_room}, Field: {context.field_strength}")
    print(f"Has GENERAL_RED: {context.has_general_red}")
    print(f"Opponent patterns: {context.opponent_patterns}")
    
    # Find all combos
    all_combos = find_all_valid_combos(hand)
    strong_combos = [c for c in all_combos if c[0] in {
        "THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND", 
        "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"
    }]
    
    print(f"\nAll strong combos found: {len(strong_combos)}")
    for combo_type, pieces in strong_combos:
        piece_display = [f"{p.kind}({p.point})" for p in pieces]
        total_points = sum(p.point for p in pieces)
        print(f"  {combo_type}: {piece_display} (total: {total_points} points)")
    
    # Evaluate openers
    opener_score = 0
    has_reliable_opener = False
    opener_pieces = []
    for piece in hand:
        if piece.point >= 11:
            reliability = evaluate_opener_reliability(piece, context.field_strength)
            if reliability > 0:
                has_reliable_opener = True
                opener_pieces.append((piece, reliability))
                opener_score += reliability
    
    print(f"\nOpener analysis:")
    print(f"  Reliable opener: {has_reliable_opener}")
    print(f"  Opener score: {opener_score}")
    for piece, reliability in opener_pieces:
        print(f"    {piece.kind}({piece.point}): {reliability:.2f} reliability")
    
    # Filter viable combos
    viable_combos = filter_viable_combos(strong_combos, context, has_reliable_opener)
    print(f"\nViable combos after filtering: {len(viable_combos)}")
    for combo_type, pieces in viable_combos:
        piece_display = [f"{p.kind}({p.point})" for p in pieces]
        total_points = sum(p.point for p in pieces)
        print(f"  {combo_type}: {piece_display} (total: {total_points} points)")
    
    # Get AI result and analyze scoring logic
    result = choose_declare_strategic(
        hand=hand,
        is_first_player=(position == 0),
        position_in_order=position,
        previous_declarations=prev_decl,
        must_declare_nonzero=False,
        verbose=False
    )
    
    # Simulate scoring logic to understand the gap
    print(f"\nScoring analysis:")
    print(f"  AI Result: {result}")
    print(f"  Expected: {expected}")
    print(f"  Difference: {result - expected}")
    
    # Check for specific strategic issues
    print(f"\nStrategic issue analysis:")
    
    # Issue 1: Combo accumulation bug
    has_four_kind = any(c[0] == "FOUR_OF_A_KIND" for c in viable_combos)
    has_five_kind = any(c[0] == "FIVE_OF_A_KIND" for c in viable_combos)
    if context.has_general_red and (has_four_kind or has_five_kind):
        print(f"  ⚠️  COMBO ACCUMULATION BUG: Has GENERAL_RED + strong combos")
        print(f"      Current logic only uses strongest combo instead of accumulating")
        
        # Calculate what score SHOULD be
        total_pieces_used = 0
        theoretical_score = 0
        sorted_combos = sorted(viable_combos, key=lambda x: len(x[1]), reverse=True)
        
        for combo_type, pieces in sorted_combos:
            combo_size = len(pieces)
            if total_pieces_used + combo_size <= 8:
                total_pieces_used += combo_size
                
                if combo_type == "FIVE_OF_A_KIND":
                    theoretical_score += 5
                elif combo_type == "FOUR_OF_A_KIND":
                    theoretical_score += 4
                elif combo_type in ["THREE_OF_A_KIND", "STRAIGHT"]:
                    theoretical_score += 3
        
        theoretical_score += round(opener_score)
        theoretical_score = min(theoretical_score, context.pile_room)
        
        print(f"      Theoretical score with full combo accumulation: {theoretical_score}")
    
    # Issue 2: Multi-opener undervaluation
    if len(opener_pieces) >= 2:
        print(f"  ⚠️  MULTI-OPENER UNDERVALUATION: {len(opener_pieces)} premium openers")
        print(f"      Should provide strategic advantage beyond individual reliability scores")
    
    # Issue 3: Field strength advantage
    if context.has_general_red and context.field_strength == "weak" and all(d <= 1 for d in prev_decl):
        print(f"  ⚠️  FIELD STRENGTH ADVANTAGE: GENERAL_RED in very weak field")
        print(f"      Should enable additional pile wins through pure strength")
    
    print(f"\nNotes: {notes}")
    
    return result == expected


def main():
    """Analyze the 5 failing scenarios in detail."""
    failing_scenarios = [
        ("general_red_01", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
         2, [1, 0], 8, "GENERAL_RED + weak field enables FOUR_OF_A_KIND + STRAIGHT = 8 piles"),
        
        ("general_red_03", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [0, 1, 2], 3, "GENERAL_RED + ADVISOR_BLACK reliable regardless of field strength"),
        
        ("general_red_field_01", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED]",
         2, [0, 0], 2, "GENERAL_RED + very weak field = guaranteed, but hand only supports 2 piles"),
        
        ("general_red_combo_01", "[GENERAL_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
         2, [1, 2], 4, "GENERAL_RED provides control to play THREE_OF_A_KIND reliably"),
        
        ("general_red_combo_03", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED]",
         3, [0, 1, 1], 6, "GENERAL_RED + weak field enables FIVE_OF_A_KIND (5) + opener (1) = 6")
    ]
    
    print("DETAILED ANALYSIS OF FAILING GENERAL_RED SCENARIOS")
    print("=" * 60)
    
    correct_count = 0
    for scenario in failing_scenarios:
        correct = deep_analyze_scenario(*scenario)
        if correct:
            correct_count += 1
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {correct_count}/{len(failing_scenarios)} scenarios currently correct")
    print("Key strategic issues identified:")
    print("1. Combo accumulation bug (affects 3 scenarios)")
    print("2. Multi-opener undervaluation (affects 1 scenario)")
    print("3. Field strength advantage missing (affects 1 scenario)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()