#!/usr/bin/env python3
"""Debug why Bot 3 plays ADVISOR_RED when declaring 0"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, choose_strategic_play, form_execution_plan,
    calculate_urgency, get_overcapture_constraints
)
from backend.engine.ai import find_all_valid_combos

def debug_bot3():
    """Debug Bot 3's decision"""
    
    # Create Bot 3's hand
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
    
    # Create context - Bot 3 is responder
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=hand,
        my_captured=0,
        my_declared=0,
        required_piece_count=4,  # Responder, must play 4
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Bot 2": {"captured": 0, "declared": 5},
            "Bot 3": {"captured": 0, "declared": 0},
            "Bot 4": {"captured": 0, "declared": 0},
            "Player 4": {"captured": 0, "declared": 4}
        }
    )
    
    print("BOT 3 SITUATION:")
    print(f"- Declared: 0 (wants to avoid winning)")
    print(f"- Must play: 4 pieces as responder")
    print(f"- Hand has ADVISOR_RED pair")
    
    # Get plan
    valid_combos = find_all_valid_combos(hand)
    print(f"\nValid combos: {len(valid_combos)}")
    for combo_type, pieces in valid_combos:
        if combo_type == "PAIR":
            piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
            print(f"  - {combo_type}: {piece_str}")
    
    # Form plan
    plan_dict = form_execution_plan(hand, context, valid_combos)
    print(f"\nPlan formation (target_remaining={0}):")
    print(f"- Assigned combos: {len(plan_dict['assigned_combos'])}")
    for combo_type, pieces in plan_dict['assigned_combos']:
        piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
        print(f"  - {combo_type}: {piece_str}")
    
    print(f"- Burden pieces: {len(plan_dict['burden_pieces'])}")
    burden_names = [f"{p.kind}({p.point})" for p in plan_dict['burden_pieces']]
    print(f"  {', '.join(burden_names)}")
    
    # Get actual choice
    chosen = choose_strategic_play(hand, context)
    print(f"\nCHOSEN PLAY:")
    play_str = "+".join([f"{p.kind}({p.point})" for p in chosen])
    print(f"  {play_str} = {sum(p.point for p in chosen)} points")
    
    # Check if ADVISOR_RED in chosen
    if any(p.kind == "ADVISOR_RED" for p in chosen):
        print("\n❌ ERROR: Bot 3 played ADVISOR_RED when declaring 0!")
    else:
        print("\n✅ OK: Bot 3 did not play ADVISOR_RED")

if __name__ == "__main__":
    debug_bot3()