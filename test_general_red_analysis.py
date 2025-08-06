#!/usr/bin/env python3

"""
Analysis script for GENERAL_RED_SPECIAL test scenarios.
"""

from backend.engine.ai import choose_declare_strategic, assess_field_strength, find_all_valid_combos
from backend.engine.piece import Piece


def parse_hand(hand_str):
    """Parse hand string to pieces."""
    # Remove brackets and split by comma
    hand_str = hand_str.strip('[]')
    piece_names = [name.strip(' "\'') for name in hand_str.split(',')]
    return [Piece(name) for name in piece_names]


def analyze_scenario(scenario_id, hand_str, position, prev_decl, expected, notes):
    """Analyze a single scenario."""
    hand = parse_hand(hand_str)
    
    # Get AI result
    result = choose_declare_strategic(
        hand=hand,
        is_first_player=(position == 0),
        position_in_order=position,
        previous_declarations=prev_decl,
        must_declare_nonzero=False,
        verbose=False
    )
    
    # Calculate context
    pile_room = 8 - sum(prev_decl)
    field_strength = assess_field_strength(prev_decl)
    has_general_red = any(p.kind == "GENERAL_RED" for p in hand)
    
    # Find combos
    all_combos = find_all_valid_combos(hand)
    strong_combos = [c for c in all_combos if c[0] in {
        "THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND", 
        "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"
    }]
    
    # Analyze hand composition
    hand_display = [f"{p.kind}({p.point})" for p in hand]
    strong_pieces = [p for p in hand if p.point >= 11]
    combo_counts = {}
    for combo_type, pieces in strong_combos:
        if combo_type not in combo_counts:
            combo_counts[combo_type] = []
        combo_counts[combo_type].append(len(pieces))
    
    print(f"\n=== {scenario_id} ===")
    print(f"Expected: {expected}, Got: {result}, Diff: {result - expected}")
    print(f"Hand: {hand_display}")
    print(f"Context: pos={position}, prev_decl={prev_decl}, pile_room={pile_room}, field={field_strength}")
    print(f"Has GENERAL_RED: {has_general_red}, Strong pieces: {len(strong_pieces)}")
    if combo_counts:
        print(f"Combos found: {dict(combo_counts)}")
    else:
        print("No strong combos found")
    print(f"Notes: {notes}")
    
    return result == expected


def main():
    """Run analysis on all GENERAL_RED scenarios."""
    print("GENERAL_RED_SPECIAL Scenario Analysis")
    print("=" * 50)
    
    # Game Changer scenarios
    game_changer_scenarios = [
        ("general_red_01", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]",
         2, [1, 0], 8, "GENERAL_RED + weak field enables FOUR_OF_A_KIND + STRAIGHT = 8 piles"),
        
        ("general_red_02", "[GENERAL_RED, CHARIOT_RED, HORSE_RED, CANNON_RED, SOLDIER_BLACK, SOLDIER_BLACK, ELEPHANT_RED, ELEPHANT_BLACK]",
         1, [1], 4, "GENERAL_RED acts like starter, enables STRAIGHT in weak field"),
        
        ("general_red_03", "[GENERAL_RED, ADVISOR_BLACK, ELEPHANT_RED, CHARIOT_BLACK, HORSE_RED, CANNON_BLACK, SOLDIER_RED, SOLDIER_BLACK]",
         3, [0, 1, 2], 3, "GENERAL_RED + ADVISOR_BLACK reliable regardless of field strength")
    ]
    
    # Field Strength Interaction scenarios
    field_interaction_scenarios = [
        ("general_red_field_01", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED]",
         2, [0, 0], 2, "GENERAL_RED + very weak field = guaranteed, but hand only supports 2 piles"),
        
        ("general_red_field_02", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED]",
         1, [5], 1, "GENERAL_RED reliable but strong opponent (5) will control, limits combo opportunities"),
        
        ("general_red_field_03", "[GENERAL_RED, ELEPHANT_BLACK, CHARIOT_RED, HORSE_BLACK, CANNON_RED, SOLDIER_RED, SOLDIER_BLACK, ELEPHANT_RED]",
         2, [2, 3], 1, "GENERAL_RED reliable in normal field, but no special advantages")
    ]
    
    # Combo Enablement scenarios
    combo_enablement_scenarios = [
        ("general_red_combo_01", "[GENERAL_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_BLACK]",
         2, [1, 2], 4, "GENERAL_RED provides control to play THREE_OF_A_KIND reliably"),
        
        ("general_red_combo_02", "[GENERAL_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK, ELEPHANT_RED, SOLDIER_RED, SOLDIER_BLACK, ADVISOR_RED]",
         1, [2], 2, "GENERAL_RED makes weak 18-point STRAIGHT viable through control"),
        
        ("general_red_combo_03", "[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED]",
         3, [0, 1, 1], 6, "GENERAL_RED + weak field enables FIVE_OF_A_KIND (5) + opener (1) = 6")
    ]
    
    all_scenarios = game_changer_scenarios + field_interaction_scenarios + combo_enablement_scenarios
    
    correct_count = 0
    total_count = len(all_scenarios)
    
    print("\n1. GAME CHANGER SCENARIOS")
    print("-" * 30)
    for scenario in game_changer_scenarios:
        correct = analyze_scenario(*scenario)
        if correct:
            correct_count += 1
    
    print("\n\n2. FIELD STRENGTH INTERACTION SCENARIOS")
    print("-" * 40)
    for scenario in field_interaction_scenarios:
        correct = analyze_scenario(*scenario)
        if correct:
            correct_count += 1
    
    print("\n\n3. COMBO ENABLEMENT SCENARIOS")
    print("-" * 30)
    for scenario in combo_enablement_scenarios:
        correct = analyze_scenario(*scenario)
        if correct:
            correct_count += 1
    
    print(f"\n\nSUMMARY: {correct_count}/{total_count} scenarios match expected values")
    if correct_count < total_count:
        print(f"❌ {total_count - correct_count} scenarios need strategic review")
    else:
        print("✅ All scenarios are strategically consistent")


if __name__ == "__main__":
    main()