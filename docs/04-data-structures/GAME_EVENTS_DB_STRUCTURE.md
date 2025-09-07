# Game Events Database Structure

## Overview
The `game_events.db` is a SQLite database that stores all game events using an event sourcing pattern. This allows complete reconstruction of game state and history.

## Database Schema

```sql
CREATE TABLE game_events (
    sequence INTEGER PRIMARY KEY,     -- Auto-incrementing sequence number
    room_id TEXT NOT NULL,           -- Game room identifier (6 chars, e.g., "6F747A")
    event_type TEXT NOT NULL,        -- Type of event (see Event Types below)
    payload TEXT NOT NULL,           -- JSON-encoded event data
    player_id TEXT,                  -- Player who triggered the event (optional)
    timestamp REAL NOT NULL,         -- Unix timestamp when event occurred
    created_at TEXT NOT NULL         -- ISO format timestamp
);

-- Indexes for performance
CREATE INDEX idx_room_sequence ON game_events(room_id, sequence);
CREATE INDEX idx_room_timestamp ON game_events(room_id, timestamp);
CREATE INDEX idx_created_at ON game_events(created_at);
```

## Event Types

### 1. `action_processed` (Most common: ~1,747 events)
Records every player action in the game.

**Payload Structure:**
```json
{
  "action_type": "declare|play_pieces|play",  // Type of action
  "player_name": "Player 1",                   // Who performed the action
  "sequence_id": 0,                            // Action sequence number
  "payload": {
    // For declare:
    "value": 2,                                // Number of piles declared

    // For play_pieces:
    "pieces": [
      {"kind": "GENERAL_RED", "point": 14},
      {"kind": "SOLDIER_BLACK", "point": 1}
    ]
  }
}
```

### 2. `phase_change` (~2,279 events)
Records game phase transitions (preparation → declaration → turn → scoring).

**Payload Structure:**
```json
{
  "phase": "preparation|declaration|turn|turn_results|scoring",
  "phase_data": {
    // Phase-specific data
  },
  "players": {
    "Player 1": {
      "name": "Player 1",
      "is_bot": false,
      "avatar_color": "red",
      "hand": [],                    // Current hand (array of pieces)
      "hand_size": 8,
      "zero_declares_in_a_row": 0,
      "declared": 2,                 // Piles declared this round
      "captured_piles": 3,           // Piles captured this round
      "score": 12                    // Total game score
    }
    // ... other players
  },
  "reason": "Starting new round",
  "sequence": 1,
  "timestamp": 1754584242.801
}
```

### 3. `phase_data_update` (~2,006 events)
Updates phase-specific data without changing the phase.

**Common Updates:**
- Turn completion status
- Current player changes
- Winner information
- Required piece counts

### 4. `hands_dealt` (~10 events per game)
Records initial hands dealt to each player at round start.

**Payload Structure:**
```json
{
  "round_number": 1,
  "hands": {
    "Player 1": [
      {"kind": "GENERAL_RED", "point": 14},
      {"kind": "CHARIOT_BLACK", "point": 7},
      // ... 8 pieces total
    ],
    // ... other players' hands
  },
  "starter": "Player 3",
  "starter_reason": "has_general_red",  // or "previous_round_winner"
  "redeal_multiplier": 1,               // Increased if weak hands cause redeal
  "phase": "preparation",
  "sequence": 2,
  "timestamp": 1754889660.458984
}
```

### 5. `turn_complete` (~13 events)
Marks the completion of a turn (all players have played).

## Piece Types
- **Generals**: `GENERAL_RED` (14 points), `GENERAL_BLACK` (13 points)
- **Advisors**: `ADVISOR_RED` (12 points), `ADVISOR_BLACK` (11 points)
- **Elephants**: `ELEPHANT_RED` (10 points), `ELEPHANT_BLACK` (9 points)
- **Chariots**: `CHARIOT_RED` (8 points), `CHARIOT_BLACK` (7 points)
- **Horses**: `HORSE_RED` (6 points), `HORSE_BLACK` (5 points)
- **Cannons**: `CANNON_RED` (4 points), `CANNON_BLACK` (3 points)
- **Soldiers**: `SOLDIER_RED` (2 points), `SOLDIER_BLACK` (1 point)

## Usage Examples

### Get all events for a room:
```sql
SELECT * FROM game_events
WHERE room_id = 'C5E645'
ORDER BY sequence;
```

### Get initial hands for a round:
```sql
SELECT payload FROM game_events
WHERE room_id = 'C5E645'
  AND event_type = 'hands_dealt'
  AND payload LIKE '%"round_number": 1%';
```

### Track game progression:
```sql
SELECT event_type, payload FROM game_events
WHERE room_id = 'C5E645'
  AND event_type = 'phase_change'
ORDER BY sequence;
```

## Key Features
1. **Complete History**: Every action is recorded, allowing full game replay
2. **Event Sourcing**: Game state can be reconstructed from events
3. **Performance**: Indexed for quick retrieval by room and timestamp
4. **Flexibility**: JSON payloads allow storing complex game data
5. **Audit Trail**: Player actions are tracked with timestamps

## File Location
The database is stored at the project root: `/liap-tui/game_events.db`

## Note on play_with_context Events
The `play_with_context` event type is used for real-time WebSocket broadcasting during gameplay but is NOT stored in the database. The Play History API calculates hand states by tracking changes from `hands_dealt` and `action_processed` events, avoiding redundant data storage.
