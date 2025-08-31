"""
Simple test to verify AI responder fixes are working
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext,
    choose_strategic_play,
    is_never_win_combo
)
from backend.engine.rules import get_play_type


def test_responder_matches_play_type():
    """Test that responder properly matches play type"""
    # Create a hand with multiple valid pairs
    hand = [
        Piece("SOLDIER_BLACK"),  # Forms never-win pair
        Piece("SOLDIER_BLACK"),  
        Piece("HORSE_RED"),      # Forms good pair
        Piece("HORSE_RED"),      
        Piece("ELEPHANT_BLACK"), # Forms good pair
        Piece("ELEPHANT_BLACK"), 
        Piece("CANNON_RED"),     # Single
        Piece("ADVISOR_RED"),    # Single
    ]
    
    # Test 1: Responder must play PAIR when starter played PAIR
    context = TurnPlayContext(
        my_name="Bot 1",
        my_hand=hand,
        my_captured=2,
        my_declared=4,
        required_piece_count=2,
        required_play_type="PAIR",  # Starter played a PAIR
        turn_number=2,
        pieces_per_player=8,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 1": {"captured": 2, "declared": 4},
            "Bot 2": {"captured": 1, "declared": 3},
            "Bot 3": {"captured": 0, "declared": 2},
            "Bot 4": {"captured": 1, "declared": 1},
        }
    )
    
    # AI should play a valid pair
    pieces = choose_strategic_play(hand, context)
    play_type = get_play_type(pieces)
    
    print(f"Test 1 - Responder must match PAIR type:")
    print(f"  Played: {[p.kind for p in pieces]} - Type: {play_type}")
    
    if play_type == "PAIR":
        is_never_win = is_never_win_combo(play_type, pieces)
        if is_never_win:
            print(f"  ⚠️ WARNING: Played never-win SOLDIER_BLACK pair")
        else:
            print(f"  ✅ SUCCESS: Played valid non-never-win pair")
    else:
        print(f"  ❌ FAIL: Did not play a PAIR (played {play_type} instead)")
        

def test_responder_single_piece():
    """Test responder with single piece requirement"""
    hand = [
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("CANNON_RED"),     # 4 points
        Piece("HORSE_BLACK"),    # 5 points
        Piece("ELEPHANT_RED"),   # 10 points
        Piece("ADVISOR_RED"),    # 12 points
    ]
    
    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=hand,
        my_captured=3,
        my_declared=3,  # At target
        required_piece_count=1,
        required_play_type="SINGLE",
        turn_number=3,
        pieces_per_player=5,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 1": {"captured": 2, "declared": 4},
            "Bot 2": {"captured": 3, "declared": 3},  # At target
            "Bot 3": {"captured": 1, "declared": 2},
            "Bot 4": {"captured": 2, "declared": 1},
        }
    )
    
    # At target, should play weakest piece
    pieces = choose_strategic_play(hand, context)
    
    print(f"\nTest 2 - Responder at target plays weak:")
    print(f"  Played: {pieces[0].kind} ({pieces[0].point} points)")
    
    if pieces[0].point == 1:
        print(f"  ✅ SUCCESS: Played weakest piece (SOLDIER_BLACK)")
    else:
        print(f"  ⚠️ Played {pieces[0].kind} instead of weakest")


def test_critical_urgency_responder():
    """Test responder in critical urgency situation"""
    hand = [
        Piece("SOLDIER_BLACK"),  
        Piece("SOLDIER_BLACK"),  
        Piece("SOLDIER_BLACK"),  # Can form THREE_OF_A_KIND
        Piece("CANNON_RED"),     
        Piece("HORSE_BLACK"),    
        Piece("CHARIOT_BLACK"),  # Can form STRAIGHT [3,5,7]
    ]
    
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=hand,
        my_captured=0,
        my_declared=5,  # Needs 5 piles!
        required_piece_count=3,
        required_play_type="THREE_OF_A_KIND",
        turn_number=1,
        pieces_per_player=6,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 1": {"captured": 0, "declared": 2},
            "Bot 2": {"captured": 0, "declared": 1},
            "Bot 3": {"captured": 0, "declared": 5},  # Critical!
            "Bot 4": {"captured": 0, "declared": 0},
        }
    )
    
    # Should play THREE_OF_A_KIND even if it's never-win
    pieces = choose_strategic_play(hand, context)
    play_type = get_play_type(pieces)
    
    print(f"\nTest 3 - Critical urgency responder:")
    print(f"  Played: {[p.kind for p in pieces]} - Type: {play_type}")
    
    if play_type == "THREE_OF_A_KIND":
        print(f"  ✅ SUCCESS: Played required THREE_OF_A_KIND in critical situation")
    else:
        print(f"  ❌ FAIL: Did not play required type")


if __name__ == "__main__":
    print("Running simplified AI responder tests...")
    print("=" * 60)
    
    test_responder_matches_play_type()
    test_responder_single_piece()
    test_critical_urgency_responder()
    
    print("\n" + "=" * 60)
    print("Tests completed!")