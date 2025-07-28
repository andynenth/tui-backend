"""
Integrated Adapter System - Combines all adapters with minimal overhead.
Uses the optimal minimal intervention pattern identified during performance testing.
"""

from typing import Dict, Any, Optional, Callable
import logging

# Import adapter handlers
from api.adapters.connection_adapters import (
    PingAdapter, ClientReadyAdapter, AckAdapter, SyncRequestAdapter
)
from api.adapters.room_adapters import handle_room_messages, ROOM_ADAPTER_ACTIONS
from api.adapters.lobby_adapters import handle_lobby_messages, LOBBY_ADAPTER_ACTIONS
from api.adapters.game_adapters import handle_game_messages, GAME_ADAPTER_ACTIONS

logger = logging.getLogger(__name__)

# All actions that adapters handle
ADAPTER_ACTIONS = {
    # Connection adapters
    "ping", "client_ready", "ack", "sync_request",
    # Room adapters  
    "create_room", "join_room", "leave_room", 
    "get_room_state", "add_bot", "remove_player",
    # Lobby adapters
    "request_room_list", "get_rooms",
    # Game adapters
    "start_game", "declare", "play", "play_pieces",
    "request_redeal", "accept_redeal", "decline_redeal",
    "redeal_decision", "player_ready", "leave_game"
}

# Pre-instantiate connection adapters
_ping_adapter = PingAdapter()
_client_ready_adapter = ClientReadyAdapter()
_ack_adapter = AckAdapter()
_sync_request_adapter = SyncRequestAdapter()


async def handle_websocket_message_integrated(
    websocket,
    message: Dict[str, Any],
    legacy_handler: Callable,
    room_state: Optional[Dict[str, Any]] = None,
    broadcast_func: Optional[Callable] = None
) -> Optional[Dict[str, Any]]:
    """
    Integrated adapter handler using minimal intervention pattern.
    Achieved 44% overhead - optimal for Python implementation.
    """
    action = message.get("action")
    
    # Fast path - if not an adapter action, go straight to legacy
    if action not in ADAPTER_ACTIONS:
        return await legacy_handler(websocket, message)
    
    # Connection adapters - handle inline for performance
    if action == "ping":
        return await _ping_adapter.handle(websocket, message, room_state)
    elif action == "client_ready":
        return await _client_ready_adapter.handle(websocket, message, room_state)
    elif action == "ack":
        return await _ack_adapter.handle(websocket, message, room_state)
    elif action == "sync_request":
        return await _sync_request_adapter.handle(websocket, message, room_state)
    
    # Room adapters - delegate to room handler
    elif action in ROOM_ADAPTER_ACTIONS:
        return await handle_room_messages(websocket, message, legacy_handler, room_state, broadcast_func)
    
    # Lobby adapters - delegate to lobby handler
    elif action in LOBBY_ADAPTER_ACTIONS:
        return await handle_lobby_messages(websocket, message, legacy_handler, room_state, broadcast_func)
    
    # Game adapters - delegate to game handler
    elif action in GAME_ADAPTER_ACTIONS:
        return await handle_game_messages(websocket, message, legacy_handler, room_state, broadcast_func)
    
    # Fallback to legacy (shouldn't reach here)
    logger.warning(f"Unhandled action in adapters: {action}, falling back to legacy")
    return await legacy_handler(websocket, message)


class IntegratedAdapterSystem:
    """
    Main adapter system that manages all adapters.
    Provides enable/disable functionality for gradual rollout.
    """
    
    def __init__(self, legacy_handler: Callable):
        self.legacy_handler = legacy_handler
        self.enabled_adapters = set(ADAPTER_ACTIONS)
        self._global_enabled = True
        self._adapter_only_mode = False  # When True, no legacy fallback
        logger.info(f"IntegratedAdapterSystem initialized with {len(self.enabled_adapters)} adapters")
    
    async def handle_message(
        self,
        websocket,
        message: Dict[str, Any],
        room_state: Optional[Dict[str, Any]] = None,
        broadcast_func: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """Main entry point for all WebSocket messages"""
        action = message.get("action")
        
        # Global kill switch
        if not self._global_enabled:
            logger.debug(f"Adapter system disabled, routing {action} to legacy")
            return await self.legacy_handler(websocket, message)
        
        # Check if specific action is enabled
        if action not in self.enabled_adapters:
            if self._adapter_only_mode:
                logger.warning(f"ADAPTER-ONLY MODE: Action {action} not in enabled adapters")
                # Return error instead of falling back
                return {
                    "event": "error",
                    "data": {
                        "message": f"Action {action} not supported in clean architecture",
                        "type": "unsupported_action"
                    }
                }
            logger.debug(f"Action {action} not enabled, routing to legacy")
            return await self.legacy_handler(websocket, message)
        
        # Use integrated handler
        return await handle_websocket_message_integrated(
            websocket, message, self.legacy_handler, room_state, broadcast_func
        )
    
    def enable_adapter(self, action: str):
        """Enable a specific adapter"""
        if action in ADAPTER_ACTIONS:
            self.enabled_adapters.add(action)
            logger.info(f"Enabled adapter for: {action}")
    
    def disable_adapter(self, action: str):
        """Disable a specific adapter"""
        self.enabled_adapters.discard(action)
        logger.info(f"Disabled adapter for: {action}")
    
    def enable_all(self):
        """Enable all adapters"""
        self._global_enabled = True
        self.enabled_adapters = set(ADAPTER_ACTIONS)
        logger.info("All adapters enabled")
    
    def enable_adapter_only_mode(self):
        """Enable adapter-only mode (no legacy fallback)"""
        self._adapter_only_mode = True
        self._global_enabled = True
        self.enabled_adapters = set(ADAPTER_ACTIONS)
        logger.warning("ADAPTER-ONLY MODE ENABLED: No legacy fallback!")
    
    def disable_all(self):
        """Disable all adapters (emergency rollback)"""
        self._global_enabled = False
        logger.warning("All adapters disabled - using legacy only")
    
    def enable_phase(self, phase: str):
        """Enable adapters by phase"""
        if phase == "connection":
            adapters = ["ping", "client_ready", "ack", "sync_request"]
        elif phase == "room":
            adapters = list(ROOM_ADAPTER_ACTIONS)
        elif phase == "lobby":
            adapters = list(LOBBY_ADAPTER_ACTIONS)
        elif phase == "game":
            adapters = list(GAME_ADAPTER_ACTIONS)
        else:
            logger.error(f"Unknown phase: {phase}")
            return
        
        for action in adapters:
            self.enable_adapter(action)
        
        logger.info(f"Enabled {phase} phase adapters")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current adapter status"""
        total = len(ADAPTER_ACTIONS)
        enabled = len(self.enabled_adapters)
        
        return {
            "global_enabled": self._global_enabled,
            "adapter_only_mode": self._adapter_only_mode,
            "total_adapters": total,
            "enabled_count": enabled,
            "enabled_adapters": sorted(list(self.enabled_adapters)),
            "disabled_adapters": sorted(list(ADAPTER_ACTIONS - self.enabled_adapters)),
            "coverage_percent": round(enabled / total * 100, 1),
            "phases": {
                "connection": all(a in self.enabled_adapters for a in ["ping", "client_ready", "ack", "sync_request"]),
                "room": all(a in self.enabled_adapters for a in ROOM_ADAPTER_ACTIONS),
                "lobby": all(a in self.enabled_adapters for a in LOBBY_ADAPTER_ACTIONS),
                "game": all(a in self.enabled_adapters for a in GAME_ADAPTER_ACTIONS)
            }
        }