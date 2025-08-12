# backend/tests/test_event_buffer.py

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch

from backend.services.event_buffer import EventBuffer, BufferedEvent


class TestEventBuffer:
    """Test cases for EventBuffer functionality"""

    @pytest.fixture
    def mock_event_store(self):
        """Create a mock event store with async methods"""
        mock = Mock()
        mock.store_event_direct = AsyncMock()
        return mock

    @pytest.fixture
    async def event_buffer(self, mock_event_store):
        """Create an EventBuffer instance for testing"""
        buffer = EventBuffer(
            max_size=5,  # Small size for testing
            flush_interval=0.5,  # Short interval for testing
            event_store=mock_event_store
        )
        yield buffer
        # Clean up
        await buffer.shutdown()

    @pytest.mark.asyncio
    async def test_buffer_initialization(self, event_buffer):
        """Test buffer initializes with correct parameters"""
        assert event_buffer.max_size == 5
        assert event_buffer.flush_interval == 0.5
        assert event_buffer.total_events_buffered == 0
        assert event_buffer.total_flushes == 0
        assert len(event_buffer._buffer) == 0

    @pytest.mark.asyncio
    async def test_add_non_critical_event(self, event_buffer):
        """Test adding a non-critical event to buffer"""
        await event_buffer.add_event(
            room_id="TEST123",
            event_type="phase_change",
            payload={"phase": "turn"},
            player_id="player1"
        )
        
        assert len(event_buffer._buffer) == 1
        assert event_buffer.total_events_buffered == 1
        assert event_buffer.event_store.store_event_direct.call_count == 0

    @pytest.mark.asyncio
    async def test_critical_event_immediate_flush(self, event_buffer):
        """Test critical events bypass buffer and flush immediately"""
        await event_buffer.add_event(
            room_id="TEST123",
            event_type="game_over",  # Critical event
            payload={"winner": "player1"},
            player_id="player1"
        )
        
        # Should not be in buffer
        assert len(event_buffer._buffer) == 0
        # Should be flushed immediately
        assert event_buffer.event_store.store_event_direct.call_count == 1
        
        # Verify call arguments
        call_args = event_buffer.event_store.store_event_direct.call_args
        assert call_args[1]["room_id"] == "TEST123"
        assert call_args[1]["event_type"] == "game_over"

    @pytest.mark.asyncio
    async def test_auto_flush_on_size_limit(self, event_buffer):
        """Test buffer auto-flushes when size limit reached"""
        # Add events up to max size
        for i in range(5):
            await event_buffer.add_event(
                room_id="TEST123",
                event_type="phase_change",
                payload={"event": i},
                player_id=f"player{i}"
            )
        
        # Buffer should be empty after auto-flush
        assert len(event_buffer._buffer) == 0
        assert event_buffer.total_flushes == 1
        # Should have flushed all 5 events
        assert event_buffer.event_store.store_event_direct.call_count == 5

    @pytest.mark.asyncio
    async def test_auto_flush_timer(self, event_buffer):
        """Test buffer auto-flushes based on timer"""
        # Add one event
        await event_buffer.add_event(
            room_id="TEST123",
            event_type="phase_change",
            payload={"test": "timer"},
            player_id="player1"
        )
        
        assert len(event_buffer._buffer) == 1
        
        # Wait for timer to trigger (0.5s + small buffer)
        await asyncio.sleep(0.7)
        
        # Buffer should be flushed
        assert len(event_buffer._buffer) == 0
        assert event_buffer.total_flushes == 1
        assert event_buffer.event_store.store_event_direct.call_count == 1

    @pytest.mark.asyncio
    async def test_manual_flush(self, event_buffer):
        """Test manual flush operation"""
        # Add some events
        for i in range(3):
            await event_buffer.add_event(
                room_id="TEST123",
                event_type="phase_change",
                payload={"event": i},
                player_id="player1"
            )
        
        assert len(event_buffer._buffer) == 3
        
        # Manual flush
        await event_buffer.flush()
        
        assert len(event_buffer._buffer) == 0
        assert event_buffer.total_flushes == 1
        assert event_buffer.event_store.store_event_direct.call_count == 3

    @pytest.mark.asyncio
    async def test_flush_error_handling(self, event_buffer):
        """Test buffer handles flush errors gracefully"""
        # Make store_event_direct raise an error
        event_buffer.event_store.store_event_direct.side_effect = Exception("Storage error")
        
        # Add events
        for i in range(3):
            await event_buffer.add_event(
                room_id="TEST123",
                event_type="phase_change",
                payload={"event": i},
                player_id="player1"
            )
        
        # Try to flush
        await event_buffer.flush()
        
        # Events should be retained in buffer due to error
        assert len(event_buffer._buffer) == 3
        assert event_buffer.total_flushes == 0

    @pytest.mark.asyncio
    async def test_shutdown(self, event_buffer):
        """Test graceful shutdown flushes pending events"""
        # Add some events
        for i in range(3):
            await event_buffer.add_event(
                room_id="TEST123",
                event_type="phase_change",
                payload={"event": i},
                player_id="player1"
            )
        
        assert len(event_buffer._buffer) == 3
        
        # Shutdown
        await event_buffer.shutdown()
        
        # Should flush before shutdown
        assert len(event_buffer._buffer) == 0
        assert event_buffer._shutdown == True
        assert event_buffer.event_store.store_event_direct.call_count == 3

    @pytest.mark.asyncio
    async def test_get_metrics(self, event_buffer):
        """Test metrics reporting"""
        # Add some events
        for i in range(3):
            await event_buffer.add_event(
                room_id="TEST123",
                event_type="phase_change",
                payload={"event": i},
                player_id="player1"
            )
        
        metrics = event_buffer.get_metrics()
        
        assert metrics["buffer_size"] == 3
        assert metrics["total_buffered"] == 3
        assert metrics["total_flushes"] == 0
        assert "time_since_flush" in metrics
        assert metrics["events_per_flush"] == 0  # No flushes yet
        
        # Flush and check metrics again
        await event_buffer.flush()
        metrics = event_buffer.get_metrics()
        
        assert metrics["buffer_size"] == 0
        assert metrics["total_buffered"] == 3
        assert metrics["total_flushes"] == 1
        assert metrics["events_per_flush"] == 3.0

    @pytest.mark.asyncio
    async def test_thread_safety(self, event_buffer):
        """Test concurrent event additions are thread-safe"""
        # Create multiple concurrent tasks adding events
        async def add_events(player_id):
            for i in range(10):
                await event_buffer.add_event(
                    room_id="TEST123",
                    event_type="phase_change",
                    payload={"player": player_id, "event": i},
                    player_id=player_id
                )
        
        # Run 5 concurrent tasks
        tasks = [add_events(f"player{i}") for i in range(5)]
        await asyncio.gather(*tasks)
        
        # Should have processed all events (50 total)
        assert event_buffer.total_events_buffered == 50
        
        # Force a flush to count stored events
        await event_buffer.flush()
        
        # All events should be stored (auto-flushes + final flush)
        total_calls = event_buffer.event_store.store_event_direct.call_count
        assert total_calls == 50

    @pytest.mark.asyncio
    async def test_critical_events_list(self):
        """Test all critical event types bypass buffer"""
        mock_store = Mock()
        mock_store.store_event_direct = AsyncMock()
        
        buffer = EventBuffer(event_store=mock_store)
        
        critical_events = [
            'game_started', 'game_over', 'round_complete', 
            'player_disconnected', 'game_recovered'
        ]
        
        for event_type in critical_events:
            await buffer.add_event(
                room_id="TEST123",
                event_type=event_type,
                payload={"test": True},
                player_id="player1"
            )
        
        # All should bypass buffer
        assert len(buffer._buffer) == 0
        assert mock_store.store_event_direct.call_count == len(critical_events)
        
        await buffer.shutdown()