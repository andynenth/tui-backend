#!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

# Test edge_forbidden_v2_04
hand_str = '[SOLDIER_RED, SOLDIER_BLACK, HORSE_RED, CANNON_BLACK, ELEPHANT_RED, CHARIOT_BLACK, ELEPHANT_BLACK, ADVISOR_BLACK]'
hand = []
parts = hand_str.replace('[', '').replace(']', '').split(', ')
for part in parts:
    part = part.strip()
    if part:
        hand.append(Piece(part))

print('Testing edge_forbidden_v2_04:')
print('Position: 3 (Last player)')
print('Previous declarations: [2, 2, 3]')
print('Hand:', [f'{p.name}({p.point})' for p in hand])
print()

# Check for openers
print('Checking for openers (>=11 points):')
for p in hand:
    if p.point >= 11:
        print(f'  - {p.name}: {p.point} points ✓ OPENER')

print('\nSum calculation: 2 + 2 + 3 = 7')
print('Forbidden value: 1 (would make sum = 8)')
print()

result = choose_declare_strategic_v2(
    hand=hand,
    is_first_player=False,
    position_in_order=3,
    previous_declarations=[2, 2, 3],
    must_declare_nonzero=False,
    verbose=True
)

print(f'\nActual result: {result}')
print(f'Expected result: 1')