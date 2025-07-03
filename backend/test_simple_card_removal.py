#!/usr/bin/env python3
"""
🧪 Simple Card Removal Test
Tests that cards are removed immediately when played using the Enterprise Architecture.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.game import Game
from engine.player import Player  
from engine.piece import Piece
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase


async def test_card_removal():
    """Simple test of immediate card removal"""
    print("🧪 Testing Card Removal Fix")
    print("=" * 40)
    
    # Create minimal test setup
    players = [
        Player("TestBot1", is_bot=True),
        Player("TestBot2", is_bot=True), 
        Player("TestBot3", is_bot=True),
        Player("TestBot4", is_bot=True)
    ]
    
    # Give each player 2 pieces for quick testing
    test_pieces = [
        Piece("GENERAL_RED"), Piece("HORSE_BLACK"),
        Piece("CANNON_RED"), Piece("SOLDIER_BLACK"),
        Piece("ELEPHANT_RED"), Piece("ADVISOR_BLACK"),
        Piece("CHARIOT_RED"), Piece("SOLDIER_RED")
    ]
    
    for i, player in enumerate(players):
        player.hand = test_pieces[i*2:(i+1)*2].copy()
        print(f"🎮 {player.name}: {[str(p) for p in player.hand]} (size: {len(player.hand)})")
    
    # Create game and state machine
    game = Game(players)
    state_machine = GameStateMachine(game)
    
    # Start state machine and go to turn phase manually
    print("\n🚀 Starting state machine...")
    await state_machine.start()
    
    # Wait to avoid rapid transition blocking
    await asyncio.sleep(1)
    
    # Force transition to turn phase directly
    print("🔄 Forcing transition to turn phase...")
    state_machine.current_phase = GamePhase.TURN
    state_machine.current_state = state_machine.states[GamePhase.TURN]
    
    # Initialize turn state manually
    turn_state = state_machine.current_state
    
    # Set up basic turn state
    turn_state.current_turn_starter = "TestBot1"
    turn_state.turn_order = ["TestBot1", "TestBot2", "TestBot3", "TestBot4"]
    turn_state.current_player_index = 0
    turn_state.required_piece_count = None
    turn_state.turn_plays = {}
    
    print("✅ Turn state initialized")
    
    # Test immediate card removal
    print("\n🎯 Testing card removal...")
    first_player = game.players[0]  # TestBot1
    initial_hand_size = len(first_player.hand)
    piece_to_play = first_player.hand[0]
    
    print(f"📋 Before play: {first_player.name} has {initial_hand_size} pieces: {[str(p) for p in first_player.hand]}")
    
    # Create play action
    action = GameAction(
        player_name=first_player.name,
        action_type=ActionType.PLAY_PIECES,
        payload={'pieces': [piece_to_play]},
        timestamp=datetime.now(),
        is_bot=True
    )
    
    # Call the method directly to test immediate removal
    print(f"🎯 Playing piece: {piece_to_play}")
    
    # Call _handle_play_pieces directly
    result = await turn_state._handle_play_pieces(action)
    
    # Check immediate removal
    after_play_hand_size = len(first_player.hand)
    print(f"📋 After play: {first_player.name} has {after_play_hand_size} pieces: {[str(p) for p in first_player.hand]}")
    
    # Validate results
    expected_size = initial_hand_size - 1
    if after_play_hand_size == expected_size:
        print("✅ PASS: Card removed immediately")
        if piece_to_play not in first_player.hand:
            print("✅ PASS: Correct piece removed")
            print("🎉 CARD REMOVAL FIX IS WORKING!")
            return True
        else:
            print(f"❌ FAIL: Played piece {piece_to_play} still in hand")
            return False
    else:
        print(f"❌ FAIL: Expected hand size {expected_size}, got {after_play_hand_size}")
        return False


async def main():
    """Run the simple test"""
    try:
        success = await test_card_removal()
        if success:
            print("\n✅ CARD REMOVAL FIX VALIDATED")
            exit(0)
        else:
            print("\n❌ CARD REMOVAL FIX FAILED")
            exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())