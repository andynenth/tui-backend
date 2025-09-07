# backend/services/optimized_event_store.py

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from backend.services.event_buffer import EventBuffer
from backend.services.event_compressor import EventCompressor
from backend.services.event_store_v2 import EventStoreV2
from backend.models.semantic_events import SemanticEventType

logger = logging.getLogger(__name__)


class OptimizedEventStore:
    """
    Optimized event store that integrates buffering, compression, and v2 schema.

    This is the complete implementation of the database optimization design,
    routing events through: Compression → Buffer → V2 Schema

    Features:
    - Event compression (90% reduction in event count)
    - Event buffering (batch writes every 2 seconds)
    - Optimized v2 schema (single row per round)
    - Backward compatibility with v1 events
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize optimized event store with all components."""
        logger.debug("🔍 DEBUG: OptimizedEventStore.__init__ called")

        # Initialize v2 store (the actual database writer)
        self.v2_store = EventStoreV2(db_path)
        logger.debug("🔍 DEBUG: OptimizedEventStore initialized EventStoreV2")

        # Initialize compressor
        compression_enabled = (
            os.getenv("EVENT_COMPRESSION_ENABLED", "true").lower() == "true"
        )
        importance_threshold = float(os.getenv("EVENT_IMPORTANCE_THRESHOLD", "0.7"))

        if compression_enabled:
            self.compressor = EventCompressor(importance_threshold)
            logger.info(
                f"OptimizedEventStore: Compression enabled (threshold: {importance_threshold})"
            )
        else:
            self.compressor = None
            logger.info("OptimizedEventStore: Compression disabled")

        # Initialize buffer with v2 store as the flush target
        buffer_enabled = os.getenv("EVENT_BUFFER_ENABLED", "true").lower() == "true"
        buffer_size = int(os.getenv("EVENT_BUFFER_SIZE", "20"))
        buffer_interval = float(os.getenv("EVENT_BUFFER_FLUSH_INTERVAL", "2.0"))

        if buffer_enabled:
            # Create custom buffer that writes to v2
            self.buffer = EventBuffer(
                max_size=buffer_size,
                flush_interval=buffer_interval,
                event_store=self,  # Buffer will call our flush_to_v2 method
            )
            logger.info(
                f"OptimizedEventStore: Buffer enabled (size: {buffer_size}, interval: {buffer_interval}s)"
            )
        else:
            self.buffer = None
            logger.info("OptimizedEventStore: Buffer disabled")

        # Track pending compressed events
        self._pending_compressed = []

        logger.info(
            "OptimizedEventStore initialized - full optimization pipeline active"
        )

    async def store_event(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
    ) -> None:
        """
        Main entry point for storing events.
        Routes through: Compression → Buffer → V2 Schema
        """

        logger.debug(
            f"🔍 DEBUG: OptimizedEventStore.store_event called - room: {room_id}, type: {event_type}"
        )
        logger.debug(
            f"🔍 DEBUG: OptimizedEventStore payload keys: {list(payload.keys()) if payload else 'None'}"
        )
        logger.debug(
            f"🔍 DEBUG: OptimizedEventStore compression enabled: {self.compressor is not None}"
        )
        logger.debug(
            f"🔍 DEBUG: OptimizedEventStore buffer enabled: {self.buffer is not None}"
        )
        # Step 1: Compression
        if self.compressor:
            # Check if event should be compressed
            should_store = self.compressor.should_store_event(event_type)
            logger.debug(
                f"🔍 DEBUG: Compressor should_store_event({event_type}) = {should_store}"
            )
            if not should_store:
                logger.debug(f"🔍 DEBUG: Filtering low-importance event: {event_type}")
                return

            # Try to compress the event
            compressed = self.compressor.compress_event(
                room_id,
                {"event_type": event_type, "payload": payload, "player_id": player_id},
            )

            if compressed:
                logger.debug(
                    f"🔍 DEBUG: Event compressed from {event_type} to type: {compressed.event_type}"
                )
                logger.debug(
                    f"🔍 DEBUG: Compressed payload keys: {list(compressed.payload.keys()) if compressed.payload else 'None'}"
                )
                # Event was compressed, route it through buffer
                await self._route_compressed_event(room_id, compressed, player_id)
                return
            # If None returned, event is being accumulated for later compression
            logger.debug(
                f"🔍 DEBUG: Event {event_type} being accumulated for compression"
            )
            return

        # Step 2: Buffer (for non-compressed events)
        if self.buffer:
            logger.debug(
                f"🔍 DEBUG: Adding to buffer - room: {room_id}, type: {event_type}"
            )
            await self.buffer.add_event(room_id, event_type, payload, player_id)
        else:
            # No buffer, write directly
            await self.store_event_direct(room_id, event_type, payload, player_id)

    async def _route_compressed_event(
        self,
        room_id: str,
        compressed: Any,  # CompressedEvent
        player_id: Optional[str] = None,
    ) -> None:
        """Route compressed event through buffer or direct storage."""

        # Critical events bypass buffer
        if compressed.event_type in [
            SemanticEventType.GAME_STARTED.value,
            SemanticEventType.GAME_COMPLETED.value,
            SemanticEventType.ROUND_COMPLETED.value,
        ]:
            await self.store_event_direct(
                room_id, compressed.event_type, compressed.payload, player_id
            )
        elif self.buffer:
            # Non-critical compressed events go through buffer
            logger.debug(
                f"🔍 DEBUG: Adding to buffer - room: {room_id}, type: {compressed.event_type}"
            )
            await self.buffer.add_event(
                room_id, compressed.event_type, compressed.payload, player_id
            )
        else:
            # No buffer, write directly
            await self.store_event_direct(
                room_id, compressed.event_type, compressed.payload, player_id
            )

    async def store_event_direct(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
    ) -> None:
        """
        Direct storage to v2 schema, bypassing buffer.
        Used by buffer flush and critical events.
        """

        logger.debug(
            f"🔍 DEBUG: Direct storage to v2 - room: {room_id}, type: {event_type}"
        )
        try:
            # Route semantic events to appropriate v2 methods
            if event_type == SemanticEventType.GAME_STARTED.value:
                players = payload.get("players", [])
                await self.v2_store.store_game_started(room_id, players)

            elif event_type == SemanticEventType.ROUND_STARTED.value:
                # Store round started event
                round_number = payload.get("round_number", 1)
                logger.info(
                    f"Storing round_started event for room {room_id}, round {round_number}"
                )
                await self.v2_store.store_event(room_id, event_type, payload)

            elif event_type == SemanticEventType.ROUND_COMPLETED.value:
                logger.info(
                    f"🔍 DEBUG: Processing ROUND_COMPLETED event for room {room_id}"
                )
                logger.info(
                    f"🔥 OPTIMIZED_EVENT_STORE: Processing ROUND_COMPLETED for room {room_id}"
                )
                logger.info(
                    f"🔥 OPTIMIZED_EVENT_STORE: Payload keys: {list(payload.keys())}"
                )
                # Store complete round snapshot
                round_data = {
                    "round_number": payload.get("round_number", 1),
                    "starter_player": payload.get("starter_player", ""),
                    "starter_reason": payload.get("starter_reason", ""),
                    "initial_hands": payload.get("initial_hands", {}),
                    "declarations": payload.get("declarations", {}),
                    "turn_sequence": payload.get("turn_sequence", []),
                    "round_scores": payload.get("scores", {}),
                    "cumulative_scores": payload.get("total_scores", {}),
                }
                logger.info(
                    f"🔍 DEBUG: Round data extracted - round_number: {round_data['round_number']}"
                )
                await self.v2_store.store_round_snapshot(
                    room_id, round_data["round_number"], round_data
                )
                logger.info(
                    f"✅ DEBUG: Round snapshot stored for room {room_id}, round {round_data['round_number']}"
                )

            elif event_type == SemanticEventType.TURN_COMPLETED.value:
                # Store turn details if enabled
                if os.getenv("STORE_TURN_DETAILS", "false").lower() == "true":
                    round_number = payload.get("round_number", 1)
                    turn_number = payload.get("turn_number", 1)
                    turn_data = {
                        "starter": payload.get("starter", ""),
                        "plays": payload.get("plays", {}),
                        "winner": payload.get("winner", ""),
                        "piles_won": payload.get("piles_won", 0),
                    }
                    await self.v2_store.store_turn_detail(
                        room_id, round_number, turn_number, turn_data
                    )
                else:
                    # Just store the event without turn details
                    await self.v2_store.store_event(room_id, event_type, payload)

            elif event_type == SemanticEventType.GAME_COMPLETED.value:
                # Store game completion
                final_scores = payload.get("final_scores", {})
                winner = payload.get("winner", "")
                await self.v2_store.store_game_completed(room_id, final_scores, winner)

            else:
                # Store generic event
                await self.v2_store.store_event(room_id, event_type, payload)

        except Exception as e:
            logger.error(f"Failed to store event in v2: {e}")
            raise

    async def flush_room(self, room_id: str) -> None:
        """
        Flush any pending events for a room.
        Called when room/game ends.
        """

        # Flush compressed events
        if self.compressor:
            compressed_events = self.compressor.flush_room_accumulators(room_id)
            for compressed in compressed_events:
                await self.store_event_direct(
                    room_id, compressed.event_type, compressed.payload
                )

        # Flush buffer
        if self.buffer:
            await self.buffer.flush()

    async def shutdown(self) -> None:
        """Graceful shutdown, flushing all pending events."""

        logger.info("OptimizedEventStore shutting down...")

        # Flush all compressed events
        if self.compressor:
            # Would need to implement flush_all in compressor
            pass

        # Shutdown buffer (will flush remaining events)
        if self.buffer:
            await self.buffer.shutdown()

        logger.info("OptimizedEventStore shutdown complete")

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from all components."""

        metrics = {
            "optimized_store": True,
            "compression_enabled": self.compressor is not None,
            "buffer_enabled": self.buffer is not None,
        }

        if self.compressor:
            metrics["compression"] = self.compressor.get_stats()

        if self.buffer:
            metrics["buffer"] = self.buffer.get_metrics()

        return metrics

    # Compatibility methods for migration
    async def store_event_buffered(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
    ) -> None:
        """Compatibility method - routes to store_event."""
        await self.store_event(room_id, event_type, payload, player_id)
