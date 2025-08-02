#!/usr/bin/env python3
"""
Test script for message queue system
Tests that messages are properly queued for disconnected players
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.websocket.message_queue import MessageQueueManager, PlayerQueue, QueuedMessage
from datetime import datetime


class TestMessageQueue:
    """Test message queue functionality"""

    @staticmethod
    async def test_queue_creation():
        """Test creating a message queue"""
        manager = MessageQueueManager()

        await manager.create_queue("room1", "Alice")

        # Verify queue was created
        key = "room1:Alice"
        assert key in manager.queues
        assert manager.queues[key].player_name == "Alice"
        assert manager.queues[key].room_id == "room1"

        print("✅ Queue creation test passed")

    @staticmethod
    async def test_message_queuing():
        """Test queuing messages"""
        manager = MessageQueueManager()

        await manager.create_queue("room1", "Bob")

        # Queue some messages
        await manager.queue_message("room1", "Bob", "phase_change", {"phase": "turn"})
        await manager.queue_message(
            "room1", "Bob", "play", {"player": "Alice", "pieces": [1, 2]}
        )
        await manager.queue_message(
            "room1", "Bob", "turn_resolved", {"winner": "Charlie"}
        )

        # Get queued messages
        messages = await manager.get_queued_messages("room1", "Bob")

        assert len(messages) == 3
        assert messages[0]["event_type"] == "phase_change"
        assert messages[1]["event_type"] == "play"
        assert messages[2]["event_type"] == "turn_resolved"

        # Verify critical messages are marked
        assert messages[0]["is_critical"] == True  # phase_change is critical
        assert messages[1]["is_critical"] == False  # play is not critical
        assert messages[2]["is_critical"] == True  # turn_resolved is critical

        print("✅ Message queuing test passed")

    @staticmethod
    async def test_queue_overflow():
        """Test queue overflow handling"""
        queue = PlayerQueue("David", "room1", max_size=5)

        # Add non-critical messages
        for i in range(10):
            queue.add_message("play", {"index": i}, is_critical=False)

        # Should only keep last 5
        assert len(queue.messages) == 5
        assert queue.messages[0].data["index"] == 5
        assert queue.messages[-1].data["index"] == 9

        # Add critical messages
        queue.add_message("game_ended", {"winners": ["Alice"]}, is_critical=True)
        queue.add_message("score_update", {"scores": {}}, is_critical=True)

        # Should prioritize critical messages
        assert len(queue.messages) == 5
        critical_count = len([m for m in queue.messages if m.is_critical])
        assert critical_count == 2

        print("✅ Queue overflow test passed")

    @staticmethod
    async def test_get_messages_since():
        """Test getting messages since a sequence number"""
        queue = PlayerQueue("Eve", "room1")

        # Add messages with known sequences
        for i in range(1, 6):
            queue.last_sequence = i
            queue.messages.append(
                QueuedMessage(
                    event_type=f"event_{i}",
                    data={"seq": i},
                    timestamp=datetime.now(),
                    sequence=i,
                    is_critical=False,
                )
            )

        # Get messages since sequence 3
        recent_messages = queue.get_messages_since(3)

        assert len(recent_messages) == 2
        assert recent_messages[0].sequence == 4
        assert recent_messages[1].sequence == 5

        print("✅ Get messages since sequence test passed")

    @staticmethod
    async def test_clear_queue():
        """Test clearing a queue"""
        manager = MessageQueueManager()

        await manager.create_queue("room2", "Frank")
        await manager.queue_message("room2", "Frank", "test", {"data": "test"})

        # Verify message was queued
        messages = await manager.get_queued_messages("room2", "Frank")
        assert len(messages) == 1

        # Clear the queue
        await manager.clear_queue("room2", "Frank")

        # Verify queue was cleared
        assert "room2:Frank" not in manager.queues

        print("✅ Clear queue test passed")

    @staticmethod
    async def test_room_cleanup():
        """Test cleaning up all queues for a room"""
        manager = MessageQueueManager()

        # Create queues for multiple players in same room
        await manager.create_queue("room3", "Player1")
        await manager.create_queue("room3", "Player2")
        await manager.create_queue("room4", "Player3")

        # Clean up room3
        await manager.cleanup_room_queues("room3")

        # Verify room3 queues are gone but room4 remains
        assert "room3:Player1" not in manager.queues
        assert "room3:Player2" not in manager.queues
        assert "room4:Player3" in manager.queues

        print("✅ Room cleanup test passed")


async def run_all_tests():
    """Run all message queue tests"""
    print("🧪 Running Message Queue Tests\n")

    await TestMessageQueue.test_queue_creation()
    await TestMessageQueue.test_message_queuing()
    await TestMessageQueue.test_queue_overflow()
    await TestMessageQueue.test_get_messages_since()
    await TestMessageQueue.test_clear_queue()
    await TestMessageQueue.test_room_cleanup()

    print("\n✅ All message queue tests passed!")
    print("✅ Critical messages are properly prioritized")
    print("✅ Queue overflow is handled correctly")
    print("✅ Reconnection message delivery ready")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
