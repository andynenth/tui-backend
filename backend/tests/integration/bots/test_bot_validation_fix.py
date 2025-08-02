#!/usr/bin/env python3
"""
Test script to verify the bot manager validation fix
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(__file__))

from engine.game import Game
from engine.piece import Piece
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine


async def test_bot_validation_fix():
    """Test that invalid bot actions don't cause state desynchronization"""
    print("🧪 Testing bot manager validation fix...")

    # Create a minimal game setup
    players = [
        Player("Andy", is_bot=False),
        Player("Bot 2", is_bot=True),
        Player("Bot 3", is_bot=True),
        Player("Bot 4", is_bot=True),
    ]

    # Give each player some pieces
    for i, player in enumerate(players):
        player.hand = [
            Piece("SOLDIER_RED"),
            Piece("SOLDIER_RED"),
            Piece("CANNON_RED"),
            Piece("CANNON_RED"),
        ]

    game = Game(players)
    game.room_id = "test_room"
    game.round_number = 3
    game.turn_number = 1

    # Create state machine
    state_machine = GameStateMachine(game)
    await state_machine.start(GamePhase.TURN)

    # Simulate the problematic scenario:
    # 1. Andy plays (valid)
    # 2. Bot 4 tries to play out of turn (invalid)

    print("\n🎯 Step 1: Andy plays valid pieces...")
    andy_action = GameAction(
        player_name="Andy",
        action_type=ActionType.PLAY_PIECES,
        payload={"pieces": [Piece("SOLDIER_RED"), Piece("SOLDIER_RED")]},
        is_bot=False,
    )

    # Queue Andy's action
    await state_machine.handle_action(andy_action)

    # Process actions
    await state_machine.process_pending_actions()

    print("\n🎯 Step 2: Bot 4 tries to play out of turn (should be rejected)...")
    bot4_action = GameAction(
        player_name="Bot 4",
        action_type=ActionType.PLAY_PIECES,
        payload={
            "pieces": [
                Piece("SOLDIER_RED"),
                Piece("SOLDIER_RED"),
                Piece("CANNON_RED"),
                Piece("CANNON_RED"),
            ]
        },
        is_bot=True,
    )

    # Queue Bot 4's invalid action
    await state_machine.handle_action(bot4_action)

    # Process actions - this should trigger validation feedback
    await state_machine.process_pending_actions()

    print("\n🔍 Checking hand sizes after invalid bot action...")
    for player in game.players:
        print(f"   {player.name}: {len(player.hand)} cards")

    # Verify no uneven distribution
    hand_sizes = [len(player.hand) for player in game.players]
    min_size = min(hand_sizes)
    max_size = max(hand_sizes)

    if max_size - min_size <= 1:
        print("✅ SUCCESS: Hand sizes are consistent after invalid bot action")
        print(f"   Hand size range: {min_size}-{max_size} cards")
        return True
    else:
        print("❌ FAILURE: Uneven hand distribution detected")
        print(f"   Hand size range: {min_size}-{max_size} cards")
        return False


async def main():
    """Run the test"""
    try:
        success = await test_bot_validation_fix()
        if success:
            print("\n🎉 Bot validation fix test PASSED")
            sys.exit(0)
        else:
            print("\n💥 Bot validation fix test FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
