# application/events/event_types.py
"""
Application-level event types.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

from domain.events.base import DomainEvent


@dataclass
class ApplicationEvent(DomainEvent):
    """
    Base class for application-level events.
    
    These are events that originate from the application layer,
    typically as a result of use case execution.
    """
    
    use_case: str = ""  # Name of the use case that generated this event
    user_id: Optional[str] = None  # User who triggered the action
    
    def __post_init__(self):
        """Set aggregate type if not provided."""
        if not self.aggregate_type:
            self.aggregate_type = "Application"


@dataclass
class IntegrationEvent(DomainEvent):
    """
    Base class for integration events.
    
    These events are designed to be consumed by external systems
    or other bounded contexts.
    """
    
    source_system: str = "liap-tui"
    target_system: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_integration_format(self) -> Dict[str, Any]:
        """
        Convert to format suitable for external systems.
        
        Override this in subclasses to customize the format.
        """
        return {
            "event_id": self.event_id,
            "event_type": self.__class__.__name__,
            "timestamp": self.timestamp.isoformat(),
            "source_system": self.source_system,
            "target_system": self.target_system,
            "correlation_id": self.correlation_id,
            "aggregate_id": self.aggregate_id,
            "data": self.data
        }


# Specific application events

@dataclass
class UserActionEvent(ApplicationEvent):
    """Event fired when a user performs an action."""
    action: str
    room_id: Optional[str] = None
    game_id: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.aggregate_type = "UserAction"


@dataclass
class SystemNotificationEvent(ApplicationEvent):
    """Event for system-wide notifications."""
    notification_type: str
    message: str
    recipients: Dict[str, Any]  # e.g., {"room": "room_id", "players": ["p1", "p2"]}
    priority: str = "normal"  # low, normal, high, urgent
    
    def __post_init__(self):
        super().__post_init__()
        self.aggregate_type = "SystemNotification"


@dataclass
class PerformanceMetricEvent(ApplicationEvent):
    """Event for tracking performance metrics."""
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str]
    
    def __post_init__(self):
        super().__post_init__()
        self.aggregate_type = "PerformanceMetric"


@dataclass
class ErrorEvent(ApplicationEvent):
    """Event fired when an error occurs."""
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.aggregate_type = "Error"
        if self.context is None:
            self.context = {}


@dataclass
class AuditEvent(ApplicationEvent):
    """Event for audit logging."""
    entity_type: str
    entity_id: str
    operation: str  # create, update, delete, access
    changes: Dict[str, Any] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.aggregate_type = "Audit"
        if self.changes is None:
            self.changes = {}