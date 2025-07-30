"""
Tests for the clean architecture adapter.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Callable

from infrastructure.adapters.clean_architecture_adapter import CleanArchitectureAdapter
from infrastructure.feature_flags import FeatureFlagManager, FeatureFlags
from application.dto.connection import HandlePingResponse
from application.dto.room_management import CreateRoomResponse
from application.dto.game import StartGameResponse


@pytest.fixture
def mock_legacy_handlers():
    """Create mock legacy handlers."""
    return {
        "ping": AsyncMock(return_value={"pong": True}),
        "create_room": AsyncMock(return_value={"room_id": "legacy_room"}),
        "start_game": AsyncMock(return_value={"game_started": True}),
        "unknown_event": AsyncMock(return_value={"handled": "legacy"}),
    }


@pytest.fixture
def mock_feature_flags():
    """Create mock feature flags."""
    flags = Mock(spec=FeatureFlagManager)
    flags.USE_CLEAN_ARCHITECTURE = FeatureFlags.USE_CLEAN_ARCHITECTURE
    flags.USE_CONNECTION_ADAPTERS = FeatureFlags.USE_CONNECTION_ADAPTERS
    flags.USE_ROOM_ADAPTERS = FeatureFlags.USE_ROOM_ADAPTERS
    flags.USE_GAME_ADAPTERS = FeatureFlags.USE_GAME_ADAPTERS
    return flags


@pytest.fixture
def adapter(mock_legacy_handlers, mock_feature_flags):
    """Create adapter instance with mocks."""
    with patch(
        "infrastructure.adapters.clean_architecture_adapter.get_feature_flags",
        return_value=mock_feature_flags,
    ):
        with patch(
            "infrastructure.adapters.clean_architecture_adapter.get_metrics_collector"
        ):
            return CleanArchitectureAdapter(mock_legacy_handlers)


class TestCleanArchitectureAdapter:
    """Test clean architecture adapter functionality."""

    @pytest.mark.asyncio
    async def test_legacy_fallback_when_disabled(self, adapter, mock_legacy_handlers):
        """Test that legacy handlers are used when clean architecture is disabled."""
        # Disable clean architecture
        adapter._feature_flags.is_enabled.return_value = False

        # Handle event
        result = await adapter.handle_event(
            "ping", {"sequence": 1}, {"player_id": "player1"}
        )

        # Should call legacy handler
        assert result == {"pong": True}
        mock_legacy_handlers["ping"].assert_called_once()

    @pytest.mark.asyncio
    async def test_clean_architecture_when_enabled(self, adapter):
        """Test that clean architecture is used when enabled."""
        # Enable clean architecture
        adapter._feature_flags.is_enabled.side_effect = lambda flag, ctx=None: True

        # Mock the use case response
        mock_response = Mock()
        mock_response.to_dict.return_value = {"sequence_number": 1, "success": True}

        with patch.object(
            adapter, "_handle_ping", return_value=mock_response.to_dict()
        ):
            result = await adapter.handle_event(
                "ping", {"sequence": 1}, {"player_id": "player1"}
            )

            assert result == {"sequence_number": 1, "success": True}

    @pytest.mark.asyncio
    async def test_feature_flag_granularity(self, adapter):
        """Test that specific feature flags control different adapters."""

        # Enable global flag but disable specific adapters
        def mock_is_enabled(flag, ctx=None):
            if flag == FeatureFlags.USE_CLEAN_ARCHITECTURE:
                return True
            elif flag == FeatureFlags.USE_CONNECTION_ADAPTERS:
                return False
            elif flag == FeatureFlags.USE_ROOM_ADAPTERS:
                return True
            elif flag == FeatureFlags.USE_GAME_ADAPTERS:
                return False
            return False

        adapter._feature_flags.is_enabled.side_effect = mock_is_enabled

        # Test connection event (should use legacy)
        await adapter.handle_event("ping", {}, {"player_id": "p1"})
        # Check that it fell back to legacy
        assert adapter._feature_flags.is_enabled.call_count >= 1

        # Reset mock
        adapter._feature_flags.is_enabled.reset_mock()

        # Test room event (should use clean architecture)
        # Note: Would need to mock the actual use case execution
        should_use = adapter._should_use_clean_architecture(
            "create_room", {"player_id": "p1"}
        )
        assert should_use is True

    @pytest.mark.asyncio
    async def test_metrics_collection(self, adapter):
        """Test that metrics are collected for successful requests."""
        # Enable clean architecture
        adapter._feature_flags.is_enabled.return_value = True

        # Mock metrics collector
        mock_metrics = Mock()
        adapter._metrics = mock_metrics

        # Mock use case response
        with patch.object(adapter, "_handle_ping", return_value={"success": True}):
            await adapter.handle_event(
                "ping", {"sequence": 1}, {"player_id": "player1"}
            )

            # Check metrics were recorded
            mock_metrics.timing.assert_called_once()
            call_args = mock_metrics.timing.call_args
            assert "clean_architecture.ping" in call_args[0]
            assert call_args[1]["tags"] == {"status": "success"}

    @pytest.mark.asyncio
    async def test_error_handling_and_metrics(self, adapter):
        """Test error handling and error metrics collection."""
        # Enable clean architecture
        adapter._feature_flags.is_enabled.return_value = True

        # Mock metrics collector
        mock_metrics = Mock()
        adapter._metrics = mock_metrics

        # Mock use case to raise error
        error = ValueError("Test error")
        with patch.object(adapter, "_handle_ping", side_effect=error):
            with pytest.raises(ValueError, match="Test error"):
                await adapter.handle_event(
                    "ping", {"sequence": 1}, {"player_id": "player1"}
                )

            # Check error metrics were recorded
            mock_metrics.increment.assert_called_once_with(
                "clean_architecture.ping.error", tags={"error_type": "ValueError"}
            )

    @pytest.mark.asyncio
    async def test_unknown_event_fallback(self, adapter, mock_legacy_handlers):
        """Test that unknown events fall back to legacy handlers."""
        # Enable clean architecture
        adapter._feature_flags.is_enabled.return_value = True

        # Handle unknown event
        result = await adapter.handle_event(
            "unknown_event", {"data": "test"}, {"player_id": "player1"}
        )

        # Should fall back to legacy
        assert result == {"handled": "legacy"}
        mock_legacy_handlers["unknown_event"].assert_called_once()

    @pytest.mark.asyncio
    async def test_ping_handler_integration(self, adapter):
        """Test the ping handler integration."""
        # Enable clean architecture
        adapter._feature_flags.is_enabled.return_value = True

        # Mock dependencies
        mock_uow = Mock()
        mock_metrics = Mock()
        mock_use_case = Mock()
        mock_response = HandlePingResponse(
            sequence_number=1, server_time=None, success=True
        )
        mock_use_case.execute = AsyncMock(return_value=mock_response)

        with patch(
            "infrastructure.adapters.clean_architecture_adapter.get_unit_of_work",
            return_value=mock_uow,
        ):
            with patch(
                "infrastructure.adapters.clean_architecture_adapter.get_metrics_collector",
                return_value=mock_metrics,
            ):
                with patch(
                    "infrastructure.adapters.clean_architecture.adapter.HandlePingUseCase",
                    return_value=mock_use_case,
                ):
                    result = await adapter._handle_ping(
                        {"sequence": 1}, {"player_id": "player1", "room_id": "room1"}
                    )

                    # Check result includes expected fields
                    assert result["success"] is True
                    assert result["sequence_number"] == 1

    @pytest.mark.asyncio
    async def test_create_room_handler_integration(self, adapter):
        """Test the create room handler integration."""
        # Mock dependencies
        mock_uow = Mock()
        mock_publisher = Mock()
        mock_use_case = Mock()
        mock_response = CreateRoomResponse(
            room_id="new_room", room_code="ABCD", success=True
        )
        mock_use_case.execute = AsyncMock(return_value=mock_response)

        with patch(
            "infrastructure.adapters.clean_architecture_adapter.get_unit_of_work",
            return_value=mock_uow,
        ):
            with patch(
                "infrastructure.adapters.clean_architecture_adapter.get_event_publisher",
                return_value=mock_publisher,
            ):
                with patch(
                    "infrastructure.adapters.clean_architecture_adapter.CreateRoomUseCase",
                    return_value=mock_use_case,
                ):
                    result = await adapter._handle_create_room(
                        {"player_name": "TestPlayer"}, {"player_id": "player1"}
                    )

                    # Check result
                    assert result["success"] is True
                    assert result["room_id"] == "new_room"
                    assert result["room_code"] == "ABCD"

    def test_use_case_mapping(self, adapter):
        """Test that all expected events are mapped to handlers."""
        expected_events = [
            "ping",
            "client_ready",
            "sync_state",
            "create_room",
            "join_room",
            "leave_room",
            "add_bot",
            "start_game",
            "declare",
            "play",
            "request_redeal",
            "accept_redeal",
            "decline_redeal",
        ]

        for event in expected_events:
            assert event in adapter._use_case_map
            assert callable(adapter._use_case_map[event])

    @pytest.mark.asyncio
    async def test_context_propagation(self, adapter):
        """Test that context is properly propagated to use cases."""
        # Enable clean architecture
        adapter._feature_flags.is_enabled.return_value = True

        context = {"player_id": "player1", "room_id": "room1", "game_id": "game1"}

        # Mock the declare handler to capture the request
        captured_request = None

        async def mock_declare_handler(data, ctx):
            nonlocal captured_request
            from application.dto.game import DeclareRequest

            captured_request = DeclareRequest(
                game_id=ctx["game_id"],
                player_id=ctx["player_id"],
                room_id=ctx["room_id"],
                declared_count=data["value"],
            )
            return {"success": True}

        adapter._handle_declare = mock_declare_handler

        await adapter.handle_event("declare", {"value": 3}, context)

        # Check context was properly propagated
        assert captured_request is not None
        assert captured_request.player_id == "player1"
        assert captured_request.room_id == "room1"
        assert captured_request.game_id == "game1"
        assert captured_request.declared_count == 3
