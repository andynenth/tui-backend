#!/usr/bin/env python3
"""
🎯 Redealing Integration Test
Tests if similar issues happen to redealing functionality
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from engine.room import Room
from engine.state_machine.core import GameAction, ActionType

async def test_redealing_integration():
    print("🎯 Testing Redealing Integration...")
    
    # Create room with bots
    room = Room("REDEAL_TEST", "TestHost")
    room.join_room("Bot1")
    room.join_room("Bot2") 
    room.join_room("Bot3")
    
    # Mark as bots
    room.players[1].is_bot = True
    room.players[2].is_bot = True
    room.players[3].is_bot = True
    
    print(f"✅ Room setup: {[p.name for p in room.players]}")
    
    # Start game first to create the game object
    result = await room.start_game_safe()
    if not result["success"]:
        print(f"❌ Game start failed: {result}")
        return False
        
    print("✅ Game started")
    
    # Now override the dealing method to force weak hands for next deal
    print("🔧 Setting up forced weak hand dealing for testing...")
    
    def force_weak_hand_dealing():
        """Force weak hands for testing redealing functionality"""
        print("🎯 FORCING weak hands for redealing test...")
        # Use _deal_weak_hand to create weak hands for player 0 (TestHost)
        room.game._deal_weak_hand(weak_player_indices=[0], max_weak_points=9, limit=2)
    
    # Replace the dealing method temporarily for future deals
    room.game._deal_guaranteed_no_redeal = force_weak_hand_dealing
    
    # Wait for preparation to complete
    await asyncio.sleep(1.0)
    
    # Check if we're in Preparation phase
    current_phase = room.game_state_machine.current_phase
    print(f"📍 Current phase: {current_phase}")
    
    if current_phase.value != "preparation":
        print(f"❌ Expected Preparation phase for redealing test, got {current_phase}")
        return False
    
    # Get preparation phase data
    phase_data = room.game_state_machine.get_phase_data()
    weak_players = phase_data.get('weak_players', [])
    round_number = phase_data.get('round_number', 1)
    
    print(f"🎯 Round number: {round_number}")
    print(f"🎯 Weak players detected: {weak_players}")
    
    # Test case 1: If no weak players, test forced weak hand scenario
    if not weak_players:
        print("🧪 No weak players detected - creating artificial weak hand scenario...")
        
        # Manually create a weak hand scenario by simulating a player request
        test_player = room.players[0].name
        
        # Test weak hand request action with correct action type
        weak_hand_action = GameAction(
            action_type=ActionType.REDEAL_REQUEST,  # Fixed: Use REDEAL_REQUEST not REQUEST_REDEAL
            player_name=test_player,
            payload={"reason": "weak_hand"}
        )
        
        print(f"🎯 Testing weak hand request from {test_player}")
        
        try:
            result = await room.game_state_machine.handle_action(weak_hand_action)
            print(f"🔧 Weak hand request result: {result}")
            
            if result:
                print("✅ Weak hand request processed")
                
                # Check if redeal was triggered
                await asyncio.sleep(0.5)
                updated_phase_data = room.game_state_machine.get_phase_data()
                updated_weak_players = updated_phase_data.get('weak_players', [])
                
                print(f"📊 Updated weak players: {updated_weak_players}")
                
                if test_player in updated_weak_players:
                    print("✅ Player added to weak players list")
                    
                    # Test redeal action with correct action type
                    redeal_action = GameAction(
                        action_type=ActionType.REDEAL_RESPONSE,  # Fixed: Use REDEAL_RESPONSE
                        player_name=test_player,
                        payload={"accept": True}  # Fixed: Provide accept/decline decision
                    )
                    
                    print("🎯 Testing redeal confirmation...")
                    redeal_result = await room.game_state_machine.handle_action(redeal_action)
                    print(f"🔧 Redeal result: {redeal_result}")
                    
                    if redeal_result:
                        print("✅ Redeal action processed successfully")
                        
                        # Wait for redeal to complete
                        await asyncio.sleep(1.0)
                        
                        # Check if cards were redealt
                        game = room.game_state_machine.game
                        redealt_hand = getattr(room.players[0], 'hand', [])
                        
                        print(f"🃏 Player hand after redeal: {len(redealt_hand)} pieces")
                        
                        if len(redealt_hand) == 8:  # Should have 8 pieces after redeal
                            print("✅ Redealing completed successfully")
                            return True
                        else:
                            print(f"❌ Expected 8 pieces after redeal, got {len(redealt_hand)}")
                            return False
                    else:
                        print("❌ Redeal action failed")
                        return False
                else:
                    print("❌ Player not added to weak players list")
                    return False
            else:
                print("❌ Weak hand request failed")
                return False
                
        except Exception as e:
            print(f"❌ Weak hand request error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Test case 2: If weak players exist, test their redeal handling
    else:
        print(f"🧪 Testing existing weak players: {weak_players}")
        
        # Test if bots handle weak hands correctly
        for weak_player_name in weak_players:
            print(f"🤖 Testing bot weak hand handling for {weak_player_name}")
            
            # Bot should automatically request redeal - wait for it
            await asyncio.sleep(1.0)
            
            # Check if redeal was processed
            updated_phase_data = room.game_state_machine.get_phase_data()
            redeal_requests = updated_phase_data.get('redeal_requests', {})
            
            print(f"📊 Redeal requests: {redeal_requests}")
            
            if weak_player_name in redeal_requests:
                print(f"✅ Bot {weak_player_name} requested redeal")
            else:
                print(f"⚠️ Bot {weak_player_name} did not request redeal yet")
        
        # Wait for all redeal processing to complete
        await asyncio.sleep(2.0)
        
        # Check final state
        final_phase_data = room.game_state_machine.get_phase_data()
        final_phase = room.game_state_machine.current_phase
        
        print(f"📍 Final phase after redeal processing: {final_phase}")
        
        if final_phase.value == "declaration":
            print("✅ Successfully transitioned to Declaration after redealing")
            return True
        elif final_phase.value == "preparation":
            # Still in preparation - check if redealing is in progress
            redeal_in_progress = final_phase_data.get('redeal_in_progress', False)
            if redeal_in_progress:
                print("✅ Redealing process is active")
                return True
            else:
                print("⚠️ Still in preparation but no redeal in progress")
                return False
        else:
            print(f"❌ Unexpected phase after redeal processing: {final_phase}")
            return False

async def main():
    print("🔄 Redealing Integration Test")
    print("=" * 40)
    
    try:
        success = await test_redealing_integration()
        
        if success:
            print("\n🎉 Redealing integration test PASSED!")
        else:
            print("\n❌ Redealing integration test FAILED!")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)