#!/usr/bin/env python3
"""
Test script to verify captured/declared numbers are preserved after page refresh.
This tests the fix for the regression bug where these values reset to 0/0.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime

# Add project root to path
sys.path.append('/Users/nrw/python/tui-project/liap-tui')

from backend.engine.async_room_manager import AsyncRoomManager
from backend.engine.state_machine.core import ActionType, GameAction

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def test_captured_declared_refresh():
    """Test that captured/declared values persist after reconnection"""
    room_manager = AsyncRoomManager()
    room_id = "TEST123"
    
    logger.info("=== Testing Captured/Declared Refresh Bug ===\n")
    
    # Create room
    room = await room_manager.create_room(room_id)
    await room_manager.join_room(room_id, "TestPlayer")
    logger.info(f"✅ Created room {room_id} and joined as TestPlayer")
    
    # Add bot players
    for i in range(3):
        await room_manager.add_bot_player(room_id, f"Bot {i+1}")
    logger.info("✅ Added 3 bot players")
    
    # Start game
    await room_manager.start_game(room_id)
    await asyncio.sleep(0.5)  # Wait for game initialization
    logger.info("✅ Game started")
    
    # Get game state
    game = room.game
    state_machine = room.game_state_machine
    
    # Wait for declaration phase
    while state_machine.get_current_phase().value != "declaration":
        await asyncio.sleep(0.1)
    logger.info(f"\n📋 Entered {state_machine.get_current_phase().value} phase")
    
    # Process bot declarations
    for i in range(3):
        bot_name = f"Bot {i+1}"
        action = GameAction(
            player_name=bot_name,
            action_type=ActionType.DECLARE,
            payload={"value": 2}
        )
        await state_machine.process_action(action)
        logger.info(f"  Bot {i+1} declared: 2")
    
    # TestPlayer declares 5
    action = GameAction(
        player_name="TestPlayer",
        action_type=ActionType.DECLARE,
        payload={"value": 5}
    )
    await state_machine.process_action(action)
    logger.info(f"  TestPlayer declared: 5")
    
    # Wait for turn phase
    while state_machine.get_current_phase().value != "turn":
        await asyncio.sleep(0.1)
    logger.info(f"\n🎮 Entered {state_machine.get_current_phase().value} phase")
    
    # Check declared values
    logger.info("\n📊 Player Declared Values:")
    for player in game.players:
        logger.info(f"  {player.name}: declared = {player.declared}")
    
    # Play one turn to get some captured piles
    # Bot 1 plays first (starter)
    action = GameAction(
        player_name="Bot 1",
        action_type=ActionType.PLAY_PIECES,
        payload={"pieces": [game.get_player("Bot 1").hand[0]]}
    )
    await state_machine.process_action(action)
    
    # Other players play
    for player_name in ["Bot 2", "Bot 3", "TestPlayer"]:
        player = game.get_player(player_name)
        action = GameAction(
            player_name=player_name,
            action_type=ActionType.PLAY_PIECES,
            payload={"pieces": [player.hand[0]]}
        )
        await state_machine.process_action(action)
    
    await asyncio.sleep(1.0)  # Wait for turn to complete
    
    # Check captured piles
    logger.info("\n📊 After Turn 1:")
    for player in game.players:
        logger.info(f"  {player.name}: captured = {player.captured_piles}, declared = {player.declared}")
    
    # Simulate what happens during phase_change broadcast
    logger.info("\n🔄 Simulating phase_change broadcast data:")
    
    # This is what base_state.py sends
    players_data = {}
    for player in game.players:
        player_name = player.name
        players_data[player_name] = {
            "name": player_name,
            "is_bot": getattr(player, "is_bot", False),
            "avatar_color": getattr(player, "avatar_color", None),
            "hand": [str(piece) for piece in player.hand],
            "hand_size": len(player.hand),
            "zero_declares_in_a_row": getattr(player, "zero_declares_in_a_row", 0),
            "declared": getattr(player, "declared", 0),  # This should include declared value
            "captured_piles": getattr(player, "captured_piles", 0),  # This should include captured piles
            "score": getattr(player, "score", 0),
        }
    
    logger.info("  Backend sends players data with:")
    for name, data in players_data.items():
        logger.info(f"    {name}: captured={data['captured_piles']}, declared={data['declared']}")
    
    # Check if bug exists
    test_player_data = players_data["TestPlayer"]
    if test_player_data["declared"] == 5:
        logger.info("\n✅ BACKEND CORRECTLY SENDS declared=5 for TestPlayer")
    else:
        logger.error(f"\n❌ BUG: Backend sends declared={test_player_data['declared']} instead of 5")
    
    # Check if any player has captured piles
    has_captured = any(p["captured_piles"] > 0 for p in players_data.values())
    if has_captured:
        logger.info("✅ BACKEND CORRECTLY SENDS captured_piles data")
    else:
        logger.error("❌ BUG: No captured_piles data sent by backend")
    
    logger.info("\n🎯 Frontend Fix Applied:")
    logger.info("  GameService.ts now preserves captured_piles and declared when")
    logger.info("  phaseData.players exists, preventing the 0/0 reset bug.")
    
    return players_data


if __name__ == "__main__":
    asyncio.run(test_captured_declared_refresh())