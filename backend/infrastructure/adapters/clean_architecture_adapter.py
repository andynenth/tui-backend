"""
Clean architecture adapter for WebSocket handlers.

This module provides the bridge between WebSocket events and the
clean architecture use cases, with feature flag support for gradual rollout.
"""

import logging
from typing import Dict, Any, Optional, Callable
import time

from infrastructure.feature_flags import get_feature_flags
from infrastructure.dependencies import (
    get_unit_of_work,
    get_event_publisher,
    get_metrics_collector
)
from application.dto.connection import (
    HandlePingRequest,
    MarkClientReadyRequest,
    SyncClientStateRequest
)
from application.dto.room_management import (
    CreateRoomRequest,
    JoinRoomRequest,
    LeaveRoomRequest,
    AddBotRequest
)
from application.dto.game import (
    StartGameRequest,
    DeclareRequest,
    PlayRequest,
    RequestRedealRequest,
    AcceptRedealRequest,
    DeclineRedealRequest
)
from application.use_cases.connection import (
    HandlePingUseCase,
    MarkClientReadyUseCase,
    SyncClientStateUseCase
)
from application.use_cases.room_management import (
    CreateRoomUseCase,
    JoinRoomUseCase,
    LeaveRoomUseCase,
    AddBotUseCase
)
from application.use_cases.game import (
    StartGameUseCase,
    DeclareUseCase,
    PlayUseCase,
    RequestRedealUseCase,
    AcceptRedealUseCase,
    DeclineRedealUseCase
)

logger = logging.getLogger(__name__)


class CleanArchitectureAdapter:
    """
    Adapter that routes WebSocket events to clean architecture use cases.
    
    This adapter checks feature flags to determine whether to use the
    new clean architecture or fall back to legacy handlers.
    """
    
    def __init__(self, legacy_handlers: Dict[str, Callable]):
        """
        Initialize the adapter.
        
        Args:
            legacy_handlers: Dictionary of legacy handler functions
        """
        self._legacy_handlers = legacy_handlers
        self._feature_flags = get_feature_flags()
        self._metrics = get_metrics_collector()
        
        # Map event types to use cases
        self._use_case_map = {
            'ping': self._handle_ping,
            'client_ready': self._handle_client_ready,
            'sync_state': self._handle_sync_state,
            'create_room': self._handle_create_room,
            'join_room': self._handle_join_room,
            'leave_room': self._handle_leave_room,
            'add_bot': self._handle_add_bot,
            'start_game': self._handle_start_game,
            'declare': self._handle_declare,
            'play': self._handle_play,
            'request_redeal': self._handle_request_redeal,
            'accept_redeal': self._handle_accept_redeal,
            'decline_redeal': self._handle_decline_redeal
        }
    
    async def handle_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Handle a WebSocket event.
        
        Args:
            event_type: Type of event
            data: Event data
            context: Request context (player_id, room_id, etc.)
            
        Returns:
            Response data if any
        """
        start_time = time.time()
        
        try:
            # Check if clean architecture is enabled for this event
            if self._should_use_clean_architecture(event_type, context):
                # Route to use case
                if event_type in self._use_case_map:
                    response = await self._use_case_map[event_type](data, context)
                    
                    # Record metrics
                    duration_ms = (time.time() - start_time) * 1000
                    self._metrics.timing(
                        f"clean_architecture.{event_type}",
                        duration_ms,
                        tags={'status': 'success'}
                    )
                    
                    return response
                else:
                    logger.warning(f"No use case mapped for event: {event_type}")
            
            # Fall back to legacy handler
            return await self._call_legacy_handler(event_type, data, context)
            
        except Exception as e:
            # Record error metrics
            self._metrics.increment(
                f"clean_architecture.{event_type}.error",
                tags={'error_type': type(e).__name__}
            )
            
            logger.error(f"Error handling {event_type}: {e}")
            
            # Re-raise to maintain existing error handling
            raise
    
    def _should_use_clean_architecture(
        self,
        event_type: str,
        context: Dict[str, Any]
    ) -> bool:
        """Check if clean architecture should be used for this request."""
        # Check global flag
        if not self._feature_flags.is_enabled(
            self._feature_flags.USE_CLEAN_ARCHITECTURE,
            context
        ):
            return False
        
        # Check specific adapter flags
        if event_type in ['ping', 'client_ready', 'sync_state']:
            return self._feature_flags.is_enabled(
                self._feature_flags.USE_CONNECTION_ADAPTERS,
                context
            )
        elif event_type in ['create_room', 'join_room', 'leave_room', 'add_bot']:
            return self._feature_flags.is_enabled(
                self._feature_flags.USE_ROOM_ADAPTERS,
                context
            )
        elif event_type in ['start_game', 'declare', 'play', 'request_redeal',
                           'accept_redeal', 'decline_redeal']:
            return self._feature_flags.is_enabled(
                self._feature_flags.USE_GAME_ADAPTERS,
                context
            )
        
        return False
    
    async def _call_legacy_handler(
        self,
        event_type: str,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Call the legacy handler for an event."""
        if event_type in self._legacy_handlers:
            handler = self._legacy_handlers[event_type]
            return await handler(data, context)
        else:
            logger.warning(f"No legacy handler for event: {event_type}")
            return None
    
    # Use case handler methods
    
    async def _handle_ping(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle ping using clean architecture."""
        request = HandlePingRequest(
            player_id=context['player_id'],
            room_id=context.get('room_id'),
            sequence_number=data.get('sequence')
        )
        
        uow = get_unit_of_work()
        metrics = get_metrics_collector()
        use_case = HandlePingUseCase(uow, metrics)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_client_ready(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle client ready using clean architecture."""
        request = MarkClientReadyRequest(
            player_id=context['player_id'],
            room_id=context['room_id'],
            client_version=data.get('version'),
            client_capabilities=data.get('capabilities')
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        metrics = get_metrics_collector()
        use_case = MarkClientReadyUseCase(uow, publisher, metrics)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_create_room(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle room creation using clean architecture."""
        request = CreateRoomRequest(
            host_player_id=context['player_id'],
            host_player_name=data['player_name'],
            room_name=data.get('room_name'),
            max_players=data.get('max_players', 4)
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        use_case = CreateRoomUseCase(uow, publisher)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_join_room(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle room joining using clean architecture."""
        request = JoinRoomRequest(
            player_id=context['player_id'],
            player_name=data['player_name'],
            room_code=data.get('room_code'),
            room_id=data.get('room_id'),
            seat_preference=data.get('seat_preference')
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        metrics = get_metrics_collector()
        use_case = JoinRoomUseCase(uow, publisher, metrics)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_start_game(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle game start using clean architecture."""
        request = StartGameRequest(
            room_id=context['room_id'],
            requesting_player_id=context['player_id']
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        use_case = StartGameUseCase(uow, publisher)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_declare(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle declaration using clean architecture."""
        request = DeclareRequest(
            game_id=context['game_id'],
            player_id=context['player_id'],
            room_id=context['room_id'],
            declared_count=data['value']
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        use_case = DeclareUseCase(uow, publisher)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_play(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle play using clean architecture."""
        request = PlayRequest(
            game_id=context['game_id'],
            player_id=context['player_id'],
            room_id=context['room_id'],
            piece_indices=data['pieces']
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        use_case = PlayUseCase(uow, publisher)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    # Add other handler methods as needed...
    
    async def _handle_sync_state(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle state sync using clean architecture."""
        request = SyncClientStateRequest(
            player_id=context['player_id'],
            room_id=context.get('room_id'),
            last_known_sequence=data.get('last_sequence'),
            include_game_state=data.get('include_game', True),
            include_player_hands=data.get('include_hands', True)
        )
        
        uow = get_unit_of_work()
        use_case = SyncClientStateUseCase(uow)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_leave_room(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle leaving room using clean architecture."""
        request = LeaveRoomRequest(
            player_id=context['player_id'],
            room_id=context['room_id'],
            reason=data.get('reason', 'Player left')
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        use_case = LeaveRoomUseCase(uow, publisher)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_add_bot(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle adding bot using clean architecture."""
        request = AddBotRequest(
            room_id=context['room_id'],
            requesting_player_id=context['player_id'],
            bot_difficulty=data.get('difficulty', 'medium')
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        use_case = AddBotUseCase(uow, publisher)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_request_redeal(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle redeal request using clean architecture."""
        request = RequestRedealRequest(
            game_id=context['game_id'],
            player_id=context['player_id'],
            room_id=context['room_id']
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        use_case = RequestRedealUseCase(uow, publisher)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_accept_redeal(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle redeal acceptance using clean architecture."""
        request = AcceptRedealRequest(
            game_id=context['game_id'],
            player_id=context['player_id'],
            room_id=context['room_id']
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        use_case = AcceptRedealUseCase(uow, publisher)
        
        response = await use_case.execute(request)
        return response.to_dict()
    
    async def _handle_decline_redeal(
        self,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle redeal decline using clean architecture."""
        request = DeclineRedealRequest(
            game_id=context['game_id'],
            player_id=context['player_id'],
            room_id=context['room_id']
        )
        
        uow = get_unit_of_work()
        publisher = get_event_publisher()
        use_case = DeclineRedealUseCase(uow, publisher)
        
        response = await use_case.execute(request)
        return response.to_dict()