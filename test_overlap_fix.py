#!/usr/bin/env python3
"""Test the overlap fix for double-counting openers and combos"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.ai import choose_declare_strategic

# Test Alexanderium's hand
hand = [
    Piece("SOLDIER_BLACK"),     # 1
    Piece("SOLDIER_BLACK"),     # 1
    Piece("CANNON_BLACK"),      # 3
    Piece("CANNON_RED"),        # 4
    Piece("HORSE_RED"),         # 6
    Piece("ELEPHANT_RED"),      # 10
    Piece("ADVISOR_RED"),       # 12
    Piece("GENERAL_RED")        # 14
]

print("Testing Alexanderium's declaration with overlap fix:")
print(f"Hand: {[f'{p.name}({p.point})' for p in hand]}")

# Test declaration
declared = choose_declare_strategic(
    hand=hand,
    is_first_player=True,
    position_in_order=0,
    previous_declarations=[],
    must_declare_nonzero=False,
    verbose=True
)

print(f"\nFinal declaration: {declared}")