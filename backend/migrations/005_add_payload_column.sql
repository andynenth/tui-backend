-- backend/migrations/005_add_payload_column.sql
-- Add payload column to game_events_v2 for bot takeover debugging

-- Add payload column to store event data
ALTER TABLE game_events_v2 ADD COLUMN payload JSON;

-- Add player_id column for player-specific events
ALTER TABLE game_events_v2 ADD COLUMN player_id TEXT;

-- Create index for player-specific queries
CREATE INDEX IF NOT EXISTS idx_events_v2_player ON game_events_v2(player_id);

-- Create index for event type + player combo (for bot takeover analysis)
CREATE INDEX IF NOT EXISTS idx_events_v2_type_player ON game_events_v2(event_type, player_id);

-- Update migration metadata
INSERT INTO schema_migrations (version, applied_at, description)
VALUES (5, datetime('now'), 'Add payload and player_id columns for bot takeover debugging');