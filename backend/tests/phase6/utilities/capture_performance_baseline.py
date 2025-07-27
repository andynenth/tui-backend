#!/usr/bin/env python3
"""
Performance Baseline Capture Script

Captures 24-48 hour performance baselines for migration monitoring.
"""

import asyncio
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from infrastructure.monitoring.enterprise_monitor import get_enterprise_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaselineCapture:
    """Captures system performance baselines over specified duration."""
    
    def __init__(self, duration_hours: int = 48):
        self.duration_hours = duration_hours
        self.monitor = get_enterprise_monitor()
        self.baseline_data: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
        self.end_time = self.start_time + timedelta(hours=duration_hours)
        
    async def capture_baseline_sample(self) -> Dict[str, Any]:
        """Capture a single baseline data sample."""
        timestamp = datetime.utcnow()
        
        # Get monitoring status
        status = self.monitor.get_monitoring_status()
        
        # Capture system metrics
        system_summary = status['system_summary']
        
        # Capture game analytics
        game_analytics = status['game_analytics']
        
        # Capture visualization data
        viz_data = self.monitor.get_visualization_data()
        
        sample = {
            "timestamp": timestamp.isoformat(),
            "system_metrics": {
                "memory_rss_mb": system_summary.get('current_rss_mb', 0),
                "memory_vms_mb": system_summary.get('current_vms_mb', 0),
                "memory_growth_rate": system_summary.get('growth_rate_mb_per_hour', 0),
                "cpu_usage_percent": system_summary.get('cpu_usage_percent', 0),
                "thread_count": system_summary.get('thread_count', 0),
                "gc_collections": system_summary.get('gc_collections', {})
            },
            "game_metrics": {
                "active_games": game_analytics.get('active_games', 0),
                "games_per_hour": game_analytics.get('games_per_hour', 0),
                "avg_game_duration": game_analytics.get('avg_game_duration_minutes', 0),
                "human_win_rate": game_analytics.get('human_win_rate', 0),
                "bot_win_rate": game_analytics.get('bot_win_rate', 0),
                "total_completed_games": game_analytics.get('total_completed_games', 0)
            },
            "websocket_metrics": {
                "active_connections": game_analytics.get('active_websocket_connections', 0),
                "avg_broadcast_time_ms": game_analytics.get('avg_broadcast_time_ms', 0)
            },
            "state_machine_metrics": {
                "states": viz_data.get('state_diagram', {}).get('nodes', []),
                "transitions": viz_data.get('state_diagram', {}).get('edges', [])
            },
            "event_stream_metrics": {
                "total_events": status['event_stream']['total_events'],
                "subscriber_count": status['event_stream']['subscriber_count']
            }
        }
        
        return sample
        
    async def capture_continuous_baseline(self, sample_interval_minutes: int = 5):
        """Capture baseline data continuously over the specified duration."""
        logger.info(f"🔍 Starting {self.duration_hours}h baseline capture")
        logger.info(f"📊 Sample interval: {sample_interval_minutes} minutes")
        logger.info(f"⏰ Start time: {self.start_time}")
        logger.info(f"⏰ End time: {self.end_time}")
        
        sample_count = 0
        
        while datetime.utcnow() < self.end_time:
            try:
                # Capture sample
                sample = await self.capture_baseline_sample()
                self.baseline_data.append(sample)
                sample_count += 1
                
                # Log progress
                if sample_count % 12 == 0:  # Every hour
                    remaining_hours = (self.end_time - datetime.utcnow()).total_seconds() / 3600
                    logger.info(f"📈 Captured {sample_count} samples, {remaining_hours:.1f}h remaining")
                
                # Wait for next sample
                await asyncio.sleep(sample_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"❌ Error capturing baseline sample: {e}")
                await asyncio.sleep(30)  # Wait 30s before retrying
        
        logger.info(f"✅ Baseline capture complete: {sample_count} samples collected")
        return self.baseline_data
    
    def calculate_baseline_statistics(self) -> Dict[str, Any]:
        """Calculate statistical summary of baseline data."""
        if not self.baseline_data:
            return {}
        
        # Extract numeric metrics
        memory_values = [s['system_metrics']['memory_rss_mb'] for s in self.baseline_data]
        cpu_values = [s['system_metrics']['cpu_usage_percent'] for s in self.baseline_data]
        game_counts = [s['game_metrics']['active_games'] for s in self.baseline_data]
        
        def calculate_stats(values: List[float]) -> Dict[str, float]:
            if not values:
                return {}
            return {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0]
            }
        
        statistics = {
            "capture_summary": {
                "duration_hours": self.duration_hours,
                "samples_collected": len(self.baseline_data),
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "actual_end_time": datetime.utcnow().isoformat()
            },
            "memory_baseline": calculate_stats(memory_values),
            "cpu_baseline": calculate_stats(cpu_values), 
            "game_activity_baseline": calculate_stats(game_counts),
            "alert_thresholds": {
                "memory_usage_alert_mb": max(memory_values) * 1.2 if memory_values else 1000,
                "cpu_usage_alert_percent": max(cpu_values) * 1.5 if cpu_values else 80,
                "response_time_alert_ms": 50,  # Based on migration requirements
                "error_rate_alert_percent": 0.5
            }
        }
        
        return statistics
    
    def save_baseline_data(self, filename: str = None):
        """Save baseline data and statistics to file."""
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"migration_baseline_{timestamp}.json"
        
        baseline_file = Path(__file__).parent / "baselines" / filename
        baseline_file.parent.mkdir(exist_ok=True)
        
        # Calculate statistics
        statistics = self.calculate_baseline_statistics()
        
        # Prepare export data
        export_data = {
            "metadata": {
                "version": "1.0",
                "phase": "6.1.4",
                "capture_script": Path(__file__).name,
                "generated_at": datetime.utcnow().isoformat()
            },
            "statistics": statistics,
            "raw_data": self.baseline_data
        }
        
        # Save to file
        with open(baseline_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"💾 Baseline data saved to: {baseline_file}")
        return baseline_file


async def capture_quick_baseline(duration_minutes: int = 10):
    """Capture a quick baseline for testing purposes."""
    logger.info(f"🚀 Quick baseline capture ({duration_minutes} minutes)")
    
    capture = BaselineCapture(duration_hours=duration_minutes/60)
    capture.end_time = capture.start_time + timedelta(minutes=duration_minutes)
    
    # Capture samples every 30 seconds for quick test
    sample_count = 0
    while datetime.utcnow() < capture.end_time:
        try:
            sample = await capture.capture_baseline_sample()
            capture.baseline_data.append(sample)
            sample_count += 1
            
            logger.info(f"📊 Sample {sample_count}: Memory={sample['system_metrics']['memory_rss_mb']}MB, "
                       f"Games={sample['game_metrics']['active_games']}")
            
            await asyncio.sleep(30)  # 30 second intervals
            
        except Exception as e:
            logger.error(f"❌ Error in quick baseline: {e}")
            break
    
    # Calculate and save
    statistics = capture.calculate_baseline_statistics()
    baseline_file = capture.save_baseline_data("quick_baseline_test.json")
    
    print(f"\n✅ Quick Baseline Summary:")
    print(f"📊 Samples collected: {len(capture.baseline_data)}")
    print(f"💾 Saved to: {baseline_file}")
    
    if statistics.get('memory_baseline'):
        mem_stats = statistics['memory_baseline']
        print(f"🧠 Memory: {mem_stats.get('min', 0):.1f}-{mem_stats.get('max', 0):.1f}MB (avg: {mem_stats.get('avg', 0):.1f}MB)")
    
    return capture


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="Capture performance baseline for migration")
    parser.add_argument("--duration", default="48h", help="Duration to capture (e.g., 48h, 24h, 10m)")
    parser.add_argument("--interval", default=5, type=int, help="Sample interval in minutes")
    parser.add_argument("--quick", action="store_true", help="Quick 10-minute test baseline")
    parser.add_argument("--output", help="Output filename for baseline data")
    
    args = parser.parse_args()
    
    try:
        if args.quick:
            # Quick test mode
            asyncio.run(capture_quick_baseline(10))
        else:
            # Parse duration
            if args.duration.endswith('h'):
                duration_hours = int(args.duration[:-1])
            elif args.duration.endswith('m'):
                duration_hours = int(args.duration[:-1]) / 60
            else:
                duration_hours = int(args.duration)
            
            # Full baseline capture
            capture = BaselineCapture(duration_hours)
            asyncio.run(capture.capture_continuous_baseline(args.interval))
            
            # Save results
            capture.save_baseline_data(args.output)
            
            # Print summary
            stats = capture.calculate_baseline_statistics()
            print(f"\n✅ Baseline Capture Complete:")
            print(f"📊 {stats['capture_summary']['samples_collected']} samples over {duration_hours}h")
            print(f"💾 Data saved with statistical analysis")
            
    except KeyboardInterrupt:
        logger.info("🛑 Baseline capture interrupted by user")
    except Exception as e:
        logger.error(f"❌ Baseline capture failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()