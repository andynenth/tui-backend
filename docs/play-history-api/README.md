# Play History API Documentation

This directory contains documentation for the Play History API implementation, including design decisions, troubleshooting notes, and integration details.

## Overview

The Play History API provides comprehensive game history data for analysis and replay. It reconstructs complete game state from events stored in SQLite, including player hands, moves, and scoring.

## Documentation Files

### [Implementation Plan](implementation-plan.md)
The original implementation plan for the Play History API, including:
- API endpoint design
- Data structures and models
- Event sourcing strategy
- Performance considerations

### [SQLite Integration](sqlite-integration.md)
Details about how the Play History API integrates with the SQLite event store:
- Event extraction logic
- Data reconstruction from events
- Caching strategy
- Performance optimizations

### [SQLite Summary](sqlite-summary.md)
Quick summary of the SQLite-based implementation:
- Key benefits
- Architecture overview
- Event types used

### [Field Status](field-status.md)
Current status of all Play History API fields:
- Which fields are populated
- Known issues and fixes
- Testing status

### [Captured Count Explanation](captured-count-explanation.md)
Detailed explanation of how the `captured_count` field works:
- Why it shows 0 on turn 1
- How captures are tracked
- Examples from actual game data

## Recent Fixes

### Empty `hands_dealt` and `hand_after` Fields (Fixed)

**Problem**: These fields were showing as empty in the API response.

**Root Cause**: Custom events (`hands_dealt`, `play_with_context`) were being broadcast via WebSocket but not stored in the database.

**Solution**:
1. Store `hands_dealt` events in the database
2. Calculate `hand_before` and `hand_after` from existing `action_processed` events rather than storing duplicate `play_with_context` events

This approach:
- Avoids storing redundant data
- Uses event sourcing properly
- Calculates hand states on-the-fly from the source of truth

## API Endpoints

- **Main endpoint**: `/api/rooms/{room_id}/play-history`
- **Range endpoint**: `/api/rooms/{room_id}/play-history/rounds?from=1&to=5`

See the backend API documentation for full details: `backend/api/docs/PLAY_HISTORY_API.md`
