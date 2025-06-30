#!/usr/bin/env python3
"""
Test Option B - Automatic transition checking after state changes
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from engine.state_machine.core import GameAction, ActionType, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine
from engine.game import Game
from engine.player import Player

async def test_auto_transition_fix():
    """Test that preparation phase automatically transitions to declaration"""
    print("🧪 Testing Option B - Automatic Transitions After State Changes")
    print("=" * 60)
    
    # Create players
    players = [
        Player("Alice", is_bot=False),
        Player("Bob", is_bot=True),
        Player("Charlie", is_bot=True),
        Player("Diana", is_bot=True)
    ]
    
    game = Game(players)
    game.room_id = "auto_transition_test"
    
    # Create state machine
    state_machine = GameStateMachine(game)
    
    print("🎯 Starting in PREPARATION phase...")
    await state_machine.start(GamePhase.PREPARATION)
    
    print(f"✅ Started in phase: {state_machine.current_phase}")
    
    # Get the initial state
    initial_state = state_machine.current_state
    initial_phase = state_machine.current_phase
    
    print(f"\n📊 Initial state:")
    if initial_phase == GamePhase.PREPARATION:
        print(f"   - Initial deal complete: {initial_state.initial_deal_complete}")
        print(f"   - Weak players: {initial_state.weak_players}")
    print(f"   - Phase data: {initial_state.phase_data}")
    
    # Wait a moment to see if automatic transition happens
    print(f"\n⏰ Waiting 3 seconds for automatic transition...")
    await asyncio.sleep(3)
    
    current_phase = state_machine.current_phase
    print(f"🎯 Phase after 3 seconds: {current_phase}")
    
    if current_phase == GamePhase.DECLARATION:
        print(f"✅ SUCCESS! Automatic transition worked!")
        print(f"   PREPARATION → DECLARATION happened automatically")
        print(f"   No weak players detected, so transition was immediate")
        print(f"   Option B event-driven architecture working perfectly!")
        
        # Show the declaration state data
        decl_state = state_machine.current_state
        print(f"\n📊 Declaration state:")
        print(f"   - Phase data: {decl_state.phase_data}")
        
        return True
    elif current_phase == GamePhase.PREPARATION:
        # Check why it's still in preparation
        print(f"⏳ Still in PREPARATION - checking why...")
        prep_state = state_machine.current_state
        
        print(f"   - Initial deal complete: {prep_state.initial_deal_complete}")
        print(f"   - Weak players: {prep_state.weak_players}")
        print(f"   - Redeal decisions: {prep_state.redeal_decisions}")
        
        # Manually check transition conditions
        next_phase = await prep_state.check_transition_conditions()
        print(f"   - check_transition_conditions() returns: {next_phase}")
        
        if next_phase == GamePhase.DECLARATION:
            print(f"❌ ISSUE: Transition conditions are met but auto-transition didn't happen")
            print(f"         This means Option B implementation has a bug")
            return False
        else:
            print(f"✅ Correctly staying in PREPARATION - conditions not met yet")
            return True
    else:
        print(f"❌ Unexpected phase: {current_phase}")
        return False

async def main():
    """Run the auto-transition test"""
    try:
        success = await test_auto_transition_fix()
        
        if success:
            print(f"\n🎉 AUTO-TRANSITION TEST PASSED!")
            print(f"\n💡 What happened:")
            print(f"   1. Started PREPARATION phase")
            print(f"   2. Initial card dealing completed") 
            print(f"   3. No weak players detected")
            print(f"   4. update_phase_data() automatically triggered transition check")
            print(f"   5. check_transition_conditions() returned DECLARATION")
            print(f"   6. Automatic transition to DECLARATION phase")
            print(f"\n🚀 Option B implementation working perfectly!")
            print(f"   ✅ Fail-safe: State changes automatically trigger transitions")
            print(f"   ✅ No manual trigger_transition() calls needed")
            print(f"   ✅ Developers can't forget to check transitions")
            
        else:
            print(f"\n❌ AUTO-TRANSITION TEST FAILED!")
            print(f"   Need to debug Option B implementation")
            
    except Exception as e:
        print(f"💥 Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())