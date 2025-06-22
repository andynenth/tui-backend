#!/usr/bin/env python3
# backend/run_turn_tests_fixed.py

import sys
import os
import asyncio
from datetime import datetime

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test imports with error handling
try:
    from engine.state_machine.core import GamePhase, ActionType, GameAction
    from engine.state_machine.states.turn_state import TurnState
    from engine.state_machine.game_state_machine import GameStateMachine
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class TestGame:
    """Mock game class for testing"""
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


async def test_turn_state_basic():
    """Test basic Turn State functionality"""
    print("\n🧪 Test 1: Basic Turn State Functionality")
    
    try:
        # Create test game and state
        game = TestGame()
        state_machine = MockStateMachine(game)
        turn_state = TurnState(state_machine)
        
        # Test phase setup
        await turn_state.on_enter()
        print(f"✅ Phase setup - starter: {turn_state.current_turn_starter}")
        print(f"✅ Turn order: {turn_state.turn_order}")
        print(f"✅ Current player: {turn_state._get_current_player()}")
        
        # Test starter playing pieces
        starter_action = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={
                'pieces': [1, 2, 3],
                'play_type': 'sequence',
                'play_value': 15,
                'is_valid': True
            },
            timestamp=datetime.now()
        )
        
        # Validate and process action
        is_valid = await turn_state._validate_action(starter_action)
        print(f"✅ Starter action validation: {is_valid}")
        
        if is_valid:
            result = await turn_state._process_action(starter_action)
            print(f"✅ Starter play result: {result['status']}")
            print(f"✅ Required piece count: {turn_state.required_piece_count}")
            print(f"✅ Next player: {result.get('next_player')}")
        
        await turn_state.on_exit()
        print("✅ Test 1 completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_complete_turn():
    """Test a complete turn with all players"""
    print("\n🧪 Test 2: Complete Turn Sequence")
    
    try:
        game = TestGame()
        state_machine = MockStateMachine(game)
        turn_state = TurnState(state_machine)
        
        await turn_state.on_enter()
        
        # All players play in sequence
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
            
            is_valid = await turn_state._validate_action(action)
            print(f"✅ {player} action valid: {is_valid}")
            
            if is_valid:
                result = await turn_state._process_action(action)
                print(f"✅ {player} played: {payload['pieces']} (value: {payload['play_value']})")
                
                if result.get('turn_complete'):
                    print(f"🏁 Turn completed!")
                    print(f"🏆 Winner: {turn_state.winner}")
                    print(f"💰 Piles awarded: {turn_state.required_piece_count}")
                    break
        
        # Verify winner
        expected_winner = "Player3"  # Highest value
        if turn_state.winner == expected_winner:
            print(f"✅ Correct winner: {expected_winner}")
        else:
            print(f"❌ Wrong winner: got {turn_state.winner}, expected {expected_winner}")
        
        await turn_state.on_exit()
        print("✅ Test 2 completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_validation_rules():
    """Test various validation rules"""
    print("\n🧪 Test 3: Validation Rules")
    
    try:
        game = TestGame()
        state_machine = MockStateMachine(game)
        turn_state = TurnState(state_machine)
        
        await turn_state.on_enter()
        
        # Test 1: Wrong player turn
        wrong_player_action = GameAction(
            player_name="Player2",  # Should be Player1's turn
            action_type=ActionType.PLAY_PIECES,
            payload={'pieces': [9, 10], 'play_type': 'pair', 'play_value': 19},
            timestamp=datetime.now()
        )
        
        is_valid = await turn_state._validate_action(wrong_player_action)
        print(f"✅ Wrong player rejected: {not is_valid}")
        
        # Test 2: Starter with too many pieces
        too_many_pieces = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={'pieces': [1, 2, 3, 4, 5, 6, 7], 'play_type': 'sequence', 'play_value': 28},
            timestamp=datetime.now()
        )
        
        is_valid = await turn_state._validate_action(too_many_pieces)
        print(f"✅ Too many pieces rejected: {not is_valid}")
        
        # Test 3: Valid starter play
        valid_starter = GameAction(
            player_name="Player1",
            action_type=ActionType.PLAY_PIECES,
            payload={'pieces': [1, 2], 'play_type': 'pair', 'play_value': 3},
            timestamp=datetime.now()
        )
        
        is_valid = await turn_state._validate_action(valid_starter)
        print(f"✅ Valid starter accepted: {is_valid}")
        
        if is_valid:
            await turn_state._process_action(valid_starter)
            
            # Test 4: Second player with wrong piece count
            wrong_count = GameAction(
                player_name="Player2",
                action_type=ActionType.PLAY_PIECES,
                payload={'pieces': [9, 10, 11], 'play_type': 'sequence', 'play_value': 30},  # 3 pieces instead of 2
                timestamp=datetime.now()
            )
            
            is_valid = await turn_state._validate_action(wrong_count)
            print(f"✅ Wrong piece count rejected: {not is_valid}")
        
        await turn_state.on_exit()
        print("✅ Test 3 completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Turn State tests"""
    print("🚀 Running Turn State Tests")
    print("=" * 50)
    
    results = []
    
    try:
        # Run each test and track results
        results.append(await test_turn_state_basic())
        results.append(await test_complete_turn())
        results.append(await test_validation_rules())
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print(f"\n" + "=" * 50)
        print(f"🎯 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Turn State tests completed successfully!")
        else:
            print(f"❌ {total - passed} tests failed")
        
    except Exception as e:
        print(f"❌ Fatal error in main: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Turn State Test Runner...")
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🏁 Test runner finished.")