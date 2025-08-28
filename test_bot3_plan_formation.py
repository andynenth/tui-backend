#!/usr/bin/env python3
"""Test Bot 3's plan formation to see combo assignment"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import TurnPlayContext, form_execution_plan
from backend.engine.ai import find_all_valid_combos

def main():
    # Bot 3's hand
    hand = [
        Piece("ADVISOR_RED"),     # 12 points
        Piece("ADVISOR_RED"),     # 12 points
        Piece("ADVISOR_BLACK"),   # 11 points
        Piece("CHARIOT_RED"),     # 8 points
        Piece("CHARIOT_BLACK"),   # 7 points
        Piece("SOLDIER_RED"),     # 2 points
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK"),   # 1 point
    ]
    
    context = TurnPlayContext(
        my_name="Bot 3",
        my_hand=hand,
        my_captured=0,
        my_declared=0,
        required_piece_count=4,
        turn_number=1,
        pieces_per_player=8,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={
            "Alexanderium": {"captured": 0, "declared": 7},
            "Bot 2": {"captured": 0, "declared": 0},
            "Bot 3": {"captured": 0, "declared": 0},
            "Bot 4": {"captured": 0, "declared": 0}
        }
    )
    
    # Find valid combos
    valid_combos = find_all_valid_combos(hand)
    
    # Form execution plan
    plan = form_execution_plan(hand, context, valid_combos)
    
    print("Plan Formation Results:")
    print(f"- Assigned openers: {len(plan['assigned_openers'])}")
    print(f"- Assigned combos: {len(plan['assigned_combos'])}")
    
    if plan['assigned_combos']:
        print("\nAssigned combos:")
        for combo_type, pieces in plan['assigned_combos']:
            piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
            print(f"  - {combo_type}: {piece_str}")
    
    print(f"\nBurden pieces ({len(plan['burden_pieces'])}):")
    for p in plan['burden_pieces']:
        print(f"  - {p.kind}: {p.point}")
    
    print(f"\nReserve pieces ({len(plan['reserve_pieces'])}):")
    for p in plan['reserve_pieces']:
        print(f"  - {p.kind}: {p.point}")
    
    # Check which category ADVISOR_REDs are in
    advisor_reds = [p for p in hand if p.kind == "ADVISOR_RED"]
    print("\nADVISOR_RED categorization:")
    for ar in advisor_reds:
        in_combos = any(ar in pieces for _, pieces in plan['assigned_combos'])
        in_burden = ar in plan['burden_pieces']
        in_reserve = ar in plan['reserve_pieces']
        print(f"  - {ar.kind}: in_combos={in_combos}, in_burden={in_burden}, in_reserve={in_reserve}")

if __name__ == "__main__":
    main()