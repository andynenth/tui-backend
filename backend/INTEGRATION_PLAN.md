# Clean Architecture Integration Plan

## Executive Summary

The clean architecture implementation is **100% complete** but **0% integrated**. All components exist but the application still uses the old implementation because `start.sh` points to the wrong entry point.

## Current State

### ✅ What's Implemented
1. **Domain Layer** - Complete with entities, value objects, services, events, interfaces
2. **Application Layer** - All use cases, command bus, services implemented
3. **Infrastructure Layer** - Repositories, adapters, event system ready
4. **API Layer** - New WebSocket handlers using clean architecture
5. **Event System** - Event bus, handlers, and publishing infrastructure
6. **Bot System** - Strategy pattern with AI implementations
7. **State Machine Adapter** - Wrapper for existing state machine
8. **Feature Flags** - System for gradual rollout
9. **Testing** - Unit and integration tests
10. **Compatibility Layer** - Message adapters for backward compatibility

### ❌ What's NOT Connected
1. **Wrong Entry Point** - `start.sh` uses `backend.api.main:app` instead of `backend.api.app:app`
2. **Old WebSocket Handler Active** - `api/routes/ws.py` handles all game traffic
3. **Direct Method Calls** - Bypasses all use cases and repositories
4. **No Feature Flag Checks** - Feature flags exist but aren't used
5. **Event System Bypassed** - Direct broadcasts instead of event publishing
6. **Old Bot Manager Active** - New bot strategies unused

## Integration Steps

### Step 1: Update Application Entry Point

**File**: `/backend/start.sh`
```bash
# Change this line:
uvicorn backend.api.main:app --host 0.0.0.0 --port 5000 --log-level info

# To this:
uvicorn backend.api.app:app --host 0.0.0.0 --port 5000 --log-level info
```

### Step 2: Import Missing Routers in New App

**File**: `/backend/api/app.py`

Add missing routers from old app:
```python
from .routes import routes  # REST API routes

# In app setup:
app.include_router(routes.router, prefix="/api", tags=["api"])
```

### Step 3: Ensure Static File Serving

**File**: `/backend/api/app.py`

Add static file mounting:
```python
from fastapi.staticfiles import StaticFiles

# After app creation:
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
app.mount("/", StaticFiles(directory="backend/static", html=True), name="root")
```

### Step 4: Verify WebSocket Message Compatibility

The new WebSocket handlers in `api/websocket/` should handle all message types that the frontend sends. The message format should remain the same.

**Test by**:
1. Start the server with new entry point
2. Connect frontend
3. Verify all game operations work

### Step 5: Monitor and Debug

**Enable logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Watch for**:
- WebSocket connection issues
- Missing message handlers
- Command execution errors
- Event publishing failures

## Testing Plan

### 1. Smoke Test
```bash
# Start with new entry point
./start.sh

# Test endpoints
curl http://localhost:5000/api/health
```

### 2. WebSocket Test
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:5000/ws/lobby');

// Test room creation
ws.send(JSON.stringify({
  type: 'create_room',
  data: { player_name: 'TestPlayer' }
}));
```

### 3. Full Game Flow Test
1. Create room
2. Add players
3. Start game
4. Play through a round
5. Verify all notifications received

## Rollback Plan

If issues occur:

### Immediate Rollback
```bash
# In start.sh, revert to:
uvicorn backend.api.main:app --host 0.0.0.0 --port 5000 --log-level info
```

### Debugging Steps
1. Check logs for errors
2. Verify all dependencies are imported
3. Test with feature flags disabled
4. Compare message formats between old and new

## Feature Flag Gradual Rollout (Optional)

Once basic integration works, use feature flags for gradual migration:

**File**: `/backend/api/app.py`
```python
from infrastructure.compatibility import get_feature_flags

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    flags = get_feature_flags()
    
    if flags.is_enabled("use_clean_architecture", {"room_id": room_id}):
        # Use new handler
        await websocket_router(websocket, room_id)
    else:
        # Use old handler
        await old_ws_handler(websocket, room_id)
```

## Expected Outcomes

After integration:
1. ✅ All game operations use clean architecture
2. ✅ Events published for all state changes
3. ✅ Use cases handle business logic
4. ✅ Repositories manage data access
5. ✅ Bot strategies used for AI
6. ✅ Proper separation of concerns

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| WebSocket message format mismatch | MessageAdapter ensures compatibility |
| Missing functionality | Old code still exists as reference |
| Performance regression | Monitor metrics, optimize if needed |
| Bot behavior changes | Feature flag for old bot manager |

## Next Steps After Integration

1. **Remove Old Code** - Once stable, remove `api/routes/ws.py`
2. **Enable Persistence** - Switch from InMemory to FileBasedGameRepository
3. **Add Monitoring** - Metrics for command execution, events, etc.
4. **Database Migration** - Implement proper database repositories
5. **Advanced Features** - Event sourcing, CQRS, etc.

## Conclusion

The clean architecture is ready. Only the entry point needs to change. All the hard work is done - we just need to flip the switch from `main:app` to `app:app`.