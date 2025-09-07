#!/usr/bin/env python3
"""Test to verify combo detection issue in multi_combo_18."""

from backend.engine.piece import Piece
from backend.engine.ai import find_all_valid_combos, find_and_select_strong_combos_iteratively

# Create the hand from multi_combo_18
hand = [
    Piece("GENERAL_RED"),
    Piece("CHARIOT_BLACK"),
    Piece("CHARIOT_BLACK"),
    Piece("HORSE_RED"),
    Piece("HORSE_RED"),
    Piece("CANNON_BLACK"),
    Piece("CANNON_BLACK"),
    Piece("SOLDIER_RED")
]

print("="*80)
print("TESTING COMBO DETECTION ISSUE")
print("="*80)
print(f"Hand: {[p.name for p in hand]}")
print("\nExpected combos:")
print("- PAIR of CHARIOT_BLACK (7+7=14)")
print("- PAIR of HORSE_RED (6+6=12)")
print("- PAIR of CANNON_BLACK (3+3=6)")
print()

# Test 1: find_all_valid_combos
print("TEST 1: find_all_valid_combos")
print("-"*40)
all_combos = find_all_valid_combos(hand)

# Count pairs
pairs = [(combo_type, pieces) for combo_type, pieces in all_combos if combo_type == "PAIR"]
print(f"Total combos found: {len(all_combos)}")
print(f"PAIRs found: {len(pairs)}")

for combo_type, pieces in pairs[:5]:  # Show first 5 pairs
    print(f"  - {combo_type}: {[f'{p.name}({p.point})' for p in pieces]}")

# Test 2: find_and_select_strong_combos_iteratively
print("\n\nTEST 2: find_and_select_strong_combos_iteratively")
print("-"*40)
hand_copy = hand.copy()
play_list = []

# Remove GENERAL first (as would happen in non-starter logic)
general = next(p for p in hand_copy if p.name == "GENERAL" and p.color == "RED")
hand_copy.remove(general)

print(f"After removing GENERAL, hand: {[p.name for p in hand_copy]}")
print("\nFinding combos iteratively:")

hand_copy, combos_found = find_and_select_strong_combos_iteratively(hand_copy, play_list, verbose=True)

print(f"\nCombos found: {combos_found}")
print("Play list:")
for play in play_list:
    if play['type'] == 'combo':
        print(f"  - {play['combo_type']}: {[f'{p.name}({p.point})' for p in play['pieces']]}")

print(f"\nRemaining hand: {[p.name for p in hand_copy]}")

# The issue is clear:
print("\n" + "="*80)
print("ISSUE ANALYSIS:")
print("="*80)
print("The iterative function only finds ONE combo at a time and removes it.")
print("After finding CHARIOT PAIR, it removes those pieces and continues.")
print("It should find the HORSE PAIR next, but it doesn't.")
print("\nThis explains why multi_combo_18 only declares 3 piles:")
print("- GENERAL opener: 1 pile")
print("- CHARIOT PAIR: 2 piles")
print("- Total: 3 piles (missing HORSE and CANNON pairs)")
