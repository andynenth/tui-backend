# Play History API Documentation

## Overview

The Play History API provides comprehensive game history data for Liap Tui games. This API is designed for:
- AI behavior analysis and improvement
- Game replay functionality
- Player statistics and analytics
- Debugging and game state verification

**Key Features:**
- Retrieves complete game history from persistent SQLite storage
- Works even when room is not in memory (no active game required)
- Survives server restarts - historical data is always available
- Falls back to in-memory data for active games

## Endpoints

### Get Complete Play History

```
GET /api/rooms/{room_id}/play-history
```

Retrieves the complete play history for all rounds in a game room.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| room_id | string | Yes | - | The unique room identifier |
| rounds | string | No | null | Comma-separated list of specific round numbers to retrieve (e.g., "1,3,5") |
| include_hands | boolean | No | true | Include detailed hand information for each player |
| include_ai_analysis | boolean | No | true | Include AI decision analysis and reasoning (AI players only) |
| format | string | No | "full" | Response format: "compact" or "full" |
| player_focus | string | No | null | Focus on specific player (filter plays) |

#### Response Format

The response includes:
- **Player Information**: Details about each player including type (human/AI) and AI version
- **Round History**: For each round:
  - Initial state with starter determination
  - Hands dealt (sorted by color then value: RED before BLACK, high to low)
  - Declaration phase with each player's target
  - Turn-by-turn play history with hand states
  - Scoring calculations and cumulative scores
- **AI Analysis** (optional): Decision reasoning for AI players

#### Examples

**Full Response** (default):
```json
{
  "room_id": "ROOM123",
  "total_rounds": 2,
  "players": {
    "Player 1": {
      "player_id": "player1",
      "player_name": "Player 1",
      "player_type": "human",
      "ai_version": null
    },
    "Bot 2": {
      "player_id": "bot2",
      "player_name": "Bot 2",
      "player_type": "ai",
      "ai_version": "v2.0"
    }
  },
  "rounds": [
    {
      "round_number": 1,
      "initial_state": {
        "starter": {
          "player_id": "player1",
          "player_name": "Player 1",
          "reason": "red_general",
          "highest_card": "GENERAL_RED"
        },
        "player_order": ["Player 1", "Bot 2", "Bot 3", "Bot 4"]
      },
      "hands_dealt": {
        "Player 1": [
          {"kind": "GENERAL_RED", "point": 9999},
          {"kind": "ADVISOR_RED", "point": 60}
        ]
      },
      "declaration_phase": {
        "declarations": [
          {
            "player_id": "player1",
            "declared": 2,
            "position": 0,
            "strategy_notes": null
          }
        ],
        "total_declared": 8,
        "pile_room_calculation": {
          "Player 1": 6
        }
      },
      "turn_history": [
        {
          "turn_number": 1,
          "plays": [
            {
              "player_id": "player1",
              "player_name": "Player 1",
              "pieces_played": [{"kind": "SOLDIER_RED", "point": 1}],
              "play_type": "SINGLE",
              "hand_before": [...],
              "hand_after": [...],
              "captured_count": 0,
              "declared_count": 2,
              "ai_decision_analysis": null
            }
          ],
          "winner": {
            "player_id": "bot3",
            "player_name": "Bot 3",
            "winning_play": [{"kind": "ELEPHANT_RED", "point": 50}],
            "pieces_captured": 4
          },
          "next_starter": "Bot 3",
          "game_state_after": {
            "Player 1": {"captured": 0, "declared": 2, "hand_size": 7}
          }
        }
      ],
      "round_summary": {
        "total_turns": 8,
        "final_captures": {
          "Player 1": {"captured": 7, "declared": 2, "difference": 5}
        },
        "scoring": {
          "Player 1": {
            "points": 10,
            "multiplier": 1,
            "reason": "overcapture"
          }
        },
        "cumulative_scores": {
          "Player 1": 10
        }
      }
    }
  ]
}
```

**Compact Response** (`format=compact`):
```json
{
  "room_id": "ROOM123",
  "total_rounds": 2,
  "players": {...},
  "rounds": [
    {
      "round_number": 1,
      "initial_state": {...},
      "hands_dealt": {},  // Empty in compact format
      "declaration_phase": {
        "declarations": [
          {"player_id": "player1", "declared": 2}
        ],
        "total_declared": 8
      },
      "turn_history": [],  // Minimal in compact format
      "round_summary": {
        "total_turns": 8,
        "final_captures": {...},
        "scoring": {...},
        "cumulative_scores": {...}
      }
    }
  ]
}
```

### Get Play History for Round Range

```
GET /api/rooms/{room_id}/play-history/rounds
```

Retrieves play history for a specific range of rounds.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| room_id | string | Yes | - | The unique room identifier |
| from | integer | No | 1 | Starting round number (inclusive) |
| to | integer | Yes | - | Ending round number (inclusive) |
| include_hands | boolean | No | true | Include detailed hand information |
| include_ai_analysis | boolean | No | true | Include AI decision analysis |
| format | string | No | "full" | Response format: "compact" or "full" |

#### Examples

- Get rounds 1-5: `/api/rooms/ROOM123/play-history/rounds?from=1&to=5`
- Get single round: `/api/rooms/ROOM123/play-history/rounds?from=3&to=3`
- Get compact format: Add `&format=compact`

## Error Responses

All error responses follow a standardized format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status_code": 400,
    "field": "field_name",  // Optional
    "context": {}  // Optional additional context
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-10T10:30:00Z",
  "path": "/api/rooms/ABC123/play-history"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| ROOM_NOT_FOUND | 404 | The specified room ID does not exist (checked in both memory and SQLite) |
| NO_ACTIVE_GAME | 400 | The room exists in memory but has no active game |
| INVALID_RANGE | 400 | The 'from' round is greater than 'to' round |
| VALIDATION_ERROR | 422 | Invalid query parameters |

## Performance Considerations

### Response Times
- **Warning Alert**: Triggered if response time exceeds 1 second
- **Critical Alert**: Triggered if response time exceeds 3 seconds

### Optimization Tips
1. Use `format=compact` for reduced response size (30-50% smaller)
2. Use `include_hands=false` to exclude detailed hand information
3. Use `include_ai_analysis=false` to exclude AI reasoning data
4. Query specific rounds instead of entire game history for large games

### Caching
- SQLite results are cached for 5 minutes to improve performance
- Completed rounds are candidates for caching
- In-progress games always return fresh data
- Cache TTL varies based on game state

## Authentication & Rate Limiting

### Authentication
- **Current Status**: None required (public endpoint)
- **Future**: May require API key or session authentication

### Rate Limiting
- **Limit**: 100 requests per minute per IP address
- **Headers**: Rate limit info included in response headers
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

## Monitoring & Alerts

### Metrics Collected
- Response times (p50, p95, p99 percentiles)
- Request counts by endpoint
- Error rates and types
- Cache hit/miss ratios
- Round counts per request

### Alert Thresholds
- **Slow Query Warning**: Response time > 1s
- **Slow Query Critical**: Response time > 3s
- **High Error Rate**: Error rate > 5%

### Monitoring Endpoints
- `GET /api/metrics`: Overall API metrics
- `GET /api/metrics/play-history`: Play history specific metrics
- `GET /api/alerts`: Recent performance alerts
- `GET /api/health/performance`: Performance health status

## Integration Guide

### JavaScript/TypeScript
```typescript
// Fetch complete play history
const response = await fetch('/api/rooms/ROOM123/play-history');
const playHistory = await response.json();

// Fetch specific rounds with compact format
const compactResponse = await fetch(
  '/api/rooms/ROOM123/play-history?rounds=1,3,5&format=compact'
);

// Fetch round range without AI analysis
const rangeResponse = await fetch(
  '/api/rooms/ROOM123/play-history/rounds?from=1&to=10&include_ai_analysis=false'
);
```

### Python
```python
import requests

# Fetch complete play history
response = requests.get(f"{API_URL}/rooms/{room_id}/play-history")
play_history = response.json()

# Fetch with query parameters
params = {
    "format": "compact",
    "include_hands": False,
    "rounds": "1,2,3"
}
response = requests.get(f"{API_URL}/rooms/{room_id}/play-history", params=params)
```

## Best Practices

1. **Use Compact Format**: When you only need summary data
2. **Filter Rounds**: Query only the rounds you need
3. **Handle Errors**: Always check for error responses
4. **Monitor Performance**: Watch for slow query alerts
5. **Respect Rate Limits**: Implement exponential backoff on 429 errors

## Data Storage

### SQLite Event Store Integration
- Primary data source for historical game data
- Stores all game events in `game_events.db`
- Enables complete game reconstruction from events
- Survives server restarts and crashes

### Data Sources Priority
1. **SQLite Event Store**: Primary source for all historical data
2. **In-Memory Game State**: Fallback for active games not yet in SQLite

## Future Enhancements

1. **WebSocket Subscriptions**: Real-time play history updates
2. **Batch Operations**: Fetch multiple rooms in one request
3. **Data Export**: CSV/JSON export formats
4. **Analytics Endpoints**: Pre-computed statistics and trends
5. **Replay API**: Step-by-step game replay functionality
