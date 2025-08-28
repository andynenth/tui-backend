#!/usr/bin/env python3
"""Trace critical urgency logic for Bot 2"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, get_optimal_piece_count_for_starter,
    get_overcapture_constraints, calculate_urgency,
    StrategicPlan, COMBO_TYPE_RANK, is_play_risky_for_overcapture,
    get_field_strength_from_players
)
from backend.engine.ai import find_all_valid_combos

def trace_critical_urgency():
    """Trace the critical urgency section of get_optimal_piece_count_for_starter"""
    
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
    
    # Create context
    context = TurnPlayContext(
        my_name="Bot 2",
        my_hand=hand,
        my_captured=0,
        my_declared=5,
        required_piece_count=None,
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
    
    # Get valid combos
    valid_combos = find_all_valid_combos(hand)
    print("ALL VALID COMBOS:")
    for combo_type, pieces in valid_combos:
        piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
        combo_value = sum(p.point for p in pieces)
        print(f"  - {combo_type}: {piece_str} = {combo_value} points")
    
    # Create plan
    plan = StrategicPlan(
        target_remaining=5,
        valid_combos=valid_combos,
        opener_pieces=[p for p in hand if p.point >= 11],
        urgency_level="critical",
        assigned_combos=[(combo_type, pieces) for combo_type, pieces in valid_combos if combo_type == "THREE_OF_A_KIND"],
        assigned_openers=[p for p in hand if p.point >= 11]
    )
    
    constraints = get_overcapture_constraints(context)
    field_strength = get_field_strength_from_players(context.player_states)
    
    print("\n" + "="*80)
    print("SIMULATING CRITICAL URGENCY LOGIC")
    print("="*80)
    
    print(f"Urgency level: {plan.urgency_level}")
    print(f"Target remaining: {plan.target_remaining}")
    
    # Simulate the critical urgency section
    if plan.urgency_level == "critical" and plan.target_remaining > 0:
        print("\nIN CRITICAL URGENCY SECTION:")
        print("Finding strongest viable combo...")
        
        best_combo = None
        best_value = 0
        
        for combo_type, pieces in plan.valid_combos:
            pieces_in_hand = all(p in hand for p in pieces)
            print(f"\nChecking {combo_type}:")
            print(f"  All pieces in hand? {pieces_in_hand}")
            
            if pieces_in_hand:
                is_risky = is_play_risky_for_overcapture(pieces, constraints, field_strength)
                print(f"  Is risky for overcapture? {is_risky}")
                
                if not is_risky:
                    combo_value = sum(p.point for p in pieces)
                    print(f"  Combo value: {combo_value}")
                    
                    if combo_value > best_value:
                        print(f"  NEW BEST! (previous best: {best_value})")
                        best_value = combo_value
                        best_combo = pieces
                    else:
                        print(f"  Not better than current best ({best_value})")
        
        print(f"\nFINAL BEST COMBO:")
        if best_combo:
            play_str = "+".join([f"{p.kind}({p.point})" for p in best_combo])
            print(f"  {play_str} = {best_value} points")
            print(f"  Would return: ({len(best_combo)}, best_combo)")
        else:
            print("  No combo found!")

if __name__ == "__main__":
    trace_critical_urgency()