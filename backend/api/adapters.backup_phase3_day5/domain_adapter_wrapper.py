"""
Domain adapter wrapper for WebSocket integration.

This provides a simple interface for ws.py to use domain adapters
with minimal code changes.
"""

import os
from typing import Dict, Any, Optional
import logging

from .domain_integration import get_domain_integration

logger = logging.getLogger(__name__)


class DomainAdapterWrapper:
    """
    Wrapper that provides a simple interface for using domain adapters.
    
    This wrapper can be enabled/disabled via environment variables and
    provides a clean integration point for ws.py.
    """
    
    def __init__(self):
        """Initialize the wrapper."""
        self.integration = get_domain_integration()
        
        # Check environment variables
        self._check_environment()
    
    def _check_environment(self):
        """Check environment variables for configuration."""
        # Check if domain adapters are enabled
        enabled = os.getenv("DOMAIN_ADAPTERS_ENABLED", "false").lower() == "true"
        
        if enabled:
            self.integration.enable()
            logger.info("Domain adapters enabled via DOMAIN_ADAPTERS_ENABLED=true")
        else:
            self.integration.disable()
            logger.info("Domain adapters disabled (set DOMAIN_ADAPTERS_ENABLED=true to enable)")
    
    async def try_handle_with_domain(
        self,
        websocket,
        message: Dict[str, Any],
        room_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Try to handle a message with domain adapters.
        
        Args:
            websocket: WebSocket connection
            message: Incoming message
            room_id: Current room ID
            
        Returns:
            Response if handled, None to fall back to legacy
        """
        if not self.integration.enabled:
            return None
        
        try:
            # Try domain adapter
            response = await self.integration.handle_message(
                websocket, message, room_id
            )
            
            if response is not None:
                logger.debug(f"Domain adapter handled {message.get('event')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in domain adapter: {e}")
            # Fall back to legacy on error
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current adapter status."""
        return {
            "domain_adapters": self.integration.get_status(),
            "environment": {
                "DOMAIN_ADAPTERS_ENABLED": os.getenv("DOMAIN_ADAPTERS_ENABLED", "false")
            }
        }


# Create singleton instance
domain_adapter_wrapper = DomainAdapterWrapper()