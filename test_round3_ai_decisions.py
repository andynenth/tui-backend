#!/usr/bin/env python3
"""Test to trace AI decisions in Round 3 - specifically why Bot 3 kept ADVISOR_REDs"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from backend.engine.piece import Piece
from backend.engine.ai import choose_strategic_play_safe
from backend.engine.ai_turn_strategy import (
    TurnPlayContext, choose_strategic_play, generate_strategic_plan,
    get_overcapture_constraints, StrategicPlan
)
from dataclasses import dataclass, field
from backend.engine.rules import get_play_type, is_valid_play

def load_round3_data():
    """Load Round 3 game data"""
    with open('game-data/room-66042B/round3/round3_extracted.json', 'r') as f:
        return json.load(f)

def create_piece(piece_data):
    """Create Piece object from JSON data"""
    # Piece takes a 'kind' string like "GENERAL_RED"
    return Piece(piece_data['type'])

def create_hand(hand_data):
    """Create list of Piece objects from hand data"""
    return [create_piece(p) for p in hand_data]

def trace_bot_decision(bot_name, hand_before, required_count, turn_number, 
                      my_captured, my_declared, am_i_starter=False):
    """Trace the decision-making process for a bot"""
    print(f"\n{'='*60}")
    print(f"TRACING {bot_name} - Turn {turn_number}")
    print(f"{'='*60}")
    
    # Create hand
    hand = create_hand(hand_before)
    print(f"\nHand ({len(hand)} pieces):")
    for p in sorted(hand, key=lambda x: x.point, reverse=True):
        print(f"  - {p.kind}: {p.point} points")
    
    # Create context
    context = TurnPlayContext(
        my_name=bot_name,
        my_hand=hand,
        my_captured=my_captured,
        my_declared=my_declared,
        required_piece_count=required_count,
        turn_number=turn_number,
        pieces_per_player=8 - turn_number + 1,  # Pieces remaining
        am_i_starter=am_i_starter,
        current_plays=[],  # Not implemented
        revealed_pieces=[],  # Not implemented
        player_states={
            "Alexanderium": {"captured": 0, "declared": 7},
            "Bot 2": {"captured": 0, "declared": 0},
            "Bot 3": {"captured": 0, "declared": 0},
            "Bot 4": {"captured": 0, "declared": 0}
        }
    )
    
    # Call the actual strategic play function
    print("\nCalling choose_strategic_play...")
    chosen_pieces = choose_strategic_play(hand, context)
    
    if chosen_pieces:
        chosen_str = "+".join([f"{p.kind}({p.point})" for p in chosen_pieces])
        print(f"\nChosen play: {chosen_str}")
        return chosen_pieces
    else:
        print("\nNo play chosen!")
        return None

def main():
    """Main test function"""
    print("Loading Round 3 data...")
    data = load_round3_data()
    round3 = data['round_3_data']
    
    # Analyze Turn 1
    print("\n" + "="*80)
    print("TURN 1 ANALYSIS")
    print("="*80)
    
    turn1 = round3['turn_history'][0]
    
    # Trace each bot's decision
    for play in turn1['plays']:
        if play['player'].startswith('Bot'):
            bot_name = play['player']
            hand_before = play['handBefore']
            actual_play = play['pieces']
            is_starter = play['isStarter']
            
            # Get declarations
            declarations = round3['declaration_phase']['declarations']
            bot_declaration = next(d for d in declarations if d['player'] == bot_name)
            declared = bot_declaration['declared']
            
            # Trace decision
            chosen = trace_bot_decision(
                bot_name=bot_name,
                hand_before=hand_before,
                required_count=4,  # Turn 1 required 4 pieces
                turn_number=1,
                my_captured=0,  # Start of round
                my_declared=declared,
                am_i_starter=is_starter
            )
            
            # Compare with actual play
            actual_str = "+".join([f"{p['type']}({p['point']})" for p in actual_play])
            print(f"\nACTUAL PLAY: {actual_str}")
            
            # Specifically check for ADVISOR_RED preservation
            if bot_name == "Bot 3":
                advisor_reds_in_hand = [p for p in hand_before if p['type'] == 'ADVISOR_RED']
                advisor_reds_played = [p for p in actual_play if p['type'] == 'ADVISOR_RED']
                print(f"\nBot 3 ADVISOR_RED analysis:")
                print(f"  - Had {len(advisor_reds_in_hand)} ADVISOR_REDs in hand")
                print(f"  - Played {len(advisor_reds_played)} ADVISOR_REDs")
                print(f"  - Kept {len(advisor_reds_in_hand) - len(advisor_reds_played)} ADVISOR_REDs")

if __name__ == "__main__":
    main()