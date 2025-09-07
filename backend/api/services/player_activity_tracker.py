# backend/api/services/player_activity_tracker.py

"""
Player Activity Tracking Service

Tracks player activity, heartbeats, and detects potential hang situations.
Part of the Player Activity Monitor system for diagnosing player hang issues.
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class PlayerActivity:
    """Represents a player's activity state"""

    player_id: str
    room_id: str
    last_heartbeat: float = field(default_factory=time.time)
    last_action: float = field(default_factory=time.time)
    last_action_type: str = ""
    heartbeat_data: dict = field(default_factory=dict)
    action_history: deque = field(default_factory=lambda: deque(maxlen=50))

    def is_active(self) -> bool:
        """Check if player is considered active"""
        return (time.time() - self.last_heartbeat) < 90  # 90 seconds threshold


@dataclass
class HangDiagnostic:
    """Diagnostic information about a detected hang"""

    player_id: str
    room_id: str
    hang_type: str
    duration_seconds: float
    timestamp: float = field(default_factory=time.time)

    # Context data
    game_phase: Optional[str] = None
    last_actions: List[dict] = field(default_factory=list)
    pending_actions: List[str] = field(default_factory=list)

    # Network state
    connection_status: str = "unknown"
    message_queue_size: int = 0
    unacked_messages: int = 0
    last_heartbeat_delta: float = 0.0

    # Server state
    server_memory_mb: float = 0.0
    active_connections: int = 0
    room_player_states: dict = field(default_factory=dict)

    # Client state (from heartbeat)
    client_ui_state: dict = field(default_factory=dict)
    client_memory_mb: Optional[float] = None
    client_pending: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "player_id": self.player_id,
            "room_id": self.room_id,
            "hang_type": self.hang_type,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp,
            "game_phase": self.game_phase,
            "last_actions": self.last_actions,
            "pending_actions": self.pending_actions,
            "connection_status": self.connection_status,
            "message_queue_size": self.message_queue_size,
            "unacked_messages": self.unacked_messages,
            "last_heartbeat_delta": self.last_heartbeat_delta,
            "server_memory_mb": self.server_memory_mb,
            "active_connections": self.active_connections,
            "room_player_states": self.room_player_states,
            "client_ui_state": self.client_ui_state,
            "client_memory_mb": self.client_memory_mb,
            "client_pending": self.client_pending,
        }


class PlayerActivityTracker:
    """
    Tracks player activity and detects hang situations
    """

    def __init__(self):
        # Track activities by room_id -> player_name -> PlayerActivity
        self.activities: Dict[str, Dict[str, PlayerActivity]] = {}
        # Store diagnostic snapshots
        self.diagnostic_buffer = deque(maxlen=100)
        # Lock for thread safety
        self.lock = asyncio.Lock()
        # Sequence number for actions
        self.sequence_numbers: Dict[str, int] = {}

    async def record_heartbeat(self, room_id: str, player_name: str, data: dict):
        """Record player heartbeat with diagnostic data"""
        async with self.lock:
            activity = self._get_or_create_activity(room_id, player_name)

            # Update heartbeat time
            activity.last_heartbeat = time.time()
            # Ensure we never set heartbeat_data to None
            activity.heartbeat_data = data or {}

            # Check for anomalies in heartbeat data
            if data.get("last_user_action_age", 0) > 300000:  # 5 minutes
                logger.warning(
                    f"Player {player_name} in room {room_id} hasn't performed "
                    f"action in {data['last_user_action_age']/1000:.1f} seconds"
                )

    async def record_action(
        self, room_id: str, player_name: str, action_type: str, context: dict = None
    ):
        """Record a player action"""
        async with self.lock:
            activity = self._get_or_create_activity(room_id, player_name)

            # Update timestamps
            activity.last_action = time.time()
            activity.last_action_type = action_type

            # Add to action history
            action_record = {
                "timestamp": time.time(),
                "type": action_type,
                "context": context or {},
                "sequence": self._get_next_sequence(room_id),
            }

            activity.action_history.append(action_record)

    async def detect_hangs(self) -> List[HangDiagnostic]:
        """Detect potential hang situations"""
        hangs = []

        async with self.lock:
            now = time.time()

            for room_id, room_activities in self.activities.items():
                for player_name, activity in room_activities.items():
                    # Check various hang conditions
                    hang_diagnostic = await self._check_for_hang(activity, now)
                    if hang_diagnostic:
                        hangs.append(hang_diagnostic)
                        self.diagnostic_buffer.append(hang_diagnostic)

        return hangs

    async def get_room_activities(self, room_id: str) -> Dict[str, PlayerActivity]:
        """Get all player activities in a room"""
        async with self.lock:
            return self.activities.get(room_id, {}).copy()

    async def get_diagnostics(
        self,
        limit: int = 20,
        hang_type: Optional[str] = None,
        player_id: Optional[str] = None,
    ) -> List[HangDiagnostic]:
        """Get recent diagnostic snapshots"""
        diagnostics = list(self.diagnostic_buffer)

        # Filter by hang type if specified
        if hang_type:
            diagnostics = [d for d in diagnostics if d.hang_type == hang_type]

        # Filter by player if specified
        if player_id:
            diagnostics = [d for d in diagnostics if d.player_id == player_id]

        # Sort by timestamp descending and limit
        diagnostics.sort(key=lambda d: d.timestamp, reverse=True)
        return diagnostics[:limit]

    async def get_hang_summary(self) -> dict:
        """Get summary of hang detections"""
        summary = {
            "total_hangs": len(self.diagnostic_buffer),
            "by_type": {},
            "by_player": {},
            "recent_count": 0,
        }

        recent_threshold = time.time() - 300  # Last 5 minutes

        for diagnostic in self.diagnostic_buffer:
            # Count by type
            hang_type = diagnostic.hang_type
            summary["by_type"][hang_type] = summary["by_type"].get(hang_type, 0) + 1

            # Count by player
            player = diagnostic.player_id
            summary["by_player"][player] = summary["by_player"].get(player, 0) + 1

            # Count recent
            if diagnostic.timestamp > recent_threshold:
                summary["recent_count"] += 1

        return summary

    def _get_or_create_activity(self, room_id: str, player_name: str) -> PlayerActivity:
        """Get or create player activity record"""
        if room_id not in self.activities:
            self.activities[room_id] = {}

        if player_name not in self.activities[room_id]:
            self.activities[room_id][player_name] = PlayerActivity(
                player_id=player_name, room_id=room_id
            )

        return self.activities[room_id][player_name]

    def _get_next_sequence(self, room_id: str) -> int:
        """Get next sequence number for room"""
        if room_id not in self.sequence_numbers:
            self.sequence_numbers[room_id] = 0
        self.sequence_numbers[room_id] += 1
        return self.sequence_numbers[room_id]

    async def _check_for_hang(
        self, activity: PlayerActivity, now: float
    ) -> Optional[HangDiagnostic]:
        """Check if a player is experiencing a hang"""
        # No heartbeat hang
        heartbeat_delta = now - activity.last_heartbeat
        if heartbeat_delta > 90:  # 90 seconds
            return await self._create_diagnostic(
                activity, "no_heartbeat", heartbeat_delta
            )

        # Check for waiting too long
        heartbeat_data = activity.heartbeat_data
        if not heartbeat_data:
            return None
        game_context = heartbeat_data.get("game_context", {})

        if game_context and game_context.get("is_my_turn"):
            action_delta = now - activity.last_action
            if action_delta > 60:  # 60 seconds to make a move
                return await self._create_diagnostic(
                    activity, "waiting_action", action_delta
                )

        return None

    async def _create_diagnostic(
        self, activity: PlayerActivity, hang_type: str, duration: float
    ) -> HangDiagnostic:
        """Create a diagnostic snapshot"""
        # Get server state
        try:
            import psutil

            process = psutil.Process()
            server_memory_mb = process.memory_info().rss / 1024 / 1024
        except:
            server_memory_mb = 0.0

        # Get connection state
        from backend.api.websocket.connection_manager import connection_manager

        connection = await connection_manager.get_connection(
            activity.room_id, activity.player_id
        )

        # Get room state
        from backend.shared_instances import shared_room_manager

        room = await shared_room_manager.get_room(activity.room_id)

        room_player_states = {}
        if room and room.game:
            for player in room.game.players:
                if player:
                    room_player_states[player.name] = {
                        "is_bot": player.is_bot,
                        "is_connected": getattr(player, "is_connected", True),
                        "score": player.score,
                    }

        # Create diagnostic
        heartbeat_data = activity.heartbeat_data or {}
        game_context = heartbeat_data.get("game_context", {})
        performance = heartbeat_data.get("performance", {})

        diagnostic = HangDiagnostic(
            player_id=activity.player_id,
            room_id=activity.room_id,
            hang_type=hang_type,
            duration_seconds=duration,
            game_phase=game_context.get("phase"),
            last_actions=list(activity.action_history)[-5:],  # Last 5 actions
            connection_status=connection.connection_status.value
            if connection
            else "unknown",
            last_heartbeat_delta=time.time() - activity.last_heartbeat,
            server_memory_mb=server_memory_mb,
            active_connections=len(connection_manager.websocket_to_player),
            room_player_states=room_player_states,
            client_ui_state=game_context,
            client_memory_mb=performance.get("memory_mb") if performance else None,
        )

        # Log the hang detection
        logger.warning(
            f"Hang detected: {hang_type} for player {activity.player_id} "
            f"in room {activity.room_id}, duration: {duration:.1f}s"
        )

        return diagnostic

    async def cleanup_room(self, room_id: str):
        """Clean up activities for a room"""
        async with self.lock:
            if room_id in self.activities:
                del self.activities[room_id]
            if room_id in self.sequence_numbers:
                del self.sequence_numbers[room_id]


# Create singleton instance
activity_tracker = PlayerActivityTracker()
