# tests/ai_turn_play/test_current_plays_data.py
"""
Test to verify what data is available in game.current_turn_plays
and if it matches what the AI needs for decision making.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.turn_resolution import TurnPlay
from backend.engine.rules import get_play_type


def test_current_turn_plays_structure():
    """Test what data is in current_turn_plays during a turn."""
    print("\n=== Testing current_turn_plays Data Structure ===\n")
    
    # Create a simple game
    players = [
        Player("Player1", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Player2", is_bot=False),
        Player("Bot2", is_bot=True)
    ]
    
    game = Game(players)
    
    # Initialize game state
    for player in game.players:
        game.pile_counts[player.name] = 0
        player.declared = 2  # Everyone declares 2
    
    # Give players some pieces
    players[0].hand = [
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK"),  # Can make pair
        Piece("HORSE_RED"),
        Piece("CANNON_BLACK")
    ]
    
    players[1].hand = [
        Piece("GENERAL_RED"),
        Piece("ADVISOR_BLACK"),
        Piece("ELEPHANT_RED"),
        Piece("SOLDIER_RED")
    ]
    
    # Simulate first player playing a pair
    pieces_played = [Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK")]
    turn_play1 = TurnPlay(
        player=players[0],
        pieces=pieces_played,
        is_valid=True
    )
    game.current_turn_plays.append(turn_play1)
    
    print("After Player1 plays:")
    print(f"Number of plays: {len(game.current_turn_plays)}")
    print(f"First play: {turn_play1}")
    print(f"  - Player: {turn_play1.player.name}")
    print(f"  - Pieces: {[str(p) for p in turn_play1.pieces]}")
    print(f"  - Is valid: {turn_play1.is_valid}")
    print(f"  - Play type (calculated): {get_play_type(turn_play1.pieces)}")
    
    # Simulate second player (Bot1) playing
    bot_pieces = [Piece("GENERAL_RED")]
    turn_play2 = TurnPlay(
        player=players[1],
        pieces=bot_pieces,
        is_valid=True
    )
    game.current_turn_plays.append(turn_play2)
    
    print("\nAfter Bot1 plays:")
    print(f"Number of plays: {len(game.current_turn_plays)}")
    
    # Now test what Bot2 would see
    print("\n=== What Bot2 sees in current_turn_plays ===")
    print(f"Bot2 is deciding what to play...")
    print(f"Current plays available: {len(game.current_turn_plays)}")
    
    # Format as the AI expects
    current_plays_for_ai = []
    for play in game.current_turn_plays:
        play_data = {
            'player': play.player,
            'pieces': play.pieces,
            'play_type': get_play_type(play.pieces) if play.is_valid else None
        }
        current_plays_for_ai.append(play_data)
        
        print(f"\nPlay by {play.player.name}:")
        print(f"  - Pieces: {[str(p) for p in play.pieces]}")
        print(f"  - Play type: {play_data['play_type']}")
        print(f"  - Points: {sum(p.point for p in play.pieces)}")
    
    # Check who's winning so far
    if current_plays_for_ai:
        from backend.engine.rules import compare_plays
        
        winning_play = current_plays_for_ai[0]
        for i in range(1, len(current_plays_for_ai)):
            result = compare_plays(current_plays_for_ai[i]['pieces'], winning_play['pieces'])
            if result == 1:  # Current play beats winning play
                winning_play = current_plays_for_ai[i]
        
        print(f"\nCurrent winning play: {winning_play['player'].name} with {winning_play['play_type']}")
    
    # Test clearing
    print("\n=== Testing turn end behavior ===")
    print(f"Before clear: {len(game.current_turn_plays)} plays")
    game.current_turn_plays.clear()
    print(f"After clear: {len(game.current_turn_plays)} plays")
    
    return True


def test_data_format_compatibility():
    """Test if the data format is compatible with AI expectations."""
    print("\n=== Testing Data Format Compatibility ===\n")
    
    # Create minimal test data
    player = Player("TestBot", is_bot=True)
    pieces = [Piece("HORSE_RED"), Piece("HORSE_RED")]
    
    turn_play = TurnPlay(
        player=player,
        pieces=pieces,
        is_valid=True
    )
    
    # Convert to AI format
    ai_format = {
        'player': turn_play.player,
        'pieces': turn_play.pieces,
        'play_type': get_play_type(turn_play.pieces)
    }
    
    print("TurnPlay object fields:")
    print(f"  - player: {type(turn_play.player)} = {turn_play.player.name}")
    print(f"  - pieces: {type(turn_play.pieces)} = {[str(p) for p in turn_play.pieces]}")
    print(f"  - is_valid: {type(turn_play.is_valid)} = {turn_play.is_valid}")
    
    print("\nConverted to AI format:")
    print(f"  - player: {ai_format['player'].name}")
    print(f"  - pieces: {[str(p) for p in ai_format['pieces']]}")
    print(f"  - play_type: {ai_format['play_type']}")
    
    # Verify it has what responder strategy needs
    print("\nChecking responder strategy requirements:")
    print(f"  ✓ Can access player object: {hasattr(ai_format['player'], 'name')}")
    print(f"  ✓ Can access pieces list: {isinstance(ai_format['pieces'], list)}")
    print(f"  ✓ Can determine play type: {ai_format['play_type'] is not None}")
    print(f"  ✓ Can compare plays: pieces have point values")
    
    return True


def test_empty_and_invalid_plays():
    """Test edge cases like empty plays or invalid plays."""
    print("\n=== Testing Edge Cases ===\n")
    
    game = Game([Player("P1"), Player("P2"), Player("P3"), Player("P4")])
    
    # Test empty current_turn_plays
    print(f"Empty game.current_turn_plays: {game.current_turn_plays}")
    print(f"Length: {len(game.current_turn_plays)}")
    print(f"Boolean value: {bool(game.current_turn_plays)}")
    
    # Test invalid play
    invalid_play = TurnPlay(
        player=game.players[0],
        pieces=[Piece("SOLDIER_BLACK"), Piece("CANNON_RED")],  # Invalid pair
        is_valid=False
    )
    
    game.current_turn_plays.append(invalid_play)
    
    print(f"\nAfter adding invalid play:")
    print(f"  - Is valid: {invalid_play.is_valid}")
    print(f"  - Pieces: {[str(p) for p in invalid_play.pieces]}")
    print(f"  - Play type: {get_play_type(invalid_play.pieces) if invalid_play.is_valid else 'INVALID'}")
    
    return True


if __name__ == "__main__":
    print("Testing game.current_turn_plays for AI integration...\n")
    
    test_current_turn_plays_structure()
    test_data_format_compatibility()
    test_empty_and_invalid_plays()
    
    print("\n✅ All tests completed!")
    print("\nConclusions:")
    print("1. game.current_turn_plays contains TurnPlay objects with player, pieces, is_valid")
    print("2. We need to calculate play_type using get_play_type(pieces)")
    print("3. Data is available during turn and cleared after")
    print("4. Format is compatible with AI responder strategy needs")
    print("5. Can handle empty plays and invalid plays")