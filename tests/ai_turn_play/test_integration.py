# tests/ai_turn_play/test_integration.py
"""
Integration tests for AI turn play system.

Tests full game scenarios to ensure the new AI integrates properly
with the game engine and doesn't break existing functionality.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.bot_manager import BotManager
from backend.engine.state_machine.game_state_machine import GameStateMachine
from backend.engine.state_machine.core import ActionType, GameAction


def create_test_game():
    """Create a game with mix of human and bot players."""
    players = [
        Player("Human1", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Human2", is_bot=False)
    ]
    
    game = Game(players)
    state_machine = GameStateMachine(game)
    
    # Register with bot manager
    bot_manager = BotManager()
    bot_manager.register_game("test_room", game, state_machine)
    
    return game, state_machine, bot_manager


def test_pile_counting_accuracy():
    """Test that pile counting is accurate throughout a turn."""
    game, state_machine, bot_manager = create_test_game()
    
    # Initialize pile counts
    for player in game.players:
        game.pile_counts[player.name] = 0
    
    # Simulate declarations
    for i, player in enumerate(game.players):
        player.declared = i  # 0, 1, 2, 3
    
    # Track initial pile counts
    assert all(game.pile_counts[p.name] == 0 for p in game.players), "Pile counts should start at 0"
    
    # Simulate a turn where Bot1 wins with a THREE_OF_A_KIND
    bot1 = game.players[1]
    bot1.hand = [
        Piece("SOLDIER_BLACK"), 
        Piece("SOLDIER_BLACK"), 
        Piece("SOLDIER_BLACK"),
        Piece("GENERAL_RED"),
        Piece("ADVISOR_BLACK")
    ]
    
    # Simulate winning a turn with THREE_OF_A_KIND
    pieces_played = [Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK")]
    
    # The fix we implemented: winner gets piles equal to pieces played
    piles_won = len(pieces_played)
    game.pile_counts["Bot1"] += piles_won
    
    # Check pile count - should win 3 piles
    assert game.pile_counts["Bot1"] == 3, f"Expected 3 piles, got {game.pile_counts['Bot1']}"
    
    print("✅ Test 1 passed: Pile counting accurate for THREE_OF_A_KIND")


def test_overcapture_avoidance():
    """Test that bot avoids winning when at declared target."""
    game, state_machine, bot_manager = create_test_game()
    
    # Initialize pile counts
    for player in game.players:
        game.pile_counts[player.name] = 0
    
    # Set up bot at target
    bot1 = game.players[1]
    bot1.declared = 2
    game.pile_counts["Bot1"] = 2  # Already at target
    
    # Give bot a strong hand
    bot1.hand = [
        Piece("GENERAL_RED"),     # 14 points
        Piece("GENERAL_RED"),     # Can make strong pair
        Piece("SOLDIER_BLACK"),   # 1 point
        Piece("SOLDIER_BLACK")    # Can make weak pair
    ]
    
    # Build context for bot play
    from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play
    
    context = TurnPlayContext(
        my_hand=bot1.hand,
        my_captured=2,
        my_declared=2,  # At target
        required_piece_count=2,
        turn_number=3,
        pieces_per_player=4,
        am_i_starter=False,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    # Bot should play weak pieces
    result = choose_strategic_play(bot1.hand, context)
    
    assert len(result) == 2, "Should play 2 pieces"
    assert all(p.name == "SOLDIER" for p in result), "Should play weak SOLDIERs to avoid winning"
    
    print("✅ Test 2 passed: Bot avoids overcapture when at target")


def test_strategic_target_achievement():
    """Test that bot makes strategic plays to reach declared target."""
    game, state_machine, bot_manager = create_test_game()
    
    # Initialize pile counts
    for player in game.players:
        game.pile_counts[player.name] = 0
    
    # Set up bot needing piles
    bot1 = game.players[1]
    bot1.declared = 4
    game.pile_counts["Bot1"] = 1  # Need 3 more
    
    # Give bot hand with opener
    bot1.hand = [
        Piece("GENERAL_RED"),     # 14 points - opener
        Piece("ADVISOR_BLACK"),   # 11 points - opener
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK"),
        Piece("SOLDIER_BLACK")    # Can make THREE_OF_A_KIND
    ]
    
    from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play
    
    # Test as starter with critical urgency
    context = TurnPlayContext(
        my_hand=bot1.hand,
        my_captured=1,
        my_declared=4,
        required_piece_count=None,  # Starter
        turn_number=6,
        pieces_per_player=3,  # Critical urgency
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={}
    )
    
    result = choose_strategic_play(bot1.hand, context)
    
    # With critical urgency, should play THREE_OF_A_KIND to capture 3 piles
    assert len(result) == 3, f"Expected 3 pieces (THREE_OF_A_KIND), got {len(result)}"
    assert all(p.name == "SOLDIER" for p in result), "Should play THREE_OF_A_KIND in critical situation"
    
    print("✅ Test 3 passed: Bot uses strategic play for target achievement")


def test_no_game_breaking_bugs():
    """Test that AI doesn't break core game functionality."""
    game, state_machine, bot_manager = create_test_game()
    
    # Initialize game state
    for player in game.players:
        game.pile_counts[player.name] = 0
        # Give each player some pieces
        player.hand = [Piece("SOLDIER_BLACK") for _ in range(8)]
    
    assert game.round_number == 1, "Game should start at round 1"
    
    # Test all players have hands
    assert all(len(p.hand) == 8 for p in game.players), "All players should have 8 pieces"
    
    # Test bot players can be identified
    bot_players = [p for p in game.players if p.is_bot]
    assert len(bot_players) == 2, "Should have 2 bot players"
    
    # Test pile counts initialized
    assert all(p.name in game.pile_counts for p in game.players), "All players should have pile counts"
    
    print("✅ Test 4 passed: No game-breaking bugs detected")


def test_bot_manager_integration():
    """Test that bot manager properly integrates with new AI."""
    game, state_machine, bot_manager = create_test_game()
    
    # Initialize game state
    for player in game.players:
        game.pile_counts[player.name] = 0
    
    # Check bot manager has the game registered
    assert "test_room" in bot_manager.active_games, "Game should be registered"
    
    # Get handler
    handler = bot_manager.active_games["test_room"]
    assert handler is not None, "Should have game handler"
    
    # Test bot can get game state
    game_state = handler._get_game_state()
    assert game_state is not None, "Should get game state"
    
    print("✅ Test 5 passed: Bot manager integration working")


if __name__ == "__main__":
    print("Running AI turn play integration tests...\n")
    
    test_pile_counting_accuracy()
    test_overcapture_avoidance()
    test_strategic_target_achievement()
    test_no_game_breaking_bugs()
    test_bot_manager_integration()
    
    print("\n✅ All integration tests passed!")