#!/usr/bin/env python3
# backend/investigate_bug.py

import sys
import os
import asyncio
from datetime import datetime

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.state_machine.core import GamePhase, ActionType, GameAction
from engine.state_machine.states.turn_state import TurnState


class TestGame:
    def __init__(self):
        self.players = ["Player1", "Player2", "Player3", "Player4"]
        self.round_starter = "Player1"
        self.current_player = "Player1"
        self.player_hands = {
            "Player1": [1, 2, 3, 4, 5, 6, 7, 8],
            "Player2": [9, 10, 11, 12, 13, 14, 15, 16],
            "Player3": [17, 18, 19, 20, 21, 22, 23, 24],
            "Player4": [25, 26, 27, 28, 29, 30, 31, 32]
        }
        self.player_piles = {
            "Player1": 0,
            "Player2": 0,
            "Player3": 0,
            "Player4": 0
        }
    
    def get_player_order_from(self, starter):
        start_idx = self.players.index(starter)
        return self.players[start_idx:] + self.players[:start_idx]


class MockStateMachine:
    def __init__(self, game):
        self.game = game


async def trace_bug():
    """Trace through the exact bug scenario"""
    print("🔍 TRACING THE BUG")
    print("=" * 60)
    
    # Setup
    game = TestGame()
    state_machine = MockStateMachine(game)
    turn_state = TurnState(state_machine)
    
    await turn_state.on_enter()
    print(f"✅ Initial setup - starter: {turn_state.current_turn_starter}")
    print(f"✅ Turn order: {turn_state.turn_order}")
    print(f"✅ Current player index: {turn_state.current_player_index}")
    
    # The exact same plays from the failing test
    plays = [
        ("Player1", {'pieces': [1, 2], 'play_type': 'pair', 'play_value': 10}),
        ("Player2", {'pieces': [9, 10], 'play_type': 'pair', 'play_value': 15}),
        ("Player3", {'pieces': [17, 18], 'play_type': 'pair', 'play_value': 20}),  # Should win
        ("Player4", {'pieces': [25, 26], 'play_type': 'pair', 'play_value': 8})
    ]
    
    for i, (player, payload) in enumerate(plays):
        print(f"\n--- PROCESSING PLAY {i+1}: {player} ---")
        
        action = GameAction(
            player_name=player,
            action_type=ActionType.PLAY_PIECES,
            payload=payload,
            timestamp=datetime.now()
        )
        
        # Before processing
        print(f"🔍 Before play - current_player_index: {turn_state.current_player_index}")
        print(f"🔍 Before play - turn_complete: {turn_state.turn_complete}")
        print(f"🔍 Before play - winner: {turn_state.winner}")
        print(f"🔍 Before play - turn_plays count: {len(turn_state.turn_plays)}")
        
        # Process the action
        result = await turn_state._process_action(action)
        
        # After processing
        print(f"🔍 After play - current_player_index: {turn_state.current_player_index}")
        print(f"🔍 After play - turn_complete: {turn_state.turn_complete}")
        print(f"🔍 After play - winner: {turn_state.winner}")
        print(f"🔍 After play - turn_plays count: {len(turn_state.turn_plays)}")
        print(f"🔍 Result turn_complete: {result.get('turn_complete')}")
        
        # Check if turn should be complete
        if turn_state.current_player_index >= len(turn_state.turn_order):
            print(f"🚨 Turn should be complete! current_player_index ({turn_state.current_player_index}) >= turn_order length ({len(turn_state.turn_order)})")
        
        # If this is the last player, dive deeper
        if i == 3:  # Player4 (last player)
            print(f"\n🔍 DEEP DIVE - LAST PLAYER")
            print(f"🔍 Turn plays data:")
            for p, data in turn_state.turn_plays.items():
                print(f"   {p}: {data}")
            
            # Manually call _determine_turn_winner to see what it returns
            print(f"\n🔍 Manually calling _determine_turn_winner()...")
            manual_winner = turn_state._determine_turn_winner()
            print(f"🔍 Manual winner result: {manual_winner}")
            
            # Check if _complete_turn was called
            if turn_state.turn_complete:
                print(f"✅ _complete_turn() was called")
            else:
                print(f"❌ _complete_turn() was NOT called")
    
    print(f"\n🔍 FINAL STATE:")
    print(f"🔍 Final winner: {turn_state.winner}")
    print(f"🔍 Final turn_complete: {turn_state.turn_complete}")
    print(f"🔍 Final current_player_index: {turn_state.current_player_index}")
    
    await turn_state.on_exit()


async def test_winner_logic_isolated():
    """Test the winner determination logic in isolation"""
    print(f"\n🧪 TESTING WINNER LOGIC IN ISOLATION")
    print("=" * 60)
    
    game = TestGame()
    state_machine = MockStateMachine(game)
    turn_state = TurnState(state_machine)
    
    await turn_state.on_enter()
    
    # Manually set up the exact turn plays from the test
    turn_state.turn_plays = {
        "Player1": {'pieces': [1, 2], 'play_type': 'pair', 'play_value': 10, 'is_valid': True},
        "Player2": {'pieces': [9, 10], 'play_type': 'pair', 'play_value': 15, 'is_valid': True},
        "Player3": {'pieces': [17, 18], 'play_type': 'pair', 'play_value': 20, 'is_valid': True},
        "Player4": {'pieces': [25, 26], 'play_type': 'pair', 'play_value': 8, 'is_valid': True}
    }
    
    print(f"🔍 Manual turn_plays setup:")
    for player, data in turn_state.turn_plays.items():
        print(f"   {player}: {data}")
    
    print(f"🔍 current_turn_starter: {turn_state.current_turn_starter}")
    
    # Test winner determination
    winner = turn_state._determine_turn_winner()
    print(f"🔍 Winner determination result: {winner}")
    
    # Step through the winner logic manually
    print(f"\n🔍 STEP-BY-STEP WINNER LOGIC:")
    
    # Step 1: Check if turn_plays exists
    if not turn_state.turn_plays:
        print(f"❌ No turn_plays")
        return
    else:
        print(f"✅ turn_plays exists: {len(turn_state.turn_plays)} plays")
    
    # Step 2: Get starter's play
    starter_play = turn_state.turn_plays.get(turn_state.current_turn_starter)
    if not starter_play:
        print(f"❌ No starter play found for {turn_state.current_turn_starter}")
        return
    else:
        print(f"✅ Starter play found: {starter_play}")
    
    # Step 3: Get target play type
    target_play_type = starter_play.get('play_type', 'unknown')
    print(f"✅ Target play type: {target_play_type}")
    
    # Step 4: Filter valid plays
    valid_plays = []
    for player, play_data in turn_state.turn_plays.items():
        if (play_data.get('play_type') == target_play_type and 
            play_data.get('is_valid', True)):
            valid_plays.append((player, play_data))
            print(f"✅ Valid play: {player} with value {play_data.get('play_value')}")
        else:
            print(f"❌ Invalid play: {player} - type: {play_data.get('play_type')}, valid: {play_data.get('is_valid')}")
    
    if not valid_plays:
        print(f"❌ No valid plays found")
        return
    else:
        print(f"✅ Found {len(valid_plays)} valid plays")
    
    # Step 5: Sort plays
    def sort_key(play_tuple):
        player, play_data = play_tuple
        play_value = play_data.get('play_value', 0)
        play_order = turn_state.turn_order.index(player) if player in turn_state.turn_order else 999
        return (-play_value, play_order)
    
    valid_plays.sort(key=sort_key)
    print(f"✅ Sorted plays:")
    for i, (player, play_data) in enumerate(valid_plays):
        print(f"   {i+1}. {player}: value {play_data.get('play_value')}")
    
    # Step 6: Get winner
    winner, winner_play = valid_plays[0]
    print(f"✅ Winner should be: {winner} with value {winner_play.get('play_value')}")
    
    await turn_state.on_exit()


async def main():
    """Run all investigations"""
    await trace_bug()
    await test_winner_logic_isolated()


if __name__ == "__main__":
    asyncio.run(main())