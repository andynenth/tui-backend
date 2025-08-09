#!/usr/bin/env python3
"""Test a single scenario to debug."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2, find_all_valid_combos

# Test ELEPHANT pair scenario
hand = [Piece(name) for name in [
    "ELEPHANT_RED", "ELEPHANT_BLACK", "CHARIOT_RED", "CHARIOT_BLACK",
    "HORSE_RED", "CANNON_BLACK", "SOLDIER_RED", "SOLDIER_BLACK"
]]

print("Hand pieces:")
for p in hand:
    print(f"  {p.name}({p.point})")

# Debug piece info
print("\nDetailed piece info:")
for p in hand:
    print(f"  {p.kind} -> name={p.name}, point={p.point}")

# Test find_all_valid_combos
print("\nAll valid combos found:")
all_combos = find_all_valid_combos(hand)
print(f"Total combos found: {len(all_combos)}")
for combo_type, pieces in all_combos:
    avg = sum(p.point for p in pieces) / len(pieces) if pieces else 0
    print(f"  {combo_type}: {[f'{p.name}({p.point})' for p in pieces]} (avg={avg:.1f})")

print("\n" + "="*60)
result = choose_declare_strategic_v2(
    hand=hand,
    is_first_player=True,
    position_in_order=0,
    previous_declarations=[],
    must_declare_nonzero=False,
    verbose=True
)

print(f"\nFinal result: {result}")