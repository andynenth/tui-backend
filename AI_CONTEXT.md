# Updated AI_CONTEXT.md
# AI_CONTEXT.md - Project Overview & Index
# ⚠️ Start Here Instead
For daily work → **Read AI_WORKING_DOC.md**This file is just the overview and historical record.
# Project Status
* ✅ **Game is playable** - All features work end-to-end
* ✅ **State machine foundation** - Declaration phase working perfectly
* 🔧 **Adding remaining phases** - Preparation, Turn, Scoring states

⠀Project Overview
**Working** multiplayer board game using FastAPI (backend) and PixiJS (frontend).
* Core gameplay complete: rooms, turns, scoring, bots
* Real-time updates via WebSocket
* Target: 2-3 concurrent games (MVP), scaling to 5-10
* **Current Focus**: Implementing remaining phases in state machine

⠀**Current Status: Implementation Phase** - Building out complete state machine architecture.
# 🎯 Current Task
**Week 1 ✅ COMPLETED - Week 2 in progress**
* ✅ State machine foundation built and tested
* ✅ Declaration phase working with full validation
* ✅ Action queue preventing race conditions
* 🔧 Now implementing: Preparation, Turn, and Scoring phases
* See **AI_WORKING_DOC.md** for detailed Week 2 tasks

⠀Document Map
### 📋 Game Design (in Project Knowledge)
* Rules - Complete game rules, piece values, play types, scoring formulas
* Game Flow - Preparation Phase - Deal, weak hands, redeal logic, starter determination
* Game Flow - Declaration Phase - Declaration order, restrictions, validation ✅ IMPLEMENTED
* Game Flow - Turn Phase - Turn sequence, play requirements, winner determination
* Game Flow - Scoring Phase - Score calculation, multipliers, win conditions

⠀🔧 Development Planning
* AI_WORKING_DOC.md - Current sprint plan, daily workflow, implementation guide
* AI_CONTEXT.md - This file - project overview and index

⠀🔧 Implementation Files
**✅ NEW State Machine Architecture** (implemented):
* backend/engine/state_machine/core.py - Core enums and data classes
* backend/engine/state_machine/action_queue.py - Race condition prevention
* backend/engine/state_machine/base_state.py - Abstract state interface
* backend/engine/state_machine/game_state_machine.py - Central coordinator
* backend/engine/state_machine/states/declaration_state.py - Declaration phase logic ✅
* backend/tests/test_state_machine.py - Comprehensive test suite
* backend/tests/test_integration.py - Integration tests
* backend/run_tests.py - Quick test runner

⠀**Existing Code** (in project - to be integrated):
* README.md - Tech stack, installation, project structure
* backend/engine/rules.py - Game rule implementations (exists)
* backend/engine/ai.py - Bot AI logic (exists)
* backend/api/routes/routes.py - Current route handlers (to be refactored)
* backend/engine/bot_manager.py - Bot management (to be refactored)
* **Other backend files** - Various game engine components

⠀✅ Proven Architecture Benefits
### Bugs That Are Now Impossible:
**1** **Phase Violations**: ✅ Declaration state only exists during declaration phase
**2** **Race Conditions**: ✅ Action queue processes sequentially
**3** **Duplicate Phase Checks**: ✅ Single source of truth in state machine
**4** **Invalid Transitions**: ✅ Transition validation enforced

⠀Development Benefits Achieved:
* ✅ **Easier Testing**: Each component tested independently
* ✅ **Clear Boundaries**: Declaration logic centralized in one state
* ✅ **Type Safety**: Enum-based actions and phases
* ✅ **Maintainable Code**: Adding features means extending state classes

⠀Current Architecture Decisions
### ✅ Implemented Decisions
**1. State Pattern Architecture** - Each phase is a state class ✅ WORKING **2. Action Queue System** - Sequential processing prevents races ✅ WORKING**3. Transition Locks** - Atomic state changes ✅ WORKING **4. Full Validation** - Actions validated before processing ✅ WORKING
### 🔧 In Progress Decisions
**5. Complete Phase Coverage** - All 4 phases in state machine (25% complete) **6. Bot Integration** - Bots use state machine instead of manual checks **7. Route Refactoring** - Replace scattered if/else with state machine calls
### Design Challenges ✅ SOLVED
**1** **Phase Violations**: ✅ State pattern makes impossible - proven in tests
**2** **Race Conditions**: ✅ Action queue solves - proven in tests
**3** **State Synchronization**: ✅ Declaraction state updates game object correctly
**4** **Complex Game Flow**: ✅ State transitions work automatically

⠀Implementation Status
### ✅ What's Working (NEW)
* **State Machine Foundation**: Core system, action queue, base state class
* **Declaration Phase**: Complete implementation with validation
* **Action Processing**: Queued, sequential, race-condition-free
* **Testing Suite**: Comprehensive tests with pytest
* **Integration**: Proven to work with existing game class

⠀✅ What's Still Working (EXISTING)
* Complete game engine (rules, AI, scoring)
* Room system (create, join, host management)
* WebSocket real-time updates
* Bot players with AI
* Full game flow from lobby to scoring
* Frontend with PixiJS scenes

⠀🔧 What's Next (Week 2)
* **Preparation State** - Deal, weak hands, redeal logic
* **Turn State** - Turn sequence, piece play, winner determination
* **Scoring State** - Score calculation, win conditions
* **Complete State Machine** - All 4 phases working together

⠀📅 Current Sprint (See AI_WORKING_DOC.md)
Week 1: ✅ COMPLETED - Foundation architecture working Week 2: 🔧 IN PROGRESS - Complete all 4 phases
# Key Principles (PROVEN)
* ✅ **Server Authority**: Server state is always correct
* ✅ **Fail Safe**: Invalid actions ignored, game continues
* ✅ **Single Source**: State machine is authoritative
* ✅ **Prevention Over Fixes**: Make bugs impossible, not fix them

⠀Testing Strategy (IMPLEMENTED)
* ✅ Unit tests for each state class
* ✅ Integration tests for state machine
* ✅ Action queue race condition tests
* ✅ Invalid action rejection tests
* 🔧 Bot integration tests (Week 2)
* 🔧 Full game flow tests (Week 2)

⠀Testing Commands (WORKING)

### bash
*# Quick integration test*
python backend/run_tests.py

*# Full test suite*  
pytest backend/tests/ -v

*# Individual test files*
pytest backend/tests/test_state_machine.py -v
pytest backend/tests/test_integration.py -v
# When to Read What
### For Game Mechanics
→ Read Rules and relevant Game Flow - * files
### For State Machine Implementation
→ Check backend/engine/state_machine/ files
### For Current Integration
→ Check backend/tests/ and backend/run_tests.py
### For Architecture Decisions
→ This file contains key decisions and their status
# Next Steps
1 ✅ ~~Design state machine based on game flow diagrams~~ COMPLETE
2 🔧 Implement remaining 3 phases (Preparation, Turn, Scoring)
3 🔧 Replace route handlers with state machine calls
4 🔧 Update bot manager to use state machine
5 🔧 Full game flow testing
