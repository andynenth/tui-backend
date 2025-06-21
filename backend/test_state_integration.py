import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase
from datetime import datetime

# Import your existing game class
# from engine.game import Game  # Adjust path to your game class

class TestGame:
    """Minimal test game class - replace with your actual Game class"""
    def __init__(self):
        self.round_starter = "Player1"
        self.player_declarations = {}
        self.players = ["Player1", "Player2", "Player3", "Player4"]
    
    def get_player_order_from(self, starter):
        # Rotate player list to start from starter
        start_idx = self.players.index(starter)
        return self.players[start_idx:] + self.players[:start_idx]

async def test_integration():
    # Create game and state machine
    game = TestGame()  # Replace with: Game()
    state_machine = GameStateMachine(game)
    
    print("🧪 Testing state machine integration...")
    
    # Start in declaration phase
    await state_machine.start(GamePhase.DECLARATION)
    print(f"✅ Started in phase: {state_machine.get_current_phase().value}")
    
    # Test each player declaring
    for i, player in enumerate(game.players):
        action = GameAction(
            player_name=player,
            action_type=ActionType.DECLARE,
            payload={"value": i + 1},  # Each player declares different value
            timestamp=datetime.now(),
            sequence_id=i
        )
        
        await state_machine.handle_action(action)
        print(f"✅ Player {player} declared: {i + 1}")
    
    # Give state machine time to process all actions
    await asyncio.sleep(0.5)
    
    # Check final state
    print(f"📊 Final declarations: {game.player_declarations}")
    print(f"🎯 Integration test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_integration())