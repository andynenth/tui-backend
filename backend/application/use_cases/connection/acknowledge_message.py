"""
Use case for acknowledging messages.

Clients acknowledge receipt of important messages to ensure reliable
delivery. This use case tracks acknowledgments and handles retries.
"""

from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta

from application.base import UseCase
from application.dto.connection import AcknowledgeMessageRequest, AcknowledgeMessageResponse
from application.interfaces import MetricsCollector
from application.exceptions import ValidationException

logger = logging.getLogger(__name__)


class AcknowledgeMessageUseCase(UseCase[AcknowledgeMessageRequest, AcknowledgeMessageResponse]):
    """
    Handles message acknowledgments from clients.
    
    This use case:
    1. Records that a message was acknowledged
    2. Tracks failed acknowledgments for retry
    3. Provides metrics on message delivery
    """
    
    # In-memory tracking of acknowledgments (would be Redis in production)
    _acknowledgments: Dict[str, Dict[str, Any]] = {}
    _retry_queue: Dict[str, Dict[str, Any]] = {}
    
    def __init__(
        self,
        metrics: Optional[MetricsCollector] = None,
        max_retries: int = 3,
        retry_delay_seconds: int = 5
    ):
        """
        Initialize the use case.
        
        Args:
            metrics: Optional metrics collector
            max_retries: Maximum retry attempts
            retry_delay_seconds: Delay between retries
        """
        self._metrics = metrics
        self._max_retries = max_retries
        self._retry_delay = timedelta(seconds=retry_delay_seconds)
    
    async def execute(self, request: AcknowledgeMessageRequest) -> AcknowledgeMessageResponse:
        """
        Acknowledge a message.
        
        Args:
            request: The acknowledgment request
            
        Returns:
            Response indicating acknowledgment status
            
        Raises:
            ValidationException: If request is invalid
        """
        # Validate request
        if not request.message_id:
            raise ValidationException({"message_id": "Message ID is required"})
        
        # Record acknowledgment
        ack_key = f"{request.player_id}:{request.message_id}"
        
        if request.success:
            # Successful acknowledgment
            self._acknowledgments[ack_key] = {
                "player_id": request.player_id,
                "message_id": request.message_id,
                "message_type": request.message_type,
                "acknowledged_at": datetime.utcnow(),
                "room_id": request.room_id
            }
            
            # Remove from retry queue if present
            self._retry_queue.pop(ack_key, None)
            
            # Record metrics
            if self._metrics:
                self._metrics.increment(
                    "message.acknowledged",
                    tags={
                        "message_type": request.message_type,
                        "room_id": request.room_id or "lobby"
                    }
                )
            
            retry_required = False
            
        else:
            # Failed acknowledgment - add to retry queue
            retry_info = self._retry_queue.get(ack_key, {
                "attempts": 0,
                "first_failure": datetime.utcnow()
            })
            
            retry_info["attempts"] += 1
            retry_info["last_failure"] = datetime.utcnow()
            retry_info["error_code"] = request.error_code
            retry_info["next_retry"] = datetime.utcnow() + self._retry_delay
            
            retry_required = retry_info["attempts"] < self._max_retries
            
            if retry_required:
                self._retry_queue[ack_key] = retry_info
            else:
                # Max retries exceeded
                logger.warning(
                    f"Max retries exceeded for message {request.message_id}",
                    extra={
                        "player_id": request.player_id,
                        "message_id": request.message_id,
                        "attempts": retry_info["attempts"]
                    }
                )
            
            # Record failure metrics
            if self._metrics:
                self._metrics.increment(
                    "message.acknowledgment_failed",
                    tags={
                        "message_type": request.message_type,
                        "error_code": request.error_code or "unknown",
                        "retry_required": str(retry_required).lower()
                    }
                )
        
        # Create response
        response = AcknowledgeMessageResponse(
            success=True,
            request_id=request.request_id,
            message_id=request.message_id,
            acknowledged=request.success,
            retry_required=retry_required
        )
        
        logger.debug(
            f"Message {request.message_id} acknowledgment processed",
            extra={
                "player_id": request.player_id,
                "message_id": request.message_id,
                "acknowledged": request.success,
                "retry_required": retry_required
            }
        )
        
        self._log_execution(request, response)
        return response
    
    @classmethod
    def get_pending_retries(cls, player_id: str) -> List[Dict[str, Any]]:
        """
        Get pending retries for a player.
        
        Args:
            player_id: The player's ID
            
        Returns:
            List of messages pending retry
        """
        now = datetime.utcnow()
        pending = []
        
        for ack_key, retry_info in cls._retry_queue.items():
            if ack_key.startswith(f"{player_id}:") and retry_info["next_retry"] <= now:
                pending.append({
                    "message_id": ack_key.split(":", 1)[1],
                    "attempts": retry_info["attempts"],
                    "error_code": retry_info.get("error_code")
                })
        
        return pending