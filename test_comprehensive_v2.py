#!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

# Key test cases related to combo selection
test_cases = [
    # Original failing test - should now pass
    {
        'name': 'combo_multi_v2_06',
        'hand_str': '[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]',
        'position': 2,
        'prev_decl': [1, 0],
        'is_starter': False,
        'expected': 5,
        'description': 'GENERAL + FOUR_OF_A_KIND with room constraint'
    },
    # Test with THREE_OF_A_KIND vs STRAIGHT
    {
        'name': 'three_vs_straight',
        'hand_str': '[ADVISOR_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED, ELEPHANT_BLACK]',
        'position': 0,
        'prev_decl': [],
        'is_starter': True,
        'expected': 6,
        'description': 'THREE_OF_A_KIND + STRAIGHT as starter'
    },
    # Test with multiple combos as non-starter
    {
        'name': 'multi_combo_non_starter',
        'hand_str': '[GENERAL_RED, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, SOLDIER_BLACK, CHARIOT_RED, HORSE_RED, CANNON_RED]',
        'position': 0,
        'prev_decl': [],
        'is_starter': True,
        'expected': 8,
        'description': 'GENERAL + FOUR_OF_A_KIND + STRAIGHT as starter'
    },
    # Test with pairs
    {
        'name': 'pair_test',
        'hand_str': '[ELEPHANT_RED, ELEPHANT_BLACK, CHARIOT_RED, CHARIOT_BLACK, HORSE_RED, HORSE_BLACK, SOLDIER_RED, SOLDIER_BLACK]',
        'position': 0,
        'prev_decl': [],
        'is_starter': True,
        'expected': 2,
        'description': 'Strong ELEPHANT pair as starter'
    },
]

print('Comprehensive V2 combo selection tests')
print('=' * 60)

passed = 0
failed = 0

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
        is_first_player=test['is_starter'],
        position_in_order=test['position'],
        previous_declarations=test['prev_decl'],
        must_declare_nonzero=False,
        verbose=False
    )
    
    # Check result
    is_passed = (result == test['expected'])
    if is_passed:
        passed += 1
        status = '✅ PASS'
    else:
        failed += 1
        status = '❌ FAIL'
    
    print(f'\n{status} {test["name"]}:')
    print(f'  Description: {test["description"]}')
    print(f'  Expected: {test["expected"]}, Got: {result}')
    
print('\n' + '=' * 60)
print(f'Summary: {passed}/{len(test_cases)} passed ({passed/len(test_cases)*100:.0f}%)')

if failed == 0:
    print('✅ All tests passed! The fix is working correctly.')
else:
    print(f'❌ {failed} tests failed.')