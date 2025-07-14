#!/usr/bin/env python3
"""
Test script to verify turn state action processing and phase data updates
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase
from engine.game import Game
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


async def test_turn_state_action_processing():
    """Test that turn state properly processes actions and updates phase data"""
    print("🧪 Starting turn state action processing test...")

    # Create mock game and state machine
    game = MockGame()
    state_machine = GameStateMachine(game)

    # Start state machine in TURN phase
    await state_machine.start(GamePhase.TURN)

    # Wait for setup
    await asyncio.sleep(0.1)

    print(f"✅ State machine started in phase: {state_machine.get_current_phase()}")

    # Get initial phase data
    initial_phase_data = state_machine.get_phase_data()
    print(f"📊 Initial phase data: {initial_phase_data}")
    print(f"📊 Initial current_player: {initial_phase_data.get('current_player')}")

    # Create a play action for the first player
    pieces_to_play = [Piece("GENERAL_RED"), Piece("GENERAL_BLACK")]
    play_action = GameAction(
        player_name="Human",
        action_type=ActionType.PLAY_PIECES,
        payload={
            "pieces": pieces_to_play,
            "play_type": "pair",
            "play_value": 3,
            "is_valid": True,
        },
        is_bot=False,
    )

    print(f"🎯 Creating play action for Human: {len(pieces_to_play)} pieces")

    # Submit action to state machine
    result = await state_machine.handle_action(play_action)
    print(f"📝 Action submission result: {result}")

    # Wait for action processing
    print("⏳ Waiting for action processing...")
    await asyncio.sleep(0.2)

    # Check phase data after action processing
    updated_phase_data = state_machine.get_phase_data()
    print(f"📊 Updated phase data: {updated_phase_data}")
    print(f"📊 Updated current_player: {updated_phase_data.get('current_player')}")

    # Verify the current player advanced
    initial_player = initial_phase_data.get("current_player")
    updated_player = updated_phase_data.get("current_player")

    if initial_player != updated_player:
        print(
            f"✅ SUCCESS: Current player advanced from '{initial_player}' to '{updated_player}'"
        )
    else:
        print(f"❌ FAILURE: Current player did not advance, still '{updated_player}'")

    # Check turn plays
    turn_plays = updated_phase_data.get("turn_plays", {})
    if "Human" in turn_plays:
        print(f"✅ SUCCESS: Human's play recorded in turn_plays")
        print(f"📊 Human's play data: {turn_plays['Human']}")
    else:
        print(f"❌ FAILURE: Human's play not found in turn_plays: {turn_plays}")

    # Check required piece count
    required_count = updated_phase_data.get("required_piece_count")
    if required_count == len(pieces_to_play):
        print(f"✅ SUCCESS: Required piece count set to {required_count}")
    else:
        print(
            f"❌ FAILURE: Required piece count incorrect. Expected {len(pieces_to_play)}, got {required_count}"
        )

    # Test Bot 1 action
    print(f"\n🤖 Testing Bot 1 action...")
    bot_pieces = [Piece("ADVISOR_RED"), Piece("ADVISOR_BLACK")]
    bot_action = GameAction(
        player_name="Bot 1",
        action_type=ActionType.PLAY_PIECES,
        payload={
            "pieces": bot_pieces,
            "play_type": "pair",
            "play_value": 7,
            "is_valid": True,
        },
        is_bot=True,
    )

    # Submit bot action
    bot_result = await state_machine.handle_action(bot_action)
    print(f"📝 Bot action submission result: {bot_result}")

    # Wait for processing
    await asyncio.sleep(0.2)

    # Check phase data after bot action
    bot_phase_data = state_machine.get_phase_data()
    print(f"📊 Phase data after bot action: {bot_phase_data}")

    final_player = bot_phase_data.get("current_player")
    if final_player != "Bot 1":
        print(f"✅ SUCCESS: Current player advanced from Bot 1 to '{final_player}'")
    else:
        print(
            f"❌ FAILURE: Current player did not advance from Bot 1, still '{final_player}'"
        )

    # Check both plays are recorded
    final_turn_plays = bot_phase_data.get("turn_plays", {})
    if len(final_turn_plays) == 2:
        print(f"✅ SUCCESS: Both plays recorded in turn_plays")
    else:
        print(
            f"❌ FAILURE: Expected 2 plays, got {len(final_turn_plays)}: {list(final_turn_plays.keys())}"
        )

    # Stop state machine
    await state_machine.stop()
    print("🛑 Test completed")


async def test_action_queue_processing():
    """Test that actions are properly queued and processed"""
    print("\n🧪 Starting action queue processing test...")

    game = MockGame()
    state_machine = GameStateMachine(game)

    await state_machine.start(GamePhase.TURN)
    await asyncio.sleep(0.1)

    # Add multiple actions rapidly
    actions = []
    piece_kinds = [
        ("GENERAL_RED", "GENERAL_BLACK"),
        ("ADVISOR_RED", "ADVISOR_BLACK"),
        ("ELEPHANT_RED", "ELEPHANT_BLACK"),
    ]
    for i, player_name in enumerate(["Human", "Bot 1", "Bot 2"]):
        pieces = [Piece(piece_kinds[i][0]), Piece(piece_kinds[i][1])]
        action = GameAction(
            player_name=player_name,
            action_type=ActionType.PLAY_PIECES,
            payload={
                "pieces": pieces,
                "play_type": "pair",
                "play_value": i + 3,
                "is_valid": True,
            },
            is_bot=(player_name != "Human"),
        )
        actions.append(action)

        # Add to queue
        result = await state_machine.handle_action(action)
        print(f"📝 Queued action for {player_name}: {result}")

    # Wait for all actions to process
    print("⏳ Waiting for all actions to process...")
    await asyncio.sleep(0.5)

    # Check final state
    final_data = state_machine.get_phase_data()
    final_plays = final_data.get("turn_plays", {})

    print(f"📊 Final turn plays: {list(final_plays.keys())}")
    print(f"📊 Final current player: {final_data.get('current_player')}")

    if len(final_plays) == 3:
        print(f"✅ SUCCESS: All 3 actions processed")
    else:
        print(f"❌ FAILURE: Expected 3 processed actions, got {len(final_plays)}")

    await state_machine.stop()
    print("🛑 Action queue test completed")


if __name__ == "__main__":

    async def main():
        await test_turn_state_action_processing()
        await test_action_queue_processing()

    asyncio.run(main())
