# Game Events Database Structure (V2)

## Overview
The `game_events.db` is a SQLite database that stores all game events using an optimized event sourcing pattern with separate tables for different types of data. This is the V2 schema which replaced the original single-table design.

## Database Schema (V2)

### Core Tables

```sql
-- 1. Game events table (minimal event tracking)
CREATE TABLE game_events_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    round_number INTEGER,
    timestamp REAL NOT NULL,
    created_at TEXT NOT NULL
);

-- 2. Game summaries (one row per game)
CREATE TABLE game_summaries (
    room_id TEXT PRIMARY KEY,
    players JSON NOT NULL,              -- JSON array of player objects
    total_rounds INTEGER DEFAULT 0,
    final_scores JSON,                  -- JSON object mapping names to scores
    winner TEXT,
    started_at REAL NOT NULL,
    completed_at REAL,
    game_config JSON,
    duration_seconds INTEGER,
    total_events INTEGER DEFAULT 0
);

-- 3. Round snapshots (one row per round)
CREATE TABLE round_snapshots (
    room_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    starter_player TEXT NOT NULL,
    starter_reason TEXT,                -- 'has_general_red' or 'previous_round_winner'
    initial_hands JSON NOT NULL,        -- Complete hands dealt this round
    declarations JSON NOT NULL,         -- Player declarations
    turn_sequence JSON NOT NULL,        -- Compressed turn data
    round_scores JSON NOT NULL,         -- Scores for this round
    cumulative_scores JSON NOT NULL,    -- Running total scores
    created_at TEXT NOT NULL,
    duration_seconds INTEGER,
    total_turns INTEGER,
    PRIMARY KEY (room_id, round_number)
);

-- 4. Turn details (optional, for detailed analysis)
CREATE TABLE turn_details (
    room_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    starter TEXT NOT NULL,
    plays JSON NOT NULL,                -- All plays in the turn
    winner TEXT,
    piles_won INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (room_id, round_number, turn_number)
);

-- Performance indexes
CREATE INDEX idx_events_v2_room_time ON game_events_v2(room_id, timestamp);
CREATE INDEX idx_events_v2_type ON game_events_v2(event_type);
CREATE INDEX idx_summaries_completed ON game_summaries(completed_at DESC);
CREATE INDEX idx_summaries_winner ON game_summaries(winner);
CREATE INDEX idx_snapshots_room ON round_snapshots(room_id);
CREATE INDEX idx_turns_room_round ON turn_details(room_id, round_number);
```

## Data Structure Examples

### Game Summary Record
```json
{
  "room_id": "6F747A",
  "players": [
    {"player_name": "Alice", "is_bot": false, "avatar_color": "red"},
    {"player_name": "Bob", "is_bot": false, "avatar_color": "blue"},
    {"player_name": "Charlie", "is_bot": true, "avatar_color": "green"},
    {"player_name": "Dana", "is_bot": true, "avatar_color": "yellow"}
  ],
  "total_rounds": 5,
  "final_scores": {"Alice": 42, "Bob": 38, "Charlie": 35, "Dana": 28},
  "winner": "Alice",
  "started_at": 1754584240.5,
  "completed_at": 1754585890.3,
  "duration_seconds": 1650,
  "total_events": 245
}
```

### Round Snapshot Record
```json
{
  "room_id": "6F747A",
  "round_number": 3,
  "starter_player": "Bob",
  "starter_reason": "previous_round_winner",
  "initial_hands": {
    "Alice": [
      {"kind": "GENERAL_RED", "point": 14},
      {"kind": "ADVISOR_BLACK", "point": 11},
      {"kind": "ELEPHANT_RED", "point": 10},
      {"kind": "CHARIOT_BLACK", "point": 7},
      {"kind": "HORSE_RED", "point": 6},
      {"kind": "CANNON_BLACK", "point": 3},
      {"kind": "SOLDIER_RED", "point": 2},
      {"kind": "SOLDIER_BLACK", "point": 1}
    ],
    "Bob": [ /* 8 pieces */ ],
    "Charlie": [ /* 8 pieces */ ],
    "Dana": [ /* 8 pieces */ ]
  },
  "declarations": {
    "Alice": 2,
    "Bob": 3,
    "Charlie": 1,
    "Dana": 2
  },
  "turn_sequence": [
    {
      "turn_number": 1,
      "starter": "Bob",
      "plays": {
        "Bob": [{"kind": "GENERAL_BLACK", "point": 13}],
        "Charlie": [{"kind": "GENERAL_RED", "point": 14}],
        "Dana": [],  // passed
        "Alice": [{"kind": "ADVISOR_RED", "point": 12}]
      },
      "winner": "Charlie",
      "piles_won": 1
    },
    /* more turns */
  ],
  "round_scores": {"Alice": 5, "Bob": -3, "Charlie": 0, "Dana": -2},
  "cumulative_scores": {"Alice": 22, "Bob": 18, "Charlie": 15, "Dana": 12},
  "duration_seconds": 240,
  "total_turns": 12
}
```

### Turn Detail Record
```json
{
  "room_id": "6F747A",
  "round_number": 3,
  "turn_number": 5,
  "starter": "Alice",
  "plays": {
    "Alice": [
      {"kind": "CHARIOT_RED", "point": 8},
      {"kind": "CHARIOT_BLACK", "point": 7}
    ],
    "Bob": [
      {"kind": "ELEPHANT_RED", "point": 10},
      {"kind": "ELEPHANT_BLACK", "point": 9}
    ],
    "Charlie": [],  // passed
    "Dana": [
      {"kind": "ADVISOR_RED", "point": 12},
      {"kind": "ADVISOR_BLACK", "point": 11}
    ]
  },
  "winner": "Dana",
  "piles_won": 2
}
```

## Key Differences from V1

1. **Separated Tables**: Instead of one `game_events` table, V2 uses specialized tables for different data types
2. **No Payload Column**: V2 stores structured JSON in specific columns rather than a generic payload
3. **Optimized for Reads**: Round snapshots allow quick game reconstruction without replaying all events
4. **Better Performance**: Smaller event table with indexes optimized for common queries
5. **Turn Compression**: Turn data is stored in the round snapshot, reducing redundancy

## Game Phases (Including ROUND_START)

The game now has 8 phases:
1. `WAITING` - Room created, waiting for players
2. `PREPARATION` - Dealing cards, handling weak hands
3. `ROUND_START` - Setting round starter (new phase)
4. `DECLARATION` - Players declare target piles
5. `TURN` - Playing pieces
6. `TURN_RESULTS` - Processing turn outcomes
7. `SCORING` - Calculating round scores
8. `GAME_OVER` - Game completed

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
- **Default**: `data/game_events.db` (relative to project root)
- **Docker**: `/app/data/game_events.db`
- **Configurable**: Via `DATABASE_PATH` environment variable

## Migration System

The database uses a migration system to upgrade schemas:

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);
```

Current version: **2** (Optimized schema with separate tables)

## SQLite Optimizations

```sql
PRAGMA journal_mode=WAL;      -- Write-ahead logging
PRAGMA synchronous=NORMAL;    -- Balanced safety/speed
PRAGMA cache_size=-64000;     -- 64MB cache
PRAGMA temp_store=MEMORY;     -- Temp tables in memory
PRAGMA mmap_size=30000000000; -- Memory-mapped I/O
```
