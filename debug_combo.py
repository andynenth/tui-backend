#!/usr/bin/env python3

import sys
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.piece import Piece
from backend.engine.ai import find_all_valid_combos, is_strong_combo, find_and_select_strong_combos_iteratively

# Create the hand
hand_str = '[GENERAL_BLACK, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, SOLDIER_RED, CHARIOT_BLACK, HORSE_BLACK, CANNON_BLACK]'
hand = []
parts = hand_str.replace('[', '').replace(']', '').split(', ')
for part in parts:
    part = part.strip()
    if part:
        hand.append(Piece(part))

print('🔍 Analyzing combo detection for combo_multi_v2_06:')
print()

# Display the full hand
print('Full hand:')
for i, p in enumerate(hand, 1):
    print(f'  {i}. {p}')
print()

# Remove the opener first (like the algorithm does)
hand_copy = [p for p in hand if p.name != 'GENERAL']
print('Hand after removing GENERAL opener:')
for i, p in enumerate(hand_copy, 1):
    print(f'  {i}. {p}')
print()

# Find all combos
combos = find_all_valid_combos(hand_copy)
print(f'Found {len(combos)} combos:')
for i, (combo_type, pieces) in enumerate(combos, 1):
    total_value = sum(p.point for p in pieces)
    piece_names = [str(p) for p in pieces]
    is_strong = is_strong_combo(combo_type, pieces)
    print(f'  {i}. {combo_type}: {piece_names}')
    print(f'     Total value: {total_value}, Strong: {is_strong}')
    print()

print('🎯 Expected combos:')
print('  - FOUR_OF_A_KIND RED: 4 SOLDIER_RED pieces = 4 piles (should be strong)')
print('  - BLACK STRAIGHT: CHARIOT_BLACK + HORSE_BLACK + CANNON_BLACK = 3 piles')
print('  - Total with GENERAL opener: 1 + 4 + 3 = 8 piles (or at least 1 + 4 = 5)')
print()

# Check if FOUR_OF_A_KIND is detected as strong
soldier_pieces = [p for p in hand_copy if p.name == 'SOLDIER' and p.color == 'RED']
if len(soldier_pieces) == 4:
    print('✅ FOUR_OF_A_KIND RED detected:')
    for p in soldier_pieces:
        print(f'    {p}')
    is_strong = is_strong_combo("FOUR_OF_A_KIND", soldier_pieces)
    print(f'    Is strong: {is_strong}')
else:
    print(f'❌ Expected 4 SOLDIER_RED pieces, found {len(soldier_pieces)}')

print()
print('🔍 Testing iterative combo selection:')
hand_copy_test = [p for p in hand if p.name != 'GENERAL']
play_list = []

print(f'\nInitial hand (without GENERAL): {[str(p) for p in hand_copy_test]}')
hand_copy_test, combos_found = find_and_select_strong_combos_iteratively(hand_copy_test, play_list, verbose=True)
print(f'\nCombos found: {combos_found}')
print(f'Play list: {[(pl["type"], pl.get("combo_type"), [str(p) for p in pl["pieces"]]) for pl in play_list]}')
print(f'Remaining hand: {[str(p) for p in hand_copy_test]}')