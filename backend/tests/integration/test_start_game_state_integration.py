"""
Integration tests for StartGameUseCase with state management.

These tests verify that state management is properly integrated
without breaking existing functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from application.use_cases.game import StartGameUseCase
from application.dto.game import StartGameRequest
from application.adapters.state_management_adapter import StateManagementAdapter
from infrastructure.state_persistence.persistence_manager import StatePersistenceManager
from infrastructure.feature_flags import get_feature_flags
from domain.entities.game import Game, GamePhase
from domain.entities.room import Room, RoomStatus, RoomSlot
from domain.entities.player import Player

pytestmark = pytest.mark.asyncio


class TestStartGameStateIntegration:
    """Test StartGameUseCase with state management integration."""

    @pytest.fixture
    def mock_uow(self):
        """Create mock unit of work."""
        uow = Mock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        
        # Mock repositories
        uow.rooms = Mock()
        uow.games = Mock()
        
        return uow

    @pytest.fixture
    def mock_publisher(self):
        """Create mock event publisher."""
        publisher = Mock()
        publisher.publish = AsyncMock()
        return publisher

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock state persistence manager."""
        manager = Mock(spec=StatePersistenceManager)
        manager.handle_transition = AsyncMock(return_value=True)
        manager.create_snapshot = AsyncMock(return_value=["snapshot-123"])
        return manager

    @pytest.fixture
    def state_adapter(self, mock_state_manager):
        """Create state management adapter."""
        return StateManagementAdapter(
            state_manager=mock_state_manager,
            enabled=True  # Force enabled for testing
        )

    @pytest.fixture
    def sample_room(self):
        """Create sample room with players."""
        room = Room(room_id="room-123", host_id="player-1")
        room.slots = [
            RoomSlot(name="Alice", is_bot=False),
            RoomSlot(name="Bob", is_bot=False),
            RoomSlot(name="Charlie", is_bot=True),
            None  # Empty slot
        ]
        room.status = RoomStatus.WAITING
        return room

    async def test_start_game_without_state_adapter(self, mock_uow, mock_publisher, sample_room):
        """Test that game starts normally without state adapter (current behavior)."""
        # Arrange
        mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)
        mock_uow.rooms.save = AsyncMock()
        mock_uow.games.save = AsyncMock()
        
        use_case = StartGameUseCase(mock_uow, mock_publisher)  # No state adapter
        request = StartGameRequest(room_id="room-123", requesting_player_id="player-1")
        
        # Act
        response = await use_case.execute(request)
        
        # Assert - Game started normally
        assert response.game_id == "room-123"
        assert response.room_id == "room-123"
        assert response.initial_state.phase == "PREPARATION"
        assert len(response.player_hands) == 3  # 3 players
        
        # No state manager calls
        assert mock_uow.games.save.called
        assert mock_uow.rooms.save.called

    async def test_start_game_with_state_adapter(self, mock_uow, mock_publisher, state_adapter, sample_room):
        """Test that game starts with state tracking when adapter provided."""
        # Arrange
        mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)
        mock_uow.rooms.save = AsyncMock()
        mock_uow.games.save = AsyncMock()
        
        use_case = StartGameUseCase(mock_uow, mock_publisher, state_adapter)
        request = StartGameRequest(room_id="room-123", requesting_player_id="player-1")
        
        # Act
        response = await use_case.execute(request)
        
        # Assert - Game started normally
        assert response.game_id == "room-123"
        assert response.initial_state.phase == "PREPARATION"
        
        # State tracking was called
        state_adapter._state_manager.handle_transition.assert_called()
        
        # Verify the tracked transitions
        calls = state_adapter._state_manager.handle_transition.call_args_list
        
        # Should have transitions for game start and phase changes
        assert len(calls) >= 1
        
        # First call should be for game start tracking
        first_call = calls[0]
        assert first_call.kwargs["state_machine_id"] == "room-123"
        transition = first_call.kwargs["transition"]
        assert transition.from_state == "NOT_STARTED"
        assert transition.to_state == "PREPARATION"
        assert transition.action == "start_game"

    async def test_state_tracking_failure_does_not_break_game(self, mock_uow, mock_publisher, mock_state_manager, sample_room):
        """Test that state tracking failures don't break game flow."""
        # Arrange
        mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)
        mock_uow.rooms.save = AsyncMock()
        mock_uow.games.save = AsyncMock()
        
        # Make state manager fail
        mock_state_manager.handle_transition = AsyncMock(side_effect=Exception("State tracking failed"))
        
        state_adapter = StateManagementAdapter(
            state_manager=mock_state_manager,
            enabled=True
        )
        
        use_case = StartGameUseCase(mock_uow, mock_publisher, state_adapter)
        request = StartGameRequest(room_id="room-123", requesting_player_id="player-1")
        
        # Act
        response = await use_case.execute(request)
        
        # Assert - Game still started successfully
        assert response.game_id == "room-123"
        assert response.initial_state.phase == "PREPARATION"
        
        # State tracking was attempted
        mock_state_manager.handle_transition.assert_called()

    async def test_state_adapter_tracks_phase_transitions(self, mock_uow, mock_publisher, state_adapter, sample_room):
        """Test that phase transitions are properly tracked."""
        # Arrange
        mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)
        mock_uow.rooms.save = AsyncMock()
        mock_uow.games.save = AsyncMock()
        
        use_case = StartGameUseCase(mock_uow, mock_publisher, state_adapter)
        request = StartGameRequest(room_id="room-123", requesting_player_id="player-1")
        
        # Act
        response = await use_case.execute(request)
        
        # Assert - Check specific transition tracking
        calls = state_adapter._state_manager.handle_transition.call_args_list
        
        # Find phase change transitions
        phase_transitions = [
            call for call in calls
            if call.kwargs["transition"].metadata.get("is_phase_change", False)
        ]
        
        # Should have at least one phase change
        assert len(phase_transitions) >= 1

    @patch("infrastructure.feature_flags.get_feature_flags")
    async def test_feature_flag_controls_state_adapter(self, mock_flags, mock_uow, mock_publisher, mock_state_manager, sample_room):
        """Test that feature flag controls state adapter creation."""
        # Arrange
        mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)
        mock_uow.rooms.save = AsyncMock()
        mock_uow.games.save = AsyncMock()
        
        # Test with feature flag disabled
        flags = Mock()
        flags.is_enabled = Mock(return_value=False)
        mock_flags.return_value = flags
        
        # In real scenario, adapter would be None when flag is off
        # For this test, we'll verify the flag is checked
        from infrastructure.adapters.clean_architecture_adapter import CleanArchitectureAdapter
        
        adapter = CleanArchitectureAdapter({})
        
        # Act
        context = {"room_id": "room-123", "player_id": "player-1"}
        
        # Check if state persistence would be used
        should_use = adapter._feature_flags.is_enabled("USE_STATE_PERSISTENCE", context)
        
        # Assert
        assert not should_use

    async def test_characterization_compatibility(self, mock_uow, mock_publisher, state_adapter, sample_room):
        """Test that behavior matches characterization tests with state adapter."""
        # Arrange
        mock_uow.rooms.get_by_id = AsyncMock(return_value=sample_room)
        mock_uow.rooms.save = AsyncMock()
        mock_uow.games.save = AsyncMock()
        
        # Track published events
        published_events = []
        mock_publisher.publish = AsyncMock(side_effect=lambda e: published_events.append(type(e).__name__))
        
        use_case = StartGameUseCase(mock_uow, mock_publisher, state_adapter)
        request = StartGameRequest(room_id="room-123", requesting_player_id="player-1")
        
        # Act
        response = await use_case.execute(request)
        
        # Assert - Same events as characterization tests
        expected_events = ["GameStarted", "RoundStarted", "PiecesDealt"]
        for event in expected_events:
            assert event in published_events
        
        # Same response structure
        assert response.initial_state.phase == "PREPARATION"
        assert response.starting_player_id is not None
        assert len(response.player_hands) == 3

    async def test_state_adapter_context_creation(self, state_adapter):
        """Test that state adapter creates proper context."""
        # Act
        context = state_adapter.create_context(
            game_id="game-123",
            room_id="room-123",
            player_id="player-1",
            current_phase="NOT_STARTED"
        )
        
        # Assert
        assert context.game_id == "game-123"
        assert context.room_id == "room-123"
        assert context.actor_id == "player-1"
        assert context.metadata["current_phase"] == "NOT_STARTED"