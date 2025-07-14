# File: backend/tests/test_integration.py

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime

from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase


class GameMock:  # FIX: Renamed to avoid pytest collecting it
    """Test game class - replace with your actual Game class"""

    def __init__(self):
        self.round_starter = "Player1"
        self.player_declarations = {}
        self.players = ["Player1", "Player2", "Player3", "Player4"]

    def get_player_order_from(self, starter):
        start_idx = self.players.index(starter)
        return self.players[start_idx:] + self.players[:start_idx]


@pytest.mark.asyncio
async def test_full_integration():
    """Test complete integration with realistic game flow"""
    game = GameMock()
    state_machine = GameStateMachine(game)

    try:
        # Start state machine
        await state_machine.start(GamePhase.DECLARATION)
        assert state_machine.get_current_phase() == GamePhase.DECLARATION

        # Test each player declaring in order
        expected_declarations = {}
        for i, player in enumerate(game.players):
            value = i + 1
            expected_declarations[player] = value

            action = GameAction(
                player_name=player,
                action_type=ActionType.DECLARE,
                payload={"value": value},
                timestamp=datetime.now(),
                sequence_id=i,
            )

            await state_machine.handle_action(action)

        # Process all actions
        await state_machine.process_pending_actions()

        # Verify final state
        assert game.player_declarations == expected_declarations
        print(f"✅ Final declarations: {game.player_declarations}")

    finally:
        await state_machine.stop()
