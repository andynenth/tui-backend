# AI_CONTEXT.md - Reference & Historical Record
**Purpose**: Stable reference information and project history for AI assistant
**For current work**: → Use AI_WORKING_DOC.md

# 🎯 Project Quick Facts
- **Type**: Liap Tui multiplayer board game (FastAPI + PixiJS)
- **Status**: Implementation Phase - State machine architecture 75% complete
- **Current Sprint**: Week 2 - Complete all 4 phase states
- **Philosophy**: Prevention by design - make bugs impossible

# 📊 Overall Progress Tracking
- **Week 1**: ✅ COMPLETE - State machine foundation working
- **Week 2**: 🔧 75% COMPLETE - 3 of 4 states implemented (Prep, Declaration, Turn)
- **Week 3-4**: 🔧 PLANNED - Integration & refactoring

# 🏗️ Architecture Decisions (PROVEN)
## ✅ Working Design Patterns
1. **State Pattern**: Each game phase = separate state class
2. **Action Queue**: Sequential processing prevents race conditions  
3. **Single Responsibility**: Each state handles only its phase logic
4. **Test-Driven**: Comprehensive tests before integration
5. **Phase Validation**: Invalid actions impossible by design

## 🔥 Critical Bugs Prevented
- **Phase Violations**: States only exist during valid phases
- **Race Conditions**: Action queue processes sequentially
- **Responsibility Boundaries**: Turn state bug caught - each state handles one concern only
- **Play Order Confusion**: Redeal changes tracked properly

# 📁 File & Directory Map
## State Machine Core
- `backend/engine/state_machine/core.py` - Enums, data classes
- `backend/engine/state_machine/base_state.py` - Abstract state interface
- `backend/engine/state_machine/game_state_machine.py` - Central coordinator
- `backend/engine/state_machine/action_queue.py` - Race condition prevention

## Implemented States (Examples)
- `backend/engine/state_machine/states/preparation_state.py` ✅ COMPLETE
- `backend/engine/state_machine/states/declaration_state.py` ✅ COMPLETE  
- `backend/engine/state_machine/states/turn_state.py` ✅ COMPLETE

## Testing
- `backend/tests/test_*_state.py` - Individual state tests
- `backend/run_*_tests.py` - Quick test runners
- `backend/test_fix.py` - Bug fix verification

## Game Design Reference (Project Knowledge)
- `Rules` - Complete game mechanics, piece values, scoring
- `Game Flow - *Phase` - Detailed phase requirements and validation

## Legacy Code (To Integrate Later)
- `backend/engine/rules.py` - Game rule implementations
- `backend/api/routes/routes.py` - Current handlers (Week 3 refactor)
- `backend/engine/bot_manager.py` - Bot logic (Week 3 integration)

# 🧠 Key Learning Points
## Play Order Management
**Rule**: When player accepts redeal → becomes starter AND play order rotates
**Example**: A,B,C,D → B accepts → New order: B,C,D,A
**Affects**: All subsequent phases (declaration, turns, etc.)

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

# 🎮 Existing Working Systems
- Complete game engine with rules, AI, scoring
- Room system (create, join, host management)  
- WebSocket real-time updates
- Bot players with AI decision making
- Frontend with PixiJS scenes and UI
- Full game flow from lobby to scoring (legacy)

# 📅 Detailed Implementation Roadmap

## Week 3-4: Integration & Refactoring
### Phase Logic Extraction
- Extract phase logic from `routes.py` → State classes
- Extract bot logic from `bot_manager.py` → State classes  
- Replace all `if phase ==` checks → State pattern
- Update WebSocket handlers to use state machine
- Add comprehensive integration tests
- Performance test with bots

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
- End-to-end game flow testing
- Multi-game concurrent testing (5-10 games target)
- Bot vs human testing scenarios
- Network disconnection testing
- Performance benchmarking

## 🏗️ Comprehensive Architecture Framework

### Core Problem Analysis
**Primary Challenges:**
- Phase Violations: Bots declaring during redeal phase
- Race Conditions: Multiple actions happening simultaneously  
- State Synchronization: Keeping all clients in sync
- Complex Game Flow: Multiple phases with specific rules

### Architectural Philosophy
**Guiding Principles:**
- **Single Source of Truth**: Server owns all game state
- **Strict Phase Boundaries**: No action crosses phase lines
- **Event-Driven Design**: Everything is a reaction to events
- **Fail-Safe Defaults**: When in doubt, reject the action

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

#### 3. Conflict Resolution: Phase-Specific Rules
**Timer System:**
- Decision Timer: Time to make game decisions (10-15s)
- Disconnection Timer: Time to reconnect before bot replacement (30s)

**Key Resolution Patterns:**
- Redeal: Process by player order, ALL weak players must decide
- Declaration: Strict turn order, auto-select on timeout
- Turn: Starter processed first, others auto-matched on timeout
- Priority: Server authority, deterministic outcomes

#### 4. State Synchronization: Delta/Patch Updates
**Delta Structure:**
```javascript
{
  type: "state_delta",
  sequence: 1234,
  changes: [{
    path: "players.player1.hand",
    operation: "remove", 
    value: [2, 5]
  }]
}
```
**Benefits**: 90% bandwidth reduction, smooth updates, audit trail

#### 5. Error Handling: Fail Fast and Notify
**Strategy**: Detect → Log → Stop → Notify → Monitor
**Categories**: Validation, State, Network, System errors
**Recovery Boundaries**: Clear what we do/don't attempt to recover

### Scalability Requirements
- **Target**: 5-10 concurrent games (small scale launch)
- **Latency**: 200-1000ms acceptable
- **Reliability**: 30s reconnection window, bot replacement
- **Architecture**: Fat Server/Thin Client, data-driven rules

### Risk Mitigation Strategies
- **Phase Violation Prevention**: Hard boundaries, explicit protocols
- **Race Condition Elimination**: Sequential processing, proper locking
- **State Consistency**: Regular snapshots, reconciliation protocols

### Implementation Components
- **Game Flow Controller**: Orchestrates lifecycle, manages transitions
- **Phase State Machine**: Enforces transitions, stores phase data
- **Action Processing System**: Queues, validates, processes in order
- **Bot Behavior System**: Phase-aware, scheduled actions
- **Client Sync Layer**: WebSocket management, real-time updates

# 🚫 Out of Scope
- Tournaments, spectator mode, ranking system
- Payment/monetization features  
- Complex social features
- Fixing existing legacy bugs (we're preventing them with architecture)

**Last Updated**: After Turn State completion with bug fix
**Next Major Update**: After Scoring State implementation
**Architecture Framework**: Comprehensive 5-aspect system defined