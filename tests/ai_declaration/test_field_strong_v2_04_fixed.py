#!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2, get_piece_threshold

# Test field_strong_v2_04
hand_str = '[ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_RED, ELEPHANT_RED]'
hand = []
parts = hand_str.replace('[', '').replace(']', '').split(', ')
for part in parts:
    part = part.strip()
    if part:
        hand.append(Piece(part))

print('Testing field_strong_v2_04 after fix:')
print('Position: 3 (Last player)')
print('Previous declarations: [4, 3, 2]')
print('Hand:', [f'{p.name}({p.point})' for p in hand])
print()

print('Pile room = 8 - 4 - 3 = 1 (ignoring 2 that exceeds 8)')
print(f'get_piece_threshold(1) = {get_piece_threshold(1)} (need > 13)')
print()

print('Checking pieces:')
for p in hand:
    if p.point > 13:
        print(f'  - {p.name}: {p.point} points ✓ QUALIFIES')
    else:
        print(f'  - {p.name}: {p.point} points ✗ Does not qualify')
print()

result = choose_declare_strategic_v2(
    hand=hand,
    is_first_player=False,
    position_in_order=3,
    previous_declarations=[4, 3, 2],
    must_declare_nonzero=False,
    verbose=True
)

print(f'\nActual result: {result}')
print(f'Expected result: 0')

if result == 0:
    print('\n✅ SUCCESS: AI correctly declared 0 because no pieces qualify for pile_room=1')
else:
    print(f'\n❌ FAILED: AI declared {result} instead of 0')