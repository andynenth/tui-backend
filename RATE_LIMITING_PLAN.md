# Rate Limiting Implementation Plan for Liap Tui

## Executive Summary

Rate limiting has already been implemented in the Liap Tui codebase with comprehensive support for both REST API endpoints and WebSocket connections. However, according to CODE_QUALITY_CHECKLIST.md, the feature is marked as "HIGH RISK - DO LAST" because previous implementation attempts broke WebSocket connections. This plan outlines a systematic approach to verify, test, fix, and improve the existing rate limiting implementation to ensure it works reliably without disrupting game functionality.

## Scope

This plan covers:
- Analysis and verification of the current rate limiting implementation
- Identification and resolution of WebSocket connection issues
- Configuration management improvements
- Comprehensive testing strategy
- Monitoring and metrics implementation
- Documentation and deployment procedures

Out of scope:
- Authentication system changes
- Database-backed rate limiting (current implementation is in-memory)
- Third-party rate limiting services

## Current Architecture

### Existing Components

1. **Core Rate Limiter** (`backend/api/middleware/rate_limit.py`)
   - Token bucket algorithm implementation
   - Per-IP and per-route rate limiting
   - Burst traffic handling
   - Temporary blocking for repeat offenders
   - Statistics tracking

2. **WebSocket Rate Limiter** (`backend/api/middleware/websocket_rate_limit.py`)
   - Per-connection, per-event-type rate limiting
   - Room-based flood protection
   - Client identification via hashed connection details
   - Specific limits for each game event type

3. **Integration Points**
   - REST API: Middleware added in `backend/api/main.py:111`
   - WebSocket: Rate limit checks in `backend/api/routes/ws.py:48-55`
   - Error handling with StandardError format support

### Current Rate Limits

#### REST API Endpoints
- `/api/health`: 60 requests/minute
- `/api/health/detailed`: 30 requests/minute
- `/api/rooms`: 30 requests/minute
- `/api/recovery`: 10 requests/minute
- Global default: 100 requests/minute with 2x burst

#### WebSocket Events
- System events (ping, ack): 120-200 requests/minute
- Room management: 3-10 requests/minute
- Game events: 5-20 requests/minute
- Create room: 5 requests/minute with 5-minute block
- Start game: 3 requests/minute with 10-minute block

## Problem Analysis

### Known Issues

1. **WebSocket Connection Breakage**
   - Previous implementation caused WebSocket disconnections
   - Likely due to aggressive rate limiting or improper error handling
   - May affect game state synchronization

2. **Configuration Rigidity**
   - Rate limits hardcoded in source files
   - No environment-based configuration
   - Difficult to adjust for different deployment scenarios

3. **Limited Visibility**
   - No metrics exposed via health endpoints
   - Rate limit violations not properly logged
   - Difficult to monitor and tune limits

## Implementation Strategy

### Phase 1: Verification and Issue Identification (Day 1)

#### Tasks:
1. **Create Test Suite** (`backend/tests/test_rate_limiting.py`)
   - Unit tests for RateLimiter class
   - Integration tests for REST API rate limiting
   - WebSocket rate limiting tests with mock connections
   - Test burst traffic handling
   - Test client blocking and unblocking

2. **Manual Testing Protocol**
   - Set up local development environment
   - Create test scenarios for WebSocket disconnection
   - Document exact conditions that cause failures
   - Test game flow with rate limiting enabled

3. **Code Review**
   - Analyze WebSocket error handling in `ws.py`
   - Review connection lifecycle management
   - Check for race conditions in rate limiter
   - Verify thread safety of shared data structures

### Phase 2: Fix WebSocket Issues (Day 2)

#### Tasks:
1. **Improve Error Handling** (`backend/api/routes/ws.py`)
   ```python
   # Ensure rate limit errors don't close connection
   if not rate_limit_allowed:
       await send_rate_limit_error(registered_ws, rate_limit_info)
       # Log the violation but continue connection
       logger.warning(f"Rate limit exceeded for {client_id} on {event_name}")
       continue  # Don't break the WebSocket loop
   ```

2. **Add Grace Period for Game Events**
   - Implement soft limits with warnings before hard limits
   - Allow critical game events (like turn timeouts) to bypass limits
   - Add event priority system

3. **Connection-Level Protection**
   - Implement per-connection message queuing
   - Add backpressure handling
   - Prevent single client from flooding a room

### Phase 3: Configuration Management (Day 3)

#### Tasks:
1. **Create Configuration Module** (`backend/config/rate_limits.py`)
   ```python
   import os
   from dataclasses import dataclass
   
   @dataclass
   class RateLimitConfig:
       # REST API limits
       health_endpoint_rpm: int = int(os.getenv("RATE_LIMIT_HEALTH", 60))
       rooms_endpoint_rpm: int = int(os.getenv("RATE_LIMIT_ROOMS", 30))
       
       # WebSocket limits
       ws_ping_rpm: int = int(os.getenv("RATE_LIMIT_WS_PING", 120))
       ws_game_action_rpm: int = int(os.getenv("RATE_LIMIT_WS_GAME", 20))
       
       # Global settings
       burst_multiplier: float = float(os.getenv("RATE_LIMIT_BURST", 1.5))
       block_duration: int = int(os.getenv("RATE_LIMIT_BLOCK_DURATION", 60))
   ```

2. **Update .env.example**
   ```bash
   # Rate Limiting Configuration
   RATE_LIMIT_HEALTH=60
   RATE_LIMIT_ROOMS=30
   RATE_LIMIT_WS_PING=120
   RATE_LIMIT_WS_GAME=20
   RATE_LIMIT_BURST=1.5
   RATE_LIMIT_BLOCK_DURATION=60
   RATE_LIMIT_ENABLED=true
   ```

3. **Add Feature Toggle**
   - Environment variable to enable/disable rate limiting
   - Useful for development and debugging
   - Gradual rollout capability

### Phase 4: Enhanced Testing (Day 4)

#### Tasks:
1. **Load Testing Suite** (`backend/tests/load_test_rate_limits.py`)
   - Use `locust` or `pytest-benchmark` for load testing
   - Test concurrent WebSocket connections
   - Simulate realistic game scenarios
   - Measure performance impact

2. **Integration Tests** (`backend/tests/test_game_with_rate_limits.py`)
   - Full game flow with rate limiting enabled
   - Multiple players in multiple rooms
   - Test reconnection scenarios
   - Verify game state consistency

3. **Edge Case Testing**
   - Network interruptions during rate limiting
   - Client reconnection after being rate limited
   - Room cleanup with rate-limited clients
   - State recovery after rate limit blocks

### Phase 5: Monitoring and Metrics (Day 5)

#### Tasks:
1. **Add Metrics Endpoint** (`backend/api/routes/routes.py`)
   ```python
   @router.get("/api/metrics/rate_limits", tags=["monitoring"])
   async def get_rate_limit_metrics():
       rate_limiter = get_rate_limiter()
       ws_rate_limiter = get_websocket_rate_limiter()
       
       return {
           "rest_api": rate_limiter.get_stats(),
           "websocket": ws_rate_limiter.get_connection_stats(),
           "configuration": get_current_limits()
       }
   ```

2. **Enhanced Logging**
   - Log all rate limit violations with context
   - Track patterns of abuse
   - Alert on suspicious activity
   - Daily summary reports

3. **Health Check Integration**
   - Add rate limit status to health endpoint
   - Show current load vs capacity
   - Alert when approaching limits

## Testing Plan

### Unit Tests
- `test_rate_limiter_basic`: Token bucket algorithm
- `test_burst_handling`: Burst multiplier functionality
- `test_client_blocking`: Temporary blocking mechanism
- `test_cleanup_task`: Old data cleanup
- `test_websocket_rate_limiter`: WebSocket-specific logic

### Integration Tests
- `test_rest_api_rate_limiting`: All REST endpoints
- `test_websocket_rate_limiting`: All WebSocket events
- `test_game_flow_with_limits`: Complete game scenarios
- `test_reconnection_handling`: Client reconnection
- `test_room_flood_protection`: Room-level protection

### Load Tests
- 100 concurrent REST API clients
- 50 concurrent WebSocket connections
- 10 active game rooms with 4 players each
- Sustained load for 30 minutes
- Measure: response times, error rates, resource usage

### Manual Testing Checklist
- [ ] Create room with rate limiting
- [ ] Join room rapidly (test join limits)
- [ ] Play complete game with normal pace
- [ ] Attempt to spam game actions
- [ ] Test reconnection after rate limit
- [ ] Verify error messages are clear
- [ ] Check metrics endpoint accuracy

## Rollback Plan

### Immediate Rollback (< 5 minutes)
1. Set `RATE_LIMIT_ENABLED=false` in environment
2. Restart application
3. Monitor for normal operation
4. Document issues encountered

### Full Rollback Procedure
1. Revert to previous commit
2. Remove rate limiting middleware from `main.py`
3. Remove rate limit checks from `ws.py`
4. Deploy previous version
5. Conduct post-mortem

### Rollback Triggers
- WebSocket connections dropping > 5%
- Game state corruption reports
- Performance degradation > 20%
- Critical game features broken

## Success Criteria

1. **Functional Requirements**
   - All rate limits enforced without breaking connections
   - Game flow unaffected for normal players
   - Clear error messages for rate-limited users
   - Graceful degradation under load

2. **Performance Requirements**
   - < 5ms latency added by rate limiting
   - < 5% additional CPU usage
   - Memory usage stable over time
   - No memory leaks from tracking data

3. **Operational Requirements**
   - Configuration via environment variables
   - Metrics available for monitoring
   - Logs capture all violations
   - Easy to adjust limits without code changes

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Verification | 1 day | Test suite, issue documentation |
| Phase 2: Fix WebSocket | 1 day | Updated error handling, grace periods |
| Phase 3: Configuration | 1 day | Config module, environment setup |
| Phase 4: Testing | 1 day | Load tests, integration tests |
| Phase 5: Monitoring | 1 day | Metrics endpoint, logging |
| Deployment & Validation | 1 day | Production rollout, monitoring |

Total: 6 days

## Dependencies

### Python Packages
- Existing: `fastapi`, `asyncio`, `dataclasses`
- May need: `python-dotenv` (already in requirements)
- For testing: `pytest`, `pytest-asyncio`, `httpx`, `websockets`

### No External Services Required
- In-memory rate limiting (no Redis/database needed)
- No third-party rate limiting services

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| WebSocket disconnections | High | High | Extensive testing, gradual rollout |
| Performance degradation | Medium | Medium | Load testing, performance monitoring |
| Configuration errors | Low | Medium | Validation, sensible defaults |
| Memory leaks | Low | High | Cleanup tasks, memory monitoring |

## Documentation Updates

1. **Update CLAUDE.md**
   - Add rate limiting configuration section
   - Document testing procedures
   - Add troubleshooting guide

2. **Update README.md**
   - Add rate limiting section
   - Environment variable documentation
   - Monitoring endpoints

3. **Create RATE_LIMITING.md**
   - Detailed technical documentation
   - Configuration reference
   - Troubleshooting guide

## Post-Implementation Tasks

1. Monitor metrics for 1 week
2. Tune limits based on real usage
3. Document patterns of normal vs abusive usage
4. Create runbook for rate limit incidents
5. Train team on configuration and monitoring

---

**Document Version**: 1.0  
**Created**: January 2025  
**Status**: Ready for Implementation  
**Owner**: Development Team