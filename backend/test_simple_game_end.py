#!/usr/bin/env python3
"""
Simple Game End Test - Watch the flow in real-time without delays
"""

import asyncio
import sys
import os
import time
sys.path.append(os.path.dirname(__file__))

from engine.state_machine.core import GameAction, ActionType, GamePhase
from engine.state_machine.game_state_machine import GameStateMachine
from engine.game import Game
from engine.player import Player
from engine.piece import Piece

async def test_simple_game_end():
    """Simple test that shows the complete game end flow"""
    print("🎮 SIMPLE GAME END TEST - Real-time Flow")
    print("=" * 50)
    
    # Create players
    players = [
        Player("Andy", is_bot=False),
        Player("Bot 2", is_bot=True),
        Player("Bot 3", is_bot=True), 
        Player("Bot 4", is_bot=True)
    ]
    
    # Set scores where Andy will win after scoring
    players[0].score = 47  # Andy - will reach 52 after +5 perfect score
    players[1].score = 45  # Bot 2 
    players[2].score = 32  # Bot 3
    players[3].score = 28  # Bot 4
    
    # Set captured piles and declarations for perfect scoring
    players[0].captured_piles = 2  # Andy: declared 2, actual 2 = +5 points = 52 total (WINS!)
    players[1].captured_piles = 1  # Bot 2: declared 1, actual 1 = +5 points = 50 total
    players[2].captured_piles = 3  # Bot 3: declared 3, actual 3 = +5 points = 37 total  
    players[3].captured_piles = 1  # Bot 4: declared 1, actual 1 = +5 points = 33 total
    
    game = Game(players)
    game.room_id = "simple_test"
    game.round_number = 11
    game.start_time = time.time() - 900  # 15 minutes ago
    game.player_declarations = {
        "Andy": 2,    # Perfect match
        "Bot 2": 1,   # Perfect match
        "Bot 3": 3,   # Perfect match
        "Bot 4": 1    # Perfect match
    }
    
    print("📊 SETUP:")
    print(f"   Round: {game.round_number}")
    for i, player in enumerate(players):
        declared = game.player_declarations[player.name]
        actual = player.captured_piles
        points_gained = 5 if declared == actual else 2  # Perfect = +5, missed = +2
        new_score = player.score + points_gained
        status = " 🏆 WINNER!" if new_score >= 50 else ""
        print(f"   {player.name}: {player.score} → {new_score} points{status}")
    
    print("\n🎯 Starting in SCORING phase...")
    
    # Create and start state machine in scoring
    state_machine = GameStateMachine(game)
    await state_machine.start(GamePhase.SCORING)
    
    print(f"✅ Current phase: {state_machine.current_phase}")
    
    # Wait and see what happens
    print("\n⏰ Watching the flow...")
    print("   - Scoring calculations should complete")
    print("   - 7-second scoring display delay")  
    print("   - Automatic transition to GAME_END (Andy wins)")
    print("   - Final rankings and statistics")
    
    # Wait for the complete flow
    for i in range(10):  # Wait up to 10 seconds
        await asyncio.sleep(1)
        current_phase = state_machine.current_phase
        print(f"   {i+1}s: Phase = {current_phase}")
        
        if current_phase == GamePhase.GAME_END:
            print("\n🎉 SUCCESS! Reached GAME_END phase!")
            
            # Show the results
            game_end_state = state_machine.current_state
            rankings = game_end_state.final_rankings
            stats = game_end_state.game_statistics
            
            print("\n🏆 FINAL RESULTS:")
            for rank in rankings:
                crown = " 👑" if rank['is_winner'] else ""
                print(f"   {rank['rank']}. {rank['name']}: {rank['score']} points{crown}")
            
            print(f"\n📊 GAME STATS:")
            print(f"   Rounds: {stats['total_rounds']}")
            print(f"   Duration: {stats['game_duration']}")
            
            print(f"\n✅ Event-driven flow working perfectly!")
            return True
    
    print(f"\n❌ Test timeout - final phase: {state_machine.current_phase}")
    return False

async def main():
    try:
        success = await test_simple_game_end()
        if success:
            print(f"\n🎉 SUCCESS! Complete game end flow demonstrated!")
            print(f"\nWhat happened:")
            print(f"1. ⚡ Scoring phase started")
            print(f"2. 🧮 Scores calculated (Andy reaches 52 points)")  
            print(f"3. ⏰ 7-second display delay")
            print(f"4. 🎆 Automatic transition to GAME_END")
            print(f"5. 🏆 Final rankings displayed")
            print(f"6. 📊 Game statistics calculated")
            print(f"7. 🏠 Ready for 'Back to Lobby' action")
        else:
            print(f"\n❌ Test failed or timed out")
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())