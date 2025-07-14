# backend/test_state_integration.py

import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine


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
    game = TestGame()
    state_machine = GameStateMachine(game)

    try:
        print("🧪 Testing state machine integration...")

        # Start in declaration phase
        await state_machine.start(GamePhase.DECLARATION)
        print(f"✅ Started in phase: {state_machine.get_current_phase().value}")

        # Test each player declaring
        for i, player in enumerate(game.players):
            action = GameAction(
                player_name=player,
                action_type=ActionType.DECLARE,
                payload={"value": i + 1},
                timestamp=datetime.now(),
                sequence_id=i,
            )

            await state_machine.handle_action(action)
            print(f"✅ Player {player} declared: {i + 1}")

        # FIX: Process all pending actions before checking results
        await state_machine.process_pending_actions()

        # Check final state
        print(f"📊 Final declarations: {game.player_declarations}")

        # Verify declarations were actually recorded
        expected = {"Player1": 1, "Player2": 2, "Player3": 3, "Player4": 4}
        if game.player_declarations == expected:
            print(f"🎯 Integration test completed successfully!")
        else:
            print(f"❌ Expected: {expected}")
            print(f"❌ Got: {game.player_declarations}")

    finally:
        await state_machine.stop()


if __name__ == "__main__":
    asyncio.run(test_integration())
