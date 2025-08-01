"""
Debug Test for the "Impossible Scenario" Result

The previous test showed that somehow all 4 players got weak hands 
when we only have 24 weak pieces (24 pieces total, need 32 for 4 players).
This seems mathematically impossible. Let's debug what actually happened.
"""

import unittest
import random
import sys
import os
from unittest.mock import MagicMock

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

# Mock specific imports
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

from engine.player import Player
from engine.piece import Piece
from engine.constants import PIECE_POINTS
from engine.game import Game


class TestImpossibleScenarioDebug(unittest.TestCase):

    def test_debug_impossible_scenario(self):
        """Debug the mathematically impossible result"""
        print(f"\n=== DEBUGGING IMPOSSIBLE SCENARIO ===")
        
        # First, verify deck composition one more time
        deck = Piece.build_deck()
        weak_pieces = [p for p in deck if p.point <= 9]
        strong_pieces = [p for p in deck if p.point > 9]
        
        print(f"Deck verification:")
        print(f"  Total pieces: {len(deck)}")
        print(f"  Weak pieces (≤9): {len(weak_pieces)}")
        print(f"  Strong pieces (>9): {len(strong_pieces)}")
        
        # List all pieces by point value
        by_points = {}
        for piece in deck:
            if piece.point not in by_points:
                by_points[piece.point] = []
            by_points[piece.point].append(piece.kind)
            
        print(f"\nPiece distribution:")
        for point in sorted(by_points.keys(), reverse=True):
            pieces = by_points[point]
            weak_strong = "WEAK" if point <= 9 else "STRONG"
            print(f"  {point} points ({weak_strong}): {pieces} (count: {len(pieces)})")
            
        # Now test the scenario
        players = [Player(f"Player{i+1}") for i in range(4)]
        game = Game(players)
        game.redeal_multiplier = 1
        
        print(f"\n=== TESTING ALL 4 PLAYERS WEAK ===")
        game._deal_weak_hand(weak_player_indices=[0, 1, 2, 3], max_weak_points=9, limit=2)
        
        # Analyze each player's hand in detail
        total_pieces_dealt = 0
        weak_pieces_used = 0
        strong_pieces_used = 0
        
        for i, player in enumerate(game.players):
            hand = player.hand
            weak_in_hand = [p for p in hand if p.point <= 9]
            strong_in_hand = [p for p in hand if p.point > 9]
            
            total_pieces_dealt += len(hand)
            weak_pieces_used += len(weak_in_hand)
            strong_pieces_used += len(strong_in_hand)
            
            print(f"\nPlayer {i} analysis:")
            print(f"  Total pieces: {len(hand)}")
            print(f"  Weak pieces: {len(weak_in_hand)}")
            print(f"  Strong pieces: {len(strong_in_hand)}")
            print(f"  Hand: {[f'{p.kind}({p.point})' for p in hand]}")
            
            if len(strong_in_hand) > 0:
                print(f"  Strong pieces in hand: {[f'{p.kind}({p.point})' for p in strong_in_hand]}")
                
        print(f"\n=== TOTALS ===")
        print(f"Total pieces dealt: {total_pieces_dealt}")
        print(f"Weak pieces used: {weak_pieces_used}")
        print(f"Strong pieces used: {strong_pieces_used}")
        print(f"Available weak pieces: {len(weak_pieces)}")
        print(f"Available strong pieces: {len(strong_pieces)}")
        
        # The key question: How did we use more weak pieces than available?
        if weak_pieces_used > len(weak_pieces):
            print(f"🚨 IMPOSSIBLE: Used {weak_pieces_used} weak pieces but only {len(weak_pieces)} exist!")
            print(f"This suggests there's an error in our piece categorization or counting")
        elif weak_pieces_used == len(weak_pieces):
            print(f"✅ Used exactly all {len(weak_pieces)} weak pieces")
        else:
            print(f"ℹ️  Used {weak_pieces_used}/{len(weak_pieces)} weak pieces")
            
        # Check if all players actually have weak hands
        all_weak = True
        for i, player in enumerate(game.players):
            strong_in_hand = [p for p in player.hand if p.point > 9]
            if len(strong_in_hand) > 0:
                all_weak = False
                print(f"Player {i} is NOT purely weak")
                
        if all_weak:
            print(f"🔍 MYSTERY: All players have purely weak hands despite insufficient pieces")
            print(f"Need to investigate the algorithm logic more deeply")
        else:
            print(f"✅ As expected, not all players have purely weak hands")
            
    def test_analyze_algorithm_source_behavior(self):
        """Look at specific edge cases in the algorithm"""
        print(f"\n=== ANALYZING ALGORITHM EDGE CASES ===")
        
        players = [Player(f"Player{i+1}") for i in range(4)]
        game = Game(players)
        game.redeal_multiplier = 1
        
        # Look at the deck preparation
        deck = Piece.build_deck()
        print(f"Original deck size: {len(deck)}")
        
        # Manually trace what _categorize_pieces does
        categories = game._categorize_pieces(deck)
        
        print(f"Categorized pieces:")
        print(f"  Red general: {categories['red_general']}")
        print(f"  Strong pieces: {len(categories['strong_pieces'])}")
        print(f"  Weak pieces: {len(categories['weak_pieces'])}")
        print(f"  All other: {len(categories['all_other'])}")
        
        # The key insight: RED_GENERAL might be treated specially
        red_general = categories['red_general']
        if red_general:
            print(f"Red general details: {red_general.kind}({red_general.point})")
            if red_general.point > 9:
                print(f"Red general is STRONG (>{red_general.point} > 9)")
            else:
                print(f"Red general is WEAK ({red_general.point} ≤ 9)")
                
        # Test with more players than we have strong pieces for
        total_strong = len(categories['strong_pieces'])
        if categories['red_general'] and categories['red_general'].point > 9:
            total_strong += 1
            
        print(f"Total strong pieces (including red general if strong): {total_strong}")
        print(f"Need to give non-weak players at least 1 strong each: 0 players (all are weak)")
        print(f"Strong pieces needed: 0")
        print(f"Strong pieces available: {total_strong}")
        
        # The algorithm might be working because when ALL players are weak,
        # no players need strong pieces, so it can give all players weak pieces
        print(f"\n🔍 HYPOTHESIS: Algorithm works when ALL players are weak because:")
        print(f"   - No non-weak players need strong pieces")
        print(f"   - Can distribute all 24 weak pieces among 4 players")
        print(f"   - Each player gets 6 weak pieces + 2 strong pieces")
        print(f"   - But since weak_player_indices=[0,1,2,3], ALL get treated as weak")
        
        # Let's verify this hypothesis
        game._deal_weak_hand(weak_player_indices=[0, 1, 2, 3], max_weak_points=9, limit=2)
        
        for i, player in enumerate(game.players):
            hand = player.hand
            weak_count = len([p for p in hand if p.point <= 9])
            strong_count = len([p for p in hand if p.point > 9])
            print(f"Player {i}: {weak_count} weak + {strong_count} strong = {len(hand)} total")


if __name__ == '__main__':
    unittest.main(verbosity=2)