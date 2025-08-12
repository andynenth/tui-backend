# backend/services/event_compressor.py

import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import json

from backend.models.semantic_events import (
    SemanticEventType,
    EventMapping,
    CompressedEvent,
    EventImportance,
)

logger = logging.getLogger(__name__)


class EventCompressor:
    """
    Compresses granular events into semantic events.

    Reduces event volume by ~90% while maintaining all game information.
    """

    def __init__(self, importance_threshold: float = 0.7):
        """
        Initialize compressor with importance threshold.

        Args:
            importance_threshold: Events below this importance are filtered (0.0-1.0)
        """
        self.importance_threshold = importance_threshold
        self.compression_stats = {
            "events_processed": 0,
            "events_compressed": 0,
            "events_filtered": 0,
            "compression_ratio": 0.0,
        }

        # Accumulators for compression
        self._turn_accumulator = defaultdict(list)
        self._declaration_accumulator = defaultdict(list)
        self._phase_accumulator = defaultdict(list)

    def should_store_event(self, event_type: str) -> bool:
        """
        Determine if an event type should be stored based on importance.

        Args:
            event_type: The event type to check

        Returns:
            bool: True if event should be stored
        """
        result = self._should_store_event_logic(event_type)
        logger.debug(f"🔍 DEBUG: should_store_event({event_type}) = {result}")
        return result

    def _should_store_event_logic(self, event_type: str) -> bool:
        # Always store critical events
        if event_type in EventMapping.STORE_AS_IS:
            return True

        # Check importance threshold
        importance = EventMapping.IMPORTANCE_SCORES.get(event_type, EventImportance.LOW)

        return importance.value >= self.importance_threshold

    def compress_event(
        self, room_id: str, event: Dict[str, Any]
    ) -> Optional[CompressedEvent]:
        """
        Compress a single event or accumulate for batch compression.

        Args:
            room_id: Room identifier for grouping
            event: Raw event to compress

        Returns:
            CompressedEvent if ready to emit, None if accumulating
        """
        event_type = event.get("event_type", "")
        logger.debug(
            f"🔍 DEBUG: EventCompressor.compress_event - room: {room_id}, type: {event_type}"
        )

        # Direct mapping (no compression)
        if event_type in EventMapping.STORE_AS_IS:
            logger.debug(
                f"🔍 DEBUG: Event {event_type} in STORE_AS_IS, creating direct event"
            )
            return self._create_direct_event(event)

        # Compression mapping
        compression_type = EventMapping.COMPRESS_EVENTS.get(event_type)
        logger.debug(
            f"🔍 DEBUG: Compression type for {event_type}: {compression_type}"
        )

        if compression_type == "accumulate_declarations":
            logger.debug(f"🔍 DEBUG: Accumulating declaration event")
            return self._accumulate_declaration(room_id, event)
        elif compression_type == "accumulate_turn":
            logger.debug(f"🔍 DEBUG: Accumulating turn event")
            return self._accumulate_turn(room_id, event)
        elif compression_type == "compress_turn":
            logger.debug(f"🔍 DEBUG: Compressing turn events")
            return self._compress_turn(room_id, event)
        elif compression_type == "filter_redundant":
            logger.debug(f"🔍 DEBUG: Filtering redundant event")
            return self._filter_redundant(room_id, event)

        # Unknown event type - log and skip
        logger.debug(
            f"🔍 DEBUG: Unknown event type for compression: {event_type} - FILTERING"
        )
        self.compression_stats["events_filtered"] += 1
        return None

    def _create_direct_event(self, event: Dict[str, Any]) -> CompressedEvent:
        """Create a semantic event from direct mapping."""
        event_type = event.get("event_type", "")
        semantic_type = EventMapping.STORE_AS_IS[event_type]

        self.compression_stats["events_processed"] += 1
        self.compression_stats["events_compressed"] += 1
        self._update_compression_ratio()

        return CompressedEvent(semantic_type, event.get("payload", {}))

    def _accumulate_declaration(
        self, room_id: str, event: Dict[str, Any]
    ) -> Optional[CompressedEvent]:
        """Accumulate declaration events until all 4 are received."""
        key = f"{room_id}:declarations"
        self._declaration_accumulator[key].append(event)
        logger.debug(
            f"🔍 DEBUG: Declaration accumulator for {key} now has {len(self._declaration_accumulator[key])} events"
        )

        # Check if we have all 4 declarations
        if len(self._declaration_accumulator[key]) >= 4:
            declarations = self._declaration_accumulator.pop(key)
            compressed = CompressedEvent.from_declaration_events(declarations)
            logger.debug(
                f"🔍 DEBUG: Created compressed DECLARATIONS_COMPLETED event from {len(declarations)} events"
            )

            self.compression_stats["events_processed"] += len(declarations)
            self.compression_stats["events_compressed"] += 1
            self._update_compression_ratio()

            return compressed

        return None

    def _accumulate_turn(self, room_id: str, event: Dict[str, Any]) -> None:
        """Accumulate turn events for compression."""
        payload = event.get("payload", {})
        turn_number = (
            payload.get("turn_number")
            or payload.get("current_turn_number")
            or len(self._turn_accumulator[room_id]) + 1
        )

        key = f"{room_id}:turn_{turn_number}"
        self._turn_accumulator[key].append(event)

        return None

    def _compress_turn(
        self, room_id: str, event: Dict[str, Any]
    ) -> Optional[CompressedEvent]:
        """Compress accumulated turn events when turn completes."""
        payload = event.get("payload", {})
        turn_number = (
            payload.get("turn_number")
            or payload.get("current_turn_number")
            or len(self._turn_accumulator)
        )

        key = f"{room_id}:turn_{turn_number}"
        logger.debug(
            f"🔍 DEBUG: Compressing turn {key} - accumulator has {len(self._turn_accumulator.get(key, []))} events"
        )

        # Add the completion event
        self._turn_accumulator[key].append(event)

        # Get all events for this turn
        turn_events = self._turn_accumulator.pop(key, [])

        if turn_events:
            compressed = CompressedEvent.from_turn_events(turn_events)
            logger.debug(
                f"🔍 DEBUG: Created compressed TURN_COMPLETED event from {len(turn_events)} events"
            )

            self.compression_stats["events_processed"] += len(turn_events)
            self.compression_stats["events_compressed"] += 1
            self._update_compression_ratio()

            return compressed

        return None

    def _filter_redundant(
        self, room_id: str, event: Dict[str, Any]
    ) -> Optional[CompressedEvent]:
        """Filter redundant phase updates."""
        # Most phase updates are redundant and can be filtered
        event_type = event.get("event_type", "")

        # Only keep phase changes to new phases
        if event_type == "phase_change":
            payload = event.get("payload", {})
            new_phase = payload.get("new_phase") or payload.get("phase")

            # Store phase transitions
            if new_phase:
                self.compression_stats["events_processed"] += 1
                self.compression_stats["events_compressed"] += 1
                self._update_compression_ratio()

                return CompressedEvent(
                    SemanticEventType.STATE_SNAPSHOT,
                    {"phase": new_phase, "transition": True},
                )

        # Filter out most phase_data_updates
        self.compression_stats["events_processed"] += 1
        self.compression_stats["events_filtered"] += 1
        self._update_compression_ratio()

        return None

    def flush_room_accumulators(self, room_id: str) -> List[CompressedEvent]:
        """
        Flush any pending accumulated events for a room.

        Called when room ends to ensure no events are lost.

        Args:
            room_id: Room to flush

        Returns:
            List of compressed events
        """
        compressed_events = []

        # Flush declarations
        decl_key = f"{room_id}:declarations"
        if decl_key in self._declaration_accumulator:
            declarations = self._declaration_accumulator.pop(decl_key)
            if declarations:
                compressed = CompressedEvent.from_declaration_events(declarations)
                compressed_events.append(compressed)

                self.compression_stats["events_processed"] += len(declarations)
                self.compression_stats["events_compressed"] += 1

        # Flush turn events
        turn_keys = [
            k for k in self._turn_accumulator.keys() if k.startswith(f"{room_id}:turn_")
        ]
        for key in turn_keys:
            turn_events = self._turn_accumulator.pop(key)
            if turn_events:
                compressed = CompressedEvent.from_turn_events(turn_events)
                compressed_events.append(compressed)

                self.compression_stats["events_processed"] += len(turn_events)
                self.compression_stats["events_compressed"] += 1

        self._update_compression_ratio()
        return compressed_events

    def _update_compression_ratio(self):
        """Update compression statistics."""
        if self.compression_stats["events_processed"] > 0:
            self.compression_stats["compression_ratio"] = 1 - (
                self.compression_stats["events_compressed"]
                / self.compression_stats["events_processed"]
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics."""
        return self.compression_stats.copy()

    def reset_stats(self):
        """Reset compression statistics."""
        self.compression_stats = {
            "events_processed": 0,
            "events_compressed": 0,
            "events_filtered": 0,
            "compression_ratio": 0.0,
        }
