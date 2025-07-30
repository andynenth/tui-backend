# Troubleshooting & Debugging Guide

## Overview

This guide provides systematic approaches to diagnosing and fixing common issues in the Liap Tui game system, from development environment problems to production deployment issues.

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Development Environment Issues](#development-environment-issues)
3. [WebSocket Connection Problems](#websocket-connection-problems)
4. [Game State Synchronization Issues](#game-state-synchronization-issues)
5. [Performance Problems](#performance-problems)
6. [Error Analysis](#error-analysis)
7. [Debugging Tools](#debugging-tools)
8. [Production Issues](#production-issues)
9. [Common Scenarios](#common-scenarios)

---

## Quick Diagnosis

### Health Check Checklist

1. **Backend Running?**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "healthy"}
   ```

2. **Frontend Building?**
   ```bash
   cd frontend && npm run build
   # Should complete without errors
   ```

3. **WebSocket Connection?**
   - Open browser developer tools → Network tab
   - Look for WebSocket connection to `ws://localhost:8000/ws/`
   - Status should be "101 Switching Protocols"

4. **Database Connected?** (if using)
   ```bash
   # Check backend logs for database connection errors
   tail -f backend/logs/app.log
   ```

### Symptom-Based Quick Fixes

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| "Cannot connect to server" | Backend not running | `./start.sh` or `cd backend && python -m api.main` |
| White screen in browser | Frontend build error | Check browser console, run `npm run dev` |
| "Room not found" error | Room doesn't exist | Create new room or check room ID |
| Players can't see each other | WebSocket connection issue | Check network tab, restart backend |
| Game actions not working | State machine error | Check backend logs, verify phase |

---

## Development Environment Issues

### Python/Backend Problems

#### Virtual Environment Issues
```bash
# Symptom: ImportError or module not found
# Fix: Ensure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify correct Python
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

#### Port Already in Use
```bash
# Symptom: "Address already in use: 8000"
# Fix: Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
# Edit backend/api/main.py:
# uvicorn.run(app, host="0.0.0.0", port=8001)
```

#### Import Errors
```bash
# Symptom: "ModuleNotFoundError: No module named 'engine'"
# Fix: Check PYTHONPATH or run from correct directory
cd backend
python -m api.main

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
```

### Node.js/Frontend Problems

#### Dependency Issues
```bash
# Symptom: Module not found or build errors
# Fix: Clear and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 16+
npm --version   # Should be 8+
```

#### ESBuild Errors
```bash
# Symptom: Build fails or CSS not loading
# Fix: Check ESBuild configuration
cd frontend
npm run build 2>&1 | grep -i error

# Common fix: Update esbuild.config.cjs
# Ensure CSS imports are properly configured
```

#### TypeScript Errors
```bash
# Check TypeScript compilation
npm run type-check

# Common issues:
# - Missing type definitions: npm install @types/...
# - Incorrect imports: Check file paths and extensions
# - Type mismatches: Review interface definitions
```

### Docker Issues

#### Container Build Failures
```bash
# Symptom: Docker build fails
# Debug: Build with verbose output
docker build --no-cache --progress=plain -t liap-tui .

# Common fixes:
# - Update Dockerfile base image
# - Check .dockerignore includes node_modules
# - Verify requirements.txt is up to date
```

#### Container Runtime Issues
```bash
# Symptom: Container exits immediately
# Debug: Check container logs
docker logs <container_id>

# Run interactive shell for debugging
docker run -it --entrypoint /bin/bash liap-tui

# Check port mapping
docker run -p 8000:8000 -p 3000:3000 liap-tui
```

---

## WebSocket Connection Problems

### Connection Refused

#### Symptom
```
WebSocket connection to 'ws://localhost:8000/ws/ROOM123' failed: Error in connection establishment
```

#### Diagnosis
1. **Check backend status**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify WebSocket endpoint**:
   ```bash
   # Use wscat to test WebSocket
   npm install -g wscat
   wscat -c ws://localhost:8000/ws/test
   ```

3. **Check firewall/proxy**:
   - Corporate firewalls may block WebSocket connections
   - Try with different network or VPN

#### Solutions
```python
# Backend: Ensure WebSocket route is registered
from fastapi import FastAPI, WebSocket
app = FastAPI()

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # ... implementation
```

### Connection Drops Frequently

#### Symptoms
- Frequent "Disconnected" status in UI
- Messages not being delivered
- Game state becomes out of sync

#### Diagnosis
```javascript
// Frontend: Add connection monitoring
const ws = new WebSocket('ws://localhost:8000/ws/ROOM123');

ws.onclose = (event) => {
    console.log('WebSocket closed:', {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean
    });
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};
```

#### Common Causes & Solutions

1. **Browser tab inactive** (browser throttling):
   ```javascript
   // Solution: Implement heartbeat/keepalive
   setInterval(() => {
       if (ws.readyState === WebSocket.OPEN) {
           ws.send(JSON.stringify({event: 'heartbeat', data: {}}));
       }
   }, 30000);
   ```

2. **Network timeout**:
   ```python
   # Backend: Increase timeout settings
   @app.websocket("/ws/{room_id}")
   async def websocket_endpoint(websocket: WebSocket, room_id: str):
       await websocket.accept()
       # Add periodic ping
       asyncio.create_task(send_ping(websocket))
   ```

3. **Proxy/Load balancer**:
   ```nginx
   # Nginx configuration for WebSocket
   location /ws/ {
       proxy_pass http://backend;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_read_timeout 86400;
   }
   ```

### CORS Issues

#### Symptom
```
Access to WebSocket at 'ws://localhost:8000/ws/ROOM123' from origin 'http://localhost:3000' has been blocked by CORS policy
```

#### Solution
```python
# Backend: Configure CORS properly
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Game State Synchronization Issues

### State Machine Errors

#### Symptom
```
ERROR: Invalid transition from TURN to DECLARATION
ERROR: Action 'declare' not allowed in phase 'turn'
```

#### Diagnosis
```python
# Backend: Add state machine debugging
class GameStateMachine:
    async def transition_to_phase(self, next_phase: GamePhase):
        current = self.current_phase
        if next_phase not in self.valid_transitions.get(current, []):
            logger.error(f"Invalid transition: {current} -> {next_phase}")
            logger.error(f"Valid transitions: {self.valid_transitions[current]}")
            # Add detailed state dump
            logger.error(f"Current state: {self.get_debug_state()}")
```

#### Solutions
1. **Reset game state**:
   ```bash
   # Delete room and recreate
   # Check backend logs for state machine sequence
   ```

2. **Fix transition logic**:
   ```python
   # Ensure all transition conditions are met
   def check_transition_conditions(self) -> Optional[GamePhase]:
       if self.phase == GamePhase.DECLARATION:
           if len(self.declarations) >= len(self.players):
               return GamePhase.TURN
       return None
   ```

### Desynchronization Between Clients

#### Symptom
- Players see different game states
- Actions accepted by one client but rejected by others
- UI shows inconsistent information

#### Diagnosis
```javascript
// Frontend: Add state validation
function validateGameState(newState, oldState) {
    if (newState.sequence <= oldState.sequence) {
        console.warn('Received old state:', {new: newState.sequence, old: oldState.sequence});
    }
    
    if (newState.phase !== oldState.phase) {
        console.log('Phase transition:', {from: oldState.phase, to: newState.phase});
    }
}
```

#### Solutions
1. **Force resynchronization**:
   ```javascript
   // Frontend: Request complete state sync
   networkService.send(roomId, 'sync_request', {
       last_sequence: currentSequence
   });
   ```

2. **Check enterprise architecture**:
   ```python
   # Backend: Ensure all state changes use enterprise pattern
   # ✅ CORRECT
   await self.update_phase_data({
       'current_player': next_player
   }, "Advanced to next player")
   
   # ❌ WRONG - bypasses automatic broadcasting
   self.phase_data['current_player'] = next_player
   ```

### Bot Behavior Issues

#### Symptom
- Bots not making moves
- Bot actions causing errors
- Bots stuck in infinite loops

#### Diagnosis
```python
# Backend: Add bot debugging
class BotManager:
    async def process_bot_action(self, bot_name: str, phase: GamePhase):
        logger.info(f"Bot {bot_name} processing action in phase {phase}")
        try:
            action = await self.calculate_bot_action(bot_name, phase)
            logger.info(f"Bot {bot_name} chose action: {action}")
            return action
        except Exception as e:
            logger.error(f"Bot {bot_name} error: {e}")
            # Add fallback action
            return self.get_safe_fallback_action(phase)
```

---

## Performance Problems

### Slow WebSocket Messages

#### Symptoms
- Noticeable delay between action and UI update
- High latency in multiplayer interactions
- Messages appearing out of order

#### Diagnosis
```javascript
// Frontend: Measure message latency
const startTime = performance.now();
networkService.send(roomId, 'play', data);

// In message handler
const endTime = performance.now();
console.log(`Message round-trip: ${endTime - startTime}ms`);
```

#### Solutions
1. **Optimize message size**:
   ```python
   # Backend: Reduce payload size
   def serialize_game_state(game_state):
       return {
           'essential_fields_only': True,
           'player_positions': [p.position for p in players],
           # Avoid sending entire piece objects
           'hand_counts': {p.name: len(p.hand) for p in players}
       }
   ```

2. **Message batching**:
   ```python
   # Backend: Batch multiple updates
   class MessageBatcher:
       def __init__(self):
           self.pending_messages = []
           
       async def queue_message(self, message):
           self.pending_messages.append(message)
           if len(self.pending_messages) >= 10:
               await self.flush_messages()
   ```

### Memory Leaks

#### Symptoms
- Frontend memory usage increases over time
- Browser becomes unresponsive
- Backend memory usage grows continuously

#### Diagnosis
```javascript
// Frontend: Monitor memory usage
setInterval(() => {
    if (performance.memory) {
        console.log('Memory usage:', {
            used: Math.round(performance.memory.usedJSHeapSize / 1048576),
            total: Math.round(performance.memory.totalJSHeapSize / 1048576),
            limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576)
        });
    }
}, 10000);
```

#### Solutions
1. **Clean up event listeners**:
   ```javascript
   // Frontend: Proper cleanup in React
   useEffect(() => {
       const handleMessage = (event) => { /* ... */ };
       ws.addEventListener('message', handleMessage);
       
       return () => {
           ws.removeEventListener('message', handleMessage);
       };
   }, []);
   ```

2. **Backend connection cleanup**:
   ```python
   # Backend: Ensure WebSocket cleanup
   @app.websocket("/ws/{room_id}")
   async def websocket_endpoint(websocket: WebSocket, room_id: str):
       try:
           await handle_websocket(websocket, room_id)
       finally:
           await cleanup_websocket(websocket, room_id)
   ```

---

## Error Analysis

### Backend Error Patterns

#### State Machine Errors
```python
# Common patterns in logs:
# "Invalid action 'X' in phase 'Y'" - Action validation failed
# "Transition condition not met" - Phase transition blocked
# "Player not found" - Player left during action
# "Game object not serializable" - JSON serialization failed

# Solution: Add comprehensive logging
logger.info(f"Processing action {action.type} from {action.player_name}")
logger.debug(f"Current phase data: {self.phase_data}")
```

#### WebSocket Errors
```python
# Common patterns:
# "Connection closed unexpectedly" - Client disconnected
# "Message too large" - Payload exceeds size limit
# "Invalid JSON" - Malformed message from client

# Solution: Add error handling and validation
try:
    message = json.loads(text_data)
except json.JSONDecodeError:
    await websocket.send_text(json.dumps({
        "event": "error",
        "data": {"message": "Invalid JSON format"}
    }))
```

### Frontend Error Patterns

#### React Errors
```javascript
// Common patterns in console:
// "Cannot read property 'X' of undefined" - Missing null checks
// "Warning: Each child in a list should have a unique key" - Missing React keys
// "Warning: Cannot update component while rendering" - State updates in render

// Solution: Add defensive programming
const PlayerComponent = ({ player }) => {
    if (!player) return <div>Loading...</div>;
    
    return (
        <div key={player.id}>
            {player.name}
        </div>
    );
};
```

#### Network Errors
```javascript
// Common patterns:
// "WebSocket connection closed" - Connection lost
// "Failed to send message" - WebSocket not ready
// "Timeout waiting for response" - Server not responding

// Solution: Add retry logic and error boundaries
class ErrorBoundary extends React.Component {
    componentDidCatch(error, errorInfo) {
        console.error('Game error:', error, errorInfo);
        // Send error report to logging service
    }
}
```

---

## Debugging Tools

### Browser Developer Tools

#### Network Tab
```
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by "WS" to see WebSocket traffic
4. Click on WebSocket connection to see messages
5. Look for connection status and message flow
```

#### Console Debugging
```javascript
// Add debug helpers
window.debugGame = {
    getState: () => gameService.getState(),
    sendMessage: (event, data) => networkService.send(roomId, event, data),
    forceSync: () => networkService.send(roomId, 'sync_request', {}),
    logState: () => console.table(gameService.getState())
};

// Use in browser console:
// debugGame.getState()
// debugGame.logState()
```

### Backend Debugging

#### Logging Configuration
```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game.log'),
        logging.StreamHandler()
    ]
)

# Add request ID for tracing
import uuid
request_id = str(uuid.uuid4())[:8]
logger.info(f"[{request_id}] Processing action: {action}")
```

#### Interactive Debugging
```python
# Add breakpoints for debugging
import pdb

class GameStateMachine:
    async def process_action(self, action):
        if action.type == ActionType.DECLARE:
            pdb.set_trace()  # Debugger will stop here
            # Examine variables: action, self.current_phase, etc.
```

### Testing Tools

#### WebSocket Testing
```bash
# Manual WebSocket testing
wscat -c ws://localhost:8000/ws/DEBUG_ROOM

# Send test messages
{"event": "client_ready", "data": {}}
{"event": "declare", "data": {"player_name": "Test", "value": 3}}
```

#### Load Testing
```javascript
// Simple load test
async function createMultipleConnections(count) {
    const connections = [];
    
    for (let i = 0; i < count; i++) {
        const ws = new WebSocket(`ws://localhost:8000/ws/LOAD_TEST_${i}`);
        connections.push(ws);
        
        ws.onopen = () => {
            ws.send(JSON.stringify({
                event: 'client_ready',
                data: {}
            }));
        };
    }
    
    return connections;
}
```

### Monitoring Tools

#### Health Checks
```python
# Backend health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "active_rooms": len(room_manager.rooms),
        "active_connections": socket_manager.connection_count()
    }
```

#### Metrics Collection
```javascript
// Frontend performance monitoring
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            messageCount: 0,
            averageLatency: 0,
            errorCount: 0
        };
    }
    
    recordMessage(latency) {
        this.metrics.messageCount++;
        this.metrics.averageLatency = 
            (this.metrics.averageLatency + latency) / 2;
    }
    
    getReport() {
        return this.metrics;
    }
}
```

---

## Production Issues

### Deployment Problems

#### Environment Variables
```bash
# Check required environment variables
echo "FRONTEND_URL: $FRONTEND_URL"
echo "BACKEND_URL: $BACKEND_URL"
echo "NODE_ENV: $NODE_ENV"

# Common production settings
export NODE_ENV=production
export FRONTEND_URL=https://your-domain.com
export BACKEND_URL=https://api.your-domain.com
```

#### SSL/HTTPS Issues
```nginx
# Nginx configuration for production
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    # WebSocket upgrade
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Scaling Issues

#### Connection Limits
```python
# Monitor connection limits
import psutil

def check_system_resources():
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "open_files": len(psutil.Process().open_files())
    }
```

#### Database Performance
```python
# Add connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600
)
```

---

## Common Scenarios

### Scenario 1: Players Can't Join Room

**Symptoms**: "Room not found" error when joining

**Diagnosis Steps**:
1. Verify room ID is correct
2. Check if room still exists in backend
3. Verify backend is running and accessible
4. Check WebSocket connection

**Solutions**:
```python
# Backend: Add room existence check
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    if room_id not in room_manager.rooms:
        await websocket.send_text(json.dumps({
            "event": "error",
            "data": {"message": f"Room {room_id} not found"}
        }))
        await websocket.close()
        return
```

### Scenario 2: Game Stuck in Phase

**Symptoms**: Game doesn't progress to next phase despite conditions being met

**Diagnosis Steps**:
1. Check backend logs for transition conditions
2. Verify all players have completed required actions
3. Check for bot processing errors
4. Review state machine logic

**Solutions**:
```python
# Add automatic timeout for stuck phases
class GameState:
    def __init__(self):
        self.phase_timeout = 60  # seconds
        
    async def check_timeout(self):
        if time.time() - self.phase_start_time > self.phase_timeout:
            logger.warning(f"Phase {self.current_phase} timed out")
            await self.force_phase_transition()
```

### Scenario 3: Bots Not Responding

**Symptoms**: Bot players don't make moves, game waits indefinitely

**Diagnosis Steps**:
1. Check bot manager logs
2. Verify bot is enabled for the phase
3. Check bot decision-making logic
4. Review bot action validation

**Solutions**:
```python
# Add bot fallback actions
class BotManager:
    async def get_safe_action(self, bot_name: str, phase: GamePhase):
        try:
            return await self.calculate_optimal_action(bot_name, phase)
        except Exception as e:
            logger.error(f"Bot {bot_name} calculation failed: {e}")
            # Return safe fallback
            if phase == GamePhase.DECLARATION:
                return {"event": "declare", "data": {"value": 0}}
            elif phase == GamePhase.TURN:
                return {"event": "play", "data": {"pieces": [0]}}
```

---

## Getting Help

### Information to Gather

When reporting issues, include:

1. **Environment Details**:
   - Operating system and version
   - Node.js and Python versions
   - Browser type and version (for frontend issues)

2. **Reproduction Steps**:
   - Exact steps to reproduce the issue
   - Expected vs actual behavior
   - Screenshots or video if relevant

3. **Log Output**:
   - Backend console output
   - Browser console errors
   - Network tab WebSocket messages

4. **Configuration**:
   - Environment variables
   - Any custom modifications
   - Deployment method (local, Docker, cloud)

### Log Collection Script

```bash
#!/bin/bash
# collect-logs.sh - Gather debugging information

echo "=== System Information ===" > debug-info.txt
uname -a >> debug-info.txt
node --version >> debug-info.txt
python --version >> debug-info.txt

echo "=== Backend Logs ===" >> debug-info.txt
tail -100 backend/logs/app.log >> debug-info.txt

echo "=== Frontend Build Output ===" >> debug-info.txt
cd frontend && npm run build >> ../debug-info.txt 2>&1

echo "Debug information collected in debug-info.txt"
```

---

## Conclusion

This troubleshooting guide covers the most common issues encountered in the Liap Tui system. The enterprise architecture and comprehensive logging make most issues traceable and fixable with systematic debugging approaches.

For additional support, refer to:
- [Technical Architecture Deep Dive](TECHNICAL_ARCHITECTURE_DEEP_DIVE.md) - Understanding system design
- [API Reference Manual](API_REFERENCE_MANUAL.md) - WebSocket and API documentation
- [Developer Onboarding Guide](DEVELOPER_ONBOARDING_GUIDE.md) - Development environment setup

Remember: The enterprise architecture's automatic broadcasting and event sourcing provide excellent debugging capabilities - use them to your advantage when diagnosing issues.

---

*Last updated: January 2024*