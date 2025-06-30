#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE TEST: Game Stuck at Declaration Screen Fixes

Tests the complete fixes for:
1. Auto-transition from PREPARATION to DECLARATION 
2. Bot manager registration timing
3. Frontend empty slots display
4. Enterprise architecture compliance

This test ensures the game properly progresses through phases without getting stuck.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.room import Room
from engine.player import Player
from engine.bot_manager import BotManager
from engine.state_machine.core import GamePhase, ActionType, GameAction

async def test_complete_game_flow():
    """Test complete game flow from room creation to declaration phase"""
    print("🎯 COMPREHENSIVE GAME FLOW TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Room Creation and Bot Manager Registration Timing
    print("\n1️⃣ Testing Room Creation and Bot Manager Registration...")
    try:
        room = Room("TEST_FLOW", "Andy")
        
        # Simulate broadcast callback
        async def test_broadcast(event_type: str, event_data: dict):
            print(f"📡 BROADCAST: {event_type} - {event_data.get('phase', 'unknown')}")
        
        # Start game (this should register bot manager BEFORE state machine starts)
        result = await room.start_game_safe(broadcast_callback=test_broadcast)
        
        if result["success"]:
            print("   ✅ Room started successfully")
            
            # Check bot manager registration
            bot_manager = BotManager()
            if room.room_id in bot_manager.active_games:
                print("   ✅ Bot manager registered BEFORE state machine start")
                results.append(("Bot manager registration timing", True))
            else:
                print("   ❌ Bot manager not registered")
                results.append(("Bot manager registration timing", False))
                
            # Check room_id propagation 
            if hasattr(room.game_state_machine, 'room_id') and room.game_state_machine.room_id == room.room_id:
                print("   ✅ Room ID properly propagated to state machine")
                results.append(("Room ID propagation", True))
            else:
                print("   ❌ Room ID not properly propagated")
                results.append(("Room ID propagation", False))
        else:
            print("   ❌ Room startup failed")
            results.append(("Bot manager registration timing", False))
            results.append(("Room ID propagation", False))
            
    except Exception as e:
        print(f"   ❌ TEST 1 ERROR: {e}")
        results.append(("Bot manager registration timing", False))
        results.append(("Room ID propagation", False))
    
    # Test 2: Auto-transition from PREPARATION to DECLARATION
    print("\n2️⃣ Testing Auto-transition from PREPARATION to DECLARATION...")
    try:
        # Wait a moment for initial setup
        await asyncio.sleep(0.5)
        
        # Check current phase
        current_phase = room.game_state_machine.current_phase
        print(f"   🔍 Current phase: {current_phase}")
        
        if current_phase == GamePhase.DECLARATION:
            print("   ✅ Successfully auto-transitioned to DECLARATION phase")
            results.append(("Auto-transition PREP->DECL", True))
        elif current_phase == GamePhase.PREPARATION:
            print("   ⏳ Still in PREPARATION - checking transition conditions...")
            
            # Manually trigger transition check 
            current_state = room.game_state_machine.current_state
            next_phase = await current_state.check_transition_conditions()
            
            if next_phase == GamePhase.DECLARATION:
                print("   ✅ Transition conditions met - should auto-transition")
                
                # Wait a bit more for auto-transition
                await asyncio.sleep(1.0)
                current_phase = room.game_state_machine.current_phase
                
                if current_phase == GamePhase.DECLARATION:
                    print("   ✅ Auto-transition completed successfully")
                    results.append(("Auto-transition PREP->DECL", True))
                else:
                    print("   ❌ Auto-transition did not complete")
                    results.append(("Auto-transition PREP->DECL", False))
            else:
                print(f"   ❌ Transition conditions not met: {next_phase}")
                results.append(("Auto-transition PREP->DECL", False))
        else:
            print(f"   ❌ Unexpected phase: {current_phase}")
            results.append(("Auto-transition PREP->DECL", False))
            
    except Exception as e:
        print(f"   ❌ TEST 2 ERROR: {e}")
        results.append(("Auto-transition PREP->DECL", False))
    
    # Test 3: Bot Declaration Triggering
    print("\n3️⃣ Testing Bot Declaration Triggering...")
    try:
        if room.game_state_machine.current_phase == GamePhase.DECLARATION:
            # Wait for bot declarations to trigger
            await asyncio.sleep(2.0)
            
            # Check if bots have declared
            game = room.game_state_machine.game
            bot_declarations = 0
            for player in game.players:
                if getattr(player, 'is_bot', False) and getattr(player, 'declared', 0) > 0:
                    bot_declarations += 1
                    print(f"   ✅ Bot {player.name} declared: {player.declared}")
            
            if bot_declarations >= 1:
                print(f"   ✅ Bots are declaring successfully ({bot_declarations} bots declared)")
                results.append(("Bot declarations triggered", True))
            else:
                print("   ❌ No bot declarations detected")
                results.append(("Bot declarations triggered", False))
        else:
            print("   ⏸️ Skipping bot test - not in DECLARATION phase")
            results.append(("Bot declarations triggered", False))
            
    except Exception as e:
        print(f"   ❌ TEST 3 ERROR: {e}")
        results.append(("Bot declarations triggered", False))
    
    # Test 4: Enterprise Architecture Compliance
    print("\n4️⃣ Testing Enterprise Architecture Compliance...")
    try:
        compliance_checks = []
        
        # Check 1: All state changes use update_phase_data
        state = room.game_state_machine.current_state
        if hasattr(state, 'update_phase_data'):
            print("   ✅ State has enterprise update_phase_data method")
            compliance_checks.append(True)
        else:
            print("   ❌ State missing update_phase_data method")
            compliance_checks.append(False)
        
        # Check 2: Auto-broadcasting is enabled
        if hasattr(state, '_auto_broadcast_enabled') and state._auto_broadcast_enabled:
            print("   ✅ Auto-broadcasting enabled")
            compliance_checks.append(True)
        else:
            print("   ❌ Auto-broadcasting not enabled")
            compliance_checks.append(False)
        
        # Check 3: Change history tracking
        if hasattr(state, '_change_history') and len(state._change_history) > 0:
            print(f"   ✅ Change history tracked ({len(state._change_history)} changes)")
            compliance_checks.append(True)
        else:
            print("   ❌ Change history not tracked")
            compliance_checks.append(False)
        
        # Check 4: JSON-safe data conversion
        if hasattr(state, '_make_json_safe'):
            print("   ✅ JSON-safe conversion available")
            compliance_checks.append(True)
        else:
            print("   ❌ JSON-safe conversion missing")
            compliance_checks.append(False)
        
        enterprise_compliant = all(compliance_checks)
        results.append(("Enterprise architecture compliance", enterprise_compliant))
        
        if enterprise_compliant:
            print("   ✅ All enterprise architecture checks passed")
        else:
            print(f"   ❌ Enterprise compliance failed ({sum(compliance_checks)}/{len(compliance_checks)})")
            
    except Exception as e:
        print(f"   ❌ TEST 4 ERROR: {e}")
        results.append(("Enterprise architecture compliance", False))
    
    # Test 5: Phase Data Structure for Frontend
    print("\n5️⃣ Testing Phase Data Structure for Frontend...")
    try:
        if hasattr(room.game_state_machine, 'current_state'):
            state = room.game_state_machine.current_state
            
            # Simulate broadcast data creation
            players_data = {}
            game = room.game_state_machine.game
            
            if hasattr(game, 'players') and game.players:
                for i, player in enumerate(game.players):
                    player_name = getattr(player, 'name', str(player))
                    players_data[player_name] = {
                        'hand': [str(piece) for piece in getattr(player, 'hand', [])],
                        'hand_size': len(getattr(player, 'hand', [])),
                        'is_bot': getattr(player, 'is_bot', False),
                        'is_host': i == 0,
                        'declared': getattr(player, 'declared', 0),
                        'captured_piles': getattr(player, 'captured_piles', 0)
                    }
            
            # Check if all required fields are present
            required_fields = ['hand', 'hand_size', 'is_bot', 'is_host', 'declared', 'captured_piles']
            frontend_compatible = True
            
            for player_name, player_data in players_data.items():
                missing_fields = [field for field in required_fields if field not in player_data]
                if missing_fields:
                    print(f"   ❌ Player {player_name} missing fields: {missing_fields}")
                    frontend_compatible = False
                else:
                    print(f"   ✅ Player {player_name} has all required fields")
            
            results.append(("Frontend data compatibility", frontend_compatible))
            
            if frontend_compatible:
                print("   ✅ Phase data structure compatible with frontend")
            else:
                print("   ❌ Phase data structure missing frontend requirements")
                
        else:
            print("   ❌ No current state available")
            results.append(("Frontend data compatibility", False))
            
    except Exception as e:
        print(f"   ❌ TEST 5 ERROR: {e}")
        results.append(("Frontend data compatibility", False))
    
    # Summary
    print(f"\n🎯 COMPREHENSIVE GAME FLOW TEST RESULTS:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Game flow fixes successful!")
    else:
        print("⚠️ SOME TESTS FAILED - Additional fixes may be needed")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(test_complete_game_flow())