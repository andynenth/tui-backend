#!/usr/bin/env python3
"""
Test script to verify bot manager timing fix with state machine
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase
from engine.bot_manager import BotManager, GameBotHandler
from engine.player import Player
from engine.piece import Piece


class MockGame:
    """Mock game for testing"""

    def __init__(self):
        self.players = [
            Player("Human", is_bot=False),
            Player("Bot 1", is_bot=True),
            Player("Bot 2", is_bot=True),
            Player("Bot 3", is_bot=True),
        ]
        self.round_starter = "Human"
        self.current_player = "Human"
        self.room_id = "test_room"

        # Set up hands with test pieces
        for player in self.players:
            player.hand = [
                Piece("GENERAL_RED"),
                Piece("GENERAL_BLACK"),
                Piece("ADVISOR_RED"),
                Piece("ADVISOR_BLACK"),
                Piece("ELEPHANT_RED"),
                Piece("ELEPHANT_BLACK"),
                Piece("HORSE_RED"),
                Piece("HORSE_BLACK"),
            ]

        self.player_hands = {p.name: p.hand for p in self.players}


async def test_bot_manager_timing():
    """Test that bot manager gets correct state after waiting for state machine processing"""
    print("🧪 Testing bot manager timing fix...")

    # Create mock game and state machine
    game = MockGame()
    state_machine = GameStateMachine(game)

    # Create bot handler
    bot_handler = GameBotHandler("test_room", game, state_machine)

    # Start state machine in TURN phase
    await state_machine.start(GamePhase.TURN)
    await asyncio.sleep(0.1)

    print(
        f"✅ State machine started, initial current_player: {state_machine.get_phase_data().get('current_player')}"
    )

    # First, human player plays to advance the turn
    human_pieces = [Piece("ADVISOR_RED"), Piece("ADVISOR_BLACK")]
    human_action = GameAction(
        player_name="Human",
        action_type=ActionType.PLAY_PIECES,
        payload={"pieces": human_pieces},
        is_bot=False,
    )

    print(f"👤 Human plays first to advance turn...")
    await state_machine.handle_action(human_action)
    await asyncio.sleep(0.15)  # Wait for processing

    current_player_after_human = state_machine.get_phase_data().get("current_player")
    print(f"📊 After human play, current_player = {current_player_after_human}")

    # Now simulate bot making a play action (like in the real bot manager)
    bot = game.players[1]  # Bot 1
    pieces_to_play = [Piece("GENERAL_RED"), Piece("GENERAL_BLACK")]

    print(f"🤖 Simulating {bot.name} play action...")

    # Create action like bot manager does
    action = GameAction(
        player_name=bot.name,
        action_type=ActionType.PLAY_PIECES,
        payload={"pieces": pieces_to_play},
        is_bot=True,
    )

    # Submit action like bot manager does
    result = await state_machine.handle_action(action)
    print(f"📝 Action submitted: {result}")

    # Apply the new timing fix (wait 0.15s for state machine processing)
    print(f"⏳ Waiting 0.15s for state machine processing...")
    await asyncio.sleep(0.15)

    # Get phase data like bot manager does
    phase_data = state_machine.get_phase_data()
    current_player = phase_data.get("current_player")

    print(f"📊 Phase data after waiting: current_player = {current_player}")

    # Verify the state advanced correctly
    if current_player != bot.name:
        print(f"✅ SUCCESS: State advanced from {bot.name} to {current_player}")
        print(f"✅ Bot manager timing fix is working!")
    else:
        print(f"❌ FAILURE: State did not advance, still {current_player}")

    await state_machine.stop()
    print("🛑 Test completed")


if __name__ == "__main__":
    asyncio.run(test_bot_manager_timing())
