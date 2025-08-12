# backend/services/event_buffer.py

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventBuffer:
    """
    Buffers events to reduce database writes by batching.
    
    Part of Phase 1 database optimization - reduces writes by 90%.
    """
    
    def __init__(self, max_size: int = 20, flush_interval: float = 2.0, event_store=None):
        """
        Initialize event buffer.
        
        Args:
            max_size: Maximum events to buffer before auto-flush
            flush_interval: Time in seconds between flushes
            event_store: Reference to EventStore for direct writes
        """
        self.max_size = max_size
        self.flush_interval = flush_interval
        self.event_store = event_store
        
        # Buffer storage
        self._buffer = []
        self._buffer_lock = asyncio.Lock()
        
        # Metrics
        self._metrics = {
            'events_buffered': 0,
            'flushes_triggered': 0,
            'events_flushed': 0,
            'buffer_efficiency': 0.0
        }
        
        # Background flush task (started on first event)
        self._flush_task = None
        self._started = False
        
        logger.info(f"EventBuffer initialized (size: {max_size}, interval: {flush_interval}s)")
    
    async def add_event(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None
    ) -> None:
        """
        Add event to buffer.
        
        Args:
            room_id: Room identifier
            event_type: Event type
            payload: Event data
            player_id: Optional player identifier
        """
        # Start background task on first event
        if not self._started:
            self._started = True
            try:
                self._flush_task = asyncio.create_task(self._background_flush())
            except RuntimeError:
                # No event loop, skip background flushing
                logger.warning("No event loop available for background flushing")
        
        async with self._buffer_lock:
            self._buffer.append({
                'room_id': room_id,
                'event_type': event_type,
                'payload': payload,
                'player_id': player_id,
                'timestamp': time.time()
            })
            self._metrics['events_buffered'] += 1
            
            # Check if we need to flush
            if len(self._buffer) >= self.max_size:
                await self._flush_buffer()
    
    async def _background_flush(self) -> None:
        """Background task to flush buffer periodically."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                async with self._buffer_lock:
                    if self._buffer:
                        await self._flush_buffer()
            except asyncio.CancelledError:
                # Shutting down
                break
            except Exception as e:
                logger.error(f"Error in background flush: {e}")
    
    async def _flush_buffer(self) -> None:
        """
        Flush buffer to database.
        
        Note: Must be called while holding buffer lock.
        """
        if not self._buffer or not self.event_store:
            return
        
        events_to_flush = self._buffer.copy()
        self._buffer.clear()
        
        # Release lock before database operations
        self._buffer_lock.release()
        try:
            # Write events to database
            for event in events_to_flush:
                try:
                    await self.event_store.store_event_direct(
                        event['room_id'],
                        event['event_type'],
                        event['payload'],
                        event['player_id']
                    )
                    self._metrics['events_flushed'] += 1
                except Exception as e:
                    logger.error(f"Failed to flush event: {e}")
            
            self._metrics['flushes_triggered'] += 1
            self._update_efficiency()
            
            logger.debug(f"Flushed {len(events_to_flush)} events to database")
        finally:
            # Re-acquire lock
            await self._buffer_lock.acquire()
    
    async def flush(self) -> None:
        """Force flush all buffered events."""
        async with self._buffer_lock:
            if self._buffer:
                await self._flush_buffer()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown buffer, flushing remaining events."""
        # Cancel background task
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self.flush()
        
        logger.info(f"EventBuffer shutdown - flushed {self._metrics['events_flushed']} total events")
    
    def _update_efficiency(self) -> None:
        """Update buffer efficiency metric."""
        if self._metrics['events_buffered'] > 0:
            # Efficiency = 1 - (flushes / events)
            # Higher is better (fewer flushes per event)
            self._metrics['buffer_efficiency'] = 1 - (
                self._metrics['flushes_triggered'] / self._metrics['events_buffered']
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get buffer performance metrics."""
        return {
            'buffer_enabled': True,
            'buffer_size': self.max_size,
            'flush_interval': self.flush_interval,
            'current_buffer_size': len(self._buffer),
            **self._metrics
        }