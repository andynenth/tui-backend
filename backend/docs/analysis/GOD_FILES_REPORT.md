# God Files Analysis Report 🚨

## Summary
Found multiple "god files" that violate Single Responsibility Principle and need refactoring.

## Critical God Files

### 1. 🔴 **api/routes/ws.py** (1,847 lines)
**Severity: CRITICAL**

#### Issues:
- Massive file handling **21+ different WebSocket events** in a single handler
- Mixed responsibilities across multiple domains
- Single massive function with 21 elif branches
- High coupling with 12+ imports

#### Event Types Handled:
- Connection: ping, ack, client_ready, sync
- Room: create_room, join_room, leave_room, get_rooms, request_room_list
- Game: start_game, play, declare, accept_redeal, decline_redeal
- Bot: add_bot, remove_player
- Lobby: multiple lobby operations
- Chat: chat messages
- Plus more...

#### Recommended Refactoring:
```
api/routes/websocket/
├── ws_router.py (main router, delegates to handlers)
├── handlers/
│   ├── connection_handler.py (ping, ack, sync, client_ready)
│   ├── room_handler.py (create, join, leave, list rooms)
│   ├── game_handler.py (start, play, declare, redeal)
│   ├── bot_handler.py (add_bot, remove_player)
│   ├── lobby_handler.py (lobby operations)
│   └── chat_handler.py (chat messages)
└── utils/
    ├── broadcast.py
    └── disconnect.py
```

---

### 2. 🟠 **engine/bot_manager.py** (1,141 lines)
**Severity: HIGH**

#### Issues:
- Two massive classes: BotManager + GameBotHandler
- 30+ methods across both classes
- Multiple responsibilities: AI, tracking, deduplication, events
- Complex internal state with multiple tracking dictionaries

#### Responsibilities Mixed:
- Bot registration/unregistration
- AI decision making
- Action deduplication
- Phase tracking
- Turn management
- Event processing
- State tracking

#### Recommended Refactoring:
```
engine/bot/
├── bot_manager.py (singleton registry only)
├── bot_handler.py (game bot coordination)
├── strategy/
│   ├── bot_strategy.py (AI decisions)
│   ├── preparation_strategy.py
│   ├── declaration_strategy.py
│   └── turn_strategy.py
├── tracking/
│   ├── action_tracker.py (deduplication)
│   └── state_tracker.py (phase/turn tracking)
└── event_processor.py (event handling)
```

---

### 3. 🟡 **engine/state_machine/states/turn_state.py** (987 lines)
**Severity: MEDIUM**

#### Issues:
- Single class with 30+ methods
- Handles validation + processing + transitions
- Complex turn resolution logic mixed with state management

#### Recommended Refactoring:
```
engine/state_machine/states/turn/
├── turn_state.py (core state class)
├── turn_validator.py (validation logic)
├── turn_processor.py (processing logic)
├── turn_resolver.py (resolution logic)
└── turn_transitions.py (state transitions)
```

---

### 4. 🟡 **api/routes/routes.py** (930 lines)
**Severity: MEDIUM**

#### Issues:
- 17 top-level functions
- 14 router endpoints
- Mixes unrelated concerns: health, debug, recovery, events, stats

#### Mixed Endpoints:
- Health checks (3 endpoints)
- Debug endpoints (4 endpoints)
- Recovery endpoints (3 endpoints)
- Event store endpoints (2 endpoints)
- System stats (2 endpoints)

#### Recommended Refactoring:
```
api/routes/
├── health_routes.py
├── debug_routes.py
├── recovery_routes.py
├── event_store_routes.py
└── system_routes.py
```

---

### 5. 🟡 **engine/game.py** (791 lines)
**Severity: MEDIUM**

#### Issues:
- Single Game class with 26 methods
- Handles multiple concerns: state, rounds, players, pieces, scoring

#### Recommended Refactoring:
```
engine/game/
├── game.py (orchestration only)
├── round_manager.py (round lifecycle)
├── piece_manager.py (piece dealing)
├── scoring_manager.py (score calculation)
└── game_state.py (state queries)
```

---

## Statistics

### File Size Distribution:
- **> 1000 lines:** 2 files (ws.py, bot_manager.py)
- **> 700 lines:** 10 files
- **> 500 lines:** 20 files

### Top Offenders by Lines:
1. ws.py: 1,847 lines
2. bot_manager.py: 1,141 lines
3. turn_state.py: 987 lines
4. routes.py: 930 lines
5. game.py: 791 lines

### Coupling Indicators:
- ws.py: 12-13 imports
- routes.py: 13 imports
- bot_manager.py: 10+ imports

## Impact Analysis

### Current Problems:
- **Maintainability:** Hard to find specific functionality
- **Testing:** Difficult to unit test mixed responsibilities
- **Debugging:** Complex to trace issues through large files
- **Team Work:** Multiple developers can't work on different features
- **Performance:** Loading large files for small functionality

### Benefits of Refactoring:
- ✅ Easier to understand and maintain
- ✅ Better testability (focused unit tests)
- ✅ Improved debugging (clear boundaries)
- ✅ Parallel development (team can work on different files)
- ✅ Better performance (smaller modules)

## Refactoring Priority

### Phase 1: Critical (Do First)
1. **ws.py** - Split into handler modules (1,847 → ~200 lines each)

### Phase 2: High Priority
2. **bot_manager.py** - Separate AI from management (1,141 → ~200 lines each)
3. **routes.py** - Split by domain (930 → ~200 lines each)

### Phase 3: Medium Priority
4. **turn_state.py** - Extract validation/processing (987 → ~250 lines each)
5. **game.py** - Separate concerns (791 → ~200 lines each)

## Recommended Action Plan

### Quick Win (1-2 hours):
- Split `routes.py` into domain-specific route files
- Easy mechanical refactor with clear boundaries

### High Impact (4-6 hours):
- Refactor `ws.py` into handler modules
- Will dramatically improve code organization

### Strategic (8-12 hours):
- Restructure `bot_manager.py` with proper separation
- Will improve bot behavior debugging and testing

## Code Smell Summary

### Violations Found:
- ❌ Single Responsibility Principle (all 5 files)
- ❌ Open/Closed Principle (ws.py with 21 elif branches)
- ❌ Interface Segregation (bot_manager.py with 30+ methods)
- ❌ Don't Repeat Yourself (similar patterns across files)

### Metrics:
- **Average god file size:** 939 lines
- **Total lines in god files:** 4,696 lines
- **Percentage of codebase:** ~15% in just 5 files

---

*Generated: December 2024*
*Recommendation: Start with ws.py refactoring for maximum impact*