#!/usr/bin/env python3
"""Test why HORSE pair isn't being detected as strong."""

from backend.engine.piece import Piece
from backend.engine.ai import is_strong_combo, STRONG_PAIR_THRESHOLD

# Test HORSE pair
horse_pair = [Piece("HORSE_RED"), Piece("HORSE_RED")]
total = sum(p.point for p in horse_pair)

print("="*80)
print("TESTING HORSE PAIR DETECTION")
print("="*80)
print(f"HORSE pair: {[f'{p.name}({p.point})' for p in horse_pair]}")
print(f"Total value: {total}")
print(f"STRONG_PAIR_THRESHOLD: {STRONG_PAIR_THRESHOLD}")
print(f"Is {total} > {STRONG_PAIR_THRESHOLD}? {total > STRONG_PAIR_THRESHOLD}")
print()

result = is_strong_combo("PAIR", horse_pair)
print(f"is_strong_combo('PAIR', horse_pair) = {result}")

if not result:
    print("\n❌ HORSE pair is NOT considered strong!")
    print("This is why it's not being selected by the iterative function.")
    
# Test CANNON pair too
cannon_pair = [Piece("CANNON_BLACK"), Piece("CANNON_BLACK")]
total_cannon = sum(p.point for p in cannon_pair)
result_cannon = is_strong_combo("PAIR", cannon_pair)

print(f"\nCANNON pair: {[f'{p.name}({p.point})' for p in cannon_pair]}")
print(f"Total value: {total_cannon}")
print(f"is_strong_combo('PAIR', cannon_pair) = {result_cannon}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("The algorithm only considers pairs 'strong' if their total > 12.")
print("- CHARIOT pair (14) is strong ✓")
print("- HORSE pair (12) is NOT strong ✗")
print("- CANNON pair (6) is NOT strong ✗")
print("\nThis explains why only 1 pair is found instead of 3!")