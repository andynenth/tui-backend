#!/usr/bin/env python3
"""
🔧 Test Declaration Processing Fix
Tests just the declaration functionality to verify it works
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from engine.room import Room
from engine.state_machine.core import GameAction, ActionType

async def test_declaration_only():
    print("🎯 Testing Declaration Processing...")
    
    # Create room with one human, three bots
    room = Room("DECL_TEST", "TestHost")
    room.join_room("Bot1")
    room.join_room("Bot2") 
    room.join_room("Bot3")
    
    # Mark as bots
    room.players[1].is_bot = True
    room.players[2].is_bot = True
    room.players[3].is_bot = True
    
    print(f"✅ Room setup: {[p.name for p in room.players]}")
    
    # Start game
    result = await room.start_game_safe()
    if not result["success"]:
        print(f"❌ Game start failed: {result}")
        return False
        
    print("✅ Game started")
    
    # Wait for preparation to complete
    await asyncio.sleep(1.0)
    
    # Check current phase
    current_phase = room.game_state_machine.current_phase
    print(f"📍 Current phase: {current_phase}")
    
    if current_phase.value != "declaration":
        print(f"❌ Expected declaration phase, got {current_phase}")
        return False
        
    # Get phase data
    phase_data = room.game_state_machine.get_phase_data()
    current_declarer = phase_data.get('current_declarer')
    declarations = phase_data.get('declarations', {})
    
    print(f"🎯 Current declarer: {current_declarer}")
    print(f"📊 Declarations so far: {declarations}")
    
    # Test manual declaration for current declarer
    if current_declarer:
        print(f"🧪 Testing manual declaration for {current_declarer}")
        
        # Create declaration action
        action = GameAction(
            action_type=ActionType.DECLARE,
            player_name=current_declarer,
            payload={"value": 2}
        )
        
        # Process the action
        result = await room.game_state_machine.handle_action(action)
        print(f"🔧 Declaration result: {result}")
        
        # Check if declaration was recorded
        await asyncio.sleep(0.1)
        updated_phase_data = room.game_state_machine.get_phase_data()
        updated_declarations = updated_phase_data.get('declarations', {})
        
        print(f"📊 Updated declarations: {updated_declarations}")
        
        if current_declarer in updated_declarations:
            print(f"✅ Declaration recorded successfully: {current_declarer} = {updated_declarations[current_declarer]}")
            return True
        else:
            print(f"❌ Declaration not recorded for {current_declarer}")
            return False
    else:
        print("❌ No current declarer found")
        return False

async def main():
    print("🔧 Testing Declaration Processing Fix")
    print("=" * 40)
    
    try:
        success = await test_declaration_only()
        
        if success:
            print("\n🎉 Declaration test PASSED!")
        else:
            print("\n❌ Declaration test FAILED!")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)