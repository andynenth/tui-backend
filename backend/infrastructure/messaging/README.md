# Message Queue Infrastructure

## Overview

The Message Queue infrastructure provides asynchronous message processing capabilities for the Liap Tui game system. It implements various queue patterns, routing strategies, and handler types to support reliable, scalable message-based communication between system components.

## Key Features

### 1. **Multiple Queue Types**
- **InMemoryQueue**: Basic FIFO queue with TTL and delay support
- **PriorityInMemoryQueue**: Priority-based message ordering
- **BoundedInMemoryQueue**: Size-limited queue with overflow strategies

### 2. **Dead Letter Queue Support**
- Failed message handling
- Automatic retry with exponential backoff
- Message inspection and recovery
- Configurable retry policies

### 3. **Flexible Routing**
- Topic-based routing (MQTT-style)
- Pattern matching (glob, regex)
- Direct routing
- Content-based routing

### 4. **Message Handlers**
- Async handlers with concurrency control
- Batch processing
- Chain of responsibility
- Error handling and retry logic
- Timeout enforcement

### 5. **Game Integration**
- Specialized game event queue
- Game-specific routing
- Background task processing
- Bot move calculations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Message Queue System                       │
│                                                              │
│  ┌─────────────┐     ┌──────────────┐    ┌──────────────┐  │
│  │  Publishers │────▶│    Router    │───▶│    Queues    │  │
│  └─────────────┘     └──────────────┘    └──────────────┘  │
│                              │                     │          │
│                              ▼                     ▼          │
│                      ┌──────────────┐    ┌──────────────┐   │
│                      │   Filters    │    │   Handlers   │   │
│                      └──────────────┘    └──────────────┘   │
│                                                   │           │
│                                                   ▼           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Dead Letter Queue                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Message Structure

```python
from backend.infrastructure.messaging import Message, MessagePriority

# Create a message
message = Message(
    payload={"event": "game_started", "room_id": "123"},
    priority=MessagePriority.HIGH
)

# Add metadata
message.metadata.source = "game_engine"
message.metadata.correlation_id = "req_456"
```

### 2. Queue Operations

```python
from backend.infrastructure.messaging import InMemoryQueue, DeliveryOptions
from datetime import timedelta

# Create queue
queue = InMemoryQueue("game_events")

# Enqueue with options
options = DeliveryOptions(
    ttl=timedelta(minutes=5),
    delay=timedelta(seconds=1),
    priority=MessagePriority.HIGH
)

message_id = await queue.enqueue(message, options)

# Dequeue and process
msg = await queue.dequeue(timeout=5.0)
if msg:
    # Process message
    await process_message(msg)
    
    # Acknowledge completion
    await queue.acknowledge(msg.metadata.message_id)
```

### 3. Dead Letter Queue

```python
from backend.infrastructure.messaging import (
    DeadLetterQueue,
    DeadLetterPolicy,
    DeadLetterHandler
)

# Configure DLQ policy
policy = DeadLetterPolicy(
    max_retries=3,
    ttl=timedelta(hours=24),
    retry_delay=timedelta(minutes=1),
    exponential_backoff=True
)

# Create DLQ
dlq = DeadLetterQueue("failed_messages", policy)

# Wrap handler with DLQ support
handler = YourMessageHandler()
dlq_handler = DeadLetterHandler(handler, dlq, policy)

# Failed messages automatically go to DLQ
await dlq_handler.handle(message)
```

### 4. Message Routing

```python
from backend.infrastructure.messaging import TopicRouter

# Create router
router = TopicRouter("game_router")

# Register queues
router.register_queue("game_events", game_queue)
router.register_queue("player_events", player_queue)

# Define routes
router.register_route("game.*", "game_events")
router.register_route("player.*.joined", "player_events")
router.register_route("#", "all_events")  # Catch-all

# Route message
destinations = await router.route(message, "game.started")
```

### 5. Message Handlers

```python
from backend.infrastructure.messaging import (
    AsyncMessageHandler,
    BatchMessageHandler,
    RetryingHandler,
    TimeoutHandler
)

# Async handler with concurrency control
async def process_game_event(message):
    # Process game event
    pass

handler = AsyncMessageHandler(
    process_game_event,
    max_concurrent=10
)

# Batch processing
batch_handler = BatchMessageHandler(
    batch_func=process_batch,
    batch_size=100,
    batch_timeout=timedelta(seconds=5)
)

# Add retry logic
retry_handler = RetryingHandler(
    handler,
    RetryPolicy(max_retries=3, initial_delay=timedelta(seconds=1))
)

# Add timeout
timeout_handler = TimeoutHandler(
    retry_handler,
    timeout=timedelta(seconds=30)
)
```

## Game Integration

### Game Event Queue

```python
from backend.infrastructure.messaging import (
    GameEventQueue,
    GameEvent,
    GameEventType
)

# Create game event queue
event_queue = GameEventQueue("game_events")

# Publish game event
event = GameEvent(
    event_type=GameEventType.GAME_STARTED,
    room_id="room_123",
    game_id="game_456",
    player_id="player_789",
    data={
        "players": ["p1", "p2", "p3", "p4"],
        "initial_state": "preparation"
    }
)

event_id = await event_queue.publish(event, MessagePriority.HIGH)

# Subscribe to events
class GameStartHandler(GameEventHandler):
    async def process_event(self, event: GameEvent):
        # Handle game start
        await initialize_game(event.data)

handler = GameStartHandler(
    event_types={GameEventType.GAME_STARTED}
)

event_queue.subscribe("game.started", handler)

# Process events
await event_queue.process_events()
```

### Task Processing

```python
from backend.infrastructure.messaging import GameTaskProcessor

# Create task processor
processor = GameTaskProcessor(max_workers=5)

# Register task handlers
async def calculate_bot_move(data):
    game_id = data['game_id']
    player_id = data['player_id']
    # Calculate and return bot move
    
processor.register_task_handler('bot_move', calculate_bot_move)

# Start processing
await processor.start()

# Submit tasks
await processor.submit_task(
    'bot_move',
    {'game_id': 'game_123', 'player_id': 'bot_1'},
    priority=MessagePriority.HIGH
)

# Shutdown when done
await processor.stop()
```

## Usage Examples

### Example 1: Game Room Events

```python
# Setup for room event processing
room_queue = PriorityInMemoryQueue("room_events")
room_router = TopicRouter("room_router")

# Register routes
room_router.register_queue("room_events", room_queue)
room_router.register_route("room.*", "room_events")

# Room event handler
class RoomEventHandler(GameEventHandler):
    async def process_event(self, event: GameEvent):
        if event.event_type == GameEventType.ROOM_CREATED:
            await notify_lobby(event.room_id)
        elif event.event_type == GameEventType.ROOM_CLOSED:
            await cleanup_room(event.room_id)

# Process room events
handler = RoomEventHandler()
async def process_room_events():
    while True:
        msg = await room_queue.dequeue(timeout=1.0)
        if msg:
            await handler.handle(msg)
            await room_queue.acknowledge(msg.metadata.message_id)
```

### Example 2: Reliable Task Processing

```python
# Create reliable task queue with DLQ
task_queue = BoundedInMemoryQueue(
    "tasks",
    max_size=1000,
    overflow_strategy="reject"
)

dlq = RetryableDeadLetterQueue(
    "task_dlq",
    DeadLetterPolicy(
        max_retries=5,
        retry_delay=timedelta(seconds=30),
        exponential_backoff=True
    )
)

# Register retry queue
dlq.register_retry_queue("tasks", task_queue)

# Task handler with error handling
async def process_task(message):
    task = message.payload
    try:
        result = await execute_task(task)
        return result
    except TemporaryError:
        # Will be retried
        raise
    except PermanentError:
        # Send to DLQ
        await dlq.add(
            message,
            DeadLetterReason.VALIDATION_FAILED
        )

handler = AsyncMessageHandler(process_task)
dlq_handler = DeadLetterHandler(handler, dlq)
```

### Example 3: Event Broadcasting

```python
# Broadcast game state changes
async def broadcast_state_change(game_id, new_state, old_state):
    event = GameEvent(
        event_type=GameEventType.STATE_CHANGED,
        game_id=game_id,
        data={
            'old_state': old_state,
            'new_state': new_state,
            'timestamp': datetime.utcnow().isoformat()
        }
    )
    
    # Publish with high priority
    await event_queue.publish(event, MessagePriority.HIGH)
    
    # Also send to analytics queue
    analytics_event = Message(
        payload={
            'event': 'state_transition',
            'game_id': game_id,
            'transition': f"{old_state}->{new_state}"
        }
    )
    
    await analytics_queue.enqueue(analytics_event)
```

## Performance Considerations

### 1. **Queue Sizing**
- Use bounded queues to prevent memory exhaustion
- Configure appropriate overflow strategies
- Monitor queue depths

### 2. **Concurrency Control**
- Limit concurrent handlers to prevent resource exhaustion
- Use semaphores for fine-grained control
- Balance throughput with resource usage

### 3. **Batch Processing**
- Group similar messages for efficient processing
- Configure batch sizes based on workload
- Use timeouts to prevent starvation

### 4. **Priority Management**
- Reserve high priority for critical events
- Use normal priority for routine operations
- Avoid priority inversion

## Monitoring and Metrics

```python
# Get queue statistics
stats = queue.get_stats()
print(f"Enqueued: {stats['enqueued']}")
print(f"Processed: {stats['dequeued']}")
print(f"Failed: {stats['rejected']}")

# Get DLQ metrics
dlq_stats = dlq.get_stats()
print(f"Dead letters: {dlq_stats['total_entries']}")
print(f"By reason: {dlq_stats['by_reason']}")

# Get handler metrics
retry_stats = retry_handler.get_stats()
print(f"Total retries: {retry_stats['total_retries']}")
print(f"Success rate: {retry_stats['successful_retries'] / retry_stats['total_retries']}")
```

## Configuration

### Environment Variables
```bash
# Queue settings
MESSAGE_QUEUE_TYPE=memory  # memory, redis (future)
MAX_QUEUE_SIZE=10000
DEFAULT_MESSAGE_TTL=300  # seconds

# DLQ settings
DLQ_MAX_RETRIES=3
DLQ_RETRY_DELAY=60  # seconds
DLQ_RETENTION_HOURS=24

# Handler settings
MAX_CONCURRENT_HANDLERS=10
HANDLER_TIMEOUT_SECONDS=30
BATCH_SIZE=100
BATCH_TIMEOUT_SECONDS=5
```

## Best Practices

1. **Message Design**
   - Keep payloads small and focused
   - Use correlation IDs for request tracking
   - Include timestamps for debugging

2. **Error Handling**
   - Always wrap handlers with error handling
   - Use DLQ for unprocessable messages
   - Log errors with context

3. **Performance**
   - Use batching for high-volume operations
   - Configure appropriate concurrency limits
   - Monitor queue depths and processing rates

4. **Testing**
   - Test timeout scenarios
   - Verify DLQ behavior
   - Load test with expected volumes

## Future Enhancements

1. **Distributed Queuing**
   - Redis-based queue implementation
   - RabbitMQ/Kafka adapters
   - Cluster-aware routing

2. **Advanced Features**
   - Message deduplication
   - Scheduled message delivery
   - Message versioning

3. **Monitoring**
   - Prometheus metrics export
   - Real-time queue dashboards
   - Alert thresholds

## Conclusion

The Message Queue infrastructure provides a robust foundation for asynchronous processing in the Liap Tui game system. With support for various queue types, routing strategies, and reliability features, it enables scalable and maintainable message-based architectures.