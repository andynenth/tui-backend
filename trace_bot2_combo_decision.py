#!/usr/bin/env python3
"""Detailed trace of Bot 2's starter decision logic"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, choose_strategic_play, form_execution_plan,
    calculate_urgency, get_overcapture_constraints, detect_opener_only_plan,
    generate_strategic_plan, evaluate_hand, get_optimal_piece_count_for_starter,
    COMBO_TYPE_RANK
)
from backend.engine.ai import find_all_valid_combos

def detailed_trace():
    """Trace Bot 2's exact decision process"""
    
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
    
    print("="*80)
    print("STEP 1: GET OVERCAPTURE CONSTRAINTS")
    print("="*80)
    constraints = get_overcapture_constraints(context)
    print(f"Risk level: {constraints.risk_level}")
    print(f"Max safe pieces: {constraints.max_safe_pieces}")
    
    print("\n" + "="*80)
    print("STEP 2: GENERATE STRATEGIC PLAN")
    print("="*80)
    plan = generate_strategic_plan(hand, context)
    print(f"Target remaining: {plan.target_remaining}")
    print(f"Urgency level: {plan.urgency_level}")
    
    print("\n" + "="*80)
    print("STEP 3: EVALUATE HAND AND FORM EXECUTION PLAN")
    print("="*80)
    hand_eval = evaluate_hand(hand, context, plan)
    
    print(f"\nAssigned combos: {len(plan.assigned_combos)}")
    for combo_type, pieces in plan.assigned_combos:
        piece_str = "+".join([f"{p.kind}({p.point})" for p in pieces])
        print(f"  - {combo_type} (rank={COMBO_TYPE_RANK.get(combo_type, 0)}): {piece_str}")
    
    print(f"\nAssigned openers: {len(plan.assigned_openers)}")
    for p in plan.assigned_openers:
        print(f"  - {p.kind}: {p.point} points")
    
    print("\n" + "="*80)
    print("STEP 4: GET OPTIMAL PIECE COUNT FOR STARTER")
    print("="*80)
    
    # This is where the decision is made!
    piece_count, combo_to_play = get_optimal_piece_count_for_starter(
        plan, constraints, context, hand
    )
    
    print(f"\nOptimal piece count: {piece_count}")
    if combo_to_play:
        play_str = "+".join([f"{p.kind}({p.point})" for p in combo_to_play])
        print(f"Pre-selected combo: {play_str}")
    else:
        print("No pre-selected combo")
    
    print("\n" + "="*80)
    print("STEP 5: ACTUAL STRATEGIC PLAY DECISION")
    print("="*80)
    
    # Get the final decision
    chosen = choose_strategic_play(hand, context)
    if chosen:
        play_str = "+".join([f"{p.kind}({p.point})" for p in chosen])
        total = sum(p.point for p in chosen)
        print(f"FINAL CHOICE: {play_str} = {total} points")
        print(f"Number of pieces: {len(chosen)}")

if __name__ == "__main__":
    detailed_trace()