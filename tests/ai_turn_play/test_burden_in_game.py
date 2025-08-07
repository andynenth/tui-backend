# tests/ai_turn_play/test_burden_in_game.py
"""
Test burden disposal in a realistic game scenario.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.bot_manager import GameBotHandler
from backend.engine.ai_turn_strategy import TurnPlayContext, choose_strategic_play


def test_burden_disposal_scenario():
    """Test burden disposal in early game with low urgency."""
    print("\n=== Testing Burden Disposal in Game ===\n")
    
    # Create game
    players = [
        Player("Bot1", is_bot=True),
        Player("Human1", is_bot=False),
        Player("Bot2", is_bot=True),
        Player("Human2", is_bot=False)
    ]
    
    game = Game(players)
    
    # Set up early game state
    game.pile_counts = {
        "Bot1": 0,
        "Human1": 0,
        "Bot2": 0,
        "Human2": 0
    }
    
    # Bot1 has mix of strong and weak pieces
    bot1 = players[0]
    bot1.declared = 3  # Needs 3 piles
    bot1.hand = [
        Piece("GENERAL_RED"),      # 14 - opener
        Piece("ADVISOR_BLACK"),    # 11 - opener
        Piece("CHARIOT_RED"),      # 8
        Piece("CHARIOT_BLACK"),    # 7
        Piece("HORSE_RED"),        # 6
        Piece("HORSE_BLACK"),      # 5
        Piece("SOLDIER_RED"),      # 2 - burden
        Piece("SOLDIER_BLACK"),    # 1 - burden
    ]
    
    print("Bot1's hand:")
    for p in bot1.hand:
        print(f"  {p}")
    print(f"\nBot1 needs: {bot1.declared} piles")
    print("Has pairs: CHARIOT pair, HORSE pair")
    print("Has singles: GENERAL, ADVISOR (openers)")
    print("Has burden: SOLDIER_RED, SOLDIER_BLACK (weak singles)\n")
    
    # Bot1 is starter
    game.current_turn_plays = []
    
    # Build context
    bot_handler = GameBotHandler("test_room", game)
    
    player_states = {}
    for player in game.players:
        player_states[player.name] = {
            "captured": game.pile_counts.get(player.name, 0),
            "declared": player.declared
        }
    
    context = TurnPlayContext(
        my_hand=bot1.hand,
        my_captured=0,
        my_declared=3,
        required_piece_count=None,  # Starter chooses
        turn_number=1,  # Early game
        pieces_per_player=8,  # Full hand
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states=player_states
    )
    
    # Bot decides
    result = choose_strategic_play(bot1.hand, context)
    
    print(f"Bot1 plays: {[str(p) for p in result]}")
    print(f"Play type: {'burden disposal' if all(p.point <= 3 for p in result) else 'strategic'}")
    
    # Early game with low urgency should dispose burdens
    if all(p.point <= 3 for p in result):
        print("✅ Bot correctly disposes burden pieces early")
    else:
        print("❌ Bot didn't dispose burdens as expected")


def test_no_burden_disposal_late_game():
    """Test that burden disposal stops when urgency increases."""
    print("\n=== Testing No Burden Disposal Late Game ===\n")
    
    players = [
        Player("Bot1", is_bot=True),
        Player("Human1", is_bot=False),
    ]
    
    game = Game(players)
    
    # Late game - Bot1 still needs piles
    game.pile_counts = {
        "Bot1": 1,  # Has 1
        "Human1": 2,
    }
    
    bot1 = players[0]
    bot1.declared = 3  # Needs 2 more
    bot1.hand = [
        Piece("GENERAL_RED"),      # 14
        Piece("SOLDIER_RED"),      # 2
        Piece("SOLDIER_BLACK"),    # 1
    ]
    
    print(f"Late game: Bot1 has {game.pile_counts['Bot1']}/{bot1.declared}")
    print(f"Pieces left: {len(bot1.hand)}")
    print(f"Hand: {[str(p) for p in bot1.hand]}")
    
    # Build context
    context = TurnPlayContext(
        my_hand=bot1.hand,
        my_captured=1,
        my_declared=3,
        required_piece_count=None,
        turn_number=6,  # Late game
        pieces_per_player=3,  # Few pieces left
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={"Bot1": {"captured": 1, "declared": 3}}
    )
    
    result = choose_strategic_play(bot1.hand, context)
    
    print(f"\nBot1 plays: {[str(p) for p in result]}")
    
    # Should play strong piece due to high urgency
    if result[0].point >= 11:
        print("✅ Bot plays strong piece when urgency is high")
    else:
        print("❌ Bot incorrectly disposed burdens when urgent")


def test_burden_disposal_preserves_combos():
    """Test that burden disposal doesn't break useful combos."""
    print("\n=== Testing Combo Preservation ===\n")
    
    players = [Player("Bot1", is_bot=True)]
    game = Game(players)
    
    bot1 = players[0]
    bot1.declared = 2
    bot1.hand = [
        Piece("CHARIOT_RED"),      # 8 - part of pair
        Piece("CHARIOT_BLACK"),    # 7 - part of pair
        Piece("SOLDIER_RED"),      # 2 - burden
        Piece("SOLDIER_BLACK"),    # 1 - burden
    ]
    
    game.pile_counts = {"Bot1": 0}
    
    print("Bot1 has CHARIOT pair (captures 2 piles)")
    print("Bot1 has SOLDIER singles (burdens)")
    print(f"Bot1 needs: {bot1.declared} piles")
    
    context = TurnPlayContext(
        my_hand=bot1.hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=None,
        turn_number=1,
        pieces_per_player=4,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=[],
        player_states={"Bot1": {"captured": 0, "declared": 2}}
    )
    
    result = choose_strategic_play(bot1.hand, context)
    
    print(f"\nBot1 plays: {[str(p) for p in result]}")
    
    # Should dispose soldiers, not chariots
    if all(p.name == "SOLDIER" for p in result):
        print("✅ Bot preserves useful CHARIOT pair, disposes SOLDIERs")
    else:
        print("❌ Bot broke up useful combo")


if __name__ == "__main__":
    print("Testing Burden Disposal in Game Scenarios...\n")
    
    test_burden_disposal_scenario()
    test_no_burden_disposal_late_game()
    test_burden_disposal_preserves_combos()
    
    print("\n✅ All game scenario tests completed!")