"""
Unified adapter handler that routes to event-based or direct adapters
based on configuration.

This provides a single entry point for all adapter handling, supporting
gradual rollout, A/B testing, and instant rollback.
"""

from typing import Dict, Any, Optional, Callable
import logging
import time

from .adapter_event_config import (
    should_adapter_use_events, 
    is_adapter_in_shadow_mode,
    adapter_event_config
)

# Import event-based adapters
from .connection_adapters_event import (
    get_ping_adapter as get_ping_adapter_event,
    get_client_ready_adapter as get_client_ready_adapter_event,
    get_ack_adapter as get_ack_adapter_event,
    get_sync_request_adapter as get_sync_request_adapter_event
)

from .room_adapters_event import (
    get_create_room_adapter as get_create_room_adapter_event,
    get_join_room_adapter as get_join_room_adapter_event,
    get_leave_room_adapter as get_leave_room_adapter_event,
    get_room_state_adapter as get_room_state_adapter_event,
    get_add_bot_adapter as get_add_bot_adapter_event,
    get_remove_player_adapter as get_remove_player_adapter_event
)

from .game_adapters_event import (
    get_start_game_adapter as get_start_game_adapter_event,
    get_declare_adapter as get_declare_adapter_event,
    get_play_adapter as get_play_adapter_event,
    get_request_redeal_adapter as get_request_redeal_adapter_event,
    get_accept_redeal_adapter as get_accept_redeal_adapter_event,
    get_decline_redeal_adapter as get_decline_redeal_adapter_event,
    get_player_ready_adapter as get_player_ready_adapter_event
)

from .lobby_adapters_event import (
    get_request_room_list_adapter as get_request_room_list_adapter_event,
    get_rooms_adapter as get_rooms_adapter_event
)

logger = logging.getLogger(__name__)


class UnifiedAdapterHandler:
    """
    Central handler that routes to appropriate adapters based on configuration.
    Supports event-based and direct adapters with shadow mode for comparison.
    """
    
    def __init__(self, room_manager=None, game_manager=None):
        """Initialize with optional dependencies."""
        self.room_manager = room_manager
        self.game_manager = game_manager
        
        # Map actions to their adapter getters
        self.adapter_map = {
            # Connection adapters
            "ping": lambda: self._get_adapter("ping", get_ping_adapter_event),
            "client_ready": lambda: self._get_adapter("client_ready", 
                lambda: get_client_ready_adapter_event(self.room_manager)),
            "ack": lambda: self._get_adapter("ack", get_ack_adapter_event),
            "sync_request": lambda: self._get_adapter("sync_request",
                lambda: get_sync_request_adapter_event(self.room_manager, self.game_manager)),
            
            # Room adapters
            "create_room": lambda: self._get_adapter("create_room",
                lambda: get_create_room_adapter_event(self.room_manager)),
            "join_room": lambda: self._get_adapter("join_room",
                lambda: get_join_room_adapter_event(self.room_manager)),
            "leave_room": lambda: self._get_adapter("leave_room",
                lambda: get_leave_room_adapter_event(self.room_manager)),
            "get_room_state": lambda: self._get_adapter("get_room_state",
                lambda: get_room_state_adapter_event(self.room_manager)),
            "add_bot": lambda: self._get_adapter("add_bot",
                lambda: get_add_bot_adapter_event(self.room_manager)),
            "remove_player": lambda: self._get_adapter("remove_player",
                lambda: get_remove_player_adapter_event(self.room_manager)),
            
            # Game adapters
            "start_game": lambda: self._get_adapter("start_game",
                lambda: get_start_game_adapter_event(self.room_manager, self.game_manager)),
            "declare": lambda: self._get_adapter("declare",
                lambda: get_declare_adapter_event(self.game_manager)),
            "play": lambda: self._get_adapter("play",
                lambda: get_play_adapter_event(self.game_manager)),
            "play_pieces": lambda: self._get_adapter("play",  # Alias to play
                lambda: get_play_adapter_event(self.game_manager)),
            "request_redeal": lambda: self._get_adapter("request_redeal",
                lambda: get_request_redeal_adapter_event(self.game_manager)),
            "accept_redeal": lambda: self._get_adapter("accept_redeal",
                lambda: get_accept_redeal_adapter_event(self.game_manager)),
            "decline_redeal": lambda: self._get_adapter("decline_redeal",
                lambda: get_decline_redeal_adapter_event(self.game_manager)),
            "player_ready": lambda: self._get_adapter("player_ready",
                lambda: get_player_ready_adapter_event(self.room_manager)),
            
            # Lobby adapters
            "request_room_list": lambda: self._get_adapter("request_room_list",
                lambda: get_request_room_list_adapter_event(self.room_manager)),
            "get_rooms": lambda: self._get_adapter("get_rooms",
                lambda: get_rooms_adapter_event(self.room_manager))
        }
        
        # Shadow mode comparison results
        self.shadow_results = []
    
    def _get_adapter(self, action: str, event_adapter_getter: Callable):
        """
        Get the appropriate adapter based on configuration.
        
        Args:
            action: The action name
            event_adapter_getter: Function to get event-based adapter
            
        Returns:
            The adapter instance or function
        """
        if should_adapter_use_events(action):
            return event_adapter_getter()
        else:
            # Return None to use legacy handler
            return None
    
    async def handle_message(
        self,
        websocket,
        message: Dict[str, Any],
        legacy_handler: Callable,
        room_state: Optional[Dict[str, Any]] = None,
        broadcast_func: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Route message to appropriate adapter based on action and configuration.
        
        Args:
            websocket: The WebSocket connection
            message: The incoming message
            legacy_handler: Fallback to legacy handling
            room_state: Optional current room state
            broadcast_func: Optional broadcast function
            
        Returns:
            Response to send back to client
        """
        action = message.get("action")
        
        # Check if we have an adapter for this action
        if action not in self.adapter_map:
            return await legacy_handler(websocket, message)
        
        # Get request ID for percentage-based rollout
        request_id = message.get("request_id") or str(time.time())
        
        # Check if this adapter should use events
        if not should_adapter_use_events(action, request_id):
            return await legacy_handler(websocket, message)
        
        # Get the adapter
        adapter = self.adapter_map[action]()
        
        if adapter is None:
            return await legacy_handler(websocket, message)
        
        # Handle shadow mode
        if is_adapter_in_shadow_mode(action):
            return await self._handle_shadow_mode(
                adapter, websocket, message, legacy_handler, 
                room_state, broadcast_func, action
            )
        
        # Normal event-based handling
        try:
            return await adapter.handle(websocket, message, room_state)
        except Exception as e:
            logger.error(f"Error in event adapter for {action}: {e}", exc_info=True)
            # Fallback to legacy on error
            return await legacy_handler(websocket, message)
    
    async def _handle_shadow_mode(
        self,
        adapter,
        websocket,
        message: Dict[str, Any],
        legacy_handler: Callable,
        room_state: Optional[Dict[str, Any]],
        broadcast_func: Optional[Callable],
        action: str
    ) -> Optional[Dict[str, Any]]:
        """
        Run both event and legacy adapters, compare results.
        
        Returns the legacy result but logs any differences.
        """
        start_time = time.time()
        
        # Run legacy handler
        legacy_result = None
        legacy_error = None
        try:
            legacy_result = await legacy_handler(websocket, message)
            legacy_time = time.time() - start_time
        except Exception as e:
            legacy_error = str(e)
            legacy_time = time.time() - start_time
        
        # Run event handler
        event_start = time.time()
        event_result = None
        event_error = None
        try:
            event_result = await adapter.handle(websocket, message, room_state)
            event_time = time.time() - event_start
        except Exception as e:
            event_error = str(e)
            event_time = time.time() - event_start
        
        # Compare results
        comparison = {
            "action": action,
            "timestamp": time.time(),
            "legacy_time": legacy_time,
            "event_time": event_time,
            "results_match": legacy_result == event_result,
            "legacy_error": legacy_error,
            "event_error": event_error
        }
        
        # Log differences
        if not comparison["results_match"]:
            logger.warning(
                f"Shadow mode mismatch for {action}: "
                f"Legacy={legacy_result}, Event={event_result}"
            )
        
        # Store for analysis
        self.shadow_results.append(comparison)
        if len(self.shadow_results) > 1000:
            self.shadow_results.pop(0)
        
        # Always return legacy result in shadow mode
        if legacy_error:
            raise Exception(legacy_error)
        return legacy_result
    
    def get_shadow_mode_stats(self) -> Dict[str, Any]:
        """Get statistics from shadow mode comparisons."""
        if not self.shadow_results:
            return {"message": "No shadow mode data available"}
        
        total = len(self.shadow_results)
        matches = sum(1 for r in self.shadow_results if r["results_match"])
        
        avg_legacy_time = sum(r["legacy_time"] for r in self.shadow_results) / total
        avg_event_time = sum(r["event_time"] for r in self.shadow_results) / total
        
        return {
            "total_comparisons": total,
            "matches": matches,
            "match_rate": matches / total,
            "avg_legacy_time_ms": avg_legacy_time * 1000,
            "avg_event_time_ms": avg_event_time * 1000,
            "performance_gain": (avg_legacy_time - avg_event_time) / avg_legacy_time
        }


# Global instance
_unified_handler: Optional[UnifiedAdapterHandler] = None


def get_unified_handler(room_manager=None, game_manager=None) -> UnifiedAdapterHandler:
    """Get or create the global unified handler."""
    global _unified_handler
    
    if _unified_handler is None:
        _unified_handler = UnifiedAdapterHandler(room_manager, game_manager)
    
    return _unified_handler


def reset_unified_handler():
    """Reset the unified handler (useful for testing)."""
    global _unified_handler
    _unified_handler = None