# backend/services/alert_service.py
"""
Alert service for monitoring and notifying about performance issues.
"""

import time
import logging
import json
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class AlertThreshold:
    """Configuration for alert thresholds."""
    name: str
    threshold_ms: float
    severity: str  # "warning", "critical"
    cooldown_seconds: int = 300  # 5 minutes default cooldown
    
    def is_exceeded(self, value_ms: float) -> bool:
        """Check if threshold is exceeded."""
        return value_ms > self.threshold_ms


@dataclass
class Alert:
    """Represents a performance alert."""
    alert_type: str
    severity: str
    message: str
    context: Dict
    timestamp: float = field(default_factory=time.time)
    alert_id: str = field(default_factory=lambda: f"alert-{int(time.time() * 1000)}")
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp).isoformat() + "Z"
        }


class AlertService:
    """Service for managing performance alerts."""
    
    def __init__(self):
        self.thresholds: Dict[str, AlertThreshold] = {}
        self.alerts: deque = deque(maxlen=1000)  # Keep last 1000 alerts
        self.last_alert_time: Dict[str, float] = {}  # For cooldown tracking
        self.alert_handlers: List[Callable] = []
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self):
        """Setup default alert thresholds."""
        # Play history specific thresholds
        self.add_threshold(AlertThreshold(
            name="play_history_slow",
            threshold_ms=1000,
            severity="warning",
            cooldown_seconds=300
        ))
        
        self.add_threshold(AlertThreshold(
            name="play_history_critical",
            threshold_ms=3000,
            severity="critical",
            cooldown_seconds=600
        ))
        
        # General API thresholds
        self.add_threshold(AlertThreshold(
            name="api_slow",
            threshold_ms=500,
            severity="warning",
            cooldown_seconds=180
        ))
        
        self.add_threshold(AlertThreshold(
            name="api_critical",
            threshold_ms=2000,
            severity="critical",
            cooldown_seconds=300
        ))
        
        # Test operation thresholds
        self.add_threshold(AlertThreshold(
            name="test_operation_slow",
            threshold_ms=1000,
            severity="warning",
            cooldown_seconds=60
        ))
    
    def add_threshold(self, threshold: AlertThreshold):
        """Add or update an alert threshold."""
        self.thresholds[threshold.name] = threshold
    
    def add_handler(self, handler: Callable):
        """Add an alert handler function."""
        self.alert_handlers.append(handler)
    
    def check_response_time(self, 
                          operation: str, 
                          duration_ms: float, 
                          context: Dict) -> Optional[Alert]:
        """
        Check if response time exceeds thresholds and create alert if needed.
        
        Args:
            operation: Operation type (e.g., "play_history", "api")
            duration_ms: Duration in milliseconds
            context: Additional context for the alert
            
        Returns:
            Alert if threshold exceeded, None otherwise
        """
        alert_created = None
        
        # Check all relevant thresholds
        for threshold_name, threshold in self.thresholds.items():
            # Only check thresholds that match the operation
            if operation in threshold_name:
                if threshold.is_exceeded(duration_ms):
                    # Check cooldown
                    cooldown_key = f"{operation}:{threshold_name}"
                    last_alert = self.last_alert_time.get(cooldown_key, 0)
                    
                    if time.time() - last_alert > threshold.cooldown_seconds:
                        # Create alert
                        alert = Alert(
                            alert_type=f"{operation}_slow_response",
                            severity=threshold.severity,
                            message=f"{operation} response time ({duration_ms:.0f}ms) exceeded {threshold.severity} threshold ({threshold.threshold_ms}ms)",
                            context={
                                **context,
                                "duration_ms": duration_ms,
                                "threshold_ms": threshold.threshold_ms,
                                "threshold_name": threshold_name
                            }
                        )
                        
                        self._trigger_alert(alert)
                        self.last_alert_time[cooldown_key] = time.time()
                        
                        # Return the highest severity alert
                        if not alert_created or threshold.severity == "critical":
                            alert_created = alert
        
        return alert_created
    
    def create_custom_alert(self, 
                          alert_type: str,
                          severity: str,
                          message: str,
                          context: Dict) -> Alert:
        """Create a custom alert."""
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            context=context
        )
        
        self._trigger_alert(alert)
        return alert
    
    def _trigger_alert(self, alert: Alert):
        """Trigger alert and notify handlers."""
        # Store alert
        self.alerts.append(alert)
        
        # Log alert
        log_method = logger.error if alert.severity == "critical" else logger.warning
        log_method(
            f"Performance Alert: {alert.message}",
            extra={
                "alert": alert.to_dict(),
                "event": "performance_alert"
            }
        )
        
        # Notify handlers asynchronously
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(alert))
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    def get_recent_alerts(self, 
                         minutes: int = 60,
                         severity: Optional[str] = None,
                         alert_type: Optional[str] = None) -> List[Dict]:
        """Get recent alerts."""
        cutoff_time = time.time() - (minutes * 60)
        
        recent_alerts = []
        for alert in reversed(self.alerts):  # Most recent first
            if alert.timestamp < cutoff_time:
                break
                
            if severity and alert.severity != severity:
                continue
                
            if alert_type and alert.alert_type != alert_type:
                continue
                
            recent_alerts.append(alert.to_dict())
        
        return recent_alerts
    
    def get_alert_summary(self) -> Dict:
        """Get summary of alerts."""
        now = time.time()
        last_hour = now - 3600
        last_24h = now - 86400
        
        hour_alerts = [a for a in self.alerts if a.timestamp > last_hour]
        day_alerts = [a for a in self.alerts if a.timestamp > last_24h]
        
        return {
            "total_alerts": len(self.alerts),
            "last_hour": {
                "total": len(hour_alerts),
                "warning": sum(1 for a in hour_alerts if a.severity == "warning"),
                "critical": sum(1 for a in hour_alerts if a.severity == "critical"),
                "by_type": self._count_by_type(hour_alerts)
            },
            "last_24h": {
                "total": len(day_alerts),
                "warning": sum(1 for a in day_alerts if a.severity == "warning"),
                "critical": sum(1 for a in day_alerts if a.severity == "critical"),
                "by_type": self._count_by_type(day_alerts)
            },
            "thresholds": {
                name: {
                    "threshold_ms": t.threshold_ms,
                    "severity": t.severity,
                    "cooldown_seconds": t.cooldown_seconds
                }
                for name, t in self.thresholds.items()
            }
        }
    
    def _count_by_type(self, alerts: List[Alert]) -> Dict[str, int]:
        """Count alerts by type."""
        counts = {}
        for alert in alerts:
            counts[alert.alert_type] = counts.get(alert.alert_type, 0) + 1
        return counts


# Global alert service instance
alert_service = AlertService()


# Example alert handlers
def log_critical_alerts(alert: Alert):
    """Example handler that logs critical alerts to a separate file."""
    if alert.severity == "critical":
        critical_logger = logging.getLogger("critical_alerts")
        critical_logger.error(
            f"CRITICAL ALERT: {alert.alert_type} - {alert.message}",
            extra=alert.to_dict()
        )


def send_to_monitoring_system(alert: Alert):
    """Example handler that could send alerts to external monitoring."""
    # This would integrate with services like:
    # - PagerDuty
    # - Slack
    # - Email
    # - CloudWatch
    # etc.
    pass


# Register default handlers
alert_service.add_handler(log_critical_alerts)