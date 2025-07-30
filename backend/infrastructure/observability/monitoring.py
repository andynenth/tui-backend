"""
Performance monitoring and alerting infrastructure.

Provides real-time performance tracking and alert management.
"""

from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import time
from collections import deque, defaultdict
import statistics
import threading
from abc import ABC, abstractmethod


class AlertSeverity(Enum):
    """Severity levels for alerts."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    request_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    percentiles: Dict[int, float] = field(default_factory=dict)

    def add_request(self, duration_ms: float, is_error: bool = False) -> None:
        """Add a request to metrics."""
        self.request_count += 1
        self.total_duration_ms += duration_ms
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)

        if is_error:
            self.error_count += 1

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration."""
        if self.request_count == 0:
            return 0.0
        return self.total_duration_ms / self.request_count

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.request_count == 0:
            return 0.0
        return self.error_count / self.request_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_rate,
            "avg_duration_ms": self.avg_duration_ms,
            "min_duration_ms": self.min_duration_ms if self.request_count > 0 else 0,
            "max_duration_ms": self.max_duration_ms,
            "percentiles": self.percentiles,
        }


@dataclass
class AlertRule:
    """Rule for triggering alerts."""

    name: str
    metric_name: str
    condition: Callable[[float], bool]
    severity: AlertSeverity
    message_template: str
    cooldown_minutes: int = 5
    consecutive_failures: int = 1

    def evaluate(self, value: float) -> Optional[str]:
        """Evaluate rule and return message if triggered."""
        if self.condition(value):
            return self.message_template.format(metric=self.metric_name, value=value)
        return None


@dataclass
class Alert:
    """Represents a triggered alert."""

    rule_name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metric_value: Optional[float] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.resolved = True
        self.resolved_at = datetime.utcnow()


class PerformanceMonitor:
    """
    Real-time performance monitoring.

    Features:
    - Request/response tracking
    - Percentile calculations
    - Time-windowed metrics
    - Resource usage monitoring
    """

    def __init__(
        self, window_size_seconds: int = 300, percentiles: List[int] = None  # 5 minutes
    ):
        """Initialize performance monitor."""
        self.window_size_seconds = window_size_seconds
        self.percentiles = percentiles or [50, 90, 95, 99]

        # Time-series data
        self._request_durations: deque = deque()
        self._error_timestamps: deque = deque()
        self._metrics_by_endpoint: Dict[str, deque] = defaultdict(deque)

        # Current window metrics
        self._current_metrics = PerformanceMetrics()

        # Lock for thread safety
        self._lock = threading.RLock()

        # Start cleanup task
        self._cleanup_task = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_task.start()

    def record_request(
        self,
        endpoint: str,
        duration_ms: float,
        is_error: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a request."""
        timestamp = datetime.utcnow()

        with self._lock:
            # Add to time series
            entry = {
                "timestamp": timestamp,
                "endpoint": endpoint,
                "duration_ms": duration_ms,
                "is_error": is_error,
                "metadata": metadata or {},
            }

            self._request_durations.append(entry)
            self._metrics_by_endpoint[endpoint].append(entry)

            if is_error:
                self._error_timestamps.append(timestamp)

            # Update current metrics
            self._current_metrics.add_request(duration_ms, is_error)

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get metrics for current window."""
        with self._lock:
            # Calculate percentiles
            durations = [
                entry["duration_ms"]
                for entry in self._request_durations
                if (datetime.utcnow() - entry["timestamp"]).total_seconds()
                < self.window_size_seconds
            ]

            if durations:
                sorted_durations = sorted(durations)
                percentiles = {}

                for p in self.percentiles:
                    idx = int(len(sorted_durations) * (p / 100))
                    percentiles[p] = sorted_durations[
                        min(idx, len(sorted_durations) - 1)
                    ]

                self._current_metrics.percentiles = percentiles

            return self._current_metrics

    def get_endpoint_metrics(self, endpoint: str) -> PerformanceMetrics:
        """Get metrics for specific endpoint."""
        with self._lock:
            entries = self._metrics_by_endpoint.get(endpoint, [])

            metrics = PerformanceMetrics()
            for entry in entries:
                if (
                    datetime.utcnow() - entry["timestamp"]
                ).total_seconds() < self.window_size_seconds:
                    metrics.add_request(entry["duration_ms"], entry["is_error"])

            return metrics

    def get_error_rate(self, window_seconds: Optional[int] = None) -> float:
        """Get error rate for time window."""
        window = window_seconds or self.window_size_seconds
        cutoff = datetime.utcnow() - timedelta(seconds=window)

        with self._lock:
            total_requests = sum(
                1 for entry in self._request_durations if entry["timestamp"] > cutoff
            )

            error_count = sum(
                1 for timestamp in self._error_timestamps if timestamp > cutoff
            )

            if total_requests == 0:
                return 0.0

            return error_count / total_requests

    def get_requests_per_second(self) -> float:
        """Get current requests per second."""
        cutoff = datetime.utcnow() - timedelta(seconds=60)

        with self._lock:
            recent_requests = sum(
                1 for entry in self._request_durations if entry["timestamp"] > cutoff
            )

            return recent_requests / 60.0

    def _cleanup_loop(self) -> None:
        """Background cleanup of old data."""
        while True:
            time.sleep(60)  # Cleanup every minute
            self._cleanup_old_data()

    def _cleanup_old_data(self) -> None:
        """Remove data outside the window."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_size_seconds * 2)

        with self._lock:
            # Clean request durations
            while (
                self._request_durations
                and self._request_durations[0]["timestamp"] < cutoff
            ):
                self._request_durations.popleft()

            # Clean error timestamps
            while self._error_timestamps and self._error_timestamps[0] < cutoff:
                self._error_timestamps.popleft()

            # Clean endpoint metrics
            for endpoint, entries in self._metrics_by_endpoint.items():
                while entries and entries[0]["timestamp"] < cutoff:
                    entries.popleft()


class AlertManager:
    """
    Manages performance alerts.

    Features:
    - Rule-based alerting
    - Alert deduplication
    - Cooldown periods
    - Alert resolution
    """

    def __init__(self):
        """Initialize alert manager."""
        self._rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._last_triggered: Dict[str, datetime] = {}
        self._consecutive_failures: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
        self._handlers: List[Callable[[Alert], None]] = []

    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        with self._lock:
            self._rules[rule.name] = rule

    def remove_rule(self, rule_name: str) -> None:
        """Remove an alert rule."""
        with self._lock:
            self._rules.pop(rule_name, None)

    def add_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add alert handler."""
        self._handlers.append(handler)

    def evaluate_metric(self, metric_name: str, value: float) -> List[Alert]:
        """Evaluate metric against all rules."""
        triggered_alerts = []

        with self._lock:
            for rule_name, rule in self._rules.items():
                if rule.metric_name != metric_name:
                    continue

                # Check cooldown
                last_triggered = self._last_triggered.get(rule_name)
                if last_triggered:
                    cooldown_end = last_triggered + timedelta(
                        minutes=rule.cooldown_minutes
                    )
                    if datetime.utcnow() < cooldown_end:
                        continue

                # Evaluate rule
                message = rule.evaluate(value)
                if message:
                    self._consecutive_failures[rule_name] += 1

                    # Check consecutive failures threshold
                    if (
                        self._consecutive_failures[rule_name]
                        >= rule.consecutive_failures
                    ):
                        alert = Alert(
                            rule_name=rule_name,
                            severity=rule.severity,
                            message=message,
                            metric_value=value,
                        )

                        # Add to active alerts
                        self._active_alerts[rule_name] = alert
                        self._alert_history.append(alert)
                        self._last_triggered[rule_name] = datetime.utcnow()

                        triggered_alerts.append(alert)

                        # Notify handlers
                        for handler in self._handlers:
                            try:
                                handler(alert)
                            except Exception:
                                pass  # Don't let handler errors affect alerting
                else:
                    # Rule passed, reset consecutive failures
                    self._consecutive_failures[rule_name] = 0

                    # Resolve active alert if exists
                    if rule_name in self._active_alerts:
                        self._active_alerts[rule_name].resolve()
                        del self._active_alerts[rule_name]

        return triggered_alerts

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        with self._lock:
            return list(self._active_alerts.values())

    def get_alert_history(
        self, since: Optional[datetime] = None, severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get alert history with optional filters."""
        with self._lock:
            alerts = self._alert_history

            if since:
                alerts = [a for a in alerts if a.timestamp >= since]

            if severity:
                alerts = [a for a in alerts if a.severity == severity]

            return alerts


@dataclass
class DashboardWidget:
    """Widget for metrics dashboard."""

    name: str
    type: str  # 'gauge', 'counter', 'graph', 'table'
    metric_source: Callable[[], Any]
    refresh_seconds: int = 5
    config: Dict[str, Any] = field(default_factory=dict)


class MetricsDashboard:
    """
    Real-time metrics dashboard.

    Features:
    - Configurable widgets
    - Auto-refresh
    - Export to various formats
    """

    def __init__(self, title: str = "System Metrics"):
        """Initialize dashboard."""
        self.title = title
        self._widgets: Dict[str, DashboardWidget] = {}
        self._widget_values: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def add_widget(self, widget: DashboardWidget) -> None:
        """Add a widget to dashboard."""
        with self._lock:
            self._widgets[widget.name] = widget

    def remove_widget(self, name: str) -> None:
        """Remove a widget."""
        with self._lock:
            self._widgets.pop(name, None)
            self._widget_values.pop(name, None)

    def refresh(self) -> Dict[str, Any]:
        """Refresh all widget values."""
        with self._lock:
            for name, widget in self._widgets.items():
                try:
                    self._widget_values[name] = widget.metric_source()
                except Exception as e:
                    self._widget_values[name] = f"Error: {str(e)}"

            return self._widget_values.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Export dashboard as dictionary."""
        self.refresh()

        return {
            "title": self.title,
            "timestamp": datetime.utcnow().isoformat(),
            "widgets": {
                name: {
                    "type": widget.type,
                    "value": self._widget_values.get(name),
                    "config": widget.config,
                }
                for name, widget in self._widgets.items()
            },
        }

    def to_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        self.refresh()

        lines = []
        for name, value in self._widget_values.items():
            widget = self._widgets[name]

            if widget.type in ["gauge", "counter"] and isinstance(value, (int, float)):
                metric_name = name.replace(" ", "_").lower()
                lines.append(f"# TYPE {metric_name} {widget.type}")
                lines.append(f"{metric_name} {value}")

        return "\n".join(lines)


# Game-specific monitoring


class GamePerformanceMonitor(PerformanceMonitor):
    """
    Performance monitor specialized for game operations.

    Tracks game-specific metrics like:
    - Turn processing time
    - WebSocket message latency
    - Room creation/join times
    - Bot response times
    """

    def __init__(self):
        """Initialize game performance monitor."""
        super().__init__(window_size_seconds=300)

        # Game-specific metrics
        self._turn_durations: deque = deque()
        self._bot_response_times: deque = deque()
        self._websocket_latencies: deque = deque()
        self._room_operations: Dict[str, deque] = defaultdict(deque)

    def record_turn(self, room_id: str, duration_ms: float, player_count: int) -> None:
        """Record turn processing time."""
        entry = {
            "timestamp": datetime.utcnow(),
            "room_id": room_id,
            "duration_ms": duration_ms,
            "player_count": player_count,
        }

        with self._lock:
            self._turn_durations.append(entry)

    def record_bot_response(self, bot_id: str, response_time_ms: float) -> None:
        """Record bot response time."""
        entry = {
            "timestamp": datetime.utcnow(),
            "bot_id": bot_id,
            "response_time_ms": response_time_ms,
        }

        with self._lock:
            self._bot_response_times.append(entry)

    def record_websocket_latency(self, connection_id: str, latency_ms: float) -> None:
        """Record WebSocket message latency."""
        entry = {
            "timestamp": datetime.utcnow(),
            "connection_id": connection_id,
            "latency_ms": latency_ms,
        }

        with self._lock:
            self._websocket_latencies.append(entry)

    def get_game_metrics(self) -> Dict[str, Any]:
        """Get game-specific metrics."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_size_seconds)

        with self._lock:
            # Turn metrics
            recent_turns = [
                entry["duration_ms"]
                for entry in self._turn_durations
                if entry["timestamp"] > cutoff
            ]

            # Bot metrics
            recent_bot_times = [
                entry["response_time_ms"]
                for entry in self._bot_response_times
                if entry["timestamp"] > cutoff
            ]

            # WebSocket metrics
            recent_latencies = [
                entry["latency_ms"]
                for entry in self._websocket_latencies
                if entry["timestamp"] > cutoff
            ]

            return {
                "turn_metrics": {
                    "count": len(recent_turns),
                    "avg_ms": statistics.mean(recent_turns) if recent_turns else 0,
                    "max_ms": max(recent_turns) if recent_turns else 0,
                    "p95_ms": self._percentile(recent_turns, 95) if recent_turns else 0,
                },
                "bot_metrics": {
                    "count": len(recent_bot_times),
                    "avg_ms": (
                        statistics.mean(recent_bot_times) if recent_bot_times else 0
                    ),
                    "max_ms": max(recent_bot_times) if recent_bot_times else 0,
                    "within_target": (
                        sum(1 for t in recent_bot_times if 500 <= t <= 1500)
                        / len(recent_bot_times)
                        if recent_bot_times
                        else 0
                    ),
                },
                "websocket_metrics": {
                    "count": len(recent_latencies),
                    "avg_ms": (
                        statistics.mean(recent_latencies) if recent_latencies else 0
                    ),
                    "max_ms": max(recent_latencies) if recent_latencies else 0,
                    "p99_ms": (
                        self._percentile(recent_latencies, 99)
                        if recent_latencies
                        else 0
                    ),
                },
            }

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        idx = int(len(sorted_values) * (percentile / 100))
        return sorted_values[min(idx, len(sorted_values) - 1)]
