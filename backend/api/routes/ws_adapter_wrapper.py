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
        # Feature flags
        self.enabled = os.getenv("ADAPTER_ENABLED", "false").lower() == "true"
        self.rollout_percentage = float(os.getenv("ADAPTER_ROLLOUT_PERCENTAGE", "0"))
        
        # Shadow mode flags
        self.shadow_enabled = os.getenv("SHADOW_MODE_ENABLED", "false").lower() == "true"
        self.shadow_percentage = float(os.getenv("SHADOW_MODE_PERCENTAGE", "1"))
        
        # Components
        self.adapter_system = None
        self._initialized = False
        
        logger.info(f"WSAdapterWrapper initialized:")
        logger.info(f"  Enabled: {self.enabled}")
        logger.info(f"  Rollout: {self.rollout_percentage}%")
        logger.info(f"  Shadow: {self.shadow_enabled} at {self.shadow_percentage}%")
    
    def initialize(self):
        """Initialize the adapter system"""
        if self._initialized:
            return
            
        # Create a legacy handler that returns None (meaning "not handled by adapter")
        async def legacy_handler(websocket, message):
            # Return None to indicate legacy code should handle it
            return None
        
        self.adapter_system = IntegratedAdapterSystem(legacy_handler)
        self._initialized = True
        logger.info("Adapter system initialized")
    
    def should_use_adapter(self, event_name: str) -> bool:
        """
        Determine if this event should be handled by adapter.
        
        Args:
            event_name: The WebSocket event name
            
        Returns:
            True if adapter should handle, False for legacy
        """
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
        if not self._initialized:
            self.initialize()
        
        event_name = message.get("event")
        
        # Check if we should use adapter
        if not self.should_use_adapter(event_name):
            return None
        
        # Convert message format (event -> action for adapters)
        adapter_message = {
            "action": event_name,
            "data": message.get("data", {})
        }
        
        try:
            # Get room state if not provided
            if room_state is None and room_id != "lobby":
                try:
                    from shared_instances import shared_room_manager
                    room = await shared_room_manager.get_room(room_id)
                    if room:
                        room_state = await room.summary()
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
            # Return None to fall back to legacy
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
       registered_ws, message, room_id
   )
   
   if adapter_response is not None:
       # Adapter handled it, send response and continue
       if adapter_response:  # Don't send if response is empty (like ack)
           await registered_ws.send_json(adapter_response)
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