#!/usr/bin/env python3
"""Debug script for multi_combo_13 to understand forbidden value handling."""

import sys
sys.path.append('.')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare_strategic_v2

# multi_combo_13 details
hand = [
    Piece("GENERAL_RED"),     # 14
    Piece("GENERAL_BLACK"),   # 13  
    Piece("ADVISOR_RED"),     # 12
    Piece("ADVISOR_BLACK"),   # 11
    Piece("CHARIOT_RED"),     # 8
    Piece("HORSE_RED"),       # 6
    Piece("CANNON_RED"),      # 4
    Piece("SOLDIER_BLACK")    # 1
]

print("="*80)
print("Analyzing multi_combo_13 - Forbidden Value Handling")
print("="*80)
print(f"Hand: {[f'{p.name}_{p.color}({p.point})' for p in hand]}")
print(f"Position: 3 (non-starter, LAST PLAYER)")
print(f"Previous declarations: [3, 2, 2]")
print(f"Sum of previous: 3 + 2 + 2 = 7")
print(f"Pile room: 8 - 7 = 1")
print()

print("IMPORTANT: As the last player (position 3), cannot declare a value that")
print("would make the total sum equal to 8, because that's the default/forbidden sum.")
print()

print("Forbidden value calculation:")
print("- Total so far: 3 + 2 + 2 = 7")
print("- To make sum = 8: need to declare 8 - 7 = 1")
print("- Therefore: declaring 1 is FORBIDDEN for the last player")
print()

print("Test expectation: 5")
print("Test description says: 'Only pile room 1, so just GENERAL despite having multiple combos'")
print("But this seems incorrect - if pile room is 1 and declaring 1 is forbidden, what can be done?")
print()

# Run the actual V2 function
print("="*80)
print("Running choose_declare_strategic_v2:")
print("="*80)

result = choose_declare_strategic_v2(
    hand=hand,
    is_first_player=False,
    position_in_order=3,
    previous_declarations=[3, 2, 2],
    must_declare_nonzero=False,
    verbose=True
)

print(f"\nFinal result: {result}")
print(f"Expected: 5")
print()

print("="*80)
print("Explanation of 'Rebuilding play_list to avoid forbidden values':")
print("="*80)
print("1. The AI initially tries to play GENERAL_RED as opener (1 piece)")
print("2. But declaring 1 is forbidden (would make sum = 8)")
print("3. So it calls rebuild_play_list_avoiding_forbidden() function")
print("4. This function tries to find alternative combinations that avoid forbidden values")
print("5. If no valid combination exists, it declares 0")
print()
print("In this case:")
print("- Can't declare 1 (forbidden)")
print("- Can't declare 0 (unless no other choice)")
print("- Any other value (2-8) exceeds pile room of 1")
print("- Therefore, the only valid choice is to declare 0")