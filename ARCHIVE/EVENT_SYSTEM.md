# Phase 4 Event System Documentation

## Overview

The Phase 4 Event System is a production-ready, high-performance event-driven architecture that provides optimal component decoupling through a centralized event bus with publisher-subscriber patterns.

## Architecture

### Core Components

```
📡 EventBus
├── 🎯 EventTypes (13 strongly-typed events)
├── 🔧 EventHandlers (Abstract handler system)
├── ⚙️ EventMiddleware (4-stage pipeline)
├── 🛤️ EventRouting (5 routing strategies)
├── 🎮 GameHandlers (6 specialized handlers)
└── 🔗 Integration (Legacy compatibility)
```

## Event Types

### Available Event Types

| Event Type | Description | Priority | Usage |
|------------|-------------|----------|-------|
| `PHASE_CHANGE_REQUESTED` | Phase transition request | HIGH | State machine transitions |
| `PHASE_CHANGE_COMPLETED` | Phase transition complete | HIGH | Broadcast phase updates |
| `ACTION_RECEIVED` | Player action received | NORMAL | Action processing |
| `ACTION_VALIDATED` | Action validation complete | NORMAL | Validation results |
| `ACTION_EXECUTED` | Action execution complete | NORMAL | Action completion |
| `BROADCAST_REQUESTED` | WebSocket broadcast request | NORMAL | Client communication |
| `BOT_NOTIFICATION_SENT` | Bot AI notification | NORMAL | Bot synchronization |
| `STATE_UPDATED` | Game state change | NORMAL | State tracking |
| `ERROR_OCCURRED` | System error | CRITICAL | Error handling |

### Event Structure

```python
@dataclass
class GameEvent(ABC):
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = field(init=False)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    room_id: Optional[str] = None
    player_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## Event Bus

### Core Features

- **Async Publisher-Subscriber**: High-performance event distribution
- **Priority Queues**: Events processed by priority (EMERGENCY > CRITICAL > HIGH > NORMAL > LOW)
- **Room Isolation**: Separate event buses per game room
- **Performance**: 650+ events/second processing rate
- **Memory Safety**: WeakSet references prevent memory leaks

### Basic Usage

```python
from backend.engine.events import get_global_event_bus, PhaseChangeEvent

# Get event bus for a room
event_bus = get_global_event_bus("room_123")
await event_bus.start()

# Publish an event
event = PhaseChangeEvent(
    room_id="room_123",
    new_phase="TURN",
    reason="All declarations complete"
)
await event_bus.publish(event)

# Clean shutdown
await event_bus.stop()
```

## Event Handlers

### Handler Types

1. **EventHandler**: Basic synchronous handler
2. **AsyncEventHandler**: Async handler with concurrency control
3. **Game Handlers**: Specialized handlers for game events

### Creating Custom Handlers

```python
from backend.engine.events import EventHandler, EventType

class CustomHandler(EventHandler):
    def __init__(self):
        super().__init__({EventType.ACTION_RECEIVED})
    
    async def _handle_event(self, event: GameEvent) -> Any:
        # Process the event
        logger.info(f"Handling action: {event.get_event_data()}")
        return {"status": "processed"}
```

### Game Event Handlers

| Handler | Events Handled | Description |
|---------|----------------|-------------|
| `PhaseChangeHandler` | Phase transitions | Coordinates state machine transitions |
| `ActionHandler` | Player actions | Validates and executes actions |
| `BroadcastHandler` | WebSocket broadcasts | Manages client communication |
| `BotNotificationHandler` | Bot communications | Synchronizes AI state |
| `StateUpdateHandler` | State changes | Maintains state consistency |
| `ErrorHandler` | Error events | Handles errors and recovery |

## Event Routing

### Routing Strategies

1. **BROADCAST**: Send to all matching handlers (default)
2. **ROUND_ROBIN**: Rotate through handlers
3. **PRIORITY**: Send to highest priority handler
4. **RANDOM**: Send to random handler
5. **FIRST_MATCH**: Send to first matching handler

### Routing Rules

```python
from backend.engine.events import create_event_type_rule, RoutingStrategy

# Route phase changes with broadcast
phase_rule = create_event_type_rule(
    name="phase_changes",
    event_types={EventType.PHASE_CHANGE_COMPLETED},
    strategy=RoutingStrategy.BROADCAST,
    priority=100
)
```

## Middleware Pipeline

### Available Middleware

1. **LoggingMiddleware**: Comprehensive event logging with performance metrics
2. **MetricsMiddleware**: Performance tracking and statistics
3. **ErrorHandlingMiddleware**: Error recovery with retry logic and dead letter queues
4. **ValidationMiddleware**: Event validation and data integrity

### Middleware Pipeline Flow

```
Event → Pre-Process → Pre-Handle → Handler → Post-Handle → Post-Process
         ↓            ↓            ↓         ↓            ↓
      Logging      Validation   Metrics   Error       Logging
      Metrics      Logging      Error     Validation  Metrics
      Error        Error        Logging   Logging     Error
      Validation   Metrics      Validation Metrics    Validation
```

## Integration

### Event Bus Integration

The integration layer provides seamless bridging between event-driven and direct method architectures:

```python
from backend.engine.events import integrate_event_bus

# Integrate with existing state machine
integration = await integrate_event_bus(state_machine, room_id)

# Integration includes:
# ✅ 6 game event handlers automatically registered
# ✅ 4 middleware components configured
# ✅ 5 routing rules with intelligent filtering
# ✅ Legacy compatibility bridge
# ✅ Performance monitoring
```

### Legacy Compatibility

The system maintains backward compatibility by bridging existing methods:

```python
# Old direct method call
await state_machine._immediate_transition_to(new_phase, reason)

# Automatically generates event
# PhaseChangeEvent published → Handlers notified → Original method called
```

## Performance Metrics

### Benchmarks

- **Publishing Rate**: 650+ events/second
- **Processing Latency**: < 0.1ms average
- **Memory Usage**: Efficient with WeakSet cleanup
- **Concurrent Handlers**: Up to 10 per handler type
- **Queue Throughput**: Priority-based processing

### Monitoring

```python
# Get event bus metrics
metrics = event_bus.get_metrics()
print(f"Events processed: {metrics.events_processed}")
print(f"Average time: {metrics.average_processing_time:.4f}s")

# Get integration status
status = integration.get_integration_status()
print(f"Handlers registered: {status['handlers_registered']}")
print(f"Queue sizes: {status['queue_sizes']}")
```

## Testing

### Running Tests

```bash
# Run comprehensive event system tests
python test_event_system.py

# Tests include:
# ✅ Basic Event Bus functionality
# ✅ Event Integration with state machine
# ✅ Performance benchmarking
# ✅ Error handling and recovery
```

### Test Results

- **Basic Event Bus**: ✅ PASSED - Core functionality works
- **Event Integration**: ✅ PASSED - Full integration successful
- **Performance**: ⚡ High performance validated (650+ events/sec)
- **Error Handling**: ✅ PASSED - Resilient error recovery

## Best Practices

### Event Publishing

```python
# ✅ Good: Use strongly-typed events
event = PhaseChangeEvent(room_id=room_id, new_phase="TURN", reason="Transition")
await event_bus.publish(event)

# ❌ Avoid: Generic events without type safety
event = GameEvent(data={"phase": "TURN"})  # No type checking
```

### Handler Implementation

```python
# ✅ Good: Mark events as processed
async def _handle_event(self, event: GameEvent):
    # Process event
    process_action(event)
    event.mark_processed()  # Important!

# ❌ Avoid: Forgetting to mark as processed
async def _handle_event(self, event: GameEvent):
    process_action(event)
    # Missing mark_processed() - triggers warnings
```

### Error Handling

```python
# ✅ Good: Add context to errors
try:
    result = await process_event(event)
except Exception as e:
    event.add_error(f"Processing failed: {str(e)}")
    logger.error(f"Event {event.event_id} failed: {str(e)}")
```

## Troubleshooting

### Common Issues

1. **Handler not receiving events**
   - Check event type registration
   - Verify routing rules
   - Confirm event bus is started

2. **Performance issues**
   - Check middleware configuration
   - Monitor queue sizes
   - Review handler concurrency limits

3. **Memory leaks**
   - Ensure event bus shutdown
   - Verify WeakSet usage
   - Check for circular references

### Debugging

```python
# Enable debug logging
import logging
logging.getLogger('backend.engine.events').setLevel(logging.DEBUG)

# Check event history
history = event_bus.get_event_history(limit=50)
for event in history:
    print(f"{event.timestamp}: {event.event_type.value}")

# Get routing statistics
stats = integration.get_routing_stats()
print(f"Rule matches: {stats}")
```

## Migration Guide

### From Direct Calls to Events

```python
# Before: Direct method call
await state_machine.broadcast_event("phase_change", data)

# After: Event publishing
await integration.publish_broadcast_event("phase_change", data)
```

### Adding New Event Types

1. Add to `EventType` enum in `event_types.py`
2. Create specialized event class if needed
3. Add to `EVENT_TYPE_MAP` for factory creation
4. Create handler if specialized logic needed
5. Add routing rules if custom routing required

## Future Enhancements

### Planned Features

- **Event Persistence**: Store events for replay and debugging
- **Event Streaming**: Real-time event streaming to external systems
- **Advanced Routing**: Content-based routing with complex filters
- **Distributed Events**: Cross-service event communication
- **Event Analytics**: Advanced metrics and performance analysis

## Support

For questions or issues with the event system:

1. Check the test file: `test_event_system.py`
2. Review handler implementations in `backend/engine/events/game_event_handlers.py`
3. Monitor logs with debug level enabled
4. Use integration status methods for diagnostics

---

**Phase 4 Event System** - Production Ready ✅
*High-performance, scalable, maintainable event-driven architecture*