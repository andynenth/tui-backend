# Debugging Guide - Common Issues and Solutions

## Table of Contents
1. [Overview](#overview)
2. [Debugging Tools](#debugging-tools)
3. [Common Backend Issues](#common-backend-issues)
4. [Common Frontend Issues](#common-frontend-issues)
5. [WebSocket Debugging](#websocket-debugging)
6. [State Synchronization Issues](#state-synchronization-issues)
7. [Performance Problems](#performance-problems)
8. [Production Debugging](#production-debugging)
9. [Debug Utilities](#debug-utilities)
10. [Troubleshooting Checklist](#troubleshooting-checklist)

## Overview

This guide helps you diagnose and fix common issues in Liap Tui. It covers debugging techniques, tools, and solutions to frequently encountered problems.

### Debugging Philosophy

1. **Reproduce First**: Always reproduce the issue before attempting fixes
2. **Isolate the Problem**: Narrow down to specific component
3. **Check Logs**: Logs often contain the answer
4. **Use Tools**: Leverage debugging tools effectively
5. **Document Findings**: Help future debugging efforts

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
```

#### 2. Logging Configuration

```python
# backend/config/logging.py
import logging
import sys

def setup_logging(log_level: str = "DEBUG"):
    """Configure comprehensive logging."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debug.log')
        ]
    )
    
    # Set specific loggers
    logging.getLogger("websockets").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    
    # Our app logger
    app_logger = logging.getLogger("liap_tui")
    app_logger.setLevel(logging.DEBUG)
    
    return app_logger

# Use in code
logger = logging.getLogger("liap_tui.game_engine")
logger.debug(f"Game state: {game.get_state()}")
logger.error(f"Invalid play: {play_data}", exc_info=True)
```

#### 3. FastAPI Debug Mode

```python
# backend/main.py
from fastapi import FastAPI
import os

# Enable debug mode in development
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

app = FastAPI(
    debug=DEBUG,
    title="Liap Tui API",
    docs_url="/api/docs" if DEBUG else None,
    redoc_url="/api/redoc" if DEBUG else None
)

# Add debug endpoints
if DEBUG:
    @app.get("/api/debug/state/{room_id}")
    async def get_game_state(room_id: str):
        """Debug endpoint to inspect game state."""
        if room_id in room_manager.game_state_machines:
            sm = room_manager.game_state_machines[room_id]
            return {
                "phase": sm.current_state.phase.value,
                "phase_data": sm.current_state.phase_data,
                "game": sm.game.to_debug_dict(),
                "history": sm.current_state.get_change_history()
            }
        return {"error": "Room not found"}
```

### Frontend Tools

#### 1. React Developer Tools

```tsx
// Use React DevTools browser extension
// Inspect component props, state, and hooks

// Add debug names to components
export const GameBoard = React.memo(({ gameState }) => {
    // Component logic
}, "GameBoard"); // Debug name

// Debug hooks
const useDebugValue = (value: any, format?: (v: any) => string) => {
    React.useDebugValue(format ? format(value) : value);
};

function useGameState() {
    const state = useContext(GameContext);
    useDebugValue(state, s => `Phase: ${s.phase}, Turn: ${s.turnNumber}`);
    return state;
}
```

#### 2. Console Debugging Helpers

```tsx
// frontend/src/debug/debugHelpers.ts
export const DebugHelpers = {
    // Log with timestamp and color
    log: (message: string, data?: any) => {
        const timestamp = new Date().toISOString();
        console.log(
            `%c[${timestamp}] ${message}`,
            'color: #3498db; font-weight: bold',
            data
        );
    },
    
    // Log errors with stack trace
    error: (message: string, error?: Error) => {
        console.error(
            `%c[ERROR] ${message}`,
            'color: #e74c3c; font-weight: bold',
            error
        );
        if (error?.stack) {
            console.error(error.stack);
        }
    },
    
    // Log WebSocket messages
    ws: (direction: 'SEND' | 'RECV', event: string, data: any) => {
        const arrow = direction === 'SEND' ? '→' : '←';
        const color = direction === 'SEND' ? '#2ecc71' : '#9b59b6';
        console.log(
            `%c[WS ${arrow}] ${event}`,
            `color: ${color}; font-weight: bold`,
            data
        );
    },
    
    // Performance timing
    time: (label: string) => {
        console.time(label);
        return () => console.timeEnd(label);
    }
};

// Global debug object
if (process.env.NODE_ENV === 'development') {
    (window as any).debug = {
        helpers: DebugHelpers,
        getGameState: () => gameContext.state,
        getNetworkStatus: () => NetworkService.getStatus(),
        clearCache: () => localStorage.clear(),
        enableVerboseLogging: () => {
            localStorage.setItem('debug_verbose', 'true');
        }
    };
}
```

#### 3. Network Debugging

```tsx
// Chrome DevTools Network tab
// Filter by WS to see WebSocket frames

// Add request interceptor
NetworkService.addInterceptor({
    onSend: (event, data) => {
        DebugHelpers.ws('SEND', event, data);
        // Modify or block if needed
        return { event, data };
    },
    
    onReceive: (event, data) => {
        DebugHelpers.ws('RECV', event, data);
        // Log specific events
        if (event === 'phase_change') {
            console.groupCollapsed('Phase Change Details');
            console.log('New Phase:', data.phase);
            console.log('Phase Data:', data.phase_data);
            console.log('Sequence:', data.sequence_number);
            console.groupEnd();
        }
        return { event, data };
    }
});
```

## Common Backend Issues

### Issue 1: WebSocket Connection Drops

**Symptoms**: Players disconnected randomly, "Connection lost" errors

**Debugging Steps**:
```python
# 1. Check WebSocket ping/pong
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    # Add ping interval
    ping_interval = 30  # seconds
    
    async def ping_loop():
        while True:
            await asyncio.sleep(ping_interval)
            try:
                await websocket.send_json({"event": "ping"})
                logger.debug(f"Ping sent to {websocket.client}")
            except:
                logger.error(f"Ping failed for {websocket.client}")
                break
    
    # Start ping task
    ping_task = asyncio.create_task(ping_loop())
```

**Common Causes & Solutions**:
1. **Nginx timeout**: Increase `proxy_read_timeout`
2. **CloudFlare timeout**: Use WebSocket compression
3. **Client network**: Implement reconnection logic

### Issue 2: State Machine Stuck

**Symptoms**: Game won't progress, actions ignored

**Debugging**:
```python
# Add state machine diagnostics
class GameStateMachine:
    def get_diagnostics(self) -> dict:
        """Get detailed state machine info."""
        return {
            "current_phase": self.current_state.phase.value,
            "phase_data": self.current_state.phase_data,
            "allowed_actions": self.current_state.get_allowed_actions(),
            "pending_actions": len(self.action_queue),
            "last_error": self.last_error,
            "transition_history": self.transition_history[-10:],
            "state_duration": time.time() - self.state_start_time
        }
    
    async def force_reset(self):
        """Emergency reset to known good state."""
        logger.warning(f"Force reset initiated for game {self.game.game_id}")
        
        # Save current state for debugging
        self.save_debug_snapshot()
        
        # Reset to PREPARATION
        self.current_state = PreparationState(self.game)
        await self.current_state.enter()
```

### Issue 3: Memory Leaks

**Symptoms**: Increasing memory usage, eventual OOM

**Detection**:
```python
# Memory profiling
import tracemalloc
import gc

# Start tracing
tracemalloc.start()

# Periodically check memory
async def memory_monitor():
    while True:
        await asyncio.sleep(60)  # Every minute
        
        # Get current memory usage
        current, peak = tracemalloc.get_traced_memory()
        logger.info(f"Memory: current={current/1024/1024:.1f}MB, peak={peak/1024/1024:.1f}MB")
        
        # Get top memory allocations
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        logger.info("Top 10 memory allocations:")
        for stat in top_stats[:10]:
            logger.info(stat)
        
        # Force garbage collection
        gc.collect()
```

**Common Leaks**:
1. **Unclosed connections**: Always cleanup in finally blocks
2. **Circular references**: Use weak references
3. **Event listeners**: Remove listeners when done

### Issue 4: Race Conditions

**Symptoms**: Inconsistent game state, duplicate actions

**Prevention**:
```python
# Use locks for critical sections
class RoomManager:
    def __init__(self):
        self.room_locks = {}
    
    async def process_action(self, room_id: str, action: GameAction):
        # Get or create lock for room
        if room_id not in self.room_locks:
            self.room_locks[room_id] = asyncio.Lock()
        
        async with self.room_locks[room_id]:
            # Process action atomically
            game_sm = self.game_state_machines[room_id]
            await game_sm.handle_action(action)
```

## Common Frontend Issues

### Issue 1: State Not Updating

**Symptoms**: UI doesn't reflect game changes

**Debugging**:
```tsx
// Check React renders
export const GameComponent: React.FC = () => {
    // Debug render count
    const renderCount = useRef(0);
    renderCount.current++;
    
    console.log(`GameComponent rendered ${renderCount.current} times`);
    
    // Check if state is actually changing
    const gameState = useGameState();
    useEffect(() => {
        console.log('Game state changed:', gameState);
    }, [gameState]);
    
    // Common issue: mutating state
    // ❌ Wrong
    gameState.players.push(newPlayer);
    
    // ✅ Correct
    setGameState({
        ...gameState,
        players: [...gameState.players, newPlayer]
    });
};
```

### Issue 2: WebSocket Messages Lost

**Symptoms**: Some updates missing, game out of sync

**Debugging**:
```tsx
// Add message queue diagnostics
class NetworkService {
    private messageLog: Array<{
        timestamp: number;
        direction: 'send' | 'receive';
        event: string;
        data: any;
        sequence?: number;
    }> = [];
    
    logMessage(direction: 'send' | 'receive', event: string, data: any) {
        this.messageLog.push({
            timestamp: Date.now(),
            direction,
            event,
            data,
            sequence: data.sequence_number
        });
        
        // Keep last 100 messages
        if (this.messageLog.length > 100) {
            this.messageLog.shift();
        }
    }
    
    checkMessageGaps(): number[] {
        const gaps: number[] = [];
        const sequences = this.messageLog
            .filter(m => m.sequence !== undefined)
            .map(m => m.sequence!)
            .sort((a, b) => a - b);
        
        for (let i = 1; i < sequences.length; i++) {
            if (sequences[i] - sequences[i-1] > 1) {
                for (let j = sequences[i-1] + 1; j < sequences[i]; j++) {
                    gaps.push(j);
                }
            }
        }
        
        return gaps;
    }
}
```

### Issue 3: Performance Issues

**Symptoms**: Laggy UI, slow reactions

**Profiling**:
```tsx
// React Profiler
import { Profiler } from 'react';

function onRenderCallback(
    id: string,
    phase: "mount" | "update",
    actualDuration: number,
    baseDuration: number,
    startTime: number,
    commitTime: number,
    interactions: Set<any>
) {
    console.log(`${id} (${phase}) took ${actualDuration}ms`);
    
    if (actualDuration > 16) {  // Over 60fps threshold
        console.warn(`Slow render in ${id}: ${actualDuration}ms`);
    }
}

<Profiler id="GameBoard" onRender={onRenderCallback}>
    <GameBoard {...props} />
</Profiler>

// Memo optimization
export const ExpensiveComponent = React.memo(({ data }) => {
    // Component logic
}, (prevProps, nextProps) => {
    // Custom comparison
    return prevProps.data.id === nextProps.data.id;
});
```

## WebSocket Debugging

### Connection Issues

```typescript
// frontend/src/debug/wsDebugger.ts
export class WebSocketDebugger {
    static analyze(ws: WebSocket) {
        console.group('WebSocket Analysis');
        console.log('URL:', ws.url);
        console.log('State:', this.getStateString(ws.readyState));
        console.log('Protocol:', ws.protocol);
        console.log('Binary Type:', ws.binaryType);
        console.log('Buffered:', ws.bufferedAmount);
        console.groupEnd();
    }
    
    static getStateString(state: number): string {
        switch(state) {
            case WebSocket.CONNECTING: return 'CONNECTING';
            case WebSocket.OPEN: return 'OPEN';
            case WebSocket.CLOSING: return 'CLOSING';
            case WebSocket.CLOSED: return 'CLOSED';
            default: return 'UNKNOWN';
        }
    }
    
    static monitorConnection(ws: WebSocket) {
        const events = ['open', 'close', 'error', 'message'];
        
        events.forEach(event => {
            ws.addEventListener(event, (e) => {
                console.log(`[WS ${event.toUpperCase()}]`, e);
                
                if (event === 'close') {
                    const closeEvent = e as CloseEvent;
                    console.log('Close code:', closeEvent.code);
                    console.log('Close reason:', closeEvent.reason);
                    console.log('Was clean:', closeEvent.wasClean);
                }
            });
        });
    }
}
```

### Message Flow Tracking

```python
# backend/debug/message_tracker.py
from collections import defaultdict
from datetime import datetime
import json

class MessageTracker:
    def __init__(self):
        self.messages = defaultdict(list)
        self.sequence_gaps = defaultdict(list)
    
    def track_inbound(self, websocket_id: str, message: dict):
        """Track incoming message."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'direction': 'inbound',
            'event': message.get('event'),
            'data': message.get('data'),
            'size': len(json.dumps(message))
        }
        
        self.messages[websocket_id].append(entry)
        
        # Check for sequence gaps
        if 'sequence' in message:
            self.check_sequence(websocket_id, message['sequence'])
    
    def track_outbound(self, websocket_id: str, message: dict):
        """Track outgoing message."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'direction': 'outbound',
            'event': message.get('event'),
            'sequence': message.get('sequence_number'),
            'size': len(json.dumps(message))
        }
        
        self.messages[websocket_id].append(entry)
    
    def get_flow_diagram(self, websocket_id: str) -> str:
        """Generate message flow diagram."""
        flow = []
        for msg in self.messages[websocket_id][-20:]:  # Last 20 messages
            direction = '→' if msg['direction'] == 'outbound' else '←'
            flow.append(f"{msg['timestamp']} {direction} {msg['event']}")
        
        return '\n'.join(flow)
```

## State Synchronization Issues

### Detecting Desync

```typescript
// frontend/src/debug/syncChecker.ts
export class SyncChecker {
    private lastKnownState: any = null;
    private stateHistory: Array<{
        timestamp: number;
        phase: string;
        sequence: number;
        hash: string;
    }> = [];
    
    checkSync(serverState: any, clientState: any): SyncIssue[] {
        const issues: SyncIssue[] = [];
        
        // Check sequence numbers
        if (serverState.sequence_number !== clientState.lastSequence) {
            issues.push({
                type: 'sequence_mismatch',
                severity: 'high',
                serverValue: serverState.sequence_number,
                clientValue: clientState.lastSequence,
                message: `Sequence mismatch: server=${serverState.sequence_number}, client=${clientState.lastSequence}`
            });
        }
        
        // Check phase
        if (serverState.phase !== clientState.phase) {
            issues.push({
                type: 'phase_mismatch',
                severity: 'critical',
                serverValue: serverState.phase,
                clientValue: clientState.phase,
                message: `Phase mismatch: server=${serverState.phase}, client=${clientState.phase}`
            });
        }
        
        // Check player data
        const serverPlayers = new Set(serverState.players.map(p => p.name));
        const clientPlayers = new Set(clientState.players.map(p => p.name));
        
        if (!this.setsEqual(serverPlayers, clientPlayers)) {
            issues.push({
                type: 'player_mismatch',
                severity: 'high',
                serverValue: Array.from(serverPlayers),
                clientValue: Array.from(clientPlayers),
                message: 'Player list mismatch'
            });
        }
        
        return issues;
    }
    
    private setsEqual(a: Set<any>, b: Set<any>): boolean {
        return a.size === b.size && [...a].every(x => b.has(x));
    }
}
```

### Fixing Desync

```typescript
// Force resync mechanism
async function forceResync(roomId: string) {
    console.warn('Forcing resync for room:', roomId);
    
    // 1. Close current connection
    NetworkService.disconnect();
    
    // 2. Clear local state
    gameStore.reset();
    
    // 3. Reconnect with full state request
    await NetworkService.connect(roomId, {
        requestFullState: true
    });
    
    // 4. Wait for state sync
    return new Promise((resolve) => {
        NetworkService.once('state_sync_complete', resolve);
    });
}
```

## Performance Problems

### Backend Performance

```python
# Profile slow operations
import cProfile
import pstats
from io import StringIO

def profile_game_operation():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run operation
    game.process_turn()
    
    profiler.disable()
    
    # Get results
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    
    logger.info(f"Profile results:\n{s.getvalue()}")

# Async profiling
import asyncio
import time

async def measure_async_operation(operation, name: str):
    start = time.perf_counter()
    try:
        result = await operation
        duration = time.perf_counter() - start
        logger.info(f"{name} took {duration:.3f}s")
        
        if duration > 1.0:  # Slow operation
            logger.warning(f"Slow operation detected: {name} took {duration:.3f}s")
            
        return result
    except Exception as e:
        duration = time.perf_counter() - start
        logger.error(f"{name} failed after {duration:.3f}s: {e}")
        raise
```

### Frontend Performance

```tsx
// Identify render bottlenecks
const useWhyDidYouUpdate = (name: string, props: Record<string, any>) => {
    const previousProps = useRef<Record<string, any>>();
    
    useEffect(() => {
        if (previousProps.current) {
            const allKeys = Object.keys({ ...previousProps.current, ...props });
            const changedProps: Record<string, any> = {};
            
            allKeys.forEach(key => {
                if (previousProps.current![key] !== props[key]) {
                    changedProps[key] = {
                        from: previousProps.current![key],
                        to: props[key]
                    };
                }
            });
            
            if (Object.keys(changedProps).length) {
                console.log('[why-did-you-update]', name, changedProps);
            }
        }
        
        previousProps.current = props;
    });
};

// Use in component
const MyComponent: React.FC<Props> = (props) => {
    useWhyDidYouUpdate('MyComponent', props);
    // Component logic
};
```

## Production Debugging

### Remote Logging

```python
# backend/debug/remote_logger.py
import httpx
import asyncio
from datetime import datetime

class RemoteLogger:
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint = endpoint
        self.api_key = api_key
        self.queue = asyncio.Queue()
        self.batch_size = 100
        self.flush_interval = 5.0
    
    async def log(self, level: str, message: str, data: dict = None):
        """Queue log for remote sending."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'data': data,
            'server_id': os.getenv('SERVER_ID', 'unknown'),
            'version': os.getenv('APP_VERSION', 'unknown')
        }
        
        await self.queue.put(entry)
    
    async def flush_logs(self):
        """Send queued logs to remote service."""
        batch = []
        
        while not self.queue.empty() and len(batch) < self.batch_size:
            try:
                batch.append(self.queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        
        if batch:
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(
                        self.endpoint,
                        json={'logs': batch},
                        headers={'X-API-Key': self.api_key}
                    )
                except Exception as e:
                    # Fall back to local logging
                    logger.error(f"Failed to send remote logs: {e}")
```

### Error Reporting

```typescript
// frontend/src/debug/errorReporter.ts
class ErrorReporter {
    private static instance: ErrorReporter;
    private errorQueue: ErrorReport[] = [];
    
    static getInstance(): ErrorReporter {
        if (!this.instance) {
            this.instance = new ErrorReporter();
        }
        return this.instance;
    }
    
    captureError(error: Error, context?: any) {
        const report: ErrorReport = {
            timestamp: new Date().toISOString(),
            message: error.message,
            stack: error.stack,
            context: {
                ...context,
                userAgent: navigator.userAgent,
                url: window.location.href,
                gameState: this.getGameState()
            }
        };
        
        this.errorQueue.push(report);
        
        // Send immediately if critical
        if (this.isCriticalError(error)) {
            this.flush();
        }
    }
    
    private isCriticalError(error: Error): boolean {
        return error.message.includes('WebSocket') ||
               error.message.includes('Connection') ||
               error.name === 'SecurityError';
    }
    
    async flush() {
        if (this.errorQueue.length === 0) return;
        
        const errors = [...this.errorQueue];
        this.errorQueue = [];
        
        try {
            await fetch('/api/errors', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ errors })
            });
        } catch (e) {
            console.error('Failed to report errors:', e);
            // Re-queue errors
            this.errorQueue.unshift(...errors);
        }
    }
}

// Global error handler
window.addEventListener('error', (event) => {
    ErrorReporter.getInstance().captureError(
        new Error(event.message),
        {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
        }
    );
});

window.addEventListener('unhandledrejection', (event) => {
    ErrorReporter.getInstance().captureError(
        new Error(event.reason),
        { type: 'unhandledRejection' }
    );
});
```

## Debug Utilities

### Game State Inspector

```python
# backend/debug/inspector.py
class GameInspector:
    @staticmethod
    def inspect_game(game: Game) -> dict:
        """Deep inspection of game state."""
        return {
            'game_id': game.game_id,
            'round': game.round_number,
            'turn': game.turn_number,
            'phase': game.current_phase,
            'players': [
                {
                    'name': p.name,
                    'score': p.score,
                    'hand_count': len(p.hand),
                    'hand_value': sum(piece.point for piece in p.hand),
                    'declared': p.declared,
                    'captured': p.captured_piles
                }
                for p in game.players
            ],
            'pile': {
                'count': len(game.current_pile),
                'pieces': [p.to_dict() for p in game.current_pile[-5:]]  # Last 5
            },
            'history': {
                'total_turns': len(game.turn_history),
                'last_5_turns': game.turn_history[-5:]
            }
        }
    
    @staticmethod
    def validate_game_state(game: Game) -> List[str]:
        """Validate game state consistency."""
        issues = []
        
        # Check player count
        if len(game.players) != 4:
            issues.append(f"Invalid player count: {len(game.players)}")
        
        # Check hand sizes
        total_pieces = sum(len(p.hand) for p in game.players)
        if game.current_phase == "TURN" and total_pieces + len(game.current_pile) != 32:
            issues.append(f"Piece count mismatch: {total_pieces + len(game.current_pile)}")
        
        # Check scores
        for player in game.players:
            if player.score < 0:
                issues.append(f"Negative score for {player.name}: {player.score}")
        
        return issues
```

### Network Monitor

```typescript
// frontend/src/debug/networkMonitor.ts
export class NetworkMonitor {
    private stats = {
        messagesSent: 0,
        messagesReceived: 0,
        bytesReceived: 0,
        reconnections: 0,
        errors: 0,
        latencies: [] as number[]
    };
    
    private pingInterval: NodeJS.Timeout | null = null;
    
    start() {
        // Monitor all messages
        NetworkService.on('*', this.handleMessage.bind(this));
        
        // Start ping monitoring
        this.pingInterval = setInterval(() => {
            this.sendPing();
        }, 5000);
    }
    
    private handleMessage(event: string, data: any) {
        if (event.startsWith('send:')) {
            this.stats.messagesSent++;
        } else {
            this.stats.messagesReceived++;
            this.stats.bytesReceived += JSON.stringify(data).length;
        }
    }
    
    private async sendPing() {
        const start = performance.now();
        
        try {
            await NetworkService.sendAndWait('ping', {
                client_time: Date.now()
            }, 'pong', 5000);
            
            const latency = performance.now() - start;
            this.stats.latencies.push(latency);
            
            // Keep last 100 latencies
            if (this.stats.latencies.length > 100) {
                this.stats.latencies.shift();
            }
        } catch (error) {
            this.stats.errors++;
        }
    }
    
    getStats() {
        const avgLatency = this.stats.latencies.length > 0
            ? this.stats.latencies.reduce((a, b) => a + b) / this.stats.latencies.length
            : 0;
        
        return {
            ...this.stats,
            averageLatency: avgLatency.toFixed(2),
            p95Latency: this.percentile(this.stats.latencies, 0.95).toFixed(2),
            messagesPerSecond: (this.stats.messagesSent / (Date.now() / 1000)).toFixed(2)
        };
    }
    
    private percentile(arr: number[], p: number): number {
        if (arr.length === 0) return 0;
        const sorted = [...arr].sort((a, b) => a - b);
        const index = Math.ceil(arr.length * p) - 1;
        return sorted[index];
    }
}
```

## Troubleshooting Checklist

### Quick Diagnosis Steps

1. **Check Browser Console**
   - JavaScript errors?
   - Network failures?
   - WebSocket status?

2. **Check Backend Logs**
   - Python exceptions?
   - WebSocket errors?
   - State machine warnings?

3. **Check Network Tab**
   - Failed requests?
   - Slow responses?
   - WebSocket frames?

4. **Check Application State**
   ```javascript
   // In browser console
   debug.getGameState()
   debug.getNetworkStatus()
   debug.helpers.log('Current state', gameContext)
   ```

5. **Check Server Health**
   ```bash
   # Health check
   curl http://localhost:8000/api/health
   
   # Detailed health
   curl http://localhost:8000/api/health/detailed
   
   # Room stats (debug mode)
   curl http://localhost:8000/api/debug/room-stats
   ```

### Common Solutions

| Problem | Solution |
|---------|----------|
| WebSocket won't connect | Check CORS, firewall, nginx config |
| State out of sync | Force reconnect, check sequence numbers |
| UI not updating | Check React keys, memo usage |
| Memory leak | Check event listeners, circular refs |
| Slow performance | Profile, check renders, optimize queries |
| Production errors | Check logs, error reports, monitoring |

### Emergency Procedures

1. **Player Stuck**: Force disconnect and reconnect
2. **Game Frozen**: Reset state machine to PREPARATION
3. **Server Overload**: Enable rate limiting, scale up
4. **Data Corruption**: Restore from backup, replay events

## Summary

Effective debugging requires:

1. **Good Logging**: Comprehensive, structured logs
2. **Proper Tools**: Use debuggers and profilers
3. **Monitoring**: Track metrics and errors
4. **Documentation**: Record issues and solutions
5. **Testing**: Reproduce issues systematically

Remember:
- Always reproduce before fixing
- Check logs first
- Use debugging tools
- Document your findings
- Test the fix thoroughly