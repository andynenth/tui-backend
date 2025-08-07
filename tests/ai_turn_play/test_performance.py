# tests/ai_turn_play/test_performance.py
"""
Performance tests for AI turn play system.

Tests that AI decisions are made within acceptable time limits.
"""

import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, choose_strategic_play, generate_strategic_plan
)


def test_decision_time_simple():
    """Test AI decision time for simple hands."""
    # Create simple hand
    hand = [
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_RED"),
        Piece("CANNON_BLACK"),
        Piece("HORSE_RED")
    ]
    
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=1,
        turn_number=1,
        pieces_per_player=4,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Measure decision time
    start_time = time.time()
    result = choose_strategic_play(hand, context)
    end_time = time.time()
    
    decision_time_ms = (end_time - start_time) * 1000
    
    assert decision_time_ms < 100, f"Decision took {decision_time_ms:.2f}ms (target < 100ms)"
    print(f"✅ Test 1 passed: Simple decision in {decision_time_ms:.2f}ms")


def test_decision_time_complex():
    """Test AI decision time for complex hands with many combos."""
    # Create complex hand with many possible combinations
    hand = [
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK"),  # THREE_OF_A_KIND
        Piece("GENERAL_RED"),
        Piece("ADVISOR_RED"),
        Piece("ELEPHANT_RED"),   # STRAIGHT
        Piece("CANNON_BLACK"),
        Piece("HORSE_BLACK")
    ]
    
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=1,
        my_declared=4,
        required_piece_count=3,
        turn_number=3,
        pieces_per_player=5,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Measure decision time
    start_time = time.time()
    result = choose_strategic_play(hand, context)
    end_time = time.time()
    
    decision_time_ms = (end_time - start_time) * 1000
    
    assert decision_time_ms < 100, f"Decision took {decision_time_ms:.2f}ms (target < 100ms)"
    print(f"✅ Test 2 passed: Complex decision in {decision_time_ms:.2f}ms")


def test_plan_generation_performance():
    """Test performance of strategic plan generation."""
    # Create hand with many options
    hand = [
        Piece("GENERAL_RED"),
        Piece("GENERAL_RED"),     # PAIR
        Piece("ADVISOR_BLACK"),
        Piece("ADVISOR_BLACK"),   # PAIR
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK"),   # THREE_OF_A_KIND
        Piece("CANNON_RED")
    ]
    
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=0,
        my_declared=3,
        required_piece_count=None,
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Measure plan generation time
    start_time = time.time()
    plan = generate_strategic_plan(hand, context)
    end_time = time.time()
    
    plan_time_ms = (end_time - start_time) * 1000
    
    assert plan_time_ms < 50, f"Plan generation took {plan_time_ms:.2f}ms (target < 50ms)"
    print(f"✅ Test 3 passed: Plan generation in {plan_time_ms:.2f}ms")


def test_responder_decision_performance():
    """Test performance when responding to opponent plays."""
    hand = [
        Piece("CHARIOT_RED"),
        Piece("CHARIOT_RED"),
        Piece("HORSE_BLACK"),
        Piece("HORSE_BLACK"),
        Piece("CANNON_RED")
    ]
    
    # Simulate current plays
    current_plays = [
        {
            'player': Player("opponent1"),
            'pieces': [Piece("CANNON_BLACK"), Piece("CANNON_BLACK")],
            'play_type': 'PAIR'
        }
    ]
    
    context = TurnPlayContext(
        my_hand=hand,
        my_captured=1,
        my_declared=3,
        required_piece_count=2,
        turn_number=4,
        pieces_per_player=5,
        am_i_starter=False,
        current_plays=current_plays,
        revealed_pieces=[],
        player_states={}
    )
    
    # Measure responder decision time
    start_time = time.time()
    result = choose_strategic_play(hand, context)
    end_time = time.time()
    
    decision_time_ms = (end_time - start_time) * 1000
    
    assert decision_time_ms < 100, f"Responder decision took {decision_time_ms:.2f}ms (target < 100ms)"
    print(f"✅ Test 4 passed: Responder decision in {decision_time_ms:.2f}ms")


def test_average_performance():
    """Test average performance across multiple decisions."""
    # Create various hands
    test_hands = [
        [Piece("SOLDIER_BLACK"), Piece("CANNON_RED"), Piece("HORSE_BLACK"), Piece("ADVISOR_RED")],
        [Piece("GENERAL_RED"), Piece("GENERAL_RED"), Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK")],
        [Piece("ELEPHANT_RED"), Piece("ADVISOR_RED"), Piece("GENERAL_RED"), Piece("CANNON_BLACK")],
        [Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK"), Piece("HORSE_RED")],
        [Piece("CHARIOT_RED"), Piece("HORSE_RED"), Piece("CANNON_RED"), Piece("SOLDIER_BLACK")]
    ]
    
    total_time = 0
    num_decisions = 0
    
    for hand in test_hands:
        for captured in [0, 1, 2]:
            for am_starter in [True, False]:
                context = TurnPlayContext(
                    my_hand=hand,
                    my_captured=captured,
                    my_declared=3,
                    required_piece_count=2 if not am_starter else None,
                    turn_number=2,
                    pieces_per_player=4,
                    am_i_starter=am_starter,
                    current_plays=[],
                    revealed_pieces=[],
                    player_states={}
                )
                
                start_time = time.time()
                result = choose_strategic_play(hand, context)
                end_time = time.time()
                
                total_time += (end_time - start_time)
                num_decisions += 1
    
    avg_time_ms = (total_time / num_decisions) * 1000
    
    assert avg_time_ms < 50, f"Average decision time {avg_time_ms:.2f}ms (target < 50ms)"
    print(f"✅ Test 5 passed: Average decision time {avg_time_ms:.2f}ms over {num_decisions} decisions")


if __name__ == "__main__":
    print("Testing AI turn play performance...\n")
    
    test_decision_time_simple()
    test_decision_time_complex()
    test_plan_generation_performance()
    test_responder_decision_performance()
    test_average_performance()
    
    print("\n✅ All performance tests passed! AI decisions are fast enough.")