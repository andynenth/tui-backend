"""
WebSocket Adapter Integration for ws.py
Connects the integrated adapter system to the WebSocket handler with feature flags.
"""

import os
import logging
import random
from typing import Dict, Any, Optional, Callable
from fastapi import WebSocket

from api.adapters.integrated_adapter_system import IntegratedAdapterSystem
from api.shadow_mode_integration import ShadowModeWebSocketAdapter

logger = logging.getLogger(__name__)


class WebSocketAdapterIntegration:
    """
    Integration layer that connects ws.py to the adapter system.
    Supports gradual rollout via feature flags and shadow mode.
    """
    
    def __init__(self):
        # Feature flag settings from environment
        self.adapter_enabled = os.getenv("ADAPTER_ENABLED", "false").lower() == "true"
        self.adapter_rollout_percentage = float(os.getenv("ADAPTER_ROLLOUT_PERCENTAGE", "0"))
        self.shadow_mode_enabled = os.getenv("SHADOW_MODE_ENABLED", "false").lower() == "true"
        self.shadow_mode_percentage = float(os.getenv("SHADOW_MODE_PERCENTAGE", "1"))
        
        # Initialize components
        self.adapter_system = None
        self.shadow_adapter = None
        self.legacy_handler = None
        
        logger.info(f"WebSocket Adapter Integration initialized:")
        logger.info(f"  Adapter enabled: {self.adapter_enabled}")
        logger.info(f"  Rollout percentage: {self.adapter_rollout_percentage}%")
        logger.info(f"  Shadow mode: {self.shadow_mode_enabled}")
        logger.info(f"  Shadow percentage: {self.shadow_mode_percentage}%")
    
    def initialize(self, legacy_handler: Callable):
        """
        Initialize the integration with the legacy handler.
        
        Args:
            legacy_handler: Function that handles messages the old way
        """
        self.legacy_handler = legacy_handler
        
        # Create adapter system
        self.adapter_system = IntegratedAdapterSystem(legacy_handler)
        
        # Create shadow mode adapter if enabled
        if self.shadow_mode_enabled:
            self.shadow_adapter = ShadowModeWebSocketAdapter(legacy_handler)
            self.shadow_adapter.set_shadow_handler(self.adapter_system.handle_message)
            self.shadow_adapter.enable_shadow_mode(sample_rate=self.shadow_mode_percentage / 100)
            logger.info("Shadow mode adapter initialized")
    
    async def handle_message(
        self,
        websocket: WebSocket,
        message: Dict[str, Any],
        room_id: str,
        room_state: Optional[Dict[str, Any]] = None,
        broadcast_func: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle a WebSocket message with adapter integration.
        
        Args:
            websocket: The WebSocket connection
            message: The message to handle
            room_id: The room ID
            room_state: Current room state (optional)
            broadcast_func: Broadcast function (optional)
            
        Returns:
            Response message or None
        """
        # Extract action from message
        action = message.get("event")  # Note: ws.py uses "event" not "action"
        
        # Convert to adapter format (event -> action)
        adapter_message = {
            "action": action,
            "data": message.get("data", {})
        }
        
        # Determine if this request should use adapters
        use_adapters = False
        
        if self.adapter_enabled:
            if self.adapter_rollout_percentage >= 100:
                use_adapters = True
            elif self.adapter_rollout_percentage > 0:
                # Random rollout based on percentage
                use_adapters = random.random() * 100 < self.adapter_rollout_percentage
        
        # Handle the message
        try:
            if self.shadow_mode_enabled and self.shadow_adapter:
                # Use shadow mode - runs both implementations
                response = await self.shadow_adapter.handle_message(
                    websocket, adapter_message, room_state, broadcast_func
                )
            elif use_adapters:
                # Use adapter system
                response = await self.adapter_system.handle_message(
                    websocket, adapter_message, room_state, broadcast_func
                )
            else:
                # Use legacy handler
                response = await self.legacy_handler(websocket, message, room_id)
            
            # Log which path was used (sampling to avoid log spam)
            if random.random() < 0.01:  # 1% sampling
                logger.info(f"Message handled via {'adapters' if use_adapters else 'legacy'} for action: {action}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            
            # Always fall back to legacy on error
            if not use_adapters:
                raise  # Re-raise if already using legacy
            
            logger.warning(f"Falling back to legacy handler after adapter error for action: {action}")
            return await self.legacy_handler(websocket, message, room_id)
    
    def enable_adapters(self, percentage: float = 100):
        """Enable adapters with specified rollout percentage"""
        self.adapter_enabled = True
        self.adapter_rollout_percentage = percentage
        logger.info(f"Adapters enabled at {percentage}% rollout")
    
    def disable_adapters(self):
        """Disable all adapters"""
        self.adapter_enabled = False
        self.adapter_rollout_percentage = 0
        logger.info("Adapters disabled")
    
    def enable_shadow_mode(self, percentage: float = 100):
        """Enable shadow mode with specified percentage"""
        self.shadow_mode_enabled = True
        self.shadow_mode_percentage = percentage
        if self.shadow_adapter:
            self.shadow_adapter.enable_shadow_mode(sample_rate=percentage / 100)
        logger.info(f"Shadow mode enabled at {percentage}%")
    
    def disable_shadow_mode(self):
        """Disable shadow mode"""
        self.shadow_mode_enabled = False
        if self.shadow_adapter:
            self.shadow_adapter.disable_shadow_mode()
        logger.info("Shadow mode disabled")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current integration status"""
        status = {
            "adapter_enabled": self.adapter_enabled,
            "adapter_rollout_percentage": self.adapter_rollout_percentage,
            "shadow_mode_enabled": self.shadow_mode_enabled,
            "shadow_mode_percentage": self.shadow_mode_percentage,
        }
        
        if self.adapter_system:
            status["adapter_system_status"] = self.adapter_system.get_status()
        
        if self.shadow_adapter and self.shadow_mode_enabled:
            shadow_status = self.shadow_adapter.get_shadow_status()
            status["shadow_mode_stats"] = {
                "messages_processed": shadow_status["messages_processed"],
                "messages_compared": shadow_status["messages_compared"],
                "mismatches": shadow_status["mismatches"],
                "mismatch_rate": shadow_status["mismatch_rate"]
            }
        
        return status


# Global instance
ws_adapter_integration = WebSocketAdapterIntegration()


def create_legacy_handler_wrapper(existing_handler_code):
    """
    Create a wrapper for existing WebSocket handler code.
    This allows us to call the existing logic as a function.
    
    Args:
        existing_handler_code: The existing handler logic from ws.py
        
    Returns:
        Async function that can be used as legacy handler
    """
    async def legacy_handler(websocket: WebSocket, message: Dict[str, Any], room_id: str) -> Optional[Dict[str, Any]]:
        """
        Wrapper that executes existing handler code.
        This would contain the actual logic extracted from ws.py.
        """
        # This is a placeholder - in actual implementation, this would
        # execute the existing handler code for the specific event
        event_name = message.get("event")
        
        # For now, return a marker response
        return {
            "event": "legacy_handler_response",
            "data": {
                "message": f"Legacy handler for {event_name} not yet extracted",
                "action": event_name
            }
        }
    
    return legacy_handler