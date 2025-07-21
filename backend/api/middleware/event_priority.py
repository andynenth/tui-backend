# backend/api/middleware/event_priority.py

"""
Event priority system for rate limiting.

This module implements a priority-based rate limiting system that allows
critical game events to have more lenient limits and provides grace periods
for important operations.
"""

from enum import Enum
from typing import Dict, Optional, Set, Any
from dataclasses import dataclass
import time


class EventPriority(Enum):
    """Priority levels for different event types."""

    CRITICAL = 1  # Must never be blocked (e.g., timeout handling)
    HIGH = 2  # Important game events (e.g., turn actions)
    NORMAL = 3  # Regular events (e.g., declarations)
    LOW = 4  # Non-essential events (e.g., pings)


@dataclass
class GracePeriodConfig:
    """Configuration for grace periods."""

    warning_threshold: float = 0.8  # Warn at 80% of limit
    grace_multiplier: float = 1.2  # Allow 20% more during grace
    grace_duration: int = 30  # Grace period in seconds


class EventPriorityManager:
    """
    Manages event priorities and grace periods for rate limiting.

    Features:
    - Priority-based rate limit adjustments
    - Grace periods for users approaching limits
    - Critical event bypass
    - Soft warnings before hard limits
    """

    # Event priority mapping
    EVENT_PRIORITIES: Dict[str, EventPriority] = {
        # Critical events - should rarely/never be blocked
        "timeout_action": EventPriority.CRITICAL,
        "disconnect_cleanup": EventPriority.CRITICAL,
        "sync_request": EventPriority.CRITICAL,
        # High priority - game flow events
        "play": EventPriority.HIGH,
        "play_pieces": EventPriority.HIGH,
        "declare": EventPriority.HIGH,
        "accept_redeal": EventPriority.HIGH,
        "decline_redeal": EventPriority.HIGH,
        # Normal priority - room management
        "create_room": EventPriority.NORMAL,
        "join_room": EventPriority.NORMAL,
        "leave_room": EventPriority.NORMAL,
        "start_game": EventPriority.NORMAL,
        "player_ready": EventPriority.NORMAL,
        # Low priority - non-essential
        "ping": EventPriority.LOW,
        "get_rooms": EventPriority.LOW,
        "get_room_state": EventPriority.LOW,
        "request_room_list": EventPriority.LOW,
    }

    # Events that should trigger grace periods
    GRACE_ELIGIBLE_EVENTS: Set[str] = {"play", "play_pieces", "declare", "start_game"}

    def __init__(self):
        self.grace_periods: Dict[str, Dict[str, float]] = (
            {}
        )  # client_id -> event -> expiry
        self.grace_config = GracePeriodConfig()
        self.warnings_sent: Dict[str, Dict[str, float]] = (
            {}
        )  # client_id -> event -> last_warning

    def get_event_priority(self, event_name: str) -> EventPriority:
        """Get the priority level for an event."""
        return self.EVENT_PRIORITIES.get(event_name, EventPriority.NORMAL)

    def should_bypass_rate_limit(self, event_name: str) -> bool:
        """Check if an event should bypass rate limiting."""
        return self.get_event_priority(event_name) == EventPriority.CRITICAL

    def adjust_rate_limit_for_priority(
        self, event_name: str, base_limit: int, current_usage: int
    ) -> tuple[int, bool]:
        """
        Adjust rate limit based on event priority.

        Returns:
            Tuple of (adjusted_limit, should_warn)
        """
        priority = self.get_event_priority(event_name)

        # Priority multipliers
        multipliers = {
            EventPriority.CRITICAL: 10.0,  # 10x limit (effectively unlimited)
            EventPriority.HIGH: 2.0,  # 2x limit
            EventPriority.NORMAL: 1.0,  # Standard limit
            EventPriority.LOW: 0.8,  # 80% of limit
        }

        adjusted_limit = int(base_limit * multipliers[priority])

        # Check if we should warn
        warning_threshold = int(adjusted_limit * self.grace_config.warning_threshold)
        should_warn = current_usage >= warning_threshold

        return adjusted_limit, should_warn

    def check_grace_period(self, client_id: str, event_name: str) -> bool:
        """Check if a client is in grace period for an event."""
        if client_id not in self.grace_periods:
            return False

        if event_name not in self.grace_periods[client_id]:
            return False

        return time.time() < self.grace_periods[client_id][event_name]

    def grant_grace_period(self, client_id: str, event_name: str):
        """Grant a grace period to a client for an event."""
        if event_name not in self.GRACE_ELIGIBLE_EVENTS:
            return

        if client_id not in self.grace_periods:
            self.grace_periods[client_id] = {}

        self.grace_periods[client_id][event_name] = (
            time.time() + self.grace_config.grace_duration
        )

    def should_send_warning(self, client_id: str, event_name: str) -> bool:
        """Check if we should send a rate limit warning."""
        if client_id not in self.warnings_sent:
            self.warnings_sent[client_id] = {}

        last_warning = self.warnings_sent[client_id].get(event_name, 0)
        current_time = time.time()

        # Only warn once per minute
        if current_time - last_warning > 60:
            self.warnings_sent[client_id][event_name] = current_time
            return True

        return False

    def apply_grace_period_multiplier(
        self, client_id: str, event_name: str, base_limit: int
    ) -> int:
        """Apply grace period multiplier if applicable."""
        if self.check_grace_period(client_id, event_name):
            return int(base_limit * self.grace_config.grace_multiplier)
        return base_limit

    def cleanup_old_data(self):
        """Clean up expired grace periods and old warnings."""
        current_time = time.time()

        # Clean up grace periods
        for client_id in list(self.grace_periods.keys()):
            for event in list(self.grace_periods[client_id].keys()):
                if self.grace_periods[client_id][event] < current_time:
                    del self.grace_periods[client_id][event]

            if not self.grace_periods[client_id]:
                del self.grace_periods[client_id]

        # Clean up old warnings (older than 5 minutes)
        warning_cutoff = current_time - 300
        for client_id in list(self.warnings_sent.keys()):
            for event in list(self.warnings_sent[client_id].keys()):
                if self.warnings_sent[client_id][event] < warning_cutoff:
                    del self.warnings_sent[client_id][event]

            if not self.warnings_sent[client_id]:
                del self.warnings_sent[client_id]

    def get_rate_limit_response(
        self,
        event_name: str,
        is_warning: bool,
        remaining: int,
        limit: int,
        in_grace: bool,
    ) -> Dict[str, Any]:
        """Generate appropriate rate limit response."""
        priority = self.get_event_priority(event_name)

        if is_warning:
            return {
                "type": "rate_limit_warning",
                "message": f"Approaching rate limit for {event_name}",
                "remaining": remaining,
                "limit": limit,
                "priority": priority.name,
                "grace_period": in_grace,
                "suggestion": "Please slow down to avoid being rate limited",
            }
        else:
            severity = "low" if priority == EventPriority.LOW else "high"
            return {
                "type": "rate_limit_error",
                "severity": severity,
                "message": f"Rate limit exceeded for {event_name}",
                "priority": priority.name,
                "suggestion": "Please wait before sending more requests",
            }


# Global instance
_priority_manager = None


def get_priority_manager() -> EventPriorityManager:
    """Get the global event priority manager instance."""
    global _priority_manager
    if _priority_manager is None:
        _priority_manager = EventPriorityManager()
    return _priority_manager
