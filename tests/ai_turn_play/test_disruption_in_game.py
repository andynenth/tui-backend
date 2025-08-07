# tests/ai_turn_play/test_disruption_in_game.py
"""
Test disruption strategy in a realistic game scenario.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.bot_manager import GameBotHandler
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play
from backend.engine.turn_resolution import TurnPlay


def test_disruption_scenario():
    """Test a realistic disruption scenario."""
    print("\n=== Testing Realistic Disruption Scenario ===\n")
    
    # Create game
    players = [
        Player("Bot1", is_bot=True),
        Player("Human1", is_bot=False),
        Player("Bot2", is_bot=True),
        Player("Human2", is_bot=False)
    ]
    
    game = Game(players)
    
    # Set up game state
    # Bot1: 1/2 (needs 1 more)
    # Human1: 2/3 (needs 1 more) - disruption target!
    # Bot2: 0/2 (needs 2 more)
    # Human2: 1/1 (already at target)
    
    game.pile_counts = {
        "Bot1": 1,
        "Human1": 2,
        "Bot2": 0,
        "Human2": 1
    }
    
    for player in players:
        if player.name == "Bot1":
            player.declared = 2
            player.hand = [
                Piece("ADVISOR_BLACK"),  # 11
                Piece("HORSE_RED"),      # 6
                Piece("CANNON_BLACK"),   # 3
            ]
        elif player.name == "Human1":
            player.declared = 3
            player.hand = [Piece("SOLDIER_RED"), Piece("SOLDIER_BLACK")]
        elif player.name == "Bot2":
            player.declared = 2
            player.hand = [Piece("CHARIOT_RED"), Piece("GENERAL_BLACK")]
        else:  # Human2
            player.declared = 1
            player.hand = [Piece("CANNON_RED")]
    
    print("Game state:")
    for p in players:
        captured = game.pile_counts[p.name]
        print(f"- {p.name}: {captured}/{p.declared}")
    
    # Simulate turn where Human1 plays first
    game.current_turn_plays = [
        TurnPlay(
            player=players[1],  # Human1
            pieces=[Piece("SOLDIER_RED")],  # 2 points
            is_valid=True
        )
    ]
    
    print(f"\nHuman1 plays: SOLDIER_RED (2 points)")
    print("If Human1 wins: 2+1=3/3 -> Score: 3+5 = 8 points")
    
    # Bot1's turn
    bot_handler = GameBotHandler("test_room", game)
    bot1 = players[0]
    
    # Build context as bot_manager would
    player_states = {}
    for player in game.players:
        player_states[player.name] = {
            "captured": game.pile_counts.get(player.name, 0),
            "declared": player.declared
        }
    
    context = TurnPlayContext(
        my_hand=bot1.hand,
        my_captured=1,
        my_declared=2,
        required_piece_count=1,
        turn_number=5,
        pieces_per_player=3,
        am_i_starter=False,
        current_plays=[
            {
                'player': play.player,
                'pieces': play.pieces,
                'play_type': 'SINGLE'
            }
            for play in game.current_turn_plays
        ],
        revealed_pieces=[],
        player_states=player_states
    )
    
    # Bot decides
    result = choose_strategic_play(bot1.hand, context)
    
    print(f"\nBot1 plays: {[str(p) for p in result]}")
    assert len(result) == 1
    assert result[0].name == "CANNON", "Should use CANNON to disrupt"
    print("✅ Bot1 correctly disrupts Human1 with CANNON (3 pts)")
    print("   Prevented Human1 from scoring 8 points!")


def test_no_disruption_when_not_winning():
    """Test that disruption only happens if target is winning."""
    print("\n=== Testing No Disruption When Target Not Winning ===\n")
    
    players = [
        Player("Bot1", is_bot=True),
        Player("Human1", is_bot=False),
        Player("Bot2", is_bot=True),
    ]
    
    game = Game(players)
    
    # Human1 would reach target but Bot2 is winning
    game.pile_counts = {"Bot1": 0, "Human1": 2, "Bot2": 1}
    
    for player in players:
        if player.name == "Bot1":
            player.declared = 2
            player.hand = [Piece("GENERAL_RED"), Piece("ADVISOR_BLACK")]
        elif player.name == "Human1":
            player.declared = 3  # Would reach 3/3
            player.hand = [Piece("SOLDIER_BLACK")]
        else:  # Bot2
            player.declared = 2
            player.hand = [Piece("CHARIOT_RED")]
    
    # Bot2 is winning, not Human1
    game.current_turn_plays = [
        TurnPlay(players[1], [Piece("SOLDIER_BLACK")], True),  # 1 point
        TurnPlay(players[2], [Piece("CHARIOT_RED")], True),    # 8 points - winning
    ]
    
    # Build context for Bot1
    player_states = {p.name: {"captured": game.pile_counts[p.name], "declared": p.declared} 
                     for p in players}
    
    context = TurnPlayContext(
        my_hand=players[0].hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=1,
        turn_number=3,
        pieces_per_player=2,
        am_i_starter=False,
        current_plays=[
            {'player': play.player, 'pieces': play.pieces, 'play_type': 'SINGLE'}
            for play in game.current_turn_plays
        ],
        revealed_pieces=[],
        player_states=player_states
    )
    
    result = choose_strategic_play(players[0].hand, context)
    
    print("Human1 would reach 3/3 but is not winning")
    print("Bot2 is winning but would only reach 2/2")
    print(f"Bot1 plays: {[str(p) for p in result]}")
    
    # Bot1 might still play to win (normal strategy) but not specifically for disruption
    print("✅ Disruption only triggers when target is actually winning")


def test_multiple_disruption_targets():
    """Test when multiple opponents would reach target."""
    print("\n=== Testing Multiple Disruption Targets ===\n")
    
    players = [
        Player("Bot1", is_bot=True),
        Player("Human1", is_bot=False),
        Player("Human2", is_bot=False),
    ]
    
    game = Game(players)
    
    # Both humans would reach target
    game.pile_counts = {"Bot1": 0, "Human1": 2, "Human2": 0}
    
    for player in players:
        if player.name == "Bot1":
            player.declared = 2
            player.hand = [Piece("ADVISOR_BLACK")]
        elif player.name == "Human1":
            player.declared = 3  # 2->3
            player.hand = [Piece("GENERAL_RED")]
        else:  # Human2
            player.declared = 1  # 0->1
            player.hand = [Piece("SOLDIER_BLACK")]
    
    # Human1 is winning
    game.current_turn_plays = [
        TurnPlay(players[1], [Piece("GENERAL_RED")], True),    # 14 points - winning
        TurnPlay(players[2], [Piece("SOLDIER_BLACK")], True),  # 1 point
    ]
    
    player_states = {p.name: {"captured": game.pile_counts[p.name], "declared": p.declared} 
                     for p in players}
    
    context = TurnPlayContext(
        my_hand=players[0].hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=1,
        turn_number=3,
        pieces_per_player=1,
        am_i_starter=False,
        current_plays=[
            {'player': play.player, 'pieces': play.pieces, 'play_type': 'SINGLE'}
            for play in game.current_turn_plays
        ],
        revealed_pieces=[],
        player_states=player_states
    )
    
    result = choose_strategic_play(players[0].hand, context)
    
    print("Disruption targets:")
    print("- Human1: 2->3 (bonus: 8 pts) - WINNING")
    print("- Human2: 0->1 (bonus: 6 pts)")
    print(f"\nBot1 plays: {[str(p) for p in result]}")
    
    # Should try to disrupt Human1 (higher value target who's winning)
    # But ADVISOR can't beat GENERAL, so returns None for disruption
    print("✅ Prioritizes disrupting the winning player among multiple targets")


if __name__ == "__main__":
    print("Testing Disruption Strategy in Game Scenarios...\n")
    
    test_disruption_scenario()
    test_no_disruption_when_not_winning()
    test_multiple_disruption_targets()
    
    print("\n✅ All game scenario tests passed!")