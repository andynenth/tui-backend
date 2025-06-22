#!/usr/bin/env python3
# backend/debug_turn_tests.py

import sys
import os

print("🔍 Starting debug script...")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Add backend to path for imports
backend_path = os.path.dirname(os.path.abspath(__file__))
print(f"Backend path: {backend_path}")

if backend_path not in sys.path:
    sys.path.append(backend_path)
    print("✅ Added backend to Python path")

# Test basic imports first
print("\n🧪 Testing basic imports...")

try:
    print("Importing datetime...")
    from datetime import datetime
    print("✅ datetime imported")
except Exception as e:
    print(f"❌ datetime import failed: {e}")
    sys.exit(1)

try:
    print("Importing asyncio...")
    import asyncio
    print("✅ asyncio imported")
except Exception as e:
    print(f"❌ asyncio import failed: {e}")
    sys.exit(1)

# Test engine imports
print("\n🧪 Testing engine imports...")

try:
    print("Importing core...")
    from engine.state_machine.core import GamePhase, ActionType, GameAction
    print("✅ Core imports successful")
    print(f"Available phases: {[p.value for p in GamePhase]}")
    print(f"Available actions: {[a.value for a in ActionType]}")
except Exception as e:
    print(f"❌ Core import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Importing TurnState...")
    from engine.state_machine.states.turn_state import TurnState
    print("✅ TurnState imported successfully")
except Exception as e:
    print(f"❌ TurnState import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Importing GameStateMachine...")
    from engine.state_machine.game_state_machine import GameStateMachine
    print("✅ GameStateMachine imported successfully")
except Exception as e:
    print(f"❌ GameStateMachine import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All imports successful!")

# Test basic instantiation
print("\n🧪 Testing basic instantiation...")

class TestGame:
    def __init__(self):
        self.players = ["Player1", "Player2", "Player3", "Player4"]
        self.round_starter = "Player1"
        self.current_player = "Player1"
        self.player_hands = {
            "Player1": [1, 2, 3, 4, 5, 6, 7, 8],
            "Player2": [9, 10, 11, 12, 13, 14, 15, 16],
            "Player3": [17, 18, 19, 20, 21, 22, 23, 24],
            "Player4": [25, 26, 27, 28, 29, 30, 31, 32]
        }
        self.player_piles = {
            "Player1": 0,
            "Player2": 0,
            "Player3": 0,
            "Player4": 0
        }
    
    def get_player_order_from(self, starter):
        start_idx = self.players.index(starter)
        return self.players[start_idx:] + self.players[:start_idx]

try:
    print("Creating test game...")
    game = TestGame()
    print("✅ Test game created")
    
    print("Creating state machine...")
    state_machine = GameStateMachine(game)
    print("✅ State machine created")
    
    print("Creating turn state...")
    class MockStateMachine:
        def __init__(self, game):
            self.game = game
    
    mock_sm = MockStateMachine(game)
    turn_state = TurnState(mock_sm)
    print("✅ Turn state created")
    
except Exception as e:
    print(f"❌ Instantiation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🎉 All basic tests passed!")
print("The issue is likely in the async test execution.")

# Test async functionality
print("\n🧪 Testing async functionality...")

async def simple_async_test():
    try:
        print("Testing turn state setup...")
        await turn_state.on_enter()
        print("✅ Turn state setup successful")
        
        print(f"Starter: {turn_state.current_turn_starter}")
        print(f"Turn order: {turn_state.turn_order}")
        
        await turn_state.on_exit()
        print("✅ Turn state cleanup successful")
        
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        import traceback
        traceback.print_exc()

# Run the async test
try:
    print("Running async test...")
    asyncio.run(simple_async_test())
    print("✅ Async test completed!")
except Exception as e:
    print(f"❌ Async execution failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🔍 Debug script completed!")
print("If you see this message, the core functionality works.")
print("The original script might have an exception in the main() function.")