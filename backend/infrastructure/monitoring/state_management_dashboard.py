"""
State Management Monitoring Dashboard Configuration.

This module defines metrics, dashboards, and alerts for monitoring
the state persistence system in production.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class MetricDefinition:
    """Definition of a metric to track."""
    name: str
    type: str  # counter, gauge, histogram
    description: str
    labels: List[str]
    unit: str = ""


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    metric: str
    condition: str
    threshold: float
    duration: timedelta
    severity: str  # critical, warning, info
    description: str


# Core metrics to track
STATE_METRICS = [
    MetricDefinition(
        name="state_transitions_total",
        type="counter",
        description="Total number of state transitions",
        labels=["game_id", "from_phase", "to_phase", "success"],
    ),
    MetricDefinition(
        name="state_snapshots_total",
        type="counter",
        description="Total number of state snapshots created",
        labels=["game_id", "trigger", "success"],
    ),
    MetricDefinition(
        name="state_recoveries_total",
        type="counter",
        description="Total number of state recovery attempts",
        labels=["game_id", "recovery_type", "success"],
    ),
    MetricDefinition(
        name="state_operation_duration_ms",
        type="histogram",
        description="Duration of state operations in milliseconds",
        labels=["operation", "storage_backend"],
        unit="milliseconds",
    ),
    MetricDefinition(
        name="state_cache_operations",
        type="counter",
        description="Cache operations for state management",
        labels=["operation", "hit"],
    ),
    MetricDefinition(
        name="state_storage_size_bytes",
        type="gauge",
        description="Size of state storage in bytes",
        labels=["storage_type", "game_id"],
        unit="bytes",
    ),
    MetricDefinition(
        name="active_games_with_state",
        type="gauge",
        description="Number of active games with state persistence",
        labels=["phase"],
    ),
    MetricDefinition(
        name="state_errors_total",
        type="counter",
        description="Total number of state management errors",
        labels=["operation", "error_type"],
    ),
    MetricDefinition(
        name="circuit_breaker_state",
        type="gauge",
        description="Circuit breaker state (0=closed, 1=open, 2=half-open)",
        labels=["component"],
    ),
]


# Alert rules for production monitoring
ALERT_RULES = [
    AlertRule(
        name="HighStateErrorRate",
        metric="rate(state_errors_total[5m])",
        condition=">",
        threshold=0.05,
        duration=timedelta(minutes=5),
        severity="critical",
        description="State management error rate above 5%",
    ),
    AlertRule(
        name="StateRecoveryFailures",
        metric="rate(state_recoveries_total{success='false'}[10m])",
        condition=">",
        threshold=0.01,
        duration=timedelta(minutes=10),
        severity="critical",
        description="State recovery failure rate above 1%",
    ),
    AlertRule(
        name="SlowStateOperations",
        metric="histogram_quantile(0.99, state_operation_duration_ms)",
        condition=">",
        threshold=100,
        duration=timedelta(minutes=5),
        severity="warning",
        description="99th percentile state operation latency above 100ms",
    ),
    AlertRule(
        name="LowCacheHitRate",
        metric="rate(state_cache_operations{hit='true'}[5m]) / rate(state_cache_operations[5m])",
        condition="<",
        threshold=0.8,
        duration=timedelta(minutes=10),
        severity="warning",
        description="State cache hit rate below 80%",
    ),
    AlertRule(
        name="CircuitBreakerOpen",
        metric="circuit_breaker_state",
        condition="==",
        threshold=1,
        duration=timedelta(minutes=1),
        severity="critical",
        description="State management circuit breaker is open",
    ),
    AlertRule(
        name="HighStorageUsage",
        metric="sum(state_storage_size_bytes)",
        condition=">",
        threshold=10 * 1024 * 1024 * 1024,  # 10GB
        duration=timedelta(minutes=30),
        severity="warning",
        description="State storage size exceeds 10GB",
    ),
]


def get_grafana_dashboard() -> Dict[str, Any]:
    """
    Get Grafana dashboard configuration for state management.
    
    Returns a dashboard JSON that can be imported into Grafana.
    """
    return {
        "dashboard": {
            "title": "State Management Dashboard",
            "tags": ["game", "state", "persistence"],
            "timezone": "browser",
            "refresh": "30s",
            "panels": [
                # Row 1: Overview
                {
                    "gridPos": {"x": 0, "y": 0, "w": 8, "h": 6},
                    "title": "State Transitions",
                    "targets": [{
                        "expr": "rate(state_transitions_total[5m])",
                        "legendFormat": "{{from_phase}} → {{to_phase}}"
                    }],
                    "type": "graph",
                },
                {
                    "gridPos": {"x": 8, "y": 0, "w": 8, "h": 6},
                    "title": "Active Games",
                    "targets": [{
                        "expr": "sum(active_games_with_state) by (phase)",
                        "legendFormat": "{{phase}}"
                    }],
                    "type": "graph",
                },
                {
                    "gridPos": {"x": 16, "y": 0, "w": 8, "h": 6},
                    "title": "Error Rate",
                    "targets": [{
                        "expr": "rate(state_errors_total[5m])",
                        "legendFormat": "{{operation}} - {{error_type}}"
                    }],
                    "type": "graph",
                },
                
                # Row 2: Performance
                {
                    "gridPos": {"x": 0, "y": 6, "w": 12, "h": 6},
                    "title": "Operation Latency (p50, p95, p99)",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.5, state_operation_duration_ms)",
                            "legendFormat": "p50"
                        },
                        {
                            "expr": "histogram_quantile(0.95, state_operation_duration_ms)",
                            "legendFormat": "p95"
                        },
                        {
                            "expr": "histogram_quantile(0.99, state_operation_duration_ms)",
                            "legendFormat": "p99"
                        }
                    ],
                    "type": "graph",
                    "yaxes": [{"format": "ms"}],
                },
                {
                    "gridPos": {"x": 12, "y": 6, "w": 12, "h": 6},
                    "title": "Cache Performance",
                    "targets": [
                        {
                            "expr": "rate(state_cache_operations{hit='true'}[5m])",
                            "legendFormat": "Hits"
                        },
                        {
                            "expr": "rate(state_cache_operations{hit='false'}[5m])",
                            "legendFormat": "Misses"
                        }
                    ],
                    "type": "graph",
                },
                
                # Row 3: Storage and Recovery
                {
                    "gridPos": {"x": 0, "y": 12, "w": 8, "h": 6},
                    "title": "Snapshot Creation",
                    "targets": [{
                        "expr": "rate(state_snapshots_total[5m])",
                        "legendFormat": "{{trigger}} - {{success}}"
                    }],
                    "type": "graph",
                },
                {
                    "gridPos": {"x": 8, "y": 12, "w": 8, "h": 6},
                    "title": "Recovery Attempts",
                    "targets": [{
                        "expr": "rate(state_recoveries_total[5m])",
                        "legendFormat": "{{recovery_type}} - {{success}}"
                    }],
                    "type": "graph",
                },
                {
                    "gridPos": {"x": 16, "y": 12, "w": 8, "h": 6},
                    "title": "Storage Usage",
                    "targets": [{
                        "expr": "sum(state_storage_size_bytes) by (storage_type)",
                        "legendFormat": "{{storage_type}}"
                    }],
                    "type": "graph",
                    "yaxes": [{"format": "bytes"}],
                },
                
                # Row 4: Circuit Breaker Status
                {
                    "gridPos": {"x": 0, "y": 18, "w": 24, "h": 4},
                    "title": "Circuit Breaker Status",
                    "targets": [{
                        "expr": "circuit_breaker_state",
                        "legendFormat": "{{component}}"
                    }],
                    "type": "stat",
                    "options": {
                        "colorMode": "value",
                        "graphMode": "none",
                        "justifyMode": "center",
                        "orientation": "horizontal",
                        "reduceOptions": {
                            "calcs": ["lastNotNull"],
                            "fields": "",
                            "values": false
                        },
                        "textMode": "value_and_name"
                    },
                    "mappings": [
                        {"value": 0, "text": "Closed", "color": "green"},
                        {"value": 1, "text": "Open", "color": "red"},
                        {"value": 2, "text": "Half-Open", "color": "yellow"}
                    ],
                },
            ],
        }
    }


def get_prometheus_recording_rules() -> List[Dict[str, Any]]:
    """
    Get Prometheus recording rules for pre-aggregated metrics.
    
    These rules create pre-computed metrics for better query performance.
    """
    return [
        {
            "record": "state:transitions_per_second",
            "expr": "rate(state_transitions_total[5m])",
        },
        {
            "record": "state:error_rate",
            "expr": "rate(state_errors_total[5m]) / rate(state_transitions_total[5m])",
        },
        {
            "record": "state:cache_hit_rate",
            "expr": "rate(state_cache_operations{hit='true'}[5m]) / rate(state_cache_operations[5m])",
        },
        {
            "record": "state:operation_latency_p99",
            "expr": "histogram_quantile(0.99, rate(state_operation_duration_ms[5m]))",
        },
        {
            "record": "state:recovery_success_rate",
            "expr": "rate(state_recoveries_total{success='true'}[10m]) / rate(state_recoveries_total[10m])",
        },
    ]


def get_datadog_monitors() -> List[Dict[str, Any]]:
    """
    Get Datadog monitor configurations.
    
    For teams using Datadog instead of Prometheus/Grafana.
    """
    return [
        {
            "name": "State Management Error Rate",
            "type": "metric alert",
            "query": "avg(last_5m):rate(custom.state.errors.total) > 0.05",
            "message": "State management error rate is above 5%! Check logs for details.",
            "tags": ["team:backend", "service:state-persistence"],
            "priority": 1,
        },
        {
            "name": "State Operation Latency",
            "type": "metric alert",
            "query": "avg(last_5m):avg:custom.state.operation.duration{percentile:0.99} > 100",
            "message": "State operation p99 latency exceeds 100ms",
            "tags": ["team:backend", "service:state-persistence"],
            "priority": 2,
        },
    ]


def get_logging_queries() -> Dict[str, str]:
    """
    Get useful logging queries for troubleshooting.
    
    These can be used in your log aggregation system (ELK, Splunk, etc).
    """
    return {
        "state_errors": 'logger:"infrastructure.state_persistence" AND level:ERROR',
        "slow_operations": 'logger:"infrastructure.state_persistence" AND duration_ms:>100',
        "recovery_failures": 'message:"Failed to recover state" OR message:"Recovery failed"',
        "circuit_breaker_trips": 'message:"Circuit breaker opened" OR message:"Circuit breaker state changed"',
        "snapshot_failures": 'message:"Failed to create snapshot" OR message:"Snapshot failed"',
        "cache_misses": 'message:"State cache miss" AND game_id:*',
    }