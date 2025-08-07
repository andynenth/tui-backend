#!/usr/bin/env python3
"""
Test script to verify overcapture avoidance is working in actual games.
"""

import asyncio
import sys
sys.path.append('backend')

from backend.engine.game import Game
from backend.engine.piece import Piece
from backend.engine.bot_manager import BotManager


async def test_overcapture_scenario():
    """Create a game scenario to test overcapture avoidance"""
    print("Testing Overcapture Avoidance in Live Game")
    print("=" * 50)
    
    # Create a game with 4 bots
    from backend.engine.player import Player
    players = [
        Player("Bot 1", is_bot=True),
        Player("Bot 2", is_bot=True),
        Player("Bot 3", is_bot=True),
        Player("Bot 4", is_bot=True)
    ]
    game = Game(players)
    
    # Initialize game (no explicit start method needed)
    print(f"Game created with {len(game.players)} bots")
    
    # Override Bot 3's hand and declaration for testing
    # Give Bot 3 a hand with weak and strong pieces
    bot3 = game.players[2]
    bot3.hand = [
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_BLACK"),  # 1 point
        Piece("SOLDIER_RED"),   # 2 points
        Piece("CHARIOT_RED"),   # 8 points
        Piece("CHARIOT_RED"),   # 8 points
        Piece("GENERAL_BLACK"), # 13 points
    ]
    bot3.declared = 0  # Declare 0 to test overcapture avoidance
    bot3.captured_piles = 0  # Already at target
    
    print(f"\nBot 3 setup:")
    print(f"  Declared: {bot3.declared}")
    print(f"  Captured: {bot3.captured_piles}")
    print(f"  Hand: {[f'{p.name}({p.point})' for p in bot3.hand]}")
    
    # Set up game state for turn phase
    game.phase = "turn"
    game.turn_number = 1
    game.pile_counts = {
        "Bot 1": 0,
        "Bot 2": 0,
        "Bot 3": 0,
        "Bot 4": 0
    }
    
    # Register game with bot manager
    bot_manager = BotManager()
    bot_manager.register_game("TEST_ROOM", game)
    
    # Get the bot handler for the game
    handler = bot_manager.active_games.get("TEST_ROOM")
    if not handler:
        print("Failed to get bot handler!")
        return
    
    # Simulate Bot 3 needing to play 2 pieces
    print("\nSimulating Bot 3's turn (required to play 2 pieces)...")
    
    # Set required piece count in handler's game state
    handler.game.required_piece_count = 2
    
    # Have Bot 3 make a play
    await handler._bot_play(bot3)
    
    print("\nTest complete! Check the console output above to see if:")
    print("1. Strategic AI was called for Bot 3")
    print("2. Overcapture avoidance was activated")
    print("3. Bot 3 played weak pieces (SOLDIER) instead of strong (CHARIOT)")


if __name__ == "__main__":
    asyncio.run(test_overcapture_scenario())