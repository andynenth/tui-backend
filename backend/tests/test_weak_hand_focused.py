"""
Focused Unit Tests for _deal_weak_hand Algorithm

This test focuses specifically on testing the _deal_weak_hand method
by creating minimal dependencies and mocking what's needed.

Key Question: Does the algorithm fail when there aren't enough weak pieces?
"""

import unittest
import random
import sys
import os
from unittest.mock import MagicMock, patch

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock all the missing engine modules
mock_modules = [
    'engine.ai',
    'engine.rules', 
    'engine.scoring',
    'engine.turn_resolution',
    'engine.win_conditions'
]

for module in mock_modules:
    sys.modules[module] = MagicMock()

# Mock specific imports that the game module needs
sys.modules['engine.rules'].get_play_type = MagicMock()
sys.modules['engine.rules'].get_valid_declares = MagicMock(return_value=[0, 1, 2, 3, 4, 5, 6, 7, 8])
sys.modules['engine.rules'].is_valid_play = MagicMock(return_value=True)
sys.modules['engine.scoring'].calculate_round_scores = MagicMock(return_value={})
sys.modules['engine.turn_resolution'].TurnPlay = MagicMock()
sys.modules['engine.turn_resolution'].resolve_turn = MagicMock()
sys.modules['engine.win_conditions'].WinConditionType = MagicMock()
sys.modules['engine.win_conditions'].WinConditionType.FIRST_TO_REACH_50 = "FIRST_TO_REACH_50"
sys.modules['engine.win_conditions'].get_winners = MagicMock(return_value=[])
sys.modules['engine.win_conditions'].is_game_over = MagicMock(return_value=False)

# Now import the actual modules we need
from engine.player import Player
from engine.piece import Piece
from engine.constants import PIECE_POINTS
from engine.game import Game


class TestWeakHandFocused(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create 4 players for testing
        self.players = [
            Player(f"Player{i+1}", is_bot=(i > 1)) for i in range(4)
        ]
        self.game = Game(self.players)
        
        # Set a fixed seed for reproducible tests
        random.seed(42)
        
    def tearDown(self):
        """Clean up after tests"""
        random.seed()

    def test_deck_composition_verification(self):
        """Verify our understanding of weak vs strong pieces"""
        deck = Piece.build_deck()
        
        # Analyze deck composition
        weak_pieces = [p for p in deck if p.point <= 9]
        strong_pieces = [p for p in deck if p.point > 9]
        
        print(f"\n=== DECK ANALYSIS ===")
        print(f"Total pieces: {len(deck)}")
        print(f"Weak pieces (≤9): {len(weak_pieces)}")
        print(f"Strong pieces (>9): {len(strong_pieces)}")
        
        # List all weak pieces by type and count
        weak_counts = {}
        for piece in weak_pieces:
            if piece.kind not in weak_counts:
                weak_counts[piece.kind] = 0
            weak_counts[piece.kind] += 1
            
        print("Weak pieces breakdown:")
        total_weak = 0
        for kind, count in sorted(weak_counts.items(), key=lambda x: PIECE_POINTS[x[0]], reverse=True):
            print(f"  {kind}: {PIECE_POINTS[kind]} points × {count} = {count} pieces")
            total_weak += count
            
        print(f"Total weak pieces available: {total_weak}")
        print(f"Pieces needed for 1 weak player: 8")
        print(f"Can support {total_weak // 8} weak players maximum")
        
        # Verify our calculation
        self.assertEqual(len(deck), 32)
        expected_weak = 24  # Based on our analysis
        self.assertEqual(len(weak_pieces), expected_weak, 
            f"Expected {expected_weak} weak pieces, found {len(weak_pieces)}")

    def test_production_scenario_single_weak_player(self):
        """Test the exact production scenario: Player 0 gets weak hand"""
        print(f"\n=== PRODUCTION SCENARIO TEST ===")
        
        # Reset game state
        self.game.redeal_multiplier = 1
        
        # Execute the exact production call
        self.game._deal_weak_hand(weak_player_indices=[0], max_weak_points=9, limit=2)
        
        # Verify all players have 8 pieces
        for i, player in enumerate(self.game.players):
            self.assertEqual(len(player.hand), 8, f"Player {i} should have 8 pieces")
            
        # Check Player 0's hand specifically
        player0_hand = self.game.players[0].hand
        player0_max_points = max(p.point for p in player0_hand)
        player0_strong_pieces = [p for p in player0_hand if p.point > 9]
        
        print(f"Player 0 hand: {[f'{p.kind}({p.point})' for p in player0_hand]}")
        print(f"Player 0 max points: {player0_max_points}")
        print(f"Player 0 strong pieces: {len(player0_strong_pieces)}")
        
        # The critical test: Does Player 0 have only weak pieces?
        self.assertEqual(len(player0_strong_pieces), 0, 
            f"Player 0 should have NO strong pieces, but has: {[f'{p.kind}({p.point})' for p in player0_strong_pieces]}")
        
        # Verify other players have at least one strong piece
        for i in range(1, 4):
            player_hand = self.game.players[i].hand
            strong_pieces = [p for p in player_hand if p.point > 9]
            self.assertGreater(len(strong_pieces), 0, 
                f"Player {i} should have at least one strong piece")
            
        print("✅ Production scenario test PASSED")

    def test_multiple_weak_players_edge_case(self):
        """Test what happens when we need more weak pieces"""
        print(f"\n=== MULTIPLE WEAK PLAYERS TEST ===")
        
        # Test with 3 weak players (3 * 8 = 24 weak pieces needed)
        # We have exactly 24 weak pieces, so this should work
        self.game.redeal_multiplier = 1
        self.game._deal_weak_hand(weak_player_indices=[0, 1, 2], max_weak_points=9, limit=2)
        
        results = []
        for i in range(3):
            player_hand = self.game.players[i].hand
            strong_pieces = [p for p in player_hand if p.point > 9]
            max_points = max(p.point for p in player_hand)
            
            results.append({
                'player': i,
                'strong_count': len(strong_pieces),
                'max_points': max_points,
                'has_weak_hand': len(strong_pieces) == 0
            })
            
            print(f"Player {i}: {len(strong_pieces)} strong pieces, max={max_points}")
            
        # Check how many actually got weak hands
        weak_hand_count = sum(1 for r in results if r['has_weak_hand'])
        print(f"Players with purely weak hands: {weak_hand_count}/3")
        
        if weak_hand_count < 3:
            print("⚠️  Not all players got weak hands - potential algorithm limitation")
            print("This might indicate the algorithm fails under pressure")

    def test_impossible_scenario_all_weak(self):
        """Test impossible scenario: all 4 players need weak hands"""
        print(f"\n=== IMPOSSIBLE SCENARIO TEST ===")
        
        # Try to give all 4 players weak hands (32 weak pieces needed, but only 24 exist)
        self.game.redeal_multiplier = 1
        self.game._deal_weak_hand(weak_player_indices=[0, 1, 2, 3], max_weak_points=9, limit=2)
        
        weak_hand_count = 0
        for i in range(4):
            player_hand = self.game.players[i].hand
            strong_pieces = [p for p in player_hand if p.point > 9]
            
            if len(strong_pieces) == 0:
                weak_hand_count += 1
                print(f"Player {i}: ✅ Pure weak hand")
            else:
                print(f"Player {i}: ❌ Has {len(strong_pieces)} strong pieces")
                
        print(f"Result: {weak_hand_count}/4 players got pure weak hands")
        print("This should be impossible with only 24 weak pieces available")
        
        # The algorithm should handle this gracefully
        # Either by falling back to normal dealing or by giving some players mixed hands
        
    def test_algorithm_consistency_multiple_runs(self):
        """Test algorithm consistency across multiple runs"""
        print(f"\n=== ALGORITHM CONSISTENCY TEST ===")
        
        success_count = 0
        failure_count = 0
        
        for run in range(20):
            # Create fresh game for each run
            fresh_players = [Player(f"Player{i+1}") for i in range(4)]
            fresh_game = Game(fresh_players)
            fresh_game.redeal_multiplier = 1
            
            # Use production parameters
            fresh_game._deal_weak_hand(weak_player_indices=[0], max_weak_points=9, limit=2)
            
            # Check if Player 0 got a weak hand
            player0_hand = fresh_game.players[0].hand
            strong_pieces = [p for p in player0_hand if p.point > 9]
            
            if len(strong_pieces) == 0:
                success_count += 1
            else:
                failure_count += 1
                print(f"  Run {run + 1}: FAILED - Player 0 has {len(strong_pieces)} strong pieces")
                
        print(f"Results over 20 runs:")
        print(f"  Successes: {success_count}")
        print(f"  Failures: {failure_count}")
        print(f"  Success rate: {success_count/20*100:.1f}%")
        
        if failure_count > 0:
            print(f"🚨 ALGORITHM ISSUE DETECTED!")
            print(f"The _deal_weak_hand function failed {failure_count} times out of 20")
            print(f"This confirms there is a bug in the algorithm")
            
            # This is the key assertion - algorithm should be 100% reliable
            self.fail(f"Algorithm failed {failure_count}/20 times. "
                     f"With 24 weak pieces available and only 8 needed, "
                     f"it should NEVER fail to create a weak hand.")
        else:
            print(f"✅ Algorithm appears to work correctly")
            
    def test_detailed_algorithm_analysis(self):
        """Deep dive into what the algorithm actually does"""
        print(f"\n=== DETAILED ALGORITHM ANALYSIS ===")
        
        # Look at the source code behavior
        self.game.redeal_multiplier = 1
        
        # Create deck and categorize pieces manually to understand the logic
        deck = Piece.build_deck()
        weak_pieces = [p for p in deck if p.point <= 9]
        strong_pieces = [p for p in deck if p.point > 9]
        
        print(f"Available weak pieces: {len(weak_pieces)}")
        print(f"Needed for Player 0: 8")
        print(f"Remaining after Player 0: {len(weak_pieces) - 8}")
        print(f"Non-weak players need strong pieces: 3 players")
        print(f"Available strong pieces: {len(strong_pieces)}")
        
        # The algorithm should:
        # 1. Give Player 0 8 weak pieces (16 weak pieces remain)
        # 2. Give other players at least 1 strong piece each (5 strong pieces remain)
        # 3. Fill remaining slots with any available pieces
        
        if len(weak_pieces) >= 8 and len(strong_pieces) >= 3:
            print("✅ Mathematical requirements are met")
            print("Algorithm SHOULD be able to create the desired distribution")
        else:
            print("❌ Mathematical requirements NOT met")
            print("Algorithm failure would be expected")
            
        # Now test it
        self.game._deal_weak_hand(weak_player_indices=[0], max_weak_points=9, limit=2)
        
        # Analyze the actual result
        player0_hand = self.game.players[0].hand
        strong_in_p0 = [p for p in player0_hand if p.point > 9]
        
        if len(strong_in_p0) == 0:
            print("✅ Algorithm succeeded as expected")
        else:
            print(f"❌ Algorithm failed despite sufficient pieces!")
            print(f"Player 0 received {len(strong_in_p0)} strong pieces:")
            for piece in strong_in_p0:
                print(f"  {piece.kind}({piece.point})")
            print("This indicates a bug in the algorithm logic")


if __name__ == '__main__':
    unittest.main(verbosity=2)