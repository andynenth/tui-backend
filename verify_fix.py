#!/usr/bin/env python3
"""Verify the fix doesn't break other tests."""

import sys
sys.path.append('.')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

# Test 1: baseline_v2_17
hand1 = [Piece('GENERAL_RED'), Piece('GENERAL_BLACK'), Piece('CHARIOT_RED'), 
         Piece('HORSE_RED'), Piece('CANNON_RED'), Piece('ADVISOR_BLACK'), 
         Piece('ADVISOR_BLACK'), Piece('SOLDIER_BLACK')]
result1 = choose_declare_strategic_v2(hand1, False, 2, [1, 0], False, verbose=False)
print(f'baseline_v2_17: Expected 7, Got {result1} {"✓" if result1 == 7 else "✗"}')

# Test 2: general_red_v2_03  
hand2 = [Piece('GENERAL_RED'), Piece('ADVISOR_BLACK'), Piece('ELEPHANT_RED'),
         Piece('CHARIOT_BLACK'), Piece('HORSE_RED'), Piece('CANNON_BLACK'),
         Piece('SOLDIER_RED'), Piece('SOLDIER_BLACK')]
result2 = choose_declare_strategic_v2(hand2, False, 3, [0, 1, 2], False, verbose=False)
print(f'general_red_v2_03: Expected 2, Got {result2} {"✓" if result2 == 2 else "✗"}')

# Test 3: multi_combo_13 (should now get 5)
hand3 = [Piece("GENERAL_RED"), Piece("GENERAL_BLACK"), Piece("ADVISOR_RED"), 
         Piece("ADVISOR_BLACK"), Piece("CHARIOT_RED"), Piece("HORSE_RED"), 
         Piece("CANNON_RED"), Piece("SOLDIER_BLACK")]
result3 = choose_declare_strategic_v2(hand3, False, 3, [3, 2, 2], False, verbose=False)
print(f'multi_combo_13: Expected 5, Got {result3} {"✓" if result3 == 5 else "✗"}')

# Test 4: multi_combo_18
hand4 = [Piece('GENERAL_RED'), Piece('GENERAL_BLACK'), Piece('SOLDIER_RED'), 
         Piece('SOLDIER_RED'), Piece('SOLDIER_RED'), Piece('SOLDIER_BLACK'), 
         Piece('SOLDIER_BLACK'), Piece('SOLDIER_BLACK')]
result4 = choose_declare_strategic_v2(hand4, False, 1, [3], False, verbose=False)
print(f'multi_combo_18: Expected 5, Got {result4} {"✓" if result4 == 5 else "✗"}')