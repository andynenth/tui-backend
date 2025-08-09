#!/usr/bin/env python3
"""Debug combo detection for multi_combo_18."""

from backend.engine.piece import Piece
from backend.engine.ai import identify_combos

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
print("DEBUGGING COMBO DETECTION FOR multi_combo_18")
print("="*80)
print(f"Hand: {[p.name for p in hand]}")
print()

# Get all combos
combos = identify_combos(hand, verbose=True)

print(f"\nTotal combos found: {len(combos)}")
print("="*80)

# Expected combos:
# 1. PAIR of CHARIOT_BLACK
# 2. PAIR of HORSE_RED
# 3. PAIR of CANNON_BLACK

print("\nEXPECTED vs ACTUAL:")
print("-"*40)
print("Expected: 3 PAIRs (CHARIOT, HORSE, CANNON)")
print(f"Actual: {len(combos)} combos")

if len(combos) < 3:
    print("\n❌ MISSING COMBOS! The algorithm is not detecting all pairs.")
    
    # Manual check
    print("\nManual pair check:")
    rank_counts = {}
    for piece in hand:
        rank = piece.rank
        if rank not in rank_counts:
            rank_counts[rank] = []
        rank_counts[rank].append(piece)
    
    for rank, pieces in rank_counts.items():
        if len(pieces) >= 2:
            print(f"  - {rank}: {len(pieces)} pieces (should form PAIR)")
            
print("\nThis explains why multi_combo_18 declares 3 instead of 8:")
print("- GENERAL opener: 1 pile")
print("- Only 1 PAIR detected: 2 piles")
print("- Total: 3 piles (instead of expected 8)")