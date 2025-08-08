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

def test_round_scenario(round_name: str, players_data: list, iterations: int = 10):
    """Test a specific round scenario multiple times"""
    print(f"\n{'='*80}")
    print(f"TESTING {round_name}")
    print(f"{'='*80}")
    
    # Track results
    opener_play_counts = {p[0]: 0 for p in players_data}
    total_starter_turns = {p[0]: 0 for p in players_data}
    
    for iteration in range(iterations):
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
                if len(starter.hand) < 1:
                    continue
                    
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
                
                print(f"\nTurn {turn_num} - {starter.name} as STARTER")
                print(f"  Hand: {[f'{p.name}({p.point})' for p in starter.hand]}")
                
                # Get strategic play
                result = choose_strategic_play(starter.hand, context)
                
                # Track if opener was played
                if result and len(result) == 1 and result[0].point >= 11:
                    opener_play_counts[starter.name] += 1
                    print(f"  🎯 OPENER PLAYED: {result[0].name}")
                
                total_starter_turns[starter.name] += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY for {round_name} ({iterations} iterations)")
    print(f"{'='*60}")
    
    for name in opener_play_counts:
        if total_starter_turns[name] > 0:
            percentage = (opener_play_counts[name] / total_starter_turns[name]) * 100
            print(f"{name}: {opener_play_counts[name]}/{total_starter_turns[name]} opener plays ({percentage:.1f}%)")

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
    
    # Run tests
    test_round_scenario("Round 2", round_2_data, iterations=20)
    test_round_scenario("Round 5", round_5_data, iterations=20)
    test_round_scenario("Round 8", round_8_data, iterations=20)
    
    print("\n" + "="*80)
    print("EXPECTED RESULTS (if random timing working):")
    print("- Early game (6+ pieces): ~35% opener plays")
    print("- Mid game (4-5 pieces): ~40% opener plays")
    print("- Late game (<4 pieces): ~50% opener plays")
    print("="*80)

if __name__ == "__main__":
    main()