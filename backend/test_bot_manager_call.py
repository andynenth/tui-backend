#!/usr/bin/env python3

"""
Test to check what the bot manager gets when calling the state machine.
"""

import asyncio

from engine.bot_manager import BotManager
from engine.game import Game
from engine.piece import Piece
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction
from engine.state_machine.game_state_machine import GameStateMachine


async def mock_broadcast(room_id, event, data):
    """Mock broadcast function for testing"""
    print(f"📡 MOCK_BROADCAST: {event} -> {data}")


async def test_bot_manager_state_machine_call():
    """Test what the bot manager actually gets from state machine"""
    print("🧪 Testing Bot Manager State Machine Integration...")

    # Create game with 4 players
    players = [
        Player("Andy", is_bot=False),
        Player("Bot 2", is_bot=True),
        Player("Bot 3", is_bot=True),
        Player("Bot 4", is_bot=True),
    ]

    game = Game(players)
    room_id = "test-bot-manager"

    # Deal specific hands
    game.player_hands = {
        "Andy": [Piece("ADVISOR_RED"), Piece("CHARIOT_BLACK")],
        "Bot 2": [Piece("GENERAL_RED"), Piece("HORSE_BLACK")],
        "Bot 3": [Piece("ADVISOR_BLACK"), Piece("ELEPHANT_RED")],
        "Bot 4": [Piece("GENERAL_BLACK"), Piece("CHARIOT_RED")],
    }

    # Set Bot 2 as starter
    game.round_starter = "Bot 2"
    game.current_player = "Bot 2"

    # Create state machine with mock broadcast
    state_machine = GameStateMachine(game, room_id)
    state_machine.broadcast_callback = mock_broadcast

    # Create bot manager
    bot_manager = BotManager()
    bot_manager.register_game(room_id, game, state_machine)
    handler = bot_manager.active_games[room_id]

    print("✅ Setup complete")

    # Manually transition to TURN phase
    from engine.state_machine.core import GamePhase
    from engine.state_machine.states.turn_state import TurnState

    # Create turn state and set it as current
    turn_state = TurnState(state_machine)
    state_machine.current_state = turn_state
    state_machine._current_phase = GamePhase.TURN

    # Initialize turn phase
    await turn_state._setup_phase()

    print(f"🎯 Current phase: {state_machine.current_phase}")
    print(f"🎯 Turn order: {turn_state.turn_order}")
    print(f"🎯 Current player: {turn_state._get_current_player()}")

    # Now test the bot manager's _bot_play_first method
    print("\n🤖 Testing bot manager _bot_play_first method...")

    # Get Bot 2 player object
    bot_2 = None
    for player in players:
        if player.name == "Bot 2":
            bot_2 = player
            break

    if not bot_2:
        print("❌ Bot 2 not found")
        return

    # Test direct state machine call (what the bot manager should do)
    print("\n🔍 Testing direct state machine call...")

    selected_pieces = [Piece("GENERAL_RED")]
    action = GameAction(
        player_name=bot_2.name,
        action_type=ActionType.PLAY_PIECES,
        payload={"pieces": selected_pieces},
        is_bot=True,
    )

    print(f"🎯 Action payload: {action.payload}")

    result = await state_machine.handle_action(action)
    print(f"🎯 DIRECT CALL RESULT: {result}")

    # Check what fields are in the result
    required_fields = ["next_player", "required_count", "turn_complete"]
    for field in required_fields:
        value = result.get(field, "MISSING")
        print(f"   - {field}: {value}")

    # Now test what the bot manager's broadcast would send
    print(f"\n📡 Bot manager would broadcast:")
    broadcast_data = {
        "player": bot_2.name,
        "pieces": [str(p) for p in selected_pieces],
        "valid": result.get("is_valid", True),
        "play_type": result.get("play_type", "UNKNOWN"),
        "next_player": result.get("next_player"),
        "required_count": result.get("required_count"),
        "turn_complete": result.get("turn_complete", False),
    }
    print(f"🎯 BROADCAST DATA: {broadcast_data}")

    # Verify critical fields
    next_player = broadcast_data.get("next_player")
    if next_player == "Bot 3":
        print("✅ SUCCESS: Bot manager would broadcast correct next_player")
    else:
        print(f"❌ FAIL: Expected Bot 3, would broadcast {next_player}")


if __name__ == "__main__":
    asyncio.run(test_bot_manager_state_machine_call())
