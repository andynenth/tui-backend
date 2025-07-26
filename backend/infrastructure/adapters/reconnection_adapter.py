"""
Adapter for integrating the reconnection system with existing WebSocket handlers.

This adapter bridges the clean architecture reconnection system with the
legacy WebSocket infrastructure, enabling gradual migration.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from application.services import ReconnectionService, MessageQueueService
from application.use_cases.connection import (
    HandlePlayerDisconnectUseCase,
    HandlePlayerReconnectUseCase,
    QueueMessageForPlayerUseCase
)
from application.dto.connection import (
    HandlePlayerDisconnectRequest,
    HandlePlayerReconnectRequest,
    QueueMessageRequest
)
from infrastructure.unit_of_work import InMemoryUnitOfWork
from infrastructure.services import WebSocketNotificationService
from infrastructure.feature_flags import FeatureFlagService


logger = logging.getLogger(__name__)


class ReconnectionAdapter:
    """
    Adapter for reconnection functionality.
    
    This adapter provides a bridge between the existing WebSocket
    handlers and the clean architecture reconnection system.
    """
    
    def __init__(self, feature_flags: Optional[FeatureFlagService] = None):
        """
        Initialize the adapter.
        
        Args:
            feature_flags: Feature flag service for gradual rollout
        """
        self._feature_flags = feature_flags or FeatureFlagService()
        self._uow = InMemoryUnitOfWork()
        
        # Initialize services
        from infrastructure.services import (
            InMemoryEventPublisher,
            SimpleBotService,
            ConsoleMetricsCollector
        )
        
        event_publisher = InMemoryEventPublisher()
        notification_service = WebSocketNotificationService()
        bot_service = SimpleBotService()
        metrics = ConsoleMetricsCollector()
        
        # Create application services
        self._reconnection_service = ReconnectionService(
            uow=self._uow,
            event_publisher=event_publisher,
            notification_service=notification_service,
            bot_service=bot_service
        )
        
        self._message_queue_service = MessageQueueService(
            uow=self._uow,
            event_publisher=event_publisher
        )
        
        # Create use cases
        self._disconnect_use_case = HandlePlayerDisconnectUseCase(
            uow=self._uow,
            event_publisher=event_publisher,
            metrics=metrics
        )
        
        self._reconnect_use_case = HandlePlayerReconnectUseCase(
            uow=self._uow,
            event_publisher=event_publisher,
            metrics=metrics
        )
        
        self._queue_message_use_case = QueueMessageForPlayerUseCase(
            uow=self._uow,
            event_publisher=event_publisher
        )
    
    async def handle_disconnect(
        self,
        room_id: str,
        player_name: str,
        activate_bot: bool = True
    ) -> Dict[str, Any]:
        """
        Handle player disconnection.
        
        Args:
            room_id: The room ID
            player_name: The player name
            activate_bot: Whether to activate bot replacement
            
        Returns:
            Response data
        """
        if not self._feature_flags.is_enabled("use_clean_reconnection", room_id):
            return {"status": "skipped", "reason": "feature_disabled"}
        
        try:
            request = HandlePlayerDisconnectRequest(
                room_id=room_id,
                player_name=player_name,
                activate_bot=activate_bot
            )
            
            response = await self._disconnect_use_case.execute(request)
            
            return {
                "status": "success",
                "bot_activated": response.bot_activated,
                "queue_created": response.queue_created
            }
            
        except Exception as e:
            logger.error(f"Disconnect handling failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def handle_reconnect(
        self,
        room_id: str,
        player_name: str,
        websocket_id: str
    ) -> Dict[str, Any]:
        """
        Handle player reconnection.
        
        Args:
            room_id: The room ID
            player_name: The player name
            websocket_id: New websocket connection ID
            
        Returns:
            Response data with queued messages
        """
        if not self._feature_flags.is_enabled("use_clean_reconnection", room_id):
            return {"status": "skipped", "reason": "feature_disabled"}
        
        try:
            request = HandlePlayerReconnectRequest(
                room_id=room_id,
                player_name=player_name,
                websocket_id=websocket_id
            )
            
            response = await self._reconnect_use_case.execute(request)
            
            return {
                "status": "success",
                "bot_deactivated": response.bot_deactivated,
                "messages_restored": response.messages_restored,
                "queued_messages": response.queued_messages,
                "current_state": response.current_state
            }
            
        except Exception as e:
            logger.error(f"Reconnect handling failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def queue_message(
        self,
        room_id: str,
        player_name: str,
        event_type: str,
        event_data: Dict[str, Any],
        is_critical: bool = False
    ) -> bool:
        """
        Queue a message for a disconnected player.
        
        Args:
            room_id: The room ID
            player_name: The player name
            event_type: Type of event to queue
            event_data: Event data
            is_critical: Whether this is a critical message
            
        Returns:
            True if message was queued
        """
        if not self._feature_flags.is_enabled("use_clean_reconnection", room_id):
            return False
        
        try:
            request = QueueMessageRequest(
                room_id=room_id,
                player_name=player_name,
                event_type=event_type,
                event_data=event_data,
                is_critical=is_critical
            )
            
            response = await self._queue_message_use_case.execute(request)
            return response.queued
            
        except Exception as e:
            logger.error(f"Message queueing failed: {e}")
            return False
    
    async def get_connection_status(self, room_id: str) -> List[Dict[str, Any]]:
        """
        Get connection status for all players in a room.
        
        Args:
            room_id: The room ID
            
        Returns:
            List of connection statuses
        """
        if not self._feature_flags.is_enabled("use_clean_reconnection", room_id):
            return []
        
        try:
            return await self._reconnection_service.check_connection_health(room_id)
        except Exception as e:
            logger.error(f"Failed to get connection status: {e}")
            return []
    
    async def cleanup_disconnected_players(
        self,
        room_id: str,
        timeout_minutes: int = 10
    ) -> int:
        """
        Clean up players who have been disconnected too long.
        
        Args:
            room_id: The room ID
            timeout_minutes: Minutes before considering player gone
            
        Returns:
            Number of players cleaned up
        """
        if not self._feature_flags.is_enabled("use_clean_reconnection", room_id):
            return 0
        
        try:
            return await self._reconnection_service.cleanup_disconnected_players(
                room_id, timeout_minutes
            )
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0
    
    async def get_queue_stats(self, room_id: str) -> Dict[str, Any]:
        """
        Get message queue statistics for a room.
        
        Args:
            room_id: The room ID
            
        Returns:
            Queue statistics
        """
        if not self._feature_flags.is_enabled("use_clean_reconnection", room_id):
            return {}
        
        try:
            return await self._message_queue_service.get_queue_stats(room_id)
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
    
    def is_enabled(self, room_id: str) -> bool:
        """
        Check if reconnection system is enabled for a room.
        
        Args:
            room_id: The room ID
            
        Returns:
            True if enabled
        """
        return self._feature_flags.is_enabled("use_clean_reconnection", room_id)