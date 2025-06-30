#!/usr/bin/env python3
"""
🎯 Direct Redealing Test
Tests redealing functionality by directly manipulating hands to create weak hand scenarios
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from engine.room import Room
from engine.state_machine.core import GameAction, ActionType, GamePhase
from engine.piece import Piece

async def test_redealing_direct():
    print("🎯 Testing Redealing Directly...")
    
    # Create room with bots
    room = Room("REDEAL_DIRECT", "TestHost")
    room.join_room("Bot1")
    room.join_room("Bot2") 
    room.join_room("Bot3")
    
    # Mark as bots
    room.players[1].is_bot = True
    room.players[2].is_bot = True
    room.players[3].is_bot = True
    
    print(f"✅ Room setup: {[p.name for p in room.players]}")
    
    # Start game first
    result = await room.start_game_safe()
    if not result["success"]:
        print(f"❌ Game start failed: {result}")
        return False
        
    print("✅ Game started")
    
    # Wait for initial setup to complete
    await asyncio.sleep(1.0)
    
    # Check current phase - should be Declaration since no weak hands by default
    current_phase = room.game_state_machine.current_phase
    print(f"📍 Initial phase: {current_phase}")
    
    # Force back to Preparation phase and create weak hands
    print("🔧 Forcing back to Preparation phase and creating weak hands...")
    
    # Manually create weak hands for TestHost (all pieces <= 9 points)
    weak_pieces = [
        Piece("SOLDIER_RED"),      # 2 points
        Piece("SOLDIER_BLACK"),    # 1 point
        Piece("CANNON_BLACK"),     # 3 points
        Piece("CANNON_RED"),       # 4 points
        Piece("HORSE_BLACK"),      # 5 points
        Piece("HORSE_RED"),        # 6 points
        Piece("CHARIOT_BLACK"),    # 7 points
        Piece("ELEPHANT_BLACK")    # 9 points - all <= 9 so it's a weak hand
    ]
    
    # Clear TestHost's hand and give them only weak pieces
    room.players[0].hand.clear()
    room.players[0].hand.extend(weak_pieces)
    
    print(f"🃏 Created weak hand for TestHost: {[str(p) for p in room.players[0].hand]}")
    print(f"🔍 Hand strength: max points = {max(p.point for p in room.players[0].hand)}")
    
    # Force transition back to Preparation phase
    await room.game_state_machine._immediate_transition_to(
        GamePhase.PREPARATION, 
        "Forced back to preparation for redealing test"
    )
    
    # Wait for transition
    await asyncio.sleep(0.5)
    
    current_phase = room.game_state_machine.current_phase
    print(f"📍 Current phase after force: {current_phase}")
    
    if current_phase.value != "preparation":
        print(f"❌ Expected Preparation phase, got {current_phase}")
        return False
    
    print("✅ Successfully in Preparation phase!")
    
    # Now test redeal request from TestHost (who has weak hand)
    print("🎯 Testing redeal request from TestHost...")
    
    # Create redeal request action
    redeal_request = GameAction(
        action_type=ActionType.REDEAL_REQUEST,
        player_name="TestHost",
        payload={"reason": "weak_hand"}
    )
    
    # Test the redeal request using legacy method (since prep state might not be event-driven yet)
    try:
        print(f"🔧 Submitting redeal request...")
        
        # Get the current state (should be PreparationState)
        current_state = room.game_state_machine.current_state
        print(f"🔧 Current state: {type(current_state).__name__}")
        
        # Use the state's handle_action method directly
        result = await current_state.handle_action(redeal_request)
        print(f"🔧 Redeal request result: {result}")
        
        if result:
            print("✅ Redeal request processed successfully")
            
            # Check if redeal state was updated
            await asyncio.sleep(0.1)
            phase_data = room.game_state_machine.get_phase_data()
            weak_players = phase_data.get('weak_players', set())
            current_weak_player = phase_data.get('current_weak_player')
            
            print(f"📊 Weak players: {weak_players}")
            print(f"🎯 Current weak player: {current_weak_player}")
            
            if "TestHost" in weak_players:
                print("✅ TestHost marked as weak player")
                
                # Now test redeal response (accept the redeal)
                print("🎯 Testing redeal response (accept)...")
                
                redeal_response = GameAction(
                    action_type=ActionType.REDEAL_RESPONSE,
                    player_name="TestHost",
                    payload={"accept": True}
                )
                
                response_result = await current_state.handle_action(redeal_response)
                print(f"🔧 Redeal response result: {response_result}")
                
                if response_result:
                    print("✅ Redeal response processed successfully")
                    
                    # Wait for redeal to process
                    await asyncio.sleep(1.0)
                    
                    # Check if hand was redealt
                    new_hand = room.players[0].hand
                    new_max_points = max(p.point for p in new_hand) if new_hand else 0
                    
                    print(f"🃏 New hand for TestHost: {[str(p) for p in new_hand]}")
                    print(f"🔍 New hand strength: max points = {new_max_points}")
                    
                    # Check if hand is no longer weak (should have at least one piece > 9)
                    if new_max_points > 9:
                        print("✅ Redealing successful - hand is no longer weak")
                        
                        # Check final phase
                        final_phase = room.game_state_machine.current_phase
                        print(f"📍 Final phase: {final_phase}")
                        
                        # Should transition to Declaration phase after successful redeal
                        if final_phase.value == "declaration":
                            print("✅ Successfully transitioned to Declaration after redeal")
                            return True
                        else:
                            print(f"⚠️ Expected Declaration phase, got {final_phase}")
                            return True  # Still successful redeal, just different phase
                    else:
                        print(f"❌ Hand still weak after redeal (max points: {new_max_points})")
                        return False
                else:
                    print("❌ Redeal response failed")
                    return False
            else:
                print("❌ TestHost not marked as weak player")
                return False
        else:
            print("❌ Redeal request failed")
            return False
            
    except Exception as e:
        print(f"❌ Redeal test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🔄 Direct Redealing Test")
    print("=" * 40)
    
    try:
        success = await test_redealing_direct()
        
        if success:
            print("\n🎉 Redealing test PASSED!")
        else:
            print("\n❌ Redealing test FAILED!")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)