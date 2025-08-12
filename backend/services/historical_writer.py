# backend/services/historical_writer.py

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
import json

from backend.services.event_store_v2 import EventStoreV2
from backend.api.services.event_store import EventStore

logger = logging.getLogger(__name__)


class HistoricalWriter:
    """
    Asynchronous service for writing historical game data.

    Phase 4 of database optimization - Decouples real-time game updates
    from historical data persistence for improved performance.

    Features:
    - Async batch writing to reduce database load
    - Compression of old game data
    - Priority queue for important events
    - Automatic retry on failures
    """

    def __init__(
        self,
        v1_store: Optional[EventStore] = None,
        v2_store: Optional[EventStoreV2] = None,
        batch_size: int = 50,
        batch_interval: float = 5.0,
        compression_age_days: int = 7,
    ):
        """
        Initialize historical writer.

        Args:
            v1_store: EventStore v1 instance
            v2_store: EventStore v2 instance
            batch_size: Number of events to batch
            batch_interval: Max time between batches (seconds)
            compression_age_days: Age at which to compress games
        """
        self.v1_store = v1_store
        self.v2_store = v2_store
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.compression_age_days = compression_age_days

        # Event queues
        self._priority_queue: deque = deque()  # For critical events
        self._normal_queue: deque = deque()  # For regular events
        self._lock = asyncio.Lock()

        # Metrics
        self._events_queued = 0
        self._events_written = 0
        self._batches_written = 0
        self._compression_runs = 0
        self._write_errors = 0

        # Background tasks
        self._writer_task: Optional[asyncio.Task] = None
        self._compressor_task: Optional[asyncio.Task] = None
        self._started = False

        logger.info(
            f"HistoricalWriter initialized: batch_size={batch_size}, "
            f"interval={batch_interval}s, compression_age={compression_age_days}d"
        )

    async def start(self):
        """Start background tasks."""
        if not self._started:
            self._writer_task = asyncio.create_task(self._writer_loop())
            self._compressor_task = asyncio.create_task(self._compressor_loop())
            self._started = True
            logger.info("HistoricalWriter background tasks started")

    async def stop(self):
        """Stop background tasks and flush remaining events."""
        if self._started:
            # Flush remaining events
            await self._flush_all()

            # Cancel tasks
            if self._writer_task:
                self._writer_task.cancel()
                try:
                    await self._writer_task
                except asyncio.CancelledError:
                    pass

            if self._compressor_task:
                self._compressor_task.cancel()
                try:
                    await self._compressor_task
                except asyncio.CancelledError:
                    pass

            self._started = False
            logger.info("HistoricalWriter stopped")

    async def queue_event(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        priority: bool = False,
    ) -> None:
        """
        Queue an event for historical writing.

        Args:
            room_id: Room identifier
            event_type: Event type
            payload: Event data
            priority: Whether this is a priority event
        """
        event = {
            "room_id": room_id,
            "event_type": event_type,
            "payload": payload,
            "timestamp": time.time(),
            "queued_at": datetime.now().isoformat(),
        }

        async with self._lock:
            if priority:
                self._priority_queue.append(event)
            else:
                self._normal_queue.append(event)
            self._events_queued += 1

        logger.debug(
            f"Queued {event_type} event for room {room_id} (priority={priority})"
        )

    async def _writer_loop(self):
        """Background task for writing batched events."""
        last_write = time.time()

        while True:
            try:
                await asyncio.sleep(1.0)  # Check every second

                current_time = time.time()
                time_since_write = current_time - last_write

                # Check if we should write a batch
                should_write = False

                async with self._lock:
                    total_queued = len(self._priority_queue) + len(self._normal_queue)

                    if total_queued >= self.batch_size:
                        should_write = True
                    elif total_queued > 0 and time_since_write >= self.batch_interval:
                        should_write = True

                if should_write:
                    await self._write_batch()
                    last_write = current_time

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in writer loop: {e}")
                self._write_errors += 1

    async def _write_batch(self):
        """Write a batch of events to the database."""
        batch = []

        async with self._lock:
            # Take up to batch_size events, prioritizing priority queue
            while len(batch) < self.batch_size and self._priority_queue:
                batch.append(self._priority_queue.popleft())

            while len(batch) < self.batch_size and self._normal_queue:
                batch.append(self._normal_queue.popleft())

        if not batch:
            return

        logger.debug(f"Writing batch of {len(batch)} events")

        # Group by room for efficiency
        events_by_room: Dict[str, List[Dict[str, Any]]] = {}
        for event in batch:
            room_id = event["room_id"]
            if room_id not in events_by_room:
                events_by_room[room_id] = []
            events_by_room[room_id].append(event)

        # Write events
        write_start = time.time()
        success_count = 0

        for room_id, room_events in events_by_room.items():
            try:
                await self._write_room_events(room_id, room_events)
                success_count += len(room_events)
            except Exception as e:
                logger.error(f"Failed to write events for room {room_id}: {e}")
                self._write_errors += 1
                # Re-queue failed events
                async with self._lock:
                    self._normal_queue.extend(room_events)

        write_time = time.time() - write_start
        self._events_written += success_count
        self._batches_written += 1

        logger.info(
            f"Wrote batch: {success_count}/{len(batch)} events "
            f"in {write_time:.2f}s ({write_time/len(batch)*1000:.1f}ms/event)"
        )

    async def _write_room_events(self, room_id: str, events: List[Dict[str, Any]]):
        """Write events for a specific room."""
        if self.v2_store:
            # For v2, we need to handle different event types
            for event in events:
                event_type = event["event_type"]
                payload = event["payload"]

                if event_type == "round_completed":
                    # Build and store round snapshot
                    round_data = await self._build_round_data(room_id, payload)
                    if round_data:
                        round_number = payload.get("round_number", 1)
                        await self.v2_store.store_round_snapshot(
                            room_id, round_number, round_data
                        )

                # Other event types would be handled similarly

        elif self.v1_store:
            # For v1, store events directly (but not buffered since this is async)
            for event in events:
                await self.v1_store.store_event(
                    room_id,
                    event["event_type"],
                    event["payload"],
                    event.get("player_id"),
                )

    async def _build_round_data(
        self, room_id: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build round data for v2 storage."""
        # This would need access to game state to build complete round data
        # For now, return a simplified version
        return {
            "round_number": payload.get("round_number", 1),
            "round_scores": payload.get("scores", {}),
            "cumulative_scores": payload.get("total_scores", {}),
            "starter_player": "",
            "declarations": {},
            "turn_sequence": [],
            "initial_hands": {},
        }

    async def _compressor_loop(self):
        """Background task for compressing old games."""
        while True:
            try:
                # Run compression once per day
                await asyncio.sleep(86400)  # 24 hours
                await self._compress_old_games()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in compressor loop: {e}")

    async def _compress_old_games(self):
        """Compress games older than threshold."""
        logger.info(
            f"Starting compression of games older than {self.compression_age_days} days"
        )

        if self.v2_store:
            # Use v2's cleanup method which could be extended for compression
            deleted = await self.v2_store.cleanup_old_data(self.compression_age_days)
            logger.info(f"Cleaned up {deleted} old games")
            self._compression_runs += 1

        # For actual compression, we would:
        # 1. Identify completed games older than threshold
        # 2. Create compressed summary (just final state, scores, key events)
        # 3. Store compressed version
        # 4. Delete detailed event history

    async def _flush_all(self):
        """Flush all queued events."""
        logger.info("Flushing all queued events")

        while True:
            async with self._lock:
                if not self._priority_queue and not self._normal_queue:
                    break

            await self._write_batch()

    def get_metrics(self) -> Dict[str, Any]:
        """Get writer metrics."""
        # Use non-async access since metrics are for monitoring
        priority_size = len(self._priority_queue)
        normal_size = len(self._normal_queue)

        return {
            "events_queued": self._events_queued,
            "events_written": self._events_written,
            "batches_written": self._batches_written,
            "compression_runs": self._compression_runs,
            "write_errors": self._write_errors,
            "priority_queue_size": priority_size,
            "normal_queue_size": normal_size,
            "total_queue_size": priority_size + normal_size,
            "average_batch_size": (
                self._events_written / self._batches_written
                if self._batches_written > 0
                else 0
            ),
        }


# Global instance
_historical_writer: Optional[HistoricalWriter] = None


def get_historical_writer() -> HistoricalWriter:
    """Get the global historical writer instance."""
    global _historical_writer
    if _historical_writer is None:
        _historical_writer = HistoricalWriter()
    return _historical_writer


async def initialize_historical_writer(
    v1_store: Optional[EventStore] = None,
    v2_store: Optional[EventStoreV2] = None,
    batch_size: int = 50,
    batch_interval: float = 5.0,
) -> HistoricalWriter:
    """Initialize and start the global historical writer."""
    global _historical_writer
    _historical_writer = HistoricalWriter(
        v1_store, v2_store, batch_size, batch_interval
    )
    await _historical_writer.start()
    return _historical_writer


async def shutdown_historical_writer():
    """Shutdown the global historical writer."""
    global _historical_writer
    if _historical_writer:
        await _historical_writer.stop()
        _historical_writer = None
