#!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

# Test edge_forbidden_v2_03
# Hand: [ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]
# Position: 3 (Last player) 
# Previous declarations: [1, 3, 3]
# Expected: 1, Actual: 0

hand_str = '[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, CANNON_RED, CANNON_BLACK]'
hand = []
parts = hand_str.replace('[', '').replace(']', '').split(', ')
for part in parts:
    part = part.strip()
    if part:
        hand.append(Piece(part))

print('Testing edge_forbidden_v2_03:')
print('Position: 3 (Last player)')
print('Previous declarations: [1, 3, 3]')
print('Hand:', [f'{p.name}({p.point})' for p in hand])
print()

# Check for openers
print('Checking for openers (>=11 points):')
for p in hand:
    if p.point >= 11:
        print(f'  - {p.name}: {p.point} points ✓')
    else:
        print(f'  - {p.name}: {p.point} points')

print('\nNo openers found! All pieces are < 11 points.')
print('\nSum calculation: 1 + 3 + 3 = 7')
print('Forbidden value: 1 (would make sum = 8)')
print()

result = choose_declare_strategic_v2(
    hand=hand,
    is_first_player=False,
    position_in_order=3,
    previous_declarations=[1, 3, 3],
    must_declare_nonzero=False,
    verbose=True
)

print(f'\nActual result: {result}')
print(f'Expected result: 1')
print()

if result == 0:
    print('The AI declared 0 because:')
    print('1. No openers (all pieces < 11 points)')
    print('2. Non-starters normally need openers to declare > 0')
    print('3. The forbidden value handling might not force finding a piece when no openers exist')