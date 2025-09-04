# backend/services/debug_db_service.py
"""
Debug database service that provides read methods for the debug endpoints.
This replaces the missing read methods from the old EventStore API.
"""

import json
import sqlite3
import logging
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GameEvent:
    """Represents a single game event for compatibility"""
    sequence: int
    room_id: str
    event_type: str
    payload: Dict[str, Any]
    player_id: Optional[str]
    timestamp: float
    created_at: str


class DebugDatabaseService:
    """Service for debug endpoints to read from the V2 database schema."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path."""
        if db_path is None:
            # Check environment variable first
            env_db_path = os.getenv('DATABASE_PATH')
            if env_db_path:
                self.db_path = env_db_path
            else:
                # Fall back to default
                current_dir = Path(__file__).resolve()
                project_root = current_dir.parent.parent.parent
                self.db_path = str(project_root / "data" / "game_events.db")
        else:
            self.db_path = db_path
        
        logger.info(f"DebugDatabaseService initialized with db: {self.db_path}")
    
    async def get_room_events(self, room_id: str, limit: Optional[int] = None) -> List[GameEvent]:
        """Get all events for a room."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT COALESCE(id, 0) as sequence, room_id, event_type, 
                       round_number, timestamp, created_at, payload, player_id
                FROM game_events_v2
                WHERE room_id = ?
                ORDER BY id ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = conn.execute(query, (room_id,))
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                # Parse payload JSON if available
                payload = {}
                if 'payload' in row.keys() and row['payload']:
                    try:
                        payload = json.loads(row['payload'])
                    except:
                        payload = {"round_number": row['round_number']} if row['round_number'] else {}
                elif row['round_number']:
                    payload = {"round_number": row['round_number']}
                
                events.append(GameEvent(
                    sequence=row['sequence'] if 'sequence' in row.keys() else 0,
                    room_id=row['room_id'],
                    event_type=row['event_type'],
                    payload=payload,
                    player_id=row['player_id'] if 'player_id' in row.keys() else None,
                    timestamp=row['timestamp'],
                    created_at=row['created_at']
                ))
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting room events: {e}")
            return []
    
    async def get_events_by_type(self, room_id: str, event_type: str, limit: Optional[int] = None) -> List[GameEvent]:
        """Get events of a specific type for a room."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT COALESCE(id, 0) as sequence, room_id, event_type, 
                       round_number, timestamp, created_at, payload, player_id
                FROM game_events_v2
                WHERE room_id = ? AND event_type = ?
                ORDER BY id ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = conn.execute(query, (room_id, event_type))
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                # Parse payload JSON if available
                payload = {}
                if 'payload' in row.keys() and row['payload']:
                    try:
                        payload = json.loads(row['payload'])
                    except:
                        payload = {"round_number": row['round_number']} if row['round_number'] else {}
                elif row['round_number']:
                    payload = {"round_number": row['round_number']}
                
                events.append(GameEvent(
                    sequence=row['sequence'] if 'sequence' in row.keys() else 0,
                    room_id=row['room_id'],
                    event_type=row['event_type'],
                    payload=payload,
                    player_id=row['player_id'] if 'player_id' in row.keys() else None,
                    timestamp=row['timestamp'],
                    created_at=row['created_at']
                ))
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events by type: {e}")
            return []
    
    async def get_events_since(self, room_id: str, sequence: int) -> List[GameEvent]:
        """Get events since a specific sequence number."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT event_sequence as sequence, room_id, event_type, 
                       round_number, timestamp, created_at
                FROM game_events_v2
                WHERE room_id = ? AND event_sequence > ?
                ORDER BY id ASC
            """
            
            cursor = conn.execute(query, (room_id, sequence))
            rows = cursor.fetchall()
            conn.close()
            
            events = []
            for row in rows:
                # v2 schema doesn't have payload/player_id, create minimal payload
                payload = {"round_number": row['round_number']} if row['round_number'] else {}
                
                events.append(GameEvent(
                    sequence=row['sequence'],
                    room_id=row['room_id'],
                    event_type=row['event_type'],
                    payload=payload,
                    player_id=None,  # Not available in v2 schema
                    timestamp=row['timestamp'],
                    created_at=row['created_at']
                ))
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events since sequence: {e}")
            return []
    
    async def replay_room_state(self, room_id: str) -> Dict[str, Any]:
        """Replay and reconstruct room state from events."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Get game summary
            cursor = conn.execute("""
                SELECT * FROM game_summaries WHERE room_id = ?
            """, (room_id,))
            summary = cursor.fetchone()
            
            if not summary:
                conn.close()
                return {}
            
            # Get latest round snapshot
            cursor = conn.execute("""
                SELECT * FROM round_snapshots 
                WHERE room_id = ? 
                ORDER BY round_number DESC 
                LIMIT 1
            """, (room_id,))
            latest_round = cursor.fetchone()
            
            conn.close()
            
            # Build state
            state = {
                "room_id": room_id,
                "status": summary['game_status'],
                "total_rounds": summary['total_rounds'],
                "current_round": summary['current_round'],
                "started_at": summary['started_at'],
                "completed_at": summary['completed_at']
            }
            
            if latest_round:
                state["latest_round"] = {
                    "round_number": latest_round['round_number'],
                    "cumulative_scores": json.loads(latest_round['cumulative_scores'] or '{}'),
                    "has_winner": latest_round['has_winner'],
                    "winning_player": latest_round['winning_player']
                }
            
            return state
            
        except Exception as e:
            logger.error(f"Error replaying room state: {e}")
            return {}
    
    async def validate_event_sequence(self, room_id: str) -> Dict[str, Any]:
        """Validate event sequence integrity."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            cursor = conn.execute("""
                SELECT event_sequence, event_type, timestamp 
                FROM game_events_v2 
                WHERE room_id = ? 
                ORDER BY event_sequence ASC
            """, (room_id,))
            
            events = cursor.fetchall()
            conn.close()
            
            if not events:
                return {"valid": True, "total_events": 0, "gaps": []}
            
            # Check for sequence gaps
            gaps = []
            expected = events[0][0]  # First sequence number
            
            for seq, event_type, timestamp in events:
                if seq != expected:
                    gaps.append({
                        "expected": expected,
                        "actual": seq,
                        "gap_size": seq - expected
                    })
                expected = seq + 1
            
            return {
                "valid": len(gaps) == 0,
                "total_events": len(events),
                "first_sequence": events[0][0],
                "last_sequence": events[-1][0],
                "gaps": gaps,
                "gap_count": len(gaps)
            }
            
        except Exception as e:
            logger.error(f"Error validating event sequence: {e}")
            return {"valid": False, "error": str(e)}
    
    async def get_event_stats(self) -> Dict[str, Any]:
        """Get overall event store statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Total events
            cursor = conn.execute("SELECT COUNT(*) FROM game_events_v2")
            total_events = cursor.fetchone()[0]
            
            # Event types
            cursor = conn.execute("""
                SELECT event_type, COUNT(*) as count 
                FROM game_events_v2 
                GROUP BY event_type
            """)
            event_types = dict(cursor.fetchall())
            
            # Room stats
            cursor = conn.execute("""
                SELECT room_id, COUNT(*) as count 
                FROM game_events_v2 
                GROUP BY room_id
            """)
            room_stats = dict(cursor.fetchall())
            
            # Active rooms
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT room_id) 
                FROM game_events_v2 
                WHERE timestamp > ?
            """, (time.time() - 3600,))  # Active in last hour
            active_rooms = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_events": total_events,
                "event_types": event_types,
                "room_stats": room_stats,
                "total_rooms": len(room_stats),
                "active_rooms": active_rooms
            }
            
        except Exception as e:
            logger.error(f"Error getting event stats: {e}")
            return {}
    
    async def export_room_history(self, room_id: str) -> Dict[str, Any]:
        """Export complete room history."""
        try:
            # Get all events
            events = await self.get_room_events(room_id)
            
            # Get room state
            state = await self.replay_room_state(room_id)
            
            # Build timeline
            timeline = []
            for event in events:
                timeline.append({
                    "sequence": event.sequence,
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "player": event.player_id,
                    "summary": self._summarize_event(event)
                })
            
            return {
                "room_id": room_id,
                "exported_at": datetime.now().isoformat(),
                "state": state,
                "timeline": timeline,
                "total_events": len(events)
            }
            
        except Exception as e:
            logger.error(f"Error exporting room history: {e}")
            return {}
    
    async def cleanup_old_events(self, older_than_hours: int) -> int:
        """Clean up old events (NOT IMPLEMENTED for safety)."""
        # Don't actually delete anything - just return 0
        logger.warning(f"cleanup_old_events called but not implemented for safety")
        return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            
            return {
                "status": "healthy",
                "database": self.db_path,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def _summarize_event(self, event: GameEvent) -> str:
        """Create a human-readable summary of an event."""
        event_type = event.event_type
        round_num = event.payload.get('round_number', '')
        
        if event_type == "game_started":
            return f"Game started"
        elif event_type == "round_started":
            return f"Round {round_num} started" if round_num else "Round started"
        elif event_type == "phase_change":
            return f"Phase changed"
        elif event_type == "phase_data_update":
            return f"Phase data updated"
        elif event_type == "hands_dealt":
            return f"Hands dealt for round {round_num}" if round_num else "Hands dealt"
        else:
            return f"{event_type}"


# Create singleton instance
debug_db_service = DebugDatabaseService()