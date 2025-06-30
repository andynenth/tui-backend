#!/usr/bin/env python3
"""
🎯 Turn Play Integration Test
Tests if similar issues happen to turn play functionality
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from engine.room import Room
from engine.state_machine.core import GameAction, ActionType

async def test_turn_play_integration():
    print("🎯 Testing Turn Play Integration...")
    
    # Create room with bots
    room = Room("TURN_TEST", "TestHost")
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
    await asyncio.sleep(2.0)
    
    # Check if we reached Declaration phase
    current_phase = room.game_state_machine.current_phase
    print(f"📍 Current phase after preparation: {current_phase}")
    
    # Force all declarations to complete quickly
    if current_phase.value == "declaration":
        print("🤖 Fast-forwarding through all declarations...")
        
        # Get declaration order
        phase_data = room.game_state_machine.get_phase_data()
        declaration_order = phase_data.get('declaration_order', [])
        
        # Make all players declare
        for i, player in enumerate(declaration_order):
            player_name = getattr(player, 'name', str(player))
            declaration_value = 2  # Standard declaration
            
            action = GameAction(
                action_type=ActionType.DECLARE,
                player_name=player_name,
                payload={"value": declaration_value}
            )
            
            print(f"🎯 Making {player_name} declare {declaration_value}")
            result = await room.game_state_machine.handle_action(action)
            print(f"   Result: {result}")
            
            # Small delay
            await asyncio.sleep(0.1)
        
        # Wait for transition to Turn phase
        await asyncio.sleep(1.0)
    
    # Check if we reached Turn phase
    current_phase = room.game_state_machine.current_phase
    print(f"📍 Current phase after declarations: {current_phase}")
    
    if current_phase.value != "turn":
        print(f"❌ Expected Turn phase, got {current_phase}")
        return False
    
    print("✅ Successfully reached Turn phase!")
    
    # Test turn play functionality
    print("🎮 Testing turn play functionality...")
    
    # Get current turn data
    phase_data = room.game_state_machine.get_phase_data()
    current_player = phase_data.get('current_player')
    turn_number = phase_data.get('turn_number', 1)
    
    print(f"🎯 Current player: {current_player}")
    print(f"🎯 Turn number: {turn_number}")
    
    if not current_player:
        print("❌ No current player found in turn phase")
        return False
    
    # Get the player's hand to play realistic pieces
    game = room.game_state_machine.game
    current_player_obj = None
    
    for player in game.players:
        player_name = getattr(player, 'name', str(player))
        if player_name == current_player:
            current_player_obj = player
            break
    
    if not current_player_obj:
        print(f"❌ Could not find player object for {current_player}")
        return False
    
    player_hand = getattr(current_player_obj, 'hand', [])
    print(f"🃏 {current_player} hand: {len(player_hand)} pieces")
    
    if not player_hand:
        print("❌ Player has no pieces to play")
        return False
    
    # Try to play the first piece
    piece_to_play = player_hand[0]
    print(f"🎯 Attempting to play piece: {piece_to_play}")
    
    # Create play action with correct action type and payload structure
    play_action = GameAction(
        action_type=ActionType.PLAY_PIECES,  # Fixed: Use PLAY_PIECES not PLAY
        player_name=current_player,
        payload={
            "pieces": [piece_to_play],  # Fixed: Use actual piece objects
            "play_type": "single",
            "play_value": getattr(piece_to_play, 'point', 0),
            "is_valid": True
        }
    )
    
    # Test the play action
    try:
        result = await room.game_state_machine.handle_action(play_action)
        print(f"🔧 Play result: {result}")
        
        if result:
            print("✅ Turn play action processed successfully")
            
            # Check if turn state was updated
            await asyncio.sleep(0.1)
            updated_phase_data = room.game_state_machine.get_phase_data()
            turn_plays = updated_phase_data.get('turn_plays', {})
            
            print(f"📊 Turn plays recorded: {turn_plays}")
            
            if current_player in turn_plays or len(turn_plays) > 0:
                print("✅ Turn play recorded successfully")
                return True
            else:
                print("❌ Turn play not recorded")
                return False
        else:
            print("❌ Turn play action failed")
            return False
            
    except Exception as e:
        print(f"❌ Turn play error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🎮 Turn Play Integration Test")
    print("=" * 40)
    
    try:
        success = await test_turn_play_integration()
        
        if success:
            print("\n🎉 Turn play integration test PASSED!")
        else:
            print("\n❌ Turn play integration test FAILED!")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)