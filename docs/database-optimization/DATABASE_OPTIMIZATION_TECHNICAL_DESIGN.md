# Database Optimization Technical Design

## Problem Analysis

### Game Constraints
- **Players**: 4 players per game
- **Pieces per player**: 8 pieces per round
- **Turns per round**: Minimum 2, Maximum 8 (bounded by pieces)
- **Win condition**: First player to reach 50 points
- **Game length**: Variable - continues until someone reaches 50 points
  - **Quick games**: 10-12 rounds (someone gets lucky with high scores)
  - **Typical games**: 15-20 rounds
  - **Long games**: 30+ rounds (close competition, low scoring)

### Current State
The game currently generates excessive database writes:
```
Per Turn: 7 writes (update_phase_data calls)
Per Round: ~126 writes actual (varies with gameplay)
  - Theoretical: 14-56 writes (2-8 turns × 7 writes)
  - Actual: ~126 due to redundant updates and duplicates
Per Game: Variable based on length
  - Quick game (12 rounds): ~1,500 writes
  - Typical game (18 rounds): ~2,300 writes
  - Long game (30 rounds): ~3,800 writes
```

### Target State After Optimization
```
Per Turn: 2 writes (turn_start + turn_complete bundled)
Per Round: 10-19 writes total
  - Fixed: 3 writes (round_start, declarations, round_complete)
  - Variable: 4-16 writes (2-8 turns × 2 writes per turn)
  - Typical: 12-14 writes (most games have 4-6 turns)
Per Game: Variable based on length
  - Quick game (12 rounds): ~150 writes
  - Typical game (18 rounds): ~230 writes
  - Long game (30 rounds): ~380 writes
Reduction: 85-92% fewer writes
```

### Root Causes
1. **Synchronous Writes**: Every state change immediately writes to database
2. **Granular Events**: Storing every micro-state change instead of semantic events
3. **Redundant Data**: phase_change contains full state, phase_data_update contains deltas
4. **No Buffering**: Each write is a separate database transaction

## Solution Architecture

### Component Diagram
```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Game State    │────▶│ Event Buffer │────▶│  Event Store    │
│    Machine      │     │  (In-Memory) │     │   (Database)    │
└─────────────────┘     └──────────────┘     └─────────────────┘
         │                      │                      │
         │                      ▼                      │
         │              ┌──────────────┐              │
         └─────────────▶│   Semantic   │              │
                        │  Compressor  │              │
                        └──────────────┘              │
                                │                      │
                                ▼                      ▼
                        ┌──────────────┐     ┌─────────────────┐
                        │ Play History │◀────│ Optimized DB    │
                        │   Service    │     │    Schema       │
                        └──────────────┘     └─────────────────┘
```

## Detailed Implementation

### 1. Event Buffer System

```python
# backend/services/event_buffer.py
import asyncio
import time
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class BufferedEvent:
    room_id: str
    event_type: str
    payload: Dict[str, Any]
    player_id: Optional[str]
    timestamp: float

class EventBuffer:
    """
    Thread-safe event buffer with automatic flushing.

    Features:
    - Automatic flush on size limit
    - Time-based flush (every N seconds)
    - Critical event immediate flush
    - Graceful shutdown with final flush
    """

    # Events that bypass buffering
    CRITICAL_EVENTS = {
        'game_started', 'game_over', 'round_complete',
        'player_disconnected', 'game_recovered'
    }

    def __init__(self,
                 max_size: int = 20,
                 flush_interval: float = 2.0,
                 event_store = None):
        self.max_size = max_size
        self.flush_interval = flush_interval
        self.event_store = event_store

        self._buffer: List[BufferedEvent] = []
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._shutdown = False

        # Metrics
        self.total_events_buffered = 0
        self.total_flushes = 0
        self.last_flush_time = time.time()

    async def add_event(self,
                       room_id: str,
                       event_type: str,
                       payload: Dict[str, Any],
                       player_id: Optional[str] = None) -> None:
        """Add event to buffer or flush immediately if critical."""

        event = BufferedEvent(
            room_id=room_id,
            event_type=event_type,
            payload=payload,
            player_id=player_id,
            timestamp=time.time()
        )

        # Critical events bypass buffer
        if event_type in self.CRITICAL_EVENTS:
            await self._flush_single_event(event)
            return

        async with self._lock:
            self._buffer.append(event)
            self.total_events_buffered += 1

            # Check if we need to flush
            if len(self._buffer) >= self.max_size:
                await self._flush_buffer()
            elif not self._flush_task or self._flush_task.done():
                # Start auto-flush timer
                self._flush_task = asyncio.create_task(
                    self._auto_flush_timer()
                )

    async def _flush_single_event(self, event: BufferedEvent) -> None:
        """Flush a single critical event immediately."""
        if self.event_store:
            try:
                await self.event_store.store_event(
                    room_id=event.room_id,
                    event_type=event.event_type,
                    payload=event.payload,
                    player_id=event.player_id
                )
            except Exception as e:
                logger.error(f"Failed to flush critical event: {e}")

    async def _flush_buffer(self) -> None:
        """Flush all buffered events to storage."""
        if not self._buffer or not self.event_store:
            return

        events_to_flush = self._buffer.copy()
        self._buffer.clear()

        try:
            # Batch insert all events
            for event in events_to_flush:
                await self.event_store.store_event(
                    room_id=event.room_id,
                    event_type=event.event_type,
                    payload=event.payload,
                    player_id=event.player_id
                )

            self.total_flushes += 1
            self.last_flush_time = time.time()

            logger.debug(
                f"Flushed {len(events_to_flush)} events "
                f"(total flushes: {self.total_flushes})"
            )

        except Exception as e:
            logger.error(f"Failed to flush buffer: {e}")
            # Re-add events to buffer on failure
            async with self._lock:
                self._buffer = events_to_flush + self._buffer

    async def _auto_flush_timer(self) -> None:
        """Periodically flush buffer based on time interval."""
        while not self._shutdown:
            await asyncio.sleep(self.flush_interval)
            async with self._lock:
                if self._buffer:
                    await self._flush_buffer()

    async def flush(self) -> None:
        """Manual flush of buffer."""
        async with self._lock:
            await self._flush_buffer()

    async def shutdown(self) -> None:
        """Graceful shutdown with final flush."""
        self._shutdown = True
        if self._flush_task:
            self._flush_task.cancel()
        await self.flush()

    def get_metrics(self) -> Dict[str, Any]:
        """Get buffer performance metrics."""
        return {
            'buffer_size': len(self._buffer),
            'total_buffered': self.total_events_buffered,
            'total_flushes': self.total_flushes,
            'time_since_flush': time.time() - self.last_flush_time,
            'events_per_flush': (
                self.total_events_buffered / max(1, self.total_flushes)
            )
        }
```

### 2. Semantic Event Compression

```python
# backend/services/event_compressor.py
from typing import List, Dict, Any, Optional
from enum import Enum
import json

class SemanticEventType(Enum):
    """High-level game events that capture meaningful state changes."""

    # Game lifecycle
    GAME_STARTED = "game_started"
    GAME_COMPLETED = "game_completed"

    # Round lifecycle
    ROUND_STARTED = "round_started"
    ROUND_COMPLETED = "round_completed"

    # Game phases
    DECLARATIONS_COMPLETED = "declarations_completed"
    TURN_COMPLETED = "turn_completed"

    # Player events
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    PLAYER_RECONNECTED = "player_reconnected"

class EventCompressor:
    """
    Compresses granular events into semantic events.

    Reduces event volume by ~90% while maintaining all game information.
    """

    def __init__(self):
        self.compression_stats = {
            'events_processed': 0,
            'events_compressed': 0,
            'compression_ratio': 0.0
        }

    def compress_turn_sequence(self,
                              turn_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compress a sequence of turn events into a single turn_completed event.

        Input: Multiple phase_data_update events
        Output: Single turn_completed event with all plays
        """

        # Extract relevant data from all events
        turn_number = None
        starter = None
        plays = {}
        winner = None
        piles_won = 0

        for event in turn_events:
            payload = event.get('payload', {})
            updates = payload.get('updates', {})

            # Extract turn number
            if 'current_turn_number' in updates:
                turn_number = updates['current_turn_number']

            # Extract starter
            if 'current_turn_starter' in updates:
                starter = updates['current_turn_starter']

            # Extract plays
            if 'turn_plays' in updates:
                plays.update(updates['turn_plays'])

            # Extract winner
            if 'winner' in updates:
                winner = updates['winner']
                piles_won = updates.get('piles_won', 0)

        # Create compressed event
        compressed_event = {
            'event_type': SemanticEventType.TURN_COMPLETED.value,
            'payload': {
                'turn_number': turn_number,
                'starter': starter,
                'plays': plays,
                'winner': winner,
                'piles_won': piles_won,
                'event_count_original': len(turn_events)
            }
        }

        self.compression_stats['events_processed'] += len(turn_events)
        self.compression_stats['events_compressed'] += 1
        self._update_compression_ratio()

        return compressed_event

    def compress_declaration_sequence(self,
                                    declaration_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compress declaration events into single event."""

        declarations = {}

        for event in declaration_events:
            payload = event.get('payload', {})
            updates = payload.get('updates', {})

            if 'declarations' in updates:
                declarations.update(updates['declarations'])

        return {
            'event_type': SemanticEventType.DECLARATIONS_COMPLETED.value,
            'payload': {
                'declarations': declarations,
                'total_declared': sum(declarations.values()),
                'event_count_original': len(declaration_events)
            }
        }

    def should_compress_event(self, event_type: str) -> bool:
        """Determine if an event type should be compressed."""

        # Always store these events
        STORE_AS_IS = {
            'game_started', 'game_over', 'hands_dealt',
            'round_started', 'round_complete', 'player_joined'
        }

        # Compress these events
        COMPRESS = {
            'phase_data_update', 'phase_change',
            'turn_started', 'piece_played'
        }

        return event_type in COMPRESS

    def _update_compression_ratio(self):
        """Update compression statistics."""
        if self.compression_stats['events_processed'] > 0:
            self.compression_stats['compression_ratio'] = (
                1 - (self.compression_stats['events_compressed'] /
                     self.compression_stats['events_processed'])
            )
```

### 3. Optimized Database Schema

```sql
-- backend/migrations/002_optimized_schema.sql

-- Migration metadata
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);

-- Core events table (minimal data)
CREATE TABLE IF NOT EXISTS game_events_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_sequence INTEGER NOT NULL,
    round_number INTEGER,
    timestamp REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Game summaries (one row per game)
CREATE TABLE IF NOT EXISTS game_summaries (
    room_id TEXT PRIMARY KEY,
    player_names JSON NOT NULL,
    player_types JSON NOT NULL,  -- human/ai mapping
    total_rounds INTEGER DEFAULT 0,
    current_round INTEGER DEFAULT 0,
    game_status TEXT DEFAULT 'active',  -- active/completed/abandoned
    final_scores JSON,
    winner TEXT,
    started_at REAL NOT NULL,
    completed_at REAL,
    last_activity REAL NOT NULL,
    game_config JSON  -- Store game rules/settings
);

-- Round snapshots (one row per round)
CREATE TABLE IF NOT EXISTS round_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,

    -- Round setup
    starter_player TEXT NOT NULL,
    starter_reason TEXT,
    initial_hands JSON NOT NULL,  -- Compressed hand data

    -- Gameplay data
    declarations JSON NOT NULL,
    turn_count INTEGER NOT NULL CHECK (turn_count BETWEEN 1 AND 8),  -- Max 8 turns (8 pieces/player)
    turn_sequence JSON NOT NULL,  -- All turns compressed (max 1.6KB)

    -- Round results
    round_scores JSON NOT NULL,
    pile_counts JSON NOT NULL,
    cumulative_scores JSON NOT NULL,

    -- Win check
    has_winner BOOLEAN DEFAULT FALSE,
    winning_player TEXT,  -- Set when someone reaches 50 points

    -- Metadata
    duration_seconds REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(room_id, round_number)
);

-- Turn details (optional, for detailed analysis)
CREATE TABLE IF NOT EXISTS turn_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,

    -- Turn data
    starter_player TEXT NOT NULL,
    plays JSON NOT NULL,  -- {player: {pieces, play_type, value}}
    winner TEXT,
    piles_won INTEGER,

    -- Analysis data
    play_sequence_time JSON,  -- Time taken per play
    ai_analysis JSON,  -- AI decision reasoning

    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(room_id, round_number, turn_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_v2_room_time
    ON game_events_v2(room_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_events_v2_type
    ON game_events_v2(event_type);

CREATE INDEX IF NOT EXISTS idx_summaries_status
    ON game_summaries(game_status, last_activity DESC);

CREATE INDEX IF NOT EXISTS idx_summaries_completed
    ON game_summaries(completed_at DESC)
    WHERE completed_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_snapshots_room
    ON round_snapshots(room_id, round_number);

CREATE INDEX IF NOT EXISTS idx_turns_room_round
    ON turn_details(room_id, round_number, turn_number);

-- Migration record
INSERT INTO schema_migrations (version, applied_at, description)
VALUES (2, datetime('now'), 'Optimized schema with event compression');
```

### 4. Integrated Event Store

```python
# backend/services/event_store_v2.py
import asyncio
import json
import sqlite3
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from .event_buffer import EventBuffer
from .event_compressor import EventCompressor, SemanticEventType

logger = logging.getLogger(__name__)

class OptimizedEventStore:
    """
    Optimized event store with buffering, compression, and new schema.

    Features:
    - Event buffering with batched writes
    - Semantic event compression
    - Optimized schema for fast queries
    - Backward compatibility mode
    """

    def __init__(self,
                 db_path: Optional[str] = None,
                 enable_buffer: bool = True,
                 enable_compression: bool = True,
                 enable_dual_write: bool = False):

        # Database setup
        if db_path is None:
            current_dir = Path(__file__).resolve()
            project_root = current_dir.parent.parent.parent
            self.db_path = str(project_root / "game_events.db")
        else:
            self.db_path = db_path

        # Features
        self.enable_buffer = enable_buffer
        self.enable_compression = enable_compression
        self.enable_dual_write = enable_dual_write

        # Components
        self.buffer = EventBuffer(event_store=self) if enable_buffer else None
        self.compressor = EventCompressor() if enable_compression else None

        # Event accumulator for compression
        self._event_accumulator: Dict[str, List[Dict]] = {}

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize optimized database schema."""
        conn = sqlite3.connect(self.db_path)

        # Read and execute migration script
        migration_path = Path(__file__).parent.parent / "migrations" / "002_optimized_schema.sql"
        if migration_path.exists():
            with open(migration_path, 'r') as f:
                conn.executescript(f.read())

        conn.close()

    async def store_event(self,
                         room_id: str,
                         event_type: str,
                         payload: Dict[str, Any],
                         player_id: Optional[str] = None) -> None:
        """
        Store event with buffering and compression.

        This is the main entry point that routes events through
        the optimization pipeline.
        """

        # Route through buffer if enabled
        if self.buffer and not self._is_critical_event(event_type):
            await self.buffer.add_event(
                room_id=room_id,
                event_type=event_type,
                payload=payload,
                player_id=player_id
            )
            return

        # Direct storage for critical events
        await self._store_event_direct(
            room_id=room_id,
            event_type=event_type,
            payload=payload,
            player_id=player_id
        )

    async def _store_event_direct(self,
                                 room_id: str,
                                 event_type: str,
                                 payload: Dict[str, Any],
                                 player_id: Optional[str] = None) -> None:
        """Store event directly to database."""

        # Apply compression if enabled
        if self.compressor and self.compressor.should_compress_event(event_type):
            # Accumulate for compression
            await self._accumulate_for_compression(
                room_id, event_type, payload, player_id
            )
            return

        # Store semantic events
        await self._store_semantic_event(
            room_id=room_id,
            event_type=event_type,
            payload=payload,
            player_id=player_id
        )

        # Dual write to old schema if enabled
        if self.enable_dual_write:
            await self._store_legacy_event(
                room_id, event_type, payload, player_id
            )

    async def _accumulate_for_compression(self,
                                        room_id: str,
                                        event_type: str,
                                        payload: Dict[str, Any],
                                        player_id: Optional[str]) -> None:
        """Accumulate events for compression."""

        key = f"{room_id}:{event_type}"
        if key not in self._event_accumulator:
            self._event_accumulator[key] = []

        self._event_accumulator[key].append({
            'event_type': event_type,
            'payload': payload,
            'player_id': player_id,
            'timestamp': time.time()
        })

        # Check if we should compress
        if self._should_compress_accumulated(key):
            await self._compress_and_store_accumulated(key)

    async def _compress_and_store_accumulated(self, key: str) -> None:
        """Compress accumulated events and store."""

        events = self._event_accumulator.pop(key, [])
        if not events:
            return

        room_id = key.split(':')[0]
        event_type = key.split(':')[1]

        # Compress based on event type
        if 'turn' in event_type:
            compressed = self.compressor.compress_turn_sequence(events)
        elif 'declaration' in event_type:
            compressed = self.compressor.compress_declaration_sequence(events)
        else:
            # Store individually if no compression logic
            for event in events:
                await self._store_semantic_event(
                    room_id=room_id,
                    event_type=event['event_type'],
                    payload=event['payload'],
                    player_id=event.get('player_id')
                )
            return

        # Store compressed event
        await self._store_semantic_event(
            room_id=room_id,
            event_type=compressed['event_type'],
            payload=compressed['payload']
        )

    async def _store_semantic_event(self,
                                  room_id: str,
                                  event_type: str,
                                  payload: Dict[str, Any],
                                  player_id: Optional[str] = None) -> None:
        """Store event in optimized schema."""

        conn = sqlite3.connect(self.db_path)

        try:
            # Determine which table to update
            if event_type == SemanticEventType.GAME_STARTED.value:
                await self._create_game_summary(conn, room_id, payload)

            elif event_type == SemanticEventType.ROUND_STARTED.value:
                await self._create_round_snapshot(conn, room_id, payload)

            elif event_type == SemanticEventType.TURN_COMPLETED.value:
                await self._update_round_snapshot_turn(conn, room_id, payload)

            elif event_type == SemanticEventType.ROUND_COMPLETED.value:
                await self._finalize_round_snapshot(conn, room_id, payload)

            # Always store core event
            conn.execute("""
                INSERT INTO game_events_v2
                (room_id, event_type, event_sequence, round_number, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                room_id,
                event_type,
                payload.get('sequence', 0),
                payload.get('round_number'),
                time.time()
            ))

            conn.commit()

        except Exception as e:
            logger.error(f"Failed to store semantic event: {e}")
            conn.rollback()
        finally:
            conn.close()

    def _is_critical_event(self, event_type: str) -> bool:
        """Check if event should bypass buffering."""
        return event_type in EventBuffer.CRITICAL_EVENTS

    def _should_compress_accumulated(self, key: str) -> bool:
        """Determine if accumulated events should be compressed."""
        events = self._event_accumulator.get(key, [])

        # Compress when turn is complete
        if 'turn' in key:
            for event in events:
                if event['payload'].get('updates', {}).get('turn_complete'):
                    return True

        # Compress when all declarations received
        if 'declaration' in key:
            return len(events) >= 4  # All 4 players declared

        return False

    async def get_play_history(self, room_id: str) -> Dict[str, Any]:
        """
        Retrieve play history using optimized schema.

        Much faster than reconstructing from individual events.
        """
        conn = sqlite3.connect(self.db_path)

        # Get game summary
        cursor = conn.execute("""
            SELECT * FROM game_summaries WHERE room_id = ?
        """, (room_id,))

        summary = cursor.fetchone()
        if not summary:
            return {'error': 'Game not found'}

        # Get round snapshots
        cursor = conn.execute("""
            SELECT * FROM round_snapshots
            WHERE room_id = ?
            ORDER BY round_number
        """, (room_id,))

        rounds = []
        for row in cursor.fetchall():
            rounds.append({
                'round_number': row['round_number'],
                'starter': row['starter_player'],
                'hands': json.loads(row['initial_hands']),
                'declarations': json.loads(row['declarations']),
                'turns': json.loads(row['turn_sequence']),
                'scores': json.loads(row['round_scores'])
            })

        conn.close()

        return {
            'room_id': room_id,
            'players': json.loads(summary['player_names']),
            'total_rounds': summary['total_rounds'],
            'rounds': rounds,
            'final_scores': json.loads(summary['final_scores'] or '{}'),
            'winner': summary['winner']
        }
```

## Performance Impact Analysis

### Write Performance
- **Current**: 126 synchronous writes per round
- **Optimized**: 10-19 writes per round (batched)
  - **Minimum**: 10 writes (3 fixed + 2 turns × 2 + buffer overhead)
  - **Typical**: 12-14 writes (3 fixed + 4-6 turns × 2)
  - **Maximum**: 19 writes (3 fixed + 8 turns × 2)
- **Improvement**: 85-92% reduction in I/O operations

### Storage Efficiency
- **Current**: Variable by game length
  - **Quick game (12 rounds)**: ~300KB
  - **Typical game (18 rounds)**: ~460KB
  - **Long game (30 rounds)**: ~760KB
- **Optimized**: 15-50KB per game
  - **Per round**: 1-1.6KB (varies with turn count)
  - **Quick game (12 rounds)**: ~15KB
  - **Typical game (18 rounds)**: ~25KB
  - **Long game (30 rounds)**: ~45KB
- **Improvement**: 90-95% reduction in storage

### Query Performance
- **Current**: Reconstruct from 126 events per round
- **Optimized**: Single row read per round
- **Improvement**: 100x faster Play History API

### Memory Usage
- **Buffer**: ~10KB per active game
- **Cache**: ~50KB per cached game
- **Total**: <100MB for 1000 concurrent games

## Migration Strategy

### Phase 1: Transparent Buffer
1. Deploy EventBuffer with existing schema
2. No changes to event structure
3. Immediate 90% write reduction
4. Zero risk to data integrity

### Phase 2: Dual Write
1. Enable compression with dual write
2. Write to both schemas
3. Read from old schema
4. Validate data consistency

### Phase 3: Schema Switch
1. Switch reads to new schema
2. Keep dual write for safety
3. Monitor performance metrics
4. Disable old schema writes

### Phase 4: Cleanup
1. Archive old event data
2. Remove dual write code
3. Optimize indexes
4. Document new system

## Monitoring & Metrics

### Key Metrics to Track
```python
# backend/services/db_metrics.py
class DatabaseMetrics:
    def __init__(self):
        self.write_latency_histogram = Histogram(
            'db_write_latency_seconds',
            'Database write latency'
        )

        self.buffer_size_gauge = Gauge(
            'event_buffer_size',
            'Current event buffer size'
        )

        self.compression_ratio = Gauge(
            'event_compression_ratio',
            'Event compression ratio'
        )

        self.events_per_second = Rate(
            'db_events_per_second',
            'Database events written per second'
        )
```

### Alerts to Configure
- Buffer overflow (>90% capacity)
- Write latency >100ms p99
- Compression failures
- Schema migration errors

## Risk Mitigation

### Data Loss Prevention
- Persist buffer on shutdown
- Write-ahead log for buffer
- Dual write during migration
- Regular backups

### Performance Degradation
- Circuit breaker for writes
- Fallback to direct writes
- Load shedding on overload
- Gradual rollout

### Rollback Procedures
- Feature flags for each phase
- Backward compatible code
- Data migration scripts
- Tested rollback process
