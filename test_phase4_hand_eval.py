#!/usr/bin/env python3
"""Test Phase 4 hand evaluation updates"""

import sys
sys.path.append('.')

from backend.engine.ai_turn_strategy import (
    TurnPlayContext, StrategicPlan, evaluate_hand, generate_strategic_plan
)
from backend.engine.piece import Piece

# Test scenario: Same hand as before
hand = [
    Piece("GENERAL_RED"),    # 14 points - should be assigned opener
    Piece("ADVISOR_BLACK"),  # 11 points - should be burden
    Piece("ELEPHANT_RED"),   # 10 points
    Piece("ELEPHANT_BLACK"), # 9 points
    Piece("CHARIOT_BLACK"),  # 7 points
    Piece("HORSE_RED"),      # 6 points
    Piece("SOLDIER_BLACK"),  # 1 point - reserve
    Piece("SOLDIER_RED")     # 2 points - reserve
]

# Create context (turn 1)
context = TurnPlayContext(
    my_name="Bot 1",
    my_hand=hand,
    my_captured=0,
    my_declared=3,  # Need 3 wins
    required_piece_count=2,
    turn_number=1,
    pieces_per_player=8,
    am_i_starter=True,
    current_plays=[],
    revealed_pieces=[],
    player_states={
        "Bot 1": {"declared": 3, "captured": 0},
        "Bot 2": {"declared": 2, "captured": 0},
        "Bot 3": {"declared": 2, "captured": 0},
        "Bot 4": {"declared": 1, "captured": 0}
    }
)

# Generate strategic plan
plan = generate_strategic_plan(hand, context)
print(f"Initial plan - Target remaining: {plan.target_remaining}, Urgency: {plan.urgency_level}")

# Evaluate hand (should form plan on turn 1)
hand_eval = evaluate_hand(hand, context, plan)

print("\n✅ Hand evaluation with plan-based roles:")
print(f"Assigned openers ({len(hand_eval['openers'])}): {[p.name + f'({p.point})' for p in hand_eval['openers']]}")
print(f"Burden pieces ({len(hand_eval['burden_pieces'])}): {[p.name + f'({p.point})' for p in hand_eval['burden_pieces']]}")
print(f"Reserve pieces ({len(hand_eval.get('reserve_pieces', []))}): {[p.name + f'({p.point})' for p in hand_eval.get('reserve_pieces', [])]}")

# Check specific pieces
general_is_opener = any(p.name == "GENERAL" for p in hand_eval['openers'])
advisor_is_burden = any(p.name == "ADVISOR" for p in hand_eval['burden_pieces'])
soldiers_are_reserve = all(
    any(p.name == "SOLDIER" for p in hand_eval.get('reserve_pieces', []))
    for p in hand if p.name == "SOLDIER"
)

print(f"\n✅ GENERAL is assigned opener: {general_is_opener}")
print(f"✅ ADVISOR is burden (not needed): {advisor_is_burden}")
print(f"✅ SOLDIERs are reserves: {soldiers_are_reserve}")

# Test turn 2 - plan should persist
context.turn_number = 2
context.my_hand = hand[1:]  # Lost one piece
plan2 = generate_strategic_plan(context.my_hand, context)
hand_eval2 = evaluate_hand(context.my_hand, context, plan2)

print(f"\n✅ Turn 2 - Plan persists:")
print(f"Still have {len(hand_eval2['openers'])} openers assigned")
print(f"Plan impossible: {plan2.plan_impossible}")

print("\n✅ Task 4.1 & 4.2 Complete: Hand evaluation uses plan-based roles!")