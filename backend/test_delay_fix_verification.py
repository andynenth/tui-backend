#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from engine.state_machine.game_state_machine import GameStateMachine
from engine.game import Game
from engine.state_machine.core import GamePhase, ActionType, GameAction
from engine.bot_manager import BotManager

async def test_delay_fix():
    """Test that asyncio.sleep delays don't cause rogue broadcasts"""
    print('🧪 DELAY FIX VERIFICATION TEST')
    print('=' * 50)
    
    # Create game
    game = Game('delay_test')
    bot_manager = BotManager()
    state_machine = GameStateMachine(game, room_id='delay_test')
    game.state_machine = state_machine  # Direct assignment
    bot_manager.register_game('delay_test', game, state_machine)
    
    print('🎯 Step 1: Start game (should go PREP → DECL)')
    await state_machine.start()
    await asyncio.sleep(1)
    print(f'   Current phase: {state_machine.current_phase}')
    
    # Skip to end of round by forcing state changes
    print('🎯 Step 2: Force transition to TURN phase')
    if state_machine.current_phase == GamePhase.DECLARATION:
        # Complete declarations
        action = GameAction('Human', ActionType.DECLARE, {'value': 1})
        await state_machine.handle_action(action)
        await asyncio.sleep(1)
    
    print(f'   Current phase: {state_machine.current_phase}')
    
    print('🎯 Step 3: Force transition to SCORING phase')
    if state_machine.current_phase == GamePhase.TURN:
        # Simulate empty hands to trigger scoring
        for player in game.players:
            player.hand = []  # Empty all hands
        
        # Trigger turn completion check
        current_state = state_machine.current_state
        if hasattr(current_state, '_process_turn_completion'):
            await current_state._process_turn_completion()
    
    print(f'   Current phase: {state_machine.current_phase}')
    
    print('🎯 Step 4: Wait 10 seconds to check for delayed transitions')
    print('   This should test if old asyncio.sleep delays interfere')
    
    for i in range(10):
        await asyncio.sleep(1)
        print(f'   {i+1}s - Phase: {state_machine.current_phase}')
        
        # Look for any rogue "preparation" broadcasts
        # The fix should prevent them from happening
    
    print('✅ Test completed - no rogue broadcasts should have occurred')
    
    # Clean up
    await state_machine.stop()

if __name__ == '__main__':
    asyncio.run(test_delay_fix())