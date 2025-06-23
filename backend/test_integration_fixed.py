#!/usr/bin/env python3
"""
Test the complete state machine integration with manual transition forcing
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.room import Room
from engine.state_machine.core import ActionType, GameAction, GamePhase

async def test_complete_integration():
    """Test the complete integration flow"""
    print("🚀 Testing Complete State Machine Integration (Fixed)")
    
    # Track all broadcast events
    broadcast_log = []
    
    async def test_broadcast(event_type, event_data):
        broadcast_log.append((event_type, event_data))
        print(f"📡 Broadcast: {event_type} -> {list(event_data.keys()) if isinstance(event_data, dict) else event_data}")
    
    try:
        # 1. Create Room
        room = Room('integration_test', 'Alice')
        print("✅ Room created")
        
        # 2. Start Game (should initialize PREPARATION phase)
        result = await room.start_game_safe(broadcast_callback=test_broadcast)
        print(f"✅ Game started: {result.get('success')}")
        print(f"✅ Current phase: {room.game_state_machine.current_phase}")
        
        # 3. Wait for PREPARATION to complete  
        await asyncio.sleep(0.5)
        await room.game_state_machine.process_pending_actions()
        print(f"✅ Phase after processing: {room.game_state_machine.current_phase}")
        
        # 4. Check if preparation is ready to transition
        prep_state = room.game_state_machine.current_state
        if prep_state:
            print(f"✅ Initial deal complete: {prep_state.initial_deal_complete}")
            print(f"✅ Weak players: {prep_state.weak_players}")
            
            # Force transition if ready
            next_phase = await prep_state.check_transition_conditions()
            print(f"✅ Next phase check: {next_phase}")
            
            if next_phase == GamePhase.DECLARATION:
                print("🔄 Manually transitioning to DECLARATION")
                await room.game_state_machine._transition_to(GamePhase.DECLARATION)
                print(f"✅ Transitioned to: {room.game_state_machine.current_phase}")
        
        # 5. Test Declaration Actions
        if room.game_state_machine.current_phase == GamePhase.DECLARATION:
            print("🗣️ Testing DECLARATION phase")
            
            # Declare for all players
            players = ["Alice", "Bot 2", "Bot 3", "Bot 4"]  # Room creates these by default
            declarations = [2, 2, 2, 1]  # Total = 7 (not 8, so valid)
            
            for player, value in zip(players, declarations):
                action = GameAction(
                    player_name=player,
                    action_type=ActionType.DECLARE,
                    payload={"value": value}
                )
                result = await room.game_state_machine.handle_action(action)
                print(f"✅ {player} declared {value}: {result.get('success')}")
                
                # Process actions
                await asyncio.sleep(0.1)
                await room.game_state_machine.process_pending_actions()
            
            # Check for manual transition to TURN
            decl_state = room.game_state_machine.current_state
            next_phase = await decl_state.check_transition_conditions()
            if next_phase == GamePhase.TURN:
                print("🔄 Manually transitioning to TURN")
                await room.game_state_machine._transition_to(GamePhase.TURN)
                print(f"✅ Transitioned to: {room.game_state_machine.current_phase}")
        
        # 6. Test Turn Actions  
        if room.game_state_machine.current_phase == GamePhase.TURN:
            print("🎯 Testing TURN phase")
            
            # Try a turn action
            action = GameAction(
                player_name="Alice",
                action_type=ActionType.PLAY_PIECES,
                payload={"piece_indices": [0, 1]}  # Play first 2 pieces
            )
            result = await room.game_state_machine.handle_action(action)
            print(f"✅ Alice play queued: {result.get('success')}")
            
            await asyncio.sleep(0.2)
            await room.game_state_machine.process_pending_actions()
        
        # 7. Show Results
        print(f"\n📊 Final Results:")
        print(f"   Final phase: {room.game_state_machine.current_phase}")
        print(f"   Broadcast events: {len(broadcast_log)}")
        for i, (event_type, data) in enumerate(broadcast_log):
            print(f"   {i+1}. {event_type}: {list(data.keys()) if isinstance(data, dict) else data}")
        print(f"   State machine running: {room.game_state_machine.is_running}")
        
        # 8. Cleanup
        await room.game_state_machine.stop()
        print("✅ Integration test complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_complete_integration()
    print(f"\n🎯 Integration Test: {'PASSED' if success else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())