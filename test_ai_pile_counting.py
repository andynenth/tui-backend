#!/usr/bin/env python3
"""Test script to verify AI pile-aware counting is working correctly"""

import sys
sys.path.insert(0, '.')

from backend.engine.piece import Piece
from backend.engine.ai import choose_declare

def create_piece(name, color):
    """Helper to create a piece"""
    return Piece(kind=f"{name}_{color}")

def test_pile_counting():
    """Test various hands to verify pile-aware counting"""
    
    print("=" * 60)
    print("Testing AI Pile-Aware Declaration Logic")
    print("=" * 60)
    
    # Test 1: Hand with ADVISOR opener + STRAIGHT
    print("\n📋 Test 1: ADVISOR opener + STRAIGHT")
    hand1 = [
        create_piece("ADVISOR", "RED"),      # 12 points - opener
        create_piece("CHARIOT", "BLACK"),    # 7 points
        create_piece("HORSE", "BLACK"),      # 5 points  
        create_piece("CANNON", "BLACK"),     # 3 points
        create_piece("SOLDIER", "RED"),      # 2 points
        create_piece("SOLDIER", "RED"),      # 2 points
        create_piece("SOLDIER", "BLACK"),    # 1 point
        create_piece("SOLDIER", "BLACK"),    # 1 point
    ]
    
    result1 = choose_declare(
        hand=hand1,
        is_first_player=False,
        position_in_order=1,
        previous_declarations=[],
        must_declare_nonzero=False,
        verbose=True
    )
    print(f"\n✅ Declaration result: {result1}")
    print("Expected: 4 (1 pile from ADVISOR opener + 3 piles from STRAIGHT)")
    
    # Test 2: Hand with THREE_OF_A_KIND SOLDIERs
    print("\n\n📋 Test 2: THREE_OF_A_KIND SOLDIERs")
    hand2 = [
        create_piece("ELEPHANT", "RED"),     # 10 points - not quite opener
        create_piece("SOLDIER", "BLACK"),    # 1 point
        create_piece("SOLDIER", "BLACK"),    # 1 point
        create_piece("SOLDIER", "BLACK"),    # 1 point
        create_piece("SOLDIER", "BLACK"),    # 1 point
        create_piece("CHARIOT", "RED"),      # 8 points
        create_piece("HORSE", "RED"),        # 6 points
        create_piece("CANNON", "RED"),       # 4 points
    ]
    
    result2 = choose_declare(
        hand=hand2,
        is_first_player=True,  # First player bonus
        position_in_order=0,
        previous_declarations=[],
        must_declare_nonzero=False,
        verbose=True
    )
    print(f"\n✅ Declaration result: {result2}")
    print("Expected: 4 (3 piles from THREE_OF_A_KIND + 1 from first player)")
    
    # Test 3: Multiple strong combos with GENERAL opener
    print("\n\n📋 Test 3: GENERAL opener + multiple combos")
    hand3 = [
        create_piece("GENERAL", "RED"),      # 14 points - strong opener
        create_piece("SOLDIER", "RED"),      # 2 points
        create_piece("SOLDIER", "RED"),      # 2 points
        create_piece("SOLDIER", "RED"),      # 2 points
        create_piece("CHARIOT", "BLACK"),    # 7 points
        create_piece("HORSE", "BLACK"),      # 5 points
        create_piece("CANNON", "BLACK"),     # 3 points
        create_piece("ELEPHANT", "BLACK"),   # 9 points
    ]
    
    result3 = choose_declare(
        hand=hand3,
        is_first_player=False,
        position_in_order=2,
        previous_declarations=[2, 3],
        must_declare_nonzero=False,
        verbose=True
    )
    print(f"\n✅ Declaration result: {result3}")
    print("Expected: 7 (1 from GENERAL + 3 from STRAIGHT + 3 from THREE_OF_A_KIND)")
    print("Note: Can't declare 8 due to game rules, might be clamped to 7")
    
    # Test 4: Weak hand with no strong pieces
    print("\n\n📋 Test 4: Weak hand")
    hand4 = [
        create_piece("ELEPHANT", "BLACK"),   # 9 points - not opener
        create_piece("CHARIOT", "RED"),      # 8 points
        create_piece("HORSE", "BLACK"),      # 5 points
        create_piece("CANNON", "RED"),       # 4 points
        create_piece("SOLDIER", "RED"),      # 2 points
        create_piece("SOLDIER", "BLACK"),    # 1 point
        create_piece("SOLDIER", "RED"),      # 2 points
        create_piece("SOLDIER", "BLACK"),    # 1 point
    ]
    
    result4 = choose_declare(
        hand=hand4,
        is_first_player=False,
        position_in_order=1,
        previous_declarations=[3],
        must_declare_nonzero=True,  # Must declare at least 1
        verbose=True
    )
    print(f"\n✅ Declaration result: {result4}")
    print("Expected: 1 (no combos, no opener, forced to declare ≥1)")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_pile_counting()