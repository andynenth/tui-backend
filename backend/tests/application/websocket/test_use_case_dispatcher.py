"""
Unit tests for UseCaseDispatcher
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import time
import uuid

from application.websocket.use_case_dispatcher import UseCaseDispatcher, DispatchContext
from application.dto.connection import PingResponse, ClientReadyResponse
from application.dto.room_management import CreateRoomResponse, JoinRoomResponse, RoomInfoDTO, PlayerInfoDTO
from application.dto.lobby import GetRoomListResponse, RoomSummaryDTO


@pytest.fixture
def mock_dependencies():
    """Mock all dependencies"""
    with patch('application.websocket.use_case_dispatcher.get_unit_of_work') as mock_uow, \
         patch('application.websocket.use_case_dispatcher.get_event_publisher') as mock_publisher, \
         patch('application.websocket.use_case_dispatcher.get_metrics_collector') as mock_metrics, \
         patch('application.websocket.use_case_dispatcher.get_bot_service') as mock_bot, \
         patch('application.websocket.use_case_dispatcher.get_game_service') as mock_game, \
         patch('application.websocket.use_case_dispatcher.get_game_state_store') as mock_store:
        
        yield {
            'uow': mock_uow.return_value,
            'publisher': mock_publisher.return_value,
            'metrics': mock_metrics.return_value,
            'bot_service': mock_bot.return_value,
            'game_service': mock_game.return_value,
            'game_state_store': mock_store.return_value
        }


@pytest.fixture
def dispatcher(mock_dependencies):
    """Create dispatcher with mocked dependencies"""
    return UseCaseDispatcher()


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection"""
    ws = Mock()
    ws._connection_id = "test_connection_123"
    return ws


@pytest.fixture
def dispatch_context(mock_websocket):
    """Create dispatch context"""
    return DispatchContext(
        websocket=mock_websocket,
        room_id="test_room",
        player_id="test_player",
        player_name="Test Player"
    )


class TestUseCaseDispatcher:
    """Test UseCaseDispatcher functionality"""
    
    @pytest.mark.asyncio
    async def test_dispatcher_initialization(self, dispatcher):
        """Test dispatcher initializes with all use cases"""
        assert dispatcher.uow is not None
        assert dispatcher.event_publisher is not None
        assert dispatcher.metrics is not None
        
        # Check all use cases are initialized
        assert hasattr(dispatcher, 'ping_use_case')
        assert hasattr(dispatcher, 'create_room_use_case')
        assert hasattr(dispatcher, 'start_game_use_case')
        
        # Check event handlers are mapped
        assert len(dispatcher.event_handlers) == 22  # All 22 events
        assert 'ping' in dispatcher.event_handlers
        assert 'create_room' in dispatcher.event_handlers
        assert 'play_pieces' in dispatcher.event_handlers  # Alias
    
    @pytest.mark.asyncio
    async def test_dispatch_unknown_event(self, dispatcher, dispatch_context):
        """Test dispatching unknown event returns None"""
        result = await dispatcher.dispatch(
            'unknown_event',
            {},
            dispatch_context
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_dispatch_error_handling(self, dispatcher, dispatch_context):
        """Test error handling in dispatch"""
        # Mock handler to raise exception
        dispatcher.event_handlers['ping'] = AsyncMock(side_effect=Exception("Test error"))
        
        result = await dispatcher.dispatch(
            'ping',
            {},
            dispatch_context
        )
        
        assert result is not None
        assert result['event'] == 'error'
        assert result['data']['type'] == 'use_case_error'
        assert 'Test error' in result['data']['details']
    
    # Connection event tests
    
    @pytest.mark.asyncio
    async def test_handle_ping(self, dispatcher, dispatch_context):
        """Test ping event handling"""
        # Mock use case response
        mock_response = PingResponse(
            server_timestamp=time.time(),
            client_timestamp=time.time() - 0.1,
            latency_ms=100,
            sequence_number=42
        )
        dispatcher.ping_use_case.execute = AsyncMock(return_value=mock_response)
        
        result = await dispatcher.dispatch(
            'ping',
            {'timestamp': time.time(), 'sequence': 42},
            dispatch_context
        )
        
        assert result['event'] == 'pong'
        assert result['data']['latency'] == 100
        assert result['data']['sequence'] == 42
    
    @pytest.mark.asyncio
    async def test_handle_client_ready(self, dispatcher, dispatch_context):
        """Test client_ready event handling"""
        mock_response = ClientReadyResponse(
            acknowledged=True,
            server_version="1.0.0",
            available_features=["game", "chat"]
        )
        dispatcher.client_ready_use_case.execute = AsyncMock(return_value=mock_response)
        
        result = await dispatcher.dispatch(
            'client_ready',
            {'version': '1.0.0'},
            dispatch_context
        )
        
        assert result['event'] == 'client_ready_ack'
        assert result['data']['success'] is True
        assert result['data']['server_version'] == '1.0.0'
        assert 'game' in result['data']['features']
    
    # Room management event tests
    
    @pytest.mark.asyncio
    async def test_handle_create_room(self, dispatcher, dispatch_context):
        """Test create_room event handling"""
        # Mock room info
        room_info = RoomInfoDTO(
            room_id="ROOM123",
            room_code="ABC123",
            room_name="Test Room",
            host_id="player_123",
            players=[
                PlayerInfoDTO(
                    player_id="player_123",
                    player_name="Test Player",
                    is_bot=False,
                    is_host=True,
                    seat_position=0
                )
            ],
            max_players=4,
            game_in_progress=False
        )
        
        mock_response = CreateRoomResponse(
            success=True,
            room_info=room_info,
            join_code="ABC123"
        )
        dispatcher.create_room_use_case.execute = AsyncMock(return_value=mock_response)
        
        # Mock legacy visibility
        with patch('application.websocket.use_case_dispatcher.ensure_room_visible_to_legacy', new_callable=AsyncMock):
            result = await dispatcher.dispatch(
                'create_room',
                {
                    'player_name': 'Test Player',
                    'max_players': 4,
                    'win_condition_value': 50
                },
                dispatch_context
            )
        
        assert result['event'] == 'room_created'
        assert result['data']['room_id'] == 'ROOM123'
        assert result['data']['room_code'] == 'ABC123'
        assert result['data']['success'] is True
        assert len(result['data']['room_info']['players']) == 1
    
    @pytest.mark.asyncio
    async def test_handle_create_room_validation_error(self, dispatcher, dispatch_context):
        """Test create_room with missing player name"""
        result = await dispatcher.dispatch(
            'create_room',
            {},  # No player_name
            dispatch_context
        )
        
        assert result['event'] == 'error'
        assert result['data']['type'] == 'validation_error'
        assert 'Player name is required' in result['data']['message']
    
    @pytest.mark.asyncio
    async def test_handle_join_room(self, dispatcher, dispatch_context):
        """Test join_room event handling"""
        room_info = RoomInfoDTO(
            room_id="ROOM123",
            room_code="ABC123",
            room_name="Test Room",
            host_id="host_123",
            players=[
                PlayerInfoDTO(
                    player_id="host_123",
                    player_name="Host",
                    is_bot=False,
                    is_host=True,
                    seat_position=0
                ),
                PlayerInfoDTO(
                    player_id="player_456",
                    player_name="New Player",
                    is_bot=False,
                    is_host=False,
                    seat_position=1
                )
            ],
            max_players=4,
            game_in_progress=False
        )
        
        mock_response = JoinRoomResponse(
            success=True,
            room_info=room_info,
            player_id="player_456"
        )
        dispatcher.join_room_use_case.execute = AsyncMock(return_value=mock_response)
        
        result = await dispatcher.dispatch(
            'join_room',
            {
                'player_name': 'New Player',
                'room_id': 'ROOM123'
            },
            dispatch_context
        )
        
        assert result['event'] == 'room_joined'
        assert result['data']['success'] is True
        assert result['data']['room_id'] == 'ROOM123'
        assert len(result['data']['room_info']['players']) == 2
    
    @pytest.mark.asyncio
    async def test_handle_join_room_failure(self, dispatcher, dispatch_context):
        """Test join_room failure handling"""
        mock_response = JoinRoomResponse(
            success=False,
            error_message="Room is full"
        )
        dispatcher.join_room_use_case.execute = AsyncMock(return_value=mock_response)
        
        result = await dispatcher.dispatch(
            'join_room',
            {
                'player_name': 'New Player',
                'room_id': 'ROOM123'
            },
            dispatch_context
        )
        
        assert result['event'] == 'join_failed'
        assert result['data']['success'] is False
        assert result['data']['error'] == 'Room is full'
    
    # Lobby event tests
    
    @pytest.mark.asyncio
    async def test_handle_request_room_list(self, dispatcher, dispatch_context):
        """Test request_room_list event handling"""
        rooms = [
            RoomSummaryDTO(
                room_id="ROOM1",
                room_code="ABC1",
                room_name="Room 1",
                host_name="Host 1",
                player_count=2,
                max_players=4,
                game_in_progress=False,
                is_private=False
            ),
            RoomSummaryDTO(
                room_id="ROOM2",
                room_code="ABC2",
                room_name="Room 2",
                host_name="Host 2",
                player_count=3,
                max_players=4,
                game_in_progress=True,
                is_private=False
            )
        ]
        
        mock_response = GetRoomListResponse(
            rooms=rooms,
            total_count=2
        )
        dispatcher.get_room_list_use_case.execute = AsyncMock(return_value=mock_response)
        
        result = await dispatcher.dispatch(
            'request_room_list',
            {'include_in_progress': True},
            dispatch_context
        )
        
        assert result['event'] == 'room_list'
        assert len(result['data']['rooms']) == 2
        assert result['data']['total_count'] == 2
        assert result['data']['rooms'][0]['room_id'] == 'ROOM1'
        assert result['data']['rooms'][1]['game_in_progress'] is True
    
    @pytest.mark.asyncio
    async def test_handle_get_rooms_alias(self, dispatcher, dispatch_context):
        """Test get_rooms event (alias) calls request_room_list handler"""
        mock_response = GetRoomListResponse(rooms=[], total_count=0)
        dispatcher.get_room_list_use_case.execute = AsyncMock(return_value=mock_response)
        
        # Spy on the handler method
        original_handler = dispatcher._handle_request_room_list
        dispatcher._handle_request_room_list = AsyncMock(wraps=original_handler)
        
        await dispatcher.dispatch('get_rooms', {}, dispatch_context)
        
        dispatcher._handle_request_room_list.assert_called_once()
    
    # Game event tests
    
    @pytest.mark.asyncio
    async def test_handle_play_pieces_alias(self, dispatcher, dispatch_context):
        """Test play_pieces event (alias) calls play handler"""
        # Spy on the handler
        dispatcher._handle_play = AsyncMock(return_value={'event': 'play_made'})
        
        await dispatcher.dispatch(
            'play_pieces',
            {'pieces': [1, 2, 3]},
            dispatch_context
        )
        
        dispatcher._handle_play.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_redeal_decision(self, dispatcher, dispatch_context):
        """Test redeal_decision event routing"""
        # Test accept decision
        dispatcher._handle_accept_redeal = AsyncMock(return_value={'event': 'redeal_vote_cast'})
        
        await dispatcher.dispatch(
            'redeal_decision',
            {'decision': 'accept'},
            dispatch_context
        )
        
        dispatcher._handle_accept_redeal.assert_called_once()
        
        # Test decline decision
        dispatcher._handle_decline_redeal = AsyncMock(return_value={'event': 'redeal_vote_cast'})
        
        await dispatcher.dispatch(
            'redeal_decision',
            {'decision': 'decline'},
            dispatch_context
        )
        
        dispatcher._handle_decline_redeal.assert_called_once()
        
        # Test invalid decision
        result = await dispatcher.dispatch(
            'redeal_decision',
            {'decision': 'invalid'},
            dispatch_context
        )
        
        assert result['event'] == 'error'
        assert result['data']['type'] == 'validation_error'
    
    # Helper method tests
    
    def test_format_room_info(self, dispatcher):
        """Test room info formatting"""
        room_info = RoomInfoDTO(
            room_id="ROOM123",
            room_code="ABC123",
            room_name="Test Room",
            host_id="player_123",
            players=[
                PlayerInfoDTO(
                    player_id="player_123",
                    player_name="Test Player",
                    is_bot=False,
                    is_host=True,
                    seat_position=0
                )
            ],
            max_players=4,
            game_in_progress=False
        )
        
        formatted = dispatcher._format_room_info(room_info)
        
        assert formatted['room_id'] == 'ROOM123'
        assert formatted['players'][0]['name'] == 'Test Player'  # Frontend expects 'name'
        assert formatted['players'][0]['is_host'] is True
        assert 'status' in formatted  # Default status added
    
    @pytest.mark.asyncio
    async def test_ensure_legacy_visibility(self, dispatcher):
        """Test legacy visibility handling"""
        # Test successful sync
        with patch('application.websocket.use_case_dispatcher.ensure_room_visible_to_legacy', new_callable=AsyncMock) as mock_sync:
            await dispatcher._ensure_legacy_visibility("ROOM123")
            mock_sync.assert_called_once_with("ROOM123")
        
        # Test import error handling
        with patch('application.websocket.use_case_dispatcher.ensure_room_visible_to_legacy', side_effect=ImportError):
            # Should not raise, just log
            await dispatcher._ensure_legacy_visibility("ROOM123")
        
        # Test general error handling
        with patch('application.websocket.use_case_dispatcher.ensure_room_visible_to_legacy', new_callable=AsyncMock) as mock_sync:
            mock_sync.side_effect = Exception("Sync failed")
            # Should not raise, just log
            await dispatcher._ensure_legacy_visibility("ROOM123")