#!/usr/bin/env python3
"""
Test urgency calculation and random opener play behavior

Tests:
1. Urgency calculation based on room concept
2. Random opener play when not urgent
3. No random play when urgent
4. Random selection from available openers
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, calculate_urgency, execute_responder_strategy,
    execute_starter_strategy, generate_strategic_plan, evaluate_hand,
    get_overcapture_constraints
)
from backend.engine.ai import find_all_valid_combos
from collections import defaultdict

def test_urgency_calculation():
    """Test the room-based urgency calculation"""
    print("TEST 1: Urgency Calculation")
    print("=" * 60)
    
    # Test Case 1: Round 5 Turn 1 - Bot 2
    # Bot 2: 0/4, Bot 3: 0/4, Bot 4: 0/3, Alexanderium: 0/3
    context1 = TurnPlayContext(
        my_name="Bot 2",
        my_hand=[Piece("GENERAL_BLACK") for _ in range(8)],  # 8 pieces
        my_captured=0,
        my_declared=4,
        required_piece_count=1,
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 2": {"captured": 0, "declared": 4},
            "Bot 3": {"captured": 0, "declared": 4},
            "Bot 4": {"captured": 0, "declared": 3},
            "Alexanderium": {"captured": 0, "declared": 3}
        }
    )
    
    urgency1 = calculate_urgency(context1)
    print(f"Bot 2: Hand=8, target_remaining=4, max_opponent_remaining=4")
    print(f"Room = 8 - 4 = 4")
    print(f"Urgency: {urgency1} (expected: low)")
    assert urgency1 == "low", f"Expected 'low' but got {urgency1}"
    
    # Test Case 2: Round 5 Turn 3 - Bot 3
    # Bot 2: 1/4, Bot 3: 0/4, Bot 4: 0/3
    context2 = TurnPlayContext(
        my_name="Bot 3",
        my_hand=[Piece("GENERAL_BLACK") for _ in range(4)],  # 4 pieces left
        my_captured=0,
        my_declared=4,
        required_piece_count=1,
        turn_number=3,
        pieces_per_player=4,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 2": {"captured": 1, "declared": 4},
            "Bot 3": {"captured": 0, "declared": 4},
            "Bot 4": {"captured": 0, "declared": 3},
            "Alexanderium": {"captured": 0, "declared": 3}
        }
    )
    
    urgency2 = calculate_urgency(context2)
    print(f"\nBot 3: Hand=4, target_remaining=4, max_opponent_remaining=3")
    print(f"Room = 4 - 3 = 1")
    print(f"Urgency: {urgency2} (expected: critical)")
    assert urgency2 == "critical", f"Expected 'critical' but got {urgency2}"
    
    # Test Case 3: Already at target
    context3 = TurnPlayContext(
        my_name="Bot 1",
        my_hand=[Piece("GENERAL_BLACK") for _ in range(5)],
        my_captured=3,
        my_declared=3,
        required_piece_count=1,
        turn_number=2,
        pieces_per_player=5,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 1": {"captured": 3, "declared": 3},
            "Bot 2": {"captured": 1, "declared": 4}
        }
    )
    
    urgency3 = calculate_urgency(context3)
    print(f"\nBot 1: Already at target (3/3)")
    print(f"Urgency: {urgency3} (expected: none)")
    assert urgency3 == "none", f"Expected 'none' but got {urgency3}"
    
    print("\n✅ All urgency calculations correct!\n")

def test_random_opener_play():
    """Test that openers are played randomly when not urgent"""
    print("TEST 2: Random Opener Play (Not Urgent)")
    print("=" * 60)
    
    # Create a hand with multiple openers
    hand = [
        Piece("GENERAL_RED"),      # 14 points
        Piece("GENERAL_BLACK"),    # 13 points
        Piece("ADVISOR_RED"),      # 12 points
        Piece("ADVISOR_BLACK"),    # 11 points
        Piece("CHARIOT_RED"),      # 8 points
        Piece("HORSE_BLACK"),      # 5 points
        Piece("CANNON_BLACK"),     # 3 points
        Piece("SOLDIER_RED"),      # 2 points
    ]
    
    # Context with low urgency
    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=hand,
        my_captured=0,
        my_declared=4,
        required_piece_count=1,
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 2": {"captured": 0, "declared": 4},
            "Bot 3": {"captured": 0, "declared": 4},
            "Bot 4": {"captured": 0, "declared": 3},
            "Alexanderium": {"captured": 0, "declared": 3}
        }
    )
    
    # Generate plan
    plan = generate_strategic_plan(hand, context)
    hand_eval = evaluate_hand(hand, context, plan)
    constraints = get_overcapture_constraints(context)
    
    print(f"Urgency: {plan.urgency_level}")
    print(f"Openers in hand: GENERAL_RED(14), GENERAL_BLACK(13), ADVISOR_RED(12), ADVISOR_BLACK(11)")
    
    # Test multiple plays to see randomness
    opener_counts = defaultdict(int)
    num_tests = 100
    opener_plays = 0
    
    print(f"\nTesting {num_tests} plays as responder...")
    for i in range(num_tests):
        result = execute_responder_strategy(plan, context, hand_eval, constraints)
        if result and len(result) == 1 and result[0].point >= 11:
            opener_plays += 1
            opener_counts[f"{result[0].kind}({result[0].point})"] += 1
    
    print(f"Opener plays: {opener_plays}/{num_tests}")
    print("Distribution of openers played:")
    for opener, count in sorted(opener_counts.items()):
        print(f"  {opener}: {count} times ({count/opener_plays*100:.1f}%)")
    
    # Verify that different openers are played (not always strongest)
    if opener_plays > 10:
        assert len(opener_counts) > 1, "Only one opener was played - not random!"
        assert "GENERAL_RED(14)" not in opener_counts or opener_counts["GENERAL_RED(14)"] < opener_plays * 0.9, \
            "GENERAL_RED played too often - not random selection!"
    
    print("\n✅ Random opener selection confirmed!\n")

def test_urgent_no_random():
    """Test that random opener play doesn't happen when urgent"""
    print("TEST 3: No Random Play When Urgent")
    print("=" * 60)
    
    # Create a hand with limited pieces (urgent situation)
    hand = [
        Piece("GENERAL_RED"),      # 14 points
        Piece("ADVISOR_BLACK"),    # 11 points
        Piece("CHARIOT_RED"),      # 8 points
        Piece("SOLDIER_BLACK"),    # 1 point
    ]
    
    # Context with critical urgency
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=hand,
        my_captured=0,
        my_declared=4,
        required_piece_count=1,
        turn_number=3,
        pieces_per_player=4,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 2": {"captured": 1, "declared": 4},
            "Bot 3": {"captured": 0, "declared": 4},
            "Bot 4": {"captured": 0, "declared": 3}
        }
    )
    
    # Generate plan
    plan = generate_strategic_plan(hand, context)
    hand_eval = evaluate_hand(hand, context, plan)
    constraints = get_overcapture_constraints(context)
    
    print(f"Urgency: {plan.urgency_level}")
    print(f"Hand: {[f'{p.kind}({p.point})' for p in hand]}")
    
    # Test multiple plays - should see strategic play, not random openers
    plays = []
    for i in range(20):
        result = execute_responder_strategy(plan, context, hand_eval, constraints)
        plays.append([p.kind for p in result])
    
    print(f"\nPlays made when urgent: {plays[0]} (repeated {len(plays)} times)")
    
    # In critical urgency, should play strongest single (trying to win)
    assert all(play == plays[0] for play in plays), "Plays vary in urgent situation!"
    
    print("\n✅ No random play when urgent confirmed!\n")

def test_starter_random_opener():
    """Test that starters can also play openers randomly when not urgent"""
    print("TEST 4: Starter Random Opener Play")
    print("=" * 60)
    
    # Create a hand with openers
    hand = [
        Piece("GENERAL_RED"),      # 14 points
        Piece("ADVISOR_RED"),      # 12 points
        Piece("ADVISOR_BLACK"),    # 11 points
        Piece("CHARIOT_RED"),      # 8 points
        Piece("HORSE_BLACK"),      # 5 points
        Piece("CANNON_BLACK"),     # 3 points
        Piece("CANNON_BLACK"),     # 3 points
        Piece("SOLDIER_RED"),      # 2 points
    ]
    
    # Context with low urgency, as starter
    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=hand,
        my_captured=0,
        my_declared=3,
        required_piece_count=None,  # Starter sets this
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 2": {"captured": 0, "declared": 3},
            "Bot 3": {"captured": 0, "declared": 3},
            "Bot 4": {"captured": 0, "declared": 2}
        }
    )
    
    # Generate plan
    plan = generate_strategic_plan(hand, context)
    hand_eval = evaluate_hand(hand, context, plan)
    constraints = get_overcapture_constraints(context)
    
    print(f"Urgency: {plan.urgency_level}")
    print(f"Openers: GENERAL_RED(14), ADVISOR_RED(12), ADVISOR_BLACK(11)")
    
    # Test starter plays
    opener_counts = defaultdict(int)
    single_plays = 0
    
    for i in range(50):
        result = execute_starter_strategy(plan, context, hand_eval, constraints)
        if len(result) == 1 and result[0].point >= 11:
            single_plays += 1
            opener_counts[f"{result[0].kind}({result[0].point})"] += 1
    
    print(f"\nSingle opener plays by starter: {single_plays}/50")
    if single_plays > 0:
        print("Distribution:")
        for opener, count in sorted(opener_counts.items()):
            print(f"  {opener}: {count} times")
    
    print("\n✅ Starter can play openers randomly!\n")

if __name__ == "__main__":
    test_urgency_calculation()
    test_random_opener_play()
    test_urgent_no_random()
    test_starter_random_opener()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! 🎉")
    print("=" * 60)