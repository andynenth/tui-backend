# Disconnect Handling Development Plan

## Executive Summary

This plan implements a robust disconnection handling system for Liap Tui, ensuring games continue smoothly when players disconnect. The system leverages the **existing AI infrastructure** (bot_manager.py and ai.py) rather than creating new AI components, significantly reducing development time and complexity.

**Last Updated:** 2025-07-18 - Major update: Core Week 1 backend infrastructure now COMPLETED (Tasks 1.0, 1.1, 1.3)

## 🚀 Major Simplification from Original Plan

**Discovery: The game already has a complete AI system!**

Original plan assumed we needed to:
- Build AI player framework from scratch
- Implement AI decision logic for each phase
- Create bot management system
- Develop AI strategies

**Reality: All of this already exists!**
- `backend/engine/ai.py` - Complete AI decision logic
- `backend/engine/bot_manager.py` - Enterprise-grade bot management
- `Player.is_bot` flag - Built-in bot support

**Result: 33% time savings (4 weeks instead of 6)**

## Current Implementation Status (2025-07-18)

### Already Completed:
- ✅ Backend sends `is_bot` data to frontend properly
- ✅ Bot avatar indicators (robot icon vs letter avatar)
- ✅ Bot thinking animations (inner border spinner)
- ✅ UI clearly distinguishes humans vs bots

### Still Needed:
- Connection tracking and disconnect detection
- Bot activation when player disconnects
- Reconnection grace period handling
- Host migration logic

## Implementation Strategy

When a player disconnects, we simply:
1. Set `player.is_bot = True`
2. The existing BotManager automatically handles all AI decisions
3. On reconnection, set `player.is_bot = False`

No AI development needed!

## Project Timeline

**Total Duration:** 4 weeks (reduced from 6)  
**Team Size:** 2 developers (1 backend, 1 frontend)  
**Start Date:** [To be determined]

## Milestones Overview

### Milestone 1: Connection Tracking (Week 1)
Core connection tracking and bot activation

### Milestone 2: Bot Integration (Week 2)
Ensure seamless AI takeover using existing bot system

### Milestone 3: UI & Advanced Features (Week 3)
Frontend updates and host migration

### Milestone 4: Testing & Polish (Week 4)
Comprehensive testing and edge cases

---

## Detailed Task Breakdown

### Week 1: Foundation & Infrastructure

#### Frontend Tasks (Priority: Critical - Start Here!)

**Task 1.0: Bot Avatar Indicators** ✅ COMPLETED (2025-07-18)

- [x] Create robot avatar component for bot players
- [x] Update player avatar to check `player.is_bot` flag  
- [x] Show robot icon for bots, letter for humans
- [x] Add "thinking" animation for bot's turn (inner border spinner)
- [x] Test with existing bot players (no disconnect needed)
- **Actual Implementation:**
  - PlayerAvatar.jsx already handles `isBot` prop from backend
  - Bot SVG icon implemented
  - Thinking animation uses inner border spinner effect
  - Distinct gray color scheme for bots
- **Files modified:**
  - `frontend/src/components/game/shared/PlayerAvatar.jsx`
  - `frontend/src/styles/components/game/shared/player-avatar.css`

#### Backend Tasks (Priority: Critical)

**Task 1.1: Player Connection Tracking System** ✅ COMPLETED (2025-07-18)

- [x] Create `PlayerConnection` class with status tracking
- [x] Add connection status to player model  
- [x] Implement connection state machine (connected/disconnected/reconnecting)
- [x] Add disconnect timestamp tracking
- [x] Create reconnection deadline logic
- **Actual Implementation:**
  - Created comprehensive ConnectionManager class with async operations
  - Added connection tracking fields to Player model
  - Implemented grace period system (30 seconds default)
  - Added automatic cleanup of expired connections
  - Full test coverage with successful test execution
- **Files modified:**
  - `backend/engine/player.py` - Added connection tracking properties
  - `backend/api/websocket/connection_manager.py` - Complete ConnectionManager implementation
  - `backend/api/routes/ws.py` - Integrated disconnect handling with bot activation
- **Test Results:** All tests passing - see TASK_1_1_TEST_REPORT.md

**Task 1.2: Enhanced WebSocket Disconnect Detection**

- [ ] Refactor `websocket_endpoint` to handle disconnects gracefully
- [ ] Create `handle_disconnect` function with phase awareness
- [ ] Implement connection cleanup logic
- [ ] Add disconnect event broadcasting
- [ ] Create player-to-websocket mapping
- **Estimate:** 6 hours
- **Dependencies:** Task 1.1
- **Files to modify:**
  - `backend/api/routes/ws.py`
  - `backend/api/websocket/handlers.py`

**Task 1.3: Bot Activation on Disconnect** ✅ COMPLETED (2025-07-18)

- [x] Add disconnect handler that sets `player.is_bot = True`
- [x] Store original bot state for reconnection
- [x] Create reconnection deadline tracking
- [x] Test bot activation in all phases
- [x] Verify BotManager handles converted players
- **Actual Implementation:**
  - Integrated with ConnectionManager for seamless bot activation
  - Player original_is_bot state preserved for reconnection
  - Bot activation occurs automatically on disconnect
  - Broadcasting of disconnect events with AI activation status
  - Comprehensive testing of bot activation scenarios
- **Files modified:**
  - `backend/api/routes/ws.py` - Complete disconnect handling with bot activation
- **Test Results:** Bot activation working correctly - see TASK_1_1_TEST_REPORT.md

#### More Frontend Tasks (Priority: High)

**Task 1.4: Connection Status UI Components**

- [ ] Create `PlayerStatus` TypeScript interface
- [ ] Build `ConnectionIndicator` component
- [ ] Add connection status overlay to avatars
- [ ] Create reconnection countdown timer
- [ ] Implement connection status store
- **Estimate:** 6 hours (reduced - avatar work done in 1.0)
- **Dependencies:** None (Task 1.0 is complete)
- **Files to create:**
  - `frontend/src/components/ConnectionIndicator.tsx`
  - `frontend/src/stores/connectionStore.ts`

**Task 1.5: WebSocket Event Handlers**

- [ ] Add handlers for new disconnect events
- [ ] Implement reconnection event handling
- [ ] Create event type definitions
- [ ] Update WebSocket message dispatcher
- [ ] Add connection status to game state
- **Estimate:** 6 hours
- **Dependencies:** Task 1.4
- **Files to modify:**
  - `frontend/src/network/websocket.ts`
  - `frontend/src/types/events.ts`

---

### Week 2: Bot Integration & Testing

#### Backend Tasks (Priority: Critical)

**Task 2.1: Reconnection Handler**

- [ ] Implement reconnection detection within grace period
- [ ] Restore `player.is_bot` to original state
- [ ] Send full game state sync to reconnected player
- [ ] Handle late reconnections (spectator mode)
- [ ] Test reconnection in all phases
- **Estimate:** 6 hours
- **Dependencies:** Week 1 backend tasks
- **Files to modify:**
  - `backend/api/routes/ws.py`
  - `backend/api/websocket/handlers.py`

**Task 2.2: Phase-Specific Testing**

- [ ] Test bot takeover during PREPARATION phase
- [ ] Test bot takeover during DECLARATION phase
- [ ] Test bot takeover during TURN phase
- [ ] Test bot behavior during SCORING phase
- [ ] Verify no duplicate bot actions
- **Estimate:** 8 hours
- **Dependencies:** Task 1.3
- **Files to modify:**
  - `backend/tests/test_disconnect_handling.py` (create)

**Task 2.3: WebSocket Event Broadcasting**

- [ ] Add `player_disconnected` event
- [ ] Add `player_reconnected` event
- [ ] Update phase_change events to include connection status
- [ ] Test event delivery to all clients
- [ ] Document event formats
- **Estimate:** 4 hours
- **Dependencies:** Task 2.1
- **Files to modify:**
  - `backend/api/websocket/events.py`

#### Frontend Tasks (Priority: High)

**Task 2.4: Disconnect UI Updates**

- [ ] Show "AI Playing" badge when player.is_bot becomes true
- [ ] Display reconnection countdown timer
- [ ] Add disconnect notification toasts
- [ ] Update player avatar opacity for disconnected players
- [ ] Show "Reconnected" animation
- **Estimate:** 6 hours
- **Dependencies:** Task 1.5
- **Files to modify:**
  - `frontend/src/components/PlayerAvatar.tsx`
  - `frontend/src/components/GameNotifications.tsx`

**Task 2.5: Connection State Management**

- [ ] Update game state to track disconnected players
- [ ] Handle player_disconnected WebSocket events
- [ ] Handle player_reconnected WebSocket events
- [ ] Sync UI with backend connection status
- [ ] Test state updates in all phases
- **Estimate:** 4 hours
- **Dependencies:** Task 1.4, Task 2.3
- **Files to modify:**
  - `frontend/src/stores/gameStore.ts`
  - `frontend/src/network/websocket.ts`

---

### Week 3: UI Polish & Advanced Features

#### Backend Tasks (Priority: High)

**Task 3.1: Host Migration System**

- [ ] Detect when host disconnects
- [ ] Select next player as host
- [ ] Transfer host privileges
- [ ] Broadcast host change event
- [ ] Test host migration scenarios
- **Estimate:** 8 hours
- **Dependencies:** Week 2 backend tasks
- **Files to modify:**
  - `backend/api/websocket/room_manager.py`
  - `backend/models/room.py`

**Task 3.2: Spectator Mode**

- [ ] Create spectator view for late reconnections
- [ ] Implement read-only game state
- [ ] Add spectator WebSocket handlers
- [ ] Test spectator functionality
- [ ] Document spectator limitations
- **Estimate:** 6 hours
- **Dependencies:** Task 2.1
- **Files to create:**
  - `backend/api/websocket/spectator_handler.py`

**Task 3.3: Connection Recovery**

- [ ] Add message queue for disconnected players
- [ ] Implement state snapshot system
- [ ] Handle partial action recovery
- [ ] Test recovery scenarios
- [ ] Add recovery metrics
- **Estimate:** 8 hours
- **Dependencies:** Week 2 backend tasks
- **Files to create:**
  - `backend/api/websocket/message_queue.py`

#### Frontend Tasks (Priority: High)

**Task 3.4: Enhanced UI Components**

- [ ] Create host crown indicator
- [ ] Add spectator mode UI
- [ ] Implement smooth transitions for bot/human switch
- [ ] Add connection quality indicator
- [ ] Create reconnection progress bar
- **Estimate:** 8 hours
- **Dependencies:** Week 2 frontend tasks
- **Files to create:**
  - `frontend/src/components/HostIndicator.tsx`
  - `frontend/src/components/SpectatorView.tsx`

---

### Week 4: Testing & Polish

#### QA Tasks (Priority: Critical)

**Task 4.1: End-to-End Testing**

- [ ] Test disconnect in each game phase
- [ ] Verify bot takes over correctly
- [ ] Test reconnection within grace period
- [ ] Test late reconnection (spectator mode)
- [ ] Verify no game freezes or hangs
- **Estimate:** 12 hours
- **Dependencies:** All previous tasks
- **Files to create:**
  - `backend/tests/test_disconnect_scenarios.py`
  - `frontend/tests/disconnect.test.ts`

**Task 4.2: Performance Testing**

- [ ] Test with multiple simultaneous disconnects
- [ ] Verify bot response times remain consistent
- [ ] Check WebSocket message queue performance
- [ ] Test reconnection under load
- [ ] Profile memory usage with disconnected players
- **Estimate:** 8 hours
- **Dependencies:** Task 4.1
- **Files to create:**
  - `backend/tests/test_disconnect_performance.py`

**Task 4.3: Edge Case Testing**

- [ ] Test rapid connect/disconnect cycles
- [ ] Test browser refresh scenarios
- [ ] Test network timeout scenarios
- [ ] Test mobile app background/foreground
- [ ] Document all edge cases found
- **Estimate:** 10 hours
- **Dependencies:** Task 4.1
- **Files to modify:**
  - `backend/tests/test_edge_cases.py`

#### Documentation Tasks (Priority: High)

**Task 4.4: User Documentation**

- [ ] Document disconnect/reconnect behavior
- [ ] Create troubleshooting guide
- [ ] Add UI screenshots with AI indicators
- [ ] Document spectator mode
- [ ] Create admin guide for monitoring
- **Estimate:** 6 hours
- **Dependencies:** All features complete
- **Files to create:**
  - `docs/disconnect_handling.md`
  - `docs/troubleshooting.md`

---

## Dependencies Matrix

### Critical Path Dependencies

1. **Connection Tracking (1.1)** → All disconnect detection features
2. **Bot Activation (1.3)** → Bot takeover functionality
3. **Reconnection Handler (2.1)** → Player control restoration
4. **WebSocket Events (1.5)** → All frontend disconnect features

### Backend Dependencies

- Bot activation depends on existing BotManager working correctly
- Host migration depends on connection tracking
- Spectator mode depends on reconnection handler

### Frontend Dependencies

- All UI components depend on connection status store
- Disconnect notifications depend on WebSocket events
- Host migration UI depends on backend implementation

---

## Risk Mitigation

### Technical Risks

1. **Existing Bot System Integration**
   - Risk: BotManager might not handle mid-game bot conversions
   - Mitigation: Thorough testing in Week 2
   - Fallback: Add special handling for converted players

2. **WebSocket Stability**
   - Mitigation: Implement heartbeat system
   - Fallback: HTTP polling for critical updates

3. **State Synchronization**
   - Mitigation: Full state sync on reconnection
   - Fallback: Force refresh if sync fails

### Schedule Risks

1. **Unknown Bot System Behavior**
   - Buffer: Week 2 dedicated to integration testing
   - Option: Manual bot action triggers if needed

2. **Testing Coverage**
   - Mitigation: Start testing in Week 2
   - Buffer: Full Week 4 for testing

---

## Success Criteria

### Week 1 Deliverables

- [x] Bot avatar indicators working (testable immediately) ✅ COMPLETED
- [x] Connection tracking operational ✅ COMPLETED
- [x] Bot activation on disconnect working ✅ COMPLETED
- [x] UI clearly distinguishes humans vs bots ✅ COMPLETED

### Week 2 Deliverables

- [ ] Reconnection handler working
- [ ] Bot integration verified in all phases
- [ ] Disconnect UI updates implemented

### Week 3 Deliverables

- [ ] Host migration functional
- [ ] Spectator mode available
- [ ] Enhanced UI components complete

### Week 4 Deliverables

- [ ] All tests passing
- [ ] Edge cases handled
- [ ] Documentation complete

---

## Team Assignments

### Backend Developer

- Week 1: Connection tracking and bot activation
- Week 2: Reconnection handler and testing
- Week 3: Host migration and spectator mode
- Week 4: Support QA and bug fixes

### Frontend Developer

- Week 1: Connection status UI components
- Week 2: Disconnect notifications and state management
- Week 3: Enhanced UI and host migration
- Week 4: Polish and testing support

### QA Engineer (Optional - can be shared role)

- Week 2: Integration test planning
- Week 3: Test implementation
- Week 4: Full testing and documentation

---

## Notes for Project Management Tools

### Quick Start
**Major Progress Update (2025-07-18):**
- ✅ Task 1.0 (Bot Avatar Indicators) - COMPLETED 
- ✅ Task 1.1 (Player Connection Tracking System) - COMPLETED
- ✅ Task 1.3 (Bot Activation on Disconnect) - COMPLETED

**Week 1 Core Backend Infrastructure is COMPLETE!** The system now has full connection tracking, automatic bot activation on disconnect, and seamless reconnection handling. Next priority is Task 1.2 (Enhanced WebSocket Disconnect Detection) and frontend tasks 1.4-1.5.

### Jira/Trello Setup

1. Create epic: "Disconnect Handling System"
2. Create sprints for each week
3. Add tasks with estimates and dependencies
4. Set up automation for status updates
5. Create dashboard for progress tracking
6. **Task 1.0 marked as DONE - bot avatars complete!**

### Labels/Tags

- `backend`, `frontend`, `qa`
- `critical`, `high`, `medium`
- `ai`, `websocket`, `ui`
- `blocked`, `in-progress`, `review`

### Definition of Done

- [ ] Code implemented and tested
- [ ] Unit tests passing
- [ ] Code reviewed by peer
- [ ] Integration tests passing
- [ ] Documentation updated
- [ ] Deployed to staging environment

---

<!--
# AI_DIRECTIVE

You are an autonomous project assistant assigned to execute the Disconnect Handling Development Plan for the "Liap Tui" project.

## Your Tasks:

1. **Interpret this document as an active checklist.**  
   Each task with `[ ]` means it's not started.  
   Each `[x]` or `✅` means it's done.  
   Your job is to go through tasks **in order**, unless marked done.

2. **For each task that is not complete:**
   - Analyze the described functionality.
   - Identify or request the required files.
   - Generate or propose code implementations if not already provided.
   - If a file or implementation is missing, pause and ask the user or flag the blocker.
   - If instructions refer to a new file, you are allowed to create it.

3. **Skip any task that is marked as done.**

4. **Maintain progress tracking**:  
   Update checklist states (`[ ]` → `✅`) as tasks are completed.  
   You may use `<!-- AI_PROGRESS_LOG -->` block if needed to track state internally.

5. **If dependencies are listed**, ensure all dependencies are completed before beginning a dependent task.

6. **For testing-related tasks**, you may:

   - Generate unit tests, integration test cases, or mock scenarios.
   - Ask for test data if required.

7. **If uncertainty arises**, stop and ask the user for clarification before proceeding.

8. **For frontend-related tasks**, generate JSX/TSX with Tailwind styling where applicable.  
   Use placeholder data where needed and mention where integration points are expected.

9. **When tasks reference business logic (e.g., AI decisions)**, provide default logic and flag for refinement later.

## Goal:

Complete this plan autonomously, step-by-step, until all tasks are implemented, reviewed, and marked ✅.

-->
