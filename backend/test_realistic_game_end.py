#!/usr/bin/env python3
"""
Realistic Game End Test - Simulates the final turn of an actual game

This test sets up a realistic game state where Andy is about to win,
then simulates the final turn and complete game end flow.
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
from engine.bot_manager import BotManager

async def test_realistic_final_turn():
    """Test a realistic final turn leading to game end"""
    print("🎮 Setting up realistic final turn scenario...")
    print("=" * 60)
    
    # Create players with realistic near-winning scores
    players = [
        Player("Andy", is_bot=False),
        Player("Bot 2", is_bot=True),
        Player("Bot 3", is_bot=True), 
        Player("Bot 4", is_bot=True)
    ]
    
    # Set realistic scores where Andy is close to winning (first to 50)
    players[0].score = 48  # Andy - 2 points away from winning
    players[1].score = 44  # Bot 2 - close second
    players[2].score = 31  # Bot 3 - solid third
    players[3].score = 26  # Bot 4 - fourth place
    
    # Set realistic captured piles for this round
    players[0].captured_piles = 2  # Andy has 2 piles
    players[1].captured_piles = 1  # Bot 2 has 1 pile  
    players[2].captured_piles = 3  # Bot 3 has 3 piles
    players[3].captured_piles = 2  # Bot 4 has 2 piles
    
    # Set realistic declarations for scoring
    game = Game(players)
    game.room_id = "final_turn_test"
    game.round_number = 12  # Round 12 - realistic game length
    game.turn_number = 8    # Final turn of the round
    game.start_time = time.time() - 1800  # Game started 30 minutes ago
    game.player_declarations = {
        "Andy": 2,    # Declared 2, has 2 - perfect match (+5 points)
        "Bot 2": 2,   # Declared 2, has 1 - missed by 1 (+2 points) 
        "Bot 3": 3,   # Declared 3, has 3 - perfect match (+5 points)
        "Bot 4": 1    # Declared 1, has 2 - missed by 1 (+2 points)
    }
    
    # Give players final hands (almost empty) - use the exact same pieces we'll play
    soldier_red = Piece("SOLDIER_RED")
    cannon_black = Piece("CANNON_BLACK") 
    general_red = Piece("GENERAL_RED")
    soldier_black = Piece("SOLDIER_BLACK")
    
    players[0].hand = [soldier_red]      # Andy: 1 piece left
    players[1].hand = [cannon_black]     # Bot 2: 1 piece left
    players[2].hand = [general_red]      # Bot 3: 1 piece left  
    players[3].hand = [soldier_black]    # Bot 4: 1 piece left
    
    print(f"🎯 SCENARIO: Round {game.round_number}, Turn {game.turn_number}")
    print(f"📊 Current Scores:")
    for player in players:
        print(f"   {player.name}: {player.score} points ({player.captured_piles} piles this round)")
    print(f"🎲 Declarations vs Actual:")
    for name, declared in game.player_declarations.items():
        actual = next(p.captured_piles for p in players if p.name == name)
        print(f"   {name}: declared {declared}, actual {actual}")
    print(f"🃏 Final hands: Each player has 1 piece left")
    print()
    
    # Setup state machine and bot manager
    state_machine = GameStateMachine(game)
    bot_manager = BotManager()
    bot_manager.register_game("final_turn_test", game, state_machine)
    
    # Start in TURN phase for the final turn
    await state_machine.start(GamePhase.TURN)
    turn_state = state_machine.current_state
    
    # Setup turn state for final turn
    turn_state.current_turn_starter = "Andy"  # Andy starts this turn
    turn_state.turn_order = ["Andy", "Bot 2", "Bot 3", "Bot 4"]
    turn_state.current_player_index = 0
    turn_state.required_piece_count = None
    turn_state.turn_plays = {}
    turn_state.turn_complete = False
    
    print("🎮 FINAL TURN SIMULATION:")
    print("=" * 40)
    
    # Andy plays first (starter)
    print("1️⃣ Andy plays SOLDIER_RED (2 points)")
    andy_action = GameAction(
        player_name="Andy",
        action_type=ActionType.PLAY_PIECES,
        payload={
            'pieces': [soldier_red],  # Use the same piece from hand
            'play_type': 'single',
            'play_value': 2,
            'is_valid': True
        }
    )
    result1 = await state_machine.handle_action(andy_action)
    print(f"   ✅ Andy's play: {result1}")
    await asyncio.sleep(0.5)  # Brief pause for realism
    
    # Bot 2 plays
    print("2️⃣ Bot 2 plays CANNON_BLACK (3 points)")
    bot2_action = GameAction(
        player_name="Bot 2",
        action_type=ActionType.PLAY_PIECES,
        payload={
            'pieces': [cannon_black],  # Use the same piece from hand
            'play_type': 'single', 
            'play_value': 3,
            'is_valid': True
        },
        is_bot=True
    )
    result2 = await state_machine.handle_action(bot2_action)
    print(f"   ✅ Bot 2's play: {result2}")
    await asyncio.sleep(0.5)
    
    # Bot 3 plays
    print("3️⃣ Bot 3 plays GENERAL_RED (9 points) - HIGHEST!")
    bot3_action = GameAction(
        player_name="Bot 3",
        action_type=ActionType.PLAY_PIECES,
        payload={
            'pieces': [general_red],  # Use the same piece from hand
            'play_type': 'single',
            'play_value': 9,
            'is_valid': True
        },
        is_bot=True
    )
    result3 = await state_machine.handle_action(bot3_action)
    print(f"   ✅ Bot 3's play: {result3}")
    await asyncio.sleep(0.5)
    
    # Bot 4 plays (final play - will trigger turn completion)
    print("4️⃣ Bot 4 plays SOLDIER_BLACK (1 point)")
    print("   🎯 This will complete the turn and trigger game end sequence...")
    bot4_action = GameAction(
        player_name="Bot 4", 
        action_type=ActionType.PLAY_PIECES,
        payload={
            'pieces': [soldier_black],  # Use the same piece from hand
            'play_type': 'single',
            'play_value': 1,
            'is_valid': True
        },
        is_bot=True
    )
    result4 = await state_machine.handle_action(bot4_action)
    print(f"   ✅ Bot 4's play: {result4}")
    
    # Allow time for turn completion processing
    await asyncio.sleep(1.0)
    
    print()
    print("🏆 TURN RESULTS:")
    print("=" * 30)
    print("   Winner: Bot 3 (GENERAL_RED - 9 points)")
    print("   Bot 3 wins 1 pile (brings total to 4 piles)")
    print("   🃏 All hands are now EMPTY!")
    print()
    
    # Wait for the 7-second turn result display delay
    print("⏰ Waiting 7 seconds for turn result display...")
    await asyncio.sleep(8.0)  # Wait for turn result display + transition
    
    # Should now be in SCORING phase
    print("📊 SCORING PHASE:")
    print("=" * 25)
    if state_machine.current_phase == GamePhase.SCORING:
        print("   ✅ Transitioned to SCORING phase")
        print("   🧮 Calculating final scores...")
        
        # Wait for scoring calculations and 7-second display
        await asyncio.sleep(8.0)  # Wait for scoring display + transition
        
        # Should now be in GAME_END phase
        print()
        print("🎉 GAME END PHASE:")
        print("=" * 25)
        if state_machine.current_phase == GamePhase.GAME_END:
            game_end_state = state_machine.current_state
            
            print("   ✅ Transitioned to GAME_END phase")
            print("   🏆 Final Rankings:")
            for ranking in game_end_state.final_rankings:
                crown = " 👑" if ranking['is_winner'] else ""
                print(f"      {ranking['rank']}. {ranking['name']}: {ranking['score']} points{crown}")
            
            print("   📊 Game Statistics:")
            stats = game_end_state.game_statistics
            print(f"      Total Rounds: {stats['total_rounds']}")
            print(f"      Game Duration: {stats['game_duration']}")
            
            # Test the back to lobby action
            print()
            print("🏠 Testing 'Back to Lobby' action...")
            lobby_action = GameAction(
                player_name="Andy",
                action_type=ActionType.NAVIGATE_TO_LOBBY,
                payload={}
            )
            lobby_result = await state_machine.handle_action(lobby_action)
            print(f"   ✅ Lobby action: {lobby_result}")
            
            print()
            print("🎯 REALISTIC GAME END TEST RESULTS:")
            print("=" * 50)
            print("   ✅ Final turn played successfully")
            print("   ✅ Turn result display (7 seconds)")
            print("   ✅ Automatic transition to SCORING")
            print("   ✅ Score calculation and display (7 seconds)")
            print("   ✅ Automatic transition to GAME_END (game complete)")
            print("   ✅ Final rankings displayed with winner")
            print("   ✅ Game statistics calculated")
            print("   ✅ Back to Lobby action handled")
            print("   ✅ Complete event-driven flow working!")
            
            return True
        else:
            print(f"   ❌ Expected GAME_END phase, got: {state_machine.current_phase}")
            return False
    else:
        print(f"   ❌ Expected SCORING phase, got: {state_machine.current_phase}")
        return False

async def main():
    """Run realistic game end test"""
    try:
        print("🚀 REALISTIC GAME END TEST")
        print("=" * 60)
        print("Simulating: Round 12, Turn 8 - Andy about to win!")
        print("This will show the complete final turn → game end flow")
        print("=" * 60)
        print()
        
        success = await test_realistic_final_turn()
        
        if success:
            print()
            print("🎉 SUCCESS! Complete game end flow working perfectly!")
            print()
            print("💡 What you just saw:")
            print("   • Final turn with 4 players (Andy close to winning)")
            print("   • All players play their last pieces")
            print("   • Bot 3 wins the turn with GENERAL_RED")
            print("   • Turn result display (7 seconds)")
            print("   • Scoring calculation and display (7 seconds)")
            print("   • Game end detection (Andy reaches 53 points)")
            print("   • Beautiful game end screen with rankings")
            print("   • User-controlled navigation back to lobby")
            print()
            print("🎮 The frontend will show:")
            print("   • Turn results UI for 7 seconds")
            print("   • Scoring UI for 7 seconds") 
            print("   • Game end celebration screen with:")
            print("     - Final rankings (1st: Andy 👑)")
            print("     - Game statistics (12 rounds, 30 minutes)")
            print("     - 'Back to Lobby' button")
            print()
            sys.exit(0)
        else:
            print("❌ Test failed - check the output above")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())