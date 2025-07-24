"""
Shadow Mode Manager
Provides tools to manage and monitor shadow mode operations.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import asyncio

from api.shadow_mode import (
    ShadowModeState, 
    ShadowModeConfig,
    shadow_mode,
    configure_shadow_mode
)


class ShadowModeManager:
    """Manages shadow mode lifecycle and monitoring"""
    
    def __init__(self, storage_path: str = "shadow_mode_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def start_shadow_mode(self, 
                         sample_rate: float = 0.1,
                         state: ShadowModeState = ShadowModeState.MONITORING) -> Dict[str, Any]:
        """Start shadow mode with specified configuration"""
        config = ShadowModeConfig()
        config.sample_rate = sample_rate
        config.state = state
        config.comparison_storage_enabled = True
        
        # Configure shadow mode (handlers should be set elsewhere)
        shadow_mode.config = config
        
        # Log session start
        session_info = {
            "session_id": self.session_id,
            "started_at": datetime.now().isoformat(),
            "config": {
                "sample_rate": sample_rate,
                "state": state.value
            }
        }
        
        self._save_session_info(session_info)
        
        return {
            "status": "started",
            "session_id": self.session_id,
            "config": session_info["config"]
        }
        
    def stop_shadow_mode(self) -> Dict[str, Any]:
        """Stop shadow mode and save final report"""
        # Get final report
        report = shadow_mode.get_shadow_report()
        
        # Disable shadow mode
        shadow_mode.config.state = ShadowModeState.DISABLED
        
        # Save final report
        final_report = {
            "session_id": self.session_id,
            "ended_at": datetime.now().isoformat(),
            "final_report": report,
            "comparisons": self._export_comparisons()
        }
        
        report_path = self.storage_path / f"session_{self.session_id}_final.json"
        with open(report_path, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
            
        return {
            "status": "stopped",
            "session_id": self.session_id,
            "report_path": str(report_path),
            "summary": report["metrics"]
        }
        
    def adjust_sample_rate(self, new_rate: float) -> Dict[str, Any]:
        """Adjust shadow mode sample rate"""
        old_rate = shadow_mode.config.sample_rate
        shadow_mode.config.sample_rate = new_rate
        
        return {
            "status": "adjusted",
            "old_rate": old_rate,
            "new_rate": new_rate
        }
        
    def change_state(self, new_state: ShadowModeState) -> Dict[str, Any]:
        """Change shadow mode state"""
        old_state = shadow_mode.config.state
        shadow_mode.config.state = new_state
        
        # Log state change
        self._log_event({
            "event": "state_change",
            "timestamp": datetime.now().isoformat(),
            "old_state": old_state.value,
            "new_state": new_state.value
        })
        
        return {
            "status": "changed",
            "old_state": old_state.value,
            "new_state": new_state.value
        }
        
    def get_current_status(self) -> Dict[str, Any]:
        """Get current shadow mode status"""
        report = shadow_mode.get_shadow_report()
        
        return {
            "session_id": self.session_id,
            "state": shadow_mode.config.state.value,
            "sample_rate": shadow_mode.config.sample_rate,
            "metrics": report["metrics"],
            "recent_mismatches": report.get("recent_mismatches", [])
        }
        
    def analyze_mismatches(self, 
                          time_window_minutes: int = 60) -> Dict[str, Any]:
        """Analyze recent mismatches to identify patterns"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        
        recent_comparisons = [
            c for c in shadow_mode.comparisons
            if c.timestamp > cutoff_time
        ]
        
        # Analyze by action type
        mismatch_by_action = {}
        for comp in recent_comparisons:
            if not comp.match:
                action = comp.message.get("action", "unknown")
                if action not in mismatch_by_action:
                    mismatch_by_action[action] = {
                        "count": 0,
                        "difference_types": {}
                    }
                    
                mismatch_by_action[action]["count"] += 1
                
                # Count difference types
                for diff in comp.differences:
                    diff_type = diff.get("type", "unknown")
                    mismatch_by_action[action]["difference_types"][diff_type] = \
                        mismatch_by_action[action]["difference_types"].get(diff_type, 0) + 1
                        
        # Find most problematic actions
        problematic_actions = sorted(
            mismatch_by_action.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:5]
        
        return {
            "time_window_minutes": time_window_minutes,
            "total_comparisons": len(recent_comparisons),
            "total_mismatches": sum(1 for c in recent_comparisons if not c.match),
            "mismatch_rate": f"{sum(1 for c in recent_comparisons if not c.match) / len(recent_comparisons) * 100:.1f}%" if recent_comparisons else "0%",
            "problematic_actions": [
                {
                    "action": action,
                    "mismatch_count": data["count"],
                    "difference_types": data["difference_types"]
                }
                for action, data in problematic_actions
            ]
        }
        
    def export_session_data(self) -> str:
        """Export all session data for analysis"""
        export_data = {
            "session_id": self.session_id,
            "exported_at": datetime.now().isoformat(),
            "current_status": self.get_current_status(),
            "mismatch_analysis": self.analyze_mismatches(),
            "all_comparisons": self._export_comparisons()
        }
        
        export_path = self.storage_path / f"session_{self.session_id}_export.json"
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
            
        return str(export_path)
        
    def _save_session_info(self, info: Dict[str, Any]):
        """Save session information"""
        session_path = self.storage_path / f"session_{self.session_id}_info.json"
        with open(session_path, 'w') as f:
            json.dump(info, f, indent=2)
            
    def _log_event(self, event: Dict[str, Any]):
        """Log shadow mode event"""
        event_log_path = self.storage_path / f"session_{self.session_id}_events.jsonl"
        with open(event_log_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
            
    def _export_comparisons(self) -> List[Dict[str, Any]]:
        """Export comparison data for analysis"""
        return [
            {
                "request_id": c.request_id,
                "timestamp": c.timestamp.isoformat(),
                "action": c.message.get("action"),
                "match": c.match,
                "differences": c.differences,
                "current_duration_ms": c.current_duration_ms,
                "shadow_duration_ms": c.shadow_duration_ms,
                "performance_ratio": c.shadow_duration_ms / c.current_duration_ms if c.current_duration_ms > 0 else None
            }
            for c in shadow_mode.comparisons
        ]


class ShadowModeMonitor:
    """Monitor shadow mode operations in real-time"""
    
    def __init__(self, manager: ShadowModeManager):
        self.manager = manager
        self.monitoring = False
        
    async def start_monitoring(self, 
                             report_interval_seconds: int = 60,
                             alert_threshold: float = 0.95):
        """Start real-time monitoring"""
        self.monitoring = True
        
        while self.monitoring:
            # Get current status
            status = self.manager.get_current_status()
            metrics = status["metrics"]
            
            # Check match rate
            match_rate = float(metrics["match_rate"].rstrip('%')) / 100
            
            if match_rate < alert_threshold:
                await self._send_alert({
                    "type": "low_match_rate",
                    "match_rate": metrics["match_rate"],
                    "threshold": f"{alert_threshold * 100}%",
                    "mismatches": metrics["mismatches"]
                })
                
            # Check for performance degradation
            if metrics["performance_degradations"] > 10:
                await self._send_alert({
                    "type": "performance_degradation",
                    "count": metrics["performance_degradations"]
                })
                
            # Log periodic report
            self.manager._log_event({
                "event": "monitoring_report",
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics
            })
            
            # Wait for next interval
            await asyncio.sleep(report_interval_seconds)
            
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        
    async def _send_alert(self, alert: Dict[str, Any]):
        """Send alert (implement based on your alerting system)"""
        alert["timestamp"] = datetime.now().isoformat()
        
        # Log alert
        self.manager._log_event({
            "event": "alert",
            "alert": alert
        })
        
        # In production, send to alerting system
        print(f"SHADOW MODE ALERT: {alert}")


# CLI interface for shadow mode management
def create_shadow_mode_cli():
    """Create CLI commands for shadow mode management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Shadow Mode Management")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start shadow mode")
    start_parser.add_argument("--sample-rate", type=float, default=0.1,
                            help="Sample rate (0.0-1.0)")
    start_parser.add_argument("--state", choices=["monitoring", "validating"],
                            default="monitoring", help="Shadow mode state")
    
    # Stop command
    subparsers.add_parser("stop", help="Stop shadow mode")
    
    # Status command
    subparsers.add_parser("status", help="Get current status")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze mismatches")
    analyze_parser.add_argument("--window", type=int, default=60,
                              help="Time window in minutes")
    
    # Export command
    subparsers.add_parser("export", help="Export session data")
    
    return parser


if __name__ == "__main__":
    # Example usage
    manager = ShadowModeManager()
    
    # Start shadow mode
    result = manager.start_shadow_mode(sample_rate=0.1)
    print(f"Shadow mode started: {result}")
    
    # Get status
    status = manager.get_current_status()
    print(f"Current status: {status}")
    
    # Analyze mismatches
    analysis = manager.analyze_mismatches()
    print(f"Mismatch analysis: {analysis}")