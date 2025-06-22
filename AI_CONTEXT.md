# AI_CONTEXT.md - Project Overview & Index
# ⚠️ Start Here Instead
For daily work → **Read AI_WORKING_DOC.md**  
This file is just the overview and historical record.

# Project Status
* ✅ **Game is playable** - All features work end-to-end
* ✅ **State machine foundation** - Declaration phase working perfectly
* ✅ **Preparation phase complete** - Full weak hand/redeal logic implemented
* ✅ **Turn phase complete** - Turn sequence, winner determination, bug fixed ✅ NEW
* 🔧 **Adding scoring phase** - Final state machine component

## Project Overview
**Working** multiplayer board game using FastAPI (backend) and PixiJS (frontend).
* Core gameplay complete: rooms, turns, scoring, bots
* Real-time updates via WebSocket
* Target: 2-3 concurrent games (MVP), scaling to 5-10
* **Current Focus**: Completing final state machine phase (Scoring)

**Current Status: Implementation Phase** - Building out complete state machine architecture.

# 🎯 Current Progress
**Week 1 ✅ COMPLETED** - State machine foundation
* ✅ State machine foundation built and tested
* ✅ Declaration phase working with full validation
* ✅ Action queue preventing race conditions

**Week 2 🔧 IN PROGRESS (75% COMPLETE)** - Complete all phases
* ✅ Task 2.1: Preparation State - COMPLETE
  - Weak hand detection
  - Redeal logic with play order changes
  - No redeal limit (can continue indefinitely)
  - Comprehensive test coverage (20 tests)
* ✅ Task 2.2: Turn State - COMPLETE WITH BUG FIX ✅ NEW
  - Turn sequence management and piece count validation
  - Winner determination by play value and order
  - Pile distribution and next turn assignment
  - Found and fixed responsibility boundary bug
  - Comprehensive test coverage (25 tests)
* 🔧 Task 2.3: Scoring State - NEXT
* 🔧 Task 2.4: Integration
* 🔧 Task 2.5: Full game flow test

## Document Map
### 📋 Game Design (in Project Knowledge)
* Rules - Complete game rules, piece values, play types, scoring formulas
* Game Flow - Preparation Phase - Deal, weak hands, redeal logic, starter determination ✅ IMPLEMENTED
* Game Flow - Declaration Phase - Declaration order, restrictions, validation ✅ IMPLEMENTED
* Game Flow - Turn Phase - Turn sequence, play requirements, winner determination ✅ IMPLEMENTED
* Game Flow - Scoring Phase - Score calculation, multipliers, win conditions

### 🔧 Development Planning
* AI_WORKING_DOC.md - Current sprint plan, daily workflow, implementation guide
* AI_CONTEXT.md - This file - project overview and index

### 🔧 Implementation Files
**✅ State Machine Architecture** (implemented):
* backend/engine/state_machine/core.py - Core enums and data classes
* backend/engine/state_machine/action_queue.py - Race condition prevention
* backend/engine/state_machine/base_state.py - Abstract state interface
* backend/engine/state_machine/game_state_machine.py - Central coordinator
* backend/engine/state_machine/states/declaration_state.py - Declaration phase logic ✅
* backend/engine/state_machine/states/preparation_state.py - Preparation phase logic ✅
* backend/engine/state_machine/states/turn_state.py - Turn phase logic ✅ NEW
* backend/tests/test_state_machine.py - Core state machine tests
* backend/tests/test_preparation_state.py - Basic preparation tests (14 tests)
* backend/tests/test_weak_hand_scenarios.py - Complex scenarios (6 tests)
* backend/tests/test_turn_state.py - Turn state tests (25 tests) ✅ NEW
* backend/run_tests.py - Quick test runner
* backend/run_preparation_tests.sh - Preparation phase test runner
* backend/run_turn_tests_fixed.py - Turn state test runner ✅ NEW
* backend/test_fix.py - Bug fix verification ✅ NEW

**Existing Code** (in project - to be integrated):
* README.md - Tech stack, installation, project structure
* backend/engine/rules.py - Game rule implementations (exists)
* backend/engine/ai.py - Bot AI logic (exists)
* backend/api/routes/routes.py - Current route handlers (to be refactored)
* backend/engine/bot_manager.py - Bot management (to be refactored)
* **Other backend files** - Various game engine components

## ✅ Proven Architecture Benefits
### Bugs That Are Now Impossible:
1. **Phase Violations**: ✅ States only exist during their phase
2. **Race Conditions**: ✅ Action queue processes sequentially
3. **Invalid Transitions**: ✅ Transition validation enforced
4. **Play Order Confusion**: ✅ Order changes tracked properly
5. **Responsibility Violations**: ✅ Turn state bug caught and fixed

### Development Benefits Achieved:
* ✅ **Easier Testing**: Each component tested independently
* ✅ **Clear Boundaries**: Phase logic centralized in state classes
* ✅ **Type Safety**: Enum-based actions and phases
* ✅ **Maintainable Code**: Adding features means extending state classes
* ✅ **Bug Prevention**: Test-driven development catches issues early

## Current Architecture Decisions
### ✅ Implemented Decisions
1. **State Pattern Architecture** - Each phase is a state class ✅ WORKING
2. **Action Queue System** - Sequential processing prevents races ✅ WORKING
3. **Transition Locks** - Atomic state changes ✅ WORKING
4. **Full Validation** - Actions validated before processing ✅ WORKING

### 🔧 In Progress Decisions
5. **Complete Phase Coverage** - All 4 phases in state machine (75% complete)
6. **Bot Integration** - Bots use state machine instead of manual checks
7. **Route Refactoring** - Replace scattered if/else with state machine calls

### Design Challenges ✅ SOLVED
1. **Phase Violations**: ✅ State pattern makes impossible
2. **Race Conditions**: ✅ Action queue solves
3. **State Synchronization**: ✅ States update game object correctly
4. **Complex Game Flow**: ✅ State transitions work automatically
5. **Play Order Changes**: ✅ Redeal starter changes tracked properly
6. **Responsibility Boundaries**: ✅ Turn state focused on single concern

## Implementation Status
### ✅ What's Working (NEW)
* **State Machine Foundation**: Core system, action queue, base state class
* **Declaration Phase**: Complete implementation with validation
* **Preparation Phase**: Full weak hand/redeal logic with play order changes
* **Turn Phase**: Complete turn sequence with winner determination ✅ NEW
* **Action Processing**: Queued, sequential, race-condition-free
* **Testing Suite**: Comprehensive tests with pytest
* **Integration**: Proven to work with existing game class
* **Bug Detection**: Test-driven development catches issues early

### ✅ What's Still Working (EXISTING)
* Complete game engine (rules, AI, scoring)
* Room system (create, join, host management)
* WebSocket real-time updates
* Bot players with AI
* Full game flow from lobby to scoring
* Frontend with PixiJS scenes

### 🔧 What's Next (Week 2 Continued)
* **Scoring State** - Score calculation, win conditions
* **Complete State Machine** - All 4 phases working together
* **Bot Integration** - Update bots to use state machine

## 📅 Current Sprint (See AI_WORKING_DOC.md)
Week 1: ✅ COMPLETED - Foundation architecture working  
Week 2: 🔧 75% COMPLETE - 3 of 4 phases implemented

# Key Principles (PROVEN)
* ✅ **Server Authority**: Server state is always correct
* ✅ **Fail Safe**: Invalid actions ignored, game continues
* ✅ **Single Source**: State machine is authoritative
* ✅ **Prevention Over Fixes**: Make bugs impossible, not fix them
* ✅ **Single Responsibility**: Each state handles one concern only

## Testing Strategy (IMPLEMENTED)
* ✅ Unit tests for each state class
* ✅ Integration tests for state machine
* ✅ Action queue race condition tests
* ✅ Invalid action rejection tests
* ✅ Complex scenario tests (weak hands, play order)
* ✅ Bug reproduction and fix verification tests
* 🔧 Bot integration tests (Week 2)
* 🔧 Full game flow tests (Week 2)

## Testing Commands (WORKING)
```bash
# Quick integration test
python backend/run_tests.py

# All preparation tests
./backend/run_preparation_tests.sh

# Turn state tests ✅ NEW
python backend/run_turn_tests_fixed.py
python backend/test_fix.py

# Full test suite
pytest backend/tests/ -v

# Individual test files
pytest backend/tests/test_state_machine.py -v
pytest backend/tests/test_preparation_state.py -v
pytest backend/tests/test_weak_hand_scenarios.py -v
pytest backend/tests/test_turn_state.py -v  # ✅ NEW
```

# Key Learning: Play Order Changes
**Critical Rule Discovered**: When a player accepts redeal and becomes starter, the play order rotates.
This affects:
- Subsequent weak hand asking order
- Declaration order
- Turn sequence
- All game mechanics

Example: A,B,C,D → B accepts redeal → New order: B,C,D,A

# Key Learning: Responsibility Boundaries ✅ NEW
**Critical Bug Found & Fixed**: Turn State was automatically starting next turns, erasing results.
**Root Cause**: Responsibility boundary violation - doing too much in one component.
**Fix**: Single Responsibility Principle - Turn State manages one turn only.
**Lesson**: Architecture prevents bugs better than fixing them.

# When to Read What
### For Game Mechanics
→ Read Rules and relevant Game Flow files
### For State Machine Implementation
→ Check backend/engine/state_machine/ files
### For Current Integration
→ Check backend/tests/ and backend/run_tests.py
### For Architecture Decisions
→ This file contains key decisions and their status

# Next Steps
1. ✅ ~~Design state machine based on game flow diagrams~~ COMPLETE
2. 🔧 Implement remaining phases (Scoring) - 75% complete
3. 🔧 Replace route handlers with state machine calls
4. 🔧 Update bot manager to use state machine
5. 🔧 Full game flow testing

**Last Updated**: After Task 2.2 completion with bug fix (Turn State)  
**Next Review**: After Scoring State implementation