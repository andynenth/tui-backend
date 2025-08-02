# backend/tests/test_bot_redeal_timing.py

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from engine.bot_manager import GameBotHandler
from engine.game import Game
from engine.player import Player
from engine.state_machine.core import ActionType, GameAction


@pytest.mark.asyncio
async def test_bot_redeal_sequential_timing():
    """Test that bot redeal decisions have sequential delays matching declaration/turn timing"""

    # Create players with weak hands
    players = [
        Player("Human1", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True),
    ]

    game = Game(players)

    # Mock state machine
    mock_state_machine = Mock()
    mock_state_machine.handle_action = AsyncMock()

    handler = GameBotHandler("test_room", game, mock_state_machine)

    # Track redeal decision calls and timing
    decision_calls = []

    async def track_handle_action(action):
        if action.action_type in [
            ActionType.REDEAL_REQUEST,
            ActionType.REDEAL_RESPONSE,
        ]:
            decision_calls.append(
                {
                    "player": action.player_name,
                    "time": time.time(),
                    "action": action.action_type.value,
                    "accept": action.payload.get("accept", True),
                }
            )

    mock_state_machine.handle_action.side_effect = track_handle_action

    # Mock _get_game_state
    handler._get_game_state = Mock(return_value=game)

    # Test the sequential handler
    start_time = time.time()

    # Call the handler with bot weak players
    await handler._handle_simultaneous_redeal_decisions(
        {"bot_weak_players": ["Bot1", "Bot2", "Bot3"]}
    )

    # Should have 3 bot decisions
    assert (
        len(decision_calls) == 3
    ), f"Expected 3 bot decisions, got {len(decision_calls)}"

    # Check timing between decisions
    previous_time = start_time
    for i, call in enumerate(decision_calls):
        delay = call["time"] - previous_time
        print(f"Bot {call['player']} decided after {delay:.2f}s delay")

        # Each bot should have 0.5-1.5s delay (with small tolerance)
        assert (
            0.4 <= delay <= 1.7
        ), f"Bot {call['player']} delay {delay}s not in expected range"

        previous_time = call["time"]

    # Verify order matches input order
    assert [c["player"] for c in decision_calls] == ["Bot1", "Bot2", "Bot3"]

    # Verify all bots accepted redeal (current default behavior)
    assert all(
        c["accept"] for c in decision_calls
    ), "All bots should accept redeal by default"


@pytest.mark.asyncio
async def test_redeal_timing_matches_declaration():
    """Test that redeal timing pattern matches declaration timing"""

    players = [
        Player("Human", is_bot=False),
        Player("Bot1", is_bot=True),
        Player("Bot2", is_bot=True),
        Player("Bot3", is_bot=True),
    ]

    game = Game(players)
    mock_state_machine = Mock()
    mock_state_machine.handle_action = AsyncMock()

    handler = GameBotHandler("test_room", game, mock_state_machine)
    handler._get_game_state = Mock(return_value=game)

    # Track timings for both redeal and declaration
    redeal_times = []
    declare_times = []

    async def track_action(action):
        if action.action_type in [
            ActionType.REDEAL_REQUEST,
            ActionType.REDEAL_RESPONSE,
        ]:
            redeal_times.append(time.time())
        elif action.action_type == ActionType.DECLARE_PILE_COUNT:
            declare_times.append(time.time())

    mock_state_machine.handle_action.side_effect = track_action

    # Test redeal timing
    redeal_start = time.time()
    await handler._handle_simultaneous_redeal_decisions(
        {"bot_weak_players": ["Bot1", "Bot2", "Bot3"]}
    )

    # Test declaration timing for comparison
    handler._get_declaration_order = Mock(
        return_value=["Human", "Bot1", "Bot2", "Bot3"]
    )
    handler._bot_declare = AsyncMock(
        side_effect=lambda bot, pos: track_action(
            Mock(action_type=ActionType.DECLARE_PILE_COUNT, player_name=bot.name)
        )
    )

    await asyncio.sleep(0.1)  # Small gap between tests
    declare_start = time.time()
    await handler._handle_declaration_phase("Human")

    # Calculate average delays
    redeal_delays = []
    prev_time = redeal_start
    for t in redeal_times:
        redeal_delays.append(t - prev_time)
        prev_time = t

    declare_delays = []
    prev_time = declare_start
    for t in declare_times:
        declare_delays.append(t - prev_time)
        prev_time = t

    # Both should have similar delay patterns (0.5-1.5s range)
    print(f"Redeal delays: {[f'{d:.2f}s' for d in redeal_delays]}")
    print(f"Declaration delays: {[f'{d:.2f}s' for d in declare_delays]}")

    # Verify all delays are in the same range
    all_delays = redeal_delays + declare_delays
    assert all(
        0.4 <= d <= 1.7 for d in all_delays
    ), "All delays should be in 0.5-1.5s range"


@pytest.mark.asyncio
async def test_mixed_human_bot_redeal():
    """Test that redeal decisions work correctly with mixed human/bot players"""

    players = [
        Player("Bot1", is_bot=True),
        Player("Human1", is_bot=False),
        Player("Bot2", is_bot=True),
        Player("Human2", is_bot=False),
        Player("Bot3", is_bot=True),
    ]

    game = Game(players)
    mock_state_machine = Mock()
    mock_state_machine.handle_action = AsyncMock()

    handler = GameBotHandler("test_room", game, mock_state_machine)
    handler._get_game_state = Mock(return_value=game)

    decision_calls = []

    async def track_handle_action(action):
        if action.action_type in [
            ActionType.REDEAL_REQUEST,
            ActionType.REDEAL_RESPONSE,
        ]:
            decision_calls.append(action.player_name)

    mock_state_machine.handle_action.side_effect = track_handle_action

    # Only bot players should be processed
    await handler._handle_simultaneous_redeal_decisions(
        {"bot_weak_players": ["Bot1", "Bot2", "Bot3"]}
    )

    # Should only have bot decisions, no human decisions
    assert len(decision_calls) == 3
    assert set(decision_calls) == {"Bot1", "Bot2", "Bot3"}
    assert "Human1" not in decision_calls
    assert "Human2" not in decision_calls


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
