# Domain Layer WebSocket Integration Guide

**Purpose**: Step-by-step guide for integrating the domain layer into ws.py with minimal code changes.

**Status**: Ready for implementation

## Prerequisites

Before starting, ensure you have:
1. Completed Phase 3 (Domain Layer) - ✅ Done
2. Completed Phase 3.5 (Infrastructure) - ✅ Done
3. Access to modify `api/routes/ws.py`
4. Ability to set environment variables

## Integration Steps

### Step 1: Add Import

Add this import at the top of `api/routes/ws.py` with the other imports:

```python
from api.adapters.domain_adapter_wrapper import domain_adapter_wrapper
```

### Step 2: Add Domain Handler

In the `websocket_endpoint` function, find the message handling section after validation.

Look for this code (around line 314):
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

Add this code RIGHT AFTER the validation, BEFORE any event handling:

```python
            # ===== DOMAIN ADAPTER INTEGRATION START =====
            # Try domain adapters first (if enabled)
            domain_response = await domain_adapter_wrapper.try_handle_with_domain(
                registered_ws, message, room_id
            )
            
            if domain_response is not None:
                # Domain adapter handled it
                await registered_ws.send_json(domain_response)
                continue  # Skip legacy handling
            # ===== DOMAIN ADAPTER INTEGRATION END =====
```

### Step 3: (Optional) Add Status Endpoint

Add this endpoint to `api/routes/ws.py` for monitoring:

```python
@router.get("/ws/domain-status")
async def get_domain_adapter_status():
    """Get current domain adapter integration status"""
    return domain_adapter_wrapper.get_status()
```

## Configuration

### Environment Variables

Set these environment variables to control the domain adapters:

```bash
# Enable/disable domain adapters
export DOMAIN_ADAPTERS_ENABLED=false  # Set to 'true' to enable

# For Docker, add to docker-compose.yml:
environment:
  - DOMAIN_ADAPTERS_ENABLED=false
```

### Supported Events

The domain adapters currently handle these game events:
- `start_game` - Start a new game
- `declare` - Make pile count declaration
- `play` / `play_pieces` - Play pieces in a turn
- `request_redeal` - Request a redeal for weak hand
- `accept_redeal` / `decline_redeal` - Respond to redeal request
- `redeal_decision` - Combined redeal decision

All other events fall through to legacy handling.

## Testing the Integration

### 1. Local Development Test

```bash
# Enable domain adapters
export DOMAIN_ADAPTERS_ENABLED=true

# Start the backend
cd backend
python main.py

# Check status
curl http://localhost:8003/api/ws/domain-status
```

### 2. Verify in Logs

When domain adapters are enabled, you'll see:
```
INFO: Domain adapters enabled via DOMAIN_ADAPTERS_ENABLED=true
DEBUG: Domain adapter handled start_game
```

### 3. Test Game Flow

1. Create a room (uses legacy)
2. Join room (uses legacy)
3. Start game (uses domain adapter)
4. Make declarations (uses domain adapter)
5. Play pieces (uses domain adapter)

## Rollback Procedure

If issues arise, disable domain adapters immediately:

```bash
# Disable domain adapters
export DOMAIN_ADAPTERS_ENABLED=false

# Or remove the environment variable entirely
unset DOMAIN_ADAPTERS_ENABLED
```

The system will immediately revert to legacy handling.

## Monitoring

### Check Adapter Status

```bash
# Get current status
curl http://localhost:8003/api/ws/domain-status
```

Response:
```json
{
  "domain_adapters": {
    "enabled": true,
    "repositories": {
      "room": "InMemoryRoomRepository"
    },
    "event_bus": {
      "type": "InMemoryEventBus",
      "handlers": 1
    },
    "adapters": {
      "game": "DomainGameAdapter"
    }
  },
  "environment": {
    "DOMAIN_ADAPTERS_ENABLED": "true"
  }
}
```

### Log Monitoring

Monitor logs for domain adapter activity:
```bash
# Watch for domain adapter logs
tail -f logs/app.log | grep -i "domain"
```

## Benefits of Domain Integration

1. **Clean Architecture**: Business logic separated from infrastructure
2. **Event Sourcing**: Complete audit trail of all game actions
3. **Better Testing**: Pure domain logic without WebSocket complexity
4. **Gradual Migration**: Can enable/disable per environment
5. **Type Safety**: Strong typing throughout domain layer

## Troubleshooting

### Domain adapters not working

1. Check environment variable is set correctly
2. Verify import was added to ws.py
3. Check logs for initialization message
4. Ensure code was added in correct location

### Errors in domain handling

1. Domain adapters automatically fall back to legacy on errors
2. Check logs for specific error messages
3. Disable if persistent issues occur

### Performance concerns

1. Domain adapters use in-memory implementations
2. Event publishing is asynchronous
3. Monitor response times in logs

## Next Steps

After successful integration:

1. Run in development for 1-2 days
2. Enable in staging environment
3. Monitor metrics and logs
4. Gradual production rollout
5. Eventually remove legacy code

## Support

For issues or questions:
- Check logs for detailed error messages
- Review domain adapter status endpoint
- Disable and report issues for investigation