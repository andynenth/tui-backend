# WebSocket Adapter Integration Guide

**Purpose**: Technical reference showing how the adapter system was integrated into ws.py during the clean architecture migration.

**Status**: ✅ INTEGRATION COMPLETE - System running 100% on clean architecture

**See Also**: [Deployment Runbook](./ADAPTER_DEPLOYMENT_RUNBOOK.md) for historical deployment procedures

## Overview

The adapter integration was successfully completed with minimal changes to `ws.py`:
1. Added adapter integration code to route messages through clean architecture
2. Updated imports to use clean architecture components
3. Removed all legacy dependencies after Phase 7

## Step-by-Step Instructions

### 1. Add Import

At the top of `api/routes/ws.py`, add this import with the other imports:

```python
from api.routes.ws_adapter_wrapper import adapter_wrapper
```

### 2. Add Adapter Integration

In the `websocket_endpoint` function, locate the message handling loop. After message validation but BEFORE the event handling, add:

Find this section (around line 314):
```python
            # Validate the message structure and content
            is_valid, error_msg, sanitized_data = validate_websocket_message(message)
            if not is_valid:
                await registered_ws.send_json(
                    {
                        "event": "error",
                        "data": {
                            "message": f"Invalid message: {error_msg}",
                            "type": "validation_error",
                        },
                    }
                )
                continue

            event_name = message.get("event")
            # Use sanitized data instead of raw event data
            event_data = sanitized_data or message.get("data", {})
```

Add this code right AFTER the validation, BEFORE the rate limiting:

```python
            # ===== ADAPTER INTEGRATION START =====
            # Try adapter system first (if enabled)
            adapter_response = await adapter_wrapper.try_handle_with_adapter(
                registered_ws, message, room_id
            )
            
            if adapter_response is not None:
                # Adapter handled it, send response if not empty
                if adapter_response:  # Some responses like 'ack' return empty
                    await registered_ws.send_json(adapter_response)
                continue  # Skip legacy handling
            # ===== ADAPTER INTEGRATION END =====
            
            # Continue with existing code...
            event_name = message.get("event")
            event_data = sanitized_data or message.get("data", {})
```

### 3. (Optional) Add Status Endpoint

Add this endpoint to monitor adapter status:

```python
@router.get("/ws/adapter-status")
async def get_adapter_status():
    """Get current adapter integration status"""
    return adapter_wrapper.get_status()
```

## Environment Variables

Configure the adapter system using these environment variables:

```bash
# Enable/disable adapter system
ADAPTER_ENABLED=false  # Set to 'true' to enable

# Rollout percentage (0-100)
ADAPTER_ROLLOUT_PERCENTAGE=0  # Start with 0, increase gradually

# Shadow mode (compare adapter vs legacy)
SHADOW_MODE_ENABLED=false  # Set to 'true' for shadow mode
SHADOW_MODE_PERCENTAGE=1  # % of traffic to shadow
```

## Rollout Plan

1. **Test in Development**
   ```bash
   ADAPTER_ENABLED=true
   ADAPTER_ROLLOUT_PERCENTAGE=100
   ```

2. **Shadow Mode in Production**
   ```bash
   SHADOW_MODE_ENABLED=true
   SHADOW_MODE_PERCENTAGE=1  # Start with 1%
   ```
   Monitor logs for mismatches

3. **Gradual Production Rollout**
   ```bash
   ADAPTER_ENABLED=true
   ADAPTER_ROLLOUT_PERCENTAGE=1   # Start with 1%
   # Increase gradually: 1 → 5 → 10 → 25 → 50 → 100
   ```

4. **Full Rollout**
   ```bash
   ADAPTER_ENABLED=true
   ADAPTER_ROLLOUT_PERCENTAGE=100
   ```

## Monitoring

Once integrated, monitor:

1. **Adapter Status**: GET `/ws/adapter-status`
2. **Logs**: Look for "Adapter handled event" messages
3. **Errors**: Watch for "Adapter error" in logs
4. **Performance**: Monitor response times

## Rollback

To instantly rollback:

```bash
ADAPTER_ENABLED=false
```

Or reduce percentage:
```bash
ADAPTER_ROLLOUT_PERCENTAGE=0
```

## Testing the Integration

1. Start the server with adapters disabled
2. Verify existing functionality works
3. Enable adapters at 100% in dev
4. Test all WebSocket events
5. Check adapter status endpoint

## Current State (Post-Phase 7)

After Phase 7 completion, the system now:
- Uses clean architecture repositories directly (no legacy room_manager)
- Broadcasts via `infrastructure/websocket/connection_singleton.py`
- Has zero legacy dependencies or imports
- Runs 100% through the adapter system

### Key Changes from Original:
1. **Room validation** now uses `RoomApplicationService` instead of legacy room_manager
2. **Broadcasting** uses `connection_singleton` instead of legacy socket_manager
3. **All imports** updated to clean architecture components
4. **Legacy handlers** removed entirely

## Complete Diff Example (Historical Reference)

Here's what the original integration change looked like in diff format:

```diff
diff --git a/backend/api/routes/ws.py b/backend/api/routes/ws.py
index abc123..def456 100644
--- a/backend/api/routes/ws.py
+++ b/backend/api/routes/ws.py
@@ -20,6 +20,7 @@ from api.websocket.connection_manager import connection_manager
 from api.websocket.message_queue import message_queue_manager
+from api.routes.ws_adapter_wrapper import adapter_wrapper
 
 # Set up logging
 logger = logging.getLogger(__name__)
@@ -311,6 +312,17 @@ async def websocket_endpoint(websocket: WebSocket, room_id: str):
                 )
                 continue
 
+            # ===== ADAPTER INTEGRATION START =====
+            # Try adapter system first (if enabled)
+            adapter_response = await adapter_wrapper.try_handle_with_adapter(
+                registered_ws, message, room_id
+            )
+            
+            if adapter_response is not None:
+                if adapter_response:
+                    await registered_ws.send_json(adapter_response)
+                continue
+            # ===== ADAPTER INTEGRATION END =====
+
             event_name = message.get("event")
             # Use sanitized data instead of raw event data
```

## Verification Steps

After integration:

1. Check adapter status:
   ```bash
   curl http://localhost:8000/ws/adapter-status
   ```

2. Test a simple message (ping):
   - Connect WebSocket to `/ws/lobby`
   - Send: `{"event": "ping", "data": {"timestamp": 123}}`
   - Should receive pong response

3. Check logs for adapter activity

4. Verify fallback works by disabling adapters

## Troubleshooting

**Problem**: Adapters not working
- Check: Is `ADAPTER_ENABLED=true`?
- Check: Is `ADAPTER_ROLLOUT_PERCENTAGE` > 0?
- Check: Are there errors in logs?

**Problem**: Different behavior with adapters
- Enable shadow mode to compare
- Check adapter implementation matches legacy
- Review mismatch logs

**Problem**: Performance issues
- Check adapter status for overhead
- Reduce rollout percentage
- Review adapter performance metrics

## Next Steps

Once integrated and tested:

1. Enable shadow mode at 1%
2. Monitor for 24 hours
3. Increase shadow mode to 10%
4. Begin actual rollout at 1%
5. Gradually increase to 100%

This completes the WebSocket adapter integration!