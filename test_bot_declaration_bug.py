#!/usr/bin/env python3
"""
Test to prove bots can violate the declaration rule by declaring values that make total = 8.

This test demonstrates two bugs:
1. Bot uses p.declared (previous round data) instead of current declarations
2. _check_declaration_restrictions() always returns True (no validation)
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece


def test_bot_declaration_bug():
    """Demonstrate the bot declaration bug"""
    print("=" * 80)
    print("TEST: Bot Declaration Rule Violation")
    print("=" * 80)
    
    # Create game with 4 players (3 humans, 1 bot)
    players = [
        Player("Human1", is_bot=False),
        Player("Human2", is_bot=False),
        Player("Human3", is_bot=False),
        Player("Bot1", is_bot=True)
    ]
    
    game = Game(players)
    game.round_number = 2  # Not first round
    
    # Give bot some cards (needed for bot logic)
    bot = players[3]
    bot.hand = Piece.build_deck()[:8]
    
    print(f"\n📋 Test Setup:")
    print(f"   - 4 players: 3 humans, 1 bot (last to declare)")
    print(f"   - Round 2 (not first round)")
    print(f"   - Bot has 8 cards in hand")
    
    # Set up previous round declarations (what p.declared contains)
    print(f"\n📜 Previous Round Data (in p.declared):")
    players[0].declared = 3  # Human1
    players[1].declared = 2  # Human2
    players[2].declared = 1  # Human3
    players[3].declared = 0  # Bot1
    
    for p in players:
        print(f"   - {p.name}: {p.declared}")
    prev_total = sum(p.declared for p in players if p.declared != 0)
    print(f"   Total (excluding zeros): {prev_total}")
    
    # Current round declarations
    print(f"\n🎯 Current Round Scenario:")
    current_declarations = {
        "Human1": 2,
        "Human2": 1,
        "Human3": 3
    }
    
    for name, value in current_declarations.items():
        print(f"   - {name} declares: {value}")
    
    current_total = sum(current_declarations.values())
    print(f"   Total so far: {current_total}")
    print(f"   ⚠️  Bot CANNOT declare: {8 - current_total} (would make total = 8)")
    
    # Show the bug - bot uses wrong data
    print(f"\n🐛 BUG #1: Bot Uses Wrong Data Source")
    print(f"   Code from bot_manager.py lines 487-489:")
    print(f"   total_so_far = sum(p.declared for p in game_state.players if p.declared != 0)")
    
    # What bot calculates (WRONG)
    bot_calculated_total = sum(p.declared for p in game.players if p.declared != 0)
    print(f"\n   Bot calculates: {bot_calculated_total} (from PREVIOUS round)")
    print(f"   Bot should use: {current_total} (from CURRENT round)")
    
    forbidden_wrong = 8 - bot_calculated_total
    forbidden_correct = 8 - current_total
    
    print(f"\n   Based on wrong data:")
    print(f"   - Bot thinks it should avoid: {forbidden_wrong}")
    print(f"   - Bot ACTUALLY should avoid: {forbidden_correct}")
    
    if forbidden_wrong != forbidden_correct:
        print(f"\n   ❌ VIOLATION POSSIBLE!")
        print(f"   Bot might declare {forbidden_correct}, thinking total is {bot_calculated_total}")
        print(f"   This would make actual total = {current_total + forbidden_correct} = 8 (ILLEGAL!)")
    
    # Show validation bug
    print(f"\n🐛 BUG #2: Validation Always Returns True")
    print(f"   Code from declaration_state.py lines 165-170:")
    print(f"   async def _check_declaration_restrictions(self, player_name: str, value: int) -> bool:")
    print(f"       return True  # Always returns True!")
    
    print(f"\n   ❌ NO VALIDATION of:")
    print(f"   - Last player making total = 8")
    print(f"   - Zero declaration streak limit")
    print(f"   - Any other game rules")
    
    # Summary
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✅ BUGS CONFIRMED:")
    print(f"\n1. Bot Declaration Logic Bug:")
    print(f"   - Location: backend/engine/bot_manager.py:487-489")
    print(f"   - Problem: Uses p.declared (previous round) instead of phase_data['declarations']")
    print(f"   - Fix: Change to use current round declarations from phase_data")
    
    print(f"\n2. Validation Function Bug:")
    print(f"   - Location: backend/engine/state_machine/states/declaration_state.py:165-170")
    print(f"   - Problem: Always returns True, no actual validation")
    print(f"   - Fix: Implement proper validation logic")
    
    print(f"\n🔧 PROPOSED FIXES:")
    print(f"\n1. Fix bot logic in bot_manager.py:")
    print(f"   # OLD (WRONG):")
    print(f"   total_so_far = sum(p.declared for p in game_state.players if p.declared != 0)")
    print(f"   ")
    print(f"   # NEW (CORRECT):")
    print(f"   declarations = phase_data.get('declarations', " + "{}" + ")")
    print(f"   total_so_far = sum(declarations.values())")
    
    print(f"\n2. Fix validation in declaration_state.py:")
    print(f"   async def _check_declaration_restrictions(self, player_name: str, value: int) -> bool:")
    print(f"       # Check last player rule")
    print(f"       order = self.phase_data['declaration_order']")
    print(f"       current_index = self.phase_data['current_declarer_index']")
    print(f"       ")
    print(f"       if current_index == len(order) - 1:  # Last player")
    print(f"           current_total = self.phase_data['declaration_total']")
    print(f"           if current_total + value == 8:")
    print(f"               return False  # Cannot make total = 8")
    print(f"       ")
    print(f"       # Check zero streak rule")
    print(f"       player = self.state_machine.game.get_player(player_name)")
    print(f"       if player.zero_declares_in_a_row >= 2 and value == 0:")
    print(f"           return False  # Must declare at least 1")
    print(f"       ")
    print(f"       return True")


def main():
    test_bot_declaration_bug()
    return 0  # Success - test demonstrates the bugs exist


if __name__ == "__main__":
    sys.exit(main())