#!/usr/bin/env python3
"""Debug script to understand why AI declares 4 instead of 5 in multi_combo_13."""

import sys
sys.path.append('.')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2, find_all_valid_combos

# multi_combo_13 details
hand = [
    Piece("GENERAL_RED"),     # 14
    Piece("GENERAL_BLACK"),   # 13  
    Piece("ADVISOR_RED"),     # 12
    Piece("ADVISOR_BLACK"),   # 11
    Piece("CHARIOT_RED"),     # 8
    Piece("HORSE_RED"),       # 6
    Piece("CANNON_RED"),      # 4
    Piece("SOLDIER_BLACK")    # 1
]

print("="*80)
print("Detailed Analysis of multi_combo_13")
print("="*80)

print("\nAll possible combos in hand:")
combos = find_all_valid_combos(hand)
for combo_type, pieces in combos:
    if combo_type != "SINGLE":
        print(f"  {combo_type}: {[f'{p.name}_{p.color}({p.point})' for p in pieces]} = {len(pieces)} pieces")

print("\nWith pile room = 4, possible plays:")
print("1. GENERAL_RED (1) + STRAIGHT (3) = 4 pieces")
print("2. GENERAL_RED (1) + GENERAL_BLACK (1) + 2 others = 4 pieces")
print("3. Other 4-piece combinations...")

print("\nWhy doesn't it play 5 pieces?")
print("- Pile room is 4 (after GENERAL_RED rule)")
print("- Cannot exceed pile room")
print("- So maximum declaration is 4, not 5")

print("\nRunning AI to confirm...")
result = choose_declare_strategic_v2(
    hand=hand,
    is_first_player=False,
    position_in_order=3,
    previous_declarations=[3, 2, 2],
    must_declare_nonzero=False,
    verbose=True
)

print(f"\nFinal result: {result}")
print("Expected: 5")
print("\nConclusion: The test expectation of 5 seems incorrect.")
print("With GENERAL_RED rule giving pile_room=4, the maximum valid declaration is 4.")