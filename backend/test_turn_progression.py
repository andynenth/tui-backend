#!/usr/bin/env python3

"""
Test to reproduce and fix the turn progression issue where currentPlayer isn't updated after bot plays.
"""

import asyncio

from engine.bot_manager import BotManager
from engine.game import Game
from engine.piece import Piece
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction
from engine.state_machine.game_state_machine import GameStateMachine


async def test_turn_progression():
    """Test that turn progression works correctly with bot plays"""
    print("🧪 Testing Turn Progression Bug...")

    # Create game with 4 players
    players = [
        Player("Andy", is_bot=False),
        Player("Bot 2", is_bot=True),
        Player("Bot 3", is_bot=True),
        Player("Bot 4", is_bot=True),
    ]

    game = Game(players)
    room_id = "test-turn-progression"

    # Create state machine
    state_machine = GameStateMachine(game, room_id)

    # Create and register bot manager
    bot_manager = BotManager()
    bot_manager.register_game(room_id, game, state_machine)

    print("✅ Game and bot manager set up")

    # Deal specific hands to ensure reproducible test
    game.player_hands = {
        "Andy": [Piece("ADVISOR_RED"), Piece("CHARIOT_BLACK"), Piece("SOLDIER_BLACK")],
        "Bot 2": [
            Piece("GENERAL_RED"),
            Piece("HORSE_BLACK"),
            Piece("CANNON_RED"),
        ],  # Bot 2 has RED_GENERAL
        "Bot 3": [Piece("ADVISOR_BLACK"), Piece("ELEPHANT_RED"), Piece("SOLDIER_RED")],
        "Bot 4": [Piece("GENERAL_BLACK"), Piece("CHARIOT_RED"), Piece("HORSE_RED")],
    }

    # Manually transition through phases to TURN
    print("🔄 Starting state machine...")
    await state_machine.start()

    # Skip to TURN phase by completing PREPARATION and DECLARATION
    print("🎯 Advancing to TURN phase...")

    # Advance through preparation (should auto-complete with no weak hands)
    # This should transition to DECLARATION automatically

    # Complete declarations
    declare_actions = [
        GameAction("Bot 2", ActionType.DECLARE, {"value": 2}, is_bot=True),
        GameAction("Bot 3", ActionType.DECLARE, {"value": 1}, is_bot=True),
        GameAction("Bot 4", ActionType.DECLARE, {"value": 2}, is_bot=True),
        GameAction("Andy", ActionType.DECLARE, {"value": 1}, is_bot=False),
    ]

    for action in declare_actions:
        result = await state_machine.handle_action(action)
        print(f"📢 Declaration result for {action.player_name}: {result}")

    # Should now be in TURN phase
    current_phase = state_machine.current_phase
    print(f"🎮 Current phase: {current_phase}")

    if current_phase.value != "turn":
        print("❌ Not in TURN phase, skipping test")
        return

    # Get initial turn state
    phase_data = state_machine.get_phase_data()
    print(f"🎯 Initial turn state:")
    print(f"   - current_player: {phase_data.get('current_player')}")
    print(f"   - turn_order: {phase_data.get('turn_order')}")
    print(f"   - turn_complete: {phase_data.get('turn_complete')}")

    # Bot 2 should be the first player (has RED_GENERAL)
    current_player = phase_data.get("current_player")
    if current_player != "Bot 2":
        print(f"❌ Expected Bot 2 to start, got {current_player}")
        return

    print("✅ Bot 2 is correctly set as starting player")

    # Now simulate Bot 2 making a play
    print("🤖 Bot 2 making play...")

    # Create play action for Bot 2
    play_action = GameAction(
        "Bot 2",
        ActionType.PLAY_PIECES,
        {"pieces": [Piece("GENERAL_RED")]},  # Play the RED_GENERAL
        is_bot=True,
    )

    result = await state_machine.handle_action(play_action)
    print(f"🎯 BOT_PLAY_DEBUG: State machine result: {result}")

    # Check the updated turn state
    updated_phase_data = state_machine.get_phase_data()
    print(f"🎯 Updated turn state after Bot 2 play:")
    print(f"   - current_player: {updated_phase_data.get('current_player')}")
    print(f"   - turn_order: {updated_phase_data.get('turn_order')}")
    print(f"   - turn_complete: {updated_phase_data.get('turn_complete')}")
    print(f"   - next_player from result: {result.get('next_player')}")

    # Verify the next player is Bot 3
    next_player = updated_phase_data.get("current_player")
    expected_next = "Bot 3"

    if next_player == expected_next:
        print(f"✅ SUCCESS: Current player correctly updated to {next_player}")
    else:
        print(f"❌ FAIL: Expected {expected_next}, got {next_player}")
        print(
            f"❌ The bot manager will broadcast next_player: {result.get('next_player')}"
        )
        print(
            f"❌ This causes the frontend to show 'Waiting for other players' indefinitely"
        )

    # Test bot manager integration
    print("\n🤖 Testing bot manager broadcast...")

    # The bot manager should process this and generate the correct broadcast
    # We can't easily test the actual broadcast without WebSocket setup,
    # but we can verify the state machine returns the right data

    required_fields = ["next_player", "required_count", "turn_complete"]
    missing_fields = [field for field in required_fields if field not in result]

    if missing_fields:
        print(f"❌ Missing required fields in state machine result: {missing_fields}")
    else:
        print("✅ State machine returns all required fields")

    print(f"📊 Complete result data: {result}")


if __name__ == "__main__":
    asyncio.run(test_turn_progression())
