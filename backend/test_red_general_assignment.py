#!/usr/bin/env python3
"""
Test script to verify RED_GENERAL assignment functionality
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.game import Game
from engine.player import Player


def test_red_general_assignment():
    """Test that RED_GENERAL can be assigned to specific players"""

    # Create test players
    players = [
        Player("Andy", is_bot=False),
        Player("Bot 2", is_bot=True),
        Player("Bot 3", is_bot=True),
        Player("Bot 4", is_bot=True),
    ]

    print("=" * 60)
    print("Testing RED_GENERAL assignment")
    print("=" * 60)

    # Test 1: No specific assignment (random)
    print("\n1. Testing random RED_GENERAL assignment:")
    game1 = Game(players)
    game1._deal_guaranteed_no_redeal()

    red_general_holder = None
    for i, player in enumerate(game1.players):
        has_red_general = any("GENERAL_RED" in str(piece) for piece in player.hand)
        print(f"   Player {i} ({player.name}): RED_GENERAL = {has_red_general}")
        if has_red_general:
            red_general_holder = i

    print(f"   → RED_GENERAL holder: Player {red_general_holder}")

    # Test 2: Assign to player 0 (Andy)
    print("\n2. Testing RED_GENERAL assignment to Player 0 (Andy):")
    players_test2 = [Player(p.name, p.is_bot) for p in players]  # Fresh players
    game2 = Game(players_test2)
    game2._deal_guaranteed_no_redeal(red_general_player_index=0)

    for i, player in enumerate(game2.players):
        has_red_general = any("GENERAL_RED" in str(piece) for piece in player.hand)
        print(f"   Player {i} ({player.name}): RED_GENERAL = {has_red_general}")
        if i == 0 and not has_red_general:
            print("   ❌ FAILED: Player 0 should have RED_GENERAL!")
        elif i == 0 and has_red_general:
            print("   ✅ SUCCESS: Player 0 has RED_GENERAL as expected!")

    # Test 3: Assign to player 1 (Bot 2)
    print("\n3. Testing RED_GENERAL assignment to Player 1 (Bot 2):")
    players_test3 = [Player(p.name, p.is_bot) for p in players]  # Fresh players
    game3 = Game(players_test3)
    game3._deal_guaranteed_no_redeal(red_general_player_index=1)

    for i, player in enumerate(game3.players):
        has_red_general = any("GENERAL_RED" in str(piece) for piece in player.hand)
        print(f"   Player {i} ({player.name}): RED_GENERAL = {has_red_general}")
        if i == 1 and not has_red_general:
            print("   ❌ FAILED: Player 1 should have RED_GENERAL!")
        elif i == 1 and has_red_general:
            print("   ✅ SUCCESS: Player 1 has RED_GENERAL as expected!")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_red_general_assignment()
