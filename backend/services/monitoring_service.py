# backend/services/monitoring_service.py
"""
Monitoring service for tracking API metrics and performance.
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Thread-safe metrics collector for API performance monitoring.
    """
    
    def __init__(self, window_size_minutes: int = 60):
        self.window_size = timedelta(minutes=window_size_minutes)
        self._lock = threading.Lock()
        
        # Metrics storage
        self.request_counts = defaultdict(int)
        self.response_times = defaultdict(lambda: deque(maxlen=1000))
        self.error_counts = defaultdict(int)
        self.cache_hits = defaultdict(int)
        self.cache_misses = defaultdict(int)
        self.slow_requests = defaultdict(int)
        
        # Time series data for graphs
        self.time_series_data = defaultdict(lambda: deque(maxlen=3600))  # 1 hour of second-by-second data
    
    def record_request(self, endpoint: str, method: str, status_code: int, duration_ms: float):
        """Record API request metrics."""
        with self._lock:
            key = f"{method}:{endpoint}"
            self.request_counts[key] += 1
            self.response_times[key].append(duration_ms)
            
            # Track errors
            if status_code >= 400:
                self.error_counts[key] += 1
            
            # Track slow requests
            if duration_ms > 1000:  # > 1 second
                self.slow_requests[key] += 1
            
            # Time series data
            timestamp = time.time()
            self.time_series_data[key].append({
                "timestamp": timestamp,
                "duration_ms": duration_ms,
                "status_code": status_code
            })
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit."""
        with self._lock:
            self.cache_hits[cache_type] += 1
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss."""
        with self._lock:
            self.cache_misses[cache_type] += 1
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        with self._lock:
            summary = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "window_size_minutes": self.window_size.total_seconds() / 60,
                "endpoints": {},
                "cache": {},
                "overall": {
                    "total_requests": sum(self.request_counts.values()),
                    "total_errors": sum(self.error_counts.values()),
                    "total_slow_requests": sum(self.slow_requests.values()),
                }
            }
            
            # Endpoint metrics
            for key, count in self.request_counts.items():
                response_times = list(self.response_times[key])
                if response_times:
                    avg_time = sum(response_times) / len(response_times)
                    p50 = sorted(response_times)[len(response_times) // 2]
                    p95 = sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max(response_times)
                    p99 = sorted(response_times)[int(len(response_times) * 0.99)] if len(response_times) > 100 else max(response_times)
                else:
                    avg_time = p50 = p95 = p99 = 0
                
                summary["endpoints"][key] = {
                    "request_count": count,
                    "error_count": self.error_counts.get(key, 0),
                    "error_rate": self.error_counts.get(key, 0) / count if count > 0 else 0,
                    "slow_request_count": self.slow_requests.get(key, 0),
                    "avg_response_time_ms": round(avg_time, 2),
                    "p50_response_time_ms": round(p50, 2),
                    "p95_response_time_ms": round(p95, 2),
                    "p99_response_time_ms": round(p99, 2),
                }
            
            # Cache metrics
            for cache_type in set(list(self.cache_hits.keys()) + list(self.cache_misses.keys())):
                hits = self.cache_hits.get(cache_type, 0)
                misses = self.cache_misses.get(cache_type, 0)
                total = hits + misses
                
                summary["cache"][cache_type] = {
                    "hits": hits,
                    "misses": misses,
                    "hit_rate": hits / total if total > 0 else 0,
                }
            
            return summary
    
    def get_time_series_data(self, endpoint: str, minutes: int = 5) -> list:
        """Get time series data for an endpoint."""
        with self._lock:
            key = f"GET:{endpoint}"  # Default to GET
            data = list(self.time_series_data.get(key, []))
            
            # Filter to requested time window
            cutoff_time = time.time() - (minutes * 60)
            filtered_data = [d for d in data if d["timestamp"] > cutoff_time]
            
            return filtered_data
    
    def reset_metrics(self):
        """Reset all metrics."""
        with self._lock:
            self.request_counts.clear()
            self.response_times.clear()
            self.error_counts.clear()
            self.cache_hits.clear()
            self.cache_misses.clear()
            self.slow_requests.clear()
            self.time_series_data.clear()


class PlayHistoryMetrics:
    """
    Specialized metrics for play history endpoints.
    """
    
    def __init__(self):
        self.metrics = MetricsCollector()
        
        # Specialized counters
        self.rounds_processed = 0
        self.total_response_size = 0
        self.format_usage = defaultdict(int)
        self.rounds_per_request = []
    
    def record_play_history_request(
        self,
        room_id: str,
        total_rounds: int,
        response_size: int,
        build_time_ms: float,
        format: str = "full"
    ):
        """Record play history specific metrics."""
        self.rounds_processed += total_rounds
        self.total_response_size += response_size
        self.format_usage[format] += 1
        self.rounds_per_request.append(total_rounds)
        
        # Log if response is large
        if response_size > 1_000_000:  # 1MB
            logger.warning(
                f"Large play history response",
                extra={
                    "room_id": room_id,
                    "response_size_bytes": response_size,
                    "total_rounds": total_rounds,
                    "format": format
                }
            )
    
    def get_play_history_stats(self) -> Dict[str, Any]:
        """Get play history specific statistics."""
        if not self.rounds_per_request:
            return {
                "total_rounds_processed": 0,
                "avg_rounds_per_request": 0,
                "total_response_size_mb": 0,
                "format_usage": {}
            }
        
        return {
            "total_rounds_processed": self.rounds_processed,
            "avg_rounds_per_request": sum(self.rounds_per_request) / len(self.rounds_per_request),
            "max_rounds_per_request": max(self.rounds_per_request),
            "total_response_size_mb": round(self.total_response_size / 1_000_000, 2),
            "format_usage": dict(self.format_usage),
            "requests_processed": len(self.rounds_per_request)
        }


# Global metrics instance
metrics_collector = MetricsCollector()
play_history_metrics = PlayHistoryMetrics()