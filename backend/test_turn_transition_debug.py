#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.game import Game
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase

async def test_turn_transition():
    """Test declaration to turn phase transition with debug logging"""
    
    print("🔧 Testing Declaration to Turn Transition Debug")
    print("=" * 50)
    
    # Create game with players
    from engine.player import Player
    
    players = [
        Player("TestHost", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True)
    ]
    # Add host status separately
    players[0].is_host = True
    
    game = Game(players)
    game.room_id = "TURN_TEST"
    
    # Mock broadcast callback (no WebSocket needed for debugging)
    async def mock_broadcast(event_type, data):
        print(f"📤 MOCK_BROADCAST: {event_type} with data keys: {list(data.keys())}")
    
    # Create state machine 
    state_machine = GameStateMachine(game, broadcast_callback=mock_broadcast)
    state_machine.room_id = "TURN_TEST"
    
    try:
        # Start in preparation phase
        await state_machine.start(GamePhase.PREPARATION)
        
        print(f"\n📍 Current phase: {state_machine.current_phase}")
        
        # Should now be in declaration phase - make all declarations
        if state_machine.current_phase == GamePhase.DECLARATION:
            print("🎯 Making all declarations to trigger turn transition...")
            
            # Bot1 declares
            action1 = GameAction(
                player_name="Bot1",
                action_type=ActionType.DECLARE,
                payload={"value": 2}
            )
            result1 = await state_machine.handle_action(action1)
            print(f"✅ Bot1 declared: {result1['success']}")
            
            # Bot2 declares  
            action2 = GameAction(
                player_name="Bot2",
                action_type=ActionType.DECLARE,
                payload={"value": 2}
            )
            result2 = await state_machine.handle_action(action2)
            print(f"✅ Bot2 declared: {result2['success']}")
            
            # Bot3 declares
            action3 = GameAction(
                player_name="Bot3",
                action_type=ActionType.DECLARE,
                payload={"value": 2}
            )
            result3 = await state_machine.handle_action(action3)
            print(f"✅ Bot3 declared: {result3['success']}")
            
            # TestHost makes final declaration (should trigger turn transition)
            print("\n🎯 Making FINAL declaration to trigger turn transition...")
            final_action = GameAction(
                player_name="TestHost",
                action_type=ActionType.DECLARE,
                payload={"value": 2}
            )
            final_result = await state_machine.handle_action(final_action)
            print(f"✅ TestHost final declaration: {final_result['success']}")
            print(f"📍 Final phase: {state_machine.current_phase}")
            
            if state_machine.current_phase == GamePhase.TURN:
                print("🎉 SUCCESS: Turn transition completed!")
            else:
                print("❌ FAILURE: Turn transition failed")
        
        await state_machine.stop()
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_turn_transition())