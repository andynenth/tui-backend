#!/usr/bin/env python3
"""
Integration test to verify the declaration rule fixes work correctly.

This test uses the actual game state machine and bot handler to ensure
the fixes prevent bots from violating the declaration rule.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.state_machine.game_state_machine import GameStateMachine
from backend.engine.bot_manager import GameBotHandler
from backend.engine.state_machine.core import GameAction, ActionType


class DeclarationFixIntegrationTest:
    """Integration test for declaration rule fixes"""
    
    def __init__(self):
        self.room_id = "test_room"
        self.violation_detected = False
        self.validation_worked = False
        
    async def setup_game(self) -> tuple[Game, GameStateMachine, GameBotHandler]:
        """Set up a game with state machine and bot handler"""
        # Create players
        players = [
            Player("Human1", is_bot=False),
            Player("Human2", is_bot=False),
            Player("Human3", is_bot=False),
            Player("Bot1", is_bot=True)
        ]
        
        # Create game
        game = Game(players)
        game.round_number = 2
        
        # Give everyone cards
        deck = Piece.build_deck()
        for i, player in enumerate(players):
            player.hand = deck[i*8:(i+1)*8]
            
        # Set previous round declarations
        players[0].declared = 1
        players[1].declared = 2  
        players[2].declared = 2
        players[3].declared = 3
        
        # Create state machine and set room_id
        state_machine = GameStateMachine(game)
        state_machine.room_id = self.room_id
        
        # Create bot handler
        bot_handler = GameBotHandler(self.room_id, game)
        bot_handler.state_machine = state_machine
        
        return game, state_machine, bot_handler
        
    async def test_declaration_phase(self):
        """Test the declaration phase with fixes"""
        print("=" * 80)
        print("INTEGRATION TEST: Declaration Rule Fixes")
        print("=" * 80)
        
        # Setup
        game, state_machine, bot_handler = await self.setup_game()
        
        print(f"\n📋 Test Setup:")
        print(f"   - Round {game.round_number}")
        print(f"   - Players: 3 humans + 1 bot (last to declare)")
        
        # Previous round data
        print(f"\n📜 Previous Round Declarations (in p.declared):")
        for p in game.players:
            print(f"   - {p.name}: {p.declared}")
        prev_total = sum(p.declared for p in game.players if p.declared != 0)
        print(f"   Total: {prev_total}")
        
        # Start declaration phase
        print(f"\n🎯 Starting Declaration Phase...")
        
        # Initialize game properly by transitioning through phases
        from backend.engine.state_machine.core import GamePhase
        
        # Start the state machine
        await state_machine.start(GamePhase.PREPARATION)
        
        # Let preparation phase initialize
        if state_machine.current_state and state_machine.current_state.phase == GamePhase.PREPARATION:
            # The preparation state should handle dealing cards automatically
            # Just wait a bit for it to process
            await asyncio.sleep(0.1)
            
        # Transition to declaration phase
        await state_machine.transition_to_phase(GamePhase.DECLARATION)
        
        # Simulate human declarations
        current_declarations = {
            "Human1": 3,
            "Human2": 2, 
            "Human3": 1
        }
        
        print(f"\n📣 Human Declarations:")
        for player_name, value in current_declarations.items():
            # Create declare action
            action = GameAction(
                type=ActionType.DECLARE,
                player=player_name,
                payload={"value": value}
            )
            
            # Process action
            result = await state_machine.process_action(action)
            
            if result["success"]:
                print(f"   - {player_name} declared: {value} ✓")
            else:
                print(f"   - {player_name} failed to declare: {result.get('error')}")
                
        # Get current state
        current_total = state_machine.current_state.phase_data["declaration_total"]
        print(f"\n   Current total: {current_total}")
        print(f"   Bot CANNOT declare: {8 - current_total} (would make total = 8)")
        
        # Now let bot declare
        print(f"\n🤖 Bot's Turn to Declare...")
        
        # Bot should use the fixed logic
        bot_action = await bot_handler.handle_declaration_phase(state_machine.current_state.phase_data)
        
        if bot_action:
            bot_value = bot_action.payload["value"]
            print(f"   Bot wants to declare: {bot_value}")
            
            # Process bot's declaration
            result = await state_machine.process_action(bot_action)
            
            if result["success"]:
                print(f"   ✅ Bot successfully declared: {bot_value}")
                final_total = current_total + bot_value
                print(f"   Final total: {final_total}")
                
                if final_total == 8:
                    print(f"   ❌ ERROR: Bot violated the rule! Total = 8")
                    self.violation_detected = True
                else:
                    print(f"   ✅ Rule enforced correctly! Total ≠ 8")
                    
            else:
                print(f"   ❌ Bot's declaration rejected: {result.get('error')}")
                if bot_value == 8 - current_total:
                    print(f"   ✅ Validation worked! Bot tried to make total = 8 but was blocked")
                    self.validation_worked = True
                    
        else:
            print(f"   ❌ Bot failed to generate a declaration")
            
        return not self.violation_detected
        
    async def run_test(self):
        """Run the complete integration test"""
        try:
            success = await self.test_declaration_phase()
            
            print(f"\n" + "=" * 80)
            print("TEST RESULTS")
            print("=" * 80)
            
            if success and not self.violation_detected:
                print(f"\n✅ TEST PASSED!")
                print(f"   - Bot correctly avoided making total = 8")
                print(f"   - Declaration rule is properly enforced")
                return 0
            else:
                print(f"\n❌ TEST FAILED!")
                print(f"   - Bot violated the declaration rule")
                return 1
                
        except Exception as e:
            print(f"\n❌ TEST ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 2


async def main():
    """Run the integration test"""
    tester = DeclarationFixIntegrationTest()
    return await tester.run_test()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)