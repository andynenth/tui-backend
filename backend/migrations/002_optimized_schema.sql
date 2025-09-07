-- backend/migrations/002_optimized_schema.sql
-- Database Schema Optimization for Phase 3

-- Migration metadata table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);

-- Core events table (minimal, optimized for writes)
CREATE TABLE IF NOT EXISTS game_events_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    round_number INTEGER,
    timestamp REAL NOT NULL,
    created_at TEXT NOT NULL
);

-- Game summaries (one row per game, optimized for game list queries)
CREATE TABLE IF NOT EXISTS game_summaries (
    room_id TEXT PRIMARY KEY,
    players JSON NOT NULL,
    total_rounds INTEGER DEFAULT 0,
    final_scores JSON,
    winner TEXT,
    started_at REAL NOT NULL,
    completed_at REAL,
    game_config JSON,
    duration_seconds INTEGER,
    total_events INTEGER DEFAULT 0
);

-- Round snapshots (one row per round, optimized for play history)
CREATE TABLE IF NOT EXISTS round_snapshots (
    room_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    starter_player TEXT NOT NULL,
    starter_reason TEXT,
    initial_hands JSON NOT NULL,
    declarations JSON NOT NULL,
    turn_sequence JSON NOT NULL,  -- Compressed turn data
    round_scores JSON NOT NULL,
    cumulative_scores JSON NOT NULL,
    created_at TEXT NOT NULL,
    duration_seconds INTEGER,
    total_turns INTEGER,
    PRIMARY KEY (room_id, round_number)
);

-- Turn details (optional, for detailed turn analysis)
CREATE TABLE IF NOT EXISTS turn_details (
    room_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    starter TEXT NOT NULL,
    plays JSON NOT NULL,  -- All plays in the turn
    winner TEXT,
    piles_won INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (room_id, round_number, turn_number),
    FOREIGN KEY (room_id, round_number) REFERENCES round_snapshots(room_id, round_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_v2_room_time ON game_events_v2(room_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_v2_type ON game_events_v2(event_type);
CREATE INDEX IF NOT EXISTS idx_summaries_completed ON game_summaries(completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_summaries_winner ON game_summaries(winner);
CREATE INDEX IF NOT EXISTS idx_snapshots_room ON round_snapshots(room_id);
CREATE INDEX IF NOT EXISTS idx_turns_room_round ON turn_details(room_id, round_number);

-- Views for common queries
CREATE VIEW IF NOT EXISTS active_games AS
SELECT
    room_id,
    players,
    total_rounds,
    started_at,
    duration_seconds
FROM game_summaries
WHERE completed_at IS NULL
ORDER BY started_at DESC;

CREATE VIEW IF NOT EXISTS completed_games AS
SELECT
    room_id,
    players,
    total_rounds,
    final_scores,
    winner,
    started_at,
    completed_at,
    duration_seconds
FROM game_summaries
WHERE completed_at IS NOT NULL
ORDER BY completed_at DESC;

-- Helper view for player statistics
CREATE VIEW IF NOT EXISTS player_stats AS
SELECT
    json_extract(value, '$.player_name') as player_name,
    COUNT(DISTINCT g.room_id) as games_played,
    SUM(CASE WHEN g.winner = json_extract(value, '$.player_name') THEN 1 ELSE 0 END) as games_won,
    AVG(json_extract(g.final_scores, '$.' || json_extract(value, '$.player_name'))) as avg_score
FROM game_summaries g, json_each(g.players)
WHERE g.completed_at IS NOT NULL
GROUP BY player_name;

-- Migration completion
INSERT INTO schema_migrations (version, applied_at, description)
VALUES (2, datetime('now'), 'Optimized schema with separate tables for events, summaries, and snapshots');
