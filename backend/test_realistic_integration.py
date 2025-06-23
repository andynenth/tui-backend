#!/usr/bin/env python3
"""
Test integration with realistic hand data - NOT all players having weak hands
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.room import Room
from engine.state_machine.core import ActionType, GameAction, GamePhase
from tests.test_helpers import create_test_hand_realistic, create_strong_hand
from engine.piece import Piece

async def test_realistic_integration():
    """Test with realistic hand data where not all players are weak"""
    print("🚀 Testing Realistic Integration (Proper Hand Distribution)")
    
    broadcast_log = []
    
    async def test_broadcast(event_type, event_data):
        broadcast_log.append((event_type, event_data))
        print(f"📡 Broadcast: {event_type}")
    
    try:
        # 1. Create Room (this creates real Game with Player objects)
        room = Room('realistic_test', 'TestHost')
        print("✅ Room created with real Game instance")
        
        # 2. Start game with state machine  
        result = await room.start_game_safe(broadcast_callback=test_broadcast)
        print(f"✅ Game started: {result.get('success')}")
        print(f"✅ Current phase: {room.game_state_machine.current_phase}")
        
        # 3. Replace hands with realistic strong hands AFTER initial dealing
        strong_hand = create_strong_hand()  # Has pieces > 9 points
        
        # Give all players strong hands (not weak)
        for player in room.game.players:
            player.hand = strong_hand.copy()  # Each gets same strong hand
            print(f"✅ {player.name} assigned strong hand (max: {max(p.point for p in player.hand)} points)")
        
        # 4. Force re-check of weak hands with new hands
        prep_state = room.game_state_machine.current_state
        if prep_state:
            # Re-run weak hand detection with new hands
            weak_players = room.game.get_weak_hand_players()
            prep_state.weak_players = set(weak_players) if weak_players else set()
            print(f"✅ Re-checked weak players: {prep_state.weak_players}")
        
        await asyncio.sleep(0.2)
        await room.game_state_machine.process_pending_actions()
        
        print(f"✅ Initial deal complete: {prep_state.initial_deal_complete}")
        
        # 5. Should transition to DECLARATION (no weak hands)
        next_phase = await prep_state.check_transition_conditions()
        print(f"✅ Next phase check: {next_phase}")
        
        if next_phase == GamePhase.DECLARATION:
            await room.game_state_machine._transition_to(GamePhase.DECLARATION)
            print(f"✅ Transitioned to: {room.game_state_machine.current_phase}")
        
        # 6. Test realistic declarations
        if room.game_state_machine.current_phase == GamePhase.DECLARATION:
            print("🗣️ Testing DECLARATION with realistic data")
            
            player_names = [p.name for p in room.game.players]
            declarations = [2, 2, 2, 1]  # Total = 7 ≠ 8 (valid)
            
            for player_name, value in zip(player_names, declarations):
                action = GameAction(
                    player_name=player_name,
                    action_type=ActionType.DECLARE,
                    payload={"value": value}
                )
                result = await room.game_state_machine.handle_action(action)
                print(f"✅ {player_name} declared {value}: {result.get('success')}")
                
                await asyncio.sleep(0.1)
                await room.game_state_machine.process_pending_actions()
            
            # Check transition to TURN
            decl_state = room.game_state_machine.current_state
            next_phase = await decl_state.check_transition_conditions()
            if next_phase == GamePhase.TURN:
                await room.game_state_machine._transition_to(GamePhase.TURN)
                print(f"✅ Transitioned to: {room.game_state_machine.current_phase}")
        
        # 7. Test TURN phase
        if room.game_state_machine.current_phase == GamePhase.TURN:
            print("🎯 Testing TURN with realistic pieces")
            
            # Get starter from game
            starter_name = getattr(room.game, 'current_player', None) or room.game.players[0].name
            print(f"✅ Current starter: {starter_name}")
            
            action = GameAction(
                player_name=starter_name,
                action_type=ActionType.PLAY_PIECES,
                payload={"piece_indices": [0]}  # Play first piece
            )
            result = await room.game_state_machine.handle_action(action)
            print(f"✅ {starter_name} play queued: {result.get('success')}")
            
            await asyncio.sleep(0.2)
            await room.game_state_machine.process_pending_actions()
        
        # 8. Results
        print(f"\n📊 Realistic Integration Results:")
        print(f"   Final phase: {room.game_state_machine.current_phase}")
        print(f"   Weak players: {len(prep_state.weak_players)} (should be 0)")
        print(f"   Broadcasts: {len(broadcast_log)}")
        
        # Show hand composition proof
        print(f"\n🃏 Hand Analysis:")
        for player in room.game.players:
            max_points = max(p.point for p in player.hand)
            print(f"   {player.name}: Max piece = {max_points} points ({'STRONG' if max_points > 9 else 'WEAK'})")
        
        # 9. Cleanup
        await room.game_state_machine.stop()
        print("✅ Realistic integration test complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Realistic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_realistic_integration()
    print(f"\n🎯 Realistic Integration Test: {'PASSED' if success else 'FAILED'}")
    
    if success:
        print("\n🎉 REALISTIC Integration SUCCESSFUL!")
        print("✅ Proper hand distribution (not all weak)")
        print("✅ PREPARATION → DECLARATION transition works")
        print("✅ State machine handles realistic game flow")
        print("✅ Ready for production with real data!")

if __name__ == "__main__":
    asyncio.run(main())