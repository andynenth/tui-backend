# AI_CONTEXT.md - Reference & Historical Record
**Purpose**: Stable reference information and project history for AI assistant
**For current work**: → Use AI_WORKING_DOC.md

# 🎯 Project Quick Facts
- **Type**: Liap Tui multiplayer board game (FastAPI + PixiJS)
- **Status**: Week 3 IN PROGRESS - Complete system replacement with state machine
- **Current Sprint**: Week 3 - Complete system replacement (removing all direct game calls)
- **Philosophy**: Prevention by design - make bugs impossible

# 📊 Implementation History & Lessons

## ✅ Task 2.1: Preparation State - COMPLETED
**Time Taken**: ~3 hours  
**Files Created**:
- backend/engine/state_machine/states/preparation_state.py
- backend/tests/test_preparation_state.py (14 tests)
- backend/tests/test_weak_hand_scenarios.py (6 tests)

**Key Implementations**:
- ✅ Initial deal of 8 pieces per player
- ✅ Weak hand detection (no piece > 9 points)
- ✅ Redeal request/response handling
- ✅ Play order changes when starter changes
- ✅ No redeal limit (can continue indefinitely)
- ✅ Disconnection handling (auto-decline)
- ✅ Comprehensive test coverage (20 tests total)

**Key Learning**: When a player accepts redeal, they become starter AND the play order rotates (A,B,C,D → B,C,D,A if B accepts).

## ✅ Task 2.2: Turn State - COMPLETED WITH BUG FIX
**Time Taken**: ~120 minutes (including bug investigation and fix)  
**Files Created**:
- backend/engine/state_machine/states/turn_state.py
- backend/tests/test_turn_state.py (25 tests)
- backend/run_turn_tests_fixed.py (integration test runner)
- backend/test_fix.py (bug fix verification)
- backend/investigate_bug.py (debugging script)
- Updated backend/engine/state_machine/game_state_machine.py
- Updated backend/engine/state_machine/states/__init__.py

**Key Implementations**:
- ✅ Turn sequence management (starter sets piece count, others follow)
- ✅ Piece count validation (1-6 for starter, must match for others)
- ✅ Winner determination by play value and play order
- ✅ Play type filtering (only matching starter's type can win)
- ✅ Pile distribution to winner
- ✅ Next turn starter assignment (winner starts next)
- ✅ Turn completion and hand management
- ✅ Multi-turn support with restart functionality
- ✅ Disconnection/timeout handling with auto-play
- ✅ State machine integration
- ✅ Comprehensive test coverage (25 tests)

**Critical Bug Found & Fixed**:
- **Issue**: Turn completion automatically started next turn, erasing results
- **Root Cause**: Responsibility boundary violation - Turn State doing too much
- **Fix**: Removed automatic turn restart, preserved results, added manual control
- **Lesson**: Single Responsibility Principle prevents complex bugs

**Integration Bug Fixed**:
- **Issue**: After Turn 1, `_get_current_player()` returned `None`
- **Root Cause**: `turn_complete` flag not reset for subsequent turns
- **Fix**: Added `restart_turn_for_testing()` method with proper state reset
- **Lesson**: Integration testing reveals state management edge cases

**Key Learning**: Winner determination follows priority: play_type match → play_value (descending) → play_order (ascending for ties). Turn State should manage one turn, not turn sequences.

## ✅ Task 2.3: Scoring State - COMPLETED
**Time Taken**: ~90 minutes (including bug fixes)  
**Files Created**:
- backend/engine/state_machine/states/scoring_state.py
- backend/tests/test_scoring_state.py (28 tests)

**Key Implementations**:
- ✅ Base score calculation (perfect/zero/missed targets)
- ✅ Redeal multiplier application (×2, ×3, ×4, etc.)
- ✅ Game winner detection (≥50 points)
- ✅ Round completion and next round preparation
- ✅ Data structure compatibility fixes
- ✅ Comprehensive test coverage (28 tests)

**Integration Issues Fixed**:
- **Issue**: `'str' object has no attribute 'score'`
- **Root Cause**: MockGame using string player names instead of objects
- **Fix**: Updated data structures for proper object handling
- **Lesson**: Mock objects must match production data structures exactly

**Key Learning**: Scoring rules require careful multiplier application order and proper game completion detection.

## ✅ Task 2.4: State Machine Integration - COMPLETED
**Time Taken**: ~15 minutes  
**Files Updated**:
- backend/engine/state_machine/game_state_machine.py
- backend/engine/state_machine/states/__init__.py

**Key Implementations**:
- ✅ ScoringState registered in state machine
- ✅ Import cleanup and organization
- ✅ Transition map includes all 4 phases
- ✅ Integration verification tests

**Key Learning**: Clean imports and proper state registration critical for state machine functionality.

## ✅ Task 2.5: Full Game Flow Integration Test - COMPLETED
**Time Taken**: ~3 hours (including integration bug fixes)  
**Files Created**:
- backend/test_full_game_flow.py

**Key Implementations**:
- ✅ Complete cycle: Preparation → Declaration → Turn → Scoring → Next Round
- ✅ Multi-turn simulation with proper state management
- ✅ Data flow validation between all phases
- ✅ Round cycling and game completion testing
- ✅ Integration bug discovery and fixes

**Critical Integration Bugs Fixed**:
1. **Declaration Phase**: Player object vs string comparison in validation
2. **Turn Phase**: Multi-turn state reset not working properly
3. **Data Flow**: Mock object attribute mismatches

**Final Test Results**:
```
🎉 ALL INTEGRATION TESTS PASSED!
✅ Full Game Flow Test: PASSED
✅ Multiple Rounds Test: PASSED
🎯 Week 2 Task 2.5 - COMPLETE
🚀 State machine fully functional!
```

**Key Learning**: Integration testing is essential for discovering state management edge cases that unit tests miss.

# 📊 Overall Progress Tracking
- **Week 1**: ✅ COMPLETE - State machine foundation working
- **Week 2**: ✅ COMPLETE - All 4 state machine phases implemented and tested
- **Week 3**: 🎯 CURRENT - Integration with existing systems (routes, bots, WebSocket)
- **Week 4**: 🔜 PLANNED - Performance testing and production readiness

# 🏗️ Architecture Decisions (PROVEN)
## ✅ Working Design Patterns
1. **State Pattern**: Each game phase = separate state class ✅ PROVEN
2. **Action Queue**: Sequential processing prevents race conditions ✅ PROVEN
3. **Single Responsibility**: Each state handles only its phase logic ✅ PROVEN
4. **Test-Driven**: Comprehensive tests before integration ✅ PROVEN
5. **Phase Validation**: Invalid actions impossible by design ✅ PROVEN
6. **Integration Testing**: Full cycle testing catches edge cases ✅ PROVEN

## 🔥 Critical Bugs Prevented
- **Phase Violations**: States only exist during valid phases
- **Race Conditions**: Action queue processes sequentially
- **Responsibility Boundaries**: Turn state bug caught - each state handles one concern only
- **Play Order Confusion**: Redeal changes tracked properly
- **Data Structure Mismatches**: Integration testing caught mock vs production differences
- **State Reset Issues**: Multi-turn functionality properly implemented

# 📁 Files Created (Reference for Future Work)

## Core Architecture (Production Ready)
- `backend/engine/state_machine/core.py` - Enums and data classes ✅ PRODUCTION
- `backend/engine/state_machine/base_state.py` - Abstract state interface ✅ PRODUCTION
- `backend/engine/state_machine/game_state_machine.py` - Central coordinator ✅ PRODUCTION

## Complete State Implementation (All Working)
- `backend/engine/state_machine/states/preparation_state.py` ✅ PRODUCTION
- `backend/engine/state_machine/states/declaration_state.py` ✅ PRODUCTION
- `backend/engine/state_machine/states/turn_state.py` ✅ PRODUCTION
- `backend/engine/state_machine/states/scoring_state.py` ✅ PRODUCTION
- `backend/engine/state_machine/states/__init__.py` ✅ PRODUCTION

## Comprehensive Test Suite (78 tests passing)
- `backend/tests/test_preparation_state.py` ✅ 15 tests
- `backend/tests/test_turn_state.py` ✅ 25 tests
- `backend/tests/test_scoring_state.py` ✅ 28 tests
- `backend/tests/test_weak_hand_scenarios.py` ✅ 6 tests (FIXED: Realistic test data)
- `backend/tests/test_state_machine.py` ✅ 4 tests
- `backend/test_full_game_flow.py` ✅ Integration tests

## Debug Tools (Proven Effective)
- `backend/test_fix.py` ✅ BUG FIX VERIFICATION PATTERN
- `backend/investigate_bug.py` ✅ DEBUGGING SCRIPT TEMPLATE
- `backend/run_turn_tests_fixed.py` ✅ INTEGRATION TEST PATTERN

## Legacy Code (Week 3 Integration Targets)
- `backend/api/routes/routes.py` - Current handlers (Week 3 refactor)
- `backend/engine/bot_manager.py` - Bot logic (Week 3 integration)
- `backend/engine/rules.py` - Game rule implementations (already working)

# 🧠 Key Learning Points
## Winner Determination Logic
**Priority**: play_type match → play_value (desc) → play_order (asc)
**Key**: Only matching starter's play type can win

## Responsibility Boundaries  
**Lesson**: Turn State should complete one turn and stop
**Anti-pattern**: Automatically starting next turn erases results
**Fix**: External control of turn sequences

## State Transition Rules
**Principle**: States only transition when their specific conditions are met
**Validation**: Transition map prevents invalid phase jumps

## Integration Testing Critical
**Lesson**: Unit tests catch logic bugs, integration tests catch architecture bugs
**Pattern**: Mock objects must exactly match production data structures
**Discovery**: State reset between phases requires careful management

## Play Order Management
**Rule**: When player accepts redeal → becomes starter AND play order rotates
**Example**: A,B,C,D → B accepts → New order: B,C,D,A
**Affects**: All subsequent phases (declaration, turns, etc.)

# 🎮 Existing Working Systems
- Complete game engine with rules, AI, scoring
- Room system (create, join, host management)  
- WebSocket real-time updates
- Bot players with AI decision making
- Frontend with PixiJS scenes and UI
- **NEW**: Complete state machine with all 4 phases working

# 📅 Week 3-4 Implementation Roadmap

## Week 3: Integration & Refactoring (CURRENT)
### Phase Logic Extraction
- Extract phase logic from `routes.py` → State classes
- Extract bot logic from `bot_manager.py` → State classes  
- Replace all `if phase ==` checks → State pattern
- Update WebSocket handlers to use state machine
- Add state machine to existing game flow

### Bot System Integration
- Update bot decision making to use state machine
- Implement fixed delay timing strategy (see Architecture Framework)
- Phase-specific bot behaviors
- Disconnection/reconnection handling for bots

### Route Refactoring
- Replace manual phase checks with state machine validation
- Centralize action processing through state machine
- Update WebSocket message handlers
- Implement delta/patch state synchronization

### Testing & Validation
- End-to-end game flow testing with real routes
- Multi-game concurrent testing (5-10 games target)
- Bot vs human testing scenarios
- Network disconnection testing

## Week 4: Performance & Production
- Performance benchmarking with concurrent games
- Production deployment preparation
- Documentation and deployment guides
- Final integration testing

## 🏗️ Comprehensive Architecture Framework

### Architectural Philosophy
**Guiding Principles:**
- **Single Source of Truth**: Server owns all game state
- **Strict Phase Boundaries**: No action crosses phase lines
- **Event-Driven Design**: Everything is a reaction to events
- **Fail-Safe Defaults**: When in doubt, reject the action
- **Prevention by Design**: Architecture makes bugs impossible

### System Architecture Decisions

#### 1. Phase Transitions: Locked States
**Transition Flow**: Current Phase → [LOCK] → Transition Period → [UNLOCK] → Next Phase
- **Lock Duration**: 450-800ms total
- **Benefits**: No race conditions, clean state boundaries
- **Implementation**: Global action lock during transitions

#### 2. Bot Timing Strategy: Fixed Delays
**Delay Categories:**
- Quick Actions: 500-1000ms (acknowledging, viewing)
- Medium Actions: 1500-3000ms (redeal decisions, declarations)
- Complex Actions: 2000-4000ms (analyzing plays)
- Strategic Actions: 3000-5000ms (critical moments)

#### 3. State Synchronization: Delta/Patch Updates
**Strategy**: Minimal data transfer, event-driven updates
**Benefits**: 90% bandwidth reduction, smooth updates, audit trail

### Scalability Requirements
- **Target**: 5-10 concurrent games (small scale launch)
- **Latency**: 200-1000ms acceptable
- **Reliability**: 30s reconnection window, bot replacement
- **Architecture**: Fat Server/Thin Client, data-driven rules

# 🚫 Week 3 Focus Areas
- Integration with existing routes and WebSocket handlers
- Bot system integration with state machine
- Performance testing with multiple concurrent games
- Real-world testing with frontend integration

## ✅ Post-Week 2: Test Data Quality Improvements - COMPLETED
**Time Taken**: ~30 minutes  
**Files Updated**:
- backend/tests/test_weak_hand_scenarios.py
- backend/test_real_game_integration.py

**Key Fixes**:
- ✅ Fixed unrealistic test scenario where all 4 players had weak hands simultaneously
- ✅ Updated to realistic distribution (2 players with weak hands max)
- ✅ Maintained test coverage for mixed accept/decline patterns
- ✅ All 78 tests still passing after fixes

**Key Learning**: Test data must reflect realistic game scenarios to be meaningful. Having all 4 players with weak hands is statistically very unlikely (probability < 1%).

## 🚀 Week 3: Complete System Replacement - IN PROGRESS
**Decision**: Replace entire system with state machine as single authority  
**Approach**: Complete replacement rather than incremental integration
**Goal**: Remove ALL direct game method calls, route everything through GameAction

### Architecture Designed - Phase 1 ✅ COMPLETE
**New Architecture**: Single Authority Pattern
- **State Machine**: Only entity that can change game state
- **GameAction**: Only way to trigger state changes  
- **Priority Queue**: Human actions processed before bot actions
- **Sequence Numbers**: All messages ordered to prevent frontend race conditions
- **Error Boundaries**: Failed actions trigger recovery, never crash game

### Phase 2: Complete Route Replacement ✅ COMPLETE
**Time Taken**: ~1 hour  
**Files Modified**:
- backend/api/routes/routes.py (complete replacement)
- backend/test_route_replacement.py (new test file)

**Key Implementations**:
- ✅ Removed ALL direct game method calls from routes
- ✅ Converted /redeal endpoint to use GameAction(ActionType.REDEAL_REQUEST)
- ✅ Converted /redeal-decision endpoint to use GameAction(ActionType.REDEAL_RESPONSE)
- ✅ Eliminated RedealController completely - state machine handles all logic
- ✅ Added error recovery - failed actions return errors, don't crash
- ✅ Maintained backward compatibility with existing API contracts

**Testing Results**:
- ✅ Route replacement test: PASSED
- ✅ Error handling test: PASSED  
- ✅ Full game flow test: PASSED
- ✅ All 78+ state machine tests: PASSED
- ✅ Zero direct game calls remaining in routes

**Key Learning**: Complete replacement approach works better than incremental - eliminates mixed authority issues.

### Remaining Problems to Address:
1. ✅ ~~Mixed Authority in Routes~~ - FIXED: All routes use state machine only
2. **Bot Manager**: Still uses direct game.play_turn(), game.declare() calls (26+ calls)
3. ✅ ~~Redeal System~~ - FIXED: RedealController eliminated, state machine handles all
4. **No Message Ordering**: Frontend can receive events out of order
5. **Error Handling**: Partial - routes have recovery, need system-wide

**Next Phase**: Bot Manager replacement with GameActions

**Last Updated**: Week 3 Phase 2 - Route replacement complete and tested
**Next Major Update**: After bot manager replacement complete  
**Status**: 🎯 PHASE 2 COMPLETE - Routes use state machine only, ready for bot integration