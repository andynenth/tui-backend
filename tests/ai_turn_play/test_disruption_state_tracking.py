# tests/ai_turn_play/test_disruption_state_tracking.py
"""
Test the correct approach for opponent disruption based on state changes.

Key: We need to detect when an opponent WOULD transition from
captured < declared to captured = declared if they win this turn.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import TurnPlayContext


def test_disruption_detection_logic():
    """Test the logic for detecting disruption opportunities."""
    print("\n=== Testing Disruption Detection Logic ===\n")
    
    # Current game state (BEFORE this turn's resolution)
    player_states = {
        "Bot1": {"captured": 1, "declared": 2},    # 1/2 - needs 1 more
        "Human1": {"captured": 2, "declared": 3},   # 2/3 - needs 1 more
        "Bot2": {"captured": 0, "declared": 2},     # 0/2 - needs 2 more
        "Human2": {"captured": 3, "declared": 3},   # 3/3 - already at target
    }
    
    # This turn is playing for 1 pile
    required_piece_count = 1
    piles_at_stake = 1
    
    print("Current state (BEFORE this turn resolves):")
    for name, state in player_states.items():
        captured = state['captured']
        declared = state['declared']
        print(f"- {name}: {captured}/{declared}", end="")
        
        # Check disruption condition
        if captured < declared:  # Not at target yet
            if captured + piles_at_stake == declared:  # Would reach target
                print(" → DISRUPTION TARGET! (would reach target)")
            else:
                print(f" (would be {captured + piles_at_stake}/{declared})")
        else:
            print(" (already at target)")
    
    print("\nDisruption targets this turn:")
    print("- Bot1: 1 + 1 = 2 (reaches 2/2) ✓")
    print("- Human1: 2 + 1 = 3 (reaches 3/3) ✓")
    print("- Bot2: 0 + 1 = 1 (only 1/2) ✗")
    print("- Human2: already at 3/3 ✗")


def test_disruption_with_different_pile_counts():
    """Test disruption detection with different pile counts."""
    print("\n=== Testing Different Pile Counts ===\n")
    
    # Playing for 2 piles this turn
    player_states = {
        "P1": {"captured": 1, "declared": 3},    # 1/3 - needs 2
        "P2": {"captured": 0, "declared": 2},    # 0/2 - needs 2
        "P3": {"captured": 2, "declared": 4},    # 2/4 - needs 2
        "P4": {"captured": 1, "declared": 2},    # 1/2 - needs 1
    }
    
    piles_at_stake = 2  # Playing pairs
    
    print(f"This turn playing for {piles_at_stake} piles\n")
    
    disruption_targets = []
    for name, state in player_states.items():
        captured = state['captured']
        declared = state['declared']
        
        # Check if they would reach target
        would_have = captured + piles_at_stake
        reaches_target = (captured < declared and would_have == declared)
        
        print(f"{name}: {captured}/{declared} + {piles_at_stake} = {would_have}/{declared}", end="")
        if reaches_target:
            print(" → DISRUPTION TARGET!")
            disruption_targets.append(name)
        else:
            print()
    
    print(f"\nDisruption targets: {disruption_targets}")


def test_disruption_strategy_decision():
    """Test how to decide whether to disrupt."""
    print("\n=== Testing Disruption Strategy Decision ===\n")
    
    # Game state
    player_states = {
        "Bot1": {"captured": 1, "declared": 2},    # Me
        "Human1": {"captured": 2, "declared": 3},   # Disruption target
        "Bot2": {"captured": 0, "declared": 1},     # Disruption target
        "Human2": {"captured": 1, "declared": 4},   # Not a target
    }
    
    # Current plays (who's winning so far)
    current_plays = [
        {
            'player': Player("Human1"),
            'pieces': [Piece("CANNON_RED")],  # 4 points
            'play_type': 'SINGLE'
        },
        {
            'player': Player("Bot2"),
            'pieces': [Piece("SOLDIER_BLACK")],  # 1 point
            'play_type': 'SINGLE'
        }
    ]
    
    piles_at_stake = 1
    
    print("Disruption analysis:")
    print("1. Identify disruption targets:")
    print("   - Human1: 2/3 → 3/3 (target!)")
    print("   - Bot2: 0/1 → 1/1 (target!)")
    
    print("\n2. Check who's currently winning:")
    print("   - Human1: CANNON (4 pts) - WINNING")
    print("   - Bot2: SOLDIER (1 pt)")
    
    print("\n3. Decision:")
    print("   - Human1 is both a disruption target AND currently winning")
    print("   - Bot1 should try to beat Human1's 4-point play")
    print("   - This prevents Human1 from scoring 3+5=8 points")
    print("   - Even with weak pieces, disruption is worth it!")
    
    print("\n4. If Bot2 was winning instead:")
    print("   - Bot2 is also a disruption target")
    print("   - But Bot2's bonus (1+5=6) is less than Human1's (3+5=8)")
    print("   - Still worth disrupting to prevent 6 points")


def test_implementation_approach():
    """Test the implementation approach."""
    print("\n=== Implementation Approach ===\n")
    
    print("Data needed in TurnPlayContext:")
    print("1. player_states with captured/declared (✓ already have)")
    print("2. required_piece_count or piles at stake (✓ already have)")
    print("3. current_plays to see who's winning (✓ already have)")
    
    print("\nAlgorithm:")
    print("1. For each opponent in player_states:")
    print("   - Check if captured < declared")
    print("   - Check if captured + required_piece_count == declared")
    print("   - If yes, mark as disruption target")
    print("2. Check current_plays to find current winner")
    print("3. If current winner is a disruption target:")
    print("   - Try to find pieces that can beat them")
    print("   - Use weakest pieces that still win")
    print("4. Return disruption play or None")
    
    print("\nIntegration:")
    print("- Add check_opponent_disruption() function")
    print("- Call it early in choose_strategic_play()")
    print("- If returns pieces, use them (high priority)")
    print("- Otherwise continue normal strategy")


if __name__ == "__main__":
    print("Testing Disruption State Tracking...\n")
    
    test_disruption_detection_logic()
    test_disruption_with_different_pile_counts()
    test_disruption_strategy_decision()
    test_implementation_approach()
    
    print("\n✅ Disruption logic clarified!")