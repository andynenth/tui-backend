#!/usr/bin/env python3
"""Trace why Bot 2 didn't play THREE_OF_A_KIND on turn 1"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, choose_strategic_play, form_execution_plan,
    calculate_urgency, get_overcapture_constraints, should_play_opener_or_combo
)
from backend.engine.ai import find_all_valid_combos
from backend.engine.rules import get_play_type

def trace_bot2_decision():
    """Trace Bot 2's turn 1 decision"""
    
    # Create Bot 2's hand
    hand = [
        Piece("GENERAL_RED"),      # 14 points
        Piece("ADVISOR_RED"),      # 12 points
        Piece("HORSE_RED"),        # 6 points
        Piece("SOLDIER_RED"),      # 2 points
        Piece("SOLDIER_RED"),      # 2 points
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK"),   # 1 point - THREE OF A KIND!
    ]
    
    print("BOT 2 HAND:")
    for p in sorted(hand, key=lambda x: x.point, reverse=True):
        print(f"  {p.kind}: {p.point} points")
    
    # Create context - Bot 2 is starter
    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=hand,
        my_captured=0,
        my_declared=5,
        required_piece_count=None,  # Starter chooses
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 2": {"captured": 0, "declared": 5},
            "Bot 3": {"captured": 0, "declared": 0},
            "Bot 4": {"captured": 0, "declared": 0},
            "Alexanderium": {"captured": 0, "declared": 4}
        }
    )
    
    # Find all valid combos
    print("\nFINDING VALID COMBOS...")
    valid_combos = find_all_valid_combos(hand)
    print(f"Found {len(valid_combos)} valid combos:")
    for combo_type, pieces in valid_combos:
        if combo_type == "THREE_OF_A_KIND":
            piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
            print(f"  *** {combo_type}: {piece_str} ***")
        else:
            piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
            print(f"  {combo_type}: {piece_str}")
    
    # Check urgency and form plan
    print("\nCALCULATING URGENCY...")
    urgency = calculate_urgency(context)
    print(f"Urgency: {urgency}")
    
    print("\nFORMING EXECUTION PLAN...")
    plan = form_execution_plan(hand, context, valid_combos)
    print(f"Assigned combos: {len(plan['assigned_combos'])}")
    for combo_type, pieces in plan['assigned_combos']:
        piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
        print(f"  - {combo_type}: {piece_str}")
    
    # Now trace the actual play decision
    print("\nTRACING PLAY DECISION...")
    print("Bot 2 is STARTER - checking should_play_opener_or_combo()...")
    
    # Check the opener/combo decision logic
    should_play = should_play_opener_or_combo(
        plan['main_plan'], 
        context, 
        plan['assigned_openers'],
        plan['reserve_pieces']
    )
    print(f"should_play_opener_or_combo returned: {should_play}")
    
    if should_play:
        print("\nChecking what to play...")
        # Check if prefers single opener
        if plan['assigned_openers'] and len(plan['assigned_openers']) == 1:
            print(f"  Would play single opener: {plan['assigned_openers'][0].kind}({plan['assigned_openers'][0].point})")
        elif plan['assigned_combos']:
            print("  Would play from assigned combos:")
            for combo_type, pieces in plan['assigned_combos']:
                piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
                print(f"    - {combo_type}: {piece_str}")
    
    # Get the actual chosen play
    print("\nACTUAL CHOSEN PLAY:")
    chosen = choose_strategic_play(hand, context)
    if chosen:
        play_str = "+".join([f"{p.kind}({p.point})" for p in chosen])
        total = sum(p.point for p in chosen)
        play_type = get_play_type(chosen)
        print(f"  {play_str} = {total} points ({play_type})")
        print(f"  Piece count: {len(chosen)}")

if __name__ == "__main__":
    trace_bot2_decision()