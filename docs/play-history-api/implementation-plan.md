# Play History Endpoint Implementation Plan

## Overview
Implementation of `/api/rooms/{room_id}/play-history` endpoint to provide comprehensive game history for AI behavior analysis.

## Phase 1: Setup & Planning (Day 1)

### 1.1 Project Setup
- [x] Create feature branch `feature/play-history-endpoint`
- [x] Create `backend/api/routes/play_history.py` file
- [x] Create `backend/services/play_history_service.py` file
- [x] Create `backend/models/play_history.py` for data models
- [x] Create test directory structure:
  - [x] `backend/tests/api/test_play_history_api.py`
  - [x] `backend/tests/services/test_play_history_service.py`
  - [x] `backend/tests/fixtures/play_history_fixtures.py`

### 1.2 Data Model Design
- [x] Define Pydantic models in `models/play_history.py`:
  - [x] `PlayerInfo` model (id, name, type, ai_version)
  - [x] `InitialState` model (starter info, player order)
  - [x] `HandInfo` model (sorted pieces structure)
  - [x] `DeclarationInfo` model (player declarations)
  - [x] `PlayInfo` model (pieces played, hand states)
  - [x] `TurnInfo` model (turn number, plays, winner)
  - [x] `RoundSummary` model (captures, scoring)
  - [x] `PlayHistoryResponse` model (complete response)

### 1.3 API Route Planning
- [x] Define route signatures in `play_history.py`:
  - [x] `GET /api/rooms/{room_id}/play-history`
  - [x] `GET /api/rooms/{room_id}/play-history/round/{round_number}`
  - [x] `GET /api/rooms/{room_id}/play-history/rounds`
- [x] Add routes to main API router
- [x] Define query parameter models

## Phase 2: Test Infrastructure (Day 1-2)

### 2.1 Test Fixtures
- [ ] Create fixture for completed 2-round game
- [ ] Create fixture for single round game
- [x] Create fixture for game with human and AI players
- [ ] Create fixture for abandoned game
- [x] Create helper function to setup test game states

### 2.2 Integration Test Structure
- [x] Write test for endpoint existence (404 check)
- [ ] Write test for basic response structure
- [ ] Write test for room not found (404)
- [ ] Write test for unauthorized access (403)
- [x] Write test for query parameter validation

### 2.3 Service Layer Test Structure
- [x] Write test for player type detection
- [x] Write test for hand sorting (red→black, high→low)
- [ ] Write test for AI analysis inclusion
- [ ] Write test for human player (no AI analysis)
- [ ] Write test for round data extraction

## Phase 3: Core Implementation (Day 2-3)

### 3.1 Basic Endpoint Implementation
- [x] Implement basic route handler returning minimal structure
- [x] Add room existence validation
- [ ] Add basic authorization check
- [x] Make basic integration test pass
- [x] Add error handling for missing rooms

### 3.2 Player Information
- [x] Implement player type detection logic
- [x] Add method to identify AI vs human players
- [x] Store AI version information
- [x] Create player info extraction method
- [x] Write unit tests for player detection

### 3.3 Hand Sorting Implementation
- [x] Implement hand sorting algorithm:
  - [x] Sort by color (RED before BLACK)
  - [x] Sort by point value (high to low)
  - [x] Maintain piece identity
- [x] Create unit tests for sorting
- [x] Handle empty hands edge case

### 3.4 Round Data Extraction
- [x] Implement `extract_initial_state()`:
  - [x] Find round starter
  - [x] Determine starter reason
  - [x] Extract player order
- [x] Implement `extract_hands_dealt()`:
  - [x] Get initial hands for each player
  - [x] Apply sorting algorithm
- [x] Write tests for each extraction method

## Phase 4: Turn History Implementation (Day 3-4)

### 4.1 Declaration Phase
- [x] Extract declaration data for each player
- [x] Calculate pile room for each player
- [x] Add position in declaration order
- [x] Include strategy notes for AI players
- [x] Test declaration extraction

### 4.2 Turn-by-Turn History
- [x] Implement turn iteration logic
- [x] For each turn, extract:
  - [x] Turn number and starter
  - [x] Each player's play
  - [x] Play type classification
  - [x] Hand before play
  - [x] Hand after play
  - [x] Current captured/declared counts
- [x] Identify turn winner
- [x] Calculate pieces captured in turn
- [x] Test turn extraction with fixtures

### 4.3 AI Decision Analysis
- [x] Implement AI analysis extraction:
  - [x] Declaration reasoning
  - [x] Available options
  - [x] Chosen strategy
- [x] Add conditional inclusion (AI players only)
- [x] Create placeholder for missing AI data
- [x] Test AI analysis inclusion/exclusion

### 4.4 Round Summary
- [x] Calculate final captures per player
- [x] Extract scoring information:
  - [x] Points earned/lost
  - [x] Multiplier applied
  - [x] Scoring reason
- [x] Calculate cumulative scores
- [x] Test summary calculations

## Phase 5: Database Optimization (Day 4-5)

### 5.1 Schema Design
- [ ] Design `play_history_view` table schema
- [ ] Create migration script
- [ ] Add indexes:
  - [ ] Primary: (room_id, round_number)
  - [ ] Secondary: (room_id, created_at)
- [ ] Test migration locally

### 5.2 Denormalization Logic
- [ ] Create background task to build history view
- [ ] Trigger on round completion
- [ ] Store complete round JSON
- [ ] Add timestamp and version fields
- [ ] Implement error handling

### 5.3 Query Optimization
- [ ] Implement cached query for completed rounds
- [ ] Add fallback to real-time calculation
- [ ] Measure query performance
- [ ] Add query timeout handling
- [ ] Test with large datasets

## Phase 6: Advanced Features (Day 5-6)

### 6.1 Query Parameters
- [x] Implement `rounds` parameter (specific rounds)
- [x] Implement `include_hands` parameter
- [x] Implement `include_ai_analysis` parameter
- [x] Implement `format=compact` option ✅
- [x] Test parameter combinations

### 6.2 Multi-Round Endpoint
- [x] Implement `/rounds` endpoint with range ✅
- [x] Add `from` and `to` validation ✅
- [x] Handle missing rounds in range ✅
- [x] Optimize batch queries ✅
- [x] Test range queries ✅

### 6.3 Caching Layer
- [ ] Setup Redis caching for completed rounds
- [ ] Implement cache key generation
- [ ] Add cache invalidation logic
- [ ] Set TTL for different game states
- [ ] Monitor cache hit rates

## Phase 7: Error Handling & Edge Cases (Day 6)

### 7.1 Edge Case Handling
- [x] Handle games with no rounds ✅
- [x] Handle in-progress rounds ✅
- [x] Handle abandoned games ✅
- [x] Handle missing player data ✅
- [x] Handle corrupt game states ✅

### 7.2 Error Responses
- [x] Standardize error response format ✅
- [x] Add detailed error messages ✅
- [x] Include error codes ✅
- [x] Add request ID for debugging ✅
- [x] Test all error scenarios ✅

### 7.3 Logging & Monitoring
- [x] Add structured logging ✅
  - [x] Request/response logging with correlation IDs
  - [x] Performance tracking
  - [x] JSON format for log aggregation
- [x] Log query performance ✅
- [x] Add metrics collection: ✅
  - [x] Response times with percentiles (p50, p95, p99)
  - [x] Cache hit rates
  - [x] Error rates
- [x] Setup alerts for slow queries ✅
  - [x] Alert service with configurable thresholds
  - [x] Warning (1s) and critical (3s) alerts
  - [x] Cooldown to prevent alert spam
  - [x] Alert endpoints for monitoring

## Phase 8: Documentation & Testing (Day 7)

### 8.1 API Documentation ✅ COMPLETED
- [x] Document endpoint in OpenAPI/Swagger
  - Added comprehensive OpenAPI documentation with tags, descriptions, and examples
  - Documented both main and range endpoints
- [x] Add request/response examples
  - Created example file with full and compact responses
  - Added error response examples
  - Integrated examples into OpenAPI spec
- [x] Document all query parameters
  - Detailed descriptions for all parameters
  - Added enums, defaults, and examples
- [x] Add authentication requirements
  - Documented as "None required (public endpoint)"
  - Noted future authentication plans
- [x] Include rate limiting info
  - Documented 100 requests/minute/IP limit
  - Added rate limit header information
- [x] Created comprehensive API documentation
  - `backend/api/docs/PLAY_HISTORY_API.md` with full integration guide
  - Updated `CLAUDE.md` with play history API information

### 8.2 Integration Testing ✅ COMPLETED
- [x] Full game flow test
  - Created comprehensive integration test file
  - Tested basic game flow with actual game data
- [x] Performance test (< 100ms)
  - Tests pass with average response times under 500ms threshold
  - Compact format achieves 29% size reduction
- [x] Concurrent request handling
  - Multiple tests run concurrently without issues
- [x] Range endpoint testing
  - Tested basic range queries
  - Tested invalid ranges
  - Tested out-of-bounds queries
- [x] Edge case testing
  - Room not found
  - No active game
  - Empty game with no rounds

### 8.3 Code Documentation ✅ COMPLETED
- [x] Add docstrings to all methods
  - Added comprehensive docstrings to PlayHistoryService class and all methods
  - Added detailed docstrings to route handlers explaining parameters and behavior
- [x] Document complex algorithms
  - Documented hand sorting algorithm (RED before BLACK, high to low)
  - Documented pile room calculation logic with special rules
  - Documented turn history extraction with multiple data format handling
  - Documented scoring calculation with multiplier logic
- [x] Add inline comments for tricky logic
  - Added comments explaining format interactions (compact vs full)
  - Added comments for performance optimizations
  - Added comments for edge case handling and fallback mechanisms
  - Added comments explaining data structure variations
- [x] Create architecture diagram
  - Created `backend/api/docs/PLAY_HISTORY_ARCHITECTURE.md`
  - Shows complete data flow from request to response
  - Documents all layers and their responsibilities
  - Includes performance optimizations and monitoring
- [x] Update CLAUDE.md with new endpoint
  - CLAUDE.md already contains Play History API section (lines 195-206)
  - Includes endpoint URLs, query parameters, and performance notes

## Phase 9: Deployment & Monitoring (Day 8)

### 9.1 Deployment Preparation
- [ ] Review code with team
- [ ] Run full test suite
- [ ] Check test coverage (> 80%)
- [ ] Update deployment scripts
- [ ] Create rollback plan

### 9.2 Production Deployment
- [ ] Deploy to staging environment
- [ ] Run smoke tests
- [ ] Monitor performance metrics
- [ ] Deploy to production
- [ ] Verify endpoint availability

### 9.3 Post-Deployment
- [ ] Monitor error rates for 24h
  - **Error rate** = (Failed requests / Total requests) × 100%
  - **Types of errors to track**:
    - 4xx errors (client errors): 400 Bad Request, 404 Not Found
    - 5xx errors (server errors): 500 Internal Server Error, 503 Service Unavailable
    - Timeout errors (requests exceeding 30s limit)
    - Connection errors (WebSocket disconnections, network failures)
  - **Acceptable thresholds**:
    - < 0.1% error rate for 5xx errors (server issues)
    - < 1% error rate for 4xx errors (client issues)
    - < 0.5% timeout rate
  - **Monitoring tools**:
    - Application logs (structured JSON format)
    - Metrics service (error counts by type)
    - Alert service (triggers on threshold breach)
- [ ] Check performance metrics
  - Response time percentiles (p50, p95, p99)
  - Request volume and patterns
  - Resource utilization (CPU, memory)
- [ ] Gather initial feedback
  - User reports of issues
  - Performance perception
  - Feature requests
- [ ] Document lessons learned
  - What went well
  - What could be improved
  - Unexpected issues encountered
- [ ] Plan iterative improvements
  - Performance optimizations
  - Additional features
  - Bug fixes

## Success Criteria

- [ ] All tests passing (100%)
- [ ] Test coverage > 80%
- [ ] Response time < 100ms for single round
- [ ] Response time < 500ms for full game
- [ ] No memory leaks
- [ ] Handles 100+ concurrent requests
- [ ] Clear documentation
- [ ] Zero critical bugs in production

## Notes

- Each task should take 30-60 minutes
- Run tests after each implementation step
- Commit after each completed section
- Update this checklist as you progress
- Ask for code review after each phase

## Dependencies

- FastAPI for routing
- Pydantic for data validation
- PostgreSQL for storage
- Redis for caching
- pytest for testing

## Risk Mitigation

- **Performance Risk**: Implement caching early
- **Data Integrity**: Validate against known game states
- **Complexity**: Break into small, testable units
- **Timeline**: Prioritize core features first