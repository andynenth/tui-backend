"""
Configuration for event-based adapter rollout.

This module controls which adapters use the event system vs direct broadcasts,
allowing for gradual migration and instant rollback.
"""

import os
from typing import Dict, Set
from enum import Enum


class AdapterMode(Enum):
    """Modes for adapter operation."""

    DIRECT = "direct"  # Original mode - direct broadcasts
    EVENT = "event"  # New mode - publish events
    SHADOW = "shadow"  # Both modes - compare outputs


class AdapterEventConfig:
    """
    Configuration for event-based adapter rollout.

    This allows fine-grained control over which adapters use events,
    supporting gradual rollout and A/B testing.
    """

    def __init__(self):
        # Global enable/disable
        self.events_enabled = self._get_bool_env("ADAPTER_EVENTS_ENABLED", False)

        # Rollout percentage (0-100)
        self.rollout_percentage = self._get_int_env("ADAPTER_EVENTS_ROLLOUT_PCT", 0)

        # Mode for all adapters (can be overridden per adapter)
        self.default_mode = self._get_mode_env(
            "ADAPTER_DEFAULT_MODE", AdapterMode.DIRECT
        )

        # Per-adapter configuration
        self.adapter_modes: Dict[str, AdapterMode] = {
            # Connection adapters
            "ping": self._get_adapter_mode("PING", AdapterMode.DIRECT),
            "client_ready": self._get_adapter_mode("CLIENT_READY", AdapterMode.DIRECT),
            "ack": self._get_adapter_mode("ACK", AdapterMode.DIRECT),
            "sync_request": self._get_adapter_mode("SYNC_REQUEST", AdapterMode.DIRECT),
            # Room adapters
            "create_room": self._get_adapter_mode("CREATE_ROOM", AdapterMode.DIRECT),
            "join_room": self._get_adapter_mode("JOIN_ROOM", AdapterMode.DIRECT),
            "leave_room": self._get_adapter_mode("LEAVE_ROOM", AdapterMode.DIRECT),
            "get_room_state": self._get_adapter_mode(
                "GET_ROOM_STATE", AdapterMode.DIRECT
            ),
            "add_bot": self._get_adapter_mode("ADD_BOT", AdapterMode.DIRECT),
            "remove_player": self._get_adapter_mode(
                "REMOVE_PLAYER", AdapterMode.DIRECT
            ),
            # Lobby adapters
            "request_room_list": self._get_adapter_mode(
                "REQUEST_ROOM_LIST", AdapterMode.DIRECT
            ),
            "get_rooms": self._get_adapter_mode("GET_ROOMS", AdapterMode.DIRECT),
            # Game adapters
            "start_game": self._get_adapter_mode("START_GAME", AdapterMode.DIRECT),
            "declare": self._get_adapter_mode("DECLARE", AdapterMode.DIRECT),
            "play": self._get_adapter_mode("PLAY", AdapterMode.DIRECT),
            "play_pieces": self._get_adapter_mode("PLAY_PIECES", AdapterMode.DIRECT),
            "request_redeal": self._get_adapter_mode(
                "REQUEST_REDEAL", AdapterMode.DIRECT
            ),
            "accept_redeal": self._get_adapter_mode(
                "ACCEPT_REDEAL", AdapterMode.DIRECT
            ),
            "decline_redeal": self._get_adapter_mode(
                "DECLINE_REDEAL", AdapterMode.DIRECT
            ),
            "redeal_decision": self._get_adapter_mode(
                "REDEAL_DECISION", AdapterMode.DIRECT
            ),
            "player_ready": self._get_adapter_mode("PLAYER_READY", AdapterMode.DIRECT),
            "leave_game": self._get_adapter_mode("LEAVE_GAME", AdapterMode.DIRECT),
        }

        # Adapters enabled for shadow mode testing
        self.shadow_adapters: Set[str] = set()
        shadow_list = os.getenv("ADAPTER_SHADOW_LIST", "").strip()
        if shadow_list:
            self.shadow_adapters = set(shadow_list.split(","))

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean from environment."""
        value = os.getenv(key, "").lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        return default

    def _get_int_env(self, key: str, default: int) -> int:
        """Get integer from environment."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    def _get_mode_env(self, key: str, default: AdapterMode) -> AdapterMode:
        """Get adapter mode from environment."""
        value = os.getenv(key, "").lower()
        if value == "direct":
            return AdapterMode.DIRECT
        elif value == "event":
            return AdapterMode.EVENT
        elif value == "shadow":
            return AdapterMode.SHADOW
        return default

    def _get_adapter_mode(self, adapter_name: str, default: AdapterMode) -> AdapterMode:
        """Get mode for specific adapter."""
        key = f"ADAPTER_{adapter_name.upper()}_MODE"
        return self._get_mode_env(key, default)

    def should_use_events(self, adapter_name: str, request_id: str = None) -> bool:
        """
        Determine if a specific adapter should use events for this request.

        Args:
            adapter_name: Name of the adapter
            request_id: Optional request ID for percentage-based rollout

        Returns:
            True if events should be used
        """
        if not self.events_enabled:
            return False

        mode = self.adapter_modes.get(adapter_name, self.default_mode)

        if mode == AdapterMode.EVENT:
            return True
        elif mode == AdapterMode.DIRECT:
            return False
        elif mode == AdapterMode.SHADOW:
            # In shadow mode, always use events but compare with direct
            return True

        # If not explicitly configured, use percentage rollout
        if request_id and self.rollout_percentage > 0:
            # Simple hash-based rollout
            hash_value = hash(f"{adapter_name}:{request_id}") % 100
            return hash_value < self.rollout_percentage

        return False

    def is_shadow_mode(self, adapter_name: str) -> bool:
        """Check if adapter is in shadow mode."""
        mode = self.adapter_modes.get(adapter_name, self.default_mode)
        return mode == AdapterMode.SHADOW or adapter_name in self.shadow_adapters

    def get_enabled_event_adapters(self) -> Set[str]:
        """Get list of adapters with events enabled."""
        enabled = set()
        for adapter, mode in self.adapter_modes.items():
            if mode in (AdapterMode.EVENT, AdapterMode.SHADOW):
                enabled.add(adapter)
        return enabled

    def enable_adapter_events(
        self, adapter_name: str, mode: AdapterMode = AdapterMode.EVENT
    ):
        """Enable events for a specific adapter."""
        self.adapter_modes[adapter_name] = mode

    def disable_adapter_events(self, adapter_name: str):
        """Disable events for a specific adapter."""
        self.adapter_modes[adapter_name] = AdapterMode.DIRECT

    def enable_all_events(self):
        """Enable events for all adapters."""
        self.events_enabled = True
        for adapter in self.adapter_modes:
            self.adapter_modes[adapter] = AdapterMode.EVENT

    def disable_all_events(self):
        """Disable events for all adapters (instant rollback)."""
        self.events_enabled = False
        for adapter in self.adapter_modes:
            self.adapter_modes[adapter] = AdapterMode.DIRECT


# Global configuration instance
adapter_event_config = AdapterEventConfig()


# Convenience functions
def should_adapter_use_events(adapter_name: str, request_id: str = None) -> bool:
    """Check if an adapter should use events."""
    return adapter_event_config.should_use_events(adapter_name, request_id)


def is_adapter_in_shadow_mode(adapter_name: str) -> bool:
    """Check if an adapter is in shadow mode."""
    return adapter_event_config.is_shadow_mode(adapter_name)


def enable_events_for_adapter(adapter_name: str):
    """Enable events for a specific adapter."""
    adapter_event_config.enable_adapter_events(adapter_name)


def rollback_all_events():
    """Emergency rollback - disable all events."""
    adapter_event_config.disable_all_events()
