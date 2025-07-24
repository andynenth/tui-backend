#!/usr/bin/env python3
"""
Adapter Metrics Collector
Collects and reports metrics for adapter system performance
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import json
import os
from dataclasses import dataclass, asdict


@dataclass
class AdapterMetric:
    """Single metric data point"""
    event_type: str
    timestamp: float
    duration_ms: float
    success: bool
    adapter_handled: bool
    error: Optional[str] = None


class MetricsCollector:
    """Collects and analyzes adapter system metrics"""
    
    def __init__(self):
        self.metrics: List[AdapterMetric] = []
        self.start_time = time.time()
        self.event_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.duration_buckets = defaultdict(list)
        
    def record_metric(self, metric: AdapterMetric):
        """Record a single metric"""
        self.metrics.append(metric)
        self.event_counts[metric.event_type] += 1
        
        if not metric.success:
            self.error_counts[metric.event_type] += 1
            
        if metric.adapter_handled:
            self.duration_buckets[metric.event_type].append(metric.duration_ms)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        runtime = time.time() - self.start_time
        total_events = len(self.metrics)
        adapter_events = sum(1 for m in self.metrics if m.adapter_handled)
        
        # Calculate percentiles for each event type
        percentiles = {}
        for event_type, durations in self.duration_buckets.items():
            if durations:
                sorted_durations = sorted(durations)
                n = len(sorted_durations)
                percentiles[event_type] = {
                    "p50": sorted_durations[n // 2],
                    "p95": sorted_durations[int(n * 0.95)] if n > 1 else sorted_durations[0],
                    "p99": sorted_durations[int(n * 0.99)] if n > 1 else sorted_durations[0],
                    "avg": sum(durations) / n,
                    "min": min(durations),
                    "max": max(durations)
                }
        
        return {
            "runtime_seconds": runtime,
            "total_events": total_events,
            "adapter_handled": adapter_events,
            "adapter_percentage": (adapter_events / total_events * 100) if total_events > 0 else 0,
            "event_counts": dict(self.event_counts),
            "error_counts": dict(self.error_counts),
            "performance_percentiles": percentiles,
            "error_rate": (sum(self.error_counts.values()) / total_events * 100) if total_events > 0 else 0
        }
    
    def generate_report(self) -> str:
        """Generate a detailed metrics report"""
        summary = self.get_summary()
        
        report = []
        report.append("\n📊 Adapter Metrics Report")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Runtime: {summary['runtime_seconds']:.1f} seconds")
        report.append("")
        
        # Overall statistics
        report.append("📈 Overall Statistics:")
        report.append(f"  Total Events: {summary['total_events']:,}")
        report.append(f"  Adapter Handled: {summary['adapter_handled']:,} ({summary['adapter_percentage']:.1f}%)")
        report.append(f"  Error Rate: {summary['error_rate']:.2f}%")
        report.append("")
        
        # Event breakdown
        report.append("📋 Event Breakdown:")
        report.append("-" * 70)
        report.append(f"{'Event Type':<20} {'Count':<10} {'Errors':<10} {'Error %':<10}")
        report.append("-" * 70)
        
        for event_type, count in sorted(summary['event_counts'].items()):
            errors = summary['error_counts'].get(event_type, 0)
            error_pct = (errors / count * 100) if count > 0 else 0
            report.append(f"{event_type:<20} {count:<10} {errors:<10} {error_pct:<10.1f}")
        
        report.append("")
        
        # Performance analysis
        if summary['performance_percentiles']:
            report.append("⚡ Performance Analysis (ms):")
            report.append("-" * 70)
            report.append(f"{'Event Type':<20} {'Avg':<8} {'P50':<8} {'P95':<8} {'P99':<8} {'Max':<8}")
            report.append("-" * 70)
            
            for event_type, stats in sorted(summary['performance_percentiles'].items()):
                report.append(
                    f"{event_type:<20} "
                    f"{stats['avg']:<8.2f} "
                    f"{stats['p50']:<8.2f} "
                    f"{stats['p95']:<8.2f} "
                    f"{stats['p99']:<8.2f} "
                    f"{stats['max']:<8.2f}"
                )
        
        return "\n".join(report)
    
    def export_metrics(self, filename: str):
        """Export metrics to JSON file"""
        data = {
            "summary": self.get_summary(),
            "metrics": [asdict(m) for m in self.metrics[-1000:]]  # Last 1000 events
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


# Global metrics collector instance
metrics_collector = MetricsCollector()


async def simulate_adapter_metrics(duration_seconds: int = 60):
    """Simulate adapter metrics for testing"""
    print(f"📊 Simulating adapter metrics for {duration_seconds} seconds...")
    
    event_types = ["ping", "create_room", "join_room", "play", "declare"]
    
    start_time = time.time()
    events_generated = 0
    
    while time.time() - start_time < duration_seconds:
        # Simulate events at different rates
        for event_type in event_types:
            # Different events have different frequencies
            if event_type == "ping" or (time.time() % 5 < 1):
                # Simulate metric
                duration = 0.5 + (hash(f"{time.time()}{event_type}") % 100) / 100  # 0.5-1.5ms
                success = hash(f"{time.time()}{event_type}success") % 100 > 2  # 98% success
                adapter_handled = hash(f"{time.time()}{event_type}adapter") % 100 < 75  # 75% adapter
                
                metric = AdapterMetric(
                    event_type=event_type,
                    timestamp=time.time(),
                    duration_ms=duration,
                    success=success,
                    adapter_handled=adapter_handled,
                    error="Simulated error" if not success else None
                )
                
                metrics_collector.record_metric(metric)
                events_generated += 1
        
        # Small delay to simulate realistic traffic
        await asyncio.sleep(0.1)
    
    print(f"✅ Generated {events_generated} events")


async def main():
    """Run metrics collection and reporting"""
    print("🔍 Adapter Metrics Collector")
    print("=" * 70)
    
    # Check adapter status
    adapter_enabled = os.getenv("ADAPTER_ENABLED", "false").lower() == "true"
    rollout_percentage = int(os.getenv("ADAPTER_ROLLOUT_PERCENTAGE", "0"))
    
    print(f"Current Configuration:")
    print(f"  Adapter Enabled: {adapter_enabled}")
    print(f"  Rollout Percentage: {rollout_percentage}%")
    print("")
    
    if not adapter_enabled:
        print("⚠️  Adapters are not enabled. Simulating metrics...")
        print("")
    
    # Simulate metrics collection
    await simulate_adapter_metrics(duration_seconds=10)
    
    # Generate report
    report = metrics_collector.generate_report()
    print(report)
    
    # Export metrics
    export_file = f"adapter_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    metrics_collector.export_metrics(export_file)
    print(f"\n📄 Metrics exported to: {export_file}")
    
    # Performance recommendations
    summary = metrics_collector.get_summary()
    print("\n🎯 Recommendations:")
    
    if summary['error_rate'] > 1:
        print("  ⚠️  High error rate detected - investigate errors before increasing rollout")
    else:
        print("  ✅ Error rate is acceptable")
    
    # Check performance
    all_averages = []
    for stats in summary['performance_percentiles'].values():
        all_averages.append(stats['avg'])
    
    if all_averages:
        overall_avg = sum(all_averages) / len(all_averages)
        if overall_avg < 2:
            print("  ✅ Excellent performance - average overhead < 2ms")
        elif overall_avg < 5:
            print("  ✅ Good performance - average overhead < 5ms")
        else:
            print("  ⚠️  Consider performance optimization - average overhead > 5ms")
    
    # Rollout recommendation
    if adapter_enabled and rollout_percentage < 100:
        if summary['error_rate'] < 0.1:
            print(f"  ✅ Ready to increase rollout from {rollout_percentage}% to {min(rollout_percentage * 2, 100)}%")
        else:
            print(f"  ⚠️  Fix errors before increasing rollout beyond {rollout_percentage}%")


if __name__ == "__main__":
    asyncio.run(main())