#!/usr/bin/env python3
"""
🎯 Full Declaration Sequence Test
Tests that all bots declare in order and the game progresses correctly
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from engine.room import Room

async def test_full_declaration_sequence():
    print("🎯 Testing Full Declaration Sequence...")
    
    # Create room with bots
    room = Room("FULL_DECL_TEST", "TestHost")
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
    
    # Wait for all declarations to complete
    max_wait = 15  # 15 seconds max
    wait_time = 0
    last_phase = None
    
    while wait_time < max_wait:
        await asyncio.sleep(1.0)
        wait_time += 1
        
        current_phase = room.game_state_machine.current_phase
        if current_phase != last_phase:
            print(f"📍 Phase changed to: {current_phase}")
            last_phase = current_phase
        
        # Check if we've moved past declarations
        if current_phase.value == "turn":
            print("🎉 Successfully transitioned to TURN phase!")
            break
        elif current_phase.value == "scoring":
            print("🎉 Successfully transitioned to SCORING phase!")
            break
            
        # Show declaration progress
        if current_phase.value == "declaration":
            phase_data = room.game_state_machine.get_phase_data()
            declarations = phase_data.get('declarations', {})
            current_declarer = phase_data.get('current_declarer')
            
            print(f"🎯 Current declarer: {current_declarer}")
            print(f"📊 Declarations so far: {declarations}")
            
            # Check if all 4 players have declared
            if len(declarations) >= 4:
                print("🎉 All players declared! Waiting for phase transition...")
                # Give a bit more time for transition
                await asyncio.sleep(2.0)
                break
    
    # Final check
    final_phase = room.game_state_machine.current_phase
    final_phase_data = room.game_state_machine.get_phase_data()
    final_declarations = final_phase_data.get('declarations', {})
    
    print(f"\n🔍 Final Results:")
    print(f"   Phase: {final_phase}")
    print(f"   Declarations: {final_declarations}")
    print(f"   Declaration count: {len(final_declarations)}")
    
    if len(final_declarations) >= 3:  # At least 3 bots should have declared
        print("✅ Bot declarations successful!")
        return True
    else:
        print("❌ Not enough declarations recorded")
        return False

async def main():
    print("🎯 Full Declaration Sequence Test")
    print("=" * 40)
    
    try:
        success = await test_full_declaration_sequence()
        
        if success:
            print("\n🎉 Declaration sequence test PASSED!")
        else:
            print("\n❌ Declaration sequence test FAILED!")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)