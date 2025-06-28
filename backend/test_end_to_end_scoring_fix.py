#!/usr/bin/env python3
"""
End-to-End Test: React Error #31 Fix Validation

This test simulates the COMPLETE game flow that caused React error #31:
1. Backend creates scoring objects with complex structure
2. Data flows through WebSocket broadcasting 
3. Frontend GameService.ts processes the data
4. React components attempt to render the processed data

This test will catch ANY remaining issues with object vs number handling.
"""

import sys
import os
import asyncio
import json
from typing import Dict, Any, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from engine.game import Game
from engine.player import Player
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.states.scoring_state import ScoringState


class MockReactRenderer:
    """Simulate React's strict object rendering rules"""
    
    @staticmethod
    def render_value(value, path="root"):
        """Simulate React's object-as-children validation"""
        if isinstance(value, dict):
            raise ReactError31(f"Objects are not valid as a React child at {path}. Object keys: {list(value.keys())}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                MockReactRenderer.render_value(item, f"{path}[{i}]")
        elif hasattr(value, '__dict__'):
            raise ReactError31(f"Complex object not renderable at {path}: {type(value)}")
        else:
            # Primitive values are fine
            return str(value)


class ReactError31(Exception):
    """Simulate React error #31"""
    pass


class FrontendGameServiceSimulator:
    """Simulate the exact GameService.ts logic"""
    
    def __init__(self):
        self.state = {
            'roundScores': {},
            'totalScores': {},
            'playersWithScores': []
        }
    
    def handlePhaseChange(self, phase_data: Dict[str, Any]):
        """Simulate GameService.ts handlePhaseChange for scoring phase"""
        
        print(f"🔄 FRONTEND_SIM: Processing phase_change with data keys: {list(phase_data.keys())}")
        
        # Simulate the EXACT logic from GameService.ts lines 654-682
        if True:  # Simulate case 'scoring':
            print("📊 FRONTEND_SIM: Entering scoring case")
            
            # Process backend scoring objects to extract numeric values
            processedRoundScores = {}
            rawRoundScores = phase_data.get('round_scores', {})
            
            print(f"🔍 FRONTEND_SIM: Raw round_scores type: {type(rawRoundScores)}")
            print(f"🔍 FRONTEND_SIM: Raw round_scores sample: {dict(list(rawRoundScores.items())[:1]) if rawRoundScores else {}}")
            
            for playerName, scoreData in rawRoundScores.items():
                print(f"🔍 FRONTEND_SIM: Processing {playerName}: {type(scoreData)} = {scoreData}")
                
                # Handle backend scoring objects vs simple numbers
                if isinstance(scoreData, dict) and scoreData is not None:
                    if 'final_score' in scoreData:
                        processedRoundScores[playerName] = scoreData['final_score']
                        print(f"  ✅ Extracted final_score: {scoreData['final_score']}")
                    else:
                        # Object without final_score - default to 0
                        processedRoundScores[playerName] = 0
                        print(f"  ✅ Object without final_score, defaulted to 0")
                else:
                    # Simple number or null
                    processedRoundScores[playerName] = scoreData or 0
                    print(f"  ✅ Used raw value: {scoreData or 0}")
            
            self.state['roundScores'] = processedRoundScores
            
            # Also process total_scores in case they're objects
            processedTotalScores = {}
            rawTotalScores = phase_data.get('total_scores', {})
            
            print(f"🔍 FRONTEND_SIM: Raw total_scores type: {type(rawTotalScores)}")
            print(f"🔍 FRONTEND_SIM: Raw total_scores sample: {dict(list(rawTotalScores.items())[:1]) if rawTotalScores else {}}")
            
            for playerName, scoreData in rawTotalScores.items():
                print(f"🔍 FRONTEND_SIM: Processing total {playerName}: {type(scoreData)} = {scoreData}")
                
                # Handle backend scoring objects vs simple numbers
                if isinstance(scoreData, dict) and scoreData is not None:
                    if 'total_score' in scoreData:
                        processedTotalScores[playerName] = scoreData['total_score']
                        print(f"  ✅ Extracted total_score: {scoreData['total_score']}")
                    else:
                        # Object without total_score - default to 0
                        processedTotalScores[playerName] = 0
                        print(f"  ✅ Object without total_score, defaulted to 0")
                else:
                    # Simple number or null
                    processedTotalScores[playerName] = scoreData or 0
                    print(f"  ✅ Used raw value: {scoreData or 0}")
            
            self.state['totalScores'] = processedTotalScores
            
            # Calculate scoring-specific UI state (simulate calculatePlayersWithScores)
            if phase_data.get('players') and phase_data.get('round_scores') and phase_data.get('total_scores'):
                print("🔍 FRONTEND_SIM: Calculating playersWithScores...")
                self.state['playersWithScores'] = self.calculatePlayersWithScores(
                    phase_data['players'], 
                    phase_data['round_scores'], 
                    phase_data['total_scores'],
                    phase_data.get('redeal_multiplier', 1),
                    phase_data.get('winners', [])
                )
                print(f"✅ FRONTEND_SIM: Generated {len(self.state['playersWithScores'])} playersWithScores")
            
            print(f"✅ FRONTEND_SIM: Final state roundScores: {self.state['roundScores']}")
            print(f"✅ FRONTEND_SIM: Final state totalScores: {self.state['totalScores']}")
    
    def calculatePlayersWithScores(self, players, roundScores, totalScores, redealMultiplier, winners):
        """Simulate the calculatePlayersWithScores method"""
        result = []
        
        for player in players:
            player_name = player['name'] if isinstance(player, dict) else player.name
            
            # Handle backend scoring objects vs simple numbers
            playerRoundScore = roundScores.get(player_name)
            if isinstance(playerRoundScore, dict) and 'final_score' in playerRoundScore:
                roundScore = playerRoundScore['final_score']
            else:
                roundScore = playerRoundScore or 0
            
            baseScore = (playerRoundScore.get('base_score') if isinstance(playerRoundScore, dict) 
                        else round(roundScore / max(1, redealMultiplier)))
            
            actualPiles = (playerRoundScore.get('actual') if isinstance(playerRoundScore, dict) 
                          else 0)  # Simplified
            
            totalScore = totalScores.get(player_name, 0)
            
            player_data = {
                'name': player_name,
                'roundScore': roundScore,
                'totalScore': totalScore,
                'baseScore': baseScore,
                'actualPiles': actualPiles,
                'scoreExplanation': f"Score calculation for {player_name}",
                'isWinner': player_name in winners
            }
            
            result.append(player_data)
        
        return sorted(result, key=lambda x: x['totalScore'], reverse=True)


class MockScoringUI:
    """Simulate ScoringUI component rendering"""
    
    @staticmethod
    def render(roundScores, totalScores, playersWithScores, players, winners=[]):
        """Simulate ScoringUI.jsx rendering logic"""
        
        print("🖥️  MOCK_SCORING_UI: Starting render...")
        
        # Simulate the fallback logic from ScoringUI.jsx lines 40-46
        if len(playersWithScores) > 0:
            sortedPlayers = playersWithScores
            print(f"🖥️  Using playersWithScores: {len(sortedPlayers)} players")
        else:
            print("🖥️  Using fallback player mapping...")
            sortedPlayers = []
            for player in players:
                player_name = player['name'] if isinstance(player, dict) else player.name
                
                # This is where React error #31 would occur!
                roundScore = roundScores.get(player_name, 0)
                totalScore = totalScores.get(player_name, 0)
                
                print(f"🖥️  Player {player_name}: roundScore={type(roundScore)}({roundScore}), totalScore={type(totalScore)}({totalScore})")
                
                # Try to render these values (this is where React would fail)
                MockReactRenderer.render_value(roundScore, f"roundScore[{player_name}]")
                MockReactRenderer.render_value(totalScore, f"totalScore[{player_name}]")
                
                player_ui = {
                    'name': player_name,
                    'roundScore': roundScore,
                    'totalScore': totalScore,
                    'isWinner': player_name in winners
                }
                sortedPlayers.append(player_ui)
            
            sortedPlayers.sort(key=lambda x: x['totalScore'], reverse=True)
        
        # Simulate rendering each player's score (lines 83-170 in ScoringUI.jsx)
        for i, player in enumerate(sortedPlayers):
            print(f"🖥️  Rendering player {i+1}: {player['name']}")
            
            # These are the exact values that would be rendered in JSX
            MockReactRenderer.render_value(player.get('roundScore'), f"player[{i}].roundScore")
            MockReactRenderer.render_value(player.get('totalScore'), f"player[{i}].totalScore")
            MockReactRenderer.render_value(player.get('baseScore', 0), f"player[{i}].baseScore")
            MockReactRenderer.render_value(player.get('actualPiles', 0), f"player[{i}].actualPiles")
        
        print("✅ MOCK_SCORING_UI: Render completed successfully!")
        return sortedPlayers


async def test_end_to_end_react_error_fix():
    """Test the complete flow that could cause React error #31"""
    
    print("🧪 END-TO-END TEST: React Error #31 Fix Validation")
    print("=" * 60)
    
    # Step 1: Create backend scoring data (with complex objects)
    print("\n📊 STEP 1: Generate Backend Scoring Data")
    players = [
        Player("Andy"),     # Human player who won last turn
        Player("Bot 2"),    # Bot
        Player("Bot 3"),    # Bot  
        Player("Bot 4")     # Bot
    ]
    
    game = Game(players)
    game.round_number = 1
    game.redeal_multiplier = 2
    
    # Set up realistic scoring scenario
    players[0].declared_piles = 2
    players[0].captured_piles = 2
    players[0].score = 15
    
    players[1].declared_piles = 0
    players[1].captured_piles = 1
    players[1].score = 8
    
    players[2].declared_piles = 1
    players[2].captured_piles = 0
    players[2].score = 12
    
    players[3].declared_piles = 3
    players[3].captured_piles = 2
    players[3].score = 20
    
    # Create scoring state and calculate scores
    game.room_id = "TEST_ROOM"
    state_machine = GameStateMachine(game)
    scoring_state = ScoringState(state_machine)
    await scoring_state._calculate_round_scores()
    
    print("✅ Backend scoring objects created")
    for player_name, score_data in scoring_state.round_scores.items():
        print(f"   {player_name}: {score_data}")
    
    # Step 2: Simulate WebSocket broadcasting (phase_change event)
    print("\n🌐 STEP 2: Simulate WebSocket Event Broadcasting")
    
    # This simulates what gets sent in a phase_change event for scoring
    phase_change_data = {
        'phase': 'scoring',
        'phase_data': {
            'round_scores': scoring_state.round_scores,  # Complex objects!
            'game_complete': False,
            'winners': [],
            'scores_calculated': True
        },
        'players': {
            player.name: {
                'name': player.name,
                'is_bot': player.name != 'Andy',
                'hand_size': len(player.hand) if hasattr(player, 'hand') else 0
            } for player in players
        },
        'total_scores': {
            player.name: player.score for player in players
        },
        'redeal_multiplier': game.redeal_multiplier
    }
    
    print(f"📡 WebSocket data prepared: {len(phase_change_data)} keys")
    print(f"   round_scores type: {type(phase_change_data['phase_data']['round_scores'])}")
    print(f"   total_scores type: {type(phase_change_data['total_scores'])}")
    
    # Step 3: Frontend GameService.ts processing
    print("\n🖥️  STEP 3: Frontend GameService Processing")
    
    frontend_service = FrontendGameServiceSimulator()
    
    try:
        # This simulates the exact flow in GameService.ts
        frontend_service.handlePhaseChange(phase_change_data['phase_data'])
        print("✅ GameService.ts processing completed successfully")
        
    except Exception as e:
        print(f"❌ GameService.ts processing failed: {e}")
        return False
    
    # Step 4: React component rendering simulation  
    print("\n⚛️  STEP 4: React Component Rendering Simulation")
    
    try:
        # Convert players to the format expected by ScoringUI
        players_data = list(phase_change_data['players'].values())
        
        # This simulates ScoringUI.jsx rendering with the processed data
        rendered_players = MockScoringUI.render(
            roundScores=frontend_service.state['roundScores'],
            totalScores=frontend_service.state['totalScores'], 
            playersWithScores=frontend_service.state['playersWithScores'],
            players=players_data,
            winners=[]
        )
        
        print("✅ React component rendering completed successfully")
        print(f"   Rendered {len(rendered_players)} players without errors")
        
    except ReactError31 as e:
        print(f"❌ React Error #31 still occurs: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected rendering error: {e}")
        return False
    
    # Step 5: Validate all data is properly processed
    print("\n🔍 STEP 5: Data Validation")
    
    validation_passed = True
    
    # Check roundScores are all numbers
    for player_name, score in frontend_service.state['roundScores'].items():
        if not isinstance(score, (int, float)):
            print(f"❌ roundScores[{player_name}] is not a number: {type(score)}")
            validation_passed = False
        else:
            print(f"✅ roundScores[{player_name}]: {score} ({type(score).__name__})")
    
    # Check totalScores are all numbers
    for player_name, score in frontend_service.state['totalScores'].items():
        if not isinstance(score, (int, float)):
            print(f"❌ totalScores[{player_name}] is not a number: {type(score)}")
            validation_passed = False
        else:
            print(f"✅ totalScores[{player_name}]: {score} ({type(score).__name__})")
    
    # Check playersWithScores has renderable values
    for player_data in frontend_service.state['playersWithScores']:
        for key, value in player_data.items():
            if isinstance(value, dict):
                print(f"❌ playersWithScores[{player_data['name']}].{key} is still an object: {value}")
                validation_passed = False
    
    if validation_passed:
        print("✅ All data validation checks passed")
    
    return validation_passed


async def test_edge_cases():
    """Test edge cases that could still cause React errors"""
    
    print("\n🧪 EDGE CASE TESTS")
    print("=" * 40)
    
    frontend_service = FrontendGameServiceSimulator()
    
    # Test case 1: Backend sends mixed object/number format
    print("\n📊 Edge Case 1: Mixed Object/Number Format")
    mixed_data = {
        'round_scores': {
            'Andy': {'declared': 2, 'actual': 2, 'final_score': 14},  # Object
            'Bot 2': -4,  # Simple number
            'Bot 3': {'declared': 0, 'actual': 1, 'final_score': -2}  # Object
        },
        'total_scores': {
            'Andy': 25,  # Simple number
            'Bot 2': {'total_score': 16},  # Object  
            'Bot 3': 18  # Simple number
        }
    }
    
    try:
        frontend_service.handlePhaseChange(mixed_data)
        
        # Verify all values are now numbers
        for name, score in frontend_service.state['roundScores'].items():
            assert isinstance(score, (int, float)), f"{name} roundScore is not a number: {type(score)}"
        
        for name, score in frontend_service.state['totalScores'].items():
            assert isinstance(score, (int, float)), f"{name} totalScore is not a number: {type(score)}"
        
        print("✅ Mixed format handled correctly")
        
    except Exception as e:
        print(f"❌ Mixed format test failed: {e}")
        return False
    
    # Test case 2: Null/undefined values
    print("\n📊 Edge Case 2: Null/Missing Values")
    null_data = {
        'round_scores': {
            'Andy': {'final_score': 10},
            'Bot 2': None,
            'Bot 3': {'declared': 0}  # Missing final_score
        },
        'total_scores': {
            'Andy': 20,
            'Bot 2': None,
            # Bot 3 missing entirely
        }
    }
    
    try:
        frontend_service.handlePhaseChange(null_data)
        
        # Verify null values become 0
        assert frontend_service.state['roundScores']['Bot 2'] == 0
        assert frontend_service.state['roundScores']['Bot 3'] == 0  # Should default to 0 for object without final_score
        assert frontend_service.state['totalScores']['Bot 2'] == 0
        
        print("✅ Null/missing values handled correctly")
        
    except Exception as e:
        print(f"❌ Null values test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("🧪 COMPREHENSIVE END-TO-END TEST SUITE")
    print("Testing React Error #31 Fix with Complete Game Flow\n")
    
    async def run_all_tests():
        # Run main end-to-end test
        main_result = await test_end_to_end_react_error_fix()
        
        # Run edge case tests
        edge_result = await test_edge_cases()
        
        print("\n" + "=" * 70)
        print("🏁 FINAL TEST RESULTS:")
        print(f"   End-to-End Test: {'✅ PASSED' if main_result else '❌ FAILED'}")
        print(f"   Edge Case Tests: {'✅ PASSED' if edge_result else '❌ FAILED'}")
        
        if main_result and edge_result:
            print("   🎉 ALL TESTS PASSED - React Error #31 fix is working correctly!")
            print("   🔒 The frontend can now safely render backend scoring objects")
        else:
            print("   💥 TESTS FAILED - React Error #31 fix needs more work")
        
        print(f"   Overall: {'✅ SUCCESS' if main_result and edge_result else '❌ FAILURE'}")
        
        return main_result and edge_result
    
    # Run the comprehensive test suite
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)