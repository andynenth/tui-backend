#!/usr/bin/env python3
"""Test PlayHistoryService directly for room AA413B"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_room_aa413b():
    """Test if PlayHistoryService can find room AA413B"""
    
    from backend.services.play_history_service import PlayHistoryService
    from backend.engine.game import Game
    from backend.engine.player import Player
    
    # Create service
    service = PlayHistoryService()
    
    # Create minimal game object (same as API does)
    players = [
        Player("Player 1", is_bot=False),
        Player("Player 2", is_bot=True),
        Player("Player 3", is_bot=True),
        Player("Player 4", is_bot=True)
    ]
    
    minimal_game = Game(players)
    minimal_game.round_number = 0
    minimal_game.current_phase = "WAITING"
    
    # Try to get history
    print("🔍 Testing PlayHistoryService for room AA413B...")
    
    try:
        play_history = await service.build_play_history(
            minimal_game, 
            "AA413B", 
            include_ai_analysis=True, 
            format="full"
        )
        
        print(f"\n✅ Found data:")
        print(f"  Total rounds: {play_history.total_rounds}")
        print(f"  Room ID: {play_history.room_id}")
        
        if play_history.total_rounds > 0:
            print(f"\n📊 Round 1 data:")
            round1 = play_history.rounds[0]
            print(f"  Hands dealt: {'✅ Has data' if round1.hands_dealt else '❌ Empty'}")
            if round1.turn_history:
                turn1 = round1.turn_history[0]
                if turn1.plays:
                    play1 = turn1.plays[0]
                    print(f"  First play hand_after: {'✅ Has data' if play1.hand_after else '❌ Empty'}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_room_aa413b())