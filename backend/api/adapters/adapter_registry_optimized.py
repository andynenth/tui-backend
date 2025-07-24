"""
Adapter Registry - Optimized Version
Maps WebSocket actions to their adapters with performance optimizations.
"""

from typing import Dict, Any, Optional, Callable
import logging

from api.adapters.connection_adapters_optimized import (
    PingAdapter,
    ClientReadyAdapter, 
    AckAdapter,
    SyncRequestAdapter
)

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """Registry that maps WebSocket actions to their appropriate adapters"""
    
    __slots__ = ['adapters', 'enabled_adapters', '_enabled_adapter_map', 
                 'ping_adapter', 'client_ready_adapter', 'ack_adapter', 
                 'sync_request_adapter']
    
    def __init__(self):
        """Initialize the registry with all adapters"""
        # Create singleton adapter instances
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
        self.enabled_adapters = {"ping", "client_ready", "ack", "sync_request"}
        
        # Pre-compute enabled adapter map for O(1) lookup
        self._enabled_adapter_map = {}
        self._update_enabled_map()
    
    def _update_enabled_map(self):
        """Update the pre-computed enabled adapter map"""
        self._enabled_adapter_map = {
            action: self.adapters[action] 
            for action in self.enabled_adapters
            if action in self.adapters
        }
    
    def get_enabled_adapter(self, action: str):
        """Direct lookup for enabled adapters - O(1) operation"""
        return self._enabled_adapter_map.get(action)
    
    def get_adapter(self, action: str):
        """Get adapter for a specific action (legacy method for compatibility)"""
        if action not in self.enabled_adapters:
            return None
        return self.adapters.get(action)
    
    def is_handled_by_adapter(self, action: str) -> bool:
        """Check if an action is handled by an adapter"""
        return action in self._enabled_adapter_map
    
    def enable_adapter(self, action: str):
        """Enable an adapter for use"""
        if action in self.adapters:
            self.enabled_adapters.add(action)
            self._update_enabled_map()
            logger.info(f"Enabled adapter for action: {action}")
    
    def disable_adapter(self, action: str):
        """Disable an adapter (fallback to legacy handler)"""
        self.enabled_adapters.discard(action)
        self._update_enabled_map()
        logger.info(f"Disabled adapter for action: {action}")
    
    async def handle_message(self, websocket, message: Dict[str, Any], 
                           room_state: Optional[Dict[str, Any]] = None,
                           broadcast_func: Optional[Callable] = None) -> Optional[Dict[str, Any]]:
        """
        Handle a WebSocket message using the appropriate adapter.
        Optimized to avoid double lookups.
        
        Returns:
            Response dict if adapter handles it, None if should use legacy handler
        """
        action = message.get("action")
        
        if not action:
            logger.warning("Message missing action field")
            return {
                "event": "error",
                "data": {"message": "Missing action field"}
            }
        
        # Direct lookup - no double checking
        adapter = self._enabled_adapter_map.get(action)
        if not adapter:
            # Not handled by adapter, use legacy handler
            return None
            
        try:
            # Call adapter directly
            return await adapter.handle(websocket, message, room_state, broadcast_func)
            
        except Exception as e:
            logger.error(f"Adapter error for {action}: {e}")
            return {
                "event": "error",
                "data": {
                    "message": f"Error processing {action}",
                    "type": "adapter_error"
                }
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get registry status for monitoring"""
        total = len(self.adapters)
        enabled_count = len(self.enabled_adapters)
        
        return {
            "total_adapters": total,
            "enabled_adapters": list(self.enabled_adapters),
            "disabled_adapters": list(set(self.adapters.keys()) - self.enabled_adapters),
            "coverage": f"{enabled_count}/{total} ({enabled_count/total*100:.1f}%)"
        }


# Global registry instance
adapter_registry = AdapterRegistry()


def get_adapter_registry() -> AdapterRegistry:
    """Get the global adapter registry"""
    return adapter_registry