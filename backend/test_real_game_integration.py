#!/usr/bin/env python3
"""
Test state machine integration with actual Game class and proper dealing
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.room import Room
from engine.state_machine.core import ActionType, GameAction, GamePhase

async def test_real_game_integration():
    """Test with actual game flow"""
    print("🚀 Testing Real Game Integration")
    
    broadcast_log = []
    
    async def test_broadcast(event_type, event_data):
        broadcast_log.append((event_type, event_data))
        print(f"📡 Broadcast: {event_type}")
    
    try:
        # 1. Create Room and start game
        room = Room('real_test', 'Alice')
        result = await room.start_game_safe(broadcast_callback=test_broadcast)
        print(f"✅ Game started: {result.get('success')}")
        print(f"✅ Current phase: {room.game_state_machine.current_phase}")
        
        # 2. Check for weak hands (not all players will have weak hands in realistic scenarios)
        prep_state = room.game_state_machine.current_state
        
        if prep_state.weak_players:
            print(f"🔍 Found weak players: {prep_state.weak_players}")
            print(f"🔍 Current weak player being asked: {prep_state.current_weak_player}")
            
            # Decline redeal for each weak player
            for player in list(prep_state.weak_players):
                if prep_state.current_weak_player == player:
                    action = GameAction(
                        player_name=player,
                        action_type=ActionType.REDEAL_RESPONSE,
                        payload={"accept": False}
                    )
                    result = await room.game_state_machine.handle_action(action)
                    print(f"✅ {player} declined redeal: {result.get('success')}")
                    
                    await asyncio.sleep(0.1)
                    await room.game_state_machine.process_pending_actions()
                    
                    print(f"   Next weak player: {prep_state.current_weak_player}")
            
            # After all decline, should transition to DECLARATION
            await asyncio.sleep(0.2)
            await room.game_state_machine.process_pending_actions()
            
            next_phase = await prep_state.check_transition_conditions()
            if next_phase == GamePhase.DECLARATION:
                await room.game_state_machine._transition_to(GamePhase.DECLARATION)
                print(f"✅ Transitioned to: {room.game_state_machine.current_phase}")
        
        # 3. Test declarations if in DECLARATION phase
        if room.game_state_machine.current_phase == GamePhase.DECLARATION:
            print("🗣️ Testing DECLARATION phase")
            
            players = ["Alice", "Bot 2", "Bot 3", "Bot 4"]
            declarations = [2, 2, 2, 1]  # Total = 7 ≠ 8 (valid)
            
            for player, value in zip(players, declarations):
                action = GameAction(
                    player_name=player,
                    action_type=ActionType.DECLARE,
                    payload={"value": value}
                )
                result = await room.game_state_machine.handle_action(action)
                print(f"✅ {player} declared {value}: {result.get('success')}")
                
                await asyncio.sleep(0.1)
                await room.game_state_machine.process_pending_actions()
            
            # Check transition to TURN
            decl_state = room.game_state_machine.current_state
            next_phase = await decl_state.check_transition_conditions()
            if next_phase == GamePhase.TURN:
                await room.game_state_machine._transition_to(GamePhase.TURN)
                print(f"✅ Transitioned to: {room.game_state_machine.current_phase}")
        
        # 4. Show final results
        print(f"\n📊 Final Results:")
        print(f"   Final phase: {room.game_state_machine.current_phase}")
        print(f"   Broadcast events: {len(broadcast_log)}")
        for i, (event_type, data) in enumerate(broadcast_log[:5]):  # Show first 5
            print(f"   {i+1}. {event_type}")
        if len(broadcast_log) > 5:
            print(f"   ... and {len(broadcast_log) - 5} more events")
        
        # 5. Cleanup
        await room.game_state_machine.stop()
        print("✅ Real game integration test complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Real game test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_real_game_integration()
    print(f"\n🎯 Real Game Integration Test: {'PASSED' if success else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())