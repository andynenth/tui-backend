#!/usr/bin/env python3
"""Debug script to analyze general_red_v2_03 test case."""

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

# Create the exact hand from general_red_v2_03
hand = [
    Piece("GENERAL_RED"),
    Piece("ADVISOR_BLACK"),
    Piece("ELEPHANT_RED"),
    Piece("CHARIOT_BLACK"),
    Piece("HORSE_RED"),
    Piece("CANNON_BLACK"),
    Piece("SOLDIER_RED"),
    Piece("SOLDIER_BLACK")
]

# Test parameters
position_in_order = 3
previous_declarations = [0, 1, 2]
is_first_player = False

print("="*80)
print("DEBUGGING general_red_v2_03 - Expected: 2")
print("="*80)
print(f"Hand: {[p.name for p in hand]}")
print(f"Position: {position_in_order} (4th player)")
print(f"Previous declarations: {previous_declarations}")
print()

# Run with verbose output
result = choose_declare_strategic_v2(
    hand=hand,
    is_first_player=is_first_player,
    position_in_order=position_in_order,
    previous_declarations=previous_declarations,
    must_declare_nonzero=False,
    verbose=True
)

print(f"\n{'='*80}")
print(f"FINAL RESULT: {result} (Expected: 2)")
print(f"{'='*80}")
