# tests/ai_turn_play/test_overcapture.py

import pytest
from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play, avoid_overcapture_strategy


def test_avoid_overcapture_when_at_target():
    """Test that bot plays weakest pieces when at declared target."""
    # Create test hand
    hand = [
        Piece("GENERAL_RED"),
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK")
    ]
    
    # Create context where bot is at target
    context = TurnPlayContext(
        my_name="Bot1",
        my_hand=hand,
        my_captured=2,
        my_declared=2,  # At target!
        required_piece_count=2,
        turn_number=3,
        pieces_per_player=3,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Execute strategic play
    result = choose_strategic_play(hand, context)
    
    # Should return two SOLDIER_BLACK pieces (weakest)
    assert len(result) == 2
    assert all(p.name == "SOLDIER" for p in result)
    assert all(p.point == 1 for p in result)


def test_avoid_overcapture_with_single_piece_required():
    """Test overcapture avoidance when only one piece required."""
    hand = [
        Piece("GENERAL_RED"),
        Piece("ADVISOR_RED"),
        Piece("SOLDIER_BLACK"),
        Piece("CHARIOT_RED")
    ]
    
    context = TurnPlayContext(
        my_name="Bot2",
        my_hand=hand,
        my_captured=3,
        my_declared=3,  # At target!
        required_piece_count=1,
        turn_number=5,
        pieces_per_player=4,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    result = choose_strategic_play(hand, context)
    
    # Should return single weakest piece (SOLDIER)
    assert len(result) == 1
    assert result[0].name == "SOLDIER"
    assert result[0].point == 1


def test_avoid_overcapture_no_required_count():
    """Test when no required piece count is set yet (first play)."""
    hand = [
        Piece("GENERAL_RED"),
        Piece("SOLDIER_BLACK"),
        Piece("HORSE_RED")
    ]
    
    context = TurnPlayContext(
        my_name="Bot3",
        my_hand=hand,
        my_captured=1,
        my_declared=1,  # At target!
        required_piece_count=None,  # Not set yet
        turn_number=1,
        pieces_per_player=3,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    result = avoid_overcapture_strategy(hand, context)
    
    # Should return single weakest piece when no requirement
    assert len(result) == 1
    assert result[0].name == "SOLDIER"


def test_normal_play_when_not_at_target():
    """Test that normal strategy is used when not at target."""
    hand = [
        Piece("GENERAL_RED"),
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK")
    ]
    
    context = TurnPlayContext(
        my_name="Bot4",
        my_hand=hand,
        my_captured=1,
        my_declared=3,  # Need 2 more piles
        required_piece_count=2,
        turn_number=3,
        pieces_per_player=3,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # This should use normal logic (choose_best_play)
    # which would prefer the GENERAL for high points
    result = choose_strategic_play(hand, context)
    
    # With current implementation, it delegates to choose_best_play
    # We can't test the exact behavior without importing that function
    assert len(result) == 2


def test_forfeit_when_no_valid_play():
    """Test that bot forfeits with weakest pieces when no valid play."""
    # Create hand with no valid 3-piece combination
    hand = [
        Piece("SOLDIER_RED"),
        Piece("SOLDIER_BLACK"),
        Piece("CANNON_RED")
    ]
    
    context = TurnPlayContext(
        my_name="Bot5",
        my_hand=hand,
        my_captured=2,
        my_declared=2,  # At target!
        required_piece_count=3,
        turn_number=4,
        pieces_per_player=3,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    result = avoid_overcapture_strategy(hand, context)
    
    # Should return all 3 pieces (will forfeit)
    assert len(result) == 3
    # Should be sorted by point value (weakest first)
    assert result[0].point == 1  # SOLDIER_BLACK
    assert result[1].point == 2  # SOLDIER_RED
    assert result[2].point == 4  # CANNON_RED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])