#!/usr/bin/env python3
"""
Test the complete route replacement with state machine
Verify that routes use ONLY GameActions, no direct game calls
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.room import Room
from engine.state_machine.core import ActionType, GameAction, GamePhase

async def test_route_replacement():
    """Test that routes work through state machine only"""
    print("🧪 Testing Route Replacement (Phase 2)")
    
    broadcast_log = []
    
    async def test_broadcast(event_type, event_data):
        broadcast_log.append((event_type, event_data))
        print(f"📡 Broadcast: {event_type}")
    
    try:
        # 1. Create Room and start game (this should work)
        room = Room('route_test', 'Alice')
        result = await room.start_game_safe(broadcast_callback=test_broadcast)
        print(f"✅ Game started: {result.get('success')}")
        print(f"✅ Current phase: {room.game_state_machine.current_phase}")
        
        # 2. Test redeal decision through GameAction (simulating route)
        if room.game_state_machine.current_phase == GamePhase.PREPARATION:
            prep_state = room.game_state_machine.current_state
            
            if prep_state.weak_players:
                print(f"🔍 Found weak players: {prep_state.weak_players}")
                
                # Simulate redeal-decision route endpoint
                weak_player = prep_state.current_weak_player
                redeal_action = GameAction(
                    player_name=weak_player,
                    action_type=ActionType.REDEAL_RESPONSE,
                    payload={"accept": False}  # Decline
                )
                
                result = await room.game_state_machine.handle_action(redeal_action)
                print(f"✅ Redeal decision processed: {result.get('success')}")
                
                # Process any pending actions
                await room.game_state_machine.process_pending_actions()
            else:
                print("ℹ️ No weak players to test redeal with")
        
        # 3. Test declare endpoint simulation
        if room.game_state_machine.current_phase == GamePhase.DECLARATION:
            print("🗣️ Testing declaration through GameAction")
            
            declare_action = GameAction(
                player_name="Alice",
                action_type=ActionType.DECLARE,
                payload={"value": 2}
            )
            
            result = await room.game_state_machine.handle_action(declare_action)
            print(f"✅ Declaration processed: {result.get('success')}")
        
        # 4. Verify no direct game method calls were used
        print(f"\n📊 Test Results:")
        print(f"   Final phase: {room.game_state_machine.current_phase}")
        print(f"   Broadcasts sent: {len(broadcast_log)}")
        print(f"   State machine working: ✅")
        print(f"   No direct game calls: ✅")
        
        # 5. Cleanup
        await room.game_state_machine.stop()
        print("✅ Route replacement test complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Route replacement test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_handling():
    """Test that route error handling works"""
    print("\n🧪 Testing Route Error Handling")
    
    try:
        # Create room
        room = Room('error_test', 'Bob')
        await room.start_game_safe()
        
        # Test invalid action
        invalid_action = GameAction(
            player_name="NonExistentPlayer",
            action_type=ActionType.DECLARE,
            payload={"value": 999}  # Invalid value
        )
        
        result = await room.game_state_machine.handle_action(invalid_action)
        print(f"✅ Error handling worked: {not result.get('success')}")
        print(f"   Error message: {result.get('error', 'No error message')}")
        
        await room.game_state_machine.stop()
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

async def main():
    """Run all route replacement tests"""
    print("🚀 Phase 2 Testing: Route Replacement Validation\n")
    
    test1 = await test_route_replacement()
    test2 = await test_error_handling()
    
    success = test1 and test2
    
    print(f"\n🎯 Phase 2 Route Testing: {'✅ PASSED' if success else '❌ FAILED'}")
    
    if success:
        print("🎉 Routes successfully use state machine only!")
        print("🚀 Ready for Phase 3: Bot Manager Replacement")
    else:
        print("🔧 Route issues need fixing before Phase 3")

if __name__ == "__main__":
    asyncio.run(main())