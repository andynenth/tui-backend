#!/usr/bin/env python3
"""
Test bot manager registration timing fix for declarations
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from engine.state_machine.core import GameAction, ActionType, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine
from engine.game import Game
from engine.player import Player
from engine.bot_manager import BotManager

async def test_bot_declaration_timing_fix():
    """Test that bot manager is properly registered before auto-transitions"""
    print("🧪 Testing Bot Manager Registration Timing Fix")
    print("=" * 55)
    
    # Create players with bots
    players = [
        Player("Andy", is_bot=False),
        Player("Bot 2", is_bot=True),
        Player("Bot 3", is_bot=True), 
        Player("Bot 4", is_bot=True)
    ]
    
    game = Game(players)
    room_id = "bot_timing_test"
    
    # Create state machine
    state_machine = GameStateMachine(game)
    state_machine.room_id = room_id
    
    print(f"🎯 Testing proper registration order...")
    print(f"   1. Create state machine ✅")
    print(f"   2. Register bot manager BEFORE start ✅")
    print(f"   3. Start state machine (will auto-transition)")
    
    # 🚀 APPLY THE FIX: Register bot manager BEFORE starting state machine
    bot_manager = BotManager()
    bot_manager.register_game(room_id, game, state_machine)
    
    print(f"✅ Bot manager registered for room {room_id}")
    print(f"   Active games: {list(bot_manager.active_games.keys())}")
    
    # Now start state machine - bot manager should be ready
    await state_machine.start(GamePhase.PREPARATION)
    
    # Wait for auto-transition and bot processing
    await asyncio.sleep(2.0)
    
    current_phase = state_machine.current_phase
    print(f"\n🎯 Current phase: {current_phase}")
    
    if current_phase == GamePhase.DECLARATION:
        print(f"✅ Auto-transition to DECLARATION worked!")
        
        # Check if bot manager received notifications
        print(f"\n🤖 Bot manager status:")
        print(f"   Active games: {list(bot_manager.active_games.keys())}")
        
        if room_id in bot_manager.active_games:
            print(f"✅ Room {room_id} found in bot manager!")
            
            # Get current state info
            decl_state = state_machine.current_state
            current_declarer = decl_state.phase_data.get('current_declarer')
            
            print(f"\n📊 Declaration state:")
            print(f"   Current declarer: {current_declarer}")
            print(f"   Declaration order: {decl_state.phase_data.get('declaration_order', [])}")
            
            # Check if current declarer is a bot
            current_player = game.get_player(current_declarer)
            if current_player.is_bot:
                print(f"🤖 Current declarer is a bot: {current_declarer}")
                print(f"   Bot manager should trigger declaration automatically...")
                
                # Wait a bit more for bot action
                await asyncio.sleep(3.0)
                
                # Check if declaration was made
                declarations = decl_state.phase_data.get('declarations', {})
                if current_declarer in declarations:
                    declaration_value = declarations[current_declarer]
                    print(f"✅ SUCCESS! Bot {current_declarer} made declaration: {declaration_value}")
                    return True
                else:
                    print(f"❌ Bot {current_declarer} did not make declaration yet")
                    print(f"   Current declarations: {declarations}")
                    return False
            else:
                print(f"ℹ️ Current declarer {current_declarer} is human - skipping bot test")
                return True
        else:
            print(f"❌ Room {room_id} NOT found in bot manager!")
            print(f"   This indicates the timing fix didn't work")
            return False
    else:
        print(f"❌ Not in DECLARATION phase: {current_phase}")
        return False

async def main():
    """Run bot declaration timing test"""
    try:
        success = await test_bot_declaration_timing_fix()
        
        if success:
            print(f"\n🎉 BOT DECLARATION TIMING FIX SUCCESSFUL!")
            print(f"\n💡 What was fixed:")
            print(f"   ❌ BEFORE: Bot manager registered AFTER state machine start")
            print(f"   ❌ BEFORE: Auto-transitions happened before bot registration")
            print(f"   ❌ BEFORE: Bot manager couldn't handle declaration events")
            print(f"   ✅ AFTER: Bot manager registered BEFORE state machine start")
            print(f"   ✅ AFTER: Bot manager ready when auto-transitions occur")
            print(f"   ✅ AFTER: Bots can handle declaration events immediately")
            
        else:
            print(f"\n❌ Bot declaration timing fix needs more work")
            print(f"   Check if bot manager is properly receiving events")
            
    except Exception as e:
        print(f"💥 Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())