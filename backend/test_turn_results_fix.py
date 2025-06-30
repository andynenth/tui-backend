#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from engine.state_machine.game_state_machine import GameStateMachine
from engine.game import Game
from engine.state_machine.core import GamePhase, ActionType, GameAction

async def test_turn_results_auto_advance():
    """Test TURN_RESULTS auto-advance timer"""
    print('🧪 TURN_RESULTS AUTO-ADVANCE TEST')
    print('=' * 50)
    
    # Create game with proper setup
    game = Game('test_timeout')
    state_machine = GameStateMachine(game, room_id='test_timeout')
    game.state_machine = state_machine
    
    print('🎯 Step 1: Start state machine and reach TURN phase')
    await state_machine.start()
    await asyncio.sleep(0.5)
    
    # Skip to TURN_RESULTS by manually transitioning
    print('🎯 Step 2: Manually transition to TURN_RESULTS')
    await state_machine.trigger_transition(GamePhase.TURN_RESULTS, "Manual test transition")
    await asyncio.sleep(0.5)
    
    current_phase = state_machine.current_phase
    print(f'   ✅ Current phase: {current_phase}')
    
    if current_phase == GamePhase.TURN_RESULTS:
        print('🎯 Step 3: Waiting for auto-advance timer (7 seconds)...')
        print('   ⏰ Should see auto-advance timer logs...')
        
        # Wait for the auto-advance (7 seconds + buffer)
        start_time = asyncio.get_event_loop().time()
        timeout = 10  # 7 second timer + 3 second buffer
        
        while True:
            await asyncio.sleep(0.5)
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - start_time
            
            print(f'   ⏰ Elapsed: {elapsed:.1f}s, Phase: {state_machine.current_phase}')
            
            if state_machine.current_phase != GamePhase.TURN_RESULTS:
                print(f'   ✅ Transitioned from TURN_RESULTS to {state_machine.current_phase}!')
                break
                
            if elapsed > timeout:
                print(f'   ❌ Timeout! Still in {state_machine.current_phase} after {timeout}s')
                break
    
    # Clean up
    await state_machine.stop()
    
    print('\n🎉 TURN_RESULTS AUTO-ADVANCE TEST RESULTS:')
    print(f'   📋 Final phase: {state_machine.current_phase}')
    if state_machine.current_phase != GamePhase.TURN_RESULTS:
        print('   ✅ Auto-advance timer working!')
    else:
        print('   ❌ Auto-advance timer failed!')

if __name__ == '__main__':
    asyncio.run(test_turn_results_auto_advance())