#!/usr/bin/env python3
"""Test script for new bug detection features"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.ai_bug_detector import AIBugDetector, BugSeverity

def test_declaration_bugs():
    """Test declaration phase bug detection"""
    detector = AIBugDetector()
    
    print("Testing Declaration Phase Bugs...")
    print("-" * 40)
    
    # Test 1: Excessive zero declarations
    data1 = {
        'final_declaration': 0,
        'position_in_order': 1,
        'previous_declarations': [1, 2],
        'zero_streak': 3,  # More than 2
        'decision_factors': {'pile_room': 5},
        'play_list': []
    }
    bugs1 = detector.check_declaration_bugs("Bot1", data1)
    print(f"Test 1 - Excessive zeros: {len(bugs1)} bugs")
    for bug in bugs1:
        print(f"  - {bug.bug_type}: {bug.description}")
    
    # Test 2: Last player sum of 8
    data2 = {
        'final_declaration': 3,
        'position_in_order': 3,  # Last player
        'previous_declarations': [2, 2, 1],  # Total = 5, +3 = 8
        'zero_streak': 0,
        'decision_factors': {'pile_room': 3},
        'play_list': []
    }
    bugs2 = detector.check_declaration_bugs("Bot4", data2)
    print(f"\nTest 2 - Last player sum 8: {len(bugs2)} bugs")
    for bug in bugs2:
        print(f"  - {bug.bug_type}: {bug.description}")
    
    # Test 3: Clean declaration (no bugs)
    data3 = {
        'final_declaration': 2,
        'position_in_order': 2,
        'previous_declarations': [1, 3],
        'zero_streak': 0,
        'decision_factors': {'pile_room': 4},
        'play_list': [{'type': 'opener'}, {'type': 'combo'}]
    }
    bugs3 = detector.check_declaration_bugs("Bot3", data3)
    print(f"\nTest 3 - Clean declaration: {len(bugs3)} bugs")

def test_turn_play_bugs():
    """Test turn play phase bug detection"""
    detector = AIBugDetector()
    
    print("\n\nTesting Turn Play Phase Bugs...")
    print("-" * 40)
    
    # Test 1: Playing piece not in hand
    data1 = {
        'selected_play': ['GENERAL_RED', 'ADVISOR_BLACK'],
        'hand_before': ['SOLDIER_RED', 'ELEPHANT_BLACK', 'ADVISOR_BLACK'],
        'play_type': 'PAIR',
        'my_captured': 1,
        'my_declared': 3,
        'pieces_remaining': 4,
        'required_piece_count': 2
    }
    bugs1 = detector.check_turn_play_bugs("Bot1", data1)
    print(f"Test 1 - Piece not in hand: {len(bugs1)} bugs")
    for bug in bugs1:
        print(f"  - {bug.bug_type}: {bug.description}")
    
    # Test 2: Wrong piece count
    data2 = {
        'selected_play': ['SOLDIER_RED'],
        'hand_before': ['SOLDIER_RED', 'ELEPHANT_BLACK'],
        'play_type': 'SINGLE',
        'my_captured': 0,
        'my_declared': 2,
        'pieces_remaining': 2,
        'required_piece_count': 3  # Should play 3 pieces
    }
    bugs2 = detector.check_turn_play_bugs("Bot2", data2)
    print(f"\nTest 2 - Wrong piece count: {len(bugs2)} bugs")
    for bug in bugs2:
        print(f"  - {bug.bug_type}: {bug.description}")
    
    # Test 3: Clean play (no bugs)
    data3 = {
        'selected_play': ['SOLDIER_RED', 'SOLDIER_BLACK'],
        'hand_before': ['SOLDIER_RED', 'SOLDIER_BLACK', 'ELEPHANT_BLACK'],
        'play_type': 'PAIR',
        'my_captured': 1,
        'my_declared': 2,
        'pieces_remaining': 3,
        'required_piece_count': 2
    }
    bugs3 = detector.check_turn_play_bugs("Bot3", data3)
    print(f"\nTest 3 - Clean play: {len(bugs3)} bugs")

def test_bug_report():
    """Test bug report generation"""
    detector = AIBugDetector()
    
    # Add some test bugs
    data1 = {
        'final_declaration': 0,
        'position_in_order': 3,
        'previous_declarations': [2, 3, 3],
        'zero_streak': 3,
        'decision_factors': {'pile_room': 0},
        'play_list': []
    }
    detector.check_declaration_bugs("Bot4", data1)
    
    data2 = {
        'selected_play': ['GENERAL_RED'],
        'hand_before': ['SOLDIER_RED', 'ELEPHANT_BLACK'],
        'play_type': 'SINGLE',
        'my_captured': 0,
        'my_declared': 1,
        'pieces_remaining': 2,
        'required_piece_count': 1
    }
    detector.check_turn_play_bugs("Bot1", data2)
    
    print("\n\nBug Report:")
    print("=" * 60)
    print(detector.generate_bug_report())

if __name__ == "__main__":
    test_declaration_bugs()
    test_turn_play_bugs()
    test_bug_report()