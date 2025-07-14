#!/usr/bin/env python3
"""
Test script for simultaneous weak hand decision system
"""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from engine.game import Game
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction
from engine.state_machine.states.preparation_state import PreparationState


class MockStateMachine:
    """Mock state machine for testing"""

    def __init__(self):
        self.room_id = "test_room"
        # Create a simple game with 4 players for testing
        players = [
            Player("Andy", is_bot=False),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
            Player("Bot 4", is_bot=True),
        ]
        self.game = Game(players)
        self.game.redeal_multiplier = 1

    async def handle_action(self, action):
        print(
            f"🎯 MockStateMachine received action: {action.action_type} from {action.player_name}"
        )
        return {"success": True}


async def test_simultaneous_decisions():
    """Test the simultaneous decision system"""
    print("🧪 Testing Simultaneous Weak Hand Decision System")
    print("=" * 50)

    # Create mock state machine and preparation state
    mock_sm = MockStateMachine()
    prep_state = PreparationState(mock_sm)

    # Set up weak players
    prep_state.weak_players = {"Andy", "Bot 3"}
    prep_state.weak_players_awaiting = {"Andy", "Bot 3"}
    prep_state.decision_start_time = asyncio.get_event_loop().time()

    print(f"✅ Weak players: {prep_state.weak_players}")
    print(f"✅ Players awaiting: {prep_state.weak_players_awaiting}")

    # Test helper methods
    print("\n🔍 Testing helper methods:")
    print(f"All decisions received: {prep_state._all_weak_decisions_received()}")
    print(f"Count acceptances: {prep_state._count_acceptances()}")

    # Test enterprise broadcasting (simulate)
    print("\n📡 Testing enterprise broadcasting:")
    await prep_state._notify_weak_hands()
    print("✅ Enterprise broadcasting completed")

    # Simulate Andy accepting
    print("\n👤 Simulating Andy accepting redeal:")
    andy_action = GameAction(
        player_name="Andy",
        action_type=ActionType.REDEAL_REQUEST,
        payload={"accept": True},
    )

    result = await prep_state._handle_redeal_decision(andy_action)
    print(f"✅ Andy decision result: {result}")
    print(f"Decisions: {prep_state.redeal_decisions}")
    print(f"Awaiting: {prep_state.weak_players_awaiting}")

    # Simulate Bot 3 declining
    print("\n🤖 Simulating Bot 3 declining redeal:")
    bot_action = GameAction(
        player_name="Bot 3",
        action_type=ActionType.REDEAL_RESPONSE,
        payload={"accept": False},
    )

    result = await prep_state._handle_redeal_decision(bot_action)
    print(f"✅ Bot 3 decision result: {result}")
    print(f"Decisions: {prep_state.redeal_decisions}")
    print(f"Awaiting: {prep_state.weak_players_awaiting}")

    # Test first accepter logic
    print("\n🎯 Testing first accepter logic:")
    first_accepter = prep_state._get_first_accepter_by_play_order()
    print(f"✅ First accepter by play order: {first_accepter}")

    # Test state consistency
    print("\n🔍 Testing state consistency:")
    is_consistent = await prep_state._validate_state_consistency()
    print(f"✅ State consistent: {is_consistent}")

    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_simultaneous_decisions())
