#!/usr/bin/env python3
"""
Test if opener detection is working correctly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import identify_opener_pieces, form_strategic_plan, form_execution_plan

def test_opener_detection():
    """Test basic opener detection"""
    print("Testing opener detection...")
    
    # Create hand with opener
    hand = [
        Piece("ADVISOR_RED"),  # 12 points - should be opener
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("CANNON_BLACK"),  # 3 points
        Piece("HORSE_BLACK"),  # 5 points
    ]
    
    print(f"\nHand: {[(p.name, p.point) for p in hand]}")
    
    # Test identify_opener_pieces
    openers = identify_opener_pieces(hand)
    print(f"Identified openers: {[(p.name, p.point) for p in openers]}")
    assert len(openers) == 1, f"Expected 1 opener, got {len(openers)}"
    assert openers[0].point == 12, f"Expected 12 point opener, got {openers[0].point}"
    
    # Test strategic plan
    from backend.engine.ai import find_all_valid_combos
    valid_combos = find_all_valid_combos(hand)
    print(f"Valid combos: {[(t, [(p.name, p.point) for p in pieces]) for t, pieces in valid_combos]}")
    
    plan = form_strategic_plan(
        hand=hand,
        valid_combos=valid_combos,
        opener_pieces=openers,
        target_remaining=2
    )
    
    print(f"\nStrategic plan:")
    print(f"  Urgency: {plan.urgency_level}")
    print(f"  Opener pieces: {[(p.name, p.point) for p in plan.opener_pieces]}")
    
    # Test execution plan
    from backend.engine.ai_turn_strategy import evaluate_hand
    hand_eval = {
        'openers': openers,
        'valid_combos': valid_combos,
        'burden_pieces': []
    }
    
    exec_plan = form_execution_plan(hand, hand_eval, target_remaining=2, turn_number=2)
    print(f"\nExecution plan:")
    print(f"  Assigned openers: {[(p.name, p.point) for p in exec_plan.assigned_openers]}")
    print(f"  Assigned combos: {[(t, [(p.name, p.point) for p in pieces]) for t, pieces in exec_plan.assigned_combos]}")
    print(f"  Main plan size: {exec_plan.main_plan_size}")
    
    # Check if it's opener-only
    opener_only = (
        len(exec_plan.assigned_openers) > 0 and
        len(exec_plan.assigned_combos) == 0 and
        exec_plan.main_plan_size == len(exec_plan.assigned_openers)
    )
    print(f"  Opener-only plan: {opener_only}")
    
    return opener_only

if __name__ == "__main__":
    if test_opener_detection():
        print("\n✅ Opener detection working correctly!")
    else:
        print("\n❌ Opener detection not working!")