#!/usr/bin/env python3
"""
Test script to debug single opener random timing feature
Uses initial hands from game_play_history_rounds_1_8.md
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.piece import Piece
from backend.engine.player import Player
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play
import random

# Seed for reproducibility in debugging
random.seed(42)

def create_player_from_hand_string(name: str, hand_str: str, declared: int) -> Player:
    """Create a player with pieces from hand string"""
    # Parse hand string like "[SOLDIER_BLACK(1), CANNON_BLACK(3), ...]"
    pieces = []
    piece_names = hand_str.strip("[]").split(", ")
    for piece_str in piece_names:
        # Extract piece name (remove point value)
        piece_name = piece_str.split("(")[0]
        pieces.append(Piece(piece_name))
    
    player = Player(name, is_bot=True)
    player.hand = pieces
    player.declared = declared
    return player

def test_round_scenario(round_name: str, players_data: list, iterations: int = 100):
    """Test a specific round scenario multiple times with enhanced tracking"""
    print(f"\n{'='*80}")
    print(f"TESTING {round_name}")
    print(f"{'='*80}")
    
    # Enhanced tracking - separate starter and responder
    starter_opener_plays = {p[0]: 0 for p in players_data}
    starter_opportunities = {p[0]: 0 for p in players_data}
    responder_opener_plays = {p[0]: 0 for p in players_data}
    responder_opportunities = {p[0]: 0 for p in players_data}
    starter_forced_singles = {p[0]: 0 for p in players_data}  # Track when starter forces singles
    
    for iteration in range(iterations):
        if iteration % 20 == 0:  # Less verbose output
            print(f"\n--- Iteration {iteration + 1} ---")
        
        # Create players
        players = []
        for name, hand_str, declared in players_data:
            player = create_player_from_hand_string(name, hand_str, declared)
            players.append(player)
            
        # Simulate turns where each bot gets to be starter
        for turn_num in range(1, 4):  # Test first 3 turns
            for starter_idx, starter in enumerate(players):
                # Skip if bot has no pieces
                if len(starter.hand) < 2:
                    continue
                    
                # Check if starter has opener-only plan
                from backend.engine.ai_turn_strategy import form_execution_plan, evaluate_hand
                hand_eval = evaluate_hand(starter.hand)
                plan = form_execution_plan(starter.hand, hand_eval, starter.declared - 0, turn_num)
                
                has_opener_only = (
                    len(plan.assigned_openers) > 0 and
                    len(plan.assigned_combos) == 0 and
                    plan.main_plan_size == len(plan.assigned_openers)
                )
                
                # Create context for starter
                context = TurnPlayContext(
                    my_name=starter.name,
                    my_hand=starter.hand,
                    my_captured=0,  # Start of round
                    my_declared=starter.declared,
                    required_piece_count=None,  # Starter chooses
                    turn_number=turn_num,
                    pieces_per_player=8 - turn_num + 1,
                    am_i_starter=True,
                    current_plays=[],
                    revealed_pieces=[],
                    player_states={p.name: {"captured": 0, "declared": p.declared} for p in players}
                )
                
                # Get strategic play for starter
                result = choose_strategic_play(starter.hand, context)
                
                # Track starter behavior
                if has_opener_only:
                    starter_opportunities[starter.name] += 1
                    if result and len(result) == 1:
                        starter_forced_singles[starter.name] += 1
                        if result[0].point >= 11:
                            starter_opener_plays[starter.name] += 1
                
                # Now simulate responders if starter played singles
                if result and len(result) == 1:
                    # Test each other player as responder
                    for responder in players:
                        if responder.name == starter.name or len(responder.hand) < 1:
                            continue
                        
                        # Check if responder has opener-only plan
                        resp_eval = evaluate_hand(responder.hand)
                        resp_plan = form_execution_plan(responder.hand, resp_eval, responder.declared - 0, turn_num)
                        
                        resp_has_opener_only = (
                            len(resp_plan.assigned_openers) > 0 and
                            len(resp_plan.assigned_combos) == 0 and
                            resp_plan.main_plan_size == len(resp_plan.assigned_openers)
                        )
                        
                        if resp_has_opener_only:
                            responder_opportunities[responder.name] += 1
                            
                            # Create responder context
                            resp_context = TurnPlayContext(
                                my_name=responder.name,
                                my_hand=responder.hand,
                                my_captured=0,
                                my_declared=responder.declared,
                                required_piece_count=1,  # Singles required
                                turn_number=turn_num,
                                pieces_per_player=8 - turn_num + 1,
                                am_i_starter=False,
                                current_plays=[{"player": starter.name, "pieces": result}],
                                revealed_pieces=result,
                                player_states={p.name: {"captured": 0, "declared": p.declared} for p in players}
                            )
                            
                            # Get responder play
                            resp_result = choose_strategic_play(responder.hand, resp_context)
                            
                            if resp_result and len(resp_result) == 1 and resp_result[0].point >= 11:
                                responder_opener_plays[responder.name] += 1
    
    # Print enhanced summary
    print(f"\n{'='*60}")
    print(f"SUMMARY for {round_name} ({iterations} iterations)")
    print(f"{'='*60}")
    
    print("\nSTARTER OPENER TIMING:")
    for name in starter_opener_plays:
        if starter_opportunities[name] > 0:
            singles_rate = (starter_forced_singles[name] / starter_opportunities[name]) * 100
            opener_rate = (starter_opener_plays[name] / starter_opportunities[name]) * 100
            print(f"  {name}: {starter_forced_singles[name]}/{starter_opportunities[name]} forced singles ({singles_rate:.1f}%)")
            print(f"        {starter_opener_plays[name]}/{starter_opportunities[name]} opener plays ({opener_rate:.1f}%)")
            
            # Verify randomness (should be 35-50% depending on hand size)
            if starter_opportunities[name] > 20:  # Need enough samples
                assert 25 <= singles_rate <= 60, f"Starter singles rate {singles_rate:.1f}% outside expected 35-50% range"
    
    print("\nRESPONDER OPENER TIMING:")
    for name in responder_opener_plays:
        if responder_opportunities[name] > 0:
            rate = (responder_opener_plays[name] / responder_opportunities[name]) * 100
            print(f"  {name}: {responder_opener_plays[name]}/{responder_opportunities[name]} opener plays ({rate:.1f}%)")
            
            # Verify randomness
            if responder_opportunities[name] > 20:
                assert 25 <= rate <= 60, f"Responder rate {rate:.1f}% outside expected 35-50% range"

def main():
    """Test multiple scenarios from game history"""
    
    # Round 2 data - good test case with multiple openers
    round_2_data = [
        ("Bot 2", "[SOLDIER_BLACK(1), SOLDIER_BLACK(1), SOLDIER_BLACK(1), HORSE_BLACK(5), SOLDIER_RED(2), CANNON_RED(4), HORSE_RED(6), ELEPHANT_RED(10)]", 0),
        ("Bot 3", "[SOLDIER_BLACK(1), HORSE_BLACK(5), ELEPHANT_BLACK(9), SOLDIER_RED(2), SOLDIER_RED(2), CHARIOT_RED(8), ELEPHANT_RED(10), ADVISOR_RED(12)]", 1),
        ("Bot 4", "[CHARIOT_BLACK(7), ELEPHANT_BLACK(9), ADVISOR_BLACK(11), SOLDIER_RED(2), SOLDIER_RED(2), CANNON_RED(4), HORSE_RED(6), ADVISOR_RED(12)]", 2),
    ]
    
    # Round 5 data - Bot 2 has strong openers
    round_5_data = [
        ("Bot 2", "[SOLDIER_BLACK(1), CHARIOT_BLACK(7), ADVISOR_BLACK(11), SOLDIER_RED(2), SOLDIER_RED(2), SOLDIER_RED(2), ELEPHANT_RED(10), GENERAL_RED(14)]", 5),
        ("Bot 3", "[SOLDIER_BLACK(1), ELEPHANT_BLACK(9), SOLDIER_RED(2), CANNON_RED(4), HORSE_RED(6), CHARIOT_RED(8), CHARIOT_RED(8), ELEPHANT_RED(10)]", 0),
        ("Bot 4", "[SOLDIER_BLACK(1), CANNON_BLACK(3), HORSE_BLACK(5), ADVISOR_BLACK(11), SOLDIER_RED(2), CANNON_RED(4), HORSE_RED(6), ADVISOR_RED(12)]", 2),
    ]
    
    # Round 8 data
    round_8_data = [
        ("Bot 2", "[SOLDIER_BLACK(1), SOLDIER_BLACK(1), CANNON_BLACK(3), HORSE_BLACK(5), ELEPHANT_BLACK(9), SOLDIER_RED(2), HORSE_RED(6), GENERAL_RED(14)]", 1),
        ("Bot 3", "[CHARIOT_BLACK(7), ELEPHANT_BLACK(9), SOLDIER_RED(2), SOLDIER_RED(2), CANNON_RED(4), CANNON_RED(4), ELEPHANT_RED(10), ELEPHANT_RED(10)]", 0),
        ("Bot 4", "[SOLDIER_BLACK(1), SOLDIER_BLACK(1), ADVISOR_BLACK(11), SOLDIER_RED(2), HORSE_RED(6), CHARIOT_RED(8), ADVISOR_RED(12), ADVISOR_RED(12)]", 3),
    ]
    
    # Run tests with more iterations for statistical validity
    test_round_scenario("Round 2", round_2_data, iterations=100)
    test_round_scenario("Round 5", round_5_data, iterations=100)
    test_round_scenario("Round 8", round_8_data, iterations=100)
    
    print("\n" + "="*80)
    print("EXPECTED RESULTS (if random timing working):")
    print("- Early game (6+ pieces): ~35% opener plays")
    print("- Mid game (4-5 pieces): ~40% opener plays")
    print("- Late game (<4 pieces): ~50% opener plays")
    print("="*80)

if __name__ == "__main__":
    main()