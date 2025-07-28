"""
WebSocket Adapter Wrapper
A minimal wrapper that integrates adapters into ws.py without extracting all legacy code.
"""

import os
import logging
import random
from typing import Dict, Any, Optional
from fastapi import WebSocket

from api.adapters.integrated_adapter_system import IntegratedAdapterSystem

logger = logging.getLogger(__name__)


class WSAdapterWrapper:
    """
    Minimal wrapper to integrate adapters into ws.py.
    This approach modifies ws.py minimally by intercepting messages.
    """
    
    def __init__(self):
        # Components
        self.adapter_system = None
        self._initialized = False
        self._config_loaded = False
        
        # Defer loading config until first use
        self.enabled = None
        self.rollout_percentage = None
        self.shadow_enabled = None
        self.shadow_percentage = None
    
    def _load_config(self):
        """Load configuration from environment variables (lazy loading)"""
        if self._config_loaded:
            return
            
        # Feature flags
        self.enabled = os.getenv("ADAPTER_ENABLED", "false").lower() == "true"
        self.rollout_percentage = float(os.getenv("ADAPTER_ROLLOUT_PERCENTAGE", "0"))
        
        # Shadow mode flags
        self.shadow_enabled = os.getenv("SHADOW_MODE_ENABLED", "false").lower() == "true"
        self.shadow_percentage = float(os.getenv("SHADOW_MODE_PERCENTAGE", "1"))
        
        self._config_loaded = True
        
        # Log configuration
        logger.info(f"WSAdapterWrapper configuration loaded:")
        logger.info(f"  Enabled: {self.enabled} (env: {os.getenv('ADAPTER_ENABLED', 'not set')})")
        logger.info(f"  Rollout: {self.rollout_percentage}% (env: {os.getenv('ADAPTER_ROLLOUT_PERCENTAGE', 'not set')})")
        logger.info(f"  Shadow: {self.shadow_enabled} at {self.shadow_percentage}%")
        
        # Log if adapter-only mode will be activated
        if self.enabled and self.rollout_percentage >= 100:
            logger.info("  🚦 Will activate ADAPTER-ONLY MODE when initialized")
    
    def initialize(self):
        """Initialize the adapter system"""
        # Load config if not already loaded
        self._load_config()
        
        if self._initialized:
            return
            
        # Create a legacy handler that returns None (meaning "not handled by adapter")
        async def legacy_handler(websocket, message):
            # Return None to indicate legacy code should handle it
            return None
        
        self.adapter_system = IntegratedAdapterSystem(legacy_handler)
        
        # Enable adapter-only mode if at 100% rollout
        if self.enabled and self.rollout_percentage >= 100:
            self.adapter_system.enable_adapter_only_mode()
            logger.info("Adapter system initialized in ADAPTER-ONLY MODE (no legacy fallback)")
        else:
            logger.info(f"Adapter system initialized (enabled={self.enabled}, rollout={self.rollout_percentage}%)")
        
        self._initialized = True
    
    def should_use_adapter(self, event_name: str) -> bool:
        """
        Determine if this event should be handled by adapter.
        
        Args:
            event_name: The WebSocket event name
            
        Returns:
            True if adapter should handle, False for legacy
        """
        # Load config if not already loaded
        if not self._config_loaded:
            self._load_config()
            
        if not self.enabled or not self._initialized:
            return False
        
        # These events are always handled by legacy code
        legacy_only_events = {"ack", "sync_request"}
        if event_name in legacy_only_events:
            return False
        
        # Check rollout percentage
        if self.rollout_percentage >= 100:
            return True
        elif self.rollout_percentage > 0:
            return random.random() * 100 < self.rollout_percentage
        
        return False
    
    async def try_handle_with_adapter(
        self,
        websocket: WebSocket,
        message: Dict[str, Any],
        room_id: str,
        room_state: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Try to handle message with adapter.
        
        Args:
            websocket: The WebSocket connection
            message: The message (with 'event' and 'data' keys)
            room_id: The room ID
            room_state: Optional room state
            
        Returns:
            Response dict if handled by adapter, None if legacy should handle
        """
        # Load config and initialize if needed
        if not self._config_loaded:
            self._load_config()
            
        # ADAPTER-ONLY MODE: Log when adapter is disabled
        if not self.enabled:
            logger.debug(f"Adapter disabled, falling back to legacy for: {message.get('event')}")
            return None
        if not self._initialized:
            self.initialize()
        
        event_name = message.get("event")
        
        # Check if we should use adapter
        if not self.should_use_adapter(event_name):
            logger.debug(f"Event {event_name} not using adapter (rollout check)")
            return None
        
        # ADAPTER-ONLY MODE: We're committed to handling this
        logger.debug(f"Adapter handling event: {event_name}")
        
        # Convert message format (event -> action for adapters)
        adapter_message = {
            "action": event_name,
            "data": message.get("data", {})
        }
        
        try:
            # Get room state if not provided
            if room_state is None and room_id != "lobby":
                try:
                    # Use clean architecture to get room state
                    from infrastructure.dependencies import get_unit_of_work
                    from application.dto.room_management import GetRoomStateRequest
                    from application.services.room_application_service import RoomApplicationService
                    
                    uow = get_unit_of_work()
                    room_service = RoomApplicationService(uow)
                    
                    async with uow:
                        request = GetRoomStateRequest(room_id=room_id)
                        result = await room_service.get_room_state(request)
                        
                        if result.success and result.data:
                            # Convert to the format adapters expect
                            room_data = result.data
                            room_state = {
                                "room_id": room_data.room_id,
                                "host": room_data.host,
                                "players": [p.dict() for p in room_data.players],
                                "status": room_data.status,
                                "game_config": room_data.game_config.dict() if room_data.game_config else None,
                                "current_round": room_data.current_round,
                                "max_players": room_data.max_players
                            }
                except Exception as e:
                    logger.debug(f"Could not get room state: {e}")
            
            # Try adapter
            response = await self.adapter_system.handle_message(
                websocket,
                adapter_message,
                room_state
            )
            
            # Log sampling
            if random.random() < 0.01:  # 1% sampling
                logger.info(f"Adapter handled event: {event_name}")
            
            return response
            
        except Exception as e:
            logger.error(f"Adapter error for {event_name}: {e}", exc_info=True)
            
            # ADAPTER-ONLY MODE: When enabled at 100%, don't fall back to legacy
            if self.enabled and self.rollout_percentage >= 100:
                logger.error(f"ADAPTER-ONLY MODE: No legacy fallback for {event_name}")
                # Return error response instead of None
                return {
                    "event": "error",
                    "data": {
                        "message": f"Failed to process {event_name} in clean architecture",
                        "type": "adapter_error",
                        "details": str(e)
                    }
                }
            
            # Otherwise fall back to legacy
            logger.warning(f"Falling back to legacy for {event_name}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter wrapper status"""
        status = {
            "enabled": self.enabled,
            "rollout_percentage": self.rollout_percentage,
            "shadow_enabled": self.shadow_enabled,
            "shadow_percentage": self.shadow_percentage,
            "initialized": self._initialized
        }
        
        if self.adapter_system:
            status["adapter_system"] = self.adapter_system.get_status()
        
        return status


# Global instance
adapter_wrapper = WSAdapterWrapper()


# ============ INTEGRATION INSTRUCTIONS FOR ws.py ============
"""
To integrate this wrapper into ws.py, make these minimal changes:

1. Add import at the top:
   from api.routes.ws_adapter_wrapper import adapter_wrapper

2. In the websocket_endpoint function, after message validation (around line 314),
   add this BEFORE the event handling:

   # Try adapter first
   adapter_response = await adapter_wrapper.try_handle_with_adapter(
       websocket, message, room_id
   )
   
   if adapter_response is not None:
       # Adapter handled it, send response and continue
       if adapter_response:  # Don't send if response is empty (like ack)
           await websocket.send_json(adapter_response)
       continue
   
   # Continue with existing event handling...
   event_name = message.get("event")
   # ... rest of the existing code ...

3. Add a status endpoint (optional):
   @router.get("/ws/adapter-status")
   async def get_adapter_status():
       return adapter_wrapper.get_status()

That's it! The adapter system will now intercept messages based on feature flags.
"""