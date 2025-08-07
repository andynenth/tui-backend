# tests/ai_turn_play/test_turn_history_integration.py
"""
Comprehensive test for turn history implementation.

Tests the full integration:
1. Turn history accumulation in TurnState
2. Clearing in PreparationState
3. Revealed pieces extraction in bot_manager
4. AI receiving correct data
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import asyncio
from backend.engine.game import Game
from backend.engine.player import Player
from backend.engine.piece import Piece
from backend.engine.state_machine.game_state_machine import GameStateMachine
from backend.engine.state_machine.core import GamePhase, GameAction, ActionType
from backend.engine.bot_manager import GameBotHandler
from backend.engine.rules import get_play_type
from backend.engine.ai_turn_strategy import TurnPlayContext


async def test_turn_history_accumulation():
    """Test that turn history accumulates correctly through state machine."""
    print("\n=== Testing Turn History Accumulation ===\n")
    
    # Create game
    players = [
        Player("Bot1", is_bot=True),
        Player("Human1", is_bot=False),
        Player("Bot2", is_bot=True), 
        Player("Human2", is_bot=False)
    ]
    
    game = Game(players)
    state_machine = GameStateMachine(game)
    
    # Initialize state machine
    # Set initial phase
    state_machine.current_phase = GamePhase.TURN
    
    # Initialize the turn state
    turn_state = state_machine.states[GamePhase.TURN]
    
    # Verify turn history starts empty
    assert hasattr(game, 'turn_history_this_round'), "Game should have turn_history_this_round"
    assert len(game.turn_history_this_round) == 0, "Turn history should start empty"
    
    print("✅ Turn history initialized correctly")
    
    # Simulate a turn
    turn_state.turn_order = ["Bot1", "Human1", "Bot2", "Human2"]
    turn_state.current_turn_starter = "Bot1"
    game.turn_number = 1
    
    # Simulate plays
    turn_state.turn_plays = {
        "Bot1": {
            "pieces": [Piece("SOLDIER_BLACK")],
            "play_type": "SINGLE",
            "play_value": 1,
            "is_valid": True
        },
        "Human1": {
            "pieces": [Piece("CANNON_RED")],
            "play_type": "SINGLE", 
            "play_value": 4,
            "is_valid": True
        },
        "Bot2": {
            "pieces": [Piece("HORSE_RED")],
            "play_type": "SINGLE",
            "play_value": 6,
            "is_valid": True
        },
        "Human2": {
            "pieces": [Piece("GENERAL_RED")],
            "play_type": "SINGLE",
            "play_value": 14,
            "is_valid": True
        }
    }
    
    # Set winner
    turn_state.winner = "Human2"
    turn_state.required_piece_count = 1
    
    # Call _process_turn_completion to accumulate history
    await turn_state._process_turn_completion()
    
    # Check turn history
    assert len(game.turn_history_this_round) == 1, "Should have 1 turn in history"
    
    turn_summary = game.turn_history_this_round[0]
    print(f"Turn summary: {turn_summary}")
    
    assert turn_summary['turn_number'] == 1
    assert turn_summary['winner'] == "Human2"
    assert turn_summary['piles_won'] == 1
    assert len(turn_summary['plays']) == 4
    
    # Verify all plays recorded correctly
    for play in turn_summary['plays']:
        print(f"  {play['player']}: {[str(p) for p in play['pieces']]} ({play['play_type']})")
    
    print("\n✅ Turn history accumulation works correctly")


async def test_revealed_pieces_extraction():
    """Test that bot_manager correctly extracts revealed pieces."""
    print("\n=== Testing Revealed Pieces Extraction ===\n")
    
    # Create game with turn history
    players = [Player("Bot1", is_bot=True)]
    game = Game(players)
    
    # Add some turn history with forfeits
    game.turn_history_this_round = [
        {
            'turn_number': 1,
            'plays': [
                {'player': 'Bot1', 'pieces': [Piece("SOLDIER_BLACK")], 'play_type': 'SINGLE', 'is_valid': True},
                {'player': 'Human1', 'pieces': [Piece("GENERAL_RED")], 'play_type': 'SINGLE', 'is_valid': True},
            ],
            'winner': 'Human1',
            'piles_won': 1
        },
        {
            'turn_number': 2,
            'plays': [
                {'player': 'Human1', 'pieces': [Piece("CHARIOT_RED"), Piece("CHARIOT_RED")], 'play_type': 'PAIR', 'is_valid': True},
                {'player': 'Bot1', 'pieces': [Piece("SOLDIER_RED"), Piece("CANNON_BLACK")], 'play_type': None, 'is_valid': False},  # Forfeit!
            ],
            'winner': 'Human1',
            'piles_won': 2
        }
    ]
    
    # Create bot handler
    bot_handler = GameBotHandler("test_room", game)
    
    # Extract revealed pieces
    revealed = bot_handler._extract_revealed_pieces(game)
    
    print(f"Extracted {len(revealed)} revealed pieces:")
    for piece in revealed:
        print(f"  {piece}")
    
    # Should have 4 pieces (excluding the forfeit)
    assert len(revealed) == 4, f"Expected 4 revealed pieces, got {len(revealed)}"
    
    # Verify correct pieces
    piece_names = [p.name for p in revealed]
    assert "SOLDIER" in piece_names[0]
    assert "GENERAL" in piece_names[1]
    assert "CHARIOT" in piece_names[2]
    assert "CHARIOT" in piece_names[3]
    
    print("\n✅ Revealed pieces extraction works correctly (forfeits filtered)")


async def test_ai_receives_revealed_pieces():
    """Test that AI context receives revealed pieces correctly."""
    print("\n=== Testing AI Receives Revealed Pieces ===\n")
    
    # Create game
    players = [
        Player("Bot1", is_bot=True),
        Player("Human1", is_bot=False)
    ]
    
    game = Game(players)
    bot = players[0]
    bot.hand = [Piece("ADVISOR_BLACK"), Piece("CANNON_BLACK")]
    bot.declared = 2
    
    # Add turn history
    game.turn_history_this_round = [
        {
            'turn_number': 1,
            'plays': [
                {'player': 'Human1', 'pieces': [Piece("GENERAL_RED"), Piece("GENERAL_BLACK")], 'play_type': 'GENERAL_PAIR', 'is_valid': True},
                {'player': 'Bot1', 'pieces': [Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK")], 'play_type': 'PAIR', 'is_valid': True},
            ],
            'winner': 'Human1',
            'piles_won': 2
        }
    ]
    
    # Set up game state
    game.pile_counts = {"Bot1": 0, "Human1": 2}
    game.current_turn_plays = []  # Empty for new turn
    
    # Create bot handler and extract context
    bot_handler = GameBotHandler("test_room", game)
    
    # Simulate bot's turn context building
    revealed_pieces = bot_handler._extract_revealed_pieces(game)
    
    context = TurnPlayContext(
        my_hand=bot.hand,
        my_captured=0,
        my_declared=2,
        required_piece_count=1,
        turn_number=2,
        pieces_per_player=2,
        am_i_starter=True,
        current_plays=[],
        revealed_pieces=revealed_pieces,
        player_states={"Bot1": {"captured": 0, "declared": 2}, "Human1": {"captured": 2, "declared": 2}}
    )
    
    print(f"AI context has {len(context.revealed_pieces)} revealed pieces:")
    for piece in context.revealed_pieces:
        print(f"  {piece}")
    
    # AI can now make informed decisions
    generals_revealed = [p for p in context.revealed_pieces if 'GENERAL' in p.name]
    print(f"\nAI insight: {len(generals_revealed)} generals already played")
    
    assert len(context.revealed_pieces) == 4
    assert len(generals_revealed) == 2
    
    print("\n✅ AI receives revealed pieces correctly in context")


async def test_turn_history_cleared_new_round():
    """Test that turn history is cleared when new round starts."""
    print("\n=== Testing Turn History Cleared on New Round ===\n")
    
    # Create game with existing turn history
    players = [Player(f"P{i+1}") for i in range(4)]
    game = Game(players)
    
    # Add some turn history
    game.turn_history_this_round = [
        {'turn_number': 1, 'plays': [], 'winner': 'P1', 'piles_won': 1},
        {'turn_number': 2, 'plays': [], 'winner': 'P2', 'piles_won': 2}
    ]
    
    print(f"Before new round: {len(game.turn_history_this_round)} turns in history")
    
    # Create state machine and go to preparation phase
    state_machine = GameStateMachine(game)
    prep_state = state_machine.states[GamePhase.PREPARATION]
    
    # Deal cards (which should clear history)
    await prep_state._deal_cards()
    
    print(f"After new round: {len(game.turn_history_this_round)} turns in history")
    
    assert len(game.turn_history_this_round) == 0, "Turn history should be cleared"
    
    print("\n✅ Turn history correctly cleared for new round")


async def main():
    """Run all integration tests."""
    print("Testing Turn History Integration...\n")
    
    await test_turn_history_accumulation()
    await test_revealed_pieces_extraction()
    await test_ai_receives_revealed_pieces()
    await test_turn_history_cleared_new_round()
    
    print("\n✅ All integration tests passed! Turn history implementation complete.")


if __name__ == "__main__":
    asyncio.run(main())