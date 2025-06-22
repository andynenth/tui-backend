#!/usr/bin/env python3
# backend/test_fix.py

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


async def test_fixed_turn():
    """Test the exact scenario that was failing"""
    print("🧪 TESTING THE FIX")
    print("=" * 50)
    
    # Setup
    game = TestGame()
    state_machine = MockStateMachine(game)
    turn_state = TurnState(state_machine)
    
    await turn_state.on_enter()
    
    # The exact same plays from the failing test
    plays = [
        ("Player1", {'pieces': [1, 2], 'play_type': 'pair', 'play_value': 10}),
        ("Player2", {'pieces': [9, 10], 'play_type': 'pair', 'play_value': 15}),
        ("Player3", {'pieces': [17, 18], 'play_type': 'pair', 'play_value': 20}),  # Should win
        ("Player4", {'pieces': [25, 26], 'play_type': 'pair', 'play_value': 8})
    ]
    
    for i, (player, payload) in enumerate(plays):
        action = GameAction(
            player_name=player,
            action_type=ActionType.PLAY_PIECES,
            payload=payload,
            timestamp=datetime.now()
        )
        
        result = await turn_state._process_action(action)
        print(f"✅ {player} played: {payload['pieces']} (value: {payload['play_value']})")
        
        if result.get('turn_complete'):
            print(f"🏁 Turn completed!")
            break
    
    # Check the results AFTER the turn is complete
    print(f"\n🔍 RESULTS AFTER TURN COMPLETION:")
    print(f"✅ Turn complete: {turn_state.turn_complete}")
    print(f"✅ Winner: {turn_state.winner}")
    print(f"✅ Turn plays preserved: {len(turn_state.turn_plays)} plays")
    print(f"✅ Piles awarded: {turn_state.required_piece_count if turn_state.winner else 0}")
    
    # Verify the expected winner
    expected_winner = "Player3"
    if turn_state.winner == expected_winner:
        print(f"🎉 SUCCESS! Correct winner: {expected_winner}")
        success = True
    else:
        print(f"❌ FAILED! Got {turn_state.winner}, expected {expected_winner}")
        success = False
    
    # Check phase data
    phase_data = turn_state.phase_data
    print(f"\n🔍 PHASE DATA:")
    print(f"✅ turn_complete: {phase_data.get('turn_complete')}")
    print(f"✅ winner: {phase_data.get('winner')}")
    print(f"✅ piles_won: {phase_data.get('piles_won')}")
    print(f"✅ next_turn_starter: {phase_data.get('next_turn_starter')}")
    
    # Test manual next turn start
    print(f"\n🧪 Testing manual next turn start...")
    can_start = await turn_state.start_next_turn_if_needed()
    print(f"✅ Next turn started: {can_start}")
    
    if can_start:
        print(f"✅ New turn starter: {turn_state.current_turn_starter}")
        print(f"✅ Turn reset properly: turn_complete = {turn_state.turn_complete}")
    
    await turn_state.on_exit()
    
    return success


async def main():
    success = await test_fixed_turn()
    if success:
        print(f"\n🎉 FIX VERIFICATION SUCCESSFUL!")
        print(f"The bug has been resolved.")
    else:
        print(f"\n❌ FIX VERIFICATION FAILED!")
        print(f"The bug still exists.")


if __name__ == "__main__":
    asyncio.run(main())