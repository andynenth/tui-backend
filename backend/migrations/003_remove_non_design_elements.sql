-- backend/migrations/003_remove_non_design_elements.sql
-- Remove tables and views that are not part of the DATABASE_OPTIMIZATION_TECHNICAL_DESIGN.md

-- Drop views that were not in the design specification
DROP VIEW IF EXISTS player_stats;
DROP VIEW IF EXISTS active_games;
DROP VIEW IF EXISTS completed_games;

-- Drop the old v1 game_events table (not part of v2 design)
-- This table contains historical data from the old schema
DROP TABLE IF EXISTS game_events;

-- Drop associated indexes from v1 schema
DROP INDEX IF EXISTS idx_room_sequence;
DROP INDEX IF EXISTS idx_room_timestamp;
DROP INDEX IF EXISTS idx_created_at;

-- Migration completion
INSERT INTO schema_migrations (version, applied_at, description)
VALUES (3, datetime('now'), 'Remove non-design tables and views to ensure strict conformance');