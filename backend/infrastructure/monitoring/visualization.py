"""
State machine visualization for monitoring.

Provides real-time visualization data for state machines,
game states, and system status.
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json


class VisualizationType(Enum):
    """Types of visualizations available."""

    STATE_DIAGRAM = "state_diagram"
    ROOM_STATUS = "room_status"
    PLAYER_ACTIVITY = "player_activity"
    PERFORMANCE_METRICS = "performance_metrics"
    ERROR_HEATMAP = "error_heatmap"
    FLOW_DIAGRAM = "flow_diagram"


@dataclass
class StateNode:
    """Represents a state in the visualization."""

    state_name: str
    active_games: int = 0
    avg_duration_seconds: float = 0.0
    error_count: int = 0
    transitions_in: int = 0
    transitions_out: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.state_name,
            "active_games": self.active_games,
            "avg_duration_seconds": self.avg_duration_seconds,
            "error_count": self.error_count,
            "transitions_in": self.transitions_in,
            "transitions_out": self.transitions_out,
            "metadata": self.metadata,
        }


@dataclass
class StateTransition:
    """Represents a transition between states."""

    from_state: str
    to_state: str
    count: int = 0
    avg_duration_ms: float = 0.0
    error_rate: float = 0.0
    last_transition: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "from": self.from_state,
            "to": self.to_state,
            "count": self.count,
            "avg_duration_ms": self.avg_duration_ms,
            "error_rate": self.error_rate,
            "last_transition": (
                self.last_transition.isoformat() if self.last_transition else None
            ),
        }


@dataclass
class RoomVisualization:
    """Visualization data for a game room."""

    room_id: str
    game_id: Optional[str]
    current_state: str
    player_count: int
    bot_count: int
    created_at: datetime
    last_activity: datetime
    total_actions: int = 0
    error_count: int = 0
    phase_durations: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "room_id": self.room_id,
            "game_id": self.game_id,
            "current_state": self.current_state,
            "player_count": self.player_count,
            "bot_count": self.bot_count,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "total_actions": self.total_actions,
            "error_count": self.error_count,
            "phase_durations": self.phase_durations,
            "health": self._calculate_health(),
        }

    def _calculate_health(self) -> str:
        """Calculate room health status."""
        if self.error_count > 10:
            return "critical"
        elif self.error_count > 5:
            return "warning"
        elif (datetime.utcnow() - self.last_activity).total_seconds() > 300:
            return "idle"
        else:
            return "healthy"


class StateVisualizationProvider:
    """
    Provides visualization data for state machines.

    Features:
    - State diagram generation
    - Room status overview
    - Performance visualization
    - Error tracking
    """

    def __init__(self):
        """Initialize visualization provider."""
        # State tracking
        self._state_nodes: Dict[str, StateNode] = {}
        self._state_transitions: Dict[str, StateTransition] = {}
        self._room_visualizations: Dict[str, RoomVisualization] = {}

        # Performance data
        self._performance_timeline: List[Dict[str, Any]] = []
        self._error_heatmap: Dict[str, Dict[str, int]] = {}

        # Initialize default states
        self._initialize_default_states()

    def _initialize_default_states(self) -> None:
        """Initialize default state nodes."""
        default_states = [
            "WAITING_FOR_PLAYERS",
            "PREPARATION",
            "DECLARATION",
            "TURN",
            "SCORING",
            "GAME_OVER",
        ]

        for state in default_states:
            self._state_nodes[state] = StateNode(state_name=state)

        # Define default transitions
        default_transitions = [
            ("WAITING_FOR_PLAYERS", "PREPARATION"),
            ("PREPARATION", "DECLARATION"),
            ("DECLARATION", "TURN"),
            ("TURN", "TURN"),  # Self-transition
            ("TURN", "SCORING"),
            ("SCORING", "PREPARATION"),  # Next round
            ("SCORING", "GAME_OVER"),
        ]

        for from_state, to_state in default_transitions:
            key = f"{from_state}->{to_state}"
            self._state_transitions[key] = StateTransition(
                from_state=from_state, to_state=to_state
            )

    def update_state_node(
        self,
        state_name: str,
        active_games_delta: int = 0,
        duration_sample: Optional[float] = None,
        error_occurred: bool = False,
    ) -> None:
        """Update state node information."""
        if state_name not in self._state_nodes:
            self._state_nodes[state_name] = StateNode(state_name=state_name)

        node = self._state_nodes[state_name]
        node.active_games += active_games_delta

        if duration_sample is not None:
            # Simple moving average
            if node.avg_duration_seconds == 0:
                node.avg_duration_seconds = duration_sample
            else:
                node.avg_duration_seconds = (
                    node.avg_duration_seconds * 0.9 + duration_sample * 0.1
                )

        if error_occurred:
            node.error_count += 1

    def update_state_transition(
        self, from_state: str, to_state: str, duration_ms: float, success: bool = True
    ) -> None:
        """Update state transition information."""
        key = f"{from_state}->{to_state}"

        if key not in self._state_transitions:
            self._state_transitions[key] = StateTransition(
                from_state=from_state, to_state=to_state
            )

        transition = self._state_transitions[key]
        transition.count += 1
        transition.last_transition = datetime.utcnow()

        # Update average duration
        if transition.avg_duration_ms == 0:
            transition.avg_duration_ms = duration_ms
        else:
            transition.avg_duration_ms = (
                transition.avg_duration_ms * 0.9 + duration_ms * 0.1
            )

        # Update error rate
        if not success:
            transition.error_rate = (
                transition.error_rate * (transition.count - 1) + 1
            ) / transition.count
        else:
            transition.error_rate = (
                transition.error_rate * (transition.count - 1)
            ) / transition.count

        # Update node transition counts
        if from_state in self._state_nodes:
            self._state_nodes[from_state].transitions_out += 1
        if to_state in self._state_nodes:
            self._state_nodes[to_state].transitions_in += 1

    def update_room_visualization(
        self,
        room_id: str,
        game_id: Optional[str] = None,
        current_state: Optional[str] = None,
        player_count: Optional[int] = None,
        action_occurred: bool = False,
        error_occurred: bool = False,
    ) -> None:
        """Update room visualization data."""
        if room_id not in self._room_visualizations:
            self._room_visualizations[room_id] = RoomVisualization(
                room_id=room_id,
                game_id=game_id,
                current_state=current_state or "UNKNOWN",
                player_count=player_count or 0,
                bot_count=0,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
            )

        room = self._room_visualizations[room_id]

        if game_id:
            room.game_id = game_id
        if current_state:
            room.current_state = current_state
        if player_count is not None:
            room.player_count = player_count

        room.last_activity = datetime.utcnow()

        if action_occurred:
            room.total_actions += 1
        if error_occurred:
            room.error_count += 1

    def get_state_diagram(self) -> Dict[str, Any]:
        """Get state diagram visualization data."""
        return {
            "type": VisualizationType.STATE_DIAGRAM.value,
            "nodes": [node.to_dict() for node in self._state_nodes.values()],
            "edges": [trans.to_dict() for trans in self._state_transitions.values()],
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_room_status(self) -> Dict[str, Any]:
        """Get room status overview."""
        rooms = list(self._room_visualizations.values())

        # Calculate statistics
        total_rooms = len(rooms)
        active_rooms = sum(1 for r in rooms if r.game_id is not None)
        total_players = sum(r.player_count for r in rooms)

        # Group by state
        rooms_by_state = {}
        for room in rooms:
            state = room.current_state
            if state not in rooms_by_state:
                rooms_by_state[state] = []
            rooms_by_state[state].append(room.to_dict())

        # Health summary
        health_summary = {
            "healthy": sum(1 for r in rooms if r._calculate_health() == "healthy"),
            "idle": sum(1 for r in rooms if r._calculate_health() == "idle"),
            "warning": sum(1 for r in rooms if r._calculate_health() == "warning"),
            "critical": sum(1 for r in rooms if r._calculate_health() == "critical"),
        }

        return {
            "type": VisualizationType.ROOM_STATUS.value,
            "summary": {
                "total_rooms": total_rooms,
                "active_rooms": active_rooms,
                "total_players": total_players,
                "health_summary": health_summary,
            },
            "rooms_by_state": rooms_by_state,
            "rooms": [room.to_dict() for room in rooms],
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_performance_metrics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance metrics visualization."""
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)

        # Filter recent timeline data
        recent_data = [
            d
            for d in self._performance_timeline
            if datetime.fromisoformat(d["timestamp"]) > cutoff
        ]

        # Calculate aggregates
        if recent_data:
            avg_response_time = sum(
                d.get("response_time", 0) for d in recent_data
            ) / len(recent_data)
            error_rate = sum(1 for d in recent_data if d.get("error", False)) / len(
                recent_data
            )
        else:
            avg_response_time = 0
            error_rate = 0

        return {
            "type": VisualizationType.PERFORMANCE_METRICS.value,
            "window_minutes": window_minutes,
            "timeline": recent_data,
            "aggregates": {
                "avg_response_time_ms": avg_response_time,
                "error_rate": error_rate,
                "total_requests": len(recent_data),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_error_heatmap(self) -> Dict[str, Any]:
        """Get error heatmap visualization."""
        # Convert heatmap to list format
        heatmap_data = []
        for state, errors_by_type in self._error_heatmap.items():
            for error_type, count in errors_by_type.items():
                heatmap_data.append(
                    {"state": state, "error_type": error_type, "count": count}
                )

        return {
            "type": VisualizationType.ERROR_HEATMAP.value,
            "data": heatmap_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def record_performance_sample(
        self,
        endpoint: str,
        response_time_ms: float,
        error: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record performance sample for timeline."""
        sample = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": endpoint,
            "response_time": response_time_ms,
            "error": error,
            "metadata": metadata or {},
        }

        self._performance_timeline.append(sample)

        # Keep only recent data (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self._performance_timeline = [
            d
            for d in self._performance_timeline
            if datetime.fromisoformat(d["timestamp"]) > cutoff
        ]

    def record_error(self, state: str, error_type: str) -> None:
        """Record error for heatmap."""
        if state not in self._error_heatmap:
            self._error_heatmap[state] = {}

        if error_type not in self._error_heatmap[state]:
            self._error_heatmap[state][error_type] = 0

        self._error_heatmap[state][error_type] += 1

    def get_all_visualizations(self) -> Dict[str, Any]:
        """Get all visualization data."""
        return {
            "state_diagram": self.get_state_diagram(),
            "room_status": self.get_room_status(),
            "performance_metrics": self.get_performance_metrics(),
            "error_heatmap": self.get_error_heatmap(),
            "generated_at": datetime.utcnow().isoformat(),
        }

    def cleanup_old_data(self, hours: int = 24) -> None:
        """Clean up old visualization data."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Clean up inactive rooms
        inactive_rooms = [
            room_id
            for room_id, room in self._room_visualizations.items()
            if room.last_activity < cutoff
        ]

        for room_id in inactive_rooms:
            del self._room_visualizations[room_id]

        # Reset old transition data
        for transition in self._state_transitions.values():
            if transition.last_transition and transition.last_transition < cutoff:
                transition.count = 0
                transition.avg_duration_ms = 0
                transition.error_rate = 0


# Global visualization provider
_visualization_provider: Optional[StateVisualizationProvider] = None


def get_visualization_provider() -> StateVisualizationProvider:
    """Get global visualization provider."""
    global _visualization_provider
    if _visualization_provider is None:
        _visualization_provider = StateVisualizationProvider()
    return _visualization_provider
