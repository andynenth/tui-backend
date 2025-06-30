#!/usr/bin/env python3
"""
🔧 Minimal Declaration Test
Just test basic room creation and phase checking
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from engine.room import Room

async def test_room_creation():
    print("🧪 Testing basic room creation...")
    
    # Create room
    room = Room("MIN_TEST", "TestHost")
    print(f"✅ Room created: {room.room_id}")
    
    # Add players
    room.join_room("Bot1")
    room.join_room("Bot2") 
    room.join_room("Bot3")
    
    # Mark as bots
    room.players[1].is_bot = True
    room.players[2].is_bot = True
    room.players[3].is_bot = True
    
    print(f"✅ Players: {[p.name for p in room.players]}")
    
    print("🎮 Testing game start with timeout...")
    
    # Start game with a timeout
    try:
        result = await asyncio.wait_for(room.start_game_safe(), timeout=10.0)
        print(f"✅ Game started: {result['success']}")
        
        if result["success"]:
            # Check state machine exists
            if room.game_state_machine:
                print(f"✅ State machine exists")
                print(f"📍 Current phase: {room.game_state_machine.current_phase}")
                return True
            else:
                print("❌ No state machine created")
                return False
        else:
            print(f"❌ Game start failed: {result}")
            return False
            
    except asyncio.TimeoutError:
        print("❌ Game start timed out after 10 seconds")
        return False
    except Exception as e:
        print(f"❌ Game start error: {e}")
        return False

async def main():
    print("🔧 Minimal Declaration Test")
    print("=" * 30)
    
    try:
        success = await test_room_creation()
        
        if success:
            print("\n🎉 Basic test PASSED!")
        else:
            print("\n❌ Basic test FAILED!")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)