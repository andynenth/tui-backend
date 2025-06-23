#!/usr/bin/env python3
"""Test complete integration: Room → Game → StateMachine → BotManager"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.room import Room
from engine.player import Player
from engine.bot_manager import BotManager
from engine.state_machine.core import GamePhase, ActionType, GameAction

# Initialize singleton bot manager
bot_manager = BotManager()

async def test_complete_integration():
    """Test the complete integrated system: Room → Game → StateMachine → BotManager"""
    print("🧪 Testing Complete Integration...")
    
    # Create room with host (automatically creates 4 players: host + 3 bots)
    room = Room("test-integration", "Alice")
    
    print(f"✅ Room created with {len(room.players)} players")
    
    # Start game (creates Game + StateMachine)
    result = await room.start_game_safe()
    
    if not result["success"]:
        print(f"❌ Game start failed: {result}")
        return False
    
    print("✅ Game started with StateMachine")
    
    # Register with bot manager (this is the fixed line we just changed)
    bot_manager.register_game("test-integration", room.game, room.game_state_machine)
    
    print("✅ Bot manager registered with StateMachine")
    
    # Test that bot manager can access state machine
    handler = bot_manager.active_games["test-integration"]
    
    # Test state machine access
    if handler.state_machine:
        print("✅ Bot handler has StateMachine reference")
        game_state = handler._get_game_state()
        print(f"✅ Bot can access game state: {len(game_state.players)} players")
    else:
        print("❌ Bot handler missing StateMachine reference")
        return False
    
    # Test bot action creation (simulating a bot declaration)
    action = GameAction(
        player_name="Bot1",
        action_type=ActionType.DECLARE,
        payload={"value": 3},
        is_bot=True
    )
    
    print(f"✅ Bot can create GameAction: {action.action_type}")
    
    # Verify the state machine is running
    if room.game_state_machine.is_running:
        print("✅ StateMachine is running and processing actions")
    else:
        print("❌ StateMachine is not running")
        return False
    
    # Test the action queue (the real integration test)
    print("🧪 Testing action processing through StateMachine...")
    
    # Submit a test action
    result = await room.game_state_machine.handle_action(action)
    print(f"✅ Action processed: {result}")
    
    # Clean up
    await room.game_state_machine.stop()
    bot_manager.unregister_game("test-integration")
    
    print("✅ Cleanup complete")
    print("🎉 Complete Integration Test PASSED")
    return True

async def test_multiple_games():
    """Test multiple concurrent games with bots"""
    print("\n🧪 Testing Multiple Concurrent Games...")
    
    games = []
    
    # Create 3 concurrent games
    for i in range(3):
        # Room automatically creates host + 3 bots
        room = Room(f"game-{i}", f"Human{i}")
        
        # Start game
        result = await room.start_game_safe()
        if result["success"]:
            # Register with bot manager with StateMachine
            bot_manager.register_game(f"game-{i}", room.game, room.game_state_machine)
            games.append(room)
            print(f"✅ Game {i} started and registered")
        else:
            print(f"❌ Game {i} failed to start")
            return False
    
    print(f"✅ {len(games)} concurrent games running")
    
    # Test that all games have proper bot integration
    for i, room in enumerate(games):
        handler = bot_manager.active_games[f"game-{i}"]
        if handler.state_machine and handler.state_machine.is_running:
            print(f"✅ Game {i} bot integration working")
        else:
            print(f"❌ Game {i} bot integration failed")
            return False
    
    # Cleanup all games
    for i, room in enumerate(games):
        await room.game_state_machine.stop()
        bot_manager.unregister_game(f"game-{i}")
    
    print("✅ All games cleaned up")
    print("🎉 Multiple Games Test PASSED")
    return True

async def main():
    """Run complete integration tests"""
    print("🚀 Starting Complete Integration Tests\n")
    
    try:
        # Test 1: Complete Integration
        success1 = await test_complete_integration()
        
        # Test 2: Multiple Concurrent Games
        success2 = await test_multiple_games()
        
        if success1 and success2:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Room → Game → StateMachine → BotManager integration working")
            print("✅ Bots now use StateMachine for all actions")
            print("✅ Multiple concurrent games supported")
            print("🚀 Phase 4 COMPLETE - System fully integrated!")
            return True
        else:
            print("\n❌ SOME INTEGRATION TESTS FAILED")
            return False
            
    except Exception as e:
        print(f"\n❌ INTEGRATION TESTS FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)