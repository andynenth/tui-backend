#!/usr/bin/env python3
"""
Test if is_never_win_combo function is working correctly
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import is_never_win_combo

def test_never_win_detection():
    """Test various combinations to see if never-win detection works"""
    
    print("Testing is_never_win_combo function:")
    print("="*50)
    
    # Test 1: All-BLACK straight (3,5,7) - should be never-win
    black_straight = [
        Piece("CANNON_BLACK"),    # 3 points
        Piece("HORSE_BLACK"),     # 5 points  
        Piece("CHARIOT_BLACK")   # 7 points
    ]
    result1 = is_never_win_combo("STRAIGHT", black_straight)
    print(f"Test 1: All-BLACK straight [3,5,7]: {result1} (expected: True)")
    
    # Test 2: Mixed straight (4,5,6) - should NOT be never-win
    mixed_straight = [
        Piece("CANNON_RED"),      # 4 points
        Piece("HORSE_BLACK"),     # 5 points
        Piece("CHARIOT_RED")      # 6 points
    ]
    result2 = is_never_win_combo("STRAIGHT", mixed_straight)
    print(f"Test 2: Mixed straight [4,5,6]: {result2} (expected: False)")
    
    # Test 3: SOLDIER_BLACK pair - should be never-win
    soldier_pair = [
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK")    # 1 point
    ]
    result3 = is_never_win_combo("PAIR", soldier_pair)
    print(f"Test 3: SOLDIER_BLACK pair [1,1]: {result3} (expected: True)")
    
    # Test 4: SOLDIER_RED pair - should NOT be never-win
    soldier_red_pair = [
        Piece("SOLDIER_RED"),     # 2 points
        Piece("SOLDIER_RED")      # 2 points
    ]
    result4 = is_never_win_combo("PAIR", soldier_red_pair)
    print(f"Test 4: SOLDIER_RED pair [2,2]: {result4} (expected: False)")
    
    # Test 5: Three SOLDIER_BLACK - should be never-win
    three_soldiers = [
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK")    # 1 point
    ]
    result5 = is_never_win_combo("THREE_OF_A_KIND", three_soldiers)
    print(f"Test 5: Three SOLDIER_BLACK [1,1,1]: {result5} (expected: True)")
    
    # Test 6: All-BLACK straight but higher values (5,7,9) - should NOT be never-win
    high_black_straight = [
        Piece("HORSE_BLACK"),     # 5 points
        Piece("CHARIOT_BLACK"),   # 7 points
        Piece("ELEPHANT_BLACK")   # 9 points
    ]
    result6 = is_never_win_combo("STRAIGHT", high_black_straight)
    print(f"Test 6: Higher BLACK straight [5,7,9]: {result6} (expected: False)")
    
    print("\nSummary:")
    all_passed = (result1 == True and result2 == False and result3 == True and 
                  result4 == False and result5 == True and result6 == False)
    
    if all_passed:
        print("✅ All tests passed! Never-win detection is working correctly.")
    else:
        print("❌ Some tests failed! Never-win detection has issues.")
        
    return all_passed

if __name__ == "__main__":
    test_never_win_detection()