"""
WebSocket Adapter Integration
Integrates the adapter pattern with existing WebSocket handlers.
"""

from typing import Dict, Any, Optional, Callable
import logging

from api.adapters.adapter_registry import get_adapter_registry

logger = logging.getLogger(__name__)


async def handle_websocket_message_with_adapters(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None,
) -> Optional[Dict[str, Any]]:
    """
    Handle WebSocket message, trying adapters first, then falling back to legacy.

    This is the main integration point that allows gradual migration.
    """
    action = message.get("action")
    registry = get_adapter_registry()

    # Check if this action is handled by an adapter
    if registry.is_handled_by_adapter(action):
        logger.debug(f"Using adapter for action: {action}")

        # Try adapter first
        response = await registry.handle_message(
            websocket, message, room_state, broadcast_func
        )

        if response is not None:
            # Adapter handled it successfully
            return response
        elif action == "ack":
            # Special case: ack returns None by design
            return None

    # Fallback to legacy handler
    logger.debug(f"Using legacy handler for action: {action}")
    return await legacy_handler(websocket, message)


def create_adapter_aware_handler(legacy_handler: Callable) -> Callable:
    """
    Create a new handler that tries adapters first, then legacy.

    Usage:
        # In your WebSocket route
        original_handler = handle_websocket_message
        new_handler = create_adapter_aware_handler(original_handler)

        # Then use new_handler instead of original_handler
    """

    async def adapter_aware_handler(websocket, message: Dict[str, Any], **kwargs):
        return await handle_websocket_message_with_adapters(
            websocket, message, legacy_handler, **kwargs
        )

    return adapter_aware_handler


class AdapterMigrationController:
    """
    Controls the gradual migration from legacy to adapter-based handlers.
    """

    def __init__(self):
        self.registry = get_adapter_registry()
        self.migration_status = {}

    def enable_adapter_for_action(self, action: str):
        """Enable adapter for a specific action"""
        self.registry.enable_adapter(action)
        self.migration_status[action] = "adapter"
        logger.info(f"Migrated '{action}' to adapter")

    def disable_adapter_for_action(self, action: str):
        """Disable adapter, reverting to legacy handler"""
        self.registry.disable_adapter(action)
        self.migration_status[action] = "legacy"
        logger.info(f"Reverted '{action}' to legacy handler")

    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        registry_status = self.registry.get_status()

        return {
            "adapter_coverage": registry_status["coverage"],
            "enabled_actions": registry_status["enabled_adapters"],
            "legacy_actions": registry_status["disabled_adapters"],
            "migration_details": self.migration_status,
        }

    def enable_phase_1_adapters(self):
        """Enable all Phase 1 adapters (connection management)"""
        phase_1_actions = ["ping", "client_ready", "ack", "sync_request"]

        for action in phase_1_actions:
            self.enable_adapter_for_action(action)

        logger.info("Phase 1 adapters enabled")

    def rollback_all_adapters(self):
        """Emergency rollback - disable all adapters"""
        all_actions = list(self.registry.adapters.keys())

        for action in all_actions:
            self.disable_adapter_for_action(action)

        logger.warning("All adapters disabled - using legacy handlers only")


# Global migration controller
migration_controller = AdapterMigrationController()


def get_migration_controller() -> AdapterMigrationController:
    """Get the global migration controller"""
    return migration_controller
