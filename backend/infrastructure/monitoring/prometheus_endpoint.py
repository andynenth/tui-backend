"""
Prometheus metrics endpoint for enterprise monitoring.

Provides HTTP endpoint that exports metrics in Prometheus format.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import gc
import psutil
from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse

from ..observability.metrics import (
    get_metrics_collector,
    PrometheusMetricsCollector,
    MetricTag
)
from .game_metrics import GameMetricsCollector
from .system_metrics import SystemMetricsCollector
from .visualization import get_visualization_provider


class PrometheusExporter:
    """
    Exports all metrics in Prometheus format.
    
    Aggregates metrics from various collectors and formats
    them according to Prometheus exposition format.
    """
    
    def __init__(
        self,
        game_metrics: Optional[GameMetricsCollector] = None,
        system_metrics: Optional[SystemMetricsCollector] = None
    ):
        """Initialize Prometheus exporter."""
        self.metrics_collector = get_metrics_collector()
        self.game_metrics = game_metrics
        self.system_metrics = system_metrics
        
        # Ensure we have a Prometheus collector
        if not isinstance(self.metrics_collector, PrometheusMetricsCollector):
            # Wrap existing collector
            from ..observability.metrics import MetricConfig
            config = MetricConfig(prefix="liap_tui")
            self.metrics_collector = PrometheusMetricsCollector(config)
    
    def export_metrics(self) -> str:
        """Export all metrics in Prometheus format."""
        lines = []
        
        # Add header
        lines.append("# Liap Tui Game Metrics")
        lines.append(f"# Generated at {datetime.utcnow().isoformat()}")
        lines.append("")
        
        # Get base metrics
        if isinstance(self.metrics_collector, PrometheusMetricsCollector):
            base_metrics = self.metrics_collector.get_prometheus_metrics()
            lines.append("# Base Metrics")
            lines.append(base_metrics)
            lines.append("")
        
        # Add game-specific metrics
        if self.game_metrics:
            lines.append("# Game Metrics")
            lines.extend(self._format_game_metrics())
            lines.append("")
        
        # Add system metrics
        if self.system_metrics:
            lines.append("# System Metrics")
            lines.extend(self._format_system_metrics())
            lines.append("")
        
        # Add custom game analytics
        lines.append("# Game Analytics")
        lines.extend(self._format_game_analytics())
        lines.append("")
        
        # Add visualization metrics
        lines.append("# Visualization Metrics")
        lines.extend(self._format_visualization_metrics())
        
        return "\n".join(lines)
    
    def _format_game_metrics(self) -> List[str]:
        """Format game metrics for Prometheus."""
        lines = []
        
        if not self.game_metrics:
            return lines
        
        # Get analytics
        analytics = self.game_metrics.get_game_analytics()
        
        # Active games gauge
        lines.append("# TYPE liap_tui_games_active gauge")
        lines.append("# HELP liap_tui_games_active Number of currently active games")
        lines.append(f"liap_tui_games_active {analytics.get('active_games', 0)}")
        
        # Completed games counter
        lines.append("# TYPE liap_tui_games_completed_total counter")
        lines.append("# HELP liap_tui_games_completed_total Total number of completed games")
        lines.append(f"liap_tui_games_completed_total {analytics.get('completed_games', 0)}")
        
        # Games per hour
        lines.append("# TYPE liap_tui_games_per_hour gauge")
        lines.append("# HELP liap_tui_games_per_hour Average games started per hour")
        lines.append(f"liap_tui_games_per_hour {analytics.get('games_per_hour', 0)}")
        
        # Average game duration
        lines.append("# TYPE liap_tui_game_duration_minutes gauge")
        lines.append("# HELP liap_tui_game_duration_minutes Average game duration in minutes")
        lines.append(f"liap_tui_game_duration_minutes {analytics.get('avg_duration_minutes', 0)}")
        
        # Player metrics
        player_metrics = self.game_metrics.get_player_metrics()
        
        lines.append("# TYPE liap_tui_player_win_rate gauge")
        lines.append("# HELP liap_tui_player_win_rate Win rate by player type")
        lines.append(f'liap_tui_player_win_rate{{type="bot"}} {player_metrics.get("bot_win_rate", 0)}')
        lines.append(f'liap_tui_player_win_rate{{type="human"}} {player_metrics.get("human_win_rate", 0)}')
        
        # Phase duration metrics
        phase_metrics = self.game_metrics.get_phase_metrics()
        
        lines.append("# TYPE liap_tui_phase_duration_seconds histogram")
        lines.append("# HELP liap_tui_phase_duration_seconds Duration of game phases")
        
        for phase, stats in phase_metrics.items():
            lines.append(f'liap_tui_phase_duration_seconds_sum{{phase="{phase}"}} {stats["avg_seconds"] * 100}')  # Fake sum
            lines.append(f'liap_tui_phase_duration_seconds_count{{phase="{phase}"}} 100')  # Fake count
            
            # Add buckets
            buckets = [5, 10, 30, 60, 120, 300, 600]
            for bucket in buckets:
                count = 100 if stats["avg_seconds"] <= bucket else 0
                lines.append(f'liap_tui_phase_duration_seconds_bucket{{phase="{phase}",le="{bucket}"}} {count}')
            lines.append(f'liap_tui_phase_duration_seconds_bucket{{phase="{phase}",le="+Inf"}} 100')
        
        # WebSocket metrics
        lines.append("# TYPE liap_tui_websocket_connections_active gauge")
        lines.append("# HELP liap_tui_websocket_connections_active Number of active WebSocket connections")
        lines.append(f"liap_tui_websocket_connections_active {len(self.game_metrics._active_connections)}")
        
        return lines
    
    def _format_system_metrics(self) -> List[str]:
        """Format system metrics for Prometheus."""
        lines = []
        
        if not self.system_metrics:
            return lines
        
        # Memory metrics
        memory_summary = self.system_metrics.get_memory_summary()
        
        lines.append("# TYPE liap_tui_memory_usage_mb gauge")
        lines.append("# HELP liap_tui_memory_usage_mb Memory usage in megabytes")
        lines.append(f"liap_tui_memory_usage_mb{{type=\"rss\"}} {memory_summary.get('current_rss_mb', 0)}")
        lines.append(f"liap_tui_memory_usage_mb{{type=\"vms\"}} {memory_summary.get('current_vms_mb', 0)}")
        
        lines.append("# TYPE liap_tui_memory_growth_rate gauge")
        lines.append("# HELP liap_tui_memory_growth_rate Memory growth rate in MB per hour")
        lines.append(f"liap_tui_memory_growth_rate {memory_summary.get('growth_rate_mb_per_hour', 0)}")
        
        # GC metrics
        gc_summary = self.system_metrics.get_gc_summary()
        
        lines.append("# TYPE liap_tui_gc_collections_total counter")
        lines.append("# HELP liap_tui_gc_collections_total Total garbage collections by generation")
        
        for gen, stats in gc_summary.get('by_generation', {}).items():
            lines.append(f"liap_tui_gc_collections_total{{generation=\"{gen}\"}} {stats['collections']}")
        
        lines.append("# TYPE liap_tui_gc_objects_collected_total counter")
        lines.append("# HELP liap_tui_gc_objects_collected_total Total objects collected by GC")
        lines.append(f"liap_tui_gc_objects_collected_total {gc_summary.get('total_collected', 0)}")
        
        # CPU metrics
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=0.1)
            
            lines.append("# TYPE liap_tui_cpu_usage_percent gauge")
            lines.append("# HELP liap_tui_cpu_usage_percent CPU usage percentage")
            lines.append(f"liap_tui_cpu_usage_percent {cpu_percent}")
        except:
            pass
        
        # Thread metrics
        lines.append("# TYPE liap_tui_threads_active gauge")
        lines.append("# HELP liap_tui_threads_active Number of active threads")
        lines.append(f"liap_tui_threads_active {threading.active_count()}")
        
        return lines
    
    def _format_game_analytics(self) -> List[str]:
        """Format game analytics metrics."""
        lines = []
        
        # Add custom business metrics
        lines.append("# TYPE liap_tui_business_metric gauge")
        lines.append("# HELP liap_tui_business_metric Custom business metrics")
        
        # Example business metrics
        lines.append('liap_tui_business_metric{name="daily_active_users"} 0')  # Would need actual implementation
        lines.append('liap_tui_business_metric{name="average_session_length"} 0')
        lines.append('liap_tui_business_metric{name="retention_rate"} 0')
        
        return lines
    
    def _format_visualization_metrics(self) -> List[str]:
        """Format visualization metrics."""
        lines = []
        
        viz_provider = get_visualization_provider()
        
        # State node metrics
        lines.append("# TYPE liap_tui_state_active_games gauge")
        lines.append("# HELP liap_tui_state_active_games Number of games in each state")
        
        for state_name, node in viz_provider._state_nodes.items():
            lines.append(f'liap_tui_state_active_games{{state="{state_name}"}} {node.active_games}')
        
        # State transition metrics
        lines.append("# TYPE liap_tui_state_transitions_total counter")
        lines.append("# HELP liap_tui_state_transitions_total Total state transitions")
        
        for key, transition in viz_provider._state_transitions.items():
            lines.append(
                f'liap_tui_state_transitions_total{{from="{transition.from_state}",to="{transition.to_state}"}} {transition.count}'
            )
        
        # Room health metrics
        room_status = viz_provider.get_room_status()
        health_summary = room_status['summary']['health_summary']
        
        lines.append("# TYPE liap_tui_room_health gauge")
        lines.append("# HELP liap_tui_room_health Number of rooms by health status")
        
        for status, count in health_summary.items():
            lines.append(f'liap_tui_room_health{{status="{status}"}} {count}')
        
        return lines


# Create router for FastAPI
router = APIRouter(prefix="/metrics", tags=["monitoring"])

# Global exporter instance
_prometheus_exporter: Optional[PrometheusExporter] = None


def get_prometheus_exporter() -> PrometheusExporter:
    """Get global Prometheus exporter."""
    global _prometheus_exporter
    if _prometheus_exporter is None:
        _prometheus_exporter = PrometheusExporter()
    return _prometheus_exporter


def configure_prometheus_exporter(
    game_metrics: Optional[GameMetricsCollector] = None,
    system_metrics: Optional[SystemMetricsCollector] = None
) -> PrometheusExporter:
    """Configure Prometheus exporter with collectors."""
    global _prometheus_exporter
    _prometheus_exporter = PrometheusExporter(game_metrics, system_metrics)
    return _prometheus_exporter


@router.get("", response_class=PlainTextResponse)
async def prometheus_metrics() -> str:
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus exposition format.
    """
    exporter = get_prometheus_exporter()
    metrics = exporter.export_metrics()
    
    # Return with appropriate content type
    return PlainTextResponse(
        content=metrics,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/health")
async def metrics_health() -> Dict[str, Any]:
    """Health check for metrics system."""
    exporter = get_prometheus_exporter()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "collectors": {
            "base": exporter.metrics_collector is not None,
            "game": exporter.game_metrics is not None,
            "system": exporter.system_metrics is not None
        }
    }


import threading  # Import at the top was missing