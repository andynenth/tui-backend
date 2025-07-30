"""
Grafana dashboard templates for Liap Tui monitoring.

Provides pre-configured dashboard definitions that can be
imported into Grafana for comprehensive system monitoring.
"""

import json
from typing import Dict, Any, List, Optional


def create_panel(
    title: str,
    panel_type: str,
    targets: List[Dict[str, Any]],
    grid_pos: Dict[str, int],
    options: Optional[Dict[str, Any]] = None,
    field_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a Grafana panel configuration."""
    panel = {
        "title": title,
        "type": panel_type,
        "gridPos": grid_pos,
        "datasource": "Prometheus",
        "targets": targets,
        "options": options or {},
        "fieldConfig": field_config
        or {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "red", "value": 80},
                    ],
                },
            },
            "overrides": [],
        },
    }
    return panel


def create_game_overview_dashboard() -> Dict[str, Any]:
    """Create game overview dashboard."""
    return {
        "uid": "liap-tui-game-overview",
        "title": "Liap Tui - Game Overview",
        "tags": ["liap-tui", "games", "overview"],
        "timezone": "browser",
        "refresh": "10s",
        "panels": [
            # Active Games
            create_panel(
                title="Active Games",
                panel_type="stat",
                targets=[{"expr": "liap_tui_games_active", "refId": "A"}],
                grid_pos={"h": 8, "w": 6, "x": 0, "y": 0},
                options={
                    "reduceOptions": {"values": False, "calcs": ["lastNotNull"]},
                    "orientation": "auto",
                    "textMode": "auto",
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                },
            ),
            # Games Per Hour
            create_panel(
                title="Games Per Hour",
                panel_type="gauge",
                targets=[{"expr": "liap_tui_games_per_hour", "refId": "A"}],
                grid_pos={"h": 8, "w": 6, "x": 6, "y": 0},
                options={"showThresholdLabels": False, "showThresholdMarkers": True},
                field_config={
                    "defaults": {
                        "max": 100,
                        "min": 0,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "red", "value": None},
                                {"color": "yellow", "value": 20},
                                {"color": "green", "value": 50},
                            ],
                        },
                        "unit": "games/hr",
                    }
                },
            ),
            # Average Game Duration
            create_panel(
                title="Average Game Duration",
                panel_type="stat",
                targets=[{"expr": "liap_tui_game_duration_minutes", "refId": "A"}],
                grid_pos={"h": 8, "w": 6, "x": 12, "y": 0},
                options={
                    "reduceOptions": {"values": False, "calcs": ["lastNotNull"]},
                    "textMode": "auto",
                    "colorMode": "value",
                    "graphMode": "none",
                },
                field_config={"defaults": {"unit": "m"}},
            ),
            # WebSocket Connections
            create_panel(
                title="WebSocket Connections",
                panel_type="stat",
                targets=[
                    {"expr": "liap_tui_websocket_connections_active", "refId": "A"}
                ],
                grid_pos={"h": 8, "w": 6, "x": 18, "y": 0},
                options={
                    "reduceOptions": {"values": False, "calcs": ["lastNotNull"]},
                    "textMode": "auto",
                    "colorMode": "background",
                    "graphMode": "area",
                },
            ),
            # Games Timeline
            create_panel(
                title="Games Timeline",
                panel_type="timeseries",
                targets=[
                    {
                        "expr": "rate(liap_tui_games_started[5m]) * 300",
                        "legendFormat": "Started",
                        "refId": "A",
                    },
                    {
                        "expr": "rate(liap_tui_games_completed_total[5m]) * 300",
                        "legendFormat": "Completed",
                        "refId": "B",
                    },
                    {
                        "expr": "rate(liap_tui_games_abandoned[5m]) * 300",
                        "legendFormat": "Abandoned",
                        "refId": "C",
                    },
                ],
                grid_pos={"h": 10, "w": 12, "x": 0, "y": 8},
                options={
                    "legend": {
                        "calcs": [],
                        "displayMode": "list",
                        "placement": "bottom",
                    },
                    "tooltip": {"mode": "single"},
                },
            ),
            # Win Rate by Player Type
            create_panel(
                title="Win Rate by Player Type",
                panel_type="bargauge",
                targets=[
                    {
                        "expr": "liap_tui_player_win_rate",
                        "legendFormat": "{{type}}",
                        "refId": "A",
                    }
                ],
                grid_pos={"h": 10, "w": 12, "x": 12, "y": 8},
                options={
                    "orientation": "horizontal",
                    "displayMode": "basic",
                    "showUnfilled": True,
                },
                field_config={"defaults": {"max": 1, "min": 0, "unit": "percentunit"}},
            ),
            # State Distribution
            create_panel(
                title="Games by State",
                panel_type="piechart",
                targets=[
                    {
                        "expr": "liap_tui_state_active_games",
                        "legendFormat": "{{state}}",
                        "refId": "A",
                    }
                ],
                grid_pos={"h": 10, "w": 12, "x": 0, "y": 18},
                options={
                    "pieType": "donut",
                    "displayLabels": ["name", "percent"],
                    "legendDisplayMode": "list",
                    "legendPlacement": "right",
                },
            ),
            # Room Health
            create_panel(
                title="Room Health Status",
                panel_type="bargauge",
                targets=[
                    {
                        "expr": "liap_tui_room_health",
                        "legendFormat": "{{status}}",
                        "refId": "A",
                    }
                ],
                grid_pos={"h": 10, "w": 12, "x": 12, "y": 18},
                options={
                    "orientation": "horizontal",
                    "displayMode": "gradient",
                    "showUnfilled": False,
                },
                field_config={
                    "defaults": {
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 5},
                                {"color": "red", "value": 10},
                            ],
                        }
                    }
                },
            ),
        ],
    }


def create_performance_dashboard() -> Dict[str, Any]:
    """Create performance monitoring dashboard."""
    return {
        "uid": "liap-tui-performance",
        "title": "Liap Tui - Performance Monitoring",
        "tags": ["liap-tui", "performance", "monitoring"],
        "timezone": "browser",
        "refresh": "5s",
        "panels": [
            # Memory Usage
            create_panel(
                title="Memory Usage",
                panel_type="timeseries",
                targets=[
                    {
                        "expr": 'liap_tui_memory_usage_mb{type="rss"}',
                        "legendFormat": "RSS",
                        "refId": "A",
                    },
                    {
                        "expr": 'liap_tui_memory_usage_mb{type="vms"}',
                        "legendFormat": "VMS",
                        "refId": "B",
                    },
                ],
                grid_pos={"h": 10, "w": 12, "x": 0, "y": 0},
                field_config={"defaults": {"unit": "decmbytes"}},
            ),
            # CPU Usage
            create_panel(
                title="CPU Usage",
                panel_type="timeseries",
                targets=[{"expr": "liap_tui_cpu_usage_percent", "refId": "A"}],
                grid_pos={"h": 10, "w": 12, "x": 12, "y": 0},
                field_config={"defaults": {"unit": "percent", "max": 100, "min": 0}},
            ),
            # Garbage Collection
            create_panel(
                title="Garbage Collection Rate",
                panel_type="timeseries",
                targets=[
                    {
                        "expr": "rate(liap_tui_gc_collections_total[5m])",
                        "legendFormat": "Gen {{generation}}",
                        "refId": "A",
                    }
                ],
                grid_pos={"h": 10, "w": 12, "x": 0, "y": 10},
                options={
                    "legend": {
                        "calcs": ["mean", "max"],
                        "displayMode": "table",
                        "placement": "bottom",
                    }
                },
            ),
            # Thread Count
            create_panel(
                title="Active Threads",
                panel_type="stat",
                targets=[{"expr": "liap_tui_threads_active", "refId": "A"}],
                grid_pos={"h": 10, "w": 6, "x": 12, "y": 10},
                options={"graphMode": "area", "textMode": "auto"},
            ),
            # Memory Growth Rate
            create_panel(
                title="Memory Growth Rate",
                panel_type="gauge",
                targets=[{"expr": "liap_tui_memory_growth_rate", "refId": "A"}],
                grid_pos={"h": 10, "w": 6, "x": 18, "y": 10},
                field_config={
                    "defaults": {
                        "unit": "MB/hr",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 10},
                                {"color": "red", "value": 50},
                            ],
                        },
                    }
                },
            ),
            # Action Processing Time
            create_panel(
                title="Action Processing Time",
                panel_type="heatmap",
                targets=[
                    {
                        "expr": "histogram_quantile(0.95, liap_tui_action_processing_time_bucket)",
                        "format": "heatmap",
                        "refId": "A",
                    }
                ],
                grid_pos={"h": 10, "w": 12, "x": 0, "y": 20},
                options={"calculate": False, "yAxis": {"unit": "ms"}},
            ),
            # State Transition Latency
            create_panel(
                title="State Transition Latency (P95)",
                panel_type="timeseries",
                targets=[
                    {
                        "expr": "histogram_quantile(0.95, rate(liap_tui_state_transition_time_bucket[5m]))",
                        "legendFormat": "{{transition}}",
                        "refId": "A",
                    }
                ],
                grid_pos={"h": 10, "w": 12, "x": 12, "y": 20},
                field_config={"defaults": {"unit": "ms"}},
            ),
        ],
    }


def create_state_machine_dashboard() -> Dict[str, Any]:
    """Create state machine monitoring dashboard."""
    return {
        "uid": "liap-tui-state-machine",
        "title": "Liap Tui - State Machine Monitor",
        "tags": ["liap-tui", "state-machine", "monitoring"],
        "timezone": "browser",
        "refresh": "5s",
        "panels": [
            # State Transitions Flow
            create_panel(
                title="State Transitions per Minute",
                panel_type="graph",
                targets=[
                    {
                        "expr": "rate(liap_tui_state_transitions_total[1m]) * 60",
                        "legendFormat": "{{from}} → {{to}}",
                        "refId": "A",
                    }
                ],
                grid_pos={"h": 12, "w": 24, "x": 0, "y": 0},
                options={
                    "legend": {
                        "show": True,
                        "values": True,
                        "current": True,
                        "avg": True,
                    }
                },
            ),
            # Phase Duration Distribution
            create_panel(
                title="Phase Duration Distribution",
                panel_type="boxplot",
                targets=[
                    {
                        "expr": "liap_tui_phase_duration_seconds",
                        "format": "time_series",
                        "refId": "A",
                    }
                ],
                grid_pos={"h": 10, "w": 12, "x": 0, "y": 12},
                field_config={"defaults": {"unit": "s"}},
            ),
            # Error Rate by State
            create_panel(
                title="Error Rate by State",
                panel_type="bargauge",
                targets=[
                    {
                        "expr": "rate(liap_tui_state_errors[5m])",
                        "legendFormat": "{{state}}",
                        "refId": "A",
                    }
                ],
                grid_pos={"h": 10, "w": 12, "x": 12, "y": 12},
                options={"orientation": "horizontal", "displayMode": "gradient"},
                field_config={
                    "defaults": {
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 0.01},
                                {"color": "red", "value": 0.05},
                            ],
                        }
                    }
                },
            ),
            # Current State Distribution
            create_panel(
                title="Current State Distribution",
                panel_type="table",
                targets=[
                    {
                        "expr": "topk(10, liap_tui_state_active_games)",
                        "format": "table",
                        "instant": True,
                        "refId": "A",
                    }
                ],
                grid_pos={"h": 10, "w": 24, "x": 0, "y": 22},
                options={"showHeader": True},
            ),
        ],
    }


def export_all_dashboards() -> Dict[str, Any]:
    """Export all dashboard configurations."""
    return {
        "game_overview": create_game_overview_dashboard(),
        "performance": create_performance_dashboard(),
        "state_machine": create_state_machine_dashboard(),
    }


def save_dashboards_to_file(filepath: str = "grafana_dashboards.json") -> None:
    """Save all dashboards to a JSON file."""
    dashboards = export_all_dashboards()

    with open(filepath, "w") as f:
        json.dump(dashboards, f, indent=2)

    print(f"Dashboards saved to {filepath}")


# Alert rules for Grafana
def create_alert_rules() -> List[Dict[str, Any]]:
    """Create alert rules for Grafana."""
    return [
        {
            "uid": "high-memory-usage",
            "title": "High Memory Usage",
            "condition": 'liap_tui_memory_usage_mb{type="rss"} > 1000',
            "for": "5m",
            "annotations": {
                "summary": "Memory usage is above 1GB",
                "description": "RSS memory usage is {{ $value }}MB",
            },
        },
        {
            "uid": "high-error-rate",
            "title": "High Error Rate",
            "condition": "rate(liap_tui_state_errors[5m]) > 0.1",
            "for": "5m",
            "annotations": {
                "summary": "Error rate is above 10%",
                "description": "State {{ $labels.state }} has error rate {{ $value }}",
            },
        },
        {
            "uid": "no-active-games",
            "title": "No Active Games",
            "condition": "liap_tui_games_active == 0",
            "for": "30m",
            "annotations": {
                "summary": "No active games for 30 minutes",
                "description": "System appears to be idle",
            },
        },
        {
            "uid": "websocket-connection-drop",
            "title": "WebSocket Connection Drop",
            "condition": "rate(liap_tui_websocket_connections_closed[5m]) > rate(liap_tui_websocket_connections_opened[5m])",
            "for": "10m",
            "annotations": {
                "summary": "More WebSocket closures than openings",
                "description": "Potential connectivity issues",
            },
        },
    ]


from typing import Optional  # Import was missing
