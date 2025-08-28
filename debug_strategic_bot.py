#!/usr/bin/env python3
"""Debug why Strategic Bot doesn't preserve ADVISOR_RED pair"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, form_execution_plan, calculate_urgency
)
from backend.engine.ai import find_all_valid_combos

def debug_strategic_bot():
    """Debug Strategic Bot's decision"""
    
    # Same hand as Bot 3 but declaring 2
    hand = [
        Piece("ADVISOR_RED"),    # 12
        Piece("ADVISOR_RED"),    # 12
        Piece("ADVISOR_BLACK"),  # 11
        Piece("CHARIOT_RED"),    # 8
        Piece("CHARIOT_BLACK"),  # 7
        Piece("SOLDIER_RED"),    # 2
        Piece("SOLDIER_BLACK"),  # 1
        Piece("SOLDIER_BLACK"),  # 1
    ]
    
    # Create context - Strategic Bot declares 2
    context = TurnPlayContext(
        my_name="Strategic Bot",
        my_hand=hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=4,
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 1": {"captured": 0, "declared": 5},
            "Strategic Bot": {"captured": 0, "declared": 2},
            "Bot 3": {"captured": 0, "declared": 0},
            "Bot 4": {"captured": 0, "declared": 0}
        }
    )
    
    print("STRATEGIC BOT SITUATION:")
    print(f"- Declared: 2 (needs 2 wins)")
    print(f"- Must play: 4 pieces as responder")
    print(f"- Hand has ADVISOR_RED pair")
    
    # Calculate urgency
    urgency = calculate_urgency(context)
    print(f"\nUrgency: {urgency}")
    
    # Get valid combos
    valid_combos = find_all_valid_combos(hand)
    print(f"\nValid combos: {len(valid_combos)}")
    for combo_type, pieces in valid_combos:
        if combo_type in ["PAIR", "THREE_OF_A_KIND"]:
            piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
            print(f"  - {combo_type}: {piece_str}")
    
    # Form plan
    plan_dict = form_execution_plan(hand, context, valid_combos)
    print(f"\nPlan formation (target_remaining={2}):")
    print(f"- Assigned combos: {len(plan_dict['assigned_combos'])}")
    for combo_type, pieces in plan_dict['assigned_combos']:
        piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
        print(f"  - {combo_type}: {piece_str}")
    
    print(f"- Assigned openers: {len(plan_dict['assigned_openers'])}")
    for p in plan_dict['assigned_openers']:
        print(f"  - {p.kind}({p.point})")
    
    print(f"- Burden pieces: {len(plan_dict['burden_pieces'])}")
    if plan_dict['burden_pieces']:
        burden_names = [f"{p.kind}({p.point})" for p in plan_dict['burden_pieces']]
        print(f"  {', '.join(burden_names)}")

if __name__ == "__main__":
    debug_strategic_bot()