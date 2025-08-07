# tests/ai_turn_play/test_revealed_pieces_accumulation.py
"""
Test accumulating revealed pieces from current_turn_plays.

This test explores how we can track all face-up pieces played
in a round by accumulating data from current_turn_plays before
it's cleared each turn.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.rules import get_play_type
from backend.engine.turn_resolution import TurnPlay


def test_accumulate_revealed_pieces():
    """Test accumulating revealed pieces across multiple turns."""
    print("\n=== Testing Revealed Pieces Accumulation ===\n")
    
    # Create game
    players = [
        Player("P1", is_bot=False),
        Player("P2", is_bot=False),
        Player("P3", is_bot=False),
        Player("P4", is_bot=False)
    ]
    
    game = Game(players)
    
    # Initialize tracking for revealed pieces
    # Option 1: Add to game object
    if not hasattr(game, 'revealed_pieces_this_round'):
        game.revealed_pieces_this_round = []
    
    # Simulate Turn 1
    print("Turn 1:")
    # Players play pieces
    turn1_plays = [
        TurnPlay(players[0], [Piece("SOLDIER_BLACK")], True),
        TurnPlay(players[1], [Piece("CANNON_RED")], True),
        TurnPlay(players[2], [Piece("HORSE_RED")], True),
        TurnPlay(players[3], [Piece("GENERAL_RED")], True)
    ]
    
    # Add to current_turn_plays
    game.current_turn_plays = turn1_plays
    
    # Before clearing, accumulate revealed pieces
    for play in game.current_turn_plays:
        for piece in play.pieces:
            game.revealed_pieces_this_round.append({
                'piece': piece,
                'player': play.player.name,
                'turn': 1,
                'play_type': get_play_type(play.pieces)
            })
    
    print(f"  Current turn plays: {len(game.current_turn_plays)}")
    print(f"  Revealed pieces so far: {len(game.revealed_pieces_this_round)}")
    
    # Clear current turn (as game does)
    game.current_turn_plays.clear()
    
    # Simulate Turn 2
    print("\nTurn 2:")
    turn2_plays = [
        TurnPlay(players[0], [Piece("CHARIOT_RED"), Piece("CHARIOT_RED")], True),
        TurnPlay(players[1], [Piece("ADVISOR_BLACK"), Piece("ADVISOR_BLACK")], True),
        TurnPlay(players[2], [Piece("CANNON_BLACK"), Piece("CANNON_BLACK")], True),
        TurnPlay(players[3], [Piece("SOLDIER_RED"), Piece("SOLDIER_RED")], True)
    ]
    
    game.current_turn_plays = turn2_plays
    
    # Accumulate before clearing
    for play in game.current_turn_plays:
        for piece in play.pieces:
            game.revealed_pieces_this_round.append({
                'piece': piece,
                'player': play.player.name,
                'turn': 2,
                'play_type': get_play_type(play.pieces)
            })
    
    print(f"  Current turn plays: {len(game.current_turn_plays)}")
    print(f"  Revealed pieces so far: {len(game.revealed_pieces_this_round)}")
    
    # Clear current turn
    game.current_turn_plays.clear()
    
    # Show accumulated data
    print("\n=== All Revealed Pieces This Round ===")
    for i, reveal in enumerate(game.revealed_pieces_this_round):
        print(f"{i+1}. Turn {reveal['turn']}: {reveal['player']} played {reveal['piece']} ({reveal['play_type']})")
    
    # Verify we have all pieces
    assert len(game.revealed_pieces_this_round) == 12, "Should have 4 + 8 = 12 pieces"
    
    # Test usage in AI context
    print("\n=== Using Revealed Pieces in AI Decision ===")
    
    # Extract just the pieces for AI
    revealed_pieces_for_ai = [r['piece'] for r in game.revealed_pieces_this_round]
    
    # Count piece types revealed
    piece_counts = {}
    for piece in revealed_pieces_for_ai:
        piece_type = piece.name
        piece_counts[piece_type] = piece_counts.get(piece_type, 0) + 1
    
    print("Piece counts revealed so far:")
    for piece_type, count in sorted(piece_counts.items()):
        print(f"  {piece_type}: {count}")
    
    # AI can use this info
    print("\nAI insights:")
    if piece_counts.get('GENERAL', 0) > 0:
        print("  - GENERAL already played, no longer a threat")
    if piece_counts.get('CHARIOT', 0) >= 2:
        print("  - 2+ CHARIOTs played, fewer strong pairs possible")
    
    print("\n✅ Test passed: Can accumulate revealed pieces from current_turn_plays")


def test_revealed_pieces_in_bot_manager_context():
    """Test how revealed pieces would be used in bot manager."""
    print("\n=== Testing Revealed Pieces in Bot Manager Context ===\n")
    
    # Simulate game state
    game = Game([Player("Bot1", is_bot=True)])
    game.revealed_pieces_this_round = [
        {'piece': Piece("GENERAL_RED"), 'player': 'P1', 'turn': 1},
        {'piece': Piece("ADVISOR_BLACK"), 'player': 'P2', 'turn': 1},
        {'piece': Piece("CHARIOT_RED"), 'player': 'P3', 'turn': 2},
        {'piece': Piece("CHARIOT_RED"), 'player': 'P3', 'turn': 2},
    ]
    
    # In bot_manager, we would extract pieces for AI context
    revealed_pieces = [r['piece'] for r in game.revealed_pieces_this_round]
    
    print(f"Revealed pieces for AI: {[str(p) for p in revealed_pieces]}")
    
    # Build context as bot_manager would
    from backend.engine.ai_turn_strategy import TurnPlayContext
    
    bot = game.players[0]
    bot.hand = [Piece("GENERAL_BLACK"), Piece("CHARIOT_BLACK")]
    
    context = TurnPlayContext(
        my_hand=bot.hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=1,
        turn_number=3,
        pieces_per_player=2,
        am_i_starter=True,
        current_plays=[],  # Empty for this turn
        revealed_pieces=revealed_pieces,  # All revealed pieces!
        player_states={}
    )
    
    print(f"\nContext has {len(context.revealed_pieces)} revealed pieces")
    
    # AI can now make informed decisions
    # For example, knowing GENERAL_RED is already played
    generals_played = [p for p in context.revealed_pieces if 'GENERAL' in p.name]
    print(f"Generals already played: {len(generals_played)}")
    
    print("\n✅ Test passed: Revealed pieces can be passed to AI context")


def test_where_to_accumulate():
    """Test different places we could accumulate revealed pieces."""
    print("\n=== Testing Where to Accumulate Revealed Pieces ===\n")
    
    print("Option 1: Add to Game object")
    print("  - game.revealed_pieces_this_round = []")
    print("  - Clear in new round setup")
    print("  - Easy to access from bot_manager")
    
    print("\nOption 2: Add to state machine")
    print("  - Accumulate in TurnState")
    print("  - Pass to bot_manager via phase_data")
    print("  - More aligned with state management")
    
    print("\nOption 3: Track in bot_manager itself")
    print("  - Listen for turn resolution events")
    print("  - Maintain own revealed pieces list")
    print("  - More complex but decoupled")
    
    print("\nRecommendation: Option 1 (Game object)")
    print("  - Simplest to implement")
    print("  - Natural place since current_turn_plays is there")
    print("  - Easy to clear between rounds")


if __name__ == "__main__":
    print("Testing revealed pieces accumulation from current_turn_plays...\n")
    
    test_accumulate_revealed_pieces()
    test_revealed_pieces_in_bot_manager_context()
    test_where_to_accumulate()
    
    print("\n✅ All tests passed! Revealed pieces can be tracked by accumulating current_turn_plays.")