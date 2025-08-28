#!/usr/bin/env python3
"""Debug Bot 4's plan formation in detail"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, form_execution_plan, calculate_urgency,
    identify_opener_pieces, execute_responder_strategy,
    StrategicPlan, get_overcapture_constraints
)
from backend.engine.ai import find_all_valid_combos

def debug_bot4():
    """Debug Bot 4's plan formation"""
    
    # Create Bot 4's hand
    hand = [
        Piece("GENERAL_RED"),      # 14 points
        Piece("GENERAL_BLACK"),    # 13 points
        Piece("ADVISOR_RED"),      # 12 points
        Piece("ADVISOR_BLACK"),    # 11 points
        Piece("CHARIOT_RED"),     # 8 points
        Piece("CHARIOT_BLACK"),   # 7 points
        Piece("CANNON_BLACK"),    # 3 points
        Piece("SOLDIER_RED"),     # 2 points
    ]
    
    # Create context
    context = TurnPlayContext(
        my_name="Bot 4",
        my_hand=hand,
        my_captured=0,
        my_declared=4,
        required_piece_count=2,
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Alexanderium": {"captured": 0, "declared": 2},
            "Bot 2": {"captured": 0, "declared": 0},
            "Bot 3": {"captured": 0, "declared": 1},
            "Bot 4": {"captured": 0, "declared": 4}
        }
    )
    
    print("BOT 4 ANALYSIS:")
    print(f"Declared: 4 (needs 4 wins)")
    print(f"Required to play: 2 pieces")
    
    # Calculate urgency
    urgency = calculate_urgency(context)
    print(f"\nUrgency: {urgency}")
    print("  (critical = need wins every turn)")
    
    # Find valid combos
    valid_combos = find_all_valid_combos(hand)
    print(f"\nValid combos: {len(valid_combos)}")
    pairs = [(t, p) for t, p in valid_combos if t == "PAIR"]
    print(f"Pairs available: {len(pairs)}")
    
    # Get openers
    openers = identify_opener_pieces(hand)
    print(f"\nOpener pieces (≥11 points): {len(openers)}")
    for p in openers:
        print(f"  - {p.kind}: {p.point} points")
    
    # Form plan
    plan_dict = form_execution_plan(hand, context, valid_combos)
    print(f"\nPlan formation:")
    print(f"- Assigned openers: {len(plan_dict['assigned_openers'])}")
    for p in plan_dict['assigned_openers']:
        print(f"  - {p.kind}({p.point})")
    
    print(f"- Assigned combos: {len(plan_dict['assigned_combos'])}")
    for combo_type, pieces in plan_dict['assigned_combos']:
        piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
        print(f"  - {combo_type}: {piece_str}")
    
    print(f"- Burden pieces: {len(plan_dict['burden_pieces'])}")
    for p in plan_dict['burden_pieces']:
        print(f"  - {p.kind}({p.point})")
    
    # Trace responder strategy
    print("\nRESPONDER STRATEGY EXECUTION:")
    print("Bot 4 has critical urgency and needs 4 wins...")
    
    # Check what happens in execute_responder_strategy
    constraints = get_overcapture_constraints(context)
    plan = StrategicPlan(
        target_remaining=4,
        valid_combos=valid_combos,
        opener_pieces=openers,
        urgency_level=urgency,
        assigned_openers=plan_dict['assigned_openers'],
        assigned_combos=plan_dict['assigned_combos'],
        burden_pieces=plan_dict['burden_pieces'],
        reserve_pieces=plan_dict['reserve_pieces']
    )
    
    # The critical urgency section should trigger
    if plan.urgency_level == "critical" and plan.target_remaining > 0:
        print("\nCRITICAL URGENCY TRIGGERED!")
        print("Looking for valid 2-piece combinations...")
        
        # Find valid combos of size 2
        valid_of_size = [(t, p) for t, p in valid_combos if len(p) == 2]
        print(f"Found {len(valid_of_size)} valid 2-piece combos")
        
        if valid_of_size:
            # Get strongest
            best = max(valid_of_size, key=lambda x: sum(p.point for p in x[1]))
            piece_str = "+".join([f"{p.kind}({p.point})" for p in best[1]])
            print(f"Strongest 2-piece combo: {best[0]} - {piece_str} = {sum(p.point for p in best[1])} points")
        else:
            print("NO valid 2-piece combos found!")
            print("\nFalling back to burden disposal...")
            print("Burden pieces sorted by value (descending):")
            sorted_burden = sorted(plan_dict['burden_pieces'], key=lambda p: p.point, reverse=True)
            for i, p in enumerate(sorted_burden[:2]):
                print(f"  {i+1}. {p.kind}({p.point})")

if __name__ == "__main__":
    debug_bot4()