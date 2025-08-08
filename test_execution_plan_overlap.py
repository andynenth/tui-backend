#!/usr/bin/env python3
"""Test execution plan with overlap fix"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.ai_turn_strategy import TurnPlayContext, form_execution_plan
from backend.engine.ai import find_all_valid_combos

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

# Create context
context = TurnPlayContext(
    my_name="Alexanderium",
    my_hand=hand,
    my_captured=0,
    my_declared=2,
    required_piece_count=3,
    turn_number=1,
    pieces_per_player=8,
    am_i_starter=True,
    current_plays=[],
    revealed_pieces=[],
    player_states={
        "Alexanderium": {"captured": 0, "declared": 2},
        "Bot 2": {"captured": 0, "declared": 4},
        "Bot 3": {"captured": 0, "declared": 3},
        "Bot 4": {"captured": 0, "declared": 1}
    }
)

print("Testing execution plan with overlap fix:")
print(f"Hand: {[f'{p.name}({p.point})' for p in hand]}")
print(f"Declared: {context.my_declared}")

# Get all valid combos
valid_combos = find_all_valid_combos(hand)

# Form execution plan
plan = form_execution_plan(hand, context, valid_combos)

if plan:
    print("\nPlan formed successfully!")
else:
    print("\nNo plan formed (not turn 1?)")