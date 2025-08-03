# backend/run_tests.py

"""
Quick test runner to verify everything works
Run with: python run_tests.py
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

from backend.engine.state_machine.core import ActionType, GameAction, GamePhase
from backend.engine.state_machine.game_state_machine import GameStateMachine


class TestGame:
    def __init__(self):
        self.round_starter = "Player1"
        self.player_declarations = {}
        self.players = ["Player1", "Player2", "Player3", "Player4"]

    def get_player_order_from(self, starter):
        start_idx = self.players.index(starter)
        return self.players[start_idx:] + self.players[:start_idx]


async def run_quick_test():
    print("🚀 Running quick state machine test...")

    game = TestGame()
    state_machine = GameStateMachine(game)

    try:
        # Start state machine
        await state_machine.start(GamePhase.DECLARATION)
        print(f"✅ Started in phase: {state_machine.get_current_phase().value}")

        # Test declarations
        for i, player in enumerate(game.players):
            action = GameAction(
                player_name=player,
                action_type=ActionType.DECLARE,
                payload={"value": i + 1},
                timestamp=datetime.now(),
                sequence_id=i,
            )

            await state_machine.handle_action(action)
            print(f"✅ {player} declared: {i + 1}")

        # Process all actions
        await state_machine.process_pending_actions()

        # Check results
        expected = {"Player1": 1, "Player2": 2, "Player3": 3, "Player4": 4}
        actual = game.player_declarations

        print(f"📊 Expected: {expected}")
        print(f"📊 Actual:   {actual}")

        if actual == expected:
            print("🎯 ✅ ALL TESTS PASSED!")
            return True
        else:
            print("❌ TESTS FAILED!")
            return False

    finally:
        await state_machine.stop()


if __name__ == "__main__":
    success = asyncio.run(run_quick_test())
    sys.exit(0 if success else 1)
