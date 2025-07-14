"""
Event Sourcing System for Liap Tui Game
Provides persistent event storage, state reconstruction, and client recovery
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    def __init__(self, db_path: str = "game_events.db"):
        """Initialize EventStore with database connection"""
        self.db_path = db_path
        self.sequence_counter = 0
        self._connection = None
        self._lock = asyncio.Lock()

        # Initialize database
        self._init_database()

        # Load current sequence counter
        self._load_sequence_counter()

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
        # Create a copy to avoid mutation
        new_state = state.copy()

        try:
            if event.event_type == "phase_change":
                new_state["phase"] = event.payload.get("phase", state["phase"])

            elif event.event_type == "player_joined":
                player_name = event.payload.get("player_name")
                if player_name:
                    new_state["players"][player_name] = event.payload.get(
                        "player_data", {}
                    )

            elif event.event_type == "player_declared":
                player_name = event.payload.get("player_name")
                declaration = event.payload.get("declaration")
                if player_name and declaration is not None:
                    if "declarations" not in new_state["game_state"]:
                        new_state["game_state"]["declarations"] = {}
                    new_state["game_state"]["declarations"][player_name] = declaration

            elif event.event_type == "pieces_played":
                player_name = event.payload.get("player_name")
                pieces = event.payload.get("pieces", [])
                if player_name:
                    if "turn_plays" not in new_state["game_state"]:
                        new_state["game_state"]["turn_plays"] = []
                    new_state["game_state"]["turn_plays"].append(
                        {"player": player_name, "pieces": pieces}
                    )

            elif event.event_type == "round_complete":
                new_state["round_number"] = event.payload.get(
                    "round_number", state["round_number"]
                )

            elif event.event_type == "game_started":
                new_state["game_state"] = event.payload.get("initial_state", {})

            # Add more event types as needed

        except Exception as e:
            logger.error(f"Error applying event {event.sequence}: {e}")
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


# Global instance
event_store = EventStore()


# Export for easy importing
__all__ = ["EventStore", "GameEvent", "event_store"]
