#!/usr/bin/env python3
"""
🎯 Simple Event-Driven Test
Quick test to verify event-driven architecture conversion works
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from engine.room import Room
from engine.state_machine.core import GameAction, ActionType, GamePhase

async def test_event_driven_simple():
    print("🎯 Testing Event-Driven Architecture...")
    
    # Create simple room
    room = Room("EVENT_TEST", "TestHost")
    room.join_room("Bot1")
    
    # Mark as bot
    room.players[1].is_bot = True
    
    print(f"✅ Room setup: {[p.name for p in room.players[:2]]}")
    
    # Start game
    result = await room.start_game_safe()
    if not result["success"]:
        print(f"❌ Game start failed: {result}")
        return False
        
    print("✅ Game started")
    
    # Wait for initial setup
    await asyncio.sleep(1.0)
    
    # Check current phase
    current_phase = room.game_state_machine.current_phase
    print(f"📍 Current phase: {current_phase}")
    
    # Test that we can now use the state machine's handle_action method directly
    # (it should now route to process_event for all states)
    
    if current_phase.value == "declaration":
        print("🎯 Testing event-driven declaration...")
        
        # Get current declarer
        phase_data = room.game_state_machine.get_phase_data()
        current_declarer = phase_data.get('current_declarer')
        print(f"🎯 Current declarer: {current_declarer}")
        
        # Create declaration action for the correct player
        action = GameAction(
            action_type=ActionType.DECLARE,
            player_name=current_declarer,
            payload={"value": 2}
        )
        
        # This should now work with event-driven architecture
        result = await room.game_state_machine.handle_action(action)
        print(f"🔧 Declaration result: {result}")
        
        if result and result.get('success', False):
            print("✅ Event-driven declaration successful!")
            return True
        else:
            print(f"❌ Event-driven declaration failed: {result}")
            return False
    else:
        print(f"⚠️ Unexpected phase {current_phase} - test designed for declaration")
        return False

async def main():
    print("🚀 Event-Driven Architecture Test")
    print("=" * 40)
    
    try:
        success = await test_event_driven_simple()
        
        if success:
            print("\n🎉 Event-driven test PASSED!")
        else:
            print("\n❌ Event-driven test FAILED!")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)