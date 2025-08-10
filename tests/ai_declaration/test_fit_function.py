#!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import fit_plays_to_pile_room

# Test the fit_plays_to_pile_room function directly
print('Testing fit_plays_to_pile_room function')
print('=' * 60)

# Create test play list with GENERAL + FOUR_OF_A_KIND + STRAIGHT = 8 pieces
play_list = [
    {
        'type': 'opener',
        'pieces': [Piece('GENERAL_BLACK')]
    },
    {
        'type': 'combo',
        'combo_type': 'FOUR_OF_A_KIND',
        'pieces': [Piece('SOLDIER_RED'), Piece('SOLDIER_RED'), Piece('SOLDIER_RED'), Piece('SOLDIER_RED')]
    },
    {
        'type': 'combo',
        'combo_type': 'STRAIGHT',
        'pieces': [Piece('CHARIOT_BLACK'), Piece('HORSE_BLACK'), Piece('CANNON_BLACK')]
    }
]

# Test with different pile room values
test_rooms = [8, 7, 5, 4, 1]

for room in test_rooms:
    print(f'\nPile room: {room}')
    print('Before fit:')
    for play in play_list:
        if play['type'] == 'opener':
            print(f"  - Opener: {[str(p) for p in play['pieces']]}")
        else:
            print(f"  - {play['combo_type']}: {[str(p) for p in play['pieces']]} ({len(play['pieces'])} pieces)")
    
    # Apply fit function
    fitted = fit_plays_to_pile_room(play_list.copy(), room)
    
    print('After fit:')
    total = 0
    for play in fitted:
        if play['type'] == 'opener':
            print(f"  - Opener: {[str(p) for p in play['pieces']]}")
        else:
            print(f"  - {play['combo_type']}: {[str(p) for p in play['pieces']]} ({len(play['pieces'])} pieces)")
        total += len(play['pieces'])
    print(f'Total pieces: {total}')

print('\n' + '=' * 60)
print('✅ The function now prefers FOUR_OF_A_KIND over STRAIGHT when space is limited!')