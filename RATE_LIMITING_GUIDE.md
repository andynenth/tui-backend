# Rate Limiting Implementation Guide

## Overview

This document describes the rate limiting implementation for the Liap Tui backend API, covering both REST endpoints and WebSocket connections.

## Architecture

### Components

1. **HTTP Rate Limiting Middleware** (`backend/api/middleware/rate_limit.py`)
   - Token bucket algorithm implementation
   - Per-IP rate limiting for REST endpoints
   - Automatic blocking for repeat offenders
   - Rate limit headers in HTTP responses

2. **WebSocket Rate Limiting** (`backend/api/middleware/websocket_rate_limit.py`)
   - Per-connection rate limiting
   - Per-event-type rate limiting
   - Room-based flood protection
   - Client identification and tracking

3. **Configuration** (`backend/api/config/rate_limit_config.py`)
   - Environment variable based configuration
   - Customizable rate limits per endpoint/event
   - Feature flags for enabling/disabling

## Default Rate Limits

### REST API Endpoints

| Endpoint | Requests/Minute | Burst Multiplier |
|----------|----------------|------------------|
| `/api/health` | 60 | 1.5 |
| `/api/health/detailed` | 30 | 1.5 |
| `/api/rooms/*` | 30 | 1.5 |
| `/api/recovery/*` | 10 | 1.5 |
| `/api/event-store/*` | 20 | 1.5 |
| Global default | 100 | 2.0 |

### WebSocket Events

| Event | Requests/Minute | Block Duration | Notes |
|-------|----------------|----------------|-------|
| `ping` | 120 | - | 2 per second allowed |
| `ack` | 200 | - | High limit for message acknowledgments |
| `declare` | 5 | - | Strict limit for game fairness |
| `play` | 20 | - | Normal gameplay pace |
| `create_room` | 5 | 5 minutes | Prevent room spam |
| `start_game` | 3 | 10 minutes | Prevent game start abuse |
| `request_redeal` | 3 | 5 minutes | Prevent redeal spam |

## Configuration

### Environment Variables

#### HTTP Rate Limiting

```bash
# Global settings
RATE_LIMIT_GLOBAL_REQUESTS=100
RATE_LIMIT_GLOBAL_WINDOW=60
RATE_LIMIT_GLOBAL_BURST=2.0

# Per-endpoint settings
RATE_LIMIT_HEALTH_REQUESTS=60
RATE_LIMIT_HEALTH_WINDOW=60
RATE_LIMIT_ROOMS_REQUESTS=30
RATE_LIMIT_ROOMS_WINDOW=60
```

#### WebSocket Rate Limiting

```bash
# Per-event settings
WS_RATE_LIMIT_DECLARE_REQUESTS=5
WS_RATE_LIMIT_DECLARE_WINDOW=60
WS_RATE_LIMIT_DECLARE_BURST=1.2

WS_RATE_LIMIT_PLAY_REQUESTS=20
WS_RATE_LIMIT_PLAY_WINDOW=60

WS_RATE_LIMIT_CREATE_ROOM_REQUESTS=5
WS_RATE_LIMIT_CREATE_ROOM_WINDOW=60
WS_RATE_LIMIT_CREATE_ROOM_BLOCK=300
```

#### Feature Flags

```bash
# Enable/disable rate limiting
RATE_LIMITING_ENABLED=true

# Log rate limit violations
RATE_LIMITING_LOG_VIOLATIONS=true

# Redis support (future enhancement)
RATE_LIMITING_REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379
```

## Implementation Details

### Token Bucket Algorithm

The rate limiter uses a token bucket algorithm:
1. Each client has a bucket with a maximum number of tokens (requests)
2. Tokens are replenished over a time window
3. Each request consumes one token
4. Burst traffic is allowed up to a multiplier
5. Empty bucket = request denied

### Client Identification

- **HTTP**: Uses IP address (supports X-Forwarded-For header)
- **WebSocket**: Uses hashed combination of IP, room ID, and connection ID

### Blocking Mechanism

Clients who repeatedly violate rate limits are temporarily blocked:
1. First violations: Return 429 with retry-after header
2. Repeated violations: Temporary block (configurable duration)
3. Blocked clients receive immediate 429 responses

## HTTP Response Headers

Rate-limited responses include these headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1704067200
X-RateLimit-Window: 60
Retry-After: 30
```

## WebSocket Error Messages

Rate-limited WebSocket messages receive:

```json
{
  "event": "error",
  "data": {
    "error_code": "NETWORK_RATE_LIMITED",
    "message": "Rate limit exceeded for this event type",
    "type": "rate_limit_error",
    "retry_after": 30,
    "limit": 5,
    "window": 60,
    "blocked": false
  }
}
```

## Monitoring

### Rate Limit Statistics Endpoint

```bash
GET /api/rate-limit/stats
```

Returns:
```json
{
  "success": true,
  "timestamp": 1704067200,
  "http_rate_limits": {
    "/api/health": {
      "total_requests": 150,
      "blocked_requests": 10,
      "unique_clients": 25,
      "block_rate": 6.67
    }
  },
  "websocket_rate_limits": {
    "total_connections": 45,
    "total_messages": 1250,
    "room_stats": {
      "room_123": 450,
      "lobby": 800
    }
  }
}
```

### Metrics

The rate limiter tracks:
- Total requests per endpoint/event
- Blocked requests count
- Unique clients
- Block rate percentage
- Per-room message counts

## Best Practices

1. **Set Appropriate Limits**: Balance between preventing abuse and allowing legitimate usage
2. **Monitor Block Rates**: High block rates may indicate limits are too strict
3. **Use Burst Multipliers**: Allow short bursts of activity for better UX
4. **Different Limits per Event**: Game events need stricter limits than system events
5. **Log Violations**: Enable logging to identify patterns of abuse

## Testing Rate Limits

### HTTP Endpoints

```bash
# Test rate limiting on health endpoint
for i in {1..70}; do 
  curl -i http://localhost:8000/api/health
done

# Check rate limit stats
curl http://localhost:8000/api/rate-limit/stats
```

### WebSocket Events

```javascript
// Test WebSocket rate limiting
const ws = new WebSocket('ws://localhost:8000/ws/test_room');

ws.onopen = () => {
  // Send many declare events
  for (let i = 0; i < 10; i++) {
    ws.send(JSON.stringify({
      event: 'declare',
      data: { player_name: 'test', value: 3 }
    }));
  }
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.event === 'error' && msg.data.type === 'rate_limit_error') {
    console.log('Rate limited!', msg.data);
  }
};
```

## Troubleshooting

### Common Issues

1. **All requests blocked**: Check if rate limits are too strict
2. **No rate limiting**: Verify RATE_LIMITING_ENABLED=true
3. **Headers missing**: Ensure middleware is properly registered
4. **WebSocket not limited**: Check event names match configuration

### Debug Mode

Enable debug logging:
```bash
RATE_LIMITING_LOG_VIOLATIONS=true
```

## Future Enhancements

1. **Redis Support**: For distributed rate limiting across multiple servers
2. **User-based Limits**: Different limits for authenticated users
3. **Dynamic Limits**: Adjust limits based on server load
4. **IP Whitelisting**: Exempt trusted IPs from rate limiting
5. **GraphQL Support**: Rate limiting for GraphQL queries