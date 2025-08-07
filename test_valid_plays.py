#!/usr/bin/env python3
"""
Test what constitutes a valid play in the game.
"""

import sys
sys.path.append('.')

from backend.engine.piece import Piece
from backend.engine.rules import is_valid_play, get_play_type
from itertools import combinations


def test_valid_plays():
    """Test various piece combinations."""
    hand = [
        Piece("GENERAL_RED"),      # 14 points
        Piece("ADVISOR_BLACK"),    # 11 points
        Piece("ELEPHANT_RED"),     # 10 points
        Piece("CANNON_BLACK"),     # 4 points
        Piece("SOLDIER_RED"),      # 2 points
        Piece("SOLDIER_BLACK"),    # 1 point
    ]
    
    print("Testing valid 2-piece combinations:")
    valid_found = False
    
    for combo in combinations(hand, 2):
        pieces = list(combo)
        if is_valid_play(pieces):
            play_type = get_play_type(pieces)
            points = sum(p.point for p in pieces)
            print(f"  ✓ {[p.name for p in pieces]} = {play_type} ({points} points)")
            valid_found = True
    
    if not valid_found:
        print("  ❌ No valid 2-piece combinations found!")
        
    print("\nChecking if any pieces form pairs:")
    for i, p1 in enumerate(hand):
        for p2 in hand[i+1:]:
            if p1.name == p2.name:
                print(f"  Pair found: {p1.name} + {p2.name}")
    
    print("\nTesting if single pieces are valid:")
    for piece in hand:
        if is_valid_play([piece]):
            print(f"  ✓ Single {piece.name} is valid")
            
    print("\nTesting specific combinations:")
    # Two different soldiers
    soldiers = [Piece("SOLDIER_RED"), Piece("SOLDIER_BLACK")]
    print(f"Two different soldiers: {is_valid_play(soldiers)} - {get_play_type(soldiers)}")
    
    # Same rank different color  
    advisors = [Piece("ADVISOR_RED"), Piece("ADVISOR_BLACK")]
    print(f"Two advisors (diff color): {is_valid_play(advisors)} - {get_play_type(advisors)}")


if __name__ == "__main__":
    test_valid_plays()