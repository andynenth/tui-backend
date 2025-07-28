"""
WebSocket Adapter Integration - Optimized Version
Integrates the adapter pattern with existing WebSocket handlers with performance optimizations.
"""

from typing import Dict, Any, Optional, Callable
import logging

from api.adapters.adapter_registry import get_adapter_registry

logger = logging.getLogger(__name__)

# Cache the registry instance at module level
_registry = None
_debug_enabled = None

def _get_cached_registry():
    """Get cached registry instance"""
    global _registry
    if _registry is None:
        _registry = get_adapter_registry()
    return _registry

def _is_debug_enabled():
    """Check if debug logging is enabled (cached)"""
    global _debug_enabled
    if _debug_enabled is None:
        _debug_enabled = logger.isEnabledFor(logging.DEBUG)
    return _debug_enabled


async def handle_websocket_message_with_adapters(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None
) -> Optional[Dict[str, Any]]:
    """
    Handle WebSocket message, trying adapters first, then falling back to legacy.
    Optimized for minimal overhead.
    """
    action = message.get("action")
    if not action:
        return await legacy_handler(websocket, message)
    
    registry = _get_cached_registry()
    
    # Fast path: direct adapter lookup without double checking
    adapter = registry.get_enabled_adapter(action)
    
    if adapter:
        if _is_debug_enabled():
            logger.debug(f"Using adapter for action: {action}")
        
        # Direct adapter call
        response = await adapter.handle(
            websocket, 
            message, 
            room_state,
            broadcast_func
        )
        
        # Handle special cases inline
        if response is not None or action == "ack":
            return response
    
    # Fallback to legacy handler
    if _is_debug_enabled():
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
            websocket,
            message,
            legacy_handler,
            **kwargs
        )
    
    return adapter_aware_handler


class AdapterMigrationController:
    """
    Controls the gradual migration from legacy to adapter-based handlers.
    """
    
    def __init__(self):
        self.registry = _get_cached_registry()
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
            "migration_details": self.migration_status
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