# Comprehensive Debugging & Troubleshooting Guide

## Overview

This guide provides complete debugging and troubleshooting strategies for Liap Tui, covering development issues, production problems, and specific scenarios like disconnections.

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Debugging Tools](#debugging-tools)
3. [Development Environment Issues](#development-environment-issues)
4. [WebSocket Connection Problems](#websocket-connection-problems)
5. [State Synchronization Issues](#state-synchronization-issues)
6. [Disconnect & Reconnection Issues](#disconnect--reconnection-issues)
7. [Common Backend Issues](#common-backend-issues)
8. [Common Frontend Issues](#common-frontend-issues)
9. [Performance Problems](#performance-problems)
10. [Production Debugging](#production-debugging)
11. [Error Analysis](#error-analysis)
12. [Debug Utilities](#debug-utilities)
13. [Troubleshooting Checklist](#troubleshooting-checklist)

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

4. **Database Connected?**
   ```bash
   # Check backend logs for database connection errors
   tail -f backend/logs/app.log
   # Check SQLite database
   sqlite3 game_events.db ".tables"
   ```

### Symptom-Based Quick Fixes

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| "Cannot connect to server" | Backend not running | Run `./start.sh` or `docker-compose up` |
| Blank white screen | Frontend build failed | Check console, run `npm install` |
| WebSocket disconnects | Proxy/firewall timeout | Enable heartbeat, check nginx config |
| Game state not updating | State sync issue | Refresh page, check phase_change events |
| Players can't join | Room full or wrong ID | Verify room ID, check player count |
| Bot not playing | AI logic error | Check logs for AI errors |

### Emergency Commands

```bash
# Full restart
docker-compose down && docker-compose up --build

# Clear all game state
rm -f game_events.db && ./start.sh

# Debug mode with verbose logging
LOG_LEVEL=DEBUG ./start.sh

# Check all services
./scripts/health_check.sh
```

## Debugging Tools

### Backend Tools

#### 1. Python Debugger (pdb)

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint() in Python 3.7+
breakpoint()

# Common pdb commands:
# n - next line
# s - step into
# c - continue
# l - list code
# p variable - print variable
# pp variable - pretty print
# h - help
# w - where (stack trace)
```

#### 2. Logging Configuration

```python
# backend/utils/logging_config.py
import logging

# Set debug level for specific modules
logging.getLogger("engine.game").setLevel(logging.DEBUG)
logging.getLogger("api.websocket").setLevel(logging.DEBUG)

# Add custom logger
logger = logging.getLogger(__name__)
logger.debug(f"Game state: {game.get_state()}")
logger.info(f"Player {player} joined room {room_id}")
logger.error(f"Invalid play: {error}", exc_info=True)
```

#### 3. WebSocket Debugging

```python
# Enable WebSocket debug logging
@websocket.route("/ws/<room_id>")
async def game_websocket(request, ws, room_id):
    # Log all messages
    async for message in ws:
        logger.debug(f"Received: {message}")
        response = await handle_message(message)
        logger.debug(f"Sending: {response}")
        await ws.send(response)
```

### Frontend Tools

#### 1. Browser DevTools

```javascript
// Enable verbose logging
localStorage.setItem('DEBUG', '*');

// Log all WebSocket messages
const originalSend = WebSocket.prototype.send;
WebSocket.prototype.send = function(data) {
    console.log('WS Send:', data);
    originalSend.call(this, data);
};
```

#### 2. React DevTools

```javascript
// Install React DevTools browser extension
// Then in console:
$r // Current React component
$r.props // Component props
$r.state // Component state (if class component)
```

#### 3. Network Debugging

```javascript
// Monitor WebSocket frames
// Chrome DevTools → Network → WS → Frames

// Log all game events
window.addEventListener('game-event', (e) => {
    console.log('Game Event:', e.detail);
});
```

### Performance Profiling

```bash
# Backend profiling
python -m cProfile -o profile.stats backend/main.py

# Analyze profile
python -m pstats profile.stats
> sort cumtime
> stats 20

# Frontend profiling
# Use Chrome DevTools Performance tab
# Record → Perform actions → Stop → Analyze
```

## Development Environment Issues

### Docker Problems

#### Container Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Common fixes:
# 1. Port already in use
lsof -i :8000  # Kill process using port
lsof -i :5050

# 2. Docker daemon not running
sudo systemctl start docker  # Linux
open /Applications/Docker.app  # macOS

# 3. Out of disk space
docker system prune -a
```

#### Build Failures

```bash
# Clear Docker cache
docker-compose build --no-cache

# Remove all containers and images
docker-compose down -v
docker system prune -a

# Check Dockerfile syntax
docker build -f backend/Dockerfile .
```

### Python Environment

#### Module Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or 'venv\Scripts\activate' on Windows

# Reinstall requirements
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Version Conflicts

```bash
# Check Python version (need 3.8+)
python --version

# Use pyenv to manage versions
pyenv install 3.11.0
pyenv local 3.11.0

# Create fresh virtual environment
python -m venv venv_new
source venv_new/bin/activate
pip install -r requirements.txt
```

### Frontend Environment

#### NPM/Node Issues

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Use correct Node version (need 18+)
nvm use 18
nvm install 18.19.0
```

#### Build Errors

```javascript
// Common ESBuild issues
// 1. Missing dependencies
npm install --save-dev @types/react @types/react-dom

// 2. TypeScript errors
// Add to tsconfig.json:
{
    "compilerOptions": {
        "skipLibCheck": true,
        "allowJs": true
    }
}

// 3. Module resolution
// Check imports use correct paths
import { GameService } from './services/GameService'; // ✓
import { GameService } from 'services/GameService';  // ✗
```

## WebSocket Connection Problems

### Connection Failures

#### Browser Can't Connect

```javascript
// Debug connection attempts
const ws = new WebSocket('ws://localhost:8000/ws/lobby');

ws.onopen = () => console.log('Connected');
ws.onerror = (e) => console.error('Error:', e);
ws.onclose = (e) => console.log('Closed:', e.code, e.reason);

// Common issues:
// 1. Wrong URL (check protocol: ws:// not http://)
// 2. CORS issues (backend should handle)
// 3. Firewall blocking WebSocket
```

#### Connection Drops

```javascript
// Implement reconnection logic
class ReconnectingWebSocket {
    constructor(url) {
        this.url = url;
        this.reconnectDelay = 1000;
        this.shouldReconnect = true;
        this.connect();
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onclose = () => {
            if (this.shouldReconnect) {
                setTimeout(() => this.connect(), this.reconnectDelay);
                this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
            }
        };

        this.ws.onopen = () => {
            this.reconnectDelay = 1000;
            console.log('WebSocket reconnected');
        };
    }
}
```

### Proxy/Nginx Configuration

```nginx
# nginx.conf for WebSocket support
location /ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    # Prevent timeout
    proxy_read_timeout 3600;
    proxy_send_timeout 3600;
}
```

### Message Format Issues

```python
# Backend: Validate message format
async def handle_message(message_str):
    try:
        message = json.loads(message_str)
        if 'event' not in message or 'data' not in message:
            raise ValueError("Invalid message format")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON: {message_str}")
        return {"event": "error", "data": {"message": "Invalid JSON"}}
```

## State Synchronization Issues

### Phase Mismatch

```python
# Backend: Log all phase changes
@state_machine.before_transition
def log_transition(event_data):
    logger.info(f"Phase transition: {event_data.transition.source} → {event_data.transition.dest}")
    logger.debug(f"Event: {event_data.event.name}, Args: {event_data.args}")
```

```javascript
// Frontend: Verify phase updates
gameService.on('phase_change', (data) => {
    console.log('Phase changed to:', data.phase);
    console.log('Phase data:', data.phase_data);
    console.log('Sequence:', data.sequence);

    // Check if frontend phase matches
    if (gameService.currentPhase !== data.phase) {
        console.error('Phase mismatch!', {
            frontend: gameService.currentPhase,
            backend: data.phase
        });
    }
});
```

### Missing Updates

```python
# Backend: Ensure all clients receive updates
async def broadcast_to_room(room_id, event, data):
    room = rooms.get(room_id)
    if not room:
        logger.error(f"Room {room_id} not found for broadcast")
        return

    failed_clients = []
    for client_id, websocket in room.clients.items():
        try:
            await websocket.send(json.dumps({
                "event": event,
                "data": data,
                "sequence": room.sequence_number
            }))
        except Exception as e:
            logger.error(f"Failed to send to client {client_id}: {e}")
            failed_clients.append(client_id)

    # Clean up failed clients
    for client_id in failed_clients:
        room.remove_client(client_id)
```

### Sequence Number Issues

```javascript
// Frontend: Track sequence numbers
let expectedSequence = 0;

gameService.on('message', (message) => {
    if (message.sequence) {
        if (message.sequence !== expectedSequence + 1) {
            console.warn('Sequence gap detected', {
                expected: expectedSequence + 1,
                received: message.sequence
            });
            // Request sync
            gameService.requestSync();
        }
        expectedSequence = message.sequence;
    }
});
```

## Disconnect & Reconnection Issues

### Player Cannot Reconnect

**Symptoms:**
- Player tries to join but gets "Room is full" error
- Player name is not recognized
- Connection fails repeatedly

**Solutions:**

1. **Verify Player Name**
   ```javascript
   // Must use exact same name (case-sensitive)
   const playerName = localStorage.getItem('playerName');
   console.log('Stored name:', playerName);

   // Remove any extra whitespace
   const cleanName = playerName.trim();
   ```

2. **Check Room Status**
   ```javascript
   // In browser console
   const state = gameService.getState();
   console.log('Room ID:', state.roomId);
   console.log('Players:', state.players);
   console.log('My slot:', state.mySlot);
   ```

3. **Backend Validation**
   ```python
   # Check if player can rejoin
   def can_rejoin(room_id, player_name):
       room = rooms.get(room_id)
       if not room:
           return False, "Room not found"

       player = room.get_player_by_name(player_name)
       if not player:
           return False, "Player not in room"

       if player.is_connected:
           return False, "Player already connected"

       if player.is_bot_active:
           # Bot took over - need to deactivate
           player.deactivate_bot()

       return True, "Can rejoin"
   ```

4. **Force Rejoin**
   ```javascript
   // Clear local state and rejoin
   localStorage.removeItem('gameState');
   sessionStorage.clear();

   // Attempt fresh connection
   const ws = new WebSocket(`ws://localhost:8000/ws/${roomId}`);
   ws.onopen = () => {
       ws.send(JSON.stringify({
           event: 'rejoin_room',
           data: {
               player_name: playerName,
               rejoin_token: localStorage.getItem('rejoinToken')
           }
       }));
   };
   ```

### Bot Not Taking Over

**Symptoms:**
- Game freezes when player disconnects
- Turn timer runs out without bot action
- Other players see no activity

**Solutions:**

1. **Check Bot Activation**
   ```python
   # Backend should log:
   logger.info(f"Player {player_name} disconnected from room {room_id}")
   logger.info(f"Bot activated for player {player_name}")

   # Verify in game state
   player = game.get_player(player_name)
   print(f"Is bot active: {player.is_bot_active}")
   print(f"Is connected: {player.is_connected}")
   ```

2. **Force Bot Activation**
   ```python
   # Manual bot activation
   async def activate_bot_for_player(room_id, player_name):
       room = rooms.get(room_id)
       game = room.game
       player = game.get_player(player_name)

       player.is_bot_active = True
       player.is_connected = False

       # If it's their turn, make bot play
       if game.current_phase == Phase.TURN:
           if game.current_player == player_name:
               await bot_make_turn(game, player)
   ```

3. **Debug Bot Decision Making**
   ```python
   # Add logging to bot logic
   def bot_decide_play(game_state, player):
       logger.debug(f"Bot deciding for {player.name}")
       logger.debug(f"Hand: {player.hand}")
       logger.debug(f"Current requirement: {game_state.required_pieces}")

       decision = calculate_best_play(player.hand, game_state)
       logger.info(f"Bot {player.name} decided: {decision}")

       return decision
   ```

### Reconnection Timeout Issues

**Problem:** Player disconnects briefly but can't rejoin because bot already active

**Solution:**
```python
# Add grace period for reconnection
RECONNECT_GRACE_PERIOD = 30  # seconds

class Player:
    def __init__(self):
        self.disconnect_time = None
        self.is_bot_active = False

    def handle_disconnect(self):
        self.disconnect_time = time.time()
        # Don't activate bot immediately
        asyncio.create_task(self._delayed_bot_activation())

    async def _delayed_bot_activation(self):
        await asyncio.sleep(RECONNECT_GRACE_PERIOD)

        # Check if still disconnected
        if not self.is_connected and self.disconnect_time:
            elapsed = time.time() - self.disconnect_time
            if elapsed >= RECONNECT_GRACE_PERIOD:
                self.activate_bot()
```

## Common Backend Issues

### Game State Corruption

```python
# Add state validation
def validate_game_state(game):
    errors = []

    # Check player count
    if len(game.players) != 4:
        errors.append(f"Invalid player count: {len(game.players)}")

    # Check hand sizes
    for player in game.players:
        if len(player.hand) > 8:
            errors.append(f"{player.name} has {len(player.hand)} cards")

    # Check phase validity
    if game.phase not in [Phase.WAITING, Phase.PREPARATION, ...]:
        errors.append(f"Invalid phase: {game.phase}")

    return errors

# Run validation after each action
errors = validate_game_state(game)
if errors:
    logger.error(f"State corruption detected: {errors}")
```

### Memory Leaks

```python
# Monitor WebSocket connections
import gc
import weakref

class ConnectionManager:
    def __init__(self):
        self.connections = weakref.WeakValueDictionary()

    def add_connection(self, client_id, websocket):
        self.connections[client_id] = websocket
        logger.info(f"Active connections: {len(self.connections)}")

    def remove_connection(self, client_id):
        self.connections.pop(client_id, None)
        gc.collect()  # Force garbage collection
        logger.info(f"Active connections after removal: {len(self.connections)}")
```

### Database Issues

```python
# SQLite debugging
import sqlite3

def debug_database():
    conn = sqlite3.connect('game_events.db')
    cursor = conn.cursor()

    # Check table structure
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")

    # Check event count
    cursor.execute("SELECT COUNT(*) FROM events")
    count = cursor.fetchone()[0]
    print(f"Total events: {count}")

    # Recent events
    cursor.execute("""
        SELECT timestamp, event_type, room_id
        FROM events
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        print(row)
```

## Common Frontend Issues

### React Re-render Loops

```javascript
// Detect excessive re-renders
let renderCount = 0;

function GameComponent() {
    useEffect(() => {
        renderCount++;
        if (renderCount > 100) {
            console.error('Excessive re-renders detected!');
            console.trace();
        }
    });

    // Use React.memo for expensive components
    return <ExpensiveChild />;
}

const ExpensiveChild = React.memo(({ data }) => {
    // Only re-renders if data changes
    return <div>{/* complex rendering */}</div>
});
```

### State Update Issues

```javascript
// Debug state updates
const [gameState, setGameState] = useState(initialState);

// Log all state changes
useEffect(() => {
    console.log('Game state updated:', gameState);
}, [gameState]);

// Ensure state updates are batched
const updateMultipleStates = () => {
    // React 18 auto-batches these
    setPlayerState(newPlayerState);
    setGamePhase(newPhase);
    setTurnData(newTurnData);
};
```

### Event Handler Memory Leaks

```javascript
// Cleanup event listeners
useEffect(() => {
    const handleGameEvent = (event) => {
        console.log('Game event:', event);
    };

    gameService.on('update', handleGameEvent);

    // Cleanup function
    return () => {
        gameService.off('update', handleGameEvent);
    };
}, []); // Empty deps = setup once
```

## Performance Problems

### Backend Performance

```python
# Profile slow endpoints
import time
from functools import wraps

def profile_endpoint(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start

        if duration > 1.0:  # Log slow requests
            logger.warning(f"{func.__name__} took {duration:.2f}s")

        return result
    return wrapper

@profile_endpoint
async def handle_play_action(game, player, pieces):
    # Implementation
    pass
```

### Frontend Performance

```javascript
// Use Chrome DevTools Performance profiler
// Or add custom timing:

performance.mark('render-start');

// Component render logic
render();

performance.mark('render-end');
performance.measure('render-time', 'render-start', 'render-end');

const measure = performance.getEntriesByName('render-time')[0];
if (measure.duration > 16) {  // Longer than one frame
    console.warn(`Slow render: ${measure.duration}ms`);
}
```

### WebSocket Performance

```python
# Monitor message sizes
async def send_message(websocket, message):
    data = json.dumps(message)
    size = len(data.encode('utf-8'))

    if size > 10000:  # 10KB warning
        logger.warning(f"Large message: {size} bytes for {message['event']}")

    await websocket.send(data)
```

## Production Debugging

### Remote Logging

```python
# Structured logging for production
import structlog

logger = structlog.get_logger()

logger.info("game_action",
    room_id=room_id,
    player=player_name,
    action="play",
    pieces=piece_count,
    phase=game.phase,
    round=game.round_number
)
```

### Error Tracking

```javascript
// Frontend error boundary
class ErrorBoundary extends React.Component {
    componentDidCatch(error, errorInfo) {
        console.error('React error:', error, errorInfo);

        // Send to error tracking service
        if (window.Sentry) {
            window.Sentry.captureException(error, {
                contexts: {
                    react: errorInfo
                }
            });
        }
    }

    render() {
        if (this.state.hasError) {
            return <h2>Something went wrong. Please refresh.</h2>;
        }
        return this.props.children;
    }
}
```

### Health Monitoring

```python
# Comprehensive health check endpoint
@app.get("/health/detailed")
async def health_detailed():
    checks = {
        "server": "healthy",
        "database": check_database_health(),
        "websocket_connections": len(active_connections),
        "active_games": len(active_games),
        "memory_usage": get_memory_usage(),
        "uptime": get_uptime()
    }

    status = "healthy" if all(
        v == "healthy" for k, v in checks.items()
        if k.endswith("_health")
    ) else "degraded"

    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

## Error Analysis

### Error Categorization

```python
# Classify errors for better debugging
class ErrorClassifier:
    @staticmethod
    def classify(error):
        if isinstance(error, ValidationError):
            return "validation", "client_error"
        elif isinstance(error, GameStateError):
            return "game_logic", "server_error"
        elif isinstance(error, ConnectionError):
            return "network", "infrastructure"
        else:
            return "unknown", "server_error"

    @staticmethod
    def get_user_message(error_type):
        messages = {
            "validation": "Please check your input and try again.",
            "game_logic": "An error occurred in the game. Please refresh.",
            "network": "Connection problem. Please check your internet.",
            "unknown": "An unexpected error occurred."
        }
        return messages.get(error_type, messages["unknown"])
```

### Error Patterns

```python
# Track error patterns
from collections import defaultdict
from datetime import datetime, timedelta

class ErrorTracker:
    def __init__(self):
        self.errors = defaultdict(list)

    def track(self, error_type, details):
        self.errors[error_type].append({
            "timestamp": datetime.now(),
            "details": details
        })

        # Check for patterns
        recent_errors = self._get_recent_errors(error_type, minutes=5)
        if len(recent_errors) > 10:
            logger.critical(f"High error rate for {error_type}: {len(recent_errors)} in 5 minutes")

    def _get_recent_errors(self, error_type, minutes):
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [e for e in self.errors[error_type] if e["timestamp"] > cutoff]
```

## Debug Utilities

### Game State Inspector

```python
# backend/debug/inspector.py
class GameStateInspector:
    @staticmethod
    def inspect(game):
        """Generate detailed game state report"""
        report = {
            "phase": game.phase,
            "round": game.round_number,
            "turn": game.turn_number,
            "players": {},
            "history": []
        }

        for player in game.players:
            report["players"][player.name] = {
                "connected": player.is_connected,
                "bot_active": player.is_bot_active,
                "hand_size": len(player.hand),
                "score": player.score,
                "declared": player.declared_piles,
                "captured": player.captured_piles
            }

        return report
```

### Frontend Debug Panel

```javascript
// Debug panel component
function DebugPanel({ gameState }) {
    const [visible, setVisible] = useState(false);

    // Toggle with keyboard shortcut
    useEffect(() => {
        const handleKeyPress = (e) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                setVisible(v => !v);
            }
        };

        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, []);

    if (!visible) return null;

    return (
        <div className="debug-panel">
            <h3>Debug Info</h3>
            <pre>{JSON.stringify(gameState, null, 2)}</pre>
            <button onClick={() => gameService.requestSync()}>
                Force Sync
            </button>
            <button onClick={() => console.log(gameService.getHistory())}>
                Log History
            </button>
        </div>
    );
}
```

### Network Traffic Monitor

```javascript
// Monitor all WebSocket traffic
class WebSocketMonitor {
    constructor() {
        this.messages = [];
        this.startMonitoring();
    }

    startMonitoring() {
        // Override WebSocket constructor
        const OriginalWebSocket = window.WebSocket;

        window.WebSocket = function(url, protocols) {
            const ws = new OriginalWebSocket(url, protocols);

            // Monitor sends
            const originalSend = ws.send;
            ws.send = (data) => {
                this.messages.push({
                    type: 'sent',
                    data: JSON.parse(data),
                    timestamp: Date.now()
                });
                originalSend.call(ws, data);
            };

            // Monitor receives
            ws.addEventListener('message', (event) => {
                this.messages.push({
                    type: 'received',
                    data: JSON.parse(event.data),
                    timestamp: Date.now()
                });
            });

            return ws;
        }.bind(this);
    }

    getMessages(eventType) {
        return this.messages.filter(m =>
            m.data.event === eventType
        );
    }

    exportLog() {
        const blob = new Blob([JSON.stringify(this.messages, null, 2)], {
            type: 'application/json'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `websocket-log-${Date.now()}.json`;
        a.click();
    }
}

// Usage
const monitor = new WebSocketMonitor();
// Later: monitor.exportLog();
```

## Troubleshooting Checklist

### Initial Setup Issues
- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed
- [ ] Docker running (if using containers)
- [ ] All ports available (8000, 5050)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend built (`npm install && npm run build`)

### Connection Issues
- [ ] Backend running and healthy
- [ ] Correct WebSocket URL
- [ ] No firewall blocking WebSocket
- [ ] Browser supports WebSocket
- [ ] Network tab shows 101 status
- [ ] No proxy interference

### Game State Issues
- [ ] Phase transitions logged
- [ ] All players receive updates
- [ ] Sequence numbers correct
- [ ] No state validation errors
- [ ] Database writes successful
- [ ] Memory usage normal

### Performance Issues
- [ ] Response times < 1s
- [ ] No memory leaks
- [ ] Database queries optimized
- [ ] Frontend renders < 16ms
- [ ] WebSocket messages < 10KB
- [ ] No excessive re-renders

### Production Issues
- [ ] Error tracking enabled
- [ ] Logging configured
- [ ] Health endpoints working
- [ ] Monitoring active
- [ ] Backups running
- [ ] SSL certificates valid

## Common Solutions Summary

1. **"It worked yesterday"** → Check what changed (git diff)
2. **"Works on my machine"** → Check environment differences
3. **"Random failures"** → Add logging, check race conditions
4. **"Slow performance"** → Profile, check N+1 queries
5. **"Connection drops"** → Check timeouts, add heartbeat
6. **"State mismatch"** → Verify event order, check sequences
7. **"Can't reproduce"** → Add more logging, check edge cases

## Getting Help

When reporting issues, include:

1. **Error messages** (full stack trace)
2. **Steps to reproduce**
3. **Environment details** (OS, versions)
4. **Relevant logs** (backend and frontend)
5. **Network trace** (for connection issues)
6. **Screenshots** (for UI issues)

### Log Locations
- Backend logs: `backend/logs/`
- Frontend console: Browser DevTools
- Docker logs: `docker-compose logs`
- System logs: `/var/log/` (Linux), Event Viewer (Windows)

---

*Remember: Most bugs are simple once you find them. Stay calm, be systematic, and the solution will reveal itself.*
