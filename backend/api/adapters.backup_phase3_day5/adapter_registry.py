"""
Adapter Registry - Maps WebSocket actions to their adapters.
This is the bridge between the old WebSocket handler and new clean architecture.
"""

from typing import Dict, Any, Optional, Callable
import logging

from api.adapters.connection_adapters import (
    PingAdapter,
    ClientReadyAdapter,
    AckAdapter,
    SyncRequestAdapter,
)

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """Registry that maps WebSocket actions to their appropriate adapters"""

    def __init__(self):
        """Initialize the registry with all adapters"""
        # Connection adapters
        self.ping_adapter = PingAdapter()
        self.client_ready_adapter = ClientReadyAdapter()
        self.ack_adapter = AckAdapter()
        self.sync_request_adapter = SyncRequestAdapter()

        # Build action mapping
        self.adapters: Dict[str, Any] = {
            # Connection management
            "ping": self.ping_adapter,
            "client_ready": self.client_ready_adapter,
            "ack": self.ack_adapter,
            "sync_request": self.sync_request_adapter,
            # Room management (to be implemented)
            # "create_room": self.create_room_adapter,
            # "join_room": self.join_room_adapter,
            # "leave_room": self.leave_room_adapter,
            # "get_room_state": self.get_room_state_adapter,
            # "add_bot": self.add_bot_adapter,
            # "remove_player": self.remove_player_adapter,
            # Game actions (to be implemented)
            # "start_game": self.start_game_adapter,
            # "declare": self.declare_adapter,
            # "play": self.play_adapter,
            # "request_redeal": self.request_redeal_adapter,
            # "accept_redeal": self.accept_redeal_adapter,
            # "decline_redeal": self.decline_redeal_adapter,
        }

        # Track which adapters are enabled
        self.enabled_adapters = set(["ping", "client_ready", "ack", "sync_request"])

    def get_adapter(self, action: str):
        """Get adapter for a specific action"""
        if action not in self.enabled_adapters:
            return None
        return self.adapters.get(action)

    def is_handled_by_adapter(self, action: str) -> bool:
        """Check if an action is handled by an adapter"""
        return action in self.enabled_adapters

    def enable_adapter(self, action: str):
        """Enable an adapter for use"""
        if action in self.adapters:
            self.enabled_adapters.add(action)
            logger.info(f"Enabled adapter for action: {action}")

    def disable_adapter(self, action: str):
        """Disable an adapter (fallback to legacy handler)"""
        self.enabled_adapters.discard(action)
        logger.info(f"Disabled adapter for action: {action}")

    async def handle_message(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
        broadcast_func: Optional[Callable] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Handle a WebSocket message using the appropriate adapter.

        Returns:
            Response dict if adapter handles it, None if should use legacy handler
        """
        action = message.get("action")

        if not action:
            logger.warning("Message missing action field")
            return {"event": "error", "data": {"message": "Missing action field"}}

        adapter = self.get_adapter(action)
        if not adapter:
            # Not handled by adapter, use legacy handler
            return None

        try:
            # Call adapter
            response = await adapter.handle(websocket, message, room_state)

            # Some adapters may return None (like ack)
            return response

        except Exception as e:
            logger.error(f"Adapter error for {action}: {e}")
            return {
                "event": "error",
                "data": {
                    "message": f"Error processing {action}",
                    "type": "adapter_error",
                },
            }

    def get_status(self) -> Dict[str, Any]:
        """Get registry status for monitoring"""
        return {
            "total_adapters": len(self.adapters),
            "enabled_adapters": list(self.enabled_adapters),
            "disabled_adapters": list(
                set(self.adapters.keys()) - self.enabled_adapters
            ),
            "coverage": f"{len(self.enabled_adapters)}/{len(self.adapters)} ({len(self.enabled_adapters)/len(self.adapters)*100:.1f}%)",
        }


# Global registry instance
adapter_registry = AdapterRegistry()


def get_adapter_registry() -> AdapterRegistry:
    """Get the global adapter registry"""
    return adapter_registry
