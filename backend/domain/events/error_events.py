"""
Error and validation failure domain events.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from .base import DomainEvent, GameEvent


@dataclass(frozen=True)
class InvalidActionAttempted(GameEvent):
    """A player attempted an invalid action."""

    player_id: str
    player_name: str
    action_type: str
    reason: str
    details: Optional[Dict[str, Any]] = None

    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update(
            {
                "player_id": self.player_id,
                "player_name": self.player_name,
                "action_type": self.action_type,
                "reason": self.reason,
                "details": self.details or {},
            }
        )
        return data


@dataclass(frozen=True)
class ErrorOccurred(DomainEvent):
    """A system error occurred."""

    error_type: str
    error_message: str
    error_code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "context": self.context or {},
        }
