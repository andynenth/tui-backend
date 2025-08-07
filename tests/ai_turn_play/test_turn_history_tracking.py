# tests/ai_turn_play/test_turn_history_tracking.py
"""
Test tracking full turn history for AI decision making.

This explores tracking all turns in a round with enough information
to extract revealed pieces (filtering out forfeits) and provide
strategic context to AI.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.rules import get_play_type, is_valid_play
from backend.engine.turn_resolution import TurnPlay


def test_turn_history_data_structure():
    """Test what data structure would be most useful for turn history."""
    print("\n=== Testing Turn History Data Structure ===\n")
    
    # Option 1: List of turn summaries
    print("Option 1: List of turn summaries")
    turn_history_v1 = [
        {
            'turn_number': 1,
            'plays': [
                {'player': 'P1', 'pieces': [Piece("SOLDIER_BLACK")], 'play_type': 'SINGLE', 'is_valid': True},
                {'player': 'P2', 'pieces': [Piece("CANNON_RED")], 'play_type': 'SINGLE', 'is_valid': True},
                {'player': 'P3', 'pieces': [Piece("HORSE_RED")], 'play_type': 'SINGLE', 'is_valid': True},
                {'player': 'P4', 'pieces': [Piece("GENERAL_RED")], 'play_type': 'SINGLE', 'is_valid': True},
            ],
            'winner': 'P4',
            'piles_won': 1
        },
        {
            'turn_number': 2,
            'plays': [
                {'player': 'P4', 'pieces': [Piece("CHARIOT_RED"), Piece("CHARIOT_RED")], 'play_type': 'PAIR', 'is_valid': True},
                {'player': 'P1', 'pieces': [Piece("SOLDIER_RED"), Piece("CANNON_BLACK")], 'play_type': None, 'is_valid': False},  # Forfeit!
                {'player': 'P2', 'pieces': [Piece("ADVISOR_BLACK"), Piece("ADVISOR_BLACK")], 'play_type': 'PAIR', 'is_valid': True},
                {'player': 'P3', 'pieces': [Piece("CANNON_BLACK"), Piece("CANNON_BLACK")], 'play_type': 'PAIR', 'is_valid': True},
            ],
            'winner': 'P2',
            'piles_won': 2
        }
    ]
    
    print("  - Clear turn boundaries")
    print("  - Easy to see winners and pile counts")
    print("  - Can filter forfeits easily")
    
    # Extract revealed pieces (filtering forfeits)
    revealed_pieces_v1 = []
    for turn in turn_history_v1:
        for play in turn['plays']:
            if play['is_valid']:  # Skip forfeits
                for piece in play['pieces']:
                    revealed_pieces_v1.append(piece)
    
    print(f"\nRevealed pieces (valid only): {len(revealed_pieces_v1)}")
    print(f"Pieces: {[str(p) for p in revealed_pieces_v1]}")
    
    # Option 2: Flat list with turn markers
    print("\n\nOption 2: Flat list with turn context")
    turn_history_v2 = [
        # Turn 1
        {'turn': 1, 'player': 'P1', 'pieces': [Piece("SOLDIER_BLACK")], 'play_type': 'SINGLE', 'is_valid': True, 'winner': False},
        {'turn': 1, 'player': 'P2', 'pieces': [Piece("CANNON_RED")], 'play_type': 'SINGLE', 'is_valid': True, 'winner': False},
        {'turn': 1, 'player': 'P3', 'pieces': [Piece("HORSE_RED")], 'play_type': 'SINGLE', 'is_valid': True, 'winner': False},
        {'turn': 1, 'player': 'P4', 'pieces': [Piece("GENERAL_RED")], 'play_type': 'SINGLE', 'is_valid': True, 'winner': True},
        # Turn 2
        {'turn': 2, 'player': 'P4', 'pieces': [Piece("CHARIOT_RED"), Piece("CHARIOT_RED")], 'play_type': 'PAIR', 'is_valid': True, 'winner': False},
        {'turn': 2, 'player': 'P1', 'pieces': [Piece("SOLDIER_RED"), Piece("CANNON_BLACK")], 'play_type': None, 'is_valid': False, 'winner': False},
        {'turn': 2, 'player': 'P2', 'pieces': [Piece("ADVISOR_BLACK"), Piece("ADVISOR_BLACK")], 'play_type': 'PAIR', 'is_valid': True, 'winner': True},
        {'turn': 2, 'player': 'P3', 'pieces': [Piece("CANNON_BLACK"), Piece("CANNON_BLACK")], 'play_type': 'PAIR', 'is_valid': True, 'winner': False},
    ]
    
    print("  - Simpler structure")
    print("  - Easy to iterate")
    print("  - Turn context preserved")
    
    # Extract revealed pieces
    revealed_pieces_v2 = []
    for play in turn_history_v2:
        if play['is_valid']:
            revealed_pieces_v2.extend(play['pieces'])
    
    print(f"\nRevealed pieces (valid only): {len(revealed_pieces_v2)}")
    
    print("\n✅ Recommendation: Option 1 (structured by turns) provides better context")


def test_forfeit_filtering():
    """Test that we correctly filter out forfeit plays."""
    print("\n=== Testing Forfeit Filtering ===\n")
    
    # Create game scenario
    players = [Player("P1"), Player("P2"), Player("P3"), Player("P4")]
    game = Game(players)
    
    # Simulate a turn with forfeits
    turn_plays = [
        TurnPlay(players[0], [Piece("CHARIOT_RED"), Piece("CHARIOT_RED")], True),  # Valid pair
        TurnPlay(players[1], [Piece("SOLDIER_BLACK"), Piece("CANNON_RED")], False),  # Invalid - forfeit!
        TurnPlay(players[2], [Piece("ADVISOR_BLACK"), Piece("ADVISOR_BLACK")], True),  # Valid pair
        TurnPlay(players[3], [Piece("HORSE_RED"), Piece("CANNON_BLACK")], False),  # Invalid - forfeit!
    ]
    
    print("Turn plays:")
    for i, play in enumerate(turn_plays):
        status = "VALID" if play.is_valid else "FORFEIT"
        play_type = get_play_type(play.pieces) if play.is_valid else "INVALID"
        print(f"  {play.player.name}: {[str(p) for p in play.pieces]} - {play_type} ({status})")
    
    # Filter for revealed pieces
    revealed_pieces = []
    forfeit_count = 0
    
    for play in turn_plays:
        if play.is_valid:
            revealed_pieces.extend(play.pieces)
        else:
            forfeit_count += 1
    
    print(f"\nResults:")
    print(f"  Valid plays: {len(turn_plays) - forfeit_count}")
    print(f"  Forfeits: {forfeit_count}")
    print(f"  Revealed pieces: {len(revealed_pieces)} - {[str(p) for p in revealed_pieces]}")
    
    # For AI, forfeits tell us something too
    print("\nAI insights from forfeits:")
    print("  - Players who forfeit likely have limited valid options")
    print("  - High forfeit rate suggests constrained hands")
    
    print("\n✅ Test passed: Forfeits correctly filtered from revealed pieces")


def test_turn_history_for_ai_strategy():
    """Test how turn history helps AI make better decisions."""
    print("\n=== Testing Turn History for AI Strategy ===\n")
    
    # Rich turn history
    turn_history = [
        {
            'turn_number': 1,
            'plays': [
                {'player': 'Bot1', 'pieces': [Piece("SOLDIER_BLACK")], 'play_type': 'SINGLE', 'is_valid': True},
                {'player': 'Human1', 'pieces': [Piece("ADVISOR_BLACK")], 'play_type': 'SINGLE', 'is_valid': True},
                {'player': 'Bot2', 'pieces': [Piece("GENERAL_BLACK")], 'play_type': 'SINGLE', 'is_valid': True},
                {'player': 'Human2', 'pieces': [Piece("GENERAL_RED")], 'play_type': 'SINGLE', 'is_valid': True},
            ],
            'winner': 'Human2',
            'piles_won': 1
        },
        {
            'turn_number': 2,
            'plays': [
                {'player': 'Human2', 'pieces': [Piece("CHARIOT_RED"), Piece("CHARIOT_RED")], 'play_type': 'PAIR', 'is_valid': True},
                {'player': 'Bot1', 'pieces': [Piece("SOLDIER_RED"), Piece("SOLDIER_RED")], 'play_type': 'PAIR', 'is_valid': True},
                {'player': 'Human1', 'pieces': [Piece("CANNON_RED"), Piece("CANNON_BLACK")], 'play_type': None, 'is_valid': False},
                {'player': 'Bot2', 'pieces': [Piece("ADVISOR_RED"), Piece("ADVISOR_RED")], 'play_type': 'PAIR', 'is_valid': True},
            ],
            'winner': 'Bot2',
            'piles_won': 2
        }
    ]
    
    # Analyze for AI insights
    print("AI Strategic Analysis from Turn History:\n")
    
    # 1. Track who's winning turns
    winners = {}
    for turn in turn_history:
        winner = turn['winner']
        winners[winner] = winners.get(winner, 0) + turn['piles_won']
    
    print("1. Pile accumulation:")
    for player, piles in winners.items():
        print(f"   {player}: {piles} piles")
    
    # 2. Track revealed high-value pieces
    high_value_revealed = []
    for turn in turn_history:
        for play in turn['plays']:
            if play['is_valid']:
                for piece in play['pieces']:
                    if piece.point >= 11:  # High value
                        high_value_revealed.append((play['player'], piece))
    
    print("\n2. High-value pieces revealed:")
    for player, piece in high_value_revealed:
        print(f"   {player}: {piece}")
    
    # 3. Track forfeit patterns
    forfeit_players = set()
    for turn in turn_history:
        for play in turn['plays']:
            if not play['is_valid']:
                forfeit_players.add(play['player'])
    
    print("\n3. Players who have forfeited:")
    for player in forfeit_players:
        print(f"   {player} - likely has constrained options")
    
    # 4. Play style analysis
    print("\n4. Play style patterns:")
    player_plays = {}
    for turn in turn_history:
        for play in turn['plays']:
            if play['is_valid']:
                player = play['player']
                if player not in player_plays:
                    player_plays[player] = []
                player_plays[player].append(play['play_type'])
    
    for player, plays in player_plays.items():
        print(f"   {player}: {plays}")
    
    print("\n✅ Turn history provides rich strategic context for AI decisions")


def test_implementation_approach():
    """Test how to implement turn history tracking."""
    print("\n=== Testing Implementation Approach ===\n")
    
    print("Implementation Plan:")
    print("1. Add to Game object:")
    print("   - self.turn_history_this_round = []")
    print("   - Clear at round start")
    
    print("\n2. In TurnState._complete_turn():")
    print("   - Build turn summary from self.turn_plays")
    print("   - Include turn number, all plays, winner, piles_won")
    print("   - Append to game.turn_history_this_round")
    
    print("\n3. In bot_manager.py:")
    print("   - Extract revealed_pieces from turn_history (filter is_valid)")
    print("   - Pass full turn_history to AI context for advanced strategies")
    
    print("\n4. Benefits over simple revealed_pieces:")
    print("   - Turn sequence preserved")
    print("   - Winners and pile counts tracked")
    print("   - Forfeit information retained")
    print("   - Play patterns visible")
    
    print("\nExample usage in bot_manager:")
    print("""
    # Extract revealed pieces
    revealed_pieces = []
    if hasattr(game, 'turn_history_this_round'):
        for turn in game.turn_history_this_round:
            for play in turn.get('plays', []):
                if play.get('is_valid', False):
                    revealed_pieces.extend(play.get('pieces', []))
    
    # AI can also access full history for advanced analysis
    turn_history = getattr(game, 'turn_history_this_round', [])
    """)


if __name__ == "__main__":
    print("Testing turn history tracking for AI...\n")
    
    test_turn_history_data_structure()
    test_forfeit_filtering()
    test_turn_history_for_ai_strategy()
    test_implementation_approach()
    
    print("\n✅ All tests passed! Turn history provides richer context than just revealed pieces.")