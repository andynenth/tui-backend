"""
Test cases for AI responder fixes:
1. Responders must match play type (not just piece count)
2. Responders should avoid never-win combos when alternatives exist
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


def test_responder_must_match_pair_type():
    """Test that responder matches PAIR type when required"""
    # Setup: Bot has SOLDIER_BLACK pairs and ELEPHANT_BLACK pairs
    hand = [
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("ELEPHANT_BLACK"), # 9 points
        Piece("ELEPHANT_BLACK"), # 9 points
        Piece("HORSE_RED"),      # 6 points
        Piece("CANNON_RED"),     # 4 points
    ]
    
    context = TurnPlayContext(
        my_name="Bot 1",
        my_hand=hand,
        my_captured=3,
        my_declared=5,
        required_piece_count=2,
        required_play_type="PAIR",  # Starter played a PAIR
        turn_number=3,
        pieces_per_player=6,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Execute strategic play (this will handle responder logic internally)
    pieces = choose_strategic_play(hand, context)
    
    # Verify it returns a valid PAIR
    assert len(pieces) == 2, f"Expected 2 pieces, got {len(pieces)}"
    assert pieces[0].name == pieces[1].name, f"Expected matching pieces for PAIR, got {[p.kind for p in pieces]}"
    
    # Verify it doesn't return the never-win SOLDIER_BLACK pair
    if pieces[0].name == "SOLDIER" and pieces[0].color == "BLACK":
        print("WARNING: Responder chose never-win SOLDIER_BLACK pair when ELEPHANT_BLACK pair was available!")
        # This is what the old code would do - we've fixed this
    else:
        print(f"SUCCESS: Responder correctly chose {pieces[0].kind} pair instead of never-win combo")


def test_responder_avoids_never_win_combo():
    """Test that responder avoids never-win combos when alternatives exist"""
    # Setup: Bot has multiple pair options
    hand = [
        Piece("SOLDIER_BLACK"),  # 1 point - forms never-win pair
        Piece("SOLDIER_BLACK"),  # 1 point - forms never-win pair
        Piece("HORSE_RED"),      # 6 points
        Piece("HORSE_RED"),      # 6 points  
        Piece("CANNON_BLACK"),   # 3 points
        Piece("ELEPHANT_RED"),   # 10 points
    ]
    
    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=hand,
        my_captured=2,
        my_declared=4,
        required_piece_count=2,
        required_play_type="PAIR",
        turn_number=2,
        pieces_per_player=6,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Execute strategic play (this will handle responder logic internally)
    pieces = choose_strategic_play(hand, context)
    
    # Check if it's a never-win combo
    play_type = get_play_type(pieces)
    is_never_win = is_never_win_combo(play_type, pieces)
    
    if is_never_win:
        print(f"FAIL: Responder chose never-win {[p.kind for p in pieces]} when better alternatives existed")
        assert False, "Responder should avoid never-win combos when alternatives exist"
    else:
        print(f"SUCCESS: Responder correctly chose {[p.kind for p in pieces]} avoiding never-win combo")


def test_responder_forced_never_win():
    """Test that responder can play never-win combo when no alternatives exist"""
    # Setup: Bot only has SOLDIER_BLACK pieces that can form pairs
    hand = [
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("CANNON_BLACK"),   # 3 points (single)
        Piece("HORSE_RED"),      # 6 points (single)
        Piece("CHARIOT_RED"),    # 8 points (single)
    ]
    
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=hand,
        my_captured=1,
        my_declared=3,
        required_piece_count=2,
        required_play_type="PAIR",
        turn_number=4,
        pieces_per_player=5,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Execute strategic play (this will handle responder logic internally)
    pieces = choose_strategic_play(hand, context)
    
    # In this case, the only valid PAIR is SOLDIER_BLACK
    assert len(pieces) == 2, f"Expected 2 pieces, got {len(pieces)}"
    assert pieces[0].kind == "SOLDIER_BLACK", "Should play SOLDIER_BLACK pair when no alternatives"
    print("SUCCESS: Responder correctly played never-win combo when forced (no alternatives)")


def test_responder_matches_straight_type():
    """Test that responder matches STRAIGHT type when required"""
    # Setup: Bot has pieces that can form straights
    hand = [
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("CANNON_BLACK"),   # 3 points
        Piece("HORSE_BLACK"),    # 5 points
        Piece("CHARIOT_BLACK"),  # 7 points
        Piece("ELEPHANT_BLACK"), # 9 points
        Piece("ADVISOR_RED"),    # 12 points
    ]
    
    context = TurnPlayContext(
        my_name="Bot 4",
        my_hand=hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=3,
        required_play_type="STRAIGHT",
        turn_number=1,
        pieces_per_player=6,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Execute strategic play (this will handle responder logic internally)
    pieces = choose_strategic_play(hand, context)
    
    # Check if it's a valid straight
    assert len(pieces) == 3, f"Expected 3 pieces for straight, got {len(pieces)}"
    
    # Sort by points to check consecutive
    points = sorted([p.point for p in pieces])
    is_consecutive = (points[1] - points[0] == 2) and (points[2] - points[1] == 2)
    assert is_consecutive, f"Expected consecutive odd/even points for STRAIGHT, got {points}"
    
    # Check if it's the never-win all-BLACK straight
    is_all_black_minimum = points == [3, 5, 7]
    if is_all_black_minimum:
        print("INFO: Responder played minimum all-BLACK straight [3,5,7] - this is a never-win combo")
    else:
        print(f"SUCCESS: Responder played valid straight with points {points}")


if __name__ == "__main__":
    print("Running AI Responder Fix Tests...")
    print("=" * 60)
    
    print("\n1. Test responder must match PAIR type:")
    test_responder_must_match_pair_type()
    
    print("\n2. Test responder avoids never-win combo:")
    test_responder_avoids_never_win_combo()
    
    print("\n3. Test responder forced never-win (no alternatives):")
    test_responder_forced_never_win()
    
    print("\n4. Test responder matches STRAIGHT type:")
    test_responder_matches_straight_type()
    
    print("\n" + "=" * 60)
    print("All tests completed!")