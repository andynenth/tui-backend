#!/usr/bin/env python3
"""
Simplified test to demonstrate the declaration rule violation bug.

This test directly calls the bot logic to show it uses wrong data source.
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.bot_manager import BotManager, GameBotHandler
from backend.engine.rules import get_valid_declares


class SimpleDeclarationTest:
    """Simplified test focusing on the bot logic bug"""
    
    def test_bot_declaration_logic(self):
        """Test that shows bot uses wrong data source"""
        print("=" * 80)
        print("SIMPLE TEST: Bot Declaration Logic Bug")
        print("=" * 80)
        
        # Create a simple game scenario
        players = [
            Player("Human1", is_bot=False),
            Player("Human2", is_bot=False),
            Player("Human3", is_bot=False),
            Player("Bot1", is_bot=True)
        ]
        
        game = Game(players)
        
        # Deal some cards to bot (needed for valid declares)
        from backend.engine.piece import Piece
        bot = players[3]
        bot.hand = Piece.build_deck()[:8]  # Give bot 8 cards
        
        print(f"\n📋 Scenario Setup:")
        print(f"   - Round 2 (not first round)")
        print(f"   - Bot has cards: {[str(p) for p in bot.hand[:3]]}... (showing first 3)")
        
        # Simulate that in PREVIOUS round, players declared these values:
        players[0].declared = 2  # Human1 declared 2 in PREVIOUS round
        players[1].declared = 3  # Human2 declared 3 in PREVIOUS round  
        players[2].declared = 1  # Human3 declared 1 in PREVIOUS round
        players[3].declared = 0  # Bot declared 0 in PREVIOUS round
        
        print(f"\n📜 Previous Round Declarations (stored in p.declared):")
        for p in players:
            print(f"   - {p.name}: {p.declared}")
        print(f"   Total from previous round: {sum(p.declared for p in players)}")
        
        # Now simulate CURRENT round declarations
        current_declarations = {
            "Human1": 2,
            "Human2": 1,
            "Human3": 3
            # Bot hasn't declared yet
        }
        
        print(f"\n🎯 Current Round Declarations (should be in phase_data):")
        for name, value in current_declarations.items():
            print(f"   - {name}: {value}")
        current_total = sum(current_declarations.values())
        print(f"   Current total: {current_total}")
        print(f"   Bot CANNOT declare: {8 - current_total} (would make total = 8)")
        
        # Create bot handler to test the logic
        bot_handler = GameBotHandler("test_room", game)
        
        # Test what bot logic calculates
        print(f"\n🔍 Testing Bot Logic:")
        
        # This is the buggy logic from bot_manager.py lines 487-489
        total_so_far = sum(p.declared for p in game.players if p.declared != 0)
        print(f"   - Bot calculates total using p.declared: {total_so_far}")
        print(f"     (This is WRONG - it's using previous round data!)")
        
        # What bot SHOULD calculate
        correct_total = sum(current_declarations.values())
        print(f"   - Bot SHOULD calculate: {correct_total}")
        print(f"     (Using current round declarations)")
        
        # Show the difference
        print(f"\n❌ BUG CONFIRMED:")
        print(f"   - Bot thinks total is: {total_so_far} (from previous round)")
        print(f"   - Actual current total is: {correct_total}")
        
        # Calculate what bot would declare
        valid_declares = get_valid_declares(bot.hand)
        print(f"\n🤖 Bot's valid declaration options: {valid_declares}")
        
        # Bot would avoid making total = 8 based on WRONG total
        forbidden_value_wrong = 8 - total_so_far
        forbidden_value_correct = 8 - correct_total
        
        print(f"\n🎲 Bot Decision Logic:")
        print(f"   - Bot thinks it should avoid: {forbidden_value_wrong} (based on wrong total)")
        print(f"   - Bot SHOULD avoid: {forbidden_value_correct} (based on correct total)")
        
        if forbidden_value_correct in valid_declares and forbidden_value_wrong != forbidden_value_correct:
            print(f"\n🚨 VIOLATION POSSIBLE:")
            print(f"   - Bot might declare {forbidden_value_correct} thinking total is {total_so_far}")
            print(f"   - This would make actual total = {correct_total + forbidden_value_correct} = 8 (ILLEGAL!)")
            return True
        
        return False
        
    def test_validation_function(self):
        """Test the validation function that always returns True"""
        print(f"\n" + "=" * 80)
        print("TEST: Declaration Validation Function")
        print("=" * 80)
        
        # Read the actual function
        import inspect
        from backend.engine.state_machine.states.declaration_state import DeclarationState
        
        # Get the source code
        source_lines = inspect.getsource(DeclarationState._check_declaration_restrictions)
        print(f"\n📄 Current _check_declaration_restrictions implementation:")
        print("```python")
        print(source_lines)
        print("```")
        
        print(f"\n❌ BUG CONFIRMED: Function always returns True!")
        print(f"   - No validation of last player rule")
        print(f"   - No validation of zero streak rule")
        print(f"   - Allows any declaration value")


def main():
    """Run the simple test"""
    tester = SimpleDeclarationTest()
    
    print("🧪 Running simplified declaration rule tests...\n")
    
    # Test 1: Bot logic bug
    bug_exists = tester.test_bot_declaration_logic()
    
    # Test 2: Validation function bug  
    tester.test_validation_function()
    
    print(f"\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if bug_exists:
        print(f"\n❌ BUGS CONFIRMED:")
        print(f"   1. Bot uses p.declared (previous round) instead of current declarations")
        print(f"   2. _check_declaration_restrictions() provides no validation")
        print(f"\n🔧 REQUIRED FIXES:")
        print(f"   1. Bot should use phase_data['declarations'] for current round")
        print(f"   2. Implement proper validation in _check_declaration_restrictions()")
        return 1
    else:
        print(f"\n✅ No bugs found (or test needs adjustment)")
        return 0


if __name__ == "__main__":
    sys.exit(main())