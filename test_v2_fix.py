#!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

# Test cases to verify the fix
test_cases = [
    # combo_multi_v2_06 - the original failing test
    {
        'name': 'combo_multi_v2_06',
        'hand_str': '[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]',
        'position': 2,
        'prev_decl': [1, 0],
        'expected': 5,
        'description': 'FOUR_OF_A_KIND + STRAIGHT with pile room constraint'
    },
    # Test without pile room constraint
    {
        'name': 'full_room_test',
        'hand_str': '[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]',
        'position': 0,
        'prev_decl': [],
        'expected': 8,
        'description': 'Same hand as starter - should get all combos'
    },
    # Test with more severe room constraint
    {
        'name': 'tight_room_test',
        'hand_str': '[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]',
        'position': 3,
        'prev_decl': [2, 2, 2],
        'expected': 2,
        'description': 'Only 2 pile room - should keep GENERAL + 1 piece'
    },
]

print('Testing V2 combo selection with pile room constraints')
print('=' * 60)

for test in test_cases:
    # Parse hand
    hand = []
    parts = test['hand_str'].replace('[', '').replace(']', '').split(', ')
    for part in parts:
        part = part.strip()
        if part:
            hand.append(Piece(part))
    
    # Run test
    result = choose_declare_strategic_v2(
        hand=hand,
        is_first_player=(test['position'] == 0),
        position_in_order=test['position'],
        previous_declarations=test['prev_decl'],
        must_declare_nonzero=False,
        verbose=False
    )
    
    # Check result
    passed = (result == test['expected'])
    status = '✅ PASS' if passed else '❌ FAIL'
    
    print(f'\n{status} {test["name"]}:')
    print(f'  Description: {test["description"]}')
    print(f'  Position: {test["position"]}, Previous: {test["prev_decl"]}')
    print(f'  Expected: {test["expected"]}, Got: {result}')
    
print('\n' + '=' * 60)
print('All tests completed!')