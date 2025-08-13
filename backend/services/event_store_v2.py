# backend/services/event_store_v2.py

import json
import sqlite3
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from backend.models.semantic_events import SemanticEventType

logger = logging.getLogger(__name__)


class EventStoreV2:
    """
    Optimized event store using new schema design.

    Phase 3 of database optimization - Uses separate tables for:
    - Minimal event tracking (game_events_v2)
    - Game summaries (game_summaries)
    - Round snapshots (round_snapshots)
    - Turn details (turn_details)
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize EventStore v2 with optimized schema."""
        if db_path is None:
            current_dir = Path(__file__).resolve()
            project_root = current_dir.parent.parent.parent
            self.db_path = str(project_root / "game_events.db")
        else:
            self.db_path = db_path

        self._ensure_schema()
        logger.info(f"EventStoreV2 initialized with database: {self.db_path}")

    def _ensure_schema(self) -> None:
        """Ensure v2 schema exists by running migrations."""
        from .db_migrator import DatabaseMigrator

        migrator = DatabaseMigrator(self.db_path)
        current_version = migrator.get_current_version()

        if current_version < 2:
            logger.info(f"Running database migrations to v2 for {self.db_path}...")
            applied = migrator.run_migrations()
            logger.info(f"Applied {applied} migrations")

    async def store_game_started(
        self, room_id: str, players: List[Dict[str, Any]]
    ) -> None:
        """Store game start in summary table."""
        logger.debug(
            f"🔍 DEBUG: EventStoreV2.store_game_started - room: {room_id}, players: {len(players) if players else 0}"
        )
        conn = sqlite3.connect(self.db_path)
        try:
            # Create game summary entry
            conn.execute(
                """
                INSERT OR REPLACE INTO game_summaries 
                (room_id, players, started_at, total_rounds, total_events)
                VALUES (?, ?, ?, 0, 0)
            """,
                (room_id, json.dumps(players), time.time()),
            )

            # Also store minimal event
            conn.execute(
                """
                INSERT INTO game_events_v2
                (room_id, event_type, timestamp, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (
                    room_id,
                    SemanticEventType.GAME_STARTED.value,
                    time.time(),
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            logger.info(f"🔍 DEBUG: Game started stored in v2 for room {room_id}")
        finally:
            conn.close()

    async def store_round_snapshot(
        self, room_id: str, round_number: int, round_data: Dict[str, Any]
    ) -> None:
        """Store complete round snapshot."""
        logger.info(
            f"🔍 DEBUG: EventStoreV2.store_round_snapshot called - room: {room_id}, round: {round_number}"
        )
        logger.info(f"🔍 DEBUG: Round data keys: {list(round_data.keys())}")
        conn = sqlite3.connect(self.db_path)
        try:
            # Extract data
            starter = round_data.get("starter_player", "")
            starter_reason = round_data.get("starter_reason", "default")
            hands = round_data.get("initial_hands", {})
            declarations = round_data.get("declarations", {})
            turns = round_data.get("turn_sequence", [])
            scores = round_data.get("round_scores", {})
            cumulative = round_data.get("cumulative_scores", {})

            # Store round snapshot
            conn.execute(
                """
                INSERT OR REPLACE INTO round_snapshots
                (room_id, round_number, starter_player, starter_reason,
                 initial_hands, declarations, turn_sequence, round_scores,
                 cumulative_scores, created_at, total_turns)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    room_id,
                    round_number,
                    starter,
                    starter_reason,
                    json.dumps(hands),
                    json.dumps(declarations),
                    json.dumps(turns),
                    json.dumps(scores),
                    json.dumps(cumulative),
                    datetime.now().isoformat(),
                    len(turns),
                ),
            )

            # Store individual turns if detailed tracking enabled
            if turns and self._should_store_turn_details():
                for turn in turns:
                    turn_num = turn.get("turn_number", 0)
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO turn_details
                        (room_id, round_number, turn_number, starter,
                         plays, winner, piles_won, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            room_id,
                            round_number,
                            turn_num,
                            turn.get("starter", ""),
                            json.dumps(turn.get("plays", {})),
                            turn.get("winner", ""),
                            turn.get("piles_won", 0),
                            datetime.now().isoformat(),
                        ),
                    )

            # Update game summary
            conn.execute(
                """
                UPDATE game_summaries
                SET total_rounds = ?,
                    total_events = total_events + ?
                WHERE room_id = ?
            """,
                (round_number, 1, room_id),
            )

            conn.commit()
            logger.info(
                f"✅ DEBUG: Round snapshot successfully stored in database - room: {room_id}, round: {round_number}"
            )
        finally:
            conn.close()

    async def store_game_completed(
        self, room_id: str, final_scores: Dict[str, int], winner: str
    ) -> None:
        """Store game completion."""
        logger.debug(
            f"🔍 DEBUG: EventStoreV2.store_game_completed - room: {room_id}, winner: {winner}"
        )
        conn = sqlite3.connect(self.db_path)
        try:
            # Get game start time
            cursor = conn.execute(
                "SELECT started_at FROM game_summaries WHERE room_id = ?", (room_id,)
            )
            row = cursor.fetchone()
            started_at = row[0] if row else time.time()

            # Calculate duration
            completed_at = time.time()
            duration = int(completed_at - started_at)

            # Update game summary
            conn.execute(
                """
                UPDATE game_summaries
                SET completed_at = ?,
                    final_scores = ?,
                    winner = ?,
                    duration_seconds = ?
                WHERE room_id = ?
            """,
                (completed_at, json.dumps(final_scores), winner, duration, room_id),
            )

            # Store completion event
            conn.execute(
                """
                INSERT INTO game_events_v2
                (room_id, event_type, timestamp, created_at)
                VALUES (?, ?, ?, ?)
            """,
                (
                    room_id,
                    SemanticEventType.GAME_COMPLETED.value,
                    completed_at,
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            logger.info(f"Game completed for room {room_id}, winner: {winner}")
        finally:
            conn.close()

    async def get_game_summary(self, room_id: str) -> Optional[Dict[str, Any]]:
        """Get game summary for quick overview."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT room_id, players, total_rounds, final_scores,
                       winner, started_at, completed_at, duration_seconds
                FROM game_summaries
                WHERE room_id = ?
            """,
                (room_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "room_id": row[0],
                "players": json.loads(row[1]) if row[1] else [],
                "total_rounds": row[2],
                "final_scores": json.loads(row[3]) if row[3] else {},
                "winner": row[4],
                "started_at": row[5],
                "completed_at": row[6],
                "duration_seconds": row[7],
                "is_active": row[6] is None,
            }
        finally:
            conn.close()

    async def get_round_snapshots(
        self, room_id: str, round_numbers: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Get round snapshots for play history."""
        conn = sqlite3.connect(self.db_path)
        try:
            if round_numbers:
                placeholders = ",".join("?" * len(round_numbers))
                query = f"""
                    SELECT * FROM round_snapshots
                    WHERE room_id = ? AND round_number IN ({placeholders})
                    ORDER BY round_number
                """
                params = [room_id] + round_numbers
            else:
                query = """
                    SELECT * FROM round_snapshots
                    WHERE room_id = ?
                    ORDER BY round_number
                """
                params = [room_id]

            cursor = conn.execute(query, params)

            rounds = []
            for row in cursor.fetchall():
                rounds.append(
                    {
                        "round_number": row[1],
                        "starter_player": row[2],
                        "starter_reason": row[3],
                        "initial_hands": json.loads(row[4]),
                        "declarations": json.loads(row[5]),
                        "turn_sequence": json.loads(row[6]),
                        "round_scores": json.loads(row[7]),
                        "cumulative_scores": json.loads(row[8]),
                        "created_at": row[9],
                        "total_turns": (
                            row[11] if len(row) > 11 else len(json.loads(row[6]))
                        ),
                    }
                )

            return rounds
        finally:
            conn.close()

    async def store_event(
        self, room_id: str, event_type: str, payload: Dict[str, Any]
    ) -> None:
        """
        Store a generic event in the v2 events table.

        Args:
            room_id: Room identifier
            event_type: Event type
            payload: Event data
        """
        logger.debug(
            f"🔍 DEBUG: EventStoreV2.store_event - room: {room_id}, type: {event_type}"
        )
        logger.debug(
            f"🔍 DEBUG: EventStoreV2 payload keys: {list(payload.keys()) if payload else 'None'}"
        )

        conn = sqlite3.connect(self.db_path)
        try:
            # Extract round number from payload if available
            round_number = payload.get("round_number") or payload.get("round") or None

            conn.execute(
                """
                INSERT INTO game_events_v2 (room_id, event_type, round_number, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    room_id,
                    event_type,
                    round_number,
                    time.time(),
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            logger.debug(
                f"🔍 DEBUG: Successfully stored {event_type} event for room {room_id} in v2"
            )

        except Exception as e:
            logger.error(f"Failed to store event in v2: {e}")
            raise
        finally:
            conn.close()

    async def get_active_games(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of active games."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                """
                SELECT room_id, players, total_rounds, started_at
                FROM game_summaries
                WHERE completed_at IS NULL
                ORDER BY started_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            games = []
            for row in cursor.fetchall():
                games.append(
                    {
                        "room_id": row[0],
                        "players": json.loads(row[1]),
                        "total_rounds": row[2],
                        "started_at": row[3],
                    }
                )

            return games
        finally:
            conn.close()

    async def get_player_statistics(self, player_name: str) -> Dict[str, Any]:
        """Get player statistics using optimized queries."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Use the player_stats view
            cursor = conn.execute(
                """
                SELECT games_played, games_won, avg_score
                FROM player_stats
                WHERE player_name = ?
            """,
                (player_name,),
            )

            row = cursor.fetchone()
            if not row:
                return {
                    "player_name": player_name,
                    "games_played": 0,
                    "games_won": 0,
                    "win_rate": 0.0,
                    "avg_score": 0.0,
                }

            games_played = row[0]
            games_won = row[1]
            avg_score = row[2] or 0.0

            return {
                "player_name": player_name,
                "games_played": games_played,
                "games_won": games_won,
                "win_rate": games_won / games_played if games_played > 0 else 0.0,
                "avg_score": avg_score,
            }
        finally:
            conn.close()

    def _should_store_turn_details(self) -> bool:
        """Check if we should store detailed turn information."""
        import os

        return os.getenv("STORE_TURN_DETAILS", "false").lower() == "true"

    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old completed games."""
        conn = sqlite3.connect(self.db_path)
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)

            # Get rooms to delete
            cursor = conn.execute(
                """
                SELECT room_id FROM game_summaries
                WHERE completed_at < ? AND completed_at IS NOT NULL
            """,
                (cutoff_time,),
            )

            rooms_to_delete = [row[0] for row in cursor.fetchall()]

            if not rooms_to_delete:
                return 0

            # Delete from all tables
            placeholders = ",".join("?" * len(rooms_to_delete))

            conn.execute(
                f"DELETE FROM turn_details WHERE room_id IN ({placeholders})",
                rooms_to_delete,
            )
            conn.execute(
                f"DELETE FROM round_snapshots WHERE room_id IN ({placeholders})",
                rooms_to_delete,
            )
            conn.execute(
                f"DELETE FROM game_events_v2 WHERE room_id IN ({placeholders})",
                rooms_to_delete,
            )
            conn.execute(
                f"DELETE FROM game_summaries WHERE room_id IN ({placeholders})",
                rooms_to_delete,
            )

            conn.commit()

            logger.info(f"Cleaned up {len(rooms_to_delete)} old games")
            return len(rooms_to_delete)
        finally:
            conn.close()
