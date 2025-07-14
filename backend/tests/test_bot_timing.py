# backend/tests/test_bot_timing.py

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock, PropertyMock
from engine.state_machine.game_state_machine import GameStateMachine
from engine.state_machine.core import GameAction, ActionType, GamePhase
from engine.game import Game
from engine.player import Player
from engine.bot_manager import BotManager
import random


@pytest.mark.asyncio
@patch("engine.ai.choose_best_play")
async def test_bot_turn_play_timing(mock_choose_play):
    """Test that bot turn plays have consistent 0.5-1.5s delays matching declaration timing"""

    # Create game with 1 human and 3 bots
    players = [
        Player("Human", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True),
    ]

    game = Game(players)
    game.room_id = "test_room"  # Set room_id for game
    state_machine = GameStateMachine(game)
    state_machine.room_id = "test_room"  # Set room_id for state machine
    bot_manager = BotManager()
    bot_manager.register_game("test_room", game, state_machine)

    # Track bot play timings
    play_times = []
    original_bot_play = bot_manager.active_games["test_room"]._bot_play

    async def mock_bot_play(player):
        play_times.append({"player": player.name, "time": time.time()})
        # Simulate bot playing pieces
        return await original_bot_play(player)

    bot_manager.active_games["test_room"]._bot_play = mock_bot_play

    # Start state machine
    await state_machine.start()

    # Skip preparation phase and go directly to turn phase
    await state_machine._transition_to(GamePhase.TURN)

    # Set up turn state
    turn_state = state_machine.current_state
    turn_state.current_turn_starter = "Human"
    turn_state.turn_order = ["Human", "Bot1", "Bot2", "Bot3"]
    turn_state.current_player_index = 0
    turn_state.required_piece_count = None  # First player can play any count
    turn_state.turn_plays = {}  # Reset turn plays

    # Give all players some pieces to play
    for player in players:
        player.hand = [Mock(value=10, type="general") for _ in range(4)]

    # Mock AI to return one piece play from bot's hand
    def mock_ai_play(hand, **kwargs):
        return [hand[0]] if hand else []

    mock_choose_play.side_effect = mock_ai_play

    # Human plays first
    human_play_time = time.time()
    action = GameAction(
        action_type=ActionType.PLAY_PIECES,
        player_name="Human",
        payload={"indices": [0]},  # Play 1 piece
    )

    # Process human action
    await state_machine.handle_action(action)

    # Wait for all bots to play
    await asyncio.sleep(5)  # Max time for 3 bots with 1.5s delays each

    # Verify timing
    assert len(play_times) == 3, f"Expected 3 bot plays, got {len(play_times)}"

    # Check delays between plays
    previous_time = human_play_time
    for i, play_record in enumerate(play_times):
        delay = play_record["time"] - previous_time
        print(f"Bot {play_record['player']} played after {delay:.2f}s")

        # Verify delay is within expected range (0.5-1.5s)
        assert (
            0.4 <= delay <= 1.6
        ), f"Bot {play_record['player']} delay {delay}s outside 0.5-1.5s range"

        previous_time = play_record["time"]

    # Verify play order
    assert [p["player"] for p in play_times] == ["Bot1", "Bot2", "Bot3"]

    # Clean up
    bot_manager.unregister_game("test_room")


@pytest.mark.asyncio
@patch("engine.ai.choose_declare", return_value=2)
async def test_bot_declaration_timing_comparison(mock_choose_declare):
    """Test that declaration timing works as expected for comparison"""

    # Create game with 1 human and 3 bots
    players = [
        Player("Human", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True),
    ]

    game = Game(players)
    game.room_id = "test_room"  # Set room_id for game
    state_machine = GameStateMachine(game)
    state_machine.room_id = "test_room"  # Set room_id for state machine
    bot_manager = BotManager()
    bot_manager.register_game("test_room", game, state_machine)

    # Track declaration timings
    declare_times = []
    original_bot_declare = bot_manager.active_games["test_room"]._bot_declare

    async def mock_bot_declare(player, position):
        declare_times.append({"player": player.name, "time": time.time()})
        # Simulate bot declaring
        return await original_bot_declare(player, position)

    bot_manager.active_games["test_room"]._bot_declare = mock_bot_declare

    # Start state machine and advance to declaration phase
    await state_machine.start()
    await state_machine._transition_to(GamePhase.DECLARATION)

    # Set up declaration state
    declaration_state = state_machine.current_state
    declaration_state.declaration_order = ["Human", "Bot1", "Bot2", "Bot3"]
    declaration_state.current_declarer = "Human"
    declaration_state.current_declarer_index = 0

    # Give all players some pieces
    for player in players:
        player.hand = [Mock(value=10) for _ in range(8)]

    # Human declares first
    human_declare_time = time.time()
    action = GameAction(
        action_type=ActionType.DECLARE_PILE_COUNT,
        player_name="Human",
        payload={"value": 2},
    )

    # Process human action
    await state_machine.handle_action(action)

    # Wait for all bots to declare
    await asyncio.sleep(5)  # Max time for 3 bots with 1.5s delays each

    # Verify timing
    assert (
        len(declare_times) == 3
    ), f"Expected 3 bot declarations, got {len(declare_times)}"

    # Check delays between declarations
    previous_time = human_declare_time
    for i, declare_record in enumerate(declare_times):
        delay = declare_record["time"] - previous_time
        print(f"Bot {declare_record['player']} declared after {delay:.2f}s")

        # Verify delay is within expected range (0.5-1.5s)
        assert (
            0.4 <= delay <= 1.6
        ), f"Bot {declare_record['player']} delay {delay}s outside 0.5-1.5s range"

        previous_time = declare_record["time"]

    # Clean up
    bot_manager.unregister_game("test_room")


@pytest.mark.asyncio
@patch("engine.ai.choose_best_play")
async def test_turn_play_stops_at_human(mock_choose_play):
    """Test that bot sequential play stops when reaching a human player"""

    # Create game with alternating humans and bots
    players = [
        Player("Human1", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Human2", is_bot=False),
        Player("Bot2", is_bot=True),
    ]

    game = Game(players)
    game.room_id = "test_room"  # Set room_id for game
    state_machine = GameStateMachine(game)
    state_machine.room_id = "test_room"  # Set room_id for state machine
    bot_manager = BotManager()
    bot_manager.register_game("test_room", game, state_machine)

    # Track bot plays
    play_times = []
    original_bot_play = bot_manager.active_games["test_room"]._bot_play

    async def mock_bot_play(player):
        play_times.append({"player": player.name, "time": time.time()})
        return await original_bot_play(player)

    bot_manager.active_games["test_room"]._bot_play = mock_bot_play

    # Start state machine and advance to turn phase
    await state_machine.start()
    await state_machine._transition_to(GamePhase.TURN)

    # Set up turn state
    turn_state = state_machine.current_state
    turn_state.current_turn_starter = "Human1"
    turn_state.turn_order = ["Human1", "Bot1", "Human2", "Bot2"]
    turn_state.current_player_index = 0
    turn_state.required_piece_count = None
    turn_state.turn_plays = {}

    # Give all players some pieces
    for player in players:
        player.hand = [Mock(value=10, type="general") for _ in range(4)]

    # Mock AI to return one piece play from bot's hand
    def mock_ai_play(hand, **kwargs):
        return [hand[0]] if hand else []

    mock_choose_play.side_effect = mock_ai_play

    # Human1 plays first
    action = GameAction(
        action_type=ActionType.PLAY_PIECES,
        player_name="Human1",
        payload={"indices": [0]},
    )

    await state_machine.process_action(action)

    # Wait for bot to play
    await asyncio.sleep(2)

    # Only Bot1 should have played, stopping at Human2
    assert len(play_times) == 1, f"Expected 1 bot play, got {len(play_times)}"
    assert play_times[0]["player"] == "Bot1"

    # Clean up
    bot_manager.unregister_game("test_room")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
