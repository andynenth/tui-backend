#!/usr/bin/env python3
"""
🎯 Simple Turn Play Test
Tests turn play functionality directly without going through declarations
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from engine.room import Room
from engine.state_machine.core import GameAction, ActionType, GamePhase

async def test_turn_play_direct():
    print("🎯 Testing Turn Play Directly...")
    
    # Create room with bots
    room = Room("TURN_SIMPLE", "TestHost")
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
    
    # Wait for initial setup
    await asyncio.sleep(2.0)
    
    # Force transition to Turn phase for testing
    print("🔧 Forcing transition to Turn phase...")
    
    # Set up game state for turn phase
    game = room.game_state_machine.game
    game.current_player = "TestHost"  # Set current player
    game.round_starter = "TestHost"
    
    # Add mock declarations to satisfy state machine
    game.player_declarations = {
        "TestHost": 2,
        "Bot1": 2, 
        "Bot2": 2,
        "Bot3": 2
    }
    
    # Force transition to Turn phase
    await room.game_state_machine._immediate_transition_to(
        GamePhase.TURN, 
        "Direct transition for turn play testing"
    )
    
    # Wait for transition to complete
    await asyncio.sleep(0.5)
    
    # Check if we're in Turn phase
    current_phase = room.game_state_machine.current_phase
    print(f"📍 Current phase: {current_phase}")
    
    if current_phase.value != "turn":
        print(f"❌ Expected Turn phase, got {current_phase}")
        return False
    
    print("✅ Successfully in Turn phase!")
    
    # Test turn play functionality
    print("🎮 Testing turn play functionality...")
    
    # Get current turn data
    phase_data = room.game_state_machine.get_phase_data()
    current_player = phase_data.get('current_player')
    
    print(f"🎯 Current player: {current_player}")
    
    if not current_player:
        print("❌ No current player found in turn phase")
        return False
    
    # Get the player's hand
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
    
    # Create play action with correct structure
    play_action = GameAction(
        action_type=ActionType.PLAY_PIECES,
        player_name=current_player,
        payload={
            "pieces": [piece_to_play],
            "play_type": "single",
            "play_value": getattr(piece_to_play, 'point', 0),
            "is_valid": True
        }
    )
    
    # Test the play action using legacy method since TurnState not converted to event-driven yet
    try:
        print(f"🔧 Submitting play action via legacy method...")
        
        # Get the current state (should be TurnState)
        current_state = room.game_state_machine.current_state
        print(f"🔧 Current state: {type(current_state).__name__}")
        
        # Use the state's handle_action method directly
        result = await current_state.handle_action(play_action)
        print(f"🔧 Play result: {result}")
        
        if result:
            print("✅ Turn play action processed successfully")
            
            # Check if turn state was updated
            await asyncio.sleep(0.1)
            updated_phase_data = room.game_state_machine.get_phase_data()
            turn_plays = updated_phase_data.get('turn_plays', {})
            next_player = updated_phase_data.get('current_player')
            required_count = updated_phase_data.get('required_piece_count')
            
            print(f"📊 Turn plays recorded: {turn_plays}")
            print(f"🎯 Next player: {next_player}")
            print(f"🎯 Required piece count: {required_count}")
            
            if current_player in turn_plays:
                print("✅ Turn play recorded successfully")
                print(f"✅ Required piece count set to: {required_count}")
                print(f"✅ Next player set to: {next_player}")
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
    print("🎮 Simple Turn Play Test")
    print("=" * 40)
    
    try:
        success = await test_turn_play_direct()
        
        if success:
            print("\n🎉 Turn play test PASSED!")
        else:
            print("\n❌ Turn play test FAILED!")
            
        return success
        
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)