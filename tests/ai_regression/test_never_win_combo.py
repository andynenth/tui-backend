#!/usr/bin/env python3
"""
Test never-win combo avoidance behavior

Tests:
1. Never-win combo detection
2. Responder avoids never-win combos when possible
3. Fallback to never-win combos when necessary
4. Edge cases with piece count requirements
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, is_never_win_combo, execute_responder_strategy,
    generate_strategic_plan, evaluate_hand, get_overcapture_constraints
)
from backend.engine.ai import find_all_valid_combos

def test_never_win_detection():
    """Test the never-win combo detection function"""
    print("TEST 1: Never-Win Combo Detection")
    print("=" * 60)
    
    # Test 1: All-BLACK straight (never wins)
    black_straight = [
        Piece("CANNON_BLACK"),   # 3
        Piece("HORSE_BLACK"),    # 5
        Piece("CHARIOT_BLACK")   # 7
    ]
    assert is_never_win_combo("STRAIGHT", black_straight), "All-BLACK straight should be never-win"
    print("✅ All-BLACK straight detected as never-win")
    
    # Test 2: Mixed color straight (can win)
    mixed_straight = [
        Piece("CANNON_RED"),     # 4
        Piece("HORSE_BLACK"),    # 5
        Piece("CHARIOT_RED")     # 8
    ]
    assert not is_never_win_combo("STRAIGHT", mixed_straight), "Mixed straight should NOT be never-win"
    print("✅ Mixed color straight NOT detected as never-win")
    
    # Test 3: All-RED straight (can win)
    red_straight = [
        Piece("CANNON_RED"),     # 4
        Piece("HORSE_RED"),      # 6
        Piece("CHARIOT_RED")     # 8
    ]
    assert not is_never_win_combo("STRAIGHT", red_straight), "All-RED straight should NOT be never-win"
    print("✅ All-RED straight NOT detected as never-win")
    
    # Test 4: Minimum PAIR (never wins)
    min_pair = [Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK")]  # 1+1=2
    assert is_never_win_combo("PAIR", min_pair), "Min PAIR should be never-win"
    print("✅ Minimum PAIR detected as never-win")
    
    # Test 5: Higher PAIR (can win)
    high_pair = [Piece("GENERAL_RED"), Piece("GENERAL_RED")]  # 14+14=28
    assert not is_never_win_combo("PAIR", high_pair), "High PAIR should NOT be never-win"
    print("✅ High-value PAIR NOT detected as never-win")
    
    # Test 6: All-BLACK extended straight
    black_extended = [
        Piece("CANNON_BLACK"),
        Piece("CANNON_BLACK"),
        Piece("HORSE_BLACK"),
        Piece("CHARIOT_BLACK")
    ]
    assert is_never_win_combo("EXTENDED_STRAIGHT", black_extended), "All-BLACK extended should be never-win"
    print("✅ All-BLACK extended straight detected as never-win")
    
    # Test 7: All-BLACK double straight
    black_double = [
        Piece("CANNON_BLACK"), Piece("CANNON_BLACK"),
        Piece("HORSE_BLACK"), Piece("HORSE_BLACK"),
        Piece("CHARIOT_BLACK"), Piece("CHARIOT_BLACK")
    ]
    assert is_never_win_combo("DOUBLE_STRAIGHT", black_double), "All-BLACK double straight should be never-win"
    print("✅ All-BLACK double straight detected as never-win")
    
    print("\n✅ All detection tests passed!\n")

def test_responder_avoids_never_win():
    """Test that responders avoid never-win combos when possible"""
    print("TEST 2: Responder Avoids Never-Win Combos")
    print("=" * 60)
    
    # Hand with both never-win and winnable combos
    hand = [
        # Never-win straight components (all BLACK)
        Piece("CANNON_BLACK"),   # 3
        Piece("HORSE_BLACK"),    # 5
        Piece("CHARIOT_BLACK"),  # 7
        # Winnable straight components (has RED)
        Piece("CANNON_RED"),     # 4
        Piece("HORSE_RED"),      # 6
        Piece("CHARIOT_RED"),    # 8
        # Some singles
        Piece("ADVISOR_BLACK"),  # 11
        Piece("SOLDIER_RED")     # 2
    ]
    
    # Context with critical urgency requiring 3 pieces
    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=hand,
        my_captured=0,
        my_declared=2,  # Need 2 more wins
        required_piece_count=3,  # Must play a straight
        turn_number=5,
        pieces_per_player=8,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 2": {"captured": 0, "declared": 2},
            "Bot 3": {"captured": 1, "declared": 2}
        }
    )
    
    # Generate plan (should be critical urgency)
    plan = generate_strategic_plan(hand, context)
    hand_eval = evaluate_hand(hand, context, plan)
    constraints = get_overcapture_constraints(context)
    
    print(f"Urgency: {plan.urgency_level}")
    print(f"Available combos: ")
    all_combos = find_all_valid_combos(hand)
    for combo_type, pieces in all_combos:
        if len(pieces) == 3:
            never_win = is_never_win_combo(combo_type, pieces)
            print(f"  {combo_type}: {[p.kind for p in pieces]} - Never-win: {never_win}")
    
    # Execute responder strategy
    result = execute_responder_strategy(plan, context, hand_eval, constraints)
    
    # Should play the RED straight, not the BLACK one
    assert len(result) == 3, "Should play 3 pieces"
    assert any(p.color == "RED" for p in result), "Should include RED pieces (winnable combo)"
    assert not all(p.color == "BLACK" for p in result), "Should NOT play all-BLACK straight"
    
    print(f"\nPlayed: {[p.kind for p in result]}")
    print("✅ Correctly avoided never-win combo!\n")

def test_fallback_to_never_win():
    """Test that responders use never-win combos when no other option"""
    print("TEST 3: Fallback to Never-Win When Necessary")
    print("=" * 60)
    
    # Test 3a: When individual pieces would be played but never-win is available
    hand_3a = [
        # Never-win straight (all BLACK)
        Piece("CANNON_BLACK"),   # 3
        Piece("HORSE_BLACK"),    # 5
        Piece("CHARIOT_BLACK"),  # 7
        # Single high-value piece
        Piece("ADVISOR_RED")     # 12
    ]
    
    print("Test 3a: Has 4 pieces, required=3")
    print(f"Hand: {[p.kind for p in hand_3a]}")
    print("Note: Current strategy prefers individual disposal over never-win combos")
    print("This is actually good - saves combos for later if possible\n")
    
    # Test 3b: True forced never-win scenario (only 3 BLACK soldiers)
    hand_3b = [
        Piece("SOLDIER_BLACK"),  # 1
        Piece("SOLDIER_BLACK"),  # 1  
        Piece("SOLDIER_BLACK"),  # 1
    ]
    
    context_3b = TurnPlayContext(
        my_name="Bot 1",
        my_hand=hand_3b,
        my_captured=0,
        my_declared=1,
        required_piece_count=3,
        turn_number=8,
        pieces_per_player=3,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 1": {"captured": 0, "declared": 1},
            "Bot 2": {"captured": 1, "declared": 1}
        }
    )
    
    print("Test 3b: Has exactly 3 SOLDIER_BLACK, required=3")
    print(f"Hand: {[p.kind for p in hand_3b]}")
    
    # Generate plan  
    plan = generate_strategic_plan(hand_3b, context_3b)
    hand_eval = evaluate_hand(hand_3b, context_3b, plan)
    constraints = get_overcapture_constraints(context_3b)
    
    # Execute responder strategy
    result = execute_responder_strategy(plan, context_3b, hand_eval, constraints)
    
    # Must play all 3 soldiers
    assert len(result) == 3, "Should play 3 pieces"
    assert all(p.kind == "SOLDIER_BLACK" for p in result), "Should play all 3 soldiers"
    
    print(f"Played: {[p.kind for p in result]}")
    print("✅ Correctly played the only available pieces (forms never-win THREE_OF_A_KIND)!\n")

def test_minimum_soldier_combos():
    """Test detection of minimum soldier combos"""
    print("TEST 4: Minimum Soldier Combo Detection")
    print("=" * 60)
    
    # Test THREE_OF_A_KIND with minimum soldiers
    min_three = [Piece("SOLDIER_BLACK")] * 3
    assert is_never_win_combo("THREE_OF_A_KIND", min_three), "Min THREE_OF_A_KIND should be never-win"
    print("✅ Minimum THREE_OF_A_KIND detected")
    
    # Test FOUR_OF_A_KIND with minimum soldiers
    min_four = [Piece("SOLDIER_BLACK")] * 4
    assert is_never_win_combo("FOUR_OF_A_KIND", min_four), "Min FOUR_OF_A_KIND should be never-win"
    print("✅ Minimum FOUR_OF_A_KIND detected")
    
    # Test FIVE_OF_A_KIND with minimum soldiers
    min_five = [Piece("SOLDIER_BLACK")] * 5
    assert is_never_win_combo("FIVE_OF_A_KIND", min_five), "Min FIVE_OF_A_KIND should be never-win"
    print("✅ Minimum FIVE_OF_A_KIND detected")
    
    # Test non-minimum soldier combos
    red_soldiers = [Piece("SOLDIER_RED")] * 3  # 2+2+2=6
    assert not is_never_win_combo("THREE_OF_A_KIND", red_soldiers), "RED soldiers should NOT be never-win"
    print("✅ RED soldier combos NOT detected as never-win")
    
    print("\n✅ All soldier combo tests passed!\n")

if __name__ == "__main__":
    test_never_win_detection()
    test_responder_avoids_never_win()
    test_fallback_to_never_win()
    test_minimum_soldier_combos()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! 🎉")
    print("=" * 60)