"""
Comprehensive tests for message queue infrastructure.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Any

from backend.infrastructure.messaging import (
    # Base types
    Message,
    MessagePriority,
    MessageStatus,
    MessageMetadata,
    DeliveryOptions,
    RetryPolicy,
    
    # Queues
    InMemoryQueue,
    PriorityInMemoryQueue,
    BoundedInMemoryQueue,
    
    # Dead letter
    DeadLetterQueue,
    DeadLetterPolicy,
    DeadLetterReason,
    DeadLetterHandler,
    RetryableDeadLetterQueue,
    
    # Routing
    MessageRouter,
    TopicRouter,
    DirectRouter,
    PatternRouter,
    
    # Serialization
    JsonMessageSerializer,
    PickleMessageSerializer,
    CompositeSerializer,
    
    # Handlers
    AsyncMessageHandler,
    BatchMessageHandler,
    ChainedMessageHandler,
    ErrorHandlingWrapper,
    RetryingHandler,
    TimeoutHandler,
    
    # Game integration
    GameEventQueue,
    GameEvent,
    GameEventType,
    GameEventHandler,
    GameTaskProcessor
)


class TestMessage:
    """Test message functionality."""
    
    def test_message_creation(self):
        """Test creating a message."""
        payload = {"data": "test"}
        message = Message(payload=payload)
        
        assert message.payload == payload
        assert message.status == MessageStatus.PENDING
        assert message.priority == MessagePriority.NORMAL
        assert message.metadata.message_id is not None
        assert isinstance(message.metadata.timestamp, datetime)
    
    def test_message_expiration(self):
        """Test message expiration check."""
        # Not expired
        message = Message(payload="test")
        assert not message.is_expired()
        
        # Expired
        message.metadata.expires_at = datetime.utcnow() - timedelta(seconds=1)
        assert message.is_expired()
    
    def test_message_serialization(self):
        """Test message to_dict conversion."""
        message = Message(
            payload={"key": "value"},
            priority=MessagePriority.HIGH
        )
        message.metadata.source = "test_source"
        
        data = message.to_dict()
        assert data['message_id'] == message.metadata.message_id
        assert data['payload'] == {"key": "value"}
        assert data['priority'] == MessagePriority.HIGH.value
        assert data['metadata']['source'] == "test_source"


class TestRetryPolicy:
    """Test retry policy functionality."""
    
    def test_retry_delay_calculation(self):
        """Test retry delay calculation."""
        policy = RetryPolicy(
            initial_delay=timedelta(seconds=1),
            exponential_backoff=True,
            backoff_multiplier=2.0,
            max_delay=timedelta(seconds=10)
        )
        
        # First retry: 1s
        assert policy.calculate_delay(1) == timedelta(seconds=1)
        
        # Second retry: 2s
        assert policy.calculate_delay(2) == timedelta(seconds=2)
        
        # Third retry: 4s
        assert policy.calculate_delay(3) == timedelta(seconds=4)
        
        # Fourth retry: 8s
        assert policy.calculate_delay(4) == timedelta(seconds=8)
        
        # Fifth retry: capped at 10s
        assert policy.calculate_delay(5) == timedelta(seconds=10)
    
    def test_no_exponential_backoff(self):
        """Test fixed retry delay."""
        policy = RetryPolicy(
            initial_delay=timedelta(seconds=5),
            exponential_backoff=False
        )
        
        assert policy.calculate_delay(1) == timedelta(seconds=5)
        assert policy.calculate_delay(5) == timedelta(seconds=5)


class TestInMemoryQueue:
    """Test in-memory queue implementation."""
    
    @pytest.mark.asyncio
    async def test_basic_enqueue_dequeue(self):
        """Test basic queue operations."""
        queue = InMemoryQueue("test")
        
        # Enqueue
        message = Message(payload="test_data")
        message_id = await queue.enqueue(message)
        assert message_id == message.metadata.message_id
        
        # Check size
        assert await queue.size() == 1
        
        # Dequeue
        dequeued = await queue.dequeue()
        assert dequeued is not None
        assert dequeued.payload == "test_data"
        assert dequeued.status == MessageStatus.PROCESSING
        
        # Queue should be empty
        assert await queue.size() == 0
    
    @pytest.mark.asyncio
    async def test_fifo_ordering(self):
        """Test FIFO message ordering."""
        queue = InMemoryQueue("test")
        
        # Enqueue multiple messages
        for i in range(5):
            message = Message(payload=f"msg_{i}")
            await queue.enqueue(message)
        
        # Dequeue and verify order
        for i in range(5):
            message = await queue.dequeue()
            assert message.payload == f"msg_{i}"
    
    @pytest.mark.asyncio
    async def test_message_ttl(self):
        """Test message TTL expiration."""
        queue = InMemoryQueue("test")
        
        # Enqueue with TTL
        message = Message(payload="expires")
        options = DeliveryOptions(ttl=timedelta(milliseconds=100))
        await queue.enqueue(message, options)
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Should skip expired message
        dequeued = await queue.dequeue()
        assert dequeued is None
        assert queue.get_stats()['expired'] == 1
    
    @pytest.mark.asyncio
    async def test_acknowledge_reject(self):
        """Test message acknowledgment and rejection."""
        queue = InMemoryQueue("test")
        
        # Enqueue and dequeue
        message = Message(payload="test")
        message_id = await queue.enqueue(message)
        dequeued = await queue.dequeue()
        
        # Acknowledge
        success = await queue.acknowledge(message_id)
        assert success
        assert queue.get_stats()['acknowledged'] == 1
        
        # Enqueue another
        message2 = Message(payload="test2")
        message_id2 = await queue.enqueue(message2)
        await queue.dequeue()
        
        # Reject with requeue
        success = await queue.reject(message_id2, requeue=True)
        assert success
        assert await queue.size() == 1
        assert queue.get_stats()['rejected'] == 1
    
    @pytest.mark.asyncio
    async def test_delayed_enqueue(self):
        """Test delayed message delivery."""
        queue = InMemoryQueue("test")
        
        # Enqueue with delay
        message = Message(payload="delayed")
        options = DeliveryOptions(delay=timedelta(milliseconds=100))
        
        start_time = datetime.utcnow()
        await queue.enqueue(message, options)
        
        # Should not be available immediately
        assert await queue.size() == 0
        
        # Wait for delay
        await asyncio.sleep(0.15)
        
        # Should be available now
        assert await queue.size() == 1
        dequeued = await queue.dequeue()
        assert dequeued.payload == "delayed"
        
        # Verify delay
        elapsed = datetime.utcnow() - start_time
        assert elapsed.total_seconds() >= 0.1
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent queue operations."""
        queue = InMemoryQueue("test")
        
        async def producer(n: int):
            for i in range(n):
                message = Message(payload=f"producer_{i}")
                await queue.enqueue(message)
                await asyncio.sleep(0.01)
        
        async def consumer(n: int):
            consumed = []
            for _ in range(n):
                message = await queue.dequeue(timeout=1.0)
                if message:
                    consumed.append(message.payload)
                    await queue.acknowledge(message.metadata.message_id)
            return consumed
        
        # Run producers and consumers concurrently
        await asyncio.gather(
            producer(10),
            producer(10),
            consumer(20)
        )
        
        # All messages should be processed
        assert await queue.size() == 0
        stats = queue.get_stats()
        assert stats['enqueued'] == 20
        assert stats['dequeued'] == 20
        assert stats['acknowledged'] == 20


class TestPriorityQueue:
    """Test priority queue implementation."""
    
    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test messages are dequeued by priority."""
        queue = PriorityInMemoryQueue("test")
        
        # Enqueue messages with different priorities
        messages = [
            (Message(payload="low", priority=MessagePriority.LOW), MessagePriority.LOW),
            (Message(payload="critical", priority=MessagePriority.CRITICAL), MessagePriority.CRITICAL),
            (Message(payload="normal", priority=MessagePriority.NORMAL), MessagePriority.NORMAL),
            (Message(payload="high", priority=MessagePriority.HIGH), MessagePriority.HIGH),
        ]
        
        for msg, _ in messages:
            await queue.enqueue(msg)
        
        # Should dequeue in priority order
        expected_order = ["critical", "high", "normal", "low"]
        for expected in expected_order:
            message = await queue.dequeue()
            assert message.payload == expected
    
    @pytest.mark.asyncio
    async def test_fifo_within_priority(self):
        """Test FIFO ordering within same priority."""
        queue = PriorityInMemoryQueue("test")
        
        # Enqueue multiple messages with same priority
        for i in range(5):
            message = Message(payload=f"msg_{i}", priority=MessagePriority.NORMAL)
            await queue.enqueue(message)
        
        # Should maintain FIFO within priority
        for i in range(5):
            message = await queue.dequeue()
            assert message.payload == f"msg_{i}"


class TestBoundedQueue:
    """Test bounded queue implementation."""
    
    @pytest.mark.asyncio
    async def test_reject_overflow(self):
        """Test rejection when queue is full."""
        queue = BoundedInMemoryQueue("test", max_size=3, overflow_strategy="reject")
        
        # Fill queue
        for i in range(3):
            await queue.enqueue(Message(payload=f"msg_{i}"))
        
        # Should reject new message
        with pytest.raises(OverflowError):
            await queue.enqueue(Message(payload="overflow"))
    
    @pytest.mark.asyncio
    async def test_drop_oldest_overflow(self):
        """Test dropping oldest message when full."""
        queue = BoundedInMemoryQueue("test", max_size=3, overflow_strategy="drop_oldest")
        
        # Fill queue
        for i in range(3):
            await queue.enqueue(Message(payload=f"msg_{i}"))
        
        # Add one more - should drop oldest
        await queue.enqueue(Message(payload="new"))
        
        # Verify oldest was dropped
        messages = []
        while True:
            msg = await queue.dequeue()
            if not msg:
                break
            messages.append(msg.payload)
        
        assert messages == ["msg_1", "msg_2", "new"]


class TestDeadLetterQueue:
    """Test dead letter queue functionality."""
    
    @pytest.mark.asyncio
    async def test_add_to_dlq(self):
        """Test adding messages to dead letter queue."""
        dlq = DeadLetterQueue("test_dlq")
        
        message = Message(payload="failed_message")
        error = ValueError("Processing failed")
        
        message_id = await dlq.add(
            message,
            DeadLetterReason.PROCESSING_FAILED,
            error,
            "original_queue"
        )
        
        assert message_id == message.metadata.message_id
        assert await dlq.size() == 1
        
        # Check stats
        stats = dlq.get_stats()
        assert stats['total_entries'] == 1
        assert stats['by_reason']['processing_failed'] == 1
    
    @pytest.mark.asyncio
    async def test_retry_from_dlq(self):
        """Test retrying messages from DLQ."""
        dlq = DeadLetterQueue("test_dlq")
        target_queue = InMemoryQueue("target")
        
        # Add to DLQ
        message = Message(payload="retry_me")
        await dlq.add(message, DeadLetterReason.PROCESSING_FAILED)
        
        # Retry to target queue
        success = await dlq.retry(message.metadata.message_id, target_queue)
        assert success
        
        # Check message in target queue
        retried = await target_queue.dequeue()
        assert retried.payload == "retry_me"
        assert retried.status == MessageStatus.PROCESSING
        
        # DLQ should be empty
        assert await dlq.size() == 0
    
    @pytest.mark.asyncio
    async def test_dlq_handler(self):
        """Test dead letter handler wrapper."""
        dlq = DeadLetterQueue("test_dlq")
        failed_count = 0
        
        # Create failing handler
        async def failing_handler(message: Message):
            nonlocal failed_count
            failed_count += 1
            raise ValueError("Always fails")
        
        handler = AsyncMessageHandler(failing_handler)
        dlq_handler = DeadLetterHandler(
            handler,
            dlq,
            DeadLetterPolicy(max_retries=2)
        )
        
        # Process message
        message = Message(payload="test")
        
        with pytest.raises(ValueError):
            await dlq_handler.handle(message)
        
        # Should not be in DLQ yet (first attempt)
        assert await dlq.size() == 0
        
        # Retry twice more
        message.metadata.attempts = 1
        with pytest.raises(ValueError):
            await dlq_handler.handle(message)
        
        # Now should be in DLQ
        assert await dlq.size() == 1
    
    @pytest.mark.asyncio
    async def test_retryable_dlq(self):
        """Test retryable dead letter queue."""
        dlq = RetryableDeadLetterQueue(
            "test_rdlq",
            DeadLetterPolicy(
                max_retries=3,
                retry_delay=timedelta(milliseconds=100)
            )
        )
        
        original_queue = InMemoryQueue("original")
        retry_queue = InMemoryQueue("retry")
        
        # Register retry queue
        dlq.register_retry_queue("original", retry_queue)
        
        # Add message that should be retried
        message = Message(payload="auto_retry")
        await dlq.add(
            message,
            DeadLetterReason.PROCESSING_FAILED,
            original_queue="original"
        )
        
        # Wait for automatic retry
        await asyncio.sleep(0.15)
        
        # Check message was retried
        retried = await retry_queue.dequeue()
        assert retried is not None
        assert retried.payload == "auto_retry"
        
        # Cleanup
        await dlq.shutdown()


class TestMessageRouting:
    """Test message routing functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_routing(self):
        """Test basic message routing."""
        router = MessageRouter("test_router")
        
        # Create queues
        queue1 = InMemoryQueue("queue1")
        queue2 = InMemoryQueue("queue2")
        
        # Register queues and routes
        router.register_queue("queue1", queue1)
        router.register_queue("queue2", queue2)
        
        router.register_route("pattern1", "queue1")
        router.register_route("pattern2", "queue2")
        router.register_route("both", "queue1")
        router.register_route("both", "queue2")
        
        # Route messages
        msg1 = Message(payload="to_queue1")
        destinations = await router.route(msg1, "pattern1")
        assert destinations == ["queue1"]
        assert await queue1.size() == 1
        assert await queue2.size() == 0
        
        msg2 = Message(payload="to_both")
        destinations = await router.route(msg2, "both")
        assert set(destinations) == {"queue1", "queue2"}
        assert await queue1.size() == 2
        assert await queue2.size() == 1
    
    @pytest.mark.asyncio
    async def test_topic_routing(self):
        """Test topic-based routing."""
        router = TopicRouter("test_topic_router")
        
        # Create queues
        game_queue = InMemoryQueue("game_events")
        player_queue = InMemoryQueue("player_events")
        all_queue = InMemoryQueue("all_events")
        
        # Register queues and routes
        router.register_queue("game_events", game_queue)
        router.register_queue("player_events", player_queue)
        router.register_queue("all_events", all_queue)
        
        # Topic patterns
        router.register_route("game.*", "game_events")
        router.register_route("player.*.joined", "player_events")
        router.register_route("#", "all_events")
        
        # Test routing
        msg1 = Message(payload="game_start")
        await router.route(msg1, "game.started")
        assert await game_queue.size() == 1
        assert await player_queue.size() == 0
        assert await all_queue.size() == 1
        
        msg2 = Message(payload="player_join")
        await router.route(msg2, "player.123.joined")
        assert await game_queue.size() == 1
        assert await player_queue.size() == 1
        assert await all_queue.size() == 2
    
    @pytest.mark.asyncio
    async def test_direct_routing(self):
        """Test direct queue routing."""
        router = DirectRouter("test_direct")
        
        # Create queues
        queue1 = InMemoryQueue("direct1")
        queue2 = InMemoryQueue("direct2")
        
        router.register_queue("direct1", queue1)
        router.register_queue("direct2", queue2)
        
        # Route directly by name
        msg = Message(payload="direct")
        destinations = await router.route(msg, "direct1")
        assert destinations == ["direct1"]
        assert await queue1.size() == 1
        assert await queue2.size() == 0


class TestMessageSerialization:
    """Test message serialization."""
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        serializer = JsonMessageSerializer()
        
        # Create message
        message = Message(
            payload={"key": "value", "number": 42},
            priority=MessagePriority.HIGH
        )
        message.metadata.source = "test"
        
        # Serialize
        data = serializer.serialize(message)
        assert isinstance(data, bytes)
        
        # Deserialize
        deserialized = serializer.deserialize(data)
        assert deserialized.payload == {"key": "value", "number": 42}
        assert deserialized.priority == MessagePriority.HIGH
        assert deserialized.metadata.source == "test"
    
    def test_pickle_serialization(self):
        """Test pickle serialization."""
        serializer = PickleMessageSerializer()
        
        # Create message with complex payload
        class CustomObject:
            def __init__(self, value):
                self.value = value
        
        obj = CustomObject("test")
        message = Message(payload=obj)
        
        # Serialize
        data = serializer.serialize(message)
        
        # Deserialize
        deserialized = serializer.deserialize(data)
        assert isinstance(deserialized.payload, CustomObject)
        assert deserialized.payload.value == "test"
    
    def test_composite_serializer(self):
        """Test composite serializer."""
        serializer = CompositeSerializer()
        
        # JSON message
        json_msg = Message(payload={"type": "json"})
        json_msg.metadata.content_type = "application/json"
        
        data = serializer.serialize(json_msg)
        deserialized = serializer.deserialize(data)
        assert deserialized.payload == {"type": "json"}


class TestMessageHandlers:
    """Test message handler implementations."""
    
    @pytest.mark.asyncio
    async def test_async_handler(self):
        """Test async message handler."""
        processed = []
        
        async def handler_func(message: Message):
            await asyncio.sleep(0.01)
            processed.append(message.payload)
        
        handler = AsyncMessageHandler(handler_func, max_concurrent=2)
        
        # Process multiple messages
        messages = [Message(payload=f"msg_{i}") for i in range(5)]
        
        await asyncio.gather(*[handler.handle(msg) for msg in messages])
        
        assert len(processed) == 5
        assert all(msg.status == MessageStatus.COMPLETED for msg in messages)
        
        # Cleanup
        await handler.shutdown()
    
    @pytest.mark.asyncio
    async def test_batch_handler(self):
        """Test batch message handler."""
        batches = []
        
        async def batch_func(messages: List[Message]):
            batches.append([msg.payload for msg in messages])
        
        handler = BatchMessageHandler(
            batch_func,
            batch_size=3,
            batch_timeout=timedelta(milliseconds=100)
        )
        
        # Process messages
        for i in range(7):
            await handler.handle(Message(payload=f"msg_{i}"))
        
        # Wait for timeout flush
        await asyncio.sleep(0.15)
        
        # Should have 2 full batches and 1 partial
        assert len(batches) == 3
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3
        assert len(batches[2]) == 1
        
        # Cleanup
        await handler.shutdown()
    
    @pytest.mark.asyncio
    async def test_retry_handler(self):
        """Test retrying handler."""
        attempts = 0
        
        async def flaky_handler(message: Message):
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Temporary failure")
            # Success on third attempt
        
        handler = AsyncMessageHandler(flaky_handler)
        retry_handler = RetryingHandler(
            handler,
            RetryPolicy(max_retries=3, initial_delay=timedelta(milliseconds=10))
        )
        
        message = Message(payload="test")
        await retry_handler.handle(message)
        
        assert attempts == 3
        assert message.status == MessageStatus.COMPLETED
        
        # Check stats
        stats = retry_handler.get_stats()
        assert stats['total_retries'] == 2
        assert stats['successful_retries'] == 1
    
    @pytest.mark.asyncio
    async def test_timeout_handler(self):
        """Test timeout handler."""
        async def slow_handler(message: Message):
            await asyncio.sleep(0.2)
        
        handler = AsyncMessageHandler(slow_handler)
        timeout_handler = TimeoutHandler(
            handler,
            timeout=timedelta(milliseconds=100)
        )
        
        message = Message(payload="test")
        
        with pytest.raises(asyncio.TimeoutError):
            await timeout_handler.handle(message)
        
        assert message.status == MessageStatus.FAILED
        assert "Timeout" in message.metadata.last_error
        assert timeout_handler.get_timeout_count() == 1


class TestGameIntegration:
    """Test game-specific message queue integration."""
    
    @pytest.mark.asyncio
    async def test_game_event_queue(self):
        """Test game event queue."""
        queue = GameEventQueue("test_game_events")
        
        # Create event
        event = GameEvent(
            event_type=GameEventType.GAME_STARTED,
            room_id="room123",
            game_id="game456",
            data={"players": 4}
        )
        
        # Publish event
        event_id = await queue.publish(event, MessagePriority.HIGH)
        assert event_id is not None
        
        # Check stats
        stats = queue.get_stats()
        assert stats['events_published'] == 1
        assert stats['by_type'][GameEventType.GAME_STARTED.value] == 1
    
    @pytest.mark.asyncio
    async def test_game_event_handler(self):
        """Test game event handler."""
        handled_events = []
        
        class TestGameHandler(GameEventHandler):
            async def process_event(self, event: GameEvent):
                handled_events.append(event)
        
        handler = TestGameHandler(
            event_types={GameEventType.GAME_STARTED, GameEventType.GAME_ENDED}
        )
        
        # Should handle matching event
        start_event = GameEvent(
            event_type=GameEventType.GAME_STARTED,
            room_id="room123"
        )
        message = Message(payload=start_event)
        assert handler.can_handle(message)
        await handler.handle(message)
        
        # Should not handle non-matching event
        player_event = GameEvent(
            event_type=GameEventType.PLAYER_CONNECTED,
            room_id="room123"
        )
        message2 = Message(payload=player_event)
        assert not handler.can_handle(message2)
        
        assert len(handled_events) == 1
        assert handled_events[0].event_type == GameEventType.GAME_STARTED
    
    @pytest.mark.asyncio
    async def test_game_task_processor(self):
        """Test game task processor."""
        processor = GameTaskProcessor(max_workers=2)
        
        handled_tasks = []
        
        async def custom_handler(data: Dict[str, Any]):
            handled_tasks.append(data)
        
        processor.register_task_handler("custom_task", custom_handler)
        
        # Start processor
        await processor.start()
        
        # Submit tasks
        for i in range(5):
            await processor.submit_task(
                "custom_task",
                {"index": i},
                priority=MessagePriority.NORMAL
            )
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Stop processor
        await processor.stop()
        
        assert len(handled_tasks) == 5
        assert all(task["index"] in range(5) for task in handled_tasks)