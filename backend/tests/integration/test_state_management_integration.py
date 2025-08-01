"""
Integration tests for state management system.

Tests that state management is properly integrated with use cases
when the feature flag is enabled.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from application.use_cases.game.start_game import StartGameUseCase
from application.dto.game import StartGameRequest
from infrastructure.state_persistence.persistence_manager import (
    StatePersistenceManager,
    PersistenceConfig,
    PersistenceStrategy,
)
from infrastructure.state_persistence.abstractions import StateTransition
from application.adapters.state_management_adapter import StateManagementAdapter
from domain.entities.room import Room, RoomStatus
from domain.entities.player import Player
from domain.entities.game import Game
from domain.value_objects.game_phase import UnifiedGamePhase


@pytest.mark.asyncio
class TestStateManagementIntegration:
    """Test state management integration with use cases."""
    
    async def test_start_game_with_state_management_enabled(self):
        """Test that StartGameUseCase tracks state when adapter is provided."""
        # Arrange
        mock_uow = AsyncMock()
        mock_publisher = AsyncMock()
        mock_state_manager = AsyncMock(spec=StatePersistenceManager)
        
        # Create state adapter with mocked state manager
        state_adapter = StateManagementAdapter(
            state_manager=mock_state_manager,
            enabled=True  # Force enable for test
        )
        
        # Create use case with state adapter
        use_case = StartGameUseCase(
            unit_of_work=mock_uow,
            event_publisher=mock_publisher,
            state_adapter=state_adapter
        )
        
        # Mock room and game
        room = MagicMock(spec=Room)
        room.room_id = "test-room"
        room.host_id = "player1"
        room.status = RoomStatus.WAITING
        # Create player mocks
        player1 = MagicMock(spec=Player)
        player1.player_id = "player1"
        player1.id = "player1"  # Some code uses .id instead of .player_id
        player1.name = "Host"
        player1.is_bot = False
        player1.hand = []  # Empty hand initially
        player1.score = 0  # Initial score
        
        player2 = MagicMock(spec=Player)
        player2.player_id = "player2"
        player2.id = "player2"  # Some code uses .id instead of .player_id
        player2.name = "Player2"
        player2.is_bot = False
        player2.hand = []  # Empty hand initially
        player2.score = 0  # Initial score
        
        room.players = [player1, player2]
        room.slots = [player1, player2, None, None]  # 4 slots as per Room entity
        room.game = None  # No game in progress
        
        mock_uow.rooms.get_by_id.return_value = room
        mock_uow.games.get_by_room_id.return_value = None  # No existing game
        
        # Mock game creation
        mock_game = MagicMock(spec=Game)
        mock_game.room_id = "test-room"
        mock_game.current_phase = UnifiedGamePhase.NOT_STARTED
        mock_game.events = []
        mock_game.players = room.players
        mock_game.turn_order = ["player1", "player2"]
        mock_game.round_number = 1
        
        # Mock phase transitions and methods
        mock_game.start_game = MagicMock(side_effect=lambda: setattr(mock_game, 'current_phase', UnifiedGamePhase.PREPARATION))
        mock_game.start_round = MagicMock(side_effect=lambda: setattr(mock_game, 'current_phase', UnifiedGamePhase.DECLARATION))
        mock_game._emit_event = MagicMock()  # Mock event emission
        mock_game.round_starter = "Host"  # Set round starter
        mock_game.deal_cards = MagicMock()  # Mock deal_cards method
        mock_game.has_red_general = MagicMock(return_value=False)  # Mock has_red_general
        
        # Mock Game class constructor
        with patch('application.use_cases.game.start_game.Game', return_value=mock_game):
            # Act
            request = StartGameRequest(
                room_id="test-room",
                requesting_player_id="player1"
            )
            response = await use_case.execute(request)
        
        # Assert - Verify state tracking was called
        assert mock_state_manager.handle_transition.call_count >= 1
        
        # Verify game start transition
        first_call = mock_state_manager.handle_transition.call_args_list[0]
        transition = first_call[1]['transition']
        assert transition.from_state == "NOT_STARTED"
        assert transition.to_state == "PREPARATION"
        assert transition.action == "start_game"
        
        # Verify response (StartGameResponse doesn't have a 'success' attribute)
        assert response is not None
        assert response.game_id == "test-room"
        assert response.room_id == "test-room"
        
    async def test_start_game_without_state_management(self):
        """Test that StartGameUseCase works without state adapter."""
        # Arrange
        mock_uow = AsyncMock()
        mock_publisher = AsyncMock()
        
        # Create use case WITHOUT state adapter
        use_case = StartGameUseCase(
            unit_of_work=mock_uow,
            event_publisher=mock_publisher,
            state_adapter=None  # No state management
        )
        
        # Mock room and game (same as above)
        room = MagicMock(spec=Room)
        room.room_id = "test-room"
        room.host_id = "player1"
        room.status = RoomStatus.WAITING
        
        # Create player mocks
        player1 = MagicMock(spec=Player)
        player1.player_id = "player1"
        player1.id = "player1"  # Some code uses .id instead of .player_id
        player1.name = "Host"
        player1.is_bot = False
        player1.hand = []  # Empty hand initially
        player1.score = 0  # Initial score
        
        player2 = MagicMock(spec=Player)
        player2.player_id = "player2"
        player2.id = "player2"  # Some code uses .id instead of .player_id
        player2.name = "Player2"
        player2.is_bot = False
        player2.hand = []  # Empty hand initially
        player2.score = 0  # Initial score
        
        room.players = [player1, player2]
        room.slots = [player1, player2, None, None]  # 4 slots as per Room entity
        
        mock_uow.rooms.get_by_id.return_value = room
        mock_uow.games.get_by_room_id.return_value = None
        
        room.game = None  # Ensure room has no game
        
        mock_game = MagicMock(spec=Game)
        mock_game.room_id = "test-room"
        mock_game.current_phase = UnifiedGamePhase.NOT_STARTED
        mock_game.events = []
        mock_game.players = room.players
        mock_game.turn_order = ["player1", "player2"]
        mock_game.round_number = 1
        
        # Mock phase transitions and methods
        mock_game.start_game = MagicMock(side_effect=lambda: setattr(mock_game, 'current_phase', UnifiedGamePhase.PREPARATION))
        mock_game.start_round = MagicMock(side_effect=lambda: setattr(mock_game, 'current_phase', UnifiedGamePhase.DECLARATION))
        mock_game._emit_event = MagicMock()
        mock_game.round_starter = "Host"
        mock_game.deal_cards = MagicMock()
        mock_game.has_red_general = MagicMock(return_value=False)
        
        with patch('application.use_cases.game.start_game.Game', return_value=mock_game):
            # Act
            request = StartGameRequest(
                room_id="test-room",
                requesting_player_id="player1"
            )
            response = await use_case.execute(request)
        
        # Assert - Game should work without state management
        assert response is not None
        assert response.game_id == "test-room"
        assert response.room_id == "test-room"
        
    async def test_state_adapter_feature_flag_disabled(self):
        """Test that state adapter doesn't track when feature flag is disabled."""
        # Arrange
        mock_state_manager = AsyncMock(spec=StatePersistenceManager)
        
        # Create state adapter with feature flag disabled
        state_adapter = StateManagementAdapter(
            state_manager=mock_state_manager,
            enabled=False  # Force disable
        )
        
        # Act
        result = await state_adapter.track_game_start(
            game_id="test-game",
            room_id="test-room",
            players=["player1", "player2"],
            starting_player="player1"
        )
        
        # Assert
        assert result is True  # Should return True (success) even when disabled
        assert mock_state_manager.handle_transition.call_count == 0  # But no actual tracking
        
    async def test_state_adapter_handles_errors_gracefully(self):
        """Test that state adapter errors don't break game flow."""
        # Arrange
        mock_state_manager = AsyncMock(spec=StatePersistenceManager)
        mock_state_manager.handle_transition.side_effect = Exception("State manager error")
        
        state_adapter = StateManagementAdapter(
            state_manager=mock_state_manager,
            enabled=True
        )
        
        # Act
        result = await state_adapter.track_game_start(
            game_id="test-game",
            room_id="test-room",
            players=["player1", "player2"],
            starting_player="player1"
        )
        
        # Assert - Should return False but not raise
        assert result is False
        
    @pytest.mark.parametrize("from_phase,to_phase,expected_state", [
        (UnifiedGamePhase.NOT_STARTED, UnifiedGamePhase.PREPARATION, "PREPARATION"),
        (UnifiedGamePhase.PREPARATION, UnifiedGamePhase.DECLARATION, "DECLARATION"),
        (UnifiedGamePhase.DECLARATION, UnifiedGamePhase.TURN, "TURN"),
        (UnifiedGamePhase.TURN, UnifiedGamePhase.SCORING, "SCORING"),
        (UnifiedGamePhase.SCORING, UnifiedGamePhase.GAME_OVER, "GAME_OVER"),
    ])
    async def test_phase_transitions_tracked(self, from_phase, to_phase, expected_state):
        """Test that phase transitions are properly tracked."""
        # Arrange
        mock_state_manager = AsyncMock(spec=StatePersistenceManager)
        state_adapter = StateManagementAdapter(
            state_manager=mock_state_manager,
            enabled=True
        )
        
        context = state_adapter.create_context(
            game_id="test-game",
            room_id="test-room",
            player_id="player1"
        )
        
        # Act
        result = await state_adapter.track_phase_change(
            context=context,
            from_phase=from_phase,
            to_phase=to_phase,
            trigger="test_trigger"
        )
        
        # Assert
        assert result is True
        assert mock_state_manager.handle_transition.called
        
        transition = mock_state_manager.handle_transition.call_args[1]['transition']
        assert transition.to_state == expected_state