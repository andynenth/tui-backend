#!/usr/bin/env python3
"""
Debug tool to test choose_best_play with specific hands that resulted in poor AI choices
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.piece import Piece
from backend.engine.ai import choose_best_play

def create_piece(name_color: str) -> Piece:
    """Create a piece from a string like 'ELEPHANT_BLACK'"""
    return Piece(name_color)

def test_poor_choice_scenario():
    """Test the exact scenario from Game AI_96414, Round 6, Turn 3"""
    
    print("Testing Poor Choice Scenario:")
    print("Game AI_96414, Round 6, Turn 3 - Bot 2")
    print("Declared: 5, Captured: 3, Piles needed: 2")
    print()
    
    # Recreate the exact hand from the analysis
    remaining_hand_str = [
        'ELEPHANT_BLACK', 'HORSE_RED', 'ELEPHANT_BLACK', 'ADVISOR_BLACK', 
        'SOLDIER_BLACK', 'SOLDIER_BLACK', 'CANNON_RED', 'CHARIOT_RED'
    ]
    
    hand = [create_piece(p) for p in remaining_hand_str]
    
    print(f"Hand: {[f'{p.name}_{p.color}({p.point})' for p in hand]}")
    print(f"Required pieces: 2")
    print()
    
    # Test with verbose output
    print("Calling choose_best_play with verbose=True:")
    print("-" * 50)
    
    selected = choose_best_play(hand, required_count=2, verbose=True)
    
    print("-" * 50)
    print(f"\nSelected pieces: {[f'{p.name}_{p.color}({p.point})' for p in selected]}")
    
    # Check if it selected SOLDIER_BLACK pair
    if len(selected) == 2 and all(p.name == 'SOLDIER' and p.color == 'BLACK' for p in selected):
        print("\n❌ ERROR: Still selected SOLDIER_BLACK pair!")
        print("   Available better pairs:")
        print("   - ELEPHANT_BLACK pair (18 points)")
    else:
        print("\n✅ Success: Did not select SOLDIER_BLACK pair")
        
    print("\n" + "="*70 + "\n")
    
def test_all_pairs_scenario():
    """Test finding all valid pairs from a hand"""
    
    print("Testing All Valid Pairs Detection:")
    
    # Create a hand with multiple pair options
    hand_str = [
        'SOLDIER_BLACK', 'SOLDIER_BLACK',  # 2 points
        'ELEPHANT_BLACK', 'ELEPHANT_BLACK',  # 18 points
        'HORSE_RED', 'CANNON_RED'  # Not a pair
    ]
    
    hand = [create_piece(p) for p in hand_str]
    
    print(f"Hand: {[f'{p.name}_{p.color}({p.point})' for p in hand]}")
    print()
    
    # Test all valid pairs
    from itertools import combinations
    from backend.engine.rules import is_valid_play, get_play_type
    from backend.engine.ai import is_never_win_combo_basic
    
    print("All valid pairs found:")
    valid_pairs = []
    
    for combo in combinations(hand, 2):
        pieces = list(combo)
        if is_valid_play(pieces):
            play_type = get_play_type(pieces)
            if play_type == "PAIR":
                total = sum(p.point for p in pieces)
                is_never_win = is_never_win_combo_basic(play_type, pieces)
                valid_pairs.append((pieces, total, is_never_win))
                print(f"  - {pieces[0].name}_{pieces[0].color} + {pieces[1].name}_{pieces[1].color} = {total} pts (never-win: {is_never_win})")
    
    print(f"\nTotal valid pairs found: {len(valid_pairs)}")
    
    # Now test choose_best_play
    print("\nTesting choose_best_play:")
    selected = choose_best_play(hand, required_count=2, verbose=True)
    print(f"Selected: {[f'{p.name}_{p.color}({p.point})' for p in selected]}")

if __name__ == "__main__":
    test_poor_choice_scenario()
    test_all_pairs_scenario()