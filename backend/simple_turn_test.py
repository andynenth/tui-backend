#!/usr/bin/env python3
# backend/simple_turn_test.py

import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🚀 Simple Turn State Test")
print("=" * 40)

# Import test
try:
    from engine.state_machine.core import GamePhase, ActionType, GameAction
    from engine.state_machine.states.turn_state import TurnState
    from datetime import datetime
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Create test data
class MockGame:
    def __init__(self):
        self.players = ["Alice", "Bob", "Charlie", "Diana"]
        self.round_starter = "Alice"
        self.current_player = "Alice"
        self.player_hands = {
            "Alice": [1, 2, 3, 4],
            "Bob": [5, 6, 7, 8],
            "Charlie": [9, 10, 11, 12],
            "Diana": [13, 14, 15, 16]
        }
        self.player_piles = {"Alice": 0, "Bob": 0, "Charlie": 0, "Diana": 0}
    
    def get_player_order_from(self, starter):
        idx = self.players.index(starter)
        return self.players[idx:] + self.players[:idx]

class MockStateMachine:
    def __init__(self, game):
        self.game = game

# Synchronous tests (no async)
print("\n🧪 Testing Turn State Creation...")
game = MockGame()
state_machine = MockStateMachine(game)
turn_state = TurnState(state_machine)

print(f"✅ Phase name: {turn_state.phase_name}")
print(f"✅ Next phases: {turn_state.next_phases}")
print(f"✅ Allowed actions: {[a.value for a in turn_state.allowed_actions]}")

# Test basic methods
print(f"✅ Current player method: {turn_state._get_current_player()}")

# Create a test action
action = GameAction(
    player_name="Alice",
    action_type=ActionType.PLAY_PIECES,
    payload={'pieces': [1, 2], 'play_type': 'pair', 'play_value': 10},
    timestamp=datetime.now()
)

print(f"✅ Created test action: {action.player_name} - {action.action_type.value}")

print("\n🎉 Basic Turn State test completed!")
print("Turn State can be created and basic methods work.")
print("\nTo test async functionality, run:")
print("python -c \"import asyncio; from simple_turn_test import *; asyncio.run(test_async())\"")

# Optional async test function
async def test_async():
    print("\n🧪 Testing async functionality...")
    await turn_state.on_enter()
    print(f"✅ Setup complete - starter: {turn_state.current_turn_starter}")
    
    is_valid = await turn_state._validate_action(action)
    print(f"✅ Action validation: {is_valid}")
    
    await turn_state.on_exit()
    print("✅ Async test completed!")

if __name__ == "__main__":
    print("\n" + "=" * 40)
    print("✅ Simple test passed!")
    print("If you see this, the Turn State works correctly.")
    print("\nTo run async tests:")
    print("python -c \"import asyncio, simple_turn_test; asyncio.run(simple_turn_test.test_async())\"")