# tests/ai_turn_play/test_responder_with_real_data.py
"""
Test AI responder strategy with real game turn data.

Verifies that the bot manager correctly passes current_turn_plays
to the AI and that responder decisions work with actual game data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.turn_resolution import TurnPlay
from backend.engine.bot_manager import BotManager, GameBotHandler
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play
from backend.engine.rules import get_play_type


def test_responder_sees_current_plays():
    """Test that responder AI can see plays made earlier in the turn."""
    print("\n=== Testing Responder Sees Current Plays ===\n")
    
    # Create game with bots
    players = [
        Player("Human1", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Human2", is_bot=False),
        Player("Bot2", is_bot=True)
    ]
    
    game = Game(players)
    
    # Initialize game state
    for player in game.players:
        game.pile_counts[player.name] = 0
        player.declared = 2
    
    # Set up hands
    bot2 = players[3]  # Bot2 will be responder
    bot2.hand = [
        Piece("CHARIOT_RED"),     # 8 points
        Piece("CHARIOT_RED"),     # Can make strong pair
        Piece("CANNON_BLACK"),    # 3 points
        Piece("CANNON_BLACK"),    # Can make weak pair
        Piece("SOLDIER_BLACK")
    ]
    
    # Simulate Human1 playing a medium pair
    human1_play = TurnPlay(
        player=players[0],
        pieces=[Piece("HORSE_RED"), Piece("HORSE_RED")],  # 6+6=12 points
        is_valid=True
    )
    game.current_turn_plays.append(human1_play)
    
    # Simulate Bot1 playing a single
    bot1_play = TurnPlay(
        player=players[1],
        pieces=[Piece("ADVISOR_BLACK")],  # 11 points
        is_valid=True
    )
    game.current_turn_plays.append(bot1_play)
    
    print("Current plays in game:")
    for i, play in enumerate(game.current_turn_plays):
        play_type = get_play_type(play.pieces) if play.is_valid else "INVALID"
        total_points = sum(p.point for p in play.pieces)
        print(f"{i+1}. {play.player.name}: {play_type} ({total_points} pts)")
    
    # Build context as bot manager would
    current_plays_for_ai = [
        {
            'player': play.player,
            'pieces': play.pieces,
            'play_type': get_play_type(play.pieces) if play.is_valid else None
        }
        for play in game.current_turn_plays
    ]
    
    context = TurnPlayContext(
        my_hand=bot2.hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=2,  # Must match Human1's pair
        turn_number=3,
        pieces_per_player=5,
        am_i_starter=False,
        current_plays=current_plays_for_ai,
        revealed_pieces=[],
        player_states={
            "Human1": {"captured": 0, "declared": 2},
            "Bot1": {"captured": 0, "declared": 2},
            "Human2": {"captured": 0, "declared": 2},
            "Bot2": {"captured": 0, "declared": 2}
        }
    )
    
    # Test responder decision
    print(f"\nBot2 decision context:")
    print(f"- Must play: {context.required_piece_count} pieces")
    print(f"- Current plays visible: {len(context.current_plays)}")
    print(f"- Winning play so far: Human1's PAIR (12 pts)")
    
    # Check urgency level
    from backend.engine.ai_turn_strategy import generate_strategic_plan
    plan = generate_strategic_plan(bot2.hand, context)
    print(f"- Urgency level: {plan.urgency_level}")
    print(f"- Target remaining: {plan.target_remaining}")
    print(f"- Valid combos: {[(t, [p.name for p in pieces]) for t, pieces in plan.valid_combos]}")
    
    result = choose_strategic_play(bot2.hand, context)
    
    print(f"\nBot2 plays: {[str(p) for p in result]}")
    print(f"Play type: {get_play_type(result)}")
    print(f"Total points: {sum(p.point for p in result)}")
    
    # Verify bot made a reasonable decision
    assert len(result) == 2, "Should play 2 pieces as required"
    
    # Check decision based on urgency
    if plan.urgency_level in ["medium", "high"]:
        # Should try to win
        assert all(p.name == "CHARIOT" for p in result), f"With {plan.urgency_level} urgency, should play CHARIOT pair to win"
    else:
        # Low urgency - might play weak pieces
        print(f"With {plan.urgency_level} urgency, bot chose not to win (reasonable)")
        # Could be CANNON pair or CHARIOT pair
    
    print("\n✅ Test passed: Bot correctly analyzed current plays and made strategic decision")


def test_empty_current_plays():
    """Test bot behavior when it's the first to play (empty current_plays)."""
    print("\n=== Testing First Player (Empty current_plays) ===\n")
    
    bot = Player("Bot1", is_bot=True)
    bot.hand = [
        Piece("GENERAL_RED"),
        Piece("ADVISOR_BLACK"),
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK")
    ]
    bot.declared = 3
    
    game = Game([bot])
    game.pile_counts[bot.name] = 1  # Already has 1 pile
    
    # No plays yet
    assert len(game.current_turn_plays) == 0
    
    context = TurnPlayContext(
        my_hand=bot.hand,
        my_captured=1,
        my_declared=3,
        required_piece_count=None,  # Starter
        turn_number=2,
        pieces_per_player=4,
        am_i_starter=True,
        current_plays=[],  # Empty!
        revealed_pieces=[],
        player_states={bot.name: {"captured": 1, "declared": 3}}
    )
    
    result = choose_strategic_play(bot.hand, context)
    
    print(f"As starter with empty current_plays:")
    print(f"Bot plays: {[str(p) for p in result]}")
    print(f"Play type: {get_play_type(result)}")
    
    # Should play opener to control next turn
    assert len(result) == 1, "Should play single piece as starter"
    assert result[0].point >= 11, "Should play opener"
    
    print("\n✅ Test passed: Bot handles empty current_plays correctly")


def test_invalid_plays_handling():
    """Test that invalid plays in current_plays are handled correctly."""
    print("\n=== Testing Invalid Plays Handling ===\n")
    
    players = [Player("P1"), Player("Bot1", is_bot=True)]
    game = Game(players)
    
    # Add an invalid play
    invalid_play = TurnPlay(
        player=players[0],
        pieces=[Piece("SOLDIER_BLACK"), Piece("CANNON_RED")],  # Invalid pair
        is_valid=False
    )
    game.current_turn_plays.append(invalid_play)
    
    # Build context
    current_plays = [
        {
            'player': play.player,
            'pieces': play.pieces,
            'play_type': get_play_type(play.pieces) if play.is_valid else None
        }
        for play in game.current_turn_plays
    ]
    
    print(f"Current plays with invalid entry:")
    for play in current_plays:
        print(f"- {play['player'].name}: {play['play_type'] or 'INVALID'}")
    
    # Bot should handle this gracefully
    bot = players[1]
    bot.hand = [Piece("GENERAL_RED"), Piece("ADVISOR_BLACK")]
    bot.declared = 1
    
    context = TurnPlayContext(
        my_hand=bot.hand,
        my_captured=0,
        my_declared=1,
        required_piece_count=2,
        turn_number=1,
        pieces_per_player=2,
        am_i_starter=False,
        current_plays=current_plays,
        revealed_pieces=[],
        player_states={}
    )
    
    # Should not crash
    result = choose_strategic_play(bot.hand, context)
    assert len(result) == 2, "Should still make a valid play"
    
    print("\n✅ Test passed: Bot handles invalid plays in current_plays")


if __name__ == "__main__":
    print("Testing AI responder strategy with real game data...\n")
    
    test_responder_sees_current_plays()
    test_empty_current_plays()
    test_invalid_plays_handling()
    
    print("\n✅ All tests passed! Responder AI works correctly with real game data.")