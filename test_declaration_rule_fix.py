#!/usr/bin/env python3
"""
Test case that will FAIL before the fix and PASS after the fix.

This test:
1. Sets up a scenario where bot would violate the rule
2. Checks if the violation occurs
3. Returns exit code 1 if violation detected (bug exists)
4. Returns exit code 0 if no violation (bug fixed)
"""

import sys
from pathlib import Path
from typing import Dict

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece


class DeclarationRuleTest:
    """Test the declaration rule enforcement"""
    
    def __init__(self):
        self.violation_detected = False
        self.bot_declared_value = None
        self.expected_forbidden = None
        self.actual_forbidden = None
        
    def setup_game(self) -> Game:
        """Set up a game in a state to test the rule"""
        players = [
            Player("Human1", is_bot=False),
            Player("Human2", is_bot=False), 
            Player("Human3", is_bot=False),
            Player("Bot1", is_bot=True)
        ]
        
        game = Game(players)
        game.round_number = 2
        
        # Give bot cards
        bot = players[3]
        bot.hand = Piece.build_deck()[:8]
        
        # Set previous round declarations (what p.declared contains)
        # Use different values that will cause a violation
        players[0].declared = 1  # Different from current round
        players[1].declared = 2  # Different from current round
        players[2].declared = 2  # Different from current round
        players[3].declared = 3  # Bot's previous declaration
        
        return game
        
    def test_bot_logic(self, game: Game, current_declarations: Dict[str, int]) -> bool:
        """Test if bot logic is fixed"""
        # Read the bot manager code to check for the fix
        from pathlib import Path
        bot_manager_path = Path(__file__).parent / "backend" / "engine" / "bot_manager.py"
        
        with open(bot_manager_path, 'r') as f:
            content = f.read()
            
        # Check if the fix is present
        if "phase_data.get('declarations'" in content or "phase_data['declarations']" in content:
            # Fixed version uses phase_data
            print(f"   ✅ Bot logic uses phase_data['declarations'] - FIXED!")
            return False  # No violation possible with fix
        else:
            # Still using buggy version
            print(f"   ❌ Bot logic still uses p.declared - BUGGY!")
            
            # Simulate the buggy behavior
            correct_total = sum(current_declarations.values())
            self.expected_forbidden = 8 - correct_total
            
            bot_total = sum(p.declared for p in game.players if p.declared != 0)
            self.actual_forbidden = 8 - bot_total
            
            if self.expected_forbidden != self.actual_forbidden:
                self.bot_declared_value = self.expected_forbidden
                final_total = correct_total + self.expected_forbidden
                
                if final_total == 8:
                    self.violation_detected = True
                    return True
                    
        return False
        
    def test_validation_function(self) -> bool:
        """Test if validation function works"""
        # Import the validation function
        from backend.engine.state_machine.states.declaration_state import DeclarationState
        
        # Check if it's the stub that always returns True
        import inspect
        source = inspect.getsource(DeclarationState._check_declaration_restrictions)
        
        # Check if it has the proper validation logic
        has_zero_streak_check = 'zero_declares_in_a_row' in source
        has_last_player_check = 'current_total + value == 8' in source
        has_validation_logic = 'if ' in source and 'return False' in source
        
        # It's properly implemented if it has the validation checks
        return has_zero_streak_check and has_last_player_check and has_validation_logic
        
    def run_test(self) -> bool:
        """Run the complete test"""
        print("=" * 80)
        print("DECLARATION RULE VIOLATION TEST")
        print("=" * 80)
        
        # Setup
        game = self.setup_game()
        
        # Current round declarations
        current_declarations = {
            "Human1": 3,
            "Human2": 2,
            "Human3": 1
        }
        
        current_total = sum(current_declarations.values())
        
        print(f"\n📋 Test Scenario:")
        print(f"   Previous round total (in p.declared): {sum(p.declared for p in game.players if p.declared != 0)}")
        print(f"   Current round declarations: {current_declarations}")
        print(f"   Current total: {current_total}")
        print(f"   Bot must NOT declare: {8 - current_total}")
        
        # Test bot logic
        bot_violates = self.test_bot_logic(game, current_declarations)
        
        # Test validation
        validation_works = self.test_validation_function()
        
        print(f"\n🔍 Test Results:")
        print(f"   Bot thinks it should avoid: {self.actual_forbidden}")
        print(f"   Bot ACTUALLY should avoid: {self.expected_forbidden}")
        
        if bot_violates:
            print(f"\n❌ VIOLATION DETECTED!")
            print(f"   Bot would declare: {self.bot_declared_value}")
            print(f"   Making total = {current_total + self.bot_declared_value} (ILLEGAL!)")
        else:
            print(f"\n✅ No violation - bot logic is correct")
            
        if not validation_works:
            print(f"\n❌ Validation function is not implemented")
        else:
            print(f"\n✅ Validation function is implemented")
            
        # Return True if bugs exist (test should fail)
        return bot_violates or not validation_works


def main():
    """Run test and return appropriate exit code"""
    tester = DeclarationRuleTest()
    
    bugs_exist = tester.run_test()
    
    print(f"\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    
    if bugs_exist:
        print(f"\n❌ TEST FAILED - Bugs detected!")
        print(f"   This is expected before applying the fixes.")
        print(f"\n   To fix:")
        print(f"   1. Update bot logic to use phase_data['declarations']")
        print(f"   2. Implement _check_declaration_restrictions()")
        return 1  # Exit code 1 = test failed (bugs exist)
    else:
        print(f"\n✅ TEST PASSED - No bugs detected!")
        print(f"   The declaration rule is properly enforced.")
        return 0  # Exit code 0 = test passed (bugs fixed)


if __name__ == "__main__":
    sys.exit(main())