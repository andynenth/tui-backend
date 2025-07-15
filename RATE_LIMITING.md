# Rate Limiting Documentation

This document describes the rate limiting implementation in Liap Tui, including configuration, behavior, and troubleshooting.

## Overview

Liap Tui implements comprehensive rate limiting to:
- Prevent abuse and DoS attacks
- Ensure fair resource usage among players
- Maintain game stability under load
- Protect against automated spam

## Features

### 1. Dual-Layer Protection
- **REST API**: Per-endpoint rate limiting with customizable limits
- **WebSocket**: Per-event-type rate limiting with connection tracking

### 2. Priority-Based System
Events are classified by priority:
- **CRITICAL**: Never blocked (e.g., timeout handling, disconnect cleanup)
- **HIGH**: Important game events with lenient limits (e.g., playing pieces)
- **NORMAL**: Standard operations (e.g., room creation)
- **LOW**: Non-essential events with strict limits (e.g., pings)

### 3. Grace Periods
- Warning at 80% of limit (configurable)
- 20% extra allowance during grace period
- Prevents sudden disconnections during active gameplay

### 4. Smart Error Handling
- WebSocket connections remain open when rate limited
- Clear error messages with retry information
- Graceful degradation for critical events

## Configuration

All rate limits can be configured via environment variables. Copy `.env.example` to `.env` and adjust as needed.

### Key Configuration Variables

```bash
# Master Controls
RATE_LIMIT_ENABLED=true              # Enable/disable all rate limiting
RATE_LIMIT_DEBUG=false               # Enable debug logging

# Global Settings
RATE_LIMIT_GLOBAL_RPM=100           # Global requests per minute
RATE_LIMIT_BURST_MULTIPLIER=1.5    # Allow 50% burst traffic
RATE_LIMIT_BLOCK_DURATION=300       # Block duration (5 minutes)

# Game-Specific Limits
RATE_LIMIT_WS_DECLARE_RPM=5         # Declarations per minute
RATE_LIMIT_WS_PLAY_RPM=20           # Plays per minute
RATE_LIMIT_WS_CREATE_ROOM_RPM=5     # Room creations per minute

# Grace Period
RATE_LIMIT_GRACE_WARNING=0.8        # Warn at 80% usage
RATE_LIMIT_GRACE_MULTIPLIER=1.2     # 20% extra during grace
```

### Disabling Rate Limiting

For development or testing:
```bash
RATE_LIMIT_ENABLED=false
```

## Client Integration

### Handling Rate Limit Errors

WebSocket clients should handle two types of rate limit messages:

1. **Rate Limit Warning** (event: `rate_limit_warning`)
```json
{
  "event": "rate_limit_warning",
  "data": {
    "type": "rate_limit_warning",
    "message": "Approaching rate limit for declare",
    "remaining": 2,
    "limit": 5,
    "priority": "HIGH",
    "grace_period": true,
    "suggestion": "Please slow down to avoid being rate limited"
  }
}
```

2. **Rate Limit Error** (event: `error`)
```json
{
  "event": "error",
  "data": {
    "code": "NETWORK_RATE_LIMITED",
    "message": "Rate limit exceeded for this event type",
    "context": {
      "retry_after": 30,
      "limit": 5,
      "window": 60,
      "blocked": false
    }
  }
}
```

### Best Practices

1. **Implement Exponential Backoff**: When rate limited, wait before retrying
2. **Show User Feedback**: Display warnings to users approaching limits
3. **Cache Responses**: Reduce unnecessary requests
4. **Batch Operations**: Combine multiple operations when possible

## Monitoring

### Metrics Endpoint

Check rate limit statistics:
```bash
GET /api/metrics/rate_limits
```

Response includes:
- Current usage per endpoint/event
- Number of blocked requests
- Active client counts
- Configuration values

### Health Check

The `/api/health/detailed` endpoint includes rate limit status:
```json
{
  "rate_limiting": {
    "enabled": true,
    "total_requests": 12345,
    "blocked_requests": 23,
    "unique_clients": 45
  }
}
```

## Troubleshooting

### Common Issues

1. **"WebSocket keeps disconnecting"**
   - Check if `RATE_LIMIT_ENABLED=true`
   - Verify client isn't exceeding limits
   - Check server logs for rate limit violations

2. **"Can't create rooms"**
   - Default limit is 5 rooms per minute
   - Check if IP is temporarily blocked
   - Wait for block duration to expire

3. **"Game feels laggy"**
   - Rate limits might be too restrictive
   - Increase `RATE_LIMIT_WS_PLAY_RPM`
   - Check grace period configuration

### Debug Mode

Enable debug logging to see all rate limit checks:
```bash
RATE_LIMIT_DEBUG=true
LOG_LEVEL=DEBUG
```

### Testing Rate Limits

Use the provided test scripts:
```bash
# Run manual tests
python backend/tests/manual_rate_limit_test.py

# Run automated test suite
pytest backend/tests/test_rate_limiting.py -v
```

## Performance Impact

- **CPU**: < 5% overhead with default settings
- **Memory**: ~1MB per 1000 active clients
- **Latency**: < 1ms per request check

## Security Considerations

1. **IP Spoofing**: Use `X-Forwarded-For` carefully behind proxies
2. **Distributed Attacks**: Consider additional DDoS protection
3. **State Synchronization**: In-memory limits don't sync across instances

## Future Enhancements

- Redis-backed rate limiting for multi-instance deployments
- Machine learning for adaptive limits
- Per-user rate limiting with authentication
- Geographic-based rate limiting

---

For implementation details, see `RATE_LIMITING_PLAN.md`