#!/usr/bin/env python3
"""
Minimal test to debug opener detection
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import identify_opener_pieces

# Create test pieces
advisor = Piece("ADVISOR_RED")
soldier = Piece("SOLDIER_BLACK")

print(f"ADVISOR_RED point value: {advisor.point}")
print(f"SOLDIER_BLACK point value: {soldier.point}")

hand = [advisor, soldier]
openers = identify_opener_pieces(hand)

print(f"\nHand: {[(p.name, p.point) for p in hand]}")
print(f"Openers (point >= 11): {[(p.name, p.point) for p in openers]}")
print(f"Number of openers: {len(openers)}")

# Check if 12 >= 11
print(f"\nIs {advisor.point} >= 11? {advisor.point >= 11}")