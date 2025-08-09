#!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

# Test various scenarios where last player must avoid sum = 8
test_cases = [
    {
        'name': 'forbidden_4',
        'prev_decl': [3, 1, 0],  # sum = 4, forbidden = 4
        'expected_avoid': 4
    },
    {
        'name': 'forbidden_3', 
        'prev_decl': [2, 2, 1],  # sum = 5, forbidden = 3
        'expected_avoid': 3
    },
    {
        'name': 'forbidden_2',
        'prev_decl': [3, 2, 1],  # sum = 6, forbidden = 2
        'expected_avoid': 2
    },
    {
        'name': 'forbidden_1',
        'prev_decl': [3, 3, 1],  # sum = 7, forbidden = 1
        'expected_avoid': 1
    },
]

# Use a hand with many options
hand_str = '[GENERAL_RED, ADVISOR_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]'
hand = []
parts = hand_str.replace('[', '').replace(']', '').split(', ')
for part in parts:
    part = part.strip()
    if part:
        hand.append(Piece(part))

print('Testing last player forbidden sum = 8 logic')
print('=' * 60)

for test in test_cases:
    print(f"\nTest: {test['name']}")
    print(f"Previous declarations: {test['prev_decl']} (sum = {sum(test['prev_decl'])})")
    print(f"Forbidden value: {test['expected_avoid']} (would make sum = 8)")
    
    result = choose_declare_strategic_v2(
        hand=hand,
        is_first_player=False,
        position_in_order=3,  # Last player
        previous_declarations=test['prev_decl'],
        must_declare_nonzero=False,
        verbose=False
    )
    
    total_sum = sum(test['prev_decl']) + result
    
    print(f"AI declared: {result}")
    print(f"Total sum: {total_sum}")
    
    if result == test['expected_avoid']:
        print("❌ FAILED - AI should avoid this value!")
    elif total_sum == 8:
        print("❌ FAILED - AI made sum = 8!")
    else:
        print("✅ PASSED - AI correctly avoided forbidden value")

print('\n' + '=' * 60)
print('Summary: Last player must always avoid making sum = 8')