# backend/engine/events/event_middleware.py

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

from .event_types import GameEvent, EventType, EventPriority
from .event_handlers import IEventHandler

logger = logging.getLogger(__name__)


class IEventMiddleware(ABC):
    """
    🎯 **Event Middleware Interface** - Abstract base for event middleware
    
    Defines the contract for event processing middleware that can intercept
    and modify events at various stages of the processing pipeline.
    """
    
    @abstractmethod
    async def pre_process(self, event: GameEvent) -> GameEvent:
        """
        Process event before it enters the handler pipeline.
        
        Args:
            event: The event to process
            
        Returns:
            Modified event (or the same event)
        """
        pass
    
    @abstractmethod
    async def pre_handle(self, event: GameEvent, handler: IEventHandler) -> GameEvent:
        """
        Process event before it's handled by a specific handler.
        
        Args:
            event: The event to process
            handler: The handler that will process the event
            
        Returns:
            Modified event (or the same event)
        """
        pass
    
    @abstractmethod
    async def post_handle(self, event: GameEvent, handler: IEventHandler):
        """
        Process event after it's handled by a specific handler.
        
        Args:
            event: The processed event
            handler: The handler that processed the event
        """
        pass
    
    @abstractmethod
    async def post_process(self, event: GameEvent):
        """
        Process event after all handlers have processed it.
        
        Args:
            event: The fully processed event
        """
        pass
    
    def get_middleware_name(self) -> str:
        """Get human-readable middleware name."""
        return self.__class__.__name__


class LoggingMiddleware(IEventMiddleware):
    """
    🎯 **Logging Middleware** - Comprehensive event logging
    
    Logs all event processing stages with configurable detail levels
    and performance metrics.
    """
    
    def __init__(self, log_level: int = logging.DEBUG, include_performance: bool = True):
        self.log_level = log_level
        self.include_performance = include_performance
        self.event_timings: Dict[str, float] = {}
        
    async def pre_process(self, event: GameEvent) -> GameEvent:
        """Log event before processing."""
        if self.include_performance:
            self.event_timings[event.event_id] = time.time()
        
        logger.log(
            self.log_level,
            f"📥 EVENT_RECEIVED: {event.event_type.value} "
            f"(ID: {event.event_id[:8]}, Priority: {event.priority.name})"
        )
        
        if event.room_id:
            logger.log(self.log_level, f"🏠 ROOM: {event.room_id}")
        
        if event.player_id:
            logger.log(self.log_level, f"👤 PLAYER: {event.player_id}")
        
        return event
    
    async def pre_handle(self, event: GameEvent, handler: IEventHandler) -> GameEvent:
        """Log before handler processing."""
        logger.log(
            self.log_level,
            f"⚡ HANDLER_START: {handler.get_handler_name()} processing {event.event_type.value}"
        )
        
        if self.include_performance:
            handler_key = f"{event.event_id}:{handler.get_handler_name()}"
            self.event_timings[handler_key] = time.time()
        
        return event
    
    async def post_handle(self, event: GameEvent, handler: IEventHandler):
        """Log after handler processing."""
        handler_name = handler.get_handler_name()
        
        if self.include_performance:
            handler_key = f"{event.event_id}:{handler_name}"
            if handler_key in self.event_timings:
                duration = time.time() - self.event_timings[handler_key]
                logger.log(
                    self.log_level,
                    f"✅ HANDLER_COMPLETE: {handler_name} processed {event.event_type.value} "
                    f"in {duration:.3f}s"
                )
                del self.event_timings[handler_key]
        else:
            logger.log(
                self.log_level,
                f"✅ HANDLER_COMPLETE: {handler_name} processed {event.event_type.value}"
            )
    
    async def post_process(self, event: GameEvent):
        """Log after all processing is complete."""
        if self.include_performance and event.event_id in self.event_timings:
            total_duration = time.time() - self.event_timings[event.event_id]
            logger.log(
                self.log_level,
                f"🎉 EVENT_COMPLETE: {event.event_type.value} processed in {total_duration:.3f}s"
            )
            del self.event_timings[event.event_id]
        else:
            logger.log(
                self.log_level,
                f"🎉 EVENT_COMPLETE: {event.event_type.value} processed"
            )
        
        if event.processing_errors:
            logger.log(
                logging.WARNING,
                f"⚠️ EVENT_ERRORS: {event.event_type.value} had {len(event.processing_errors)} errors"
            )


@dataclass
class EventMetrics:
    """Metrics collected by MetricsMiddleware."""
    total_events: int = 0
    events_by_type: Dict[str, int] = None
    events_by_priority: Dict[str, int] = None
    average_processing_time: float = 0.0
    total_processing_time: float = 0.0
    error_count: int = 0
    handler_metrics: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.events_by_type is None:
            self.events_by_type = {}
        if self.events_by_priority is None:
            self.events_by_priority = {}
        if self.handler_metrics is None:
            self.handler_metrics = {}


class MetricsMiddleware(IEventMiddleware):
    """
    🎯 **Metrics Middleware** - Performance and usage metrics collection
    
    Collects detailed metrics about event processing performance,
    handler usage, and system health.
    """
    
    def __init__(self, metrics_interval: float = 60.0):
        self.metrics = EventMetrics()
        self.metrics_interval = metrics_interval
        self.event_timings: Dict[str, float] = {}
        self.handler_timings: Dict[str, List[float]] = {}
        self.last_metrics_log = time.time()
        
    async def pre_process(self, event: GameEvent) -> GameEvent:
        """Start timing and update counters."""
        self.event_timings[event.event_id] = time.time()
        
        # Update metrics
        self.metrics.total_events += 1
        
        event_type_str = event.event_type.value
        self.metrics.events_by_type[event_type_str] = (
            self.metrics.events_by_type.get(event_type_str, 0) + 1
        )
        
        priority_str = event.priority.name
        self.metrics.events_by_priority[priority_str] = (
            self.metrics.events_by_priority.get(priority_str, 0) + 1
        )
        
        return event
    
    async def pre_handle(self, event: GameEvent, handler: IEventHandler) -> GameEvent:
        """Start handler timing."""
        handler_name = handler.get_handler_name()
        handler_key = f"{event.event_id}:{handler_name}"
        self.event_timings[handler_key] = time.time()
        
        return event
    
    async def post_handle(self, event: GameEvent, handler: IEventHandler):
        """Record handler performance."""
        handler_name = handler.get_handler_name()
        handler_key = f"{event.event_id}:{handler_name}"
        
        if handler_key in self.event_timings:
            duration = time.time() - self.event_timings[handler_key]
            
            # Track handler performance
            if handler_name not in self.handler_timings:
                self.handler_timings[handler_name] = []
            self.handler_timings[handler_name].append(duration)
            
            # Update handler metrics
            if handler_name not in self.metrics.handler_metrics:
                self.metrics.handler_metrics[handler_name] = {
                    "total_calls": 0,
                    "total_time": 0.0,
                    "average_time": 0.0,
                    "min_time": float('inf'),
                    "max_time": 0.0
                }
            
            handler_metrics = self.metrics.handler_metrics[handler_name]
            handler_metrics["total_calls"] += 1
            handler_metrics["total_time"] += duration
            handler_metrics["average_time"] = (
                handler_metrics["total_time"] / handler_metrics["total_calls"]
            )
            handler_metrics["min_time"] = min(handler_metrics["min_time"], duration)
            handler_metrics["max_time"] = max(handler_metrics["max_time"], duration)
            
            del self.event_timings[handler_key]
    
    async def post_process(self, event: GameEvent):
        """Record total processing time and log metrics."""
        if event.event_id in self.event_timings:
            total_duration = time.time() - self.event_timings[event.event_id]
            
            # Update overall metrics
            self.metrics.total_processing_time += total_duration
            self.metrics.average_processing_time = (
                self.metrics.total_processing_time / self.metrics.total_events
            )
            
            del self.event_timings[event.event_id]
        
        # Count errors
        if event.processing_errors:
            self.metrics.error_count += len(event.processing_errors)
        
        # Log metrics periodically
        current_time = time.time()
        if current_time - self.last_metrics_log > self.metrics_interval:
            self._log_metrics()
            self.last_metrics_log = current_time
    
    def _log_metrics(self):
        """Log current metrics summary."""
        logger.info(f"📊 METRICS_SUMMARY: "
                   f"Events: {self.metrics.total_events}, "
                   f"Avg Time: {self.metrics.average_processing_time:.3f}s, "
                   f"Errors: {self.metrics.error_count}")
        
        # Log top event types
        if self.metrics.events_by_type:
            top_events = sorted(
                self.metrics.events_by_type.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            logger.info(f"📈 TOP_EVENTS: {dict(top_events)}")
        
        # Log slowest handlers
        if self.metrics.handler_metrics:
            slowest_handlers = sorted(
                self.metrics.handler_metrics.items(),
                key=lambda x: x[1]["average_time"],
                reverse=True
            )[:3]
            slowest_handler_strings = [f'{h[0]}:{h[1]["average_time"]:.3f}s' for h in slowest_handlers]
            logger.info(f"🐌 SLOWEST_HANDLERS: {slowest_handler_strings}")
    
    def get_metrics(self) -> EventMetrics:
        """Get current metrics."""
        return self.metrics
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = EventMetrics()
        self.event_timings.clear()
        self.handler_timings.clear()


class ErrorHandlingMiddleware(IEventMiddleware):
    """
    🎯 **Error Handling Middleware** - Comprehensive error handling and recovery
    
    Provides error handling, recovery strategies, and dead letter queue
    for failed events.
    """
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.dead_letter_queue: List[GameEvent] = []
        self.error_counts: Dict[str, int] = {}
        
    async def pre_process(self, event: GameEvent) -> GameEvent:
        """Initialize error handling for event."""
        if not hasattr(event, '_error_handling_initialized'):
            event.metadata['retry_count'] = 0
            event.metadata['error_handling_initialized'] = True
        
        return event
    
    async def pre_handle(self, event: GameEvent, handler: IEventHandler) -> GameEvent:
        """Pre-handler error checking."""
        handler_name = handler.get_handler_name()
        
        # Check if handler has too many recent errors
        if self._should_skip_handler(handler_name):
            logger.warning(f"⚠️ HANDLER_SKIP: Skipping {handler_name} due to high error rate")
            event.cancel(f"Handler {handler_name} has high error rate")
        
        return event
    
    async def post_handle(self, event: GameEvent, handler: IEventHandler):
        """Post-handler error processing."""
        handler_name = handler.get_handler_name()
        
        # Check if handler added errors
        if event.processing_errors:
            recent_errors = [
                error for error in event.processing_errors
                if handler_name in error
            ]
            
            if recent_errors:
                self._record_handler_error(handler_name)
                logger.error(f"❌ HANDLER_ERROR: {handler_name} had {len(recent_errors)} errors")
    
    async def post_process(self, event: GameEvent):
        """Final error processing and retry logic."""
        if event.processing_errors:
            retry_count = event.metadata.get('retry_count', 0)
            
            if retry_count < self.max_retries:
                # Retry the event
                logger.warning(f"🔄 RETRY: Retrying {event.event_type.value} "
                              f"(attempt {retry_count + 1}/{self.max_retries})")
                
                event.metadata['retry_count'] = retry_count + 1
                event.processing_errors.clear()
                event.is_processed = False
                
                # Add delay before retry
                await asyncio.sleep(self.retry_delay * (retry_count + 1))
                
                # Re-publish event for retry
                # Note: This would need access to the event bus
                # In practice, this would be handled by the event bus itself
                
            else:
                # Move to dead letter queue
                logger.error(f"💀 DEAD_LETTER: {event.event_type.value} "
                            f"failed after {self.max_retries} retries")
                
                self._add_to_dead_letter_queue(event)
    
    def _should_skip_handler(self, handler_name: str) -> bool:
        """Check if handler should be skipped due to high error rate."""
        error_count = self.error_counts.get(handler_name, 0)
        return error_count > 10  # Skip if more than 10 recent errors
    
    def _record_handler_error(self, handler_name: str):
        """Record an error for a handler."""
        self.error_counts[handler_name] = self.error_counts.get(handler_name, 0) + 1
    
    def _add_to_dead_letter_queue(self, event: GameEvent):
        """Add event to dead letter queue."""
        self.dead_letter_queue.append(event)
        
        # Limit dead letter queue size
        if len(self.dead_letter_queue) > 1000:
            self.dead_letter_queue = self.dead_letter_queue[-1000:]
    
    def get_dead_letter_queue(self) -> List[GameEvent]:
        """Get events in dead letter queue."""
        return self.dead_letter_queue.copy()
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics by handler."""
        return self.error_counts.copy()
    
    def reset_error_stats(self):
        """Reset error statistics."""
        self.error_counts.clear()


class ValidationMiddleware(IEventMiddleware):
    """
    🎯 **Validation Middleware** - Event validation and sanitization
    
    Validates event data, sanitizes inputs, and ensures event consistency
    before processing.
    """
    
    def __init__(self, strict_validation: bool = True):
        self.strict_validation = strict_validation
        self.validation_errors: List[str] = []
        
    async def pre_process(self, event: GameEvent) -> GameEvent:
        """Validate event before processing."""
        validation_errors = []
        
        # Basic event validation
        if not event.event_id:
            validation_errors.append("Event ID is required")
        
        if not event.event_type:
            validation_errors.append("Event type is required")
        
        if not event.timestamp:
            validation_errors.append("Event timestamp is required")
        
        # Event type specific validation
        validation_errors.extend(self._validate_event_type_specific(event))
        
        # Room/player validation
        validation_errors.extend(self._validate_room_player_context(event))
        
        if validation_errors:
            self.validation_errors.extend(validation_errors)
            
            if self.strict_validation:
                error_msg = f"Event validation failed: {', '.join(validation_errors)}"
                logger.error(f"❌ VALIDATION_ERROR: {error_msg}")
                event.cancel(error_msg)
            else:
                logger.warning(f"⚠️ VALIDATION_WARNING: {', '.join(validation_errors)}")
        
        return event
    
    async def pre_handle(self, event: GameEvent, handler: IEventHandler) -> GameEvent:
        """Validate event for specific handler."""
        # Check if handler can handle this event type
        if not handler.can_handle(event.event_type):
            logger.warning(f"⚠️ HANDLER_MISMATCH: {handler.get_handler_name()} "
                          f"cannot handle {event.event_type.value}")
            event.cancel(f"Handler {handler.get_handler_name()} cannot handle event type")
        
        return event
    
    async def post_handle(self, event: GameEvent, handler: IEventHandler):
        """Validate event after handler processing."""
        # Check if handler marked event as processed correctly
        if not event.is_processed and not event.is_cancelled and not event.processing_errors:
            logger.warning(f"⚠️ HANDLER_INCOMPLETE: {handler.get_handler_name()} "
                          f"did not mark event as processed")
    
    async def post_process(self, event: GameEvent):
        """Final validation after all processing."""
        # Ensure event is in a valid final state
        if not event.is_processed and not event.is_cancelled:
            if not event.processing_errors:
                logger.warning(f"⚠️ EVENT_INCOMPLETE: {event.event_type.value} "
                              f"not marked as processed or cancelled")
    
    def _validate_event_type_specific(self, event: GameEvent) -> List[str]:
        """Validate event data specific to event type."""
        errors = []
        
        # Add specific validation rules based on event type
        if event.event_type == EventType.PHASE_CHANGE_COMPLETED:
            if 'new_phase' not in event.data:
                errors.append("Phase change events must include new_phase")
        
        elif event.event_type == EventType.ACTION_RECEIVED:
            if 'action_type' not in event.data:
                errors.append("Action events must include action_type")
        
        elif event.event_type == EventType.BROADCAST_REQUESTED:
            if 'broadcast_type' not in event.data:
                errors.append("Broadcast events must include broadcast_type")
        
        return errors
    
    def _validate_room_player_context(self, event: GameEvent) -> List[str]:
        """Validate room and player context."""
        errors = []
        
        # Some events require room context
        room_required_events = {
            EventType.PHASE_CHANGE_COMPLETED,
            EventType.BROADCAST_REQUESTED,
            EventType.BOT_NOTIFICATION_SENT
        }
        
        if event.event_type in room_required_events and not event.room_id:
            errors.append(f"Event {event.event_type.value} requires room_id")
        
        # Some events require player context
        player_required_events = {
            EventType.ACTION_RECEIVED,
            EventType.ACTION_EXECUTED
        }
        
        if event.event_type in player_required_events and not event.player_id:
            errors.append(f"Event {event.event_type.value} requires player_id")
        
        return errors
    
    def get_validation_errors(self) -> List[str]:
        """Get all validation errors."""
        return self.validation_errors.copy()
    
    def clear_validation_errors(self):
        """Clear validation error history."""
        self.validation_errors.clear()