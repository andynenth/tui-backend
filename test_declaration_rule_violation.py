#!/usr/bin/env python3
"""
Test case to demonstrate and verify the declaration phase rule violation bug.

This test proves that bots can illegally declare values that make the total equal to 8
when they are the last player to declare, which violates the game rules.

The test will:
1. Initially FAIL (demonstrating the bug exists)
2. PASS after the fixes are implemented
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.bot_manager import BotManager
from backend.engine.state_machine.game_state_machine import GameStateMachine
from backend.engine.state_machine.core import GamePhase, ActionType, GameAction


class TestDeclarationRuleViolation:
    """Test case for declaration rule violation by bots"""
    
    def __init__(self):
        self.test_results = {
            "bot_violation_detected": False,
            "bot_declared_value": None,
            "total_declarations": None,
            "validation_working": False,
            "bot_logic_correct": False,
            "error_messages": []
        }
        
    async def setup_test_game(self) -> tuple:
        """Set up a game with specific conditions to test the rule violation"""
        # Create players - 3 humans and 1 bot
        players = [
            Player("Human1", is_bot=False),
            Player("Human2", is_bot=False),
            Player("Human3", is_bot=False),
            Player("Bot1", is_bot=True)
        ]
        
        # Create game
        game = Game(players)
        game.round_number = 2  # Not first round to avoid GENERAL_RED logic
        
        # Create state machine
        state_machine = GameStateMachine(game)
        
        # Set room_id using property setter (initializes ActionQueue)
        state_machine.room_id = "test_room"
        
        # Register with bot manager
        bot_manager = BotManager()
        bot_manager.register_game("test_room", game, state_machine)
        
        # Start the game and move to declaration phase
        await state_machine.start()
        
        # Manually transition to declaration phase for testing
        state_machine.current_phase = GamePhase.DECLARATION
        state_machine.current_state = state_machine.states[GamePhase.DECLARATION]
        await state_machine.current_state._setup_phase()
        
        return game, state_machine, bot_manager
        
    async def test_bot_violation(self):
        """Test that demonstrates bot can violate the rule"""
        print("=" * 80)
        print("TEST: Declaration Rule Violation by Bots")
        print("=" * 80)
        
        # Setup
        game, state_machine, bot_manager = await self.setup_test_game()
        
        # Set up a scenario where humans declare values that sum to 6
        # This means the bot (last player) cannot declare 2 (as 6 + 2 = 8)
        human_declarations = [
            ("Human1", 2),
            ("Human2", 1),
            ("Human3", 3)  # Total so far: 6
        ]
        
        print(f"\n📋 Test Scenario:")
        print(f"   - 3 humans declare first, 1 bot declares last")
        print(f"   - Human declarations will sum to 6")
        print(f"   - Bot must NOT declare 2 (since 6 + 2 = 8)")
        
        # Have humans declare
        for player_name, value in human_declarations:
            action = GameAction(
                player_name=player_name,
                action_type=ActionType.DECLARE,
                payload={"value": value},
                timestamp=datetime.now(),
                sequence_id=0
            )
            
            # Process declaration
            await state_machine.current_state._process_action(action)
            print(f"   ✓ {player_name} declared {value}")
            
            # Update player's declared value to simulate current round
            for p in game.players:
                if p.name == player_name:
                    p.declared = value
        
        current_total = sum(v for _, v in human_declarations)
        print(f"\n📊 Current total: {current_total}")
        print(f"   Bot CANNOT declare: {8 - current_total} (would make total = 8)")
        
        # Now trigger bot decision
        print(f"\n🤖 Triggering bot decision...")
        
        # Get current phase data
        phase_data = state_machine.current_state.phase_data
        
        # Manually trigger bot manager event (simulating what happens in real game)
        await bot_manager.handle_game_event("test_room", "phase_change", {
            "phase": "DECLARATION",
            "phase_data": phase_data
        })
        
        # Give bot time to make decision
        await asyncio.sleep(1.0)
        
        # Check what the bot declared
        bot_player = game.players[3]  # Bot1 is the 4th player
        bot_declared = phase_data.get("declarations", {}).get("Bot1", 0)
        
        print(f"\n🎯 Bot declared: {bot_declared}")
        
        # Calculate final total
        final_total = current_total + bot_declared
        print(f"📊 Final total: {final_total}")
        
        # Check if rule was violated
        if final_total == 8:
            print(f"\n❌ RULE VIOLATION DETECTED!")
            print(f"   Bot illegally declared {bot_declared}, making total = 8")
            self.test_results["bot_violation_detected"] = True
            self.test_results["bot_declared_value"] = bot_declared
            self.test_results["total_declarations"] = final_total
        else:
            print(f"\n✅ No violation - Bot correctly avoided making total = 8")
            self.test_results["bot_violation_detected"] = False
            
        # Test the validation function
        print(f"\n🔍 Testing validation function...")
        validation_result = await state_machine.current_state._check_declaration_restrictions(
            "Bot1", bot_declared
        )
        
        if validation_result and final_total == 8:
            print(f"❌ Validation function failed - returned True for illegal declaration")
            self.test_results["validation_working"] = False
        else:
            print(f"✅ Validation function working correctly")
            self.test_results["validation_working"] = True
            
        # Clean up
        bot_manager.unregister_game("test_room")
        
        return self.test_results
        
    def print_test_summary(self, results: Dict):
        """Print a summary of test results"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        if results["bot_violation_detected"]:
            print(f"❌ BUG CONFIRMED: Bot violated the declaration rule")
            print(f"   - Bot declared: {results['bot_declared_value']}")
            print(f"   - Total became: {results['total_declarations']} (illegal)")
            print(f"\n📝 Root Causes:")
            print(f"   1. _check_declaration_restrictions() always returns True")
            print(f"   2. Bot uses wrong data source (p.declared from previous round)")
            print(f"\n🔧 Required Fixes:")
            print(f"   1. Implement proper validation in _check_declaration_restrictions()")
            print(f"   2. Fix bot to use phase_data['declarations'] instead of p.declared")
        else:
            print(f"✅ TEST PASSED: Bot correctly followed the declaration rule")
            print(f"   - Validation working: {results['validation_working']}")
            
        if results["error_messages"]:
            print(f"\n⚠️  Errors encountered:")
            for error in results["error_messages"]:
                print(f"   - {error}")


async def main():
    """Run the test"""
    tester = TestDeclarationRuleViolation()
    
    try:
        results = await tester.test_bot_violation()
        tester.print_test_summary(results)
        
        # Exit with appropriate code
        if results["bot_violation_detected"]:
            print("\n🚨 Test demonstrates the bug exists (expected before fix)")
            sys.exit(1)  # Fail - bug exists
        else:
            print("\n✅ Test passes - bug has been fixed!")
            sys.exit(0)  # Success - bug fixed
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)  # Error during test


if __name__ == "__main__":
    asyncio.run(main())