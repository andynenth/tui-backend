"""
WebSocket Integration Patch
This shows how to modify ws.py to use the adapter system.

INSTRUCTIONS:
1. Add imports at the top of ws.py
2. Initialize the adapter integration
3. Replace the message handling logic
"""

# ============= ADD THESE IMPORTS TO ws.py =============
from api.routes.ws_adapter_integration import ws_adapter_integration
from api.routes.ws_legacy_handlers import legacy_handlers

# ============= ADD THIS INITIALIZATION =============
# Add this after the router initialization (around line 26)
def initialize_adapter_integration():
    """Initialize the adapter integration with legacy handlers"""
    
    # Create a legacy handler function that wraps existing ws.py logic
    async def legacy_message_handler(websocket, message, room_id):
        """
        This function should contain the existing message handling logic from ws.py.
        For now, it calls the legacy handlers class which would need to be populated
        with the actual implementation from ws.py.
        """
        # Get the registered websocket (this matches ws.py pattern)
        from backend.socket_manager import get_registered_websocket
        registered_ws = get_registered_websocket(room_id, websocket) or websocket
        
        # Call legacy handler
        response = await legacy_handlers.handle_message(registered_ws, message, room_id)
        
        # Send response if there is one
        if response:
            await registered_ws.send_json(response)
        
        return response
    
    # Initialize the integration
    ws_adapter_integration.initialize(legacy_message_handler)
    
    logger.info("WebSocket adapter integration initialized")

# Call this at module level
initialize_adapter_integration()

# ============= REPLACE MESSAGE HANDLING IN websocket_endpoint =============
# Replace the existing message handling logic (starting around line 314) with:

"""
Example of how to modify the message handling in websocket_endpoint function:

Replace this section:
```python
            event_name = message.get("event")
            event_data = sanitized_data or message.get("data", {})
            
            # ... rate limiting ...
            
            # Handle reliable message delivery events
            if event_name == "ack":
                # ... existing ack handling ...
            elif event_name == "sync_request":
                # ... existing sync_request handling ...
            # ... all other event handlers ...
```

With this:
```python
            event_name = message.get("event")
            event_data = sanitized_data or message.get("data", {})
            
            # ... keep rate limiting as is ...
            
            # Special handlers that bypass adapters (ack and sync_request)
            if event_name == "ack":
                # ... keep existing ack handling ...
                continue
            elif event_name == "sync_request":
                # ... keep existing sync_request handling ...
                continue
            
            # Get room state for adapter
            room_state = None
            if room_id != "lobby":
                room = await room_manager.get_room(room_id)
                if room:
                    room_state = await room.summary()
            
            # Use adapter integration for all other messages
            try:
                response = await ws_adapter_integration.handle_message(
                    registered_ws,
                    message,
                    room_id,
                    room_state=room_state,
                    broadcast_func=broadcast
                )
                
                # Adapter system handles sending response if needed
                # Some messages (like broadcasts) don't have direct responses
                
            except Exception as e:
                logger.error(f"Error in adapter integration: {e}", exc_info=True)
                # Send error response
                await registered_ws.send_json({
                    "event": "error",
                    "data": {
                        "message": "Internal server error",
                        "type": "adapter_error"
                    }
                })
```
"""

# ============= EXAMPLE USAGE =============
async def example_integrated_handler(websocket, message, room_id):
    """
    Example of how the integrated handler would work.
    This shows the flow but would be implemented inside ws.py.
    """
    from backend.socket_manager import get_registered_websocket
    registered_ws = get_registered_websocket(room_id, websocket) or websocket
    
    # Special cases that bypass adapters
    event_name = message.get("event")
    if event_name in ["ack", "sync_request"]:
        # Handle these directly as before
        return
    
    # Get room state
    room_state = None
    if room_id != "lobby":
        from shared_instances import shared_room_manager
        room = await shared_room_manager.get_room(room_id)
        if room:
            room_state = await room.summary()
    
    # Use adapter integration
    response = await ws_adapter_integration.handle_message(
        registered_ws,
        message,
        room_id,
        room_state=room_state,
        broadcast_func=broadcast
    )
    
    return response

# ============= MONITORING ENDPOINT =============
# Add this new endpoint to ws.py for monitoring adapter status

from fastapi import APIRouter

# Add to the router
@router.get("/adapter-status")
async def get_adapter_status():
    """Get current adapter integration status"""
    return ws_adapter_integration.get_status()

# ============= ENVIRONMENT VARIABLES =============
"""
Add these environment variables for configuration:

# Enable/disable adapters
ADAPTER_ENABLED=false  # Set to true to enable

# Rollout percentage (0-100)
ADAPTER_ROLLOUT_PERCENTAGE=0  # Start with 0%, increase gradually

# Shadow mode for testing
SHADOW_MODE_ENABLED=false  # Set to true for shadow mode
SHADOW_MODE_PERCENTAGE=1  # Percentage of traffic to shadow

Example rollout:
1. SHADOW_MODE_ENABLED=true, SHADOW_MODE_PERCENTAGE=1  # Test with 1% shadow
2. SHADOW_MODE_ENABLED=true, SHADOW_MODE_PERCENTAGE=10  # Increase shadow
3. ADAPTER_ENABLED=true, ADAPTER_ROLLOUT_PERCENTAGE=1  # Start real rollout
4. ADAPTER_ENABLED=true, ADAPTER_ROLLOUT_PERCENTAGE=5  # Increase to 5%
5. ADAPTER_ENABLED=true, ADAPTER_ROLLOUT_PERCENTAGE=10  # Increase to 10%
6. ADAPTER_ENABLED=true, ADAPTER_ROLLOUT_PERCENTAGE=50  # Half traffic
7. ADAPTER_ENABLED=true, ADAPTER_ROLLOUT_PERCENTAGE=100  # Full rollout
"""