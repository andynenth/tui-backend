# Play History API Architecture

## Overview

The Play History API provides comprehensive game history data through a layered architecture that separates concerns and optimizes performance.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Request                          │
│              GET /api/rooms/{room_id}/play-history              │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API Route Layer                           │
│                   play_history.py                                │
│  • Request validation       • Query parameter parsing            │
│  • Error handling          • Response formatting                 │
│  • Performance monitoring  • Alert triggering                    │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Service Layer                                │
│                play_history_service.py                           │
│  • Orchestration logic     • SQLite integration                  │
│  • Fallback handling       • Async coordination                  │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
┌─────────────────────────────┐  ┌────────────────────────────────┐
│  Event Store Service        │  │    In-Memory Extraction        │
│ event_store_play_history.py │  │  • Game state extraction       │
│ • SQLite event parsing      │  │  • Hand sorting algorithm      │
│ • Event reconstruction      │  │  • AI analysis extraction      │
│ • 5-minute caching          │  │  • Format optimization         │
│ • Primary data source       │  │  • Fallback data source        │
└──────────────┬──────────────┘  └─────────────┬────────────────┘
               │                                │
               ▼                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Models                                │
│                    play_history.py                               │
│  • Pydantic models         • Validation rules                    │
│  • JSON serialization      • Type safety                         │
└─────────────────────────────────────────────────────────────────┘
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
┌─────────────────────────────┐  ┌────────────────────────────────┐
│     SQLite Event Store      │  │        Game Engine             │
│      game_events.db         │  │   game.py, player.py, rules.py │
│ • Persistent storage        │  │ • Core game state              │
│ • Event sourcing            │  │ • Turn history                 │
│ • Complete history          │  │ • Player hands                 │
└─────────────────────────────┘  └────────────────────────────────┘
```

## Data Flow

### 1. Request Processing
```
Client Request → FastAPI Router → Request Validation → Query Parsing
```

### 2. Data Extraction
```
Primary Path (SQLite):
PlayHistoryService → EventStorePlayHistoryService → SQLite Events → Event Reconstruction

Fallback Path (Memory):
Room Manager → Game Instance → PlayHistoryService → Data Extraction Methods
```

### 3. Data Transformation
```
Raw Game Data → Sorting/Filtering → Format Optimization → Pydantic Models
```

### 4. Response Generation
```
Pydantic Serialization → JSON Response → Performance Metrics → Client
```

## Key Components

### Route Layer (`play_history.py`)
- **Responsibilities:**
  - HTTP request handling
  - Parameter validation
  - Error response formatting
  - Performance monitoring
  - Alert integration

- **Key Methods:**
  - `get_play_history()`: Main endpoint handler
  - `get_rounds_range()`: Range-based query handler

### Service Layer (`play_history_service.py`)
- **Responsibilities:**
  - Orchestration between SQLite and memory sources
  - Async coordination and fallback handling
  - Integration with PlayHistoryV2Service (V2 event store)

- **Key Methods:**
  - `build_play_history()`: Main orchestration (now async)
  - Falls back to memory extraction if SQLite fails

### Event Store Service (`play_history_v2.py`)
- **Responsibilities:**
  - V2 optimized schema access
  - Fast extraction from pre-computed round snapshots
  - 10x faster query performance than V1
  - Primary data source for historical games

- **Key Methods:**
  - `get_play_history()`: Main entry point
  - Uses pre-computed game_summaries and round_snapshots
  - Optimized for performance with V2 schema

### Data Models (`models/play_history.py`)
- **Key Models:**
  - `PlayHistoryResponse`: Top-level response
  - `RoundHistory`: Per-round data
  - `TurnInfo`: Turn-by-turn plays
  - `PlayData`: Individual player actions
  - `AIDecisionAnalysis`: AI reasoning

## Performance Optimizations

### 1. Compact Format
- Reduces response size by 30-50%
- Excludes turn history and hand details
- Retains essential scoring information

### 2. Query Filtering
- Round-specific queries avoid loading all data
- Efficient filtering at service layer

### 3. Lazy Loading
- AI analysis only extracted when requested
- Hand details can be excluded

### 4. Caching Implementation
- SQLite results cached for 5 minutes
- Cache key includes room_id, format, and AI analysis flags
- Completed rounds could be cached longer
- Player information rarely changes

## Monitoring & Alerts

### Performance Metrics
- Response time percentiles (p50, p95, p99)
- Response size distribution
- Cache hit rates
- Error rates by type

### Alert Thresholds
- Warning: Response time > 1 second
- Critical: Response time > 3 seconds
- Cooldown: 5 minutes between alerts

## Error Handling

### Error Flow
```
Exception → Error Response Builder → Structured Error → Client
```

### Error Types
- `ROOM_NOT_FOUND`: Room ID not found in memory or SQLite
- `NO_ACTIVE_GAME`: Room exists in memory but has no game
- `INVALID_RANGE`: Bad round range
- `INTERNAL_ERROR`: Unexpected failures

## Security Considerations

1. **Input Validation**: All parameters validated
2. **SQL Injection**: Not applicable (no direct DB queries)
3. **Rate Limiting**: 100 requests/minute/IP
4. **Authentication**: Currently public (future: JWT tokens)

## Current Implementation

### SQLite Integration (Completed)
- Event store in `game_events.db` serves as primary data source
- Complete event history enables full game reconstruction
- Works even when room is not in memory
- Persists across server restarts

## Future Enhancements

### Advanced Database Features
- Denormalized `play_history_view` table for faster queries
- Indexed by (room_id, round_number, player_id)
- Background task for history pre-computation

### Caching Layer
- Redis for completed rounds
- TTL based on game state
- Cache invalidation on updates

### Real-time Updates
- WebSocket notifications for new rounds
- Incremental history updates
- Live game following

## Testing Strategy

### Unit Tests
- Service layer methods
- Data transformation logic
- Edge case handling

### Integration Tests
- Full request flow
- Performance benchmarks
- Concurrent request handling

### Load Tests
- 100+ concurrent requests
- Large game histories (20+ rounds)
- Memory usage monitoring
