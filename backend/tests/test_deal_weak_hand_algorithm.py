"""
Comprehensive Unit Tests for _deal_weak_hand Algorithm

This test suite validates whether the _deal_weak_hand function works correctly
or has algorithm failures when dealing with insufficient weak pieces.

Test Parameters Used in Production:
- weak_player_indices=[0] (Player 0 gets weak hand)
- max_weak_points=9 (pieces ≤9 points are "weak")
- limit=2 (max 2 redeals before forcing no redeal)

Deck Composition Analysis:
- Total pieces: 32
- Weak pieces (≤9 points): ELEPHANT_BLACK(9), CHARIOT_BLACK(7), CHARIOT_RED(8), 
  HORSE_BLACK(5), HORSE_RED(6), CANNON_BLACK(3), CANNON_RED(4), 
  SOLDIER_BLACK(1) x5, SOLDIER_RED(2) x5
- Total weak pieces: 2 + 2 + 2 + 2 + 2 + 5 + 5 = 20 pieces
- Strong pieces (>9 points): GENERAL_RED(14), GENERAL_BLACK(13), 
  ADVISOR_RED(12), ADVISOR_BLACK(11), ELEPHANT_RED(10)
- Total strong pieces: 1 + 1 + 2 + 2 + 2 = 8 pieces
- Plus ELEPHANT_BLACK(9) which is considered weak: 8 + 2 = 10 strong pieces
- Wait, ELEPHANT_BLACK(9) ≤ 9, so it's weak, leaving only 10 strong pieces

Actually, let me recalculate:
Strong pieces (>9 points): GENERAL_RED(14), GENERAL_BLACK(13), ADVISOR_RED(12), 
ADVISOR_BLACK(11), ELEPHANT_RED(10)
Count: 1 + 1 + 2 + 2 + 2 = 8 total strong pieces

Weak pieces (≤9 points): ELEPHANT_BLACK(9) x2, CHARIOT_RED(8) x2, CHARIOT_BLACK(7) x2,
HORSE_RED(6) x2, HORSE_BLACK(5) x2, CANNON_RED(4) x2, CANNON_BLACK(3) x2,
SOLDIER_RED(2) x5, SOLDIER_BLACK(1) x5
Count: 2 + 2 + 2 + 2 + 2 + 2 + 2 + 5 + 5 = 24 total weak pieces

Total: 8 strong + 24 weak = 32 pieces ✓

Test Scenarios:
1. Normal case: Player 0 needs 8 weak pieces, we have 24 available → Should work
2. Edge case: Multiple weak players need more weak pieces than available
3. Test with exact production parameters
4. Validate that weak hands actually contain only pieces ≤9 points
"""

import unittest
import random
from unittest.mock import MagicMock, patch
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the missing ai module to avoid import errors
sys.modules['engine.ai'] = MagicMock()

from engine.player import Player
from engine.piece import Piece
from engine.constants import PIECE_POINTS

# Import game after mocking dependencies
from engine.game import Game


class TestDealWeakHandAlgorithm(unittest.TestCase):
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
        # Reset random seed
        random.seed()
        
    def test_deck_composition_analysis(self):
        """Verify our understanding of the deck composition"""
        deck = Piece.build_deck()
        
        # Count total pieces
        self.assertEqual(len(deck), 32, "Deck should have 32 pieces")
        
        # Categorize pieces by strength
        weak_pieces = [p for p in deck if p.point <= 9]
        strong_pieces = [p for p in deck if p.point > 9]
        
        print(f"\n=== DECK COMPOSITION ANALYSIS ===")
        print(f"Total pieces: {len(deck)}")
        print(f"Weak pieces (≤9 points): {len(weak_pieces)}")
        print(f"Strong pieces (>9 points): {len(strong_pieces)}")
        
        # Print weak pieces by type
        weak_by_point = {}
        for piece in weak_pieces:
            if piece.point not in weak_by_point:
                weak_by_point[piece.point] = []
            weak_by_point[piece.point].append(piece.kind)
            
        for point in sorted(weak_by_point.keys(), reverse=True):
            pieces = weak_by_point[point]
            print(f"  {point} points: {pieces} (count: {len(pieces)})")
            
        # Print strong pieces
        strong_by_point = {}
        for piece in strong_pieces:
            if piece.point not in strong_by_point:
                strong_by_point[piece.point] = []
            strong_by_point[piece.point].append(piece.kind)
            
        for point in sorted(strong_by_point.keys(), reverse=True):
            pieces = strong_by_point[point]
            print(f"  {point} points: {pieces} (count: {len(pieces)})")
            
        # Verify our calculations
        self.assertEqual(len(weak_pieces), 24, f"Expected 24 weak pieces, got {len(weak_pieces)}")
        self.assertEqual(len(strong_pieces), 8, f"Expected 8 strong pieces, got {len(strong_pieces)}")
        
    def test_production_parameters_normal_case(self):
        """Test with exact production parameters: weak_player_indices=[0], max_weak_points=9, limit=2"""
        # Reset redeal multiplier to simulate first round
        self.game.redeal_multiplier = 1
        
        # Call with production parameters
        self.game._deal_weak_hand(weak_player_indices=[0], max_weak_points=9, limit=2)
        
        # Verify Player 0 has a weak hand
        player0_hand = self.game.players[0].hand
        self.assertEqual(len(player0_hand), 8, "Player 0 should have 8 pieces")
        
        # Check that all pieces in Player 0's hand are ≤9 points
        for piece in player0_hand:
            self.assertLessEqual(piece.point, 9, 
                f"Player 0 should only have weak pieces, found {piece.kind}({piece.point})")
            
        # Verify other players have at least one strong piece
        for i in range(1, 4):
            player_hand = self.game.players[i].hand
            self.assertEqual(len(player_hand), 8, f"Player {i} should have 8 pieces")
            
            # Check for at least one strong piece
            has_strong = any(p.point > 9 for p in player_hand)
            self.assertTrue(has_strong, 
                f"Player {i} should have at least one strong piece (>9 points)")
            
        print(f"\n=== PRODUCTION PARAMETERS TEST PASSED ===")
        print(f"Player 0 hand: {[f'{p.kind}({p.point})' for p in player0_hand]}")
        print(f"Player 0 max points: {max(p.point for p in player0_hand)}")
        
    def test_insufficient_weak_pieces_scenario(self):
        """Test edge case: multiple players need weak hands but insufficient pieces"""
        # Try to give 3 players weak hands (3 * 8 = 24 pieces needed)
        # We have exactly 24 weak pieces, so this should work
        self.game.redeal_multiplier = 1
        
        self.game._deal_weak_hand(weak_player_indices=[0, 1, 2], max_weak_points=9, limit=2)
        
        # Check players 0, 1, 2 have weak hands
        for i in range(3):
            player_hand = self.game.players[i].hand
            max_points = max(p.point for p in player_hand) if player_hand else 0
            print(f"Player {i} max points: {max_points}")
            
            # They might not all have purely weak hands if we run out of weak pieces
            # The algorithm should handle this gracefully
            
        # Player 3 should definitely have a strong piece since they're not in weak indices
        player3_hand = self.game.players[3].hand
        has_strong = any(p.point > 9 for p in player3_hand)
        self.assertTrue(has_strong, "Player 3 should have at least one strong piece")
            
    def test_extreme_insufficient_weak_pieces(self):
        """Test case where we need more weak pieces than exist"""
        # Try to give all 4 players weak hands (4 * 8 = 32 pieces needed)
        # But we only have 24 weak pieces and 8 strong pieces
        self.game.redeal_multiplier = 1
        
        self.game._deal_weak_hand(weak_player_indices=[0, 1, 2, 3], max_weak_points=9, limit=2)
        
        # This should cause some players to get strong pieces in their "weak" hands
        # Or the algorithm should fall back to normal dealing
        
        total_pieces_dealt = sum(len(p.hand) for p in self.game.players)
        self.assertEqual(total_pieces_dealt, 32, "All 32 pieces should be dealt")
        
        print(f"\n=== EXTREME CASE: ALL PLAYERS WEAK ===")
        for i, player in enumerate(self.game.players):
            max_points = max(p.point for p in player.hand) if player.hand else 0
            weak_count = sum(1 for p in player.hand if p.point <= 9)
            print(f"Player {i}: {len(player.hand)} pieces, max={max_points}, weak_pieces={weak_count}")
            
    def test_redeal_limit_reached(self):
        """Test behavior when redeal limit is reached"""
        # Set multiplier to exceed limit
        self.game.redeal_multiplier = 3  # > limit of 2
        
        # This should call _deal_guaranteed_no_redeal instead
        self.game._deal_weak_hand(weak_player_indices=[0], max_weak_points=9, limit=2)
        
        # All players should have at least one strong piece
        for i, player in enumerate(self.game.players):
            has_strong = any(p.point > 9 for p in player.hand)
            self.assertTrue(has_strong, 
                f"Player {i} should have strong piece when limit exceeded")
                
        print(f"\n=== REDEAL LIMIT TEST ===")
        print(f"Redeal multiplier: {self.game.redeal_multiplier}")
        print("All players should have strong pieces (no weak hands allowed)")
        
    def test_weak_hand_detection_accuracy(self):
        """Test that get_weak_hand_players correctly identifies weak hands"""
        # Deal with known parameters
        self.game.redeal_multiplier = 1
        self.game._deal_weak_hand(weak_player_indices=[0], max_weak_points=9, limit=2)
        
        # Use the game's own weak hand detection
        weak_players = self.game.get_weak_hand_players(include_details=True)
        
        print(f"\n=== WEAK HAND DETECTION TEST ===")
        print(f"Detected weak players: {[p['name'] for p in weak_players]}")
        
        # Player 0 should be detected as weak
        weak_names = [p['name'] for p in weak_players]
        self.assertIn('Player1', weak_names, "Player1 should be detected as weak")
        
        # Verify the detection logic matches our expectation
        for player_info in weak_players:
            if player_info['name'] == 'Player1':
                self.assertLessEqual(player_info['hand_strength'], 9 * 8, 
                    "Weak player should have low hand strength")
                    
    def test_algorithm_edge_case_analysis(self):
        """Deep analysis of potential algorithm failures"""
        print(f"\n=== ALGORITHM EDGE CASE ANALYSIS ===")
        
        # Test multiple scenarios to find potential failures
        scenarios = [
            {"weak_indices": [0], "description": "Single weak player (production)"},
            {"weak_indices": [0, 1], "description": "Two weak players"},
            {"weak_indices": [0, 1, 2], "description": "Three weak players (24 pieces needed)"},
            {"weak_indices": [0, 1, 2, 3], "description": "All players weak (impossible)"},
        ]
        
        for scenario in scenarios:
            print(f"\n--- {scenario['description']} ---")
            
            # Create fresh game
            test_game = Game([Player(f"Player{i+1}") for i in range(4)])
            test_game.redeal_multiplier = 1
            
            try:
                test_game._deal_weak_hand(
                    weak_player_indices=scenario['weak_indices'], 
                    max_weak_points=9, 
                    limit=2
                )
                
                # Analyze results
                total_dealt = sum(len(p.hand) for p in test_game.players)
                weak_players_found = test_game.get_weak_hand_players()
                
                print(f"  Total pieces dealt: {total_dealt}")
                print(f"  Weak players detected: {weak_players_found}")
                print(f"  Expected weak: {[f'Player{i+1}' for i in scenario['weak_indices']]}")
                
                # Check if algorithm succeeded or failed
                expected_weak = set(f'Player{i+1}' for i in scenario['weak_indices'])
                actual_weak = set(weak_players_found)
                
                if expected_weak.issubset(actual_weak):
                    print(f"  Result: ✅ SUCCESS - All expected players have weak hands")
                else:
                    missing = expected_weak - actual_weak
                    print(f"  Result: ⚠️  PARTIAL - Missing weak hands: {missing}")
                    
                    # This might indicate an algorithm limitation
                    if len(scenario['weak_indices']) * 8 > 24:
                        print(f"  Analysis: Expected, not enough weak pieces (need {len(scenario['weak_indices']) * 8}, have 24)")
                    else:
                        print(f"  Analysis: Potential algorithm issue - should have enough weak pieces")
                        
            except Exception as e:
                print(f"  Result: ❌ FAILED - Exception: {e}")
                
    def test_piece_distribution_validation(self):
        """Validate that piece distribution follows deck rules"""
        self.game.redeal_multiplier = 1
        self.game._deal_weak_hand(weak_player_indices=[0], max_weak_points=9, limit=2)
        
        # Collect all dealt pieces
        all_dealt_pieces = []
        for player in self.game.players:
            all_dealt_pieces.extend(player.hand)
            
        # Count by piece type
        piece_counts = {}
        for piece in all_dealt_pieces:
            if piece.kind not in piece_counts:
                piece_counts[piece.kind] = 0
            piece_counts[piece.kind] += 1
            
        print(f"\n=== PIECE DISTRIBUTION VALIDATION ===")
        for piece_kind, count in sorted(piece_counts.items()):
            expected_count = self._get_expected_piece_count(piece_kind)
            status = "✅" if count == expected_count else "❌"
            print(f"  {piece_kind}: {count}/{expected_count} {status}")
            
        # Verify no piece type is over-dealt
        for piece_kind, count in piece_counts.items():
            expected = self._get_expected_piece_count(piece_kind)
            self.assertLessEqual(count, expected, 
                f"Over-dealt {piece_kind}: {count} > {expected}")
                
    def _get_expected_piece_count(self, piece_kind):
        """Get expected count for a piece type based on deck composition"""
        name = piece_kind.split("_")[0]
        if name == "GENERAL":
            return 1
        elif name == "SOLDIER":
            return 5
        else:
            return 2
            
    def test_user_reported_issue_recreation(self):
        """Try to recreate the exact issue reported by the user"""
        print(f"\n=== USER REPORTED ISSUE RECREATION ===")
        print("Testing if algorithm fails when there aren't enough weak pieces...")
        
        # Run the exact production scenario multiple times
        failures = 0
        successes = 0
        
        for iteration in range(10):
            test_game = Game([Player(f"Player{i+1}") for i in range(4)])
            test_game.redeal_multiplier = 1
            
            # Use exact production parameters
            test_game._deal_weak_hand(weak_player_indices=[0], max_weak_points=9, limit=2)
            
            # Check if Player1 actually got a weak hand
            weak_players = test_game.get_weak_hand_players()
            
            if "Player1" in weak_players:
                successes += 1
            else:
                failures += 1
                print(f"  Iteration {iteration + 1}: Player1 did NOT get weak hand")
                
                # Analyze what happened
                player1_hand = test_game.players[0].hand
                strong_pieces = [p for p in player1_hand if p.point > 9]
                print(f"    Player1 strong pieces: {[f'{p.kind}({p.point})' for p in strong_pieces]}")
                
        print(f"\nResults after 10 iterations:")
        print(f"  Successes (weak hand dealt): {successes}")
        print(f"  Failures (no weak hand): {failures}")
        
        if failures > 0:
            print(f"  🚨 ALGORITHM ISSUE CONFIRMED: {failures}/10 failures")
            print(f"  The user's analysis appears to be CORRECT")
        else:
            print(f"  ✅ Algorithm appears to work correctly")
            print(f"  The user's analysis appears to be INCORRECT")
            
        # Even 1 failure suggests the algorithm has issues
        self.assertEqual(failures, 0, 
            f"Algorithm failed {failures}/10 times - should always succeed with sufficient weak pieces")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)