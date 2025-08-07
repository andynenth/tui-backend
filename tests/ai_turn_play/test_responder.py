# tests/ai_turn_play/test_responder.py
"""
Tests for AI responder strategies.

Tests that AI makes appropriate decisions when responding to other players' leads.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, StrategicPlan, 
    choose_strategic_play, execute_responder_strategy, generate_strategic_plan
)


def test_critical_urgency_beat_winner():
    """Test that AI tries to beat current winner when urgency is critical."""
    # Create hand with strong pair
    hand = [
        Piece("GENERAL_RED"),     # 14 points
        Piece("GENERAL_RED"),     # 14 points - can make strong pair  
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK"),   # 1 point - can make weak pair
    ]
    
    # Current winning play is a weak pair
    current_plays = [
        {
            'player': Player("opponent1"),
            'pieces': [Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK")],  # Weak pair
            'play_type': 'PAIR'
        }
    ]
    
    # Context: critical urgency, need piles
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=0,
        my_declared=3,  # Need 3 piles
        required_piece_count=2,  # Must play pair
        turn_number=7,  # Late game
        pieces_per_player=2,  # Almost out of pieces!
        am_i_starter=False,
        current_plays=current_plays,
        revealed_pieces=[],
        player_states={}
    )
    
    # Generate plan to see what's available
    plan = generate_strategic_plan(hand, context)
    result = choose_strategic_play(hand, context)
    
    # Should play GENERAL pair to beat weak SOLDIER pair
    assert len(result) == 2, f"Expected pair, got {len(result)} pieces"
    assert all(p.name == "GENERAL" for p in result), "Expected GENERAL pair"
    
    print("✅ Test 1 passed: AI beats current winner in critical situation")


def test_at_target_avoid_winning():
    """Test that AI avoids winning when already at target."""
    # Create hand with mixed pieces
    hand = [
        Piece("ADVISOR_RED"),     # 12 points
        Piece("ADVISOR_RED"),     # 12 points - could make strong pair
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK"),   # 1 point - could make weak pair
    ]
    
    # Current winning play
    current_plays = [
        {
            'player': Player("opponent1"),
            'pieces': [Piece("HORSE_BLACK"), Piece("HORSE_BLACK")],  # Medium pair
            'play_type': 'PAIR'
        }
    ]
    
    # Context: already at target
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=2,
        my_declared=2,  # Already at target!
        required_piece_count=2,
        turn_number=4,
        pieces_per_player=4,
        am_i_starter=False,
        current_plays=current_plays,
        revealed_pieces=[],
        player_states={}
    )
    
    result = choose_strategic_play(hand, context)
    
    # Should play weakest pair (SOLDIERs) to avoid winning
    assert len(result) == 2, f"Expected pair, got {len(result)} pieces"
    assert sum(p.point for p in result) <= 2, "Expected weak SOLDIER pair to avoid winning"
    
    print("✅ Test 2 passed: AI avoids winning when at target")


def test_medium_urgency_strategic_winning():
    """Test strategic decision making with medium urgency."""
    # Create hand with options
    hand = [
        Piece("CHARIOT_RED"),     # 8 points
        Piece("CHARIOT_RED"),     # 8 points - can make pair
        Piece("CANNON_BLACK"),    # 3 points
        Piece("CANNON_BLACK"),    # 3 points - can make weaker pair
        Piece("SOLDIER_BLACK"),   # 1 point
    ]
    
    # Current winning play is medium strength
    current_plays = [
        {
            'player': Player("opponent1"),
            'pieces': [Piece("HORSE_RED"), Piece("HORSE_RED")],  # 6+6=12 points
            'play_type': 'PAIR'
        }
    ]
    
    # Context: medium urgency (need 2 piles with 4 pieces = 0.5 ratio)
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=1,
        my_declared=3,  # Need 2 more
        required_piece_count=2,
        turn_number=4,
        pieces_per_player=4,  # Changed to 4 to get medium urgency
        am_i_starter=False,
        current_plays=current_plays,
        revealed_pieces=[],
        player_states={}
    )
    
    # Generate plan to understand the situation
    plan = generate_strategic_plan(hand, context)
    print(f"Valid combos: {[(t, [p.name for p in pieces]) for t, pieces in plan.valid_combos]}")
    print(f"Urgency: {plan.urgency_level}, Target remaining: {plan.target_remaining}")
    
    result = choose_strategic_play(hand, context)
    print(f"Result pieces: {[(p.name, p.point) for p in result]}")
    
    # With medium urgency and needing 2 piles, should try to win
    # CHARIOT (8+8=16) beats HORSE (6+6=12), but CANNON pair (3+3=6) does not
    assert len(result) == 2, f"Expected pair, got {len(result)} pieces"
    
    # With medium urgency, AI should try to win turns, so should play CHARIOT
    assert all(p.name == "CHARIOT" for p in result), f"Expected CHARIOT pair to win turn, got {[p.name for p in result]}"
    
    print("✅ Test 3 passed: AI makes strategic winning decision with medium urgency")


def test_low_urgency_cheap_win():
    """Test that AI only wins cheaply when urgency is low."""
    # Create hand where weakest valid combo can win
    hand = [
        Piece("ELEPHANT_RED"),    # 10 points
        Piece("ELEPHANT_RED"),    # 10 points - strong pair
        Piece("CANNON_BLACK"),    # 3 points
        Piece("CANNON_BLACK"),    # 3 points - weak pair that can still win
        Piece("SOLDIER_BLACK"),   # 1 point
    ]
    
    # Current winning play is very weak
    current_plays = [
        {
            'player': Player("opponent1"),
            'pieces': [Piece("SOLDIER_BLACK"), Piece("SOLDIER_RED")],  # 1+2=3 points
            'play_type': 'PAIR'
        }
    ]
    
    # Context: low urgency
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=0,
        my_declared=1,  # Only need 1 pile
        required_piece_count=2,
        turn_number=2,
        pieces_per_player=6,
        am_i_starter=False,
        current_plays=current_plays,
        revealed_pieces=[],
        player_states={}
    )
    
    result = choose_strategic_play(hand, context)
    
    # Should play CANNON pair (cheap win) rather than ELEPHANT pair
    assert len(result) == 2, f"Expected pair, got {len(result)} pieces"
    assert all(p.name == "CANNON" for p in result), "Expected cheap CANNON pair win"
    
    print("✅ Test 4 passed: AI wins cheaply with low urgency")


def test_no_valid_combo_responder():
    """Test responder behavior when no valid combos available."""
    # Create hand with no valid pairs
    hand = [
        Piece("GENERAL_RED"),     # 14 points - single
        Piece("ADVISOR_BLACK"),   # 11 points - single
        Piece("CHARIOT_RED"),     # 8 points - single
        Piece("HORSE_BLACK"),     # 5 points - single
    ]
    
    current_plays = [
        {
            'player': Player("opponent1"),
            'pieces': [Piece("CANNON_RED"), Piece("CANNON_RED")],
            'play_type': 'PAIR'
        }
    ]
    
    # Context: must play 2 pieces
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=1,
        my_declared=2,
        required_piece_count=2,
        turn_number=3,
        pieces_per_player=4,
        am_i_starter=False,
        current_plays=current_plays,
        revealed_pieces=[],
        player_states={}
    )
    
    result = choose_strategic_play(hand, context)
    
    # Should play weakest 2 pieces
    assert len(result) == 2, f"Expected 2 pieces, got {len(result)}"
    assert result[0].name == "HORSE" and result[1].name == "CHARIOT", \
        f"Expected HORSE and CHARIOT (weakest), got {[p.name for p in result]}"
    
    print("✅ Test 5 passed: Responder plays weakest pieces when no valid combo")


if __name__ == "__main__":
    print("Testing responder strategies...\n")
    
    test_critical_urgency_beat_winner()
    test_at_target_avoid_winning()
    test_medium_urgency_strategic_winning()
    test_low_urgency_cheap_win()
    test_no_valid_combo_responder()
    
    print("\n✅ All responder tests passed!")