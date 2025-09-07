-- backend/migrations/004_schema_corrections.sql
-- Correct schema to exactly match DATABASE_OPTIMIZATION_TECHNICAL_DESIGN.md

-- Step 1: Fix game_events_v2 table
-- Add missing event_sequence column
ALTER TABLE game_events_v2 ADD COLUMN event_sequence INTEGER NOT NULL DEFAULT 0;

-- Step 2: Fix game_summaries table
-- Need to recreate table to rename columns and change structure
CREATE TABLE game_summaries_new (
    room_id TEXT PRIMARY KEY,
    player_names JSON NOT NULL,
    player_types JSON NOT NULL,
    total_rounds INTEGER DEFAULT 0,
    current_round INTEGER DEFAULT 0,
    game_status TEXT DEFAULT 'active',
    final_scores JSON,
    winner TEXT,
    started_at REAL NOT NULL,
    completed_at REAL,
    last_activity REAL NOT NULL,
    game_config JSON
);

-- Copy data from old table to new, mapping column names
INSERT INTO game_summaries_new (
    room_id,
    player_names,  -- was 'players'
    player_types,
    total_rounds,
    current_round,
    game_status,
    final_scores,
    winner,
    started_at,
    completed_at,
    last_activity,
    game_config
)
SELECT
    room_id,
    players as player_names,
    '{}' as player_types,  -- default empty object
    total_rounds,
    total_rounds as current_round,  -- use total_rounds as current
    CASE
        WHEN completed_at IS NOT NULL THEN 'completed'
        ELSE 'active'
    END as game_status,
    final_scores,
    winner,
    started_at,
    completed_at,
    COALESCE(completed_at, started_at) as last_activity,
    game_config
FROM game_summaries;

-- Drop old table and rename new
DROP TABLE game_summaries;
ALTER TABLE game_summaries_new RENAME TO game_summaries;

-- Step 3: Fix round_snapshots table
-- Need to recreate to add id column, fix types, add constraints
CREATE TABLE round_snapshots_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,

    -- Round setup
    starter_player TEXT NOT NULL,
    starter_reason TEXT,
    initial_hands JSON NOT NULL,

    -- Gameplay data
    declarations JSON NOT NULL,
    turn_count INTEGER NOT NULL CHECK (turn_count BETWEEN 1 AND 8),
    turn_sequence JSON NOT NULL,

    -- Round results
    round_scores JSON NOT NULL,
    pile_counts JSON NOT NULL,
    cumulative_scores JSON NOT NULL,

    -- Win check
    has_winner BOOLEAN DEFAULT FALSE,
    winning_player TEXT,

    -- Metadata
    duration_seconds REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(room_id, round_number)
);

-- Copy data from old table
INSERT INTO round_snapshots_new (
    room_id,
    round_number,
    starter_player,
    starter_reason,
    initial_hands,
    declarations,
    turn_count,
    turn_sequence,
    round_scores,
    pile_counts,
    cumulative_scores,
    has_winner,
    winning_player,
    duration_seconds,
    created_at
)
SELECT
    room_id,
    round_number,
    starter_player,
    starter_reason,
    initial_hands,
    declarations,
    COALESCE(total_turns, 1) as turn_count,  -- was 'total_turns'
    turn_sequence,
    round_scores,
    '{}' as pile_counts,  -- new column, default empty
    cumulative_scores,
    FALSE as has_winner,  -- new column
    NULL as winning_player,  -- new column
    CAST(duration_seconds as REAL),  -- convert INTEGER to REAL
    created_at
FROM round_snapshots;

-- Drop old table and rename new
DROP TABLE round_snapshots;
ALTER TABLE round_snapshots_new RENAME TO round_snapshots;

-- Step 4: Fix turn_details table
-- Need to recreate to add id, rename columns, add missing columns
CREATE TABLE turn_details_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,

    -- Turn data
    starter_player TEXT NOT NULL,  -- was 'starter'
    plays JSON NOT NULL,
    winner TEXT,
    piles_won INTEGER,

    -- Analysis data
    play_sequence_time JSON,  -- new column
    ai_analysis JSON,  -- new column

    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(room_id, round_number, turn_number)
);

-- Copy data from old table
INSERT INTO turn_details_new (
    room_id,
    round_number,
    turn_number,
    starter_player,
    plays,
    winner,
    piles_won,
    play_sequence_time,
    ai_analysis,
    created_at
)
SELECT
    room_id,
    round_number,
    turn_number,
    starter as starter_player,  -- rename column
    plays,
    winner,
    piles_won,
    NULL as play_sequence_time,  -- new column
    NULL as ai_analysis,  -- new column
    created_at
FROM turn_details;

-- Drop old table and rename new
DROP TABLE turn_details;
ALTER TABLE turn_details_new RENAME TO turn_details;

-- Step 5: Recreate all indexes as specified in design
CREATE INDEX idx_events_v2_room_time ON game_events_v2(room_id, timestamp DESC);
CREATE INDEX idx_events_v2_type ON game_events_v2(event_type);
CREATE INDEX idx_summaries_status ON game_summaries(game_status, last_activity DESC);
CREATE INDEX idx_summaries_completed ON game_summaries(completed_at DESC) WHERE completed_at IS NOT NULL;
CREATE INDEX idx_snapshots_room ON round_snapshots(room_id, round_number);
CREATE INDEX idx_turns_room_round ON turn_details(room_id, round_number, turn_number);

-- Migration completion
INSERT INTO schema_migrations (version, applied_at, description)
VALUES (4, datetime('now'), 'Correct schema to exactly match DATABASE_OPTIMIZATION_TECHNICAL_DESIGN.md');