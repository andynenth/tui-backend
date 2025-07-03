# backend/engine/events/integration.py

import asyncio
import logging
from typing import Dict, Optional, Set, TYPE_CHECKING

from .event_bus import EventBus, get_global_event_bus
from .event_types import (
    GameEvent, EventType, EventPriority,
    PhaseChangeEvent, ActionEvent, BroadcastEvent,
    StateUpdateEvent, create_event
)
from .event_handlers import EventHandlerRegistry
from .event_middleware import LoggingMiddleware, MetricsMiddleware, ErrorHandlingMiddleware, ValidationMiddleware
from .event_routing import EventRouter, create_event_type_rule, create_room_rule, RoutingStrategy
from .game_event_handlers import create_game_handlers

if TYPE_CHECKING:
    from ..state_machine.game_state_machine import GameStateMachine

logger = logging.getLogger(__name__)


class EventBusIntegration:
    """
    🎯 **Event Bus Integration** - Phase 4 Event System Integration
    
    Integrates the centralized event bus with existing game state machine components,
    providing a seamless bridge between event-driven and direct method architectures.
    
    Features:
    - Automatic event bus setup and configuration
    - Handler registration and routing setup
    - Middleware pipeline configuration
    - Legacy compatibility bridge
    - Performance monitoring and metrics
    """
    
    def __init__(self, state_machine: 'GameStateMachine', room_id: Optional[str] = None):
        self.state_machine = state_machine
        self.room_id = room_id or getattr(state_machine, 'room_id', None)
        
        # Event bus instance
        self.event_bus: Optional[EventBus] = None
        self.event_router = EventRouter()
        
        # Handler tracking
        self.registered_handlers: Dict[str, object] = {}
        self.middleware_instances: Dict[str, object] = {}
        
        # Integration state
        self.is_integrated = False
        self.integration_errors: list = []
        
    async def integrate(self) -> bool:
        """
        Integrate event bus with state machine.
        
        Returns:
            True if integration successful, False otherwise
        """
        try:
            logger.info(f"🔗 EVENT_INTEGRATION: Starting integration for room {self.room_id}")
            
            # Step 1: Initialize event bus
            await self._initialize_event_bus()
            
            # Step 2: Setup middleware pipeline
            self._setup_middleware()
            
            # Step 3: Register game handlers
            await self._register_game_handlers()
            
            # Step 4: Setup routing rules
            self._setup_routing_rules()
            
            # Step 5: Bridge legacy methods
            self._setup_legacy_bridge()
            
            # Step 6: Start event bus
            await self.event_bus.start()
            
            self.is_integrated = True
            logger.info(f"✅ EVENT_INTEGRATION: Successfully integrated event bus")
            return True
            
        except Exception as e:
            logger.error(f"❌ INTEGRATION_ERROR: Failed to integrate event bus: {str(e)}")
            self.integration_errors.append(str(e))
            return False
    
    async def shutdown(self):
        """Shutdown event bus integration."""
        if self.event_bus and self.is_integrated:
            logger.info(f"🛑 EVENT_INTEGRATION: Shutting down event bus")
            await self.event_bus.stop()
            self.is_integrated = False
    
    async def _initialize_event_bus(self):
        """Initialize the event bus instance."""
        # Get or create event bus for this room
        self.event_bus = get_global_event_bus(self.room_id)
        
        if not self.event_bus:
            raise RuntimeError(f"Failed to create event bus for room {self.room_id}")
        
        logger.debug(f"🚀 EVENT_BUS: Initialized for room {self.room_id}")
    
    def _setup_middleware(self):
        """Setup middleware pipeline."""
        try:
            # Logging middleware for debugging
            logging_middleware = LoggingMiddleware(
                log_level=logging.DEBUG,
                include_performance=True
            )
            self.event_bus.add_middleware(logging_middleware)
            self.middleware_instances['logging'] = logging_middleware
            
            # Metrics middleware for performance monitoring
            metrics_middleware = MetricsMiddleware(metrics_interval=30.0)
            self.event_bus.add_middleware(metrics_middleware)
            self.middleware_instances['metrics'] = metrics_middleware
            
            # Error handling middleware for resilience
            error_middleware = ErrorHandlingMiddleware(
                max_retries=2,
                retry_delay=0.5
            )
            self.event_bus.add_middleware(error_middleware)
            self.middleware_instances['error_handling'] = error_middleware
            
            # Validation middleware for data integrity
            validation_middleware = ValidationMiddleware(strict_validation=False)
            self.event_bus.add_middleware(validation_middleware)
            self.middleware_instances['validation'] = validation_middleware
            
            logger.debug(f"⚙️ MIDDLEWARE: Setup {len(self.middleware_instances)} middleware components")
            
        except Exception as e:
            logger.error(f"❌ MIDDLEWARE_ERROR: Failed to setup middleware: {str(e)}")
            raise
    
    async def _register_game_handlers(self):
        """Register all game event handlers."""
        try:
            # Create all game handlers
            handlers = create_game_handlers(self.state_machine)
            
            # Register each handler with the event bus
            for handler_name, handler in handlers.items():
                # Subscribe handler to its supported events
                for event_type in handler.get_supported_events():
                    self.event_bus.subscribe(event_type, handler)
                    logger.debug(f"📝 SUBSCRIBED: {handler_name} to {event_type.value}")
                
                # Register with router for advanced routing
                self.event_router.register_handler(handler_name, handler)
                
                # Track registration
                self.registered_handlers[handler_name] = handler
            
            logger.info(f"📋 HANDLERS: Registered {len(handlers)} game event handlers")
            
        except Exception as e:
            logger.error(f"❌ HANDLER_ERROR: Failed to register handlers: {str(e)}")
            raise
    
    def _setup_routing_rules(self):
        """Setup event routing rules."""
        try:
            # Rule 1: Route phase change events with broadcast strategy
            phase_rule = create_event_type_rule(
                name="phase_changes",
                event_types={
                    EventType.PHASE_CHANGE_REQUESTED,
                    EventType.PHASE_CHANGE_COMPLETED,
                    EventType.PHASE_CHANGE_FAILED
                },
                strategy=RoutingStrategy.BROADCAST,
                priority=100
            )
            self.event_router.add_rule(phase_rule)
            
            # Rule 2: Route action events with priority strategy
            action_rule = create_event_type_rule(
                name="actions",
                event_types={
                    EventType.ACTION_RECEIVED,
                    EventType.ACTION_VALIDATED,
                    EventType.ACTION_EXECUTED,
                    EventType.ACTION_REJECTED
                },
                strategy=RoutingStrategy.PRIORITY,
                priority=90
            )
            self.event_router.add_rule(action_rule)
            
            # Rule 3: Route broadcast events
            broadcast_rule = create_event_type_rule(
                name="broadcasts",
                event_types={
                    EventType.BROADCAST_REQUESTED,
                    EventType.BROADCAST_SENT,
                    EventType.BROADCAST_FAILED
                },
                strategy=RoutingStrategy.FIRST_MATCH,
                priority=80
            )
            self.event_router.add_rule(broadcast_rule)
            
            # Rule 4: Route room-specific events
            if self.room_id:
                room_rule = create_room_rule(
                    name=f"room_{self.room_id}",
                    room_id=self.room_id,
                    strategy=RoutingStrategy.BROADCAST,
                    priority=70
                )
                self.event_router.add_rule(room_rule)
            
            # Rule 5: Route error events with high priority
            error_rule = create_event_type_rule(
                name="errors",
                event_types={
                    EventType.ERROR_OCCURRED,
                    EventType.WARNING_ISSUED,
                    EventType.RECOVERY_ATTEMPTED
                },
                strategy=RoutingStrategy.BROADCAST,
                priority=150  # Highest priority
            )
            self.event_router.add_rule(error_rule)
            
            logger.debug(f"🛤️ ROUTING: Setup {len(self.event_router.routing_rules)} routing rules")
            
        except Exception as e:
            logger.error(f"❌ ROUTING_ERROR: Failed to setup routing: {str(e)}")
            raise
    
    def _setup_legacy_bridge(self):
        """Setup bridge for legacy method compatibility."""
        try:
            # Monkey patch state machine methods to emit events
            original_methods = {}
            
            # Bridge phase transitions
            if hasattr(self.state_machine, '_immediate_transition_to'):
                original_methods['_immediate_transition_to'] = self.state_machine._immediate_transition_to
                self.state_machine._immediate_transition_to = self._bridge_phase_transition
            
            # Bridge action handling
            if hasattr(self.state_machine, 'handle_action'):
                original_methods['handle_action'] = self.state_machine.handle_action
                self.state_machine.handle_action = self._bridge_action_handling
            
            # Bridge broadcasting
            if hasattr(self.state_machine, 'broadcast_event'):
                original_methods['broadcast_event'] = self.state_machine.broadcast_event
                self.state_machine.broadcast_event = self._bridge_broadcast_event
            
            # Store original methods for restoration
            self.state_machine._event_bridge_originals = original_methods
            
            logger.debug(f"🌉 BRIDGE: Setup legacy compatibility bridge for {len(original_methods)} methods")
            
        except Exception as e:
            logger.error(f"❌ BRIDGE_ERROR: Failed to setup legacy bridge: {str(e)}")
            # Don't raise here - legacy bridge is optional
    
    async def _bridge_phase_transition(self, new_phase, reason: str):
        """Bridge phase transitions to emit events."""
        try:
            # Emit phase change request event
            event = PhaseChangeEvent(
                room_id=self.room_id,
                new_phase=new_phase.name if hasattr(new_phase, 'name') else str(new_phase),
                reason=reason,
                priority=EventPriority.HIGH
            )
            
            await self.publish_event(event)
            
            # Call original method
            original_method = self.state_machine._event_bridge_originals.get('_immediate_transition_to')
            if original_method:
                await original_method(new_phase, reason)
            
        except Exception as e:
            logger.error(f"❌ BRIDGE_PHASE_ERROR: {str(e)}")
            # Fallback to original method
            original_method = self.state_machine._event_bridge_originals.get('_immediate_transition_to')
            if original_method:
                await original_method(new_phase, reason)
    
    async def _bridge_action_handling(self, action):
        """Bridge action handling to emit events."""
        try:
            # Emit action received event
            event = ActionEvent(
                room_id=self.room_id,
                action_type=action.action_type.value if hasattr(action.action_type, 'value') else str(action.action_type),
                player_name=getattr(action, 'player_name', 'Unknown'),
                action_payload=getattr(action, 'payload', {}),
                priority=EventPriority.NORMAL
            )
            
            await self.publish_event(event)
            
            # Call original method
            original_method = self.state_machine._event_bridge_originals.get('handle_action')
            if original_method:
                return await original_method(action)
            
        except Exception as e:
            logger.error(f"❌ BRIDGE_ACTION_ERROR: {str(e)}")
            # Fallback to original method
            original_method = self.state_machine._event_bridge_originals.get('handle_action')
            if original_method:
                return await original_method(action)
    
    async def _bridge_broadcast_event(self, event_type: str, event_data: dict):
        """Bridge broadcast events to emit events."""
        try:
            # Emit broadcast request event
            event = BroadcastEvent(
                room_id=self.room_id,
                broadcast_type=event_type,
                message_data=event_data,
                priority=EventPriority.NORMAL
            )
            
            await self.publish_event(event)
            
            # Call original method
            original_method = self.state_machine._event_bridge_originals.get('broadcast_event')
            if original_method:
                await original_method(event_type, event_data)
            
        except Exception as e:
            logger.error(f"❌ BRIDGE_BROADCAST_ERROR: {str(e)}")
            # Fallback to original method
            original_method = self.state_machine._event_bridge_originals.get('broadcast_event')
            if original_method:
                await original_method(event_type, event_data)
    
    async def publish_event(self, event: GameEvent, **kwargs):
        """Publish an event through the integrated event bus."""
        if self.event_bus and self.is_integrated:
            await self.event_bus.publish(event, **kwargs)
        else:
            logger.warning(f"⚠️ EVENT_BUS: Not integrated, cannot publish {event.event_type.value}")
    
    async def publish_phase_change(self, old_phase: str, new_phase: str, reason: str):
        """Convenience method to publish phase change events."""
        event = PhaseChangeEvent(
            room_id=self.room_id,
            old_phase=old_phase,
            new_phase=new_phase,
            reason=reason,
            priority=EventPriority.HIGH
        )
        await self.publish_event(event)
    
    async def publish_action_event(self, action_type: str, player_name: str, payload: dict, event_type: EventType = EventType.ACTION_RECEIVED):
        """Convenience method to publish action events."""
        event = ActionEvent(
            room_id=self.room_id,
            action_type=action_type,
            player_name=player_name,
            action_payload=payload,
            priority=EventPriority.NORMAL
        )
        event.event_type = event_type
        await self.publish_event(event)
    
    async def publish_broadcast_event(self, broadcast_type: str, message_data: dict):
        """Convenience method to publish broadcast events."""
        event = BroadcastEvent(
            room_id=self.room_id,
            broadcast_type=broadcast_type,
            message_data=message_data,
            priority=EventPriority.NORMAL
        )
        await self.publish_event(event)
    
    async def publish_state_update(self, state_type: str, state_data: dict, reason: str):
        """Convenience method to publish state update events."""
        event = StateUpdateEvent(
            room_id=self.room_id,
            state_type=state_type,
            state_data=state_data,
            update_reason=reason,
            priority=EventPriority.NORMAL
        )
        await self.publish_event(event)
    
    def get_integration_status(self) -> dict:
        """Get integration status and metrics."""
        status = {
            'is_integrated': self.is_integrated,
            'room_id': self.room_id,
            'handlers_registered': len(self.registered_handlers),
            'middleware_count': len(self.middleware_instances),
            'routing_rules': len(self.event_router.routing_rules) if self.event_router else 0,
            'integration_errors': self.integration_errors.copy()
        }
        
        # Add event bus metrics if available
        if self.event_bus:
            status['event_bus_metrics'] = self.event_bus.get_metrics()
            status['queue_sizes'] = self.event_bus.get_queue_sizes()
        
        # Add middleware metrics
        if 'metrics' in self.middleware_instances:
            metrics_middleware = self.middleware_instances['metrics']
            status['middleware_metrics'] = metrics_middleware.get_metrics()
        
        return status
    
    def get_handler_registry(self) -> Dict[str, object]:
        """Get registered handlers."""
        return self.registered_handlers.copy()
    
    def get_routing_stats(self) -> dict:
        """Get routing statistics."""
        if self.event_router:
            return self.event_router.get_routing_stats()
        return {}


# Factory function for easy integration
async def integrate_event_bus(state_machine: 'GameStateMachine', room_id: Optional[str] = None) -> EventBusIntegration:
    """
    Factory function to integrate event bus with state machine.
    
    Args:
        state_machine: The game state machine to integrate
        room_id: Optional room ID for scoped integration
        
    Returns:
        Configured EventBusIntegration instance
    """
    integration = EventBusIntegration(state_machine, room_id)
    
    success = await integration.integrate()
    if not success:
        logger.error(f"❌ INTEGRATION_FAILED: Could not integrate event bus")
        raise RuntimeError("Event bus integration failed")
    
    logger.info(f"✅ INTEGRATION_SUCCESS: Event bus integrated successfully")
    return integration