-- Join Room Monitoring Queries
-- For use with SQLite game_events.db

-- 1. Monitor join success rate after fix deployment
SELECT
    DATE(datetime(timestamp, 'unixepoch')) as date,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN json_extract(payload, '$.success') = 1 THEN 1 ELSE 0 END) as successful,
    AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait_ms,
    MAX(json_extract(payload, '$.lock_wait_ms')) as max_lock_wait_ms
FROM game_events_v2
WHERE event_type = 'join_attempt'
  AND timestamp > unixepoch('2025-01-01')  -- Replace with deployment date
GROUP BY date
ORDER BY date;

-- 2. Detect any remaining race conditions
WITH concurrent_joins AS (
    SELECT
        e1.room_id,
        e1.timestamp as t1,
        e2.timestamp as t2,
        json_extract(e1.payload, '$.success') as p1_success,
        json_extract(e2.payload, '$.success') as p2_success,
        json_extract(e1.payload, '$.error_type') as p1_error,
        json_extract(e2.payload, '$.error_type') as p2_error
    FROM game_events_v2 e1
    JOIN game_events_v2 e2
      ON e1.room_id = e2.room_id
      AND e1.id < e2.id
      AND ABS(e1.timestamp - e2.timestamp) < 0.5
    WHERE e1.event_type = 'join_attempt'
      AND e2.event_type = 'join_attempt'
      AND e1.timestamp > unixepoch('2025-01-01')  -- Replace with deployment date
)
SELECT
    room_id,
    COUNT(*) as concurrent_pairs,
    -- This should be 0 after fix
    SUM(CASE WHEN p1_success = 1 AND p2_success = 1
             AND p1_error IS NULL AND p2_error IS NULL
        THEN 1 ELSE 0 END) as both_succeeded_same_slot
FROM concurrent_joins
GROUP BY room_id
HAVING concurrent_pairs > 0;

-- 3. Find rooms with high join contention
SELECT
    room_id,
    COUNT(*) as total_attempts,
    COUNT(DISTINCT player_id) as unique_players,
    SUM(CASE WHEN json_extract(payload, '$.success') = 1 THEN 1 ELSE 0 END) as successful,
    AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait,
    MAX(json_extract(payload, '$.lock_wait_ms')) as max_lock_wait,
    MIN(timestamp) as first_attempt,
    MAX(timestamp) as last_attempt,
    (MAX(timestamp) - MIN(timestamp)) as duration_seconds
FROM game_events_v2
WHERE event_type = 'join_attempt'
  AND timestamp > unixepoch('now') - 86400  -- Last 24 hours
GROUP BY room_id
HAVING total_attempts > 10
ORDER BY total_attempts DESC;

-- 4. Error type distribution
SELECT
    json_extract(payload, '$.error_type') as error_type,
    COUNT(*) as count,
    AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait_ms
FROM game_events_v2
WHERE event_type = 'join_attempt'
  AND json_extract(payload, '$.success') = 0
  AND timestamp > unixepoch('now') - 3600  -- Last hour
GROUP BY error_type
ORDER BY count DESC;

-- 5. Lock wait time analysis
SELECT
    CASE
        WHEN json_extract(payload, '$.lock_wait_ms') < 1 THEN '< 1ms'
        WHEN json_extract(payload, '$.lock_wait_ms') < 10 THEN '1-10ms'
        WHEN json_extract(payload, '$.lock_wait_ms') < 50 THEN '10-50ms'
        WHEN json_extract(payload, '$.lock_wait_ms') < 100 THEN '50-100ms'
        WHEN json_extract(payload, '$.lock_wait_ms') < 500 THEN '100-500ms'
        ELSE '500ms+'
    END as wait_time_bucket,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM game_events_v2 WHERE event_type = 'join_attempt' AND timestamp > unixepoch('now') - 3600), 2) as percentage
FROM game_events_v2
WHERE event_type = 'join_attempt'
  AND timestamp > unixepoch('now') - 3600  -- Last hour
GROUP BY wait_time_bucket
ORDER BY
    CASE wait_time_bucket
        WHEN '< 1ms' THEN 1
        WHEN '1-10ms' THEN 2
        WHEN '10-50ms' THEN 3
        WHEN '50-100ms' THEN 4
        WHEN '100-500ms' THEN 5
        ELSE 6
    END;

-- 6. Join timeline for a specific room (replace ROOM_ID)
SELECT
    datetime(timestamp, 'unixepoch') as time,
    player_id,
    json_extract(payload, '$.success') as success,
    json_extract(payload, '$.error_type') as error_type,
    json_extract(payload, '$.slot') as slot,
    json_extract(payload, '$.lock_wait_ms') as lock_wait_ms,
    json_extract(payload, '$.total_ms') as total_ms
FROM game_events_v2
WHERE event_type = 'join_attempt'
  AND room_id = 'ROOM_ID'  -- Replace with actual room_id
ORDER BY timestamp;

-- 7. Health check query - join system status
SELECT
    'Join System Health' as metric,
    CASE
        WHEN max_lock_wait > 3000 THEN 'DEGRADED - High lock contention'
        WHEN success_rate < 80 THEN 'UNHEALTHY - Low success rate'
        ELSE 'HEALTHY'
    END as status,
    total_attempts,
    successful,
    ROUND(success_rate, 2) || '%' as success_rate,
    ROUND(avg_lock_wait, 1) || 'ms' as avg_lock_wait,
    max_lock_wait || 'ms' as max_lock_wait
FROM (
    SELECT
        COUNT(*) as total_attempts,
        SUM(CASE WHEN json_extract(payload, '$.success') = 1 THEN 1 ELSE 0 END) as successful,
        (SUM(CASE WHEN json_extract(payload, '$.success') = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as success_rate,
        AVG(json_extract(payload, '$.lock_wait_ms')) as avg_lock_wait,
        MAX(json_extract(payload, '$.lock_wait_ms')) as max_lock_wait
    FROM game_events_v2
    WHERE event_type = 'join_attempt'
      AND timestamp > unixepoch('now') - 300  -- Last 5 minutes
);
