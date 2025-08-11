#!/usr/bin/env python3
"""
Simple test to verify Play History API works with SQLite
"""

import asyncio
import json
from backend.services.play_history_service import PlayHistoryService
from backend.engine.game import Game


async def test_simple():
    """Simple test of the play history service"""
    
    # Create service
    service = PlayHistoryService()
    
    # Create a minimal game object (simulating no in-memory data)
    from backend.engine.player import Player
    
    # Create minimal players
    players = [
        Player("Andy", is_bot=False),
        Player("Bot 2", is_bot=True),
        Player("Bot 3", is_bot=True),
        Player("Bot 4", is_bot=True)
    ]
    
    game = Game(players)
    game.round_number = 0  # No rounds in memory
    game.current_phase = "WAITING"
    
    # Test extraction from SQLite
    room_id = "258B79"
    print(f"Testing Play History Service for room {room_id}...")
    
    try:
        # This should fall back to SQLite since game has no data
        play_history = await service.build_play_history(
            game=game,
            room_id=room_id,
            include_ai_analysis=True,
            format=None
        )
        
        print(f"\n✅ Success!")
        print(f"Total Rounds from SQLite: {play_history.total_rounds}")
        print(f"Players: {list(play_history.players.keys())}")
        
        # Show summary
        for round_data in play_history.rounds:
            print(f"\nRound {round_data.round_number}:")
            print(f"  Turns: {len(round_data.turn_history)}")
            if round_data.round_summary:
                print(f"  Winners:")
                for player, score in round_data.round_summary.scoring.items():
                    if score.points > 0:
                        print(f"    {player}: {score.points} points")
        
        print("\n🎉 SQLite integration working! Historical data retrieved successfully.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_simple())