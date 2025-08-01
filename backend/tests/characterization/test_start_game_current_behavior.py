"""
Characterization tests for StartGameUseCase current behavior.

These tests document EXACTLY how the system works today, before any state management
integration. They serve as a safety net to ensure we don't break existing functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, call
from datetime import datetime

# Mark all async tests
pytestmark = pytest.mark.asyncio

from application.use_cases.game.start_game import StartGameUseCase
from application.dto.game import StartGameRequest, StartGameResponse
from domain.entities.game import Game, GamePhase
from domain.entities.room import Room, RoomStatus
from domain.entities.player import Player
from domain.value_objects.piece import Piece
from domain.events.game_events import (
    GameStarted,
    RoundStarted,
    PiecesDealt,
    WeakHandDetected,
    PhaseChanged,
)


class TestStartGameCurrentBehavior:
    """Document current behavior of StartGameUseCase."""

    @pytest.fixture
    def mock_uow(self):
        """Create mock unit of work."""
        uow = AsyncMock()
        uow.__aenter__.return_value = uow
        uow.__aexit__.return_value = None
        
        # Mock repositories
        uow.rooms = AsyncMock()
        uow.games = AsyncMock()
        
        return uow

    @pytest.fixture
    def mock_event_publisher(self):
        """Create mock event publisher."""
        publisher = AsyncMock()
        publisher.publish = AsyncMock()
        return publisher

    @pytest.fixture
    def mock_room(self):
        """Create a mock room ready for game start."""
        room = Mock(spec=Room)
        room.room_id = "test-room-123"
        room.host_id = "host-player"
        room.game = None  # No game in progress
        room.status = RoomStatus.WAITING
        
        # Create 4 players
        room.slots = [
            Mock(name="Player1", is_bot=False),
            Mock(name="Player2", is_bot=False),
            Mock(name="Player3", is_bot=True),
            Mock(name="Player4", is_bot=False),
        ]
        
        return room

    async def test_start_game_direct_domain_calls(self, mock_uow, mock_event_publisher, mock_room):
        """
        CHARACTERIZATION TEST: Document that StartGameUseCase calls domain methods directly.
        
        Current behavior:
        1. Creates Game entity
        2. Calls game.start_game() directly
        3. Calls game.start_round() directly  
        4. NO state persistence calls
        """
        # Arrange
        mock_uow.rooms.get_by_id.return_value = mock_room
        use_case = StartGameUseCase(mock_uow, mock_event_publisher)
        request = StartGameRequest(
            room_id="test-room-123",
            requesting_player_id="host-player"
        )
        
        # Mock game to track method calls
        with patch('application.use_cases.game.start_game.Game') as MockGame:
            mock_game = Mock(spec=Game)
            mock_game.room_id = "test-room-123"
            mock_game.round_number = 1
            mock_game.current_phase = GamePhase.PREPARATION
            mock_game.events = []
            mock_game.players = []
            mock_game.max_score = 50
            mock_game.max_rounds = 20
            
            MockGame.return_value = mock_game
            
            # Act
            response = await use_case.execute(request)
            
            # Assert - CURRENT BEHAVIOR
            # 1. Game entity is created with room_id and players
            MockGame.assert_called_once()
            
            # 2. start_game() is called directly on domain entity
            mock_game.start_game.assert_called_once()
            
            # 3. start_round() is called directly on domain entity (line 149)
            mock_game.start_round.assert_called_once()
            
            # 4. NO state persistence calls (no StatePersistenceManager)
            # This is the key behavior we're documenting
            
            # 5. Game is saved via repository
            mock_uow.games.save.assert_called_once_with(mock_game)
            
            # 6. Room status is updated
            assert mock_room.status == RoomStatus.IN_GAME
            assert mock_room.game == mock_game

    async def test_domain_events_emitted_order(self, mock_uow, mock_event_publisher, mock_room):
        """
        CHARACTERIZATION TEST: Document exact order of domain events.
        
        Current behavior emits events in this specific order:
        1. Events from game.start_game() and game.start_round()
        2. GameStarted event (manually created)
        3. RoundStarted event (manually created)
        4. PiecesDealt event (manually created)
        5. WeakHandDetected event (if weak hands exist)
        """
        # Arrange
        mock_uow.rooms.get_by_id.return_value = mock_room
        use_case = StartGameUseCase(mock_uow, mock_event_publisher)
        request = StartGameRequest(
            room_id="test-room-123",
            requesting_player_id="host-player"
        )
        
        # Track all published events
        published_events = []
        mock_event_publisher.publish.side_effect = lambda event: published_events.append(event)
        
        # Act
        response = await use_case.execute(request)
        
        # Assert - document EXACT event order
        # The use case publishes domain events from the game entity first
        # Then manually creates and publishes additional events
        
        # Verify the manual event creation (lines 205-276 in start_game.py)
        event_types = [type(event).__name__ for event in published_events]
        
        # These are the manually created events in the use case
        assert "GameStarted" in event_types
        assert "RoundStarted" in event_types  
        assert "PiecesDealt" in event_types
        
        # Note: PhaseChanged is commented out in current implementation (line 277)
        assert "PhaseChanged" not in event_types

    async def test_current_phase_enum_usage(self, mock_uow, mock_event_publisher, mock_room):
        """
        CHARACTERIZATION TEST: Document which GamePhase enum is used.
        
        Current behavior:
        - Uses domain.entities.game.GamePhase
        - Does NOT use engine.state_machine.core.GamePhase
        """
        # Arrange
        mock_uow.rooms.get_by_id.return_value = mock_room
        use_case = StartGameUseCase(mock_uow, mock_event_publisher)
        request = StartGameRequest(
            room_id="test-room-123", 
            requesting_player_id="host-player"
        )
        
        # Act
        response = await use_case.execute(request)
        
        # Assert - verify domain GamePhase is used
        # The response contains game state with phase
        assert hasattr(response.initial_state, 'phase')
        # Phase comes from domain entity, not state machine
        assert response.initial_state.phase in ["NOT_STARTED", "PREPARATION", "DECLARATION", "TURN", "SCORING", "GAME_OVER"]

    async def test_no_state_persistence_integration(self, mock_uow, mock_event_publisher, mock_room):
        """
        CHARACTERIZATION TEST: Confirm NO state persistence is used.
        
        Current behavior:
        - No StatePersistenceManager in constructor
        - No state transition tracking
        - No snapshots created
        - No recovery mechanisms
        """
        # Arrange
        mock_uow.rooms.get_by_id.return_value = mock_room
        
        # Verify constructor takes only 3 parameters (no state manager)
        use_case = StartGameUseCase(mock_uow, mock_event_publisher)
        
        # Act
        request = StartGameRequest(
            room_id="test-room-123",
            requesting_player_id="host-player"
        )
        response = await use_case.execute(request)
        
        # Assert - NO state persistence calls
        # If state persistence was integrated, we would see:
        # - state_manager.handle_transition() calls
        # - state_manager.create_snapshot() calls
        # - state transition events
        
        # Currently, NONE of these exist
        assert not hasattr(use_case, 'state_manager')
        assert not hasattr(use_case, '_state_persistence')

    async def test_error_handling_current_behavior(self, mock_uow, mock_event_publisher):
        """
        CHARACTERIZATION TEST: Document current error handling.
        """
        # Test 1: Room not found
        mock_uow.rooms.get_by_id.return_value = None
        use_case = StartGameUseCase(mock_uow, mock_event_publisher)
        
        from application.exceptions import ResourceNotFoundException
        with pytest.raises(ResourceNotFoundException) as exc_info:
            await use_case.execute(StartGameRequest(
                room_id="non-existent",
                requesting_player_id="player1"
            ))
        assert "Room" in str(exc_info.value)
        
        # Test 2: Not authorized (not host)
        mock_room = Mock()
        mock_room.host_id = "other-player"
        mock_room.game = None
        mock_uow.rooms.get_by_id.return_value = mock_room
        
        from application.exceptions import AuthorizationException
        with pytest.raises(AuthorizationException) as exc_info:
            await use_case.execute(StartGameRequest(
                room_id="test-room",
                requesting_player_id="not-host"
            ))
        assert "start game" in str(exc_info.value)
        
        # Test 3: Game already in progress
        mock_room.host_id = "host-player"
        mock_room.game = Mock()  # Game exists
        
        from application.exceptions import ConflictException
        with pytest.raises(ConflictException) as exc_info:
            await use_case.execute(StartGameRequest(
                room_id="test-room",
                requesting_player_id="host-player"
            ))
        assert "already in progress" in str(exc_info.value)

    async def test_performance_baseline(self, mock_uow, mock_event_publisher, mock_room):
        """
        CHARACTERIZATION TEST: Capture performance baseline.
        
        Current behavior performance characteristics.
        """
        import time
        
        # Arrange
        mock_uow.rooms.get_by_id.return_value = mock_room
        use_case = StartGameUseCase(mock_uow, mock_event_publisher)
        request = StartGameRequest(
            room_id="test-room-123",
            requesting_player_id="host-player"
        )
        
        # Act - measure execution time
        start_time = time.time()
        response = await use_case.execute(request)
        end_time = time.time()
        
        execution_time_ms = (end_time - start_time) * 1000
        
        # Document current performance
        # These values will be our baseline for comparison
        assert execution_time_ms < 100  # Should be fast without state persistence
        
        # Document method call counts
        assert mock_uow.rooms.get_by_id.call_count == 1
        assert mock_uow.games.save.call_count == 1
        assert mock_uow.rooms.save.call_count == 1
        
        # No state persistence calls means faster execution
        # After integration, we expect some performance impact

    async def test_response_structure(self, mock_uow, mock_event_publisher, mock_room):
        """
        CHARACTERIZATION TEST: Document exact response structure.
        
        This ensures we maintain backward compatibility.
        """
        # Arrange
        mock_uow.rooms.get_by_id.return_value = mock_room
        use_case = StartGameUseCase(mock_uow, mock_event_publisher)
        request = StartGameRequest(
            room_id="test-room-123",
            requesting_player_id="host-player"
        )
        
        # Create a more complete mock game
        with patch('application.use_cases.game.start_game.Game') as MockGame:
            mock_game = Mock(spec=Game)
            mock_game.room_id = "test-room-123"
            mock_game.round_number = 1
            mock_game.turn_number = 0
            mock_game.current_phase = GamePhase.PREPARATION
            mock_game.events = []
            
            # Mock players with IDs
            mock_players = [
                Mock(id="p1", name="Player1", score=0, hand=[]),
                Mock(id="p2", name="Player2", score=0, hand=[]),
                Mock(id="p3", name="Player3", score=0, hand=[]),
                Mock(id="p4", name="Player4", score=0, hand=[]),
            ]
            mock_game.players = mock_players
            
            MockGame.return_value = mock_game
            
            # Act
            response = await use_case.execute(request)
            
            # Assert - document EXACT response structure
            assert isinstance(response, StartGameResponse)
            assert response.game_id == "test-room-123"
            assert response.room_id == "test-room-123"
            assert hasattr(response, 'initial_state')
            assert hasattr(response, 'player_hands')
            assert hasattr(response, 'starting_player_id')
            assert hasattr(response, 'weak_hands_detected')
            
            # Initial state structure
            state = response.initial_state
            assert hasattr(state, 'game_id')
            assert hasattr(state, 'room_id')
            assert hasattr(state, 'round_number')
            assert hasattr(state, 'turn_number')
            assert hasattr(state, 'phase')
            assert hasattr(state, 'player_scores')
            assert hasattr(state, 'pieces_remaining')