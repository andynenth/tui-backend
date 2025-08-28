#!/usr/bin/env python3
"""Trace exact logic flow for Bot 3's decision"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import TurnPlayContext, get_overcapture_constraints

def simulate_responder_logic():
    # Bot 3's exact situation
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
        player_states={}
    )
    
    constraints = get_overcapture_constraints(context)
    required = context.required_piece_count
    
    print(f"Risk level: {constraints.risk_level}")
    print(f"Required pieces: {required}")
    print(f"Avoid piece counts: {constraints.avoid_piece_counts}")
    
    # Check if special handling applies
    special_handling = (
        constraints.risk_level in ["medium", "high"] and 
        required in constraints.avoid_piece_counts
    )
    print(f"\nSpecial handling applies: {special_handling}")
    print(f"  - Risk level in ['medium', 'high']: {constraints.risk_level in ['medium', 'high']}")
    print(f"  - Required ({required}) in avoid_piece_counts: {required in constraints.avoid_piece_counts}")
    
    # Since Bot 3 declared 0, all pieces are burden pieces
    burden_pieces = sorted(hand, key=lambda p: p.point, reverse=True)
    print(f"\nBurden pieces (sorted by value desc):")
    for i, p in enumerate(burden_pieces):
        print(f"  {i+1}. {p.kind}: {p.point} points")
    
    print(f"\nNormal disposal strategy would play pieces 1-{required}:")
    normal_play = burden_pieces[:required]
    for p in normal_play:
        print(f"  - {p.kind}: {p.point}")
    
    # Check if there's special different-name logic
    if not special_handling:
        print("\nNo special handling - using normal disposal order")
        print("This should play the 4 highest burden pieces")

if __name__ == "__main__":
    simulate_responder_logic()