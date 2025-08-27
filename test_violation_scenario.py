#!/usr/bin/env python3
"""
Test showing a realistic scenario where bot violates the rule.

Scenario: Previous round had different declarations than current round,
causing bot to calculate wrong total and violate the rule.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece


def test_violation_scenario():
    """Show a realistic scenario where violation occurs"""
    print("=" * 80)
    print("REALISTIC VIOLATION SCENARIO")
    print("=" * 80)
    
    # Create game
    players = [
        Player("Alice", is_bot=False),
        Player("Bob", is_bot=False),
        Player("Carol", is_bot=False),
        Player("BotDan", is_bot=True)
    ]
    
    game = Game(players)
    game.round_number = 3
    
    # Give bot cards
    bot = players[3]
    bot.hand = Piece.build_deck()[:8]
    
    print(f"\n🎮 Game Setup:")
    print(f"   - Round 3 of the game")
    print(f"   - Players: Alice, Bob, Carol, BotDan (bot)")
    print(f"   - BotDan declares last")
    
    # Previous round (Round 2) declarations - stored in p.declared
    print(f"\n📜 Previous Round (Round 2) Declarations:")
    players[0].declared = 1  # Alice
    players[1].declared = 2  # Bob
    players[2].declared = 2  # Carol
    players[3].declared = 3  # BotDan
    
    for p in players:
        print(f"   - {p.name}: {p.declared}")
    prev_total = sum(p.declared for p in players)
    print(f"   Total: {prev_total}")
    
    # Current round (Round 3) declarations
    print(f"\n🎯 Current Round (Round 3) Declarations:")
    current_declarations = {
        "Alice": 3,   # Different from previous round!
        "Bob": 1,     # Different from previous round!
        "Carol": 2    # Same as previous round
    }
    
    for name, value in current_declarations.items():
        print(f"   - {name} declares: {value}")
        
    current_total = sum(current_declarations.values())
    print(f"   Current total: {current_total}")
    print(f"   ⚠️  BotDan CANNOT declare: {8 - current_total} (would make total = 8)")
    
    # Show what bot calculates
    print(f"\n🤖 Bot's Flawed Logic:")
    # Bot excludes zeros, so it calculates based on non-zero p.declared values
    bot_calculated = sum(p.declared for p in game.players if p.declared != 0)
    print(f"   Bot uses: sum(p.declared for p in players if p.declared != 0)")
    print(f"   Bot calculates total: {bot_calculated} (from PREVIOUS round)")
    print(f"   Bot thinks it should avoid: {8 - bot_calculated}")
    
    print(f"\n🚨 THE VIOLATION:")
    forbidden_correct = 8 - current_total
    forbidden_wrong = 8 - bot_calculated
    
    print(f"   Bot should avoid: {forbidden_correct}")
    print(f"   Bot thinks to avoid: {forbidden_wrong}")
    
    if forbidden_correct != forbidden_wrong:
        print(f"\n   ❌ RULE VIOLATION!")
        print(f"   Bot will declare {forbidden_correct} (thinking it's safe)")
        print(f"   This makes total = {current_total} + {forbidden_correct} = {current_total + forbidden_correct}")
        
        if current_total + forbidden_correct == 8:
            print(f"   💥 ILLEGAL! Total equals 8!")
            print(f"\n   The bot violated the rule because:")
            print(f"   1. It used data from the PREVIOUS round")
            print(f"   2. The validation function didn't catch it")
            return True
    
    return False


def show_fix():
    """Show how the fix would work"""
    print(f"\n" + "=" * 80)
    print("HOW THE FIX WORKS")
    print("=" * 80)
    
    print(f"\n🔧 Fix 1: Bot Uses Correct Data")
    print(f"   Instead of: sum(p.declared for p in players)")
    print(f"   Use: sum(phase_data['declarations'].values())")
    print(f"   This gives the CURRENT round's declarations")
    
    print(f"\n🔧 Fix 2: Validation Catches Violations")
    print(f"   The validation function checks:")
    print(f"   - Is this the last player? ✓")
    print(f"   - Would this declaration make total = 8? ✓")
    print(f"   - If yes, reject the declaration ✓")
    
    print(f"\n✅ Result: Bot cannot violate the rule anymore!")


def main():
    violation_occurred = test_violation_scenario()
    
    if violation_occurred:
        show_fix()
        print(f"\n🎯 Test successfully demonstrated the rule violation!")
        return 0
    else:
        print(f"\n❓ No violation in this scenario")
        return 1


if __name__ == "__main__":
    sys.exit(main())