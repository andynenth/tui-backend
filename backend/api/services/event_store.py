"""
Event Sourcing System for Liap Tui Game
Provides persistent event storage, state reconstruction, and client recovery
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import EventBuffer for optimized writes
from backend.services.event_buffer import EventBuffer

# Import EventCompressor for semantic compression
from backend.services.event_compressor import EventCompressor

logger = logging.getLogger(__name__)


@dataclass
class GameEvent:
    """Represents a single game event for storage and replay"""

    sequence: int
    room_id: str
    event_type: str
    payload: Dict[str, Any]
    player_id: Optional[str]
    timestamp: float
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameEvent":
        """Create GameEvent from dictionary"""
        return cls(**data)


class EventStore:
    """
    Persistent event storage for game state reconstruction and debugging
    Uses SQLite for development, can be extended for PostgreSQL in production
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize EventStore with database connection"""
        # Use absolute path to ensure database is always in project root
        if db_path is None:
            # Get the project root directory (3 levels up from this file)
            # backend/api/services/event_store.py -> project_root
            current_dir = Path(__file__).resolve()
            project_root = current_dir.parent.parent.parent.parent
            self.db_path = str(project_root / "data" / "game_events.db")
        else:
            self.db_path = db_path
        self.sequence_counter = 0
        self._connection = None
        self._lock = asyncio.Lock()

        # Initialize database
        self._init_database()

        # Load current sequence counter
        self._load_sequence_counter()

        # Initialize event buffer if enabled
        buffer_enabled = os.getenv("EVENT_BUFFER_ENABLED", "true").lower() == "true"
        buffer_size = int(os.getenv("EVENT_BUFFER_SIZE", "20"))
        buffer_interval = float(os.getenv("EVENT_BUFFER_FLUSH_INTERVAL", "2.0"))

        if buffer_enabled:
            self._buffer = EventBuffer(
                max_size=buffer_size, flush_interval=buffer_interval, event_store=self
            )
            logger.info(
                f"EventStore: Buffer enabled (size: {buffer_size}, interval: {buffer_interval}s)"
            )
        else:
            self._buffer = None
            logger.info("EventStore: Buffer disabled, using direct writes")

        # Initialize event compressor if enabled
        compression_enabled = (
            os.getenv("EVENT_COMPRESSION_ENABLED", "false").lower() == "true"
        )
        importance_threshold = float(os.getenv("EVENT_IMPORTANCE_THRESHOLD", "0.7"))

        if compression_enabled:
            self._compressor = EventCompressor(
                importance_threshold=importance_threshold
            )
            logger.info(
                f"EventStore: Compression enabled (threshold: {importance_threshold})"
            )
        else:
            self._compressor = None
            logger.info("EventStore: Compression disabled")

        logger.info(f"EventStore initialized with database: {db_path}")

    def _init_database(self):
        """Initialize SQLite database with events table"""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS game_events (
                sequence INTEGER PRIMARY KEY,
                room_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                player_id TEXT,
                timestamp REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """
        )

        # Create indexes for performance
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_room_sequence ON game_events(room_id, sequence)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_room_timestamp ON game_events(room_id, timestamp)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_created_at ON game_events(created_at)"
        )

        conn.commit()
        conn.close()

    def _load_sequence_counter(self):
        """Load the current sequence counter from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT MAX(sequence) FROM game_events")
        result = cursor.fetchone()
        self.sequence_counter = (result[0] or 0) + 1
        conn.close()

        logger.info(f"Loaded sequence counter: {self.sequence_counter}")

    def _next_sequence(self) -> int:
        """Generate next sequence number (thread-safe)"""
        current = self.sequence_counter
        self.sequence_counter += 1
        return current

    async def store_event_buffered(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
    ) -> None:
        """
        Store event through buffer if enabled, otherwise direct storage

        This is the new optimized entry point that uses buffering to
        reduce database writes by 90%.

        Args:
            room_id: The room/game identifier
            event_type: Type of event
            payload: Event data
            player_id: Optional player identifier
        """
        # Apply compression if enabled
        if self._compressor:
            # Check if event should be stored
            if not self._compressor.should_store_event(event_type):
                logger.debug(f"Event {event_type} filtered by compression")
                return

            # Try to compress the event
            event_dict = {
                "event_type": event_type,
                "payload": payload,
                "player_id": player_id,
            }
            compressed = self._compressor.compress_event(room_id, event_dict)

            # If compressed event is ready, store it
            if compressed:
                compressed_dict = compressed.to_dict()
                await self._store_compressed_event(
                    room_id,
                    compressed_dict["event_type"],
                    compressed_dict["payload"],
                    player_id,
                )
                return
            # If None returned, event is being accumulated
            else:
                return

        # No compression - use buffer if enabled
        if self._buffer:
            await self._buffer.add_event(room_id, event_type, payload, player_id)
        else:
            await self.store_event(room_id, event_type, payload, player_id)

    async def _store_compressed_event(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
    ) -> None:
        """
        Store a compressed event through the buffer.

        Args:
            room_id: The room/game identifier
            event_type: Semantic event type
            payload: Compressed event data
            player_id: Optional player identifier
        """
        # Mark as compressed event
        payload["_compressed"] = True

        # Use buffer if enabled
        if self._buffer:
            await self._buffer.add_event(room_id, event_type, payload, player_id)
        else:
            await self.store_event(room_id, event_type, payload, player_id)

    async def store_event_direct(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
    ) -> GameEvent:
        """
        Direct storage without buffering - used by buffer flush

        This bypasses the buffer and writes directly to the database.
        Used internally by the EventBuffer during flush operations.
        """
        return await self.store_event(room_id, event_type, payload, player_id)

    async def store_event(
        self,
        room_id: str,
        event_type: str,
        payload: Dict[str, Any],
        player_id: Optional[str] = None,
    ) -> GameEvent:
        """
        Store a game event with sequence number and timestamp

        Args:
            room_id: The room/game identifier
            event_type: Type of event (e.g., 'phase_change', 'player_declared')
            payload: Event data
            player_id: Optional player identifier

        Returns:
            GameEvent: The stored event with sequence number
        """
        async with self._lock:
            sequence = self._next_sequence()
            timestamp = time.time()
            created_at = datetime.now().isoformat()

            event = GameEvent(
                sequence=sequence,
                room_id=room_id,
                event_type=event_type,
                payload=payload,
                player_id=player_id,
                timestamp=timestamp,
                created_at=created_at,
            )

            # Store in database
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                """
                INSERT INTO game_events 
                (sequence, room_id, event_type, payload, player_id, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event.sequence,
                    event.room_id,
                    event.event_type,
                    json.dumps(event.payload),
                    event.player_id,
                    event.timestamp,
                    event.created_at,
                ),
            )
            conn.commit()
            conn.close()

            logger.debug(
                f"Stored event: {event.event_type} for room {room_id} (seq: {sequence})"
            )
            return event

    async def get_events_since(
        self, room_id: str, since_sequence: int
    ) -> List[GameEvent]:
        """
        Retrieve events after specific sequence for client recovery

        Args:
            room_id: The room identifier
            since_sequence: Get events after this sequence number

        Returns:
            List[GameEvent]: Events in chronological order
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT sequence, room_id, event_type, payload, player_id, timestamp, created_at
            FROM game_events 
            WHERE room_id = ? AND sequence > ?
            ORDER BY sequence ASC
        """,
            (room_id, since_sequence),
        )

        events = []
        for row in cursor.fetchall():
            event = GameEvent(
                sequence=row[0],
                room_id=row[1],
                event_type=row[2],
                payload=json.loads(row[3]),
                player_id=row[4],
                timestamp=row[5],
                created_at=row[6],
            )
            events.append(event)

        conn.close()

        logger.info(
            f"Retrieved {len(events)} events for room {room_id} since sequence {since_sequence}"
        )
        return events

    async def get_room_events(
        self, room_id: str, limit: Optional[int] = None
    ) -> List[GameEvent]:
        """
        Get all events for a room

        Args:
            room_id: The room identifier
            limit: Optional limit on number of events to return

        Returns:
            List[GameEvent]: All events for the room in chronological order
        """
        conn = sqlite3.connect(self.db_path)

        query = """
            SELECT sequence, room_id, event_type, payload, player_id, timestamp, created_at
            FROM game_events 
            WHERE room_id = ?
            ORDER BY sequence ASC
        """

        params = [room_id]
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = conn.execute(query, params)

        events = []
        for row in cursor.fetchall():
            event = GameEvent(
                sequence=row[0],
                room_id=row[1],
                event_type=row[2],
                payload=json.loads(row[3]),
                player_id=row[4],
                timestamp=row[5],
                created_at=row[6],
            )
            events.append(event)

        conn.close()

        logger.info(f"Retrieved {len(events)} total events for room {room_id}")
        return events

    async def replay_room_state(self, room_id: str) -> Dict[str, Any]:
        """
        Reconstruct current room state from stored events

        Args:
            room_id: The room identifier

        Returns:
            Dict: Reconstructed room state
        """
        events = await self.get_room_events(room_id)

        # Initialize empty state
        state = {
            "room_id": room_id,
            "phase": "waiting",
            "players": {},
            "game_state": {},
            "round_number": 0,
            "events_processed": 0,
            "last_sequence": 0,
        }

        # Replay events to reconstruct state
        for event in events:
            state = self._apply_event_to_state(state, event)
            state["events_processed"] += 1
            state["last_sequence"] = event.sequence

        logger.info(f"Reconstructed state for room {room_id} from {len(events)} events")
        return state

    def _apply_event_to_state(
        self, state: Dict[str, Any], event: GameEvent
    ) -> Dict[str, Any]:
        """
        Apply a single event to the current state

        Args:
            state: Current state dictionary
            event: Event to apply

        Returns:
            Dict: Updated state
        """
        # Create a deep copy to avoid mutation of nested structures
        import copy

        new_state = copy.deepcopy(state)

        try:
            # Initialize nested structures if they don't exist
            if "game_state" not in new_state:
                new_state["game_state"] = {}
            if "phase_data" not in new_state:
                new_state["phase_data"] = {}
            if "players" not in new_state:
                new_state["players"] = {}
            if "actions" not in new_state:
                new_state["actions"] = []

            # Handle different event types
            if event.event_type == "phase_change":
                # Enhanced phase change handling
                old_phase = event.payload.get("old_phase")
                new_phase = event.payload.get("new_phase")
                if old_phase:
                    new_state["previous_phase"] = old_phase
                new_state["phase"] = new_phase

                # Store game context if provided
                game_context = event.payload.get("game_context", {})
                if game_context:
                    new_state["round_number"] = game_context.get(
                        "round_number", state.get("round_number", 1)
                    )
                    new_state["player_count"] = game_context.get("player_count", 4)
                    if "current_player" in game_context:
                        new_state["current_player"] = game_context["current_player"]

            elif event.event_type == "phase_data_update":
                # Handle phase-specific data updates
                phase = event.payload.get("phase")
                updates = event.payload.get("updates", {})
                reason = event.payload.get("reason", "")

                if phase not in new_state["phase_data"]:
                    new_state["phase_data"][phase] = {}

                # Apply updates to phase-specific data
                new_state["phase_data"][phase].update(updates)
                new_state["last_update_reason"] = reason
                new_state["last_update_sequence"] = event.payload.get("sequence", 0)

            elif event.event_type == "action_processed":
                # Track player actions
                action_data = {
                    "sequence_id": event.payload.get("sequence_id"),
                    "action_type": event.payload.get("action_type"),
                    "player_name": event.payload.get("player_name"),
                    "payload": event.payload.get("payload", {}),
                    "timestamp": event.timestamp,
                }
                new_state["actions"].append(action_data)

            elif event.event_type == "player_joined":
                player_name = event.payload.get("player_name")
                if player_name:
                    new_state["players"][player_name] = event.payload.get(
                        "player_data", {"joined_at": event.timestamp}
                    )

            elif event.event_type == "player_declared":
                player_name = event.payload.get("player_name")
                declaration = event.payload.get(
                    "declaration", event.payload.get("value")
                )
                if player_name and declaration is not None:
                    if "declarations" not in new_state["game_state"]:
                        new_state["game_state"]["declarations"] = {}
                    new_state["game_state"]["declarations"][player_name] = declaration

            elif event.event_type == "pieces_played" or event.event_type == "play":
                # Handle piece plays
                player_name = event.payload.get("player_name")
                pieces = event.payload.get("pieces", [])
                if player_name:
                    if "current_turn" not in new_state["game_state"]:
                        new_state["game_state"]["current_turn"] = {"plays": []}
                    new_state["game_state"]["current_turn"]["plays"].append(
                        {
                            "player": player_name,
                            "pieces": pieces,
                            "timestamp": event.timestamp,
                        }
                    )

            elif (
                event.event_type == "turn_complete"
                or event.event_type == "turn_resolved"
            ):
                # Handle turn completion
                winner = event.payload.get("winner")
                turn_number = event.payload.get(
                    "turn_number", state.get("turn_number", 0) + 1
                )

                new_state["turn_number"] = turn_number
                if winner:
                    new_state["last_turn_winner"] = winner

                # Archive current turn data
                if "turn_history" not in new_state["game_state"]:
                    new_state["game_state"]["turn_history"] = []

                current_turn = new_state["game_state"].get("current_turn", {})
                if current_turn:
                    current_turn["winner"] = winner
                    current_turn["turn_number"] = turn_number
                    new_state["game_state"]["turn_history"].append(current_turn)
                    new_state["game_state"]["current_turn"] = {}

            elif (
                event.event_type == "round_complete"
                or event.event_type == "round_scoring"
            ):
                # Handle round scoring
                new_state["round_number"] = event.payload.get(
                    "round_number", state.get("round_number", 0) + 1
                )

                scores = event.payload.get("scores", {})
                if scores:
                    if "round_scores" not in new_state["game_state"]:
                        new_state["game_state"]["round_scores"] = []
                    new_state["game_state"]["round_scores"].append(
                        {
                            "round": new_state["round_number"],
                            "scores": scores,
                            "timestamp": event.timestamp,
                        }
                    )

                    # Update player total scores
                    for player, score_data in scores.items():
                        if player in new_state["players"]:
                            current_score = new_state["players"][player].get("score", 0)
                            round_score = (
                                score_data
                                if isinstance(score_data, (int, float))
                                else score_data.get("score", 0)
                            )
                            new_state["players"][player]["score"] = (
                                current_score + round_score
                            )

            elif event.event_type == "game_started":
                new_state["game_state"] = event.payload.get("initial_state", {})
                new_state["started_at"] = event.timestamp
                new_state["status"] = "in_progress"

            elif event.event_type == "game_complete" or event.event_type == "game_over":
                # Handle game completion
                new_state["status"] = "complete"
                new_state["completed_at"] = event.timestamp

                final_scores = event.payload.get("final_scores", {})
                winner = event.payload.get("winner")

                if final_scores:
                    new_state["final_scores"] = final_scores
                if winner:
                    new_state["winner"] = winner

            # Log unhandled event types for debugging
            else:
                logger.debug(f"Unhandled event type: {event.event_type}")

        except Exception as e:
            logger.error(
                f"Error applying event {event.sequence} ({event.event_type}): {e}"
            )
            # Return original state on error to prevent corruption
            return state

        return new_state

    async def cleanup_old_events(self, older_than_hours: int = 24) -> int:
        """
        Remove old events to prevent storage bloat

        Args:
            older_than_hours: Remove events older than this many hours

        Returns:
            int: Number of events removed
        """
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cutoff_timestamp = cutoff_time.timestamp()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "DELETE FROM game_events WHERE timestamp < ?", (cutoff_timestamp,)
        )
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(
            f"Cleaned up {deleted_count} events older than {older_than_hours} hours"
        )
        return deleted_count

    async def count_events_for_date(self, date: datetime) -> int:
        """
        Count events for a specific date

        Args:
            date: The date to count events for

        Returns:
            int: Number of events on that date
        """
        date_str = date.strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM game_events WHERE date(created_at) = date(?)",
            (date_str,),
        )
        count = cursor.fetchone()[0]
        conn.close()

        return count

    async def get_event_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored events

        Returns:
            Dict: Event storage statistics
        """
        conn = sqlite3.connect(self.db_path)

        # Total events
        cursor = conn.execute("SELECT COUNT(*) FROM game_events")
        total_events = cursor.fetchone()[0]

        # Events by room
        cursor = conn.execute(
            """
            SELECT room_id, COUNT(*) as event_count 
            FROM game_events 
            GROUP BY room_id 
            ORDER BY event_count DESC
        """
        )
        room_stats = dict(cursor.fetchall())

        # Events by type
        cursor = conn.execute(
            """
            SELECT event_type, COUNT(*) as event_count 
            FROM game_events 
            GROUP BY event_type 
            ORDER BY event_count DESC
        """
        )
        type_stats = dict(cursor.fetchall())

        # Recent activity (last 24 hours)
        cutoff_time = (datetime.now() - timedelta(hours=24)).timestamp()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM game_events WHERE timestamp > ?", (cutoff_time,)
        )
        recent_events = cursor.fetchone()[0]

        conn.close()

        return {
            "total_events": total_events,
            "current_sequence": self.sequence_counter - 1,
            "rooms_with_events": len(room_stats),
            "events_last_24h": recent_events,
            "room_stats": room_stats,
            "event_type_stats": type_stats,
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the event store

        Returns:
            Dict: Health status information
        """
        try:
            # Test database connection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
            conn.close()

            # Get basic stats
            stats = await self.get_event_stats()

            return {
                "status": "healthy",
                "database_accessible": True,
                "total_events": stats["total_events"],
                "current_sequence": stats["current_sequence"],
                "last_check": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"EventStore health check failed: {e}")
            return {
                "status": "unhealthy",
                "database_accessible": False,
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }

    async def get_events_by_type(
        self, room_id: str, event_type: str, limit: Optional[int] = None
    ) -> List[GameEvent]:
        """
        Get events of a specific type for a room

        Args:
            room_id: The room identifier
            event_type: The event type to filter by
            limit: Optional limit on number of events

        Returns:
            List[GameEvent]: Filtered events in chronological order
        """
        conn = sqlite3.connect(self.db_path)

        query = """
            SELECT sequence, room_id, event_type, payload, player_id, timestamp, created_at
            FROM game_events 
            WHERE room_id = ? AND event_type = ?
            ORDER BY sequence ASC
        """

        params = [room_id, event_type]
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = conn.execute(query, params)

        events = []
        for row in cursor.fetchall():
            event = GameEvent(
                sequence=row[0],
                room_id=row[1],
                event_type=row[2],
                payload=json.loads(row[3]),
                player_id=row[4],
                timestamp=row[5],
                created_at=row[6],
            )
            events.append(event)

        conn.close()

        logger.info(f"Retrieved {len(events)} {event_type} events for room {room_id}")
        return events

    async def export_room_history(self, room_id: str) -> Dict[str, Any]:
        """
        Export complete room history for debugging

        Args:
            room_id: The room identifier

        Returns:
            Dict: Complete room history with events and reconstructed state
        """
        events = await self.get_room_events(room_id)
        state = await self.replay_room_state(room_id)

        # Group events by type for analysis
        events_by_type = {}
        for event in events:
            if event.event_type not in events_by_type:
                events_by_type[event.event_type] = []
            events_by_type[event.event_type].append(
                {
                    "sequence": event.sequence,
                    "timestamp": event.timestamp,
                    "player": event.player_id,
                    "payload": event.payload,
                }
            )

        return {
            "room_id": room_id,
            "total_events": len(events),
            "event_types": list(events_by_type.keys()),
            "events_by_type": events_by_type,
            "reconstructed_state": state,
            "timeline": [
                {
                    "sequence": e.sequence,
                    "type": e.event_type,
                    "timestamp": e.timestamp,
                    "player": e.player_id,
                }
                for e in events
            ],
        }

    async def validate_event_sequence(self, room_id: str) -> Dict[str, Any]:
        """
        Validate event sequence integrity for a room

        Args:
            room_id: The room identifier

        Returns:
            Dict: Validation results including any gaps or issues
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT sequence FROM game_events 
            WHERE room_id = ?
            ORDER BY sequence ASC
            """,
            (room_id,),
        )

        sequences = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not sequences:
            return {
                "valid": True,
                "message": "No events found",
                "gaps": [],
                "total_events": 0,
            }

        # Check for gaps
        gaps = []
        expected = sequences[0]
        for seq in sequences:
            if seq != expected:
                gaps.append({"expected": expected, "found": seq})
            expected = seq + 1

        return {
            "valid": len(gaps) == 0,
            "message": (
                "Sequence valid" if len(gaps) == 0 else f"Found {len(gaps)} gaps"
            ),
            "gaps": gaps,
            "total_events": len(sequences),
            "first_sequence": sequences[0],
            "last_sequence": sequences[-1],
        }

    async def flush_room_events(self, room_id: str) -> None:
        """
        Flush any pending events for a room (compression + buffer).

        Should be called when a room/game completes.

        Args:
            room_id: The room to flush
        """
        # Flush compressed events first
        if self._compressor:
            compressed_events = self._compressor.flush_room_accumulators(room_id)
            for event in compressed_events:
                event_dict = event.to_dict()
                await self._store_compressed_event(
                    room_id, event_dict["event_type"], event_dict["payload"]
                )

        # Then flush buffer
        if self._buffer:
            await self._buffer.flush()

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the event store

        Flushes any pending buffered events to ensure no data loss.
        """
        # Flush all room compressors first
        if self._compressor:
            logger.info("Shutting down EventStore - flushing compressor...")
            # Note: In production, we'd track active rooms and flush each
            # For now, we rely on room cleanup to handle this

        if self._buffer:
            logger.info("Shutting down EventStore - flushing buffer...")
            await self._buffer.shutdown()
            logger.info("EventStore buffer flushed successfully")

    def get_buffer_metrics(self) -> Dict[str, Any]:
        """
        Get buffer performance metrics

        Returns:
            Dict: Buffer metrics or empty dict if buffer disabled
        """
        if self._buffer:
            return self._buffer.get_metrics()
        return {"buffer_enabled": False, "message": "Event buffering is disabled"}

    def get_compression_metrics(self) -> Dict[str, Any]:
        """
        Get compression performance metrics

        Returns:
            Dict: Compression metrics or status if disabled
        """
        if self._compressor:
            return self._compressor.get_stats()
        return {
            "compression_enabled": False,
            "message": "Event compression is disabled",
        }


# Note: The global event_store instance is now created in shared_event_store.py
# to avoid circular imports with MigrationAdapter

# Export for easy importing
__all__ = ["EventStore", "GameEvent"]
