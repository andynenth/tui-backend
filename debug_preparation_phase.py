#!/usr/bin/env python3

"""
Debug PREPARATION phase transitions
"""

import asyncio
import sys
import os
sys.path.append('/Users/nrw/python/tui-project/liap-tui/backend')

from engine.game import Game
from engine.player import Player
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GamePhase


async def debug_preparation_phase():
    """Debug what happens in preparation phase"""
    print("🔍 PREPARATION PHASE DEBUG")
    print("=" * 50)
    
    # Create test game
    players = [
        Player("Player1", is_bot=False),
        Player("Bot2", is_bot=True), 
        Player("Bot3", is_bot=True),
        Player("Bot4", is_bot=True)
    ]
    
    game = Game(players)
    
    # Create state machine
    state_machine = GameStateMachine(game)
    state_machine.room_id = "test_room"
    
    print(f"📋 Initial game state:")
    print(f"   Round number: {getattr(game, 'round_number', 'NONE')}")
    print(f"   Players: {[p.name for p in players]}")
    print(f"   Current player: {getattr(game, 'current_player', 'NONE')}")
    
    # Start state machine
    print(f"\n🚀 Starting state machine in PREPARATION phase...")
    await state_machine.start(GamePhase.PREPARATION)
    
    print(f"✅ State machine started")
    print(f"   Current phase: {state_machine.current_phase}")
    print(f"   Is running: {state_machine.is_running}")
    
    # Check preparation state
    prep_state = state_machine.states[GamePhase.PREPARATION]
    print(f"\n🎴 Preparation state info:")
    print(f"   Initial deal complete: {prep_state.initial_deal_complete}")
    print(f"   Weak players: {prep_state.weak_players}")
    print(f"   Redeal decisions: {prep_state.redeal_decisions}")
    
    # Check game state after preparation
    print(f"\n🎯 Game state after preparation:")
    print(f"   Current player: {getattr(game, 'current_player', 'NONE')}")
    print(f"   Round starter: {getattr(game, 'round_starter', 'NONE')}")
    print(f"   Starter reason: {getattr(game, 'starter_reason', 'NONE')}")
    print(f"   Redeal multiplier: {getattr(game, 'redeal_multiplier', 'NONE')}")
    
    # Check what weak hands were detected
    if hasattr(game, 'get_weak_hand_players'):
        weak_players = game.get_weak_hand_players()
        print(f"   Weak hand players: {weak_players}")
    else:
        print(f"   No weak hand detection method")
    
    # Wait and check for transitions
    print(f"\n⏰ Waiting for phase transitions...")
    for i in range(10):
        await asyncio.sleep(1)
        current_phase = state_machine.current_phase
        print(f"   t+{i+1}s: Phase = {current_phase}")
        
        # Check transition conditions manually
        if current_phase == GamePhase.PREPARATION:
            next_phase = await prep_state.check_transition_conditions()
            print(f"        Next phase check: {next_phase}")
            
            # Check the actual conditions
            print(f"        Initial deal complete: {prep_state.initial_deal_complete}")
            print(f"        Weak players count: {len(prep_state.weak_players)}")
            print(f"        Decisions received: {len(prep_state.redeal_decisions)}")
        
        if current_phase != GamePhase.PREPARATION:
            print(f"   ✅ Phase changed to: {current_phase}")
            break
    else:
        print(f"   ❌ Phase stuck in: {state_machine.current_phase}")
    
    # Stop state machine
    await state_machine.stop()
    print(f"🛑 State machine stopped")


if __name__ == "__main__":
    asyncio.run(debug_preparation_phase())