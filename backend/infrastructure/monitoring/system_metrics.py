"""
System-level metrics collection.

Monitors memory usage, garbage collection, and system resources.
"""

import gc
import psutil
import asyncio
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import deque
import os

from ..observability.metrics import (
    IMetricsCollector,
    MetricTag,
    Gauge,
    Counter,
    Histogram,
    get_metrics_collector,
)


class SystemMetricsCollector:
    """
    Collects system-level metrics.

    Features:
    - Memory usage tracking
    - Garbage collection monitoring
    - CPU usage tracking
    - Thread/coroutine monitoring
    - File descriptor tracking
    """

    def __init__(
        self,
        metrics_collector: Optional[IMetricsCollector] = None,
        collection_interval: int = 30,  # seconds
    ):
        """Initialize system metrics collector."""
        self.collector = metrics_collector or get_metrics_collector()
        self.collection_interval = collection_interval

        # Get process handle
        self.process = psutil.Process()

        # Historical data
        self._memory_history: deque = deque(maxlen=120)  # 1 hour at 30s intervals
        self._gc_history: deque = deque(maxlen=1000)

        # GC generation stats
        self._last_gc_stats = gc.get_stats()
        self._gc_enabled = gc.isenabled()

        # Start collection
        self._collection_task = threading.Thread(
            target=self._collection_loop, daemon=True
        )
        self._collection_task.start()

        # Register GC callback
        self._register_gc_callback()

    def _collection_loop(self) -> None:
        """Background collection loop."""
        while True:
            try:
                self._collect_metrics()
            except Exception as e:
                # Log error but continue collecting
                print(f"Error collecting system metrics: {e}")

            threading.Event().wait(self.collection_interval)

    def _collect_metrics(self) -> None:
        """Collect all system metrics."""
        timestamp = datetime.utcnow()

        # Memory metrics
        memory_info = self._collect_memory_metrics()
        self._memory_history.append({"timestamp": timestamp, **memory_info})

        # CPU metrics
        self._collect_cpu_metrics()

        # Thread/coroutine metrics
        self._collect_concurrency_metrics()

        # File descriptor metrics
        self._collect_fd_metrics()

        # GC metrics
        self._collect_gc_metrics()

    def _collect_memory_metrics(self) -> Dict[str, float]:
        """Collect memory usage metrics."""
        # Process memory
        mem_info = self.process.memory_info()
        mem_percent = self.process.memory_percent()

        # Convert to MB
        rss_mb = mem_info.rss / (1024 * 1024)
        vms_mb = mem_info.vms / (1024 * 1024)

        # Update gauges
        self.collector.gauge("system.memory.rss_mb", rss_mb)
        self.collector.gauge("system.memory.vms_mb", vms_mb)
        self.collector.gauge("system.memory.percent", mem_percent)

        # System memory
        sys_mem = psutil.virtual_memory()
        self.collector.gauge("system.memory.total_gb", sys_mem.total / (1024**3))
        self.collector.gauge(
            "system.memory.available_gb", sys_mem.available / (1024**3)
        )
        self.collector.gauge("system.memory.used_percent", sys_mem.percent)

        # Python-specific memory
        if hasattr(mem_info, "shared"):
            shared_mb = mem_info.shared / (1024 * 1024)
            self.collector.gauge("system.memory.shared_mb", shared_mb)

        return {"rss_mb": rss_mb, "vms_mb": vms_mb, "percent": mem_percent}

    def _collect_cpu_metrics(self) -> None:
        """Collect CPU usage metrics."""
        # Process CPU
        cpu_percent = self.process.cpu_percent(interval=0.1)
        self.collector.gauge("system.cpu.process_percent", cpu_percent)

        # System CPU
        sys_cpu = psutil.cpu_percent(interval=0.1, percpu=True)
        self.collector.gauge("system.cpu.total_percent", sum(sys_cpu) / len(sys_cpu))

        # CPU count
        self.collector.gauge("system.cpu.count", psutil.cpu_count())

        # Load average (Unix only)
        if hasattr(os, "getloadavg"):
            load1, load5, load15 = os.getloadavg()
            self.collector.gauge("system.load.1min", load1)
            self.collector.gauge("system.load.5min", load5)
            self.collector.gauge("system.load.15min", load15)

    def _collect_concurrency_metrics(self) -> None:
        """Collect thread and coroutine metrics."""
        # Thread count
        thread_count = threading.active_count()
        self.collector.gauge("system.threads.active", thread_count)

        # List all threads
        for thread in threading.enumerate():
            if thread.is_alive():
                self.collector.gauge(
                    "system.threads.info",
                    1,
                    [
                        MetricTag("name", thread.name),
                        MetricTag("daemon", str(thread.daemon)),
                    ],
                )

        # Asyncio tasks (if in async context)
        try:
            loop = asyncio.get_running_loop()
            tasks = asyncio.all_tasks(loop)
            self.collector.gauge("system.asyncio.tasks", len(tasks))

            # Task states
            pending = sum(1 for t in tasks if not t.done())
            done = sum(1 for t in tasks if t.done() and not t.cancelled())
            cancelled = sum(1 for t in tasks if t.cancelled())

            self.collector.gauge("system.asyncio.tasks_pending", pending)
            self.collector.gauge("system.asyncio.tasks_done", done)
            self.collector.gauge("system.asyncio.tasks_cancelled", cancelled)
        except RuntimeError:
            # No running loop
            pass

    def _collect_fd_metrics(self) -> None:
        """Collect file descriptor metrics."""
        try:
            open_files = self.process.open_files()
            self.collector.gauge("system.fd.open_files", len(open_files))

            connections = self.process.connections()
            self.collector.gauge("system.fd.connections", len(connections))

            # Connection types
            conn_types = {}
            for conn in connections:
                conn_type = (
                    f"{conn.type}_{conn.status}"
                    if hasattr(conn, "status")
                    else str(conn.type)
                )
                conn_types[conn_type] = conn_types.get(conn_type, 0) + 1

            for conn_type, count in conn_types.items():
                self.collector.gauge(
                    "system.connections.by_type", count, [MetricTag("type", conn_type)]
                )
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass

    def _collect_gc_metrics(self) -> None:
        """Collect garbage collection metrics."""
        # GC counts
        counts = gc.get_count()
        for i, count in enumerate(counts):
            self.collector.gauge(f"system.gc.objects.gen{i}", count)

        # GC stats
        stats = gc.get_stats()
        for i, gen_stats in enumerate(stats):
            self.collector.gauge(
                f"system.gc.collections.gen{i}", gen_stats.get("collections", 0)
            )
            self.collector.gauge(
                f"system.gc.collected.gen{i}", gen_stats.get("collected", 0)
            )
            self.collector.gauge(
                f"system.gc.uncollectable.gen{i}", gen_stats.get("uncollectable", 0)
            )

    def _register_gc_callback(self) -> None:
        """Register callback for GC events."""
        # This would require gc.callbacks in Python 3.11+
        # For now, we'll track GC stats periodically
        pass

    def record_gc_collection(
        self, generation: int, collected: int, uncollectable: int
    ) -> None:
        """Record a garbage collection event."""
        self.collector.increment(
            "system.gc.events", tags=[MetricTag("generation", str(generation))]
        )

        self.collector.histogram(
            "system.gc.collected_objects",
            collected,
            [MetricTag("generation", str(generation))],
        )

        if uncollectable > 0:
            self.collector.gauge(
                "system.gc.uncollectable_objects",
                uncollectable,
                [MetricTag("generation", str(generation))],
            )

        # Record in history
        self._gc_history.append(
            {
                "timestamp": datetime.utcnow(),
                "generation": generation,
                "collected": collected,
                "uncollectable": uncollectable,
            }
        )

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get memory usage summary."""
        if not self._memory_history:
            return {}

        recent = list(self._memory_history)
        current = recent[-1]

        # Calculate trends
        if len(recent) > 1:
            first = recent[0]
            growth_mb = current["rss_mb"] - first["rss_mb"]
            time_diff = (
                current["timestamp"] - first["timestamp"]
            ).total_seconds() / 3600
            growth_rate_mb_per_hour = growth_mb / time_diff if time_diff > 0 else 0
        else:
            growth_rate_mb_per_hour = 0

        return {
            "current_rss_mb": current["rss_mb"],
            "current_vms_mb": current["vms_mb"],
            "current_percent": current["percent"],
            "growth_rate_mb_per_hour": growth_rate_mb_per_hour,
            "samples": len(recent),
        }

    def get_gc_summary(self) -> Dict[str, Any]:
        """Get garbage collection summary."""
        if not self._gc_history:
            stats = gc.get_stats()
            return {
                "enabled": gc.isenabled(),
                "generations": len(stats),
                "thresholds": gc.get_threshold(),
                "total_collections": sum(s.get("collections", 0) for s in stats),
            }

        # Analyze recent GC events
        recent_events = list(self._gc_history)
        total_collected = sum(e["collected"] for e in recent_events)
        total_uncollectable = sum(e["uncollectable"] for e in recent_events)

        # Group by generation
        by_generation = {}
        for event in recent_events:
            gen = event["generation"]
            if gen not in by_generation:
                by_generation[gen] = {
                    "collections": 0,
                    "collected": 0,
                    "uncollectable": 0,
                }
            by_generation[gen]["collections"] += 1
            by_generation[gen]["collected"] += event["collected"]
            by_generation[gen]["uncollectable"] += event["uncollectable"]

        return {
            "enabled": gc.isenabled(),
            "total_collections": len(recent_events),
            "total_collected": total_collected,
            "total_uncollectable": total_uncollectable,
            "by_generation": by_generation,
            "thresholds": gc.get_threshold(),
        }

    def force_gc_collection(self, generation: Optional[int] = None) -> Dict[str, int]:
        """Force a garbage collection and return stats."""
        before_counts = gc.get_count()

        if generation is not None:
            collected = gc.collect(generation)
        else:
            collected = gc.collect()

        after_counts = gc.get_count()

        # Record the collection
        self.record_gc_collection(
            generation or 2,  # Full collection if not specified
            collected,
            0,  # Can't easily determine uncollectable from gc.collect()
        )

        return {
            "collected": collected,
            "before_counts": before_counts,
            "after_counts": after_counts,
        }

    def set_gc_thresholds(self, gen0: int, gen1: int, gen2: int) -> None:
        """Set garbage collection thresholds."""
        gc.set_threshold(gen0, gen1, gen2)
        self.collector.gauge("system.gc.threshold.gen0", gen0)
        self.collector.gauge("system.gc.threshold.gen1", gen1)
        self.collector.gauge("system.gc.threshold.gen2", gen2)
