#!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

# Test edge_forbidden_v2_02
hand_str = '[GENERAL_RED, ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]'
hand = []
parts = hand_str.replace('[', '').replace(']', '').split(', ')
for part in parts:
    part = part.strip()
    if part:
        hand.append(Piece(part))

print('Testing edge_forbidden_v2_02 with new play_list rebuilding:')
print('Position: 3 (Last player)')
print('Previous declarations: [3, 1, 0]')
print('Expected behavior: AI should rebuild play_list to avoid forbidden value 4')
print()

result = choose_declare_strategic_v2(
    hand=hand,
    is_first_player=False,
    position_in_order=3,
    previous_declarations=[3, 1, 0],
    must_declare_nonzero=False,
    verbose=True
)

print(f'\nActual result: {result}')
print(f'Total sum: {3 + 1 + 0 + result} = {sum([3, 1, 0]) + result}')

if result == 3:
    print('\n✅ SUCCESS: AI declared 3 with properly rebuilt play_list')
else:
    print(f'\n❌ UNEXPECTED: AI declared {result}')