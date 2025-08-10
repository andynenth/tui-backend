#!/usr/bin/env python3
"""Compare general_red_v2_03 (working) vs multi_combo_18 (failing)."""

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

print("="*80)
print("COMPARING TWO TEST CASES")
print("="*80)

# Test Case 1: general_red_v2_03 (WORKING - Expected: 2, Got: 2)
print("\n1. general_red_v2_03 (WORKING)")
print("-"*40)
hand1 = [
    Piece("GENERAL_RED"),
    Piece("ADVISOR_BLACK"),
    Piece("ELEPHANT_RED"),
    Piece("CHARIOT_BLACK"),
    Piece("HORSE_RED"),
    Piece("CANNON_BLACK"),
    Piece("SOLDIER_RED"),
    Piece("SOLDIER_BLACK")
]
print("Hand:", [p.name for p in hand1])
print("Position: 3, Previous: [0, 1, 2]")
print("Expected: 2")
result1 = choose_declare_strategic_v2(
    hand=hand1,
    is_first_player=False,
    position_in_order=3,
    previous_declarations=[0, 1, 2],
    must_declare_nonzero=False,
    verbose=False
)
print(f"Actual: {result1} ✅")

# Test Case 2: multi_combo_18 (FAILING - Expected: 8, Got: 7)
print("\n2. multi_combo_18 (FAILING)")
print("-"*40)
hand2 = [
    Piece("GENERAL_RED"),
    Piece("CHARIOT_BLACK"),
    Piece("CHARIOT_BLACK"),
    Piece("HORSE_RED"),
    Piece("HORSE_RED"),
    Piece("CANNON_BLACK"),
    Piece("CANNON_BLACK"),
    Piece("SOLDIER_RED")
]
print("Hand:", [p.name for p in hand2])
print("Position: 3, Previous: [0, 1, 2]")
print("Expected: 8")
result2 = choose_declare_strategic_v2(
    hand=hand2,
    is_first_player=False,
    position_in_order=3,
    previous_declarations=[0, 1, 2],
    must_declare_nonzero=False,
    verbose=False
)
print(f"Actual: {result2} ❌ (off by {8-result2})")

# Key differences
print("\n" + "="*80)
print("KEY DIFFERENCES:")
print("="*80)

print("\n1. Hand Composition:")
print("   - general_red_v2_03: Individual pieces (no combos)")
print("   - multi_combo_18: Multiple pairs (3 pairs)")

print("\n2. Expected Results:")
print("   - general_red_v2_03: Low expectation (2 piles)")
print("   - multi_combo_18: High expectation (8 piles)")

print("\n3. Algorithm Challenge:")
print("   - general_red_v2_03: Simple opener detection")
print("   - multi_combo_18: Complex combo + opener interaction")

# Run multi_combo_18 with verbose to see where it goes wrong
print("\n" + "="*80)
print("VERBOSE OUTPUT FOR multi_combo_18:")
print("="*80)
result2_verbose = choose_declare_strategic_v2(
    hand=hand2,
    is_first_player=False,
    position_in_order=3,
    previous_declarations=[0, 1, 2],
    must_declare_nonzero=False,
    verbose=True
)