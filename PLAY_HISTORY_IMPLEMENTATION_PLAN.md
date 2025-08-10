# Play History Endpoint Implementation Plan

## Overview
Implementation of `/api/rooms/{room_id}/play-history` endpoint to provide comprehensive game history for AI behavior analysis.

## Phase 1: Setup & Planning (Day 1)

### 1.1 Project Setup
- [ ] Create feature branch `feature/play-history-endpoint`
- [ ] Create `backend/api/routes/play_history.py` file
- [ ] Create `backend/services/play_history_service.py` file
- [ ] Create `backend/models/play_history.py` for data models
- [ ] Create test directory structure:
  - [ ] `backend/tests/api/test_play_history_api.py`
  - [ ] `backend/tests/services/test_play_history_service.py`
  - [ ] `backend/tests/fixtures/play_history_fixtures.py`

### 1.2 Data Model Design
- [ ] Define Pydantic models in `models/play_history.py`:
  - [ ] `PlayerInfo` model (id, name, type, ai_version)
  - [ ] `InitialState` model (starter info, player order)
  - [ ] `HandInfo` model (sorted pieces structure)
  - [ ] `DeclarationInfo` model (player declarations)
  - [ ] `PlayInfo` model (pieces played, hand states)
  - [ ] `TurnInfo` model (turn number, plays, winner)
  - [ ] `RoundSummary` model (captures, scoring)
  - [ ] `PlayHistoryResponse` model (complete response)

### 1.3 API Route Planning
- [ ] Define route signatures in `play_history.py`:
  - [ ] `GET /api/rooms/{room_id}/play-history`
  - [ ] `GET /api/rooms/{room_id}/play-history/round/{round_number}`
  - [ ] `GET /api/rooms/{room_id}/play-history/rounds`
- [ ] Add routes to main API router
- [ ] Define query parameter models

## Phase 2: Test Infrastructure (Day 1-2)

### 2.1 Test Fixtures
- [ ] Create fixture for completed 2-round game
- [ ] Create fixture for single round game
- [ ] Create fixture for game with human and AI players
- [ ] Create fixture for abandoned game
- [ ] Create helper function to setup test game states

### 2.2 Integration Test Structure
- [ ] Write test for endpoint existence (404 check)
- [ ] Write test for basic response structure
- [ ] Write test for room not found (404)
- [ ] Write test for unauthorized access (403)
- [ ] Write test for query parameter validation

### 2.3 Service Layer Test Structure
- [ ] Write test for player type detection
- [ ] Write test for hand sorting (red→black, high→low)
- [ ] Write test for AI analysis inclusion
- [ ] Write test for human player (no AI analysis)
- [ ] Write test for round data extraction

## Phase 3: Core Implementation (Day 2-3)

### 3.1 Basic Endpoint Implementation
- [ ] Implement basic route handler returning minimal structure
- [ ] Add room existence validation
- [ ] Add basic authorization check
- [ ] Make basic integration test pass
- [ ] Add error handling for missing rooms

### 3.2 Player Information
- [ ] Implement player type detection logic
- [ ] Add method to identify AI vs human players
- [ ] Store AI version information
- [ ] Create player info extraction method
- [ ] Write unit tests for player detection

### 3.3 Hand Sorting Implementation
- [ ] Implement hand sorting algorithm:
  - [ ] Sort by color (RED before BLACK)
  - [ ] Sort by point value (high to low)
  - [ ] Maintain piece identity
- [ ] Create unit tests for sorting
- [ ] Handle empty hands edge case

### 3.4 Round Data Extraction
- [ ] Implement `extract_initial_state()`:
  - [ ] Find round starter
  - [ ] Determine starter reason
  - [ ] Extract player order
- [ ] Implement `extract_hands_dealt()`:
  - [ ] Get initial hands for each player
  - [ ] Apply sorting algorithm
- [ ] Write tests for each extraction method

## Phase 4: Turn History Implementation (Day 3-4)

### 4.1 Declaration Phase
- [ ] Extract declaration data for each player
- [ ] Calculate pile room for each player
- [ ] Add position in declaration order
- [ ] Include strategy notes for AI players
- [ ] Test declaration extraction

### 4.2 Turn-by-Turn History
- [ ] Implement turn iteration logic
- [ ] For each turn, extract:
  - [ ] Turn number and starter
  - [ ] Each player's play
  - [ ] Play type classification
  - [ ] Hand before play
  - [ ] Hand after play
  - [ ] Current captured/declared counts
- [ ] Identify turn winner
- [ ] Calculate pieces captured in turn
- [ ] Test turn extraction with fixtures

### 4.3 AI Decision Analysis
- [ ] Implement AI analysis extraction:
  - [ ] Declaration reasoning
  - [ ] Available options
  - [ ] Chosen strategy
- [ ] Add conditional inclusion (AI players only)
- [ ] Create placeholder for missing AI data
- [ ] Test AI analysis inclusion/exclusion

### 4.4 Round Summary
- [ ] Calculate final captures per player
- [ ] Extract scoring information:
  - [ ] Points earned/lost
  - [ ] Multiplier applied
  - [ ] Scoring reason
- [ ] Calculate cumulative scores
- [ ] Test summary calculations

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
- [ ] Implement `rounds` parameter (specific rounds)
- [ ] Implement `include_hands` parameter
- [ ] Implement `include_ai_analysis` parameter
- [ ] Implement `format=compact` option
- [ ] Test parameter combinations

### 6.2 Multi-Round Endpoint
- [ ] Implement `/rounds` endpoint with range
- [ ] Add `from` and `to` validation
- [ ] Handle missing rounds in range
- [ ] Optimize batch queries
- [ ] Test range queries

### 6.3 Caching Layer
- [ ] Setup Redis caching for completed rounds
- [ ] Implement cache key generation
- [ ] Add cache invalidation logic
- [ ] Set TTL for different game states
- [ ] Monitor cache hit rates

## Phase 7: Error Handling & Edge Cases (Day 6)

### 7.1 Edge Case Handling
- [ ] Handle games with no rounds
- [ ] Handle in-progress rounds
- [ ] Handle abandoned games
- [ ] Handle missing player data
- [ ] Handle corrupt game states

### 7.2 Error Responses
- [ ] Standardize error response format
- [ ] Add detailed error messages
- [ ] Include error codes
- [ ] Add request ID for debugging
- [ ] Test all error scenarios

### 7.3 Logging & Monitoring
- [ ] Add structured logging
- [ ] Log query performance
- [ ] Add metrics collection:
  - [ ] Response times
  - [ ] Cache hit rates
  - [ ] Error rates
- [ ] Setup alerts for slow queries

## Phase 8: Documentation & Testing (Day 7)

### 8.1 API Documentation
- [ ] Document endpoint in OpenAPI/Swagger
- [ ] Add request/response examples
- [ ] Document all query parameters
- [ ] Add authentication requirements
- [ ] Include rate limiting info

### 8.2 Integration Testing
- [ ] Full game flow test
- [ ] Performance test (< 100ms)
- [ ] Concurrent request handling
- [ ] Load testing with 100+ rounds
- [ ] Memory usage validation

### 8.3 Code Documentation
- [ ] Add docstrings to all methods
- [ ] Document complex algorithms
- [ ] Add inline comments for tricky logic
- [ ] Create architecture diagram
- [ ] Update CLAUDE.md with new endpoint

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
- [ ] Check performance metrics
- [ ] Gather initial feedback
- [ ] Document lessons learned
- [ ] Plan iterative improvements

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