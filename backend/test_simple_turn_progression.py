#!/usr/bin/env python3

"""
Simple test to check if turn state machine returns correct next_player data.
"""

import asyncio
from engine.state_machine.states.turn_state import TurnState
from engine.state_machine.core import GameAction, ActionType, GamePhase
from engine.game import Game
from engine.player import Player
from engine.piece import Piece

class MockStateMachine:
    def __init__(self, game):
        self.game = game
        self.current_phase = GamePhase.TURN
        
async def test_turn_state_directly():
    """Test the turn state directly to isolate the next_player issue"""
    print("🧪 Testing Turn State Next Player Logic...")
    
    # Create game with 4 players
    players = [
        Player("Andy", is_bot=False),
        Player("Bot 2", is_bot=True), 
        Player("Bot 3", is_bot=True),
        Player("Bot 4", is_bot=True)
    ]
    
    game = Game(players)
    
    # Deal specific hands
    game.player_hands = {
        "Andy": [Piece("ADVISOR_RED"), Piece("CHARIOT_BLACK"), Piece("SOLDIER_BLACK")],
        "Bot 2": [Piece("GENERAL_RED"), Piece("HORSE_BLACK"), Piece("CANNON_RED")],
        "Bot 3": [Piece("ADVISOR_BLACK"), Piece("ELEPHANT_RED"), Piece("SOLDIER_RED")],
        "Bot 4": [Piece("GENERAL_BLACK"), Piece("CHARIOT_RED"), Piece("HORSE_RED")]
    }
    
    # Set Bot 2 as the round starter
    game.round_starter = "Bot 2"
    game.current_player = "Bot 2"
    
    # Create mock state machine
    mock_sm = MockStateMachine(game)
    
    # Create turn state
    turn_state = TurnState(mock_sm)
    
    # Initialize the turn phase
    await turn_state._setup_phase()
    
    print("✅ Turn state initialized")
    
    # Check initial state
    initial_current = turn_state._get_current_player()
    print(f"🎯 Initial current player: {initial_current}")
    print(f"🎯 Turn order: {turn_state.turn_order}")
    print(f"🎯 Current player index: {turn_state.current_player_index}")
    
    # Bot 2 makes a play
    print("\n🤖 Bot 2 making play...")
    
    play_action = GameAction(
        "Bot 2", 
        ActionType.PLAY_PIECES, 
        {"pieces": [Piece("GENERAL_RED")]},
        is_bot=True
    )
    
    # Validate the action
    is_valid = await turn_state._validate_action(play_action)
    print(f"🔍 Play action valid: {is_valid}")
    
    if not is_valid:
        print("❌ Play action failed validation")
        return
    
    # Process the action
    result = await turn_state._process_action(play_action)
    print(f"🎯 Turn state result: {result}")
    
    # Check updated state
    updated_current = turn_state._get_current_player()
    print(f"🎯 Updated current player: {updated_current}")
    print(f"🎯 Updated player index: {turn_state.current_player_index}")
    print(f"🎯 Turn complete: {turn_state.turn_complete}")
    
    # Verify the result contains next_player
    next_player_from_result = result.get('next_player')
    print(f"🎯 next_player from result: {next_player_from_result}")
    
    # Expected: Bot 3 should be next
    expected_next = "Bot 3"
    
    if next_player_from_result == expected_next:
        print(f"✅ SUCCESS: next_player correctly set to {next_player_from_result}")
    else:
        print(f"❌ FAIL: Expected {expected_next}, got {next_player_from_result}")
        
        # Debug the issue
        print(f"\n🔍 Debugging:")
        print(f"   - Turn order length: {len(turn_state.turn_order)}")
        print(f"   - Current index: {turn_state.current_player_index}")
        print(f"   - Index >= length: {turn_state.current_player_index >= len(turn_state.turn_order)}")
        
        if turn_state.current_player_index < len(turn_state.turn_order):
            actual_next = turn_state.turn_order[turn_state.current_player_index]
            print(f"   - Player at current index: {actual_next}")
    
    # Test second play to make sure progression continues
    print(f"\n🤖 {expected_next} making play...")
    
    if next_player_from_result == expected_next:
        play_action_2 = GameAction(
            expected_next, 
            ActionType.PLAY_PIECES, 
            {"pieces": [Piece("ADVISOR_BLACK")]},
            is_bot=True
        )
        
        is_valid_2 = await turn_state._validate_action(play_action_2)
        if is_valid_2:
            result_2 = await turn_state._process_action(play_action_2)
            next_player_2 = result_2.get('next_player')
            print(f"🎯 After {expected_next} play, next_player: {next_player_2}")
            
            if next_player_2 == "Bot 4":
                print("✅ Turn progression working correctly")
            else:
                print(f"❌ Expected Bot 4, got {next_player_2}")

if __name__ == "__main__":
    asyncio.run(test_turn_state_directly())