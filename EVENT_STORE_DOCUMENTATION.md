# Event Store Documentation - Liap Tui Game System

## Table of Contents
1. [Introduction](#introduction)
2. [What is Event Sourcing?](#what-is-event-sourcing)
3. [Architecture Overview](#architecture-overview)
4. [Event Types](#event-types)
5. [How Events Flow](#how-events-flow)
6. [State Reconstruction](#state-reconstruction)
7. [Implementation Details](#implementation-details)
8. [Debug Interface](#debug-interface)
9. [Code Examples](#code-examples)
10. [Benefits & Trade-offs](#benefits--trade-offs)
11. [Future Considerations](#future-considerations)

## Introduction

The Liap Tui game uses an **Event Store** to capture every game action as an immutable event. This provides a complete audit trail, enables debugging, and allows state reconstruction at any point in the game's history.

## What is Event Sourcing?

Event Sourcing is a pattern where:
- **State changes** are stored as a sequence of **events**
- Events are **immutable** - once stored, they never change
- Current state is derived by **replaying events** from the beginning
- Every action has a **complete history**

### Traditional Approach vs Event Sourcing

**Traditional (CRUD)**:
```
Players Table: [id: 1, name: "Alice", score: 50]
UPDATE players SET score = 55 WHERE id = 1
```
- Only current state is stored
- History is lost

**Event Sourcing**:
```
Event 1: {type: "player_joined", player: "Alice"}
Event 2: {type: "round_scored", player: "Alice", points: 50}
Event 3: {type: "round_scored", player: "Alice", points: 5}
```
- Complete history preserved
- Current score = sum of all scoring events

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Game Actions   │────▶│  State Machine   │────▶│ Event Store │
│ (player moves)  │     │ (processes)      │     │  (SQLite)   │
└─────────────────┘     └──────────────────┘     └─────────────┘
                               │                         │
                               ▼                         │
                        ┌──────────────────┐            │
                        │ In-Memory State  │            │
                        │ (current game)   │            │
                        └──────────────────┘            │
                               ▲                         │
                               └─────────────────────────┘
                                    State Replay
```

### Components

1. **EventStore Service** (`backend/api/services/event_store.py`)
   - Manages SQLite database
   - Stores and retrieves events
   - Handles state reconstruction

2. **ActionQueue** (`backend/engine/state_machine/action_queue.py`)
   - Automatically captures game events
   - Integrates with EventStore

3. **State Machine** (`backend/engine/state_machine/`)
   - Generates events for all state changes
   - Uses enterprise architecture patterns

4. **Debug API** (`backend/api/routes/debug.py`)
   - REST endpoints for event inspection
   - State replay capabilities

## Event Types

### Core Event Types

| Event Type | Purpose | Example Payload |
|------------|---------|-----------------|
| `game_started` | New game begins | `{"initial_state": {}}` |
| `phase_change` | Game phase transition | `{"old_phase": "preparation", "new_phase": "declaration"}` |
| `phase_data_update` | Phase-specific data changes | `{"phase": "turn", "updates": {"current_player": "Alice"}}` |
| `action_processed` | Player action executed | `{"action_type": "DECLARE", "player_name": "Bob", "payload": {"value": 3}}` |
| `player_joined` | Player enters room | `{"player_name": "Charlie", "player_data": {"is_bot": false}}` |
| `player_declared` | Declaration made | `{"player_name": "Alice", "value": 2}` |
| `pieces_played` | Pieces played in turn | `{"player_name": "Bob", "pieces": ["R5", "R6"]}` |
| `turn_complete` | Turn ends | `{"winner": "Alice", "turn_number": 1}` |
| `round_scoring` | Round scores calculated | `{"round_number": 1, "scores": {"Alice": 10, "Bob": -5}}` |
| `game_complete` | Game ends | `{"winner": "Alice", "final_scores": {...}}` |

## How Events Flow

### 1. Player Action Triggers Event

```python
# Player makes a declaration
action = GameAction(
    player_name="Alice",
    action_type=ActionType.DECLARE,
    payload={"value": 3}
)
```

### 2. State Machine Processes Action

```python
# In DeclarationState
async def handle_action(self, action: GameAction):
    # Process the declaration
    self.game.players[0].declared = 3
    
    # Update phase data (automatically stores event)
    await self.update_phase_data({
        "declarations": {"Alice": 3}
    }, "Alice declared 3 piles")
```

### 3. Event Automatically Stored

```python
# Inside update_phase_data (automatic)
await self.state_machine.action_queue.store_state_event(
    event_type='phase_data_update',
    payload={
        'phase': 'declaration',
        'updates': {'declarations': {'Alice': 3}},
        'reason': 'Alice declared 3 piles',
        'sequence': 42,
        'timestamp': 1753237375.546
    }
)
```

### 4. Event Persisted to SQLite

```sql
INSERT INTO game_events (
    sequence, room_id, event_type, payload, 
    player_id, timestamp, created_at
) VALUES (
    42, 'ABC123', 'phase_data_update', 
    '{"phase": "declaration", ...}',
    NULL, 1753237375.546, '2025-07-22T19:22:55'
);
```

## State Reconstruction

### How Replay Works

```python
async def replay_room_state(self, room_id: str) -> Dict[str, Any]:
    """Reconstruct game state by replaying all events"""
    
    # Start with empty state
    state = {
        "room_id": room_id,
        "phase": None,
        "players": {},
        "game_state": {},
        "phase_data": {},
        "actions": []
    }
    
    # Get all events for room
    events = await self.get_room_events(room_id)
    
    # Apply each event in sequence
    for event in events:
        state = self._apply_event_to_state(state, event)
    
    state["events_processed"] = len(events)
    return state
```

### Event Application Logic

```python
def _apply_event_to_state(self, state: Dict, event: GameEvent) -> Dict:
    """Apply a single event to reconstruct state"""
    
    if event.event_type == "phase_change":
        state["phase"] = event.payload["new_phase"]
        
    elif event.event_type == "player_joined":
        state["players"][event.payload["player_name"]] = {
            "score": 0,
            "is_bot": event.payload["player_data"]["is_bot"]
        }
        
    elif event.event_type == "round_scoring":
        for player, score in event.payload["scores"].items():
            state["players"][player]["score"] += score
            
    # ... handle other event types
    
    return state
```

## Implementation Details

### Database Schema

```sql
CREATE TABLE game_events (
    sequence INTEGER PRIMARY KEY,    -- Global sequence number
    room_id TEXT NOT NULL,          -- Game room identifier  
    event_type TEXT NOT NULL,       -- Type of event
    payload TEXT NOT NULL,          -- JSON event data
    player_id TEXT,                 -- Optional player who triggered event
    timestamp REAL NOT NULL,        -- Unix timestamp
    created_at TEXT NOT NULL        -- ISO format timestamp
);

-- Indexes for performance
CREATE INDEX idx_room_sequence ON game_events(room_id, sequence);
CREATE INDEX idx_room_timestamp ON game_events(room_id, timestamp);
CREATE INDEX idx_created_at ON game_events(created_at);
```

### Automatic Integration

The enterprise architecture ensures events are automatically captured:

```python
# In BaseState
async def update_phase_data(self, updates: Dict[str, Any], reason: str):
    """Update phase data with automatic event storage"""
    
    # Update in-memory state
    self.phase_data.update(updates)
    
    # Automatically store event
    await self._store_state_transition_event(updates, reason)
    
    # Automatically broadcast to clients
    await self._broadcast_phase_change()
```

### Performance Optimizations

1. **Batch Reading**: Events loaded in chunks for replay
2. **Indexed Queries**: Room and timestamp indexes for fast lookup
3. **JSON Caching**: Parsed JSON cached in memory
4. **Async Operations**: Non-blocking database operations

## Debug Interface

### REST API Endpoints

| Endpoint | Method | Purpose |
|----------|---------|---------|
| `/api/debug/events/{room_id}` | GET | View all events for a room |
| `/api/debug/replay/{room_id}` | GET | Replay and show current state |
| `/api/debug/events/{room_id}/sequence/{seq}` | GET | Get events after sequence |
| `/api/debug/export/{room_id}` | GET | Export complete room history |
| `/api/debug/stats` | GET | Event store statistics |
| `/api/debug/validate/{room_id}` | GET | Validate event sequence |
| `/api/debug/cleanup` | POST | Clean up old events |

### Example Debug Usage

```bash
# View game events
curl http://localhost:5050/api/debug/events/ABC123

# Replay game state
curl http://localhost:5050/api/debug/replay/ABC123

# Check statistics
curl http://localhost:5050/api/debug/stats
```

## Code Examples

### Storing Custom Events

```python
# Store a custom game event
await event_store.store_event(
    room_id="ABC123",
    event_type="special_rule_activated",
    payload={
        "rule": "double_points",
        "activated_by": "Alice",
        "duration": 2
    },
    player_id="Alice"
)
```

### Querying Events

```python
# Get all events for a room
events = await event_store.get_room_events("ABC123")

# Get events by type
phase_changes = await event_store.get_events_by_type(
    "ABC123", 
    "phase_change"
)

# Get recent events
recent = await event_store.get_events_since("ABC123", sequence=100)
```

### Implementing Recovery

```python
async def recover_game_after_crash(room_id: str):
    """Recover game state after server crash"""
    
    # Replay all events
    state = await event_store.replay_room_state(room_id)
    
    # Recreate game objects
    game = Game()
    game.round_number = state["round_number"]
    
    # Restore players
    for name, data in state["players"].items():
        player = Player(name)
        player.score = data["score"]
        game.players.append(player)
    
    # Resume from current phase
    state_machine = GameStateMachine(game, broadcast_callback)
    state_machine.current_phase = GamePhase[state["phase"].upper()]
    
    return state_machine
```

## Benefits & Trade-offs

### Benefits ✅

1. **Complete Audit Trail**
   - Every action is recorded
   - Can investigate any game issue
   - Prove game fairness

2. **Time Travel Debugging**
   - Replay to any point
   - See exact sequence of events
   - Identify when bugs occurred

3. **Crash Recovery**
   - Restore complete game state
   - No lost games
   - Players can continue

4. **Analytics & Learning**
   - Analyze player patterns
   - Train AI on real games
   - Generate statistics

5. **Simplified Testing**
   - Record problematic games
   - Replay in tests
   - Ensure fixes work

### Trade-offs ⚠️

1. **Storage Growth**
   - Events accumulate over time
   - Need cleanup strategy
   - ~1KB per event

2. **Replay Performance**
   - Replaying long games takes time
   - May need snapshots for optimization

3. **Complexity**
   - More moving parts
   - Need to understand event flow
   - Debugging requires event thinking

4. **Schema Evolution**
   - Old events must remain playable
   - Need migration strategies

## Future Considerations

### 1. Snapshots for Performance
```python
# Store periodic snapshots
if event.sequence % 100 == 0:
    await store_snapshot(room_id, current_state)

# Replay from nearest snapshot
snapshot = await get_nearest_snapshot(room_id, target_sequence)
events = await get_events_since(room_id, snapshot.sequence)
```

### 2. Event Versioning
```python
{
    "version": 2,
    "event_type": "pieces_played_v2",
    "payload": {
        "player": "Alice",
        "pieces": ["R5", "R6"],
        "combo_bonus": true  # New in v2
    }
}
```

### 3. PostgreSQL Migration
```python
# Easy to switch databases
class PostgresEventStore(EventStore):
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
```

### 4. Event Streaming
```python
# Real-time event subscriptions
async def subscribe_to_events(room_id: str):
    async for event in event_store.stream_events(room_id):
        yield event
```

### 5. GDPR Compliance
```python
# Anonymize player data
async def anonymize_player_events(player_id: str):
    await event_store.update_events(
        {"player_id": player_id},
        {"player_id": f"ANON_{hash(player_id)}"}
    )
```

## Conclusion

The Event Store provides a robust foundation for the Liap Tui game system. It enables debugging, recovery, and analytics while maintaining excellent performance. The automatic integration through the enterprise architecture ensures no events are missed, making the system reliable and maintainable.

For developers, it transforms debugging from "what happened?" to "let me replay and see exactly what happened." This is invaluable for maintaining game quality and player trust.