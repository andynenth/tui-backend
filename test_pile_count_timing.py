#!/usr/bin/env python3
"""
Test to investigate the timing of pile_count updates.

This simulates a game flow to see when pile_counts are updated
relative to when bots make decisions.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece


class MockGameState:
    """Mock game state to simulate pile_count updates"""
    def __init__(self):
        self.pile_counts = {
            "Bot 1": 0,
            "Bot 2": 0,
            "Bot 3": 0,
            "Bot 4": 0
        }
        self.turn_number = 1
        self.players = [
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True)
        ]
        
        # Set declarations
        self.players[0].declared = 2
        self.players[1].declared = 0
        self.players[2].declared = 1  # Bot 3 declares 1
        self.players[3].declared = 2
        
    def simulate_turn_win(self, winner_name: str, piles_won: int):
        """Simulate a player winning a turn and getting piles"""
        print(f"\n📍 TURN {self.turn_number} COMPLETED")
        print(f"   Winner: {winner_name}, Piles won: {piles_won}")
        print(f"   pile_counts BEFORE update: {self.pile_counts}")
        
        # Update pile counts (simulating _award_piles)
        self.pile_counts[winner_name] += piles_won
        
        print(f"   pile_counts AFTER update: {self.pile_counts}")
        
        # Increment turn number
        self.turn_number += 1
        
    def bot_makes_decision(self, bot_name: str):
        """Simulate bot making a decision - checking pile_counts"""
        bot_captured = self.pile_counts.get(bot_name, 0)
        bot = next((p for p in self.players if p.name == bot_name), None)
        bot_declared = bot.declared if bot else 0
        
        print(f"\n🤖 {bot_name} MAKING DECISION (Turn {self.turn_number})")
        print(f"   pile_counts when deciding: {self.pile_counts}")
        print(f"   {bot_name}: captured={bot_captured}, declared={bot_declared}")
        
        if bot_captured == bot_declared:
            print(f"   ⚠️ AT TARGET - Should play weak pieces!")
        elif bot_captured > bot_declared:
            print(f"   🚨 OVERCAPTURED by {bot_captured - bot_declared} - Should still play weak!")
        else:
            print(f"   ✅ Below target - Can play normally")
            
        return bot_captured, bot_declared


def test_timing_scenario():
    """Test the exact timing scenario from Bot 3's Round 1"""
    print("\n" + "="*60)
    print("TIMING SCENARIO: Bot 3 Round 1")
    print("="*60)
    
    game_state = MockGameState()
    
    print("\nINITIAL STATE:")
    print(f"Bot 3: declared=1, captured=0")
    
    # Turn 1
    print("\n--- TURN 1 ---")
    game_state.bot_makes_decision("Bot 3")
    # Bot 3 doesn't win
    game_state.simulate_turn_win("Bot 4", 1)
    
    # Turn 2
    print("\n--- TURN 2 ---")
    game_state.bot_makes_decision("Bot 3")
    print("   Bot 3 plays and wins this turn...")
    game_state.simulate_turn_win("Bot 3", 1)
    
    # Turn 3 - THE CRITICAL MOMENT
    print("\n--- TURN 3 (CRITICAL) ---")
    captured, declared = game_state.bot_makes_decision("Bot 3")
    
    if captured == declared:
        print("\n✅ CORRECT: Bot 3 sees it is at target and should avoid winning!")
    else:
        print("\n❌ BUG: Bot 3 doesn't see updated pile_counts!")
        print("   This would cause overcapture!")
    
    # Simulate what happens if bot wins anyway
    print("\n   What if Bot 3 wins anyway?")
    game_state.simulate_turn_win("Bot 3", 1)
    
    # Turn 4
    print("\n--- TURN 4 ---")
    game_state.bot_makes_decision("Bot 3")
    print("   Now Bot 3 is definitely overcaptured!")


def test_update_sequence():
    """Test the exact sequence of updates in the state machine"""
    print("\n" + "="*60)
    print("UPDATE SEQUENCE ANALYSIS")
    print("="*60)
    
    print("\nTypical turn completion sequence:")
    print("1. All players have played")
    print("2. determine_turn_winner() called")
    print("3. _award_piles() updates game.pile_counts")
    print("4. update_phase_data() broadcasts updated state")
    print("5. _broadcast_turn_completion() sends turn_complete event")
    print("6. Next turn starts")
    print("7. Bots make decisions - do they see updated pile_counts?")
    
    print("\nKey Question: When bots make decisions for the next turn,")
    print("are they seeing the pile_counts BEFORE or AFTER the previous turn's award?")


if __name__ == "__main__":
    test_timing_scenario()
    test_update_sequence()
    
    print("\n" + "="*60)
    print("INVESTIGATION COMPLETE")
    print("="*60)
    print("\nThe tests show the flow of pile_count updates.")
    print("The key issue is whether bots see updated pile_counts")
    print("when making decisions for the next turn.")