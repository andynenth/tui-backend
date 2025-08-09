#!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import find_all_valid_combos, is_strong_combo

# Test edge_forbidden_v2_02
hand_str = '[GENERAL_RED, ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]'
hand = []
parts = hand_str.replace('[', '').replace(']', '').split(', ')
for part in parts:
    part = part.strip()
    if part:
        hand.append(Piece(part))

print('Analyzing all possible combinations for edge_forbidden_v2_02:')
print('=' * 60)
print()

# Find all combos
all_combos = find_all_valid_combos(hand)

print('Strong combos found:')
for combo_type, pieces in all_combos:
    if combo_type != "SINGLE" and is_strong_combo(combo_type, pieces):
        print(f'- {combo_type}: {[str(p) for p in pieces]} ({len(pieces)} pieces, {sum(p.point for p in pieces)} points)')

print()
print('Strong openers (>=11 points):')
for p in hand:
    if p.point >= 11:
        print(f'- {p} (1 piece, {p.point} points)')

print()
print('Valid non-forbidden combinations (avoiding 4):')
print('1 piece: Just opener')
print('2 pieces: Two openers')
print('3 pieces: Just THREE_OF_A_KIND or just STRAIGHT')
print('5+ pieces: Too many')
print()
print('The AI should prefer 3-piece combos over 2 openers!')