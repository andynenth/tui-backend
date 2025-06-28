#!/usr/bin/env python3
"""
Test Case: Backend Scoring Object Format for Frontend

This test validates that the backend sends the correct scoring object format
to the frontend during the scoring phase, and that the frontend can properly
handle both object and numeric formats.

Expected backend format:
{
  "declared": int,
  "actual": int, 
  "base_score": int,
  "multiplier": int,
  "final_score": int,
  "total_score": int
}
"""

import sys
import os
import asyncio
import json
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from engine.game import Game
from engine.player import Player
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.states.scoring_state import ScoringState


async def test_scoring_object_format():
    """Test that backend produces correct scoring object format for frontend"""
    
    print("🧪 Testing Backend Scoring Object Format")
    print("=" * 50)
    
    # Create test game with 4 players
    players = [
        Player("Andy"),     # Human player
        Player("Bot 2"),    # Bot
        Player("Bot 3"),    # Bot  
        Player("Bot 4")     # Bot
    ]
    
    game = Game(players)
    
    # Set up test scenario
    game.round_number = 1
    game.redeal_multiplier = 2  # Test with multiplier
    
    # Set player declarations and captured piles for testing
    players[0].declared_piles = 2    # Andy declared 2
    players[0].captured_piles = 2    # Andy got 2 (perfect match)
    players[0].score = 10           # Previous score
    
    players[1].declared_piles = 0    # Bot 2 declared 0
    players[1].captured_piles = 1    # Bot 2 got 1 (broke zero)
    players[1].score = 5            # Previous score
    
    players[2].declared_piles = 3    # Bot 3 declared 3
    players[2].captured_piles = 1    # Bot 3 got 1 (missed by 2)
    players[2].score = 8            # Previous score
    
    players[3].declared_piles = 0    # Bot 4 declared 0
    players[3].captured_piles = 0    # Bot 4 got 0 (perfect zero)
    players[3].score = 12           # Previous score
    
    # Create state machine and scoring state
    game.room_id = "TEST_ROOM"  # Set room_id on game object
    state_machine = GameStateMachine(game)
    scoring_state = ScoringState(state_machine)
    
    print("📊 Test Setup:")
    print(f"   Redeal Multiplier: {game.redeal_multiplier}x")
    for player in players:
        print(f"   {player.name}: declared={player.declared_piles}, actual={player.captured_piles}, prev_score={player.score}")
    print()
    
    # Calculate scoring
    await scoring_state._calculate_round_scores()
    
    print("🔍 Backend Scoring Objects:")
    print("-" * 30)
    
    # Validate scoring object format
    expected_fields = {'declared', 'actual', 'base_score', 'multiplier', 'final_score', 'total_score'}
    all_tests_passed = True
    
    for player_name, score_data in scoring_state.round_scores.items():
        print(f"\n{player_name}:")
        print(f"  Raw object: {score_data}")
        
        # Check if it's a dictionary with expected fields
        if not isinstance(score_data, dict):
            print(f"  ❌ ERROR: Expected dict, got {type(score_data)}")
            all_tests_passed = False
            continue
            
        # Validate all expected fields are present
        missing_fields = expected_fields - set(score_data.keys())
        if missing_fields:
            print(f"  ❌ ERROR: Missing fields: {missing_fields}")
            all_tests_passed = False
            
        extra_fields = set(score_data.keys()) - expected_fields
        if extra_fields:
            print(f"  ⚠️  WARNING: Extra fields: {extra_fields}")
            
        # Validate field types
        for field, value in score_data.items():
            if not isinstance(value, (int, float)):
                print(f"  ❌ ERROR: Field '{field}' should be numeric, got {type(value)}: {value}")
                all_tests_passed = False
            else:
                print(f"  ✅ {field}: {value}")
                
        # Validate scoring logic
        expected_base = calculate_expected_base_score(score_data['declared'], score_data['actual'])
        expected_final = expected_base * score_data['multiplier']
        
        if score_data['base_score'] != expected_base:
            print(f"  ❌ ERROR: Base score mismatch. Expected {expected_base}, got {score_data['base_score']}")
            all_tests_passed = False
            
        if score_data['final_score'] != expected_final:
            print(f"  ❌ ERROR: Final score mismatch. Expected {expected_final}, got {score_data['final_score']}")
            all_tests_passed = False
    
    print("\n" + "=" * 50)
    
    # Test JSON serialization (what gets sent to frontend)
    print("🌐 JSON Serialization Test:")
    try:
        json_data = json.dumps(scoring_state.round_scores, indent=2)
        print("✅ Scoring objects are JSON serializable")
        print(f"Sample JSON:\n{json_data[:200]}...")
        
        # Test deserialization 
        deserialized = json.loads(json_data)
        print("✅ JSON can be deserialized")
        
    except Exception as e:
        print(f"❌ ERROR: JSON serialization failed: {e}")
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    
    # Test frontend compatibility simulation
    print("🖥️  Frontend Compatibility Test:")
    
    def simulate_frontend_processing(backend_scores: Dict[str, Any]) -> Dict[str, float]:
        """Simulate how frontend processes backend scoring objects"""
        processed_scores = {}
        
        for player_name, score_data in backend_scores.items():
            # Simulate the frontend logic from GameService.ts
            if isinstance(score_data, dict) and 'final_score' in score_data:
                processed_scores[player_name] = score_data['final_score']
            else:
                processed_scores[player_name] = score_data or 0
                
        return processed_scores
    
    try:
        frontend_scores = simulate_frontend_processing(scoring_state.round_scores)
        print("✅ Frontend processing simulation successful")
        print(f"   Processed scores: {frontend_scores}")
        
        # Validate all values are numeric
        for player, score in frontend_scores.items():
            if not isinstance(score, (int, float)):
                print(f"❌ ERROR: Frontend score for {player} is not numeric: {type(score)}")
                all_tests_passed = False
                
    except Exception as e:
        print(f"❌ ERROR: Frontend processing simulation failed: {e}")
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    print(f"🏁 Overall Test Result: {'✅ PASSED' if all_tests_passed else '❌ FAILED'}")
    
    return all_tests_passed


def calculate_expected_base_score(declared: int, actual: int) -> int:
    """Calculate expected base score using game rules"""
    if declared == 0:
        if actual == 0:
            return 3  # Perfect zero declaration
        else:
            return -actual  # Broke zero declaration
    else:
        if actual == declared:
            return declared + 5  # Perfect prediction
        else:
            return -abs(declared - actual)  # Missed target penalty


async def test_edge_cases():
    """Test edge cases for scoring object format"""
    
    print("\n🧪 Testing Edge Cases")
    print("=" * 50)
    
    # Test with zero multiplier
    print("📊 Test Case: Zero Multiplier")
    players = [Player("TestPlayer")]
    game = Game(players)
    game.redeal_multiplier = 0  # Edge case
    
    players[0].declared_piles = 1
    players[0].captured_piles = 1
    players[0].score = 0
    
    game.room_id = "TEST_ROOM"  # Set room_id on game object
    state_machine = GameStateMachine(game)
    scoring_state = ScoringState(state_machine)
    await scoring_state._calculate_round_scores()
    
    score_data = scoring_state.round_scores["TestPlayer"]
    expected_final = score_data['base_score'] * 0  # Should be 0
    
    if score_data['final_score'] == expected_final:
        print("✅ Zero multiplier handled correctly")
    else:
        print(f"❌ Zero multiplier error: expected {expected_final}, got {score_data['final_score']}")
        return False
    
    # Test with large multiplier
    print("\n📊 Test Case: Large Multiplier")
    game.redeal_multiplier = 5  # Large multiplier
    await scoring_state._calculate_round_scores()
    
    score_data = scoring_state.round_scores["TestPlayer"]
    expected_final = score_data['base_score'] * 5
    
    if score_data['final_score'] == expected_final:
        print("✅ Large multiplier handled correctly")
    else:
        print(f"❌ Large multiplier error: expected {expected_final}, got {score_data['final_score']}")
        return False
    
    # Test with negative scores
    print("\n📊 Test Case: Negative Scores")
    players[0].declared_piles = 5
    players[0].captured_piles = 0  # Big miss
    game.redeal_multiplier = 2
    await scoring_state._calculate_round_scores()
    
    score_data = scoring_state.round_scores["TestPlayer"]
    if score_data['base_score'] < 0 and score_data['final_score'] < 0:
        print("✅ Negative scores handled correctly")
    else:
        print(f"❌ Negative score error: base={score_data['base_score']}, final={score_data['final_score']}")
        return False
    
    print("✅ All edge cases passed")
    return True


if __name__ == "__main__":
    print("🧪 Backend Scoring Object Format Test Suite")
    print("Testing scoring data format sent from backend to frontend\n")
    
    async def run_all_tests():
        # Run main test
        main_result = await test_scoring_object_format()
        
        # Run edge case tests
        edge_result = await test_edge_cases()
        
        print("\n" + "=" * 60)
        print("🏁 FINAL TEST RESULTS:")
        print(f"   Main Tests: {'✅ PASSED' if main_result else '❌ FAILED'}")
        print(f"   Edge Cases: {'✅ PASSED' if edge_result else '❌ FAILED'}")
        print(f"   Overall: {'✅ ALL TESTS PASSED' if main_result and edge_result else '❌ SOME TESTS FAILED'}")
        
        return main_result and edge_result
    
    # Run the tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)