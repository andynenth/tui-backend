# tests/ai_turn_play/test_opponent_disruption_concept.py
"""
Test to understand and demonstrate the opponent disruption concept.

The key insight: If an opponent will reach their declared target THIS TURN
if they win, we should try to prevent them from winning to disrupt their
scoring (they would get declared + 5 bonus points).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.ai_turn_strategy import TurnPlayContext
from backend.engine.scoring import calculate_score


def test_disruption_concept():
    """Test the concept of opponent disruption."""
    print("\n=== Understanding Opponent Disruption ===\n")
    
    # Example scenario
    print("Scenario: Player 2 has declared 3 piles")
    print("- Last turn: Player 2 had 1/3 piles")
    print("- This turn: If Player 2 wins, they'll have 3/3 piles")
    print("- Score if they reach target: 3 + 5 = 8 points")
    print("- Score if disrupted (2/3): -1 point")
    print("- Disruption value: 9 points prevented!\n")
    
    # Test scoring
    target_met = calculate_score(declared=3, actual=3)
    target_missed = calculate_score(declared=3, actual=2)
    
    print(f"Score if target met (3/3): {target_met}")
    print(f"Score if disrupted (2/3): {target_missed}")
    print(f"Points prevented by disruption: {target_met - target_missed}\n")
    
    # Different scenarios
    print("Other disruption scenarios:")
    scenarios = [
        (2, 1, "Player declared 2, has 1, needs 1 more"),
        (4, 3, "Player declared 4, has 3, needs 1 more"),
        (1, 0, "Player declared 1, has 0, needs 1 more"),
        (0, 0, "Player declared 0, has 0, already at target (no disruption needed)"),
        (3, 3, "Player declared 3, has 3, already at target (disruption missed)"),
    ]
    
    for declared, current, desc in scenarios:
        if current < declared:
            # They need more piles
            piles_needed = declared - current
            if piles_needed <= 2:  # Could win this turn (1-2 piles)
                score_if_wins = calculate_score(declared, declared)
                score_if_disrupted = calculate_score(declared, current)
                value = score_if_wins - score_if_disrupted
                print(f"- {desc}")
                print(f"  If wins: {score_if_wins} pts, If disrupted: {score_if_disrupted} pts")
                print(f"  Disruption value: {value} points!\n")
            else:
                print(f"- {desc}")
                print(f"  Needs {piles_needed} piles - can't reach target this turn\n")
        elif current == declared:
            print(f"- {desc}")
            print(f"  Already at target - no disruption possible\n")


def test_disruption_detection():
    """Test detecting when disruption is possible."""
    print("\n=== Testing Disruption Detection ===\n")
    
    # Set up game state
    player_states = {
        "Bot1": {"captured": 0, "declared": 2},
        "Human1": {"captured": 2, "declared": 3},  # Needs 1 more!
        "Bot2": {"captured": 1, "declared": 1},    # Already at target
        "Human2": {"captured": 0, "declared": 4},  # Needs 4 - too many
    }
    
    # Current turn plays
    current_plays = [
        {
            'player': Player("Human1"),
            'pieces': [Piece("GENERAL_RED")],
            'play_type': 'SINGLE'
        }
    ]
    
    # Required piece count (must play singles)
    required_piece_count = 1
    
    print("Player states:")
    for name, state in player_states.items():
        captured = state['captured']
        declared = state['declared']
        print(f"- {name}: {captured}/{declared}", end="")
        
        # Check if disruption target
        if captured < declared:
            piles_needed = declared - captured
            if piles_needed <= required_piece_count:
                print(f" -> DISRUPTION TARGET! (needs {piles_needed})")
            else:
                print(f" (needs {piles_needed} - safe)")
        else:
            print(" (already at target)")
    
    print("\nCurrent turn status:")
    print(f"- Human1 is currently winning with {current_plays[0]['play_type']}")
    print(f"- If Human1 wins: 2+1=3/3 -> Score: 3+5 = 8 points")
    print(f"- If disrupted: 2/3 -> Score: -1 point")
    print(f"- Disruption value: 9 points!")
    
    print("\nDisruption strategy:")
    print("- ANY player should try to beat Human1's play")
    print("- Even with weak pieces, preventing 9 points is worth it")
    print("- This applies to both starters and responders")


def test_disruption_strategy():
    """Test how disruption affects play decisions."""
    print("\n=== Testing Disruption Strategy ===\n")
    
    # Bot's hand
    bot_hand = [
        Piece("ADVISOR_BLACK"),  # 11 points
        Piece("HORSE_RED"),      # 6 points
        Piece("CANNON_BLACK"),   # 3 points
    ]
    
    # Scenario 1: No disruption opportunity
    print("Scenario 1: No disruption opportunity")
    player_states = {
        "Bot1": {"captured": 1, "declared": 2},
        "Human1": {"captured": 0, "declared": 3},  # Needs 3 - can't get in 1 turn
        "Human2": {"captured": 2, "declared": 2},  # Already at target
    }
    
    print("- No opponents can reach target this turn")
    print("- Play normally based on own needs\n")
    
    # Scenario 2: Disruption opportunity exists
    print("Scenario 2: Disruption opportunity - Human1 needs 1 pile")
    player_states = {
        "Bot1": {"captured": 1, "declared": 2},
        "Human1": {"captured": 2, "declared": 3},  # Needs 1 more!
        "Human2": {"captured": 0, "declared": 2},
    }
    
    current_plays = [
        {
            'player': Player("Human1"),
            'pieces': [Piece("SOLDIER_BLACK")],  # Weak play
            'play_type': 'SINGLE'
        }
    ]
    
    print(f"- Human1 played weak {current_plays[0]['play_type']} (1 point)")
    print(f"- Bot can easily beat with CANNON (3 points)")
    print(f"- Disruption prevents Human1 from scoring 8 points")
    print(f"- Even though CANNON is weak, disruption is worth it!\n")
    
    # Decision logic
    print("Decision logic:")
    print("1. Check if any opponent is exactly N piles away from target")
    print("   where N = required_piece_count for this turn")
    print("2. If yes, check who's currently winning")
    print("3. If disruption target is winning, try to beat them")
    print("4. Use weakest pieces that can still win")


if __name__ == "__main__":
    print("Testing Opponent Disruption Concept...\n")
    
    test_disruption_concept()
    test_disruption_detection()
    test_disruption_strategy()
    
    print("\n✅ Disruption concept clarified!")