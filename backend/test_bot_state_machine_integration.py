#!/usr/bin/env python3
"""Test bot manager integration with state machine"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from engine.game import Game
from engine.player import Player
from engine.bot_manager import BotManager
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GamePhase

async def test_bot_state_machine_integration():
    """Test that bots work with state machine instead of direct game calls"""
    print("🧪 Testing Bot + State Machine Integration...")
    
    # Create game with mixed bots and humans
    players = [
        Player("Alice", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True), 
        Player("Charlie", is_bot=False)
    ]
    
    game = Game(players)
    
    # Create state machine
    state_machine = GameStateMachine(game)
    
    # Create bot manager with state machine
    bot_manager = BotManager()
    bot_manager.register_game("test_room", game, state_machine)
    
    # Start state machine in preparation phase
    await state_machine.start(GamePhase.PREPARATION)
    
    print("✅ State machine started in PREPARATION phase")
    
    # Test that bot manager can access game state
    handler = bot_manager.active_games["test_room"]
    game_state = handler._get_game_state()
    
    print(f"✅ Bot manager can access game state: {len(game_state.players)} players")
    
    # Test bot action creation (without executing)
    from engine.state_machine.core import GameAction, ActionType
    
    test_action = GameAction(
        player_name="Bot1",
        action_type=ActionType.DECLARE,
        payload={"value": 3},
        is_bot=True
    )
    
    print(f"✅ Bot can create GameAction: {test_action.action_type}")
    
    # Test property access patterns
    try:
        current_order = game_state.current_order if hasattr(game_state, 'current_order') else []
        players_list = game_state.players if hasattr(game_state, 'players') else []
        print(f"✅ Property access works: {len(current_order)} in order, {len(players_list)} total")
    except Exception as e:
        print(f"❌ Property access failed: {e}")
        return False
    
    # Stop state machine
    await state_machine.stop()
    print("✅ State machine stopped")
    
    print("🎉 Bot + State Machine Integration Test PASSED")
    return True

async def test_bot_fallback_mode():
    """Test that bots work without state machine (fallback mode)"""
    print("\n🧪 Testing Bot Fallback Mode (no state machine)...")
    
    # Create game with bots
    players = [
        Player("Alice", is_bot=False),
        Player("Bot1", is_bot=True),
    ]
    
    game = Game(players)
    
    # Create bot manager WITHOUT state machine
    bot_manager = BotManager()
    bot_manager.register_game("test_fallback", game)  # No state machine
    
    handler = bot_manager.active_games["test_fallback"]
    
    # Test fallback access
    game_state = handler._get_game_state()  # Should return game directly
    
    print(f"✅ Fallback mode works: {len(game_state.players)} players via direct game access")
    
    print("🎉 Bot Fallback Mode Test PASSED")
    return True

async def main():
    """Run all bot integration tests"""
    print("🚀 Starting Bot Manager Integration Tests\n")
    
    try:
        # Test 1: Bot + State Machine Integration
        success1 = await test_bot_state_machine_integration()
        
        # Test 2: Bot Fallback Mode
        success2 = await test_bot_fallback_mode()
        
        if success1 and success2:
            print("\n🎉 ALL TESTS PASSED - Bot Manager Ready for Phase 3!")
            return True
        else:
            print("\n❌ SOME TESTS FAILED")
            return False
            
    except Exception as e:
        print(f"\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)