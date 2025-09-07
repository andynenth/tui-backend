#!/usr/bin/env python3
import sys
sys.path.append('.')

from backend.engine.piece import Piece
from backend.engine.ai import find_all_valid_combos

hand = [
    Piece('GENERAL_RED'),
    Piece('GENERAL_BLACK'),
    Piece('ADVISOR_RED'),
    Piece('ADVISOR_BLACK'),
    Piece('CHARIOT_RED'),
    Piece('HORSE_RED'),
    Piece('CANNON_RED'),
    Piece('SOLDIER_BLACK')
]

combos = find_all_valid_combos(hand)
print('All valid combos found:')
for combo_type, pieces in combos:
    if combo_type != 'SINGLE':
        pieces_str = [f"{p.name}_{p.color}" for p in pieces]
        print(f'  {combo_type}: {pieces_str}')
