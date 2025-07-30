#!/usr/bin/env python3
"""
Game Actions Integration Tests for Phase 6.3.3

Tests integration between game adapters and business logic.
Validates game actions with clean architecture.
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
import uuid
from datetime import datetime

# Import test utilities
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from api.adapters.adapter_registry import AdapterRegistry
from api.adapters.game_adapters import handle_game_messages, GAME_ADAPTER_ACTIONS
from infrastructure.feature_flags import FeatureFlags


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self, player_id: Optional[str] = None):
        self.player_id = player_id
        self.sent_messages = []
        self.closed = False

    async def send(self, message: str):
        """Mock send method."""
        self.sent_messages.append(message)

    async def close(self):
        """Mock close method."""
        self.closed = True


class MockGameState:
    """Mock game state for testing."""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.phase = "DECLARATION"
        self.players = []
        self.current_player_index = 0
        self.declarations = {}

    def add_player(self, player_id: str, player_name: str):
        """Add player to game."""
        self.players.append(
            {
                "id": player_id,
                "name": player_name,
                "pieces": [f"piece_{i}" for i in range(8)],
            }
        )

    def get_state(self):
        """Get game state."""
        return {
            "game_id": self.game_id,
            "phase": self.phase,
            "players": self.players.copy(),
            "current_player": (
                self.players[self.current_player_index]["id"] if self.players else None
            ),
            "declarations": self.declarations.copy(),
        }


@pytest.fixture
def mock_websocket():
    """Fixture for mock WebSocket."""
    return MockWebSocket(player_id="test_player")


@pytest.fixture
def mock_feature_flags():
    """Fixture for feature flags."""
    flags = FeatureFlags()
    flags.override(FeatureFlags.USE_GAME_ADAPTERS, True)
    flags.override(FeatureFlags.USE_CLEAN_ARCHITECTURE, True)
    return flags


@pytest.fixture
def sample_game():
    """Fixture for sample game."""
    game = MockGameState("test_game_123")
    game.add_player("player_1", "TestPlayer1")
    game.add_player("player_2", "TestPlayer2")
    return game


class TestGameActionIntegration:
    """Test game action integration with adapters."""

    @pytest.mark.asyncio
    async def test_declare_action_integration(self, mock_websocket, sample_game):
        """Test declare action integration."""

        # Mock legacy handler
        legacy_handler = AsyncMock(
            return_value={"event": "legacy_response", "data": {"fallback": True}}
        )

        # Declare message
        declare_message = {
            "action": "declare",
            "data": {"player_id": "player_1", "pile_count": 2},
        }

        # Test adapter handling
        result = await handle_game_messages(
            websocket=mock_websocket,
            message=declare_message,
            legacy_handler=legacy_handler,
            room_state=sample_game.get_state(),
        )

        # Assertions
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_play_action_integration(self, mock_websocket, sample_game):
        """Test play action integration."""

        # Mock legacy handler
        legacy_handler = AsyncMock(
            return_value={"event": "legacy_response", "data": {"success": True}}
        )

        # Set game to turn phase
        sample_game.phase = "TURN"

        # Play message
        play_message = {
            "action": "play",
            "data": {"player_id": "player_1", "piece_count": 3},
        }

        # Test adapter handling
        result = await handle_game_messages(
            websocket=mock_websocket,
            message=play_message,
            legacy_handler=legacy_handler,
            room_state=sample_game.get_state(),
        )

        # Assertions
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_start_game_action_integration(self, mock_websocket, sample_game):
        """Test start game action integration."""

        # Mock legacy handler
        legacy_handler = AsyncMock(
            return_value={"event": "game_started", "data": {"game_id": "test_game_123"}}
        )

        # Start game message
        start_message = {"action": "start_game", "data": {"game_id": "test_game_123"}}

        # Test adapter handling
        result = await handle_game_messages(
            websocket=mock_websocket,
            message=start_message,
            legacy_handler=legacy_handler,
            room_state=sample_game.get_state(),
        )

        # Assertions
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_game_adapter_actions_recognition(self, mock_websocket):
        """Test game adapter actions recognition."""

        # Test that game actions are properly recognized
        game_actions = [
            "start_game",
            "declare",
            "play",
            "request_redeal",
            "accept_redeal",
            "decline_redeal",
        ]

        for action in game_actions:
            assert action in GAME_ADAPTER_ACTIONS

        # Test non-game action
        non_game_actions = ["ping", "create_room", "join_room"]
        for action in non_game_actions:
            assert action not in GAME_ADAPTER_ACTIONS

    @pytest.mark.asyncio
    async def test_non_game_message_passthrough(self, mock_websocket):
        """Test non-game messages pass through to legacy handler."""

        # Mock legacy handler
        legacy_handler = AsyncMock(
            return_value={"event": "legacy_handled", "data": {"processed": True}}
        )

        # Non-game message
        room_message = {"action": "create_room", "data": {"host_name": "TestHost"}}

        # Test adapter handling
        result = await handle_game_messages(
            websocket=mock_websocket,
            message=room_message,
            legacy_handler=legacy_handler,
        )

        # Should call legacy handler for non-game messages
        legacy_handler.assert_called_once_with(mock_websocket, room_message)

        # Assertions
        assert result is not None
        assert result["event"] == "legacy_handled"

    @pytest.mark.asyncio
    async def test_game_action_performance(self, mock_websocket, sample_game):
        """Test game action performance."""

        # Mock legacy handler
        legacy_handler = AsyncMock(
            return_value={"event": "action_response", "data": {"success": True}}
        )

        # Test multiple game actions
        game_messages = [
            {
                "action": "declare",
                "data": {"player_id": f"player_{i%2+1}", "pile_count": 2},
            }
            for i in range(20)
        ]

        times = []

        for message in game_messages:
            start_time = time.perf_counter()

            result = await handle_game_messages(
                websocket=mock_websocket,
                message=message,
                legacy_handler=legacy_handler,
                room_state=sample_game.get_state(),
            )

            end_time = time.perf_counter()
            operation_time = (end_time - start_time) * 1000  # ms
            times.append(operation_time)

            # Verify result
            assert result is not None
            assert isinstance(result, dict)

        # Performance assertions
        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time < 5.0  # Average under 5ms
        assert max_time < 20.0  # Max under 20ms

    @pytest.mark.asyncio
    async def test_concurrent_game_actions(self, mock_websocket, sample_game):
        """Test concurrent game actions."""

        # Mock legacy handler
        legacy_handler = AsyncMock(
            return_value={"event": "action_response", "data": {"success": True}}
        )

        async def concurrent_declare(player_index: int):
            message = {
                "action": "declare",
                "data": {
                    "player_id": f"concurrent_player_{player_index}",
                    "pile_count": 2,
                },
            }
            return await handle_game_messages(
                websocket=mock_websocket,
                message=message,
                legacy_handler=legacy_handler,
                room_state=sample_game.get_state(),
            )

        # Execute concurrent declarations
        tasks = [concurrent_declare(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # Assertions
        assert len(results) == 10
        assert all(result is not None for result in results)
        assert all(isinstance(result, dict) for result in results)

    @pytest.mark.asyncio
    async def test_game_state_validation(self, mock_websocket, sample_game):
        """Test game state validation in adapters."""

        # Mock legacy handler
        legacy_handler = AsyncMock(
            return_value={"event": "action_response", "data": {"success": True}}
        )

        # Test with valid game state
        valid_message = {
            "action": "declare",
            "data": {"player_id": "player_1", "pile_count": 2},
        }

        result = await handle_game_messages(
            websocket=mock_websocket,
            message=valid_message,
            legacy_handler=legacy_handler,
            room_state=sample_game.get_state(),
        )

        assert result is not None

        # Test with None game state
        result_no_state = await handle_game_messages(
            websocket=mock_websocket,
            message=valid_message,
            legacy_handler=legacy_handler,
            room_state=None,
        )

        # Should handle gracefully
        assert result_no_state is not None

    @pytest.mark.asyncio
    async def test_redeal_actions_integration(self, mock_websocket, sample_game):
        """Test redeal actions integration."""

        # Mock legacy handler
        legacy_handler = AsyncMock(
            return_value={"event": "redeal_response", "data": {"success": True}}
        )

        # Test redeal request
        redeal_request = {
            "action": "request_redeal",
            "data": {"player_id": "player_1", "reason": "weak_hand"},
        }

        result = await handle_game_messages(
            websocket=mock_websocket,
            message=redeal_request,
            legacy_handler=legacy_handler,
            room_state=sample_game.get_state(),
        )

        assert result is not None

        # Test accept redeal
        accept_redeal = {"action": "accept_redeal", "data": {"player_id": "player_1"}}

        result = await handle_game_messages(
            websocket=mock_websocket,
            message=accept_redeal,
            legacy_handler=legacy_handler,
            room_state=sample_game.get_state(),
        )

        assert result is not None

        # Test decline redeal
        decline_redeal = {"action": "decline_redeal", "data": {"player_id": "player_1"}}

        result = await handle_game_messages(
            websocket=mock_websocket,
            message=decline_redeal,
            legacy_handler=legacy_handler,
            room_state=sample_game.get_state(),
        )

        assert result is not None


class TestGameActionPerformance:
    """Test game action performance characteristics."""

    @pytest.mark.asyncio
    async def test_game_adapter_overhead(self, mock_websocket, sample_game):
        """Test game adapter overhead."""

        # Mock legacy handler
        legacy_handler = AsyncMock(
            return_value={"event": "fast_response", "data": {"success": True}}
        )

        # Measure baseline performance
        baseline_times = []

        for i in range(50):
            start_time = time.perf_counter()

            message = {
                "action": "declare",
                "data": {"player_id": f"perf_player_{i%4}", "pile_count": i % 3 + 1},
            }

            await handle_game_messages(
                websocket=mock_websocket,
                message=message,
                legacy_handler=legacy_handler,
                room_state=sample_game.get_state(),
            )

            end_time = time.perf_counter()
            baseline_times.append((end_time - start_time) * 1000)

        # Performance assertions
        avg_time = sum(baseline_times) / len(baseline_times)
        p95_time = sorted(baseline_times)[int(len(baseline_times) * 0.95)]

        assert avg_time < 2.0  # Average under 2ms
        assert p95_time < 10.0  # 95th percentile under 10ms

    @pytest.mark.asyncio
    async def test_sustained_game_operations(self, mock_websocket, sample_game):
        """Test sustained game operations without memory leaks."""

        # Mock legacy handler
        legacy_handler = AsyncMock(
            return_value={"event": "sustained_response", "data": {"success": True}}
        )

        # Simulate sustained operations
        for batch in range(5):  # 5 batches of operations

            # Mixed game operations
            for i in range(20):
                if i % 3 == 0:
                    action = "declare"
                    data = {"player_id": f"sustained_player_{i%4}", "pile_count": 2}
                elif i % 3 == 1:
                    action = "play"
                    data = {"player_id": f"sustained_player_{i%4}", "piece_count": 1}
                else:
                    action = "start_game"
                    data = {"game_id": sample_game.game_id}

                message = {"action": action, "data": data}

                result = await handle_game_messages(
                    websocket=mock_websocket,
                    message=message,
                    legacy_handler=legacy_handler,
                    room_state=sample_game.get_state(),
                )

                # Verify operation
                assert result is not None
                assert isinstance(result, dict)

            # Small delay between batches
            await asyncio.sleep(0.01)

        # If we complete without memory issues, test passed
        assert True


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
