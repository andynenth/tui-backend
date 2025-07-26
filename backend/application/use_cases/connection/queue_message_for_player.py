"""
Queue message for player use case.

This use case handles queuing messages for disconnected players.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

from application.interfaces import UnitOfWork
from application.interfaces.services import EventPublisher, MetricsCollector
from application.dto.connection import QueueMessageRequest, QueueMessageResponse
from application.exceptions import ApplicationException


@dataclass
class QueueMessageForPlayerRequest(QueueMessageRequest):
    """Alias for backward compatibility."""
    pass


@dataclass 
class QueueMessageForPlayerResponse(QueueMessageResponse):
    """Alias for backward compatibility."""
    pass


class QueueMessageForPlayerUseCase:
    """
    Queue a message for a disconnected player.
    
    This use case:
    1. Checks if player has a message queue
    2. Adds the message to the queue
    3. Handles queue overflow
    """
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        event_publisher: EventPublisher,
        metrics: Optional[MetricsCollector] = None
    ):
        self._uow = unit_of_work
        self._event_publisher = event_publisher
        self._metrics = metrics
    
    async def execute(self, request: QueueMessageForPlayerRequest) -> QueueMessageForPlayerResponse:
        """Execute the use case."""
        try:
            async with self._uow:
                # Get or create the queue
                queue = await self._uow.message_queues.get_queue(
                    request.room_id,
                    request.player_name
                )
                
                if not queue:
                    # Player doesn't have a queue (not disconnected)
                    return QueueMessageForPlayerResponse(
                        success=True,
                        queued=False,
                        queue_size=0
                    )
                
                # Add the message
                initial_size = queue.size()
                queue.add_message(
                    request.event_type,
                    request.event_data,
                    request.is_critical
                )
                
                # Check if overflow occurred
                message_dropped = queue.size() == initial_size and initial_size >= queue.max_size
                
                # Save the queue
                await self._uow.message_queues.save_queue(queue)
                await self._uow.commit()
                
                # Record metrics
                if self._metrics:
                    self._metrics.increment(
                        "message_queue.message_added",
                        tags={
                            "event_type": request.event_type,
                            "is_critical": str(request.is_critical).lower()
                        }
                    )
                    
                    if message_dropped:
                        self._metrics.increment("message_queue.overflow")
                    
                    self._metrics.gauge(
                        f"message_queue.size.{request.room_id}.{request.player_name}",
                        queue.size()
                    )
                
                return QueueMessageForPlayerResponse(
                    success=True,
                    queued=True,
                    queue_size=queue.size(),
                    message_dropped=message_dropped
                )
                
        except Exception as e:
            if self._metrics:
                self._metrics.increment("message_queue.error")
            
            raise ApplicationException(
                f"Failed to queue message: {str(e)}",
                code="QUEUE_MESSAGE_FAILED"
            )