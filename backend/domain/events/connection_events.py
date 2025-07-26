"""
Connection-related domain events.

These events track player connection state changes including
disconnections, reconnections, and bot activation/deactivation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from .base import GameEvent


@dataclass(frozen=True)
class PlayerDisconnected(GameEvent):
    """Emitted when a player disconnects from the game."""
    
    player_name: str
    disconnect_time: datetime
    was_bot_activated: bool
    game_in_progress: bool
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_name': self.player_name,
            'disconnect_time': self.disconnect_time.isoformat(),
            'was_bot_activated': self.was_bot_activated,
            'game_in_progress': self.game_in_progress
        })
        return data


@dataclass(frozen=True)
class PlayerReconnected(GameEvent):
    """Emitted when a player reconnects to the game."""
    
    player_name: str
    reconnect_time: datetime
    messages_queued: int
    bot_was_deactivated: bool
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_name': self.player_name,
            'reconnect_time': self.reconnect_time.isoformat(),
            'messages_queued': self.messages_queued,
            'bot_was_deactivated': self.bot_was_deactivated
        })
        return data


@dataclass(frozen=True)
class BotActivated(GameEvent):
    """Emitted when a bot takes over for a disconnected player."""
    
    player_name: str
    activation_time: datetime
    game_phase: Optional[str] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_name': self.player_name,
            'activation_time': self.activation_time.isoformat(),
            'game_phase': self.game_phase
        })
        return data


@dataclass(frozen=True)
class BotDeactivated(GameEvent):
    """Emitted when a bot is deactivated on player return."""
    
    player_name: str
    deactivation_time: datetime
    game_phase: Optional[str] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        data = super()._get_event_data()
        data.update({
            'player_name': self.player_name,
            'deactivation_time': self.deactivation_time.isoformat(),
            'game_phase': self.game_phase
        })
        return data