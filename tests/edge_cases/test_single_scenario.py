#\!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

# Test combo_multi_v2_06
hand_str = '[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]'
hand = []
parts = hand_str.replace('[', '').replace(']', '').split(', ')
for part in parts:
    part = part.strip()
    if part:
        hand.append(Piece(part))

print('Testing combo_multi_v2_06:')
print('Position: 2 (Non-starter)')
print('Previous declarations: [1, 0]')
print('Expected: 5')
print()

result = choose_declare_strategic_v2(
    hand=hand,
    is_first_player=False,
    position_in_order=2,
    previous_declarations=[1, 0],
    must_declare_nonzero=False,
    verbose=True
)

print(f'\nActual result: {result}')
print(f'Expected: 5')
print(f'Test {"PASSED" if result == 5 else "FAILED"}')
EOF < /dev/null
