"""
Game-specific metrics collection.

Provides comprehensive metrics for game operations, state transitions,
and business intelligence.
"""

from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict, deque
import statistics

from ..observability.metrics import (
    IMetricsCollector,
    MetricTag,
    Counter,
    Gauge,
    Histogram,
    Timer,
    get_metrics_collector,
)


class GameMetricType(Enum):
    """Types of game-specific metrics."""

    # Game lifecycle
    GAMES_STARTED = "games.started"
    GAMES_COMPLETED = "games.completed"
    GAMES_ABANDONED = "games.abandoned"
    GAME_DURATION = "game.duration"

    # Player metrics
    PLAYER_ACTIONS = "player.actions"
    PLAYER_WINS = "player.wins"
    PLAYER_DISCONNECTS = "player.disconnects"
    PLAYER_RECONNECTS = "player.reconnects"

    # State metrics
    STATE_TRANSITIONS = "state.transitions"
    STATE_DURATION = "state.duration"
    STATE_ERRORS = "state.errors"

    # Phase metrics
    PHASE_DURATION = "phase.duration"
    TURN_DURATION = "turn.duration"
    DECLARATION_TIME = "declaration.time"

    # WebSocket metrics
    WS_CONNECTIONS = "websocket.connections"
    WS_MESSAGES = "websocket.messages"
    WS_BROADCAST_TIME = "websocket.broadcast_time"
    WS_BROADCAST_FAILURES = "websocket.broadcast_failures"

    # Performance metrics
    ACTION_QUEUE_DEPTH = "action.queue_depth"
    ACTION_PROCESSING_TIME = "action.processing_time"
    MEMORY_USAGE = "memory.usage_mb"
    GC_COLLECTIONS = "gc.collections"


@dataclass
class GameStats:
    """Statistics for a single game."""

    game_id: str
    room_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    player_count: int = 0
    bot_count: int = 0
    total_turns: int = 0
    winner_id: Optional[str] = None
    final_scores: Dict[str, int] = field(default_factory=dict)
    phase_durations: Dict[str, float] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get game duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """Check if game completed."""
        return self.end_time is not None

    @property
    def average_turn_time(self) -> float:
        """Calculate average turn time."""
        if self.total_turns == 0:
            return 0.0
        duration = self.duration_seconds
        if duration:
            return duration / self.total_turns
        return 0.0


class GameMetricsCollector:
    """
    Collects and aggregates game-specific metrics.

    Features:
    - Real-time game statistics
    - Player behavior tracking
    - Performance monitoring
    - Business intelligence metrics
    """

    def __init__(
        self,
        metrics_collector: Optional[IMetricsCollector] = None,
        retention_hours: int = 24,
    ):
        """Initialize game metrics collector."""
        self.collector = metrics_collector or get_metrics_collector()
        self.retention_hours = retention_hours

        # Game tracking
        self._active_games: Dict[str, GameStats] = {}
        self._completed_games: deque = deque(maxlen=10000)

        # Time-based aggregations
        self._hourly_stats: defaultdict = defaultdict(
            lambda: {
                "games_started": 0,
                "games_completed": 0,
                "games_abandoned": 0,
                "total_players": 0,
                "total_turns": 0,
            }
        )

        # Player statistics
        self._player_stats: defaultdict = defaultdict(
            lambda: {
                "games_played": 0,
                "games_won": 0,
                "total_score": 0,
                "actions_taken": 0,
                "avg_response_time": 0,
            }
        )

        # State tracking
        self._state_transitions: deque = deque(maxlen=10000)
        self._phase_times: defaultdict = defaultdict(list)

        # WebSocket metrics
        self._active_connections: Set[str] = set()
        self._message_counts: defaultdict = defaultdict(int)

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def record_game_start(
        self, game_id: str, room_id: str, player_count: int, bot_count: int
    ) -> None:
        """Record game start."""
        # Create game stats
        game_stats = GameStats(
            game_id=game_id,
            room_id=room_id,
            start_time=datetime.utcnow(),
            player_count=player_count,
            bot_count=bot_count,
        )
        self._active_games[game_id] = game_stats

        # Update metrics
        self.collector.increment(GameMetricType.GAMES_STARTED.value)
        self.collector.gauge(
            "games.active", len(self._active_games), [MetricTag("type", "realtime")]
        )

        # Update hourly stats
        hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
        self._hourly_stats[hour_key]["games_started"] += 1
        self._hourly_stats[hour_key]["total_players"] += player_count

    async def record_game_end(
        self,
        game_id: str,
        winner_id: Optional[str],
        final_scores: Dict[str, int],
        abandoned: bool = False,
    ) -> None:
        """Record game end."""
        game_stats = self._active_games.get(game_id)
        if not game_stats:
            return

        # Update game stats
        game_stats.end_time = datetime.utcnow()
        game_stats.winner_id = winner_id
        game_stats.final_scores = final_scores

        # Calculate duration
        duration = game_stats.duration_seconds
        if duration:
            self.collector.histogram(
                GameMetricType.GAME_DURATION.value,
                duration,
                [MetricTag("abandoned", str(abandoned))],
            )

        # Update metrics
        if abandoned:
            self.collector.increment(GameMetricType.GAMES_ABANDONED.value)
            hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
            self._hourly_stats[hour_key]["games_abandoned"] += 1
        else:
            self.collector.increment(GameMetricType.GAMES_COMPLETED.value)
            hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
            self._hourly_stats[hour_key]["games_completed"] += 1

            # Update player stats
            if winner_id:
                self._player_stats[winner_id]["games_won"] += 1
                self.collector.increment(
                    GameMetricType.PLAYER_WINS.value,
                    tags=[
                        MetricTag(
                            "player_type",
                            "human" if not winner_id.startswith("bot_") else "bot",
                        )
                    ],
                )

        # Move to completed
        self._active_games.pop(game_id)
        self._completed_games.append(game_stats)

        # Update active games gauge
        self.collector.gauge(
            "games.active", len(self._active_games), [MetricTag("type", "realtime")]
        )

    async def record_player_action(
        self,
        player_id: str,
        action_type: str,
        response_time_ms: float,
        game_id: Optional[str] = None,
    ) -> None:
        """Record player action."""
        # Update counters
        self.collector.increment(
            GameMetricType.PLAYER_ACTIONS.value,
            tags=[
                MetricTag("action_type", action_type),
                MetricTag(
                    "player_type",
                    "human" if not player_id.startswith("bot_") else "bot",
                ),
            ],
        )

        # Record response time
        self.collector.histogram(
            "player.response_time",
            response_time_ms,
            [MetricTag("action_type", action_type)],
        )

        # Update player stats
        self._player_stats[player_id]["actions_taken"] += 1

        # Update game stats
        if game_id and game_id in self._active_games:
            self._active_games[game_id].total_turns += 1

    async def record_state_transition(
        self, game_id: str, from_state: str, to_state: str, transition_time_ms: float
    ) -> None:
        """Record state transition."""
        # Record transition
        self.collector.increment(
            GameMetricType.STATE_TRANSITIONS.value,
            tags=[MetricTag("from_state", from_state), MetricTag("to_state", to_state)],
        )

        # Record transition time
        self.collector.histogram(
            "state.transition_time",
            transition_time_ms,
            [MetricTag("transition", f"{from_state}->{to_state}")],
        )

        # Track transition history
        self._state_transitions.append(
            {
                "timestamp": datetime.utcnow(),
                "game_id": game_id,
                "from_state": from_state,
                "to_state": to_state,
                "duration_ms": transition_time_ms,
            }
        )

    async def record_phase_duration(
        self, game_id: str, phase: str, duration_seconds: float
    ) -> None:
        """Record phase duration."""
        # Record in histogram
        self.collector.histogram(
            GameMetricType.PHASE_DURATION.value,
            duration_seconds,
            [MetricTag("phase", phase)],
        )

        # Store for aggregation
        self._phase_times[phase].append(duration_seconds)

        # Update game stats
        if game_id in self._active_games:
            self._active_games[game_id].phase_durations[phase] = duration_seconds

    async def record_websocket_connection(
        self, connection_id: str, connected: bool
    ) -> None:
        """Record WebSocket connection event."""
        if connected:
            self._active_connections.add(connection_id)
            self.collector.increment(f"{GameMetricType.WS_CONNECTIONS.value}.opened")
        else:
            self._active_connections.discard(connection_id)
            self.collector.increment(f"{GameMetricType.WS_CONNECTIONS.value}.closed")

        # Update gauge
        self.collector.gauge(
            f"{GameMetricType.WS_CONNECTIONS.value}.active",
            len(self._active_connections),
        )

    async def record_websocket_broadcast(
        self,
        room_id: str,
        recipient_count: int,
        broadcast_time_ms: float,
        success: bool = True,
    ) -> None:
        """Record WebSocket broadcast metrics."""
        if success:
            self.collector.histogram(
                GameMetricType.WS_BROADCAST_TIME.value,
                broadcast_time_ms,
                [MetricTag("room_id", room_id)],
            )
            self.collector.increment(
                f"{GameMetricType.WS_MESSAGES.value}.broadcast", recipient_count
            )
        else:
            self.collector.increment(
                GameMetricType.WS_BROADCAST_FAILURES.value,
                tags=[MetricTag("room_id", room_id)],
            )

    def get_hourly_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics aggregated by hour."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        metrics = {}
        for hour_key, stats in self._hourly_stats.items():
            try:
                hour_time = datetime.strptime(hour_key, "%Y-%m-%d-%H")
                if hour_time >= cutoff:
                    metrics[hour_key] = stats
            except ValueError:
                continue

        return metrics

    def get_player_metrics(self, player_id: Optional[str] = None) -> Dict[str, Any]:
        """Get player metrics."""
        if player_id:
            return self._player_stats.get(player_id, {})

        # Aggregate all players
        total_players = len(self._player_stats)
        if total_players == 0:
            return {}

        total_games = sum(p["games_played"] for p in self._player_stats.values())
        total_wins = sum(p["games_won"] for p in self._player_stats.values())

        return {
            "total_players": total_players,
            "average_games_per_player": total_games / total_players,
            "overall_win_rate": total_wins / total_games if total_games > 0 else 0,
            "bot_win_rate": self._calculate_bot_win_rate(),
            "human_win_rate": self._calculate_human_win_rate(),
        }

    def get_phase_metrics(self) -> Dict[str, Any]:
        """Get phase duration metrics."""
        metrics = {}

        for phase, durations in self._phase_times.items():
            if durations:
                metrics[phase] = {
                    "avg_seconds": statistics.mean(durations),
                    "min_seconds": min(durations),
                    "max_seconds": max(durations),
                    "p95_seconds": self._percentile(durations, 95),
                }

        return metrics

    def get_game_analytics(self) -> Dict[str, Any]:
        """Get comprehensive game analytics."""
        completed_games = list(self._completed_games)

        if not completed_games:
            return {
                "total_games": 0,
                "active_games": len(self._active_games),
                "avg_duration": 0,
                "avg_players": 0,
                "completion_rate": 0,
            }

        durations = [g.duration_seconds for g in completed_games if g.duration_seconds]
        player_counts = [g.player_count for g in completed_games]

        total_games = len(completed_games) + len(self._active_games)
        completed_count = len([g for g in completed_games if g.is_completed])

        return {
            "total_games": total_games,
            "active_games": len(self._active_games),
            "completed_games": completed_count,
            "abandoned_games": total_games - completed_count - len(self._active_games),
            "avg_duration_minutes": statistics.mean(durations) / 60 if durations else 0,
            "avg_players": statistics.mean(player_counts) if player_counts else 0,
            "completion_rate": completed_count / total_games if total_games > 0 else 0,
            "games_per_hour": self._calculate_games_per_hour(),
        }

    def _calculate_bot_win_rate(self) -> float:
        """Calculate bot win rate."""
        bot_games = 0
        bot_wins = 0

        for player_id, stats in self._player_stats.items():
            if player_id.startswith("bot_"):
                bot_games += stats["games_played"]
                bot_wins += stats["games_won"]

        return bot_wins / bot_games if bot_games > 0 else 0

    def _calculate_human_win_rate(self) -> float:
        """Calculate human win rate."""
        human_games = 0
        human_wins = 0

        for player_id, stats in self._player_stats.items():
            if not player_id.startswith("bot_"):
                human_games += stats["games_played"]
                human_wins += stats["games_won"]

        return human_wins / human_games if human_games > 0 else 0

    def _calculate_games_per_hour(self) -> float:
        """Calculate average games per hour."""
        hour_count = len(self._hourly_stats)
        if hour_count == 0:
            return 0

        total_games = sum(
            stats["games_started"] for stats in self._hourly_stats.values()
        )
        return total_games / hour_count

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        idx = int(len(sorted_values) * (percentile / 100))
        return sorted_values[min(idx, len(sorted_values) - 1)]

    async def _cleanup_loop(self) -> None:
        """Periodically clean up old data."""
        while True:
            await asyncio.sleep(3600)  # Run every hour
            self._cleanup_old_data()

    def _cleanup_old_data(self) -> None:
        """Clean up data older than retention period."""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)

        # Clean hourly stats
        old_keys = []
        for hour_key in self._hourly_stats:
            try:
                hour_time = datetime.strptime(hour_key, "%Y-%m-%d-%H")
                if hour_time < cutoff:
                    old_keys.append(hour_key)
            except ValueError:
                old_keys.append(hour_key)

        for key in old_keys:
            del self._hourly_stats[key]

        # Clean state transitions
        while (
            self._state_transitions and self._state_transitions[0]["timestamp"] < cutoff
        ):
            self._state_transitions.popleft()
