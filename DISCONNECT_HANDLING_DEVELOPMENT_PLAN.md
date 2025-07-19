# Disconnect Handling Development Plan

## Executive Summary

This plan enhances the **existing disconnect handling infrastructure** in Liap Tui to support unlimited reconnection time and improved UI feedback. The system leverages existing components (ConnectionManager, BotManager, ConnectionIndicator) rather than creating duplicates.

**Last Updated:** 2025-07-19 - Major revision: Identified extensive existing infrastructure, removed redundant tasks

## 🎯 Existing Infrastructure Analysis

**Backend (Already Complete):**
- ✅ `ConnectionManager` - Full connection tracking with grace periods
- ✅ `BotManager` - Enterprise-grade bot management system
- ✅ `Player` model - Connection fields (is_connected, disconnect_time, original_is_bot)
- ✅ `handle_disconnect()` - WebSocket disconnect handling with bot activation
- ✅ `ai.py` - Complete AI decision logic for all phases
- ✅ Event broadcasting - player_disconnected events

**Frontend (Already Complete):**
- ✅ `ConnectionIndicator` - Connection status component
- ✅ `useConnectionStatus` - TypeScript hook for connection state
- ✅ `PlayerAvatar` - Bot indicators with robot icons and thinking animations
- ✅ `NetworkService` - WebSocket event handling infrastructure
- ✅ `RecoveryService` - Connection recovery mechanisms

**What Actually Needs Work:**
1. Remove grace period logic → unlimited reconnection
2. Enhance ConnectionIndicator → show "AI Playing" messages
3. Add browser close recovery (NEW)
4. Add host migration (NEW)
5. Add multi-tab detection (NEW)

## Revised Project Scope

### Phase 1: Update Existing Infrastructure (1 week)
- Modify ConnectionManager to remove grace periods
- Enhance ConnectionIndicator with AI playing messages
- Update PlayerAvatar disconnect indicators

### Phase 2: New Features Only (1 week)
- Browser close recovery with sessionStorage
- Multi-tab detection with BroadcastChannel
- Auto-reconnection prompts

### Phase 3: Advanced Features (1 week)
- Host migration system
- Connection state persistence
- Enhanced UI polish

**Total Duration:** 3 weeks (reduced from 4)

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

**Task 1.1: Update Connection Tracking for Unlimited Reconnection** 🔄 ALREADY EXISTS - NEEDS UPDATE

- **Current State:** ConnectionManager fully implemented with 30-second grace periods
- **Required Changes:**
  - [ ] Remove grace period checks from `connection_manager.py`
  - [ ] Remove `reconnect_deadline` and `is_within_grace_period()` logic
  - [ ] Update cleanup task to not remove disconnected players
  - [ ] Ensure players can reconnect anytime while game is active
- **Estimate:** 2 hours (modification only)
- **Files to modify:**
  - `backend/api/websocket/connection_manager.py` - Remove grace period logic
  - `backend/api/routes/ws.py` - Update reconnection handling

**Task 1.2: Enhanced WebSocket Disconnect Detection** ✅ COMPLETED (2025-07-19)

- [x] Refactor `websocket_endpoint` to handle disconnects gracefully
- [x] Create `handle_disconnect` function with phase awareness
- [x] Implement connection cleanup logic
- [x] Add disconnect event broadcasting
- [x] Create player-to-websocket mapping
- **Estimate:** 6 hours
- **Dependencies:** Task 1.1 ✅ COMPLETED
- **Scope:** Complete the WebSocket layer to properly handle disconnections with phase awareness
- **Current State:** Basic disconnect handling exists in ws.py but needs enhancement for production robustness
- **What's Missing:**
  - Graceful WebSocket endpoint error handling for production use
  - Phase-aware disconnect logic (different handling based on game phase)
  - More thorough connection cleanup processes
  - Enhanced disconnect event broadcasting structure
- **Implementation Approach:**
  - Enhance existing `handle_disconnect` function with comprehensive phase awareness
  - Create dedicated `backend/api/websocket/handlers.py` for organized disconnect logic
  - Add comprehensive error handling to websocket_endpoint function
  - Improve disconnect event broadcasting with standardized event structure
- **Files to modify:**
  - `backend/api/routes/ws.py` - Enhance websocket_endpoint exception handling
  - Create `backend/api/websocket/handlers.py` - Dedicated disconnect handlers
- **UI Impact:** None (backend-only reliability improvement)
- **Actual Implementation:**
  - Created comprehensive `DisconnectHandler` class with phase-aware logic
  - Enhanced reconnection with `ReconnectionHandler` for full state sync
  - Improved error handling with graceful shutdown support
  - Added phase-specific action tracking for better debugging
  - Full test coverage with all scenarios passing
- **Files created:**
  - `backend/api/websocket/handlers.py` - Phase-aware disconnect handlers
- **Files modified:**
  - `backend/api/routes/ws.py` - Enhanced error handling and phase awareness
- **Test Results:** All tests passing - see TASK_1_2_TEST_REPORT.md

**Task 1.3: Bot Activation on Disconnect** ✅ ALREADY EXISTS IN CODEBASE

- **Status:** FULLY IMPLEMENTED - NO WORK NEEDED
- **Existing Implementation:**
  - `handle_disconnect()` in ws.py already sets `player.is_bot = True`
  - Player model has `original_is_bot` field for reconnection
  - Bot activation broadcasts `player_disconnected` event
  - BotManager automatically handles bot players
- **Location:** `backend/api/routes/ws.py` lines 45-66

#### More Frontend Tasks (Priority: High)

**Task 1.4: Enhance Existing UI Components** 🔄 PARTIALLY EXISTS - NEEDS ENHANCEMENT

- **Current State:** 
  - ConnectionIndicator component exists
  - useConnectionStatus TypeScript hook exists
  - PlayerAvatar has bot support
- **Required Enhancements:**
  - [ ] Add `disconnectedPlayers` prop to ConnectionIndicator
  - [ ] Show "AI Playing for: [names] - Can reconnect anytime" message
  - [ ] Add disconnect badge overlay to PlayerAvatar
  - [ ] Add grayed-out styling for disconnected players
- **Estimate:** 3 hours (enhancement only)
- **Files to modify:**
  - `frontend/src/components/ConnectionIndicator.jsx` - Add AI playing message
  - `frontend/src/components/game/shared/PlayerAvatar.jsx` - Add disconnect indicators
  - `frontend/src/styles/components/game/shared/player-avatar.css` - Add disconnect styles

**Task 1.5: WebSocket Event Handlers** ✅ COMPLETED (2025-07-19)

- [x] Add handlers for new disconnect events
- [x] Implement reconnection event handling
- [x] Create event type definitions
- [x] Update WebSocket message dispatcher
- [x] Add connection status to game state
- [x] Add handler for `ai_activated` event - Triggers when bot takes over
- [x] Add handler for `reconnection_summary` event - Contains game events during disconnect
- [x] Create toast notification triggers for disconnect/reconnect events
- **Actual Implementation:**
  - Created comprehensive event type definitions in `frontend/src/types/events.ts`
  - Built DisconnectEventService to handle NetworkService events
  - Created NetworkServiceIntegration module for easy setup
  - Implemented toast notification system with auto-dismiss
  - Updated useDisconnectStatus hook to use window events
  - Created demo component showing full integration
- **Architecture:**
  - NetworkService dispatches CustomEvents
  - DisconnectEventService listens and re-dispatches as window events
  - UI components listen to window events for decoupling
  - Toast notifications automatically appear for all disconnect events
- **Files created:**
  - `frontend/src/types/events.ts` - TypeScript event definitions
  - `frontend/src/services/DisconnectEventService.ts` - Event handling service
  - `frontend/src/services/NetworkServiceIntegration.ts` - Integration module
  - `frontend/src/components/ToastNotification.jsx` - Toast component
  - `frontend/src/components/ToastContainer.jsx` - Toast container
  - `frontend/src/hooks/useToastNotifications.js` - Toast management hook
  - `frontend/src/styles/toast-notifications.css` - Toast styling
  - `frontend/src/components/WebSocketEventDemo.jsx` - Demo component
- **Files modified:**
  - `frontend/src/hooks/useDisconnectStatus.js` - Updated to use window events
- **Estimate:** 6 hours
- **Dependencies:** Task 1.4
- **Scope:** Connect the backend disconnect events to frontend UI updates through enhanced WebSocket handling
- **Current State:** NetworkService.ts exists but needs disconnect event integration
- **What's Missing:**
  - Event handlers for player_disconnected and player_reconnected events
  - Integration with existing NetworkService.ts for disconnect events
  - Event type definitions for TypeScript safety
  - UI state synchronization when disconnect events are received
- **UI Components Affected:**
  - All game components that show player status need real-time updates
  - Real-time disconnect notifications must appear immediately
  - Connection status indicators need to update automatically
- **Implementation Approach:**
  - Enhance existing `NetworkService.ts` with disconnect event handlers
  - Create `frontend/src/types/events.ts` for event type definitions  
  - Add event listeners for player_disconnected and player_reconnected
  - Trigger UI updates automatically when disconnect events are received
  - Ensure real-time synchronization between backend events and frontend state
- **UI Changes:**
  - Real-time disconnect notifications appear immediately when players disconnect
  - Automatic UI updates when players disconnect/reconnect (no refresh needed)
  - Connection indicators update in real-time across all game components
- **Files to create:**
  - `frontend/src/types/events.ts` - Disconnect event type definitions
- **Files to modify:**
  - `frontend/src/services/NetworkService.ts` - Add disconnect event handling

---

### Week 2: Bot Integration & Testing

#### Backend Tasks (Priority: Critical)

**Task 2.1: Browser Recovery Features** 🆕 NEW FEATURE

- **Status:** Genuinely new functionality not in codebase
- **Features to Add:**
  - [ ] Store session info in localStorage on connection
  - [ ] Implement auto-reconnect check on page load
  - [ ] Add session expiry after 24 hours of inactivity
  - [ ] Add room ID to game URL format: `/game/{roomId}`
  - [ ] Detect if game is already open in another tab
  - [ ] Show warning dialog for duplicate sessions
  - [ ] Handle tab communication via BroadcastChannel API
- **Estimate:** 8 hours (all new code)
- **Files to create:**
  - `frontend/src/utils/sessionStorage.js` - Browser session persistence
  - `frontend/src/utils/tabCommunication.js` - Multi-tab detection
  - `frontend/src/hooks/useAutoReconnect.js` - Auto-reconnection logic
  - `frontend/src/components/ReconnectionPrompt.jsx` - UI prompt

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

**Task 2.3: WebSocket Event Broadcasting** ✅ ALREADY EXISTS

- **Status:** FULLY IMPLEMENTED - NO WORK NEEDED
- **Existing Implementation:**
  - `player_disconnected` event already broadcast in `handle_disconnect()`
  - Event includes player_name, ai_activated, and is_bot fields
  - NetworkService in frontend handles these events
- **Location:** `backend/api/routes/ws.py` lines 57-66

#### Frontend Tasks (Priority: High)

**Task 2.4: Disconnect UI Updates** 🎨 HIGH PRIORITY

- [ ] Show "AI Playing" badge when player.is_bot becomes true
- [ ] Display "Can reconnect anytime" message (no countdown timer)
- [ ] Add disconnect notification toasts
- [ ] Update player avatar opacity for disconnected players
- [ ] Show "Reconnected" animation
- [ ] Create `ReconnectSummary.jsx` - Shows "While you were away" summary
- [ ] Create `useToastNotifications.js` hook - Manages toast notification queue
- [ ] Add CSS files: `disconnect-overlay.css`, `toast-notifications.css`, `connection-badges.css`
- [ ] Implement 5-second auto-dismiss functionality for toast notifications
- **Estimate:** 6 hours
- **Dependencies:** Task 1.5
- **Scope:** Provide rich visual feedback when players disconnect and bots take over
- **What's Missing:**
  - "AI Playing" badges with clear visual indicators when bot takes control
  - Toast notification system for disconnect/reconnect events
  - Visual avatar changes (opacity, styling) for disconnected players
  - Smooth reconnection success animations and transitions
- **UI Components to Create/Modify:**
  - **Create:** `frontend/src/components/DisconnectNotification.jsx`
    - Toast-style notifications for disconnect events
    - Reconnection success messages with animations
    - Configurable notification types (disconnect, reconnect, bot takeover)
  - **Create:** `frontend/src/components/AIPlayingBadge.jsx`
    - Badge/indicator showing bot is in control with clear messaging
    - "Can reconnect anytime" message instead of timer
    - Visual distinction from normal player indicators
  - **Modify:** `frontend/src/components/game/shared/PlayerAvatar.jsx`
    - Add disconnect styling (reduced opacity, grayed out appearance)
    - Smooth CSS animations for state changes
    - Integration with new badges and status indicators
  - **Enhance:** All game phase components
    - Show disconnect notifications contextually within each phase
    - Ensure consistent disconnect feedback across all game phases
- **UI Changes:**
  - Clear visual indicators when bots take over player control
  - Toast notifications appear immediately for disconnect events
  - Player avatars visually change when disconnected (dimmed/grayed)
  - Smooth animations for reconnection events
  - Professional, polished visual feedback system
- **Implementation Approach:**
  - Create comprehensive toast notification system for disconnect events
  - Add professional visual styling for disconnected player avatars  
  - Implement "AI Playing" badges with "Can reconnect anytime" message
  - Add smooth CSS transitions for all state changes
  - Ensure consistent user experience across all game components
- **Files to create:**
  - `frontend/src/components/DisconnectNotification.jsx` - Toast notifications
  - `frontend/src/components/AIPlayingBadge.jsx` - Bot control indicators
  - `frontend/src/components/ReconnectSummary.jsx` - Post-reconnection summary
  - `frontend/src/hooks/useToastNotifications.js` - Toast queue management
  - `frontend/src/styles/disconnect-overlay.css` - Overlay styling
  - `frontend/src/styles/toast-notifications.css` - Toast positioning and animations
  - `frontend/src/styles/connection-badges.css` - Badge overlay styles
- **Files to modify:**
  - `frontend/src/components/game/shared/PlayerAvatar.jsx` - Disconnect styling
  - All game phase components - Contextual disconnect notifications

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

**Task 3.1: Host Migration System** 🆕 NEW FEATURE

- **Status:** Genuinely new functionality not in codebase
- **Features to Add:**
  - [ ] Detect when host disconnects
  - [ ] Select next player as host (prefer humans over bots)
  - [ ] Transfer host privileges
  - [ ] Broadcast host_changed event
  - [ ] Show crown icon for current host
  - [ ] Update UI to show host-only controls
- **Estimate:** 6 hours (all new code)
- **Why Needed:** Without this, rooms become orphaned when host disconnects
- **Files to modify:**
  - `backend/engine/room.py` - Add host migration logic
  - `backend/api/routes/ws.py` - Trigger migration on host disconnect
- **Files to create:**
  - `frontend/src/components/HostIndicator.jsx` - Crown icon UI

**Task 3.2: Connection Recovery** 🔄 MEDIUM PRIORITY

- [ ] Add message queue for disconnected players
- [ ] Implement state snapshot system
- [ ] Handle partial action recovery
- [ ] Test recovery scenarios
- [ ] Add recovery metrics
- **Estimate:** 8 hours
- **Dependencies:** Week 2 backend tasks
- **Scope:** Queue important game events for disconnected players and provide state synchronization when they reconnect
- **What It Does:**
  - **Message queuing**: Stores critical game events that happened during disconnect
  - **State snapshots**: Creates periodic saves of complete game state
  - **Recovery on reconnect**: Sends missed events and current state to reconnecting players
  - **Partial action recovery**: Handles cases where players disconnected mid-action
- **Why We Need It:**
  - **Without connection recovery**: Reconnecting players have incomplete/outdated game state. They might see wrong scores, positions, or phase information. Can cause desync between clients and server.
  - **With connection recovery**: Reconnecting players get complete, up-to-date game state. No confusion about what happened during disconnect. Prevents game state desynchronization.
- **What's Missing:**
  - Message queuing system for disconnected players
  - State snapshot system for game state preservation
  - Recovery metrics to track success rates
  - Partial action recovery for mid-action disconnects
- **Implementation Approach:**
  - Create `backend/api/websocket/message_queue.py` for event queuing system
  - Implement state snapshot system for game state preservation
  - Add recovery progress indicators in UI
  - Ensure reliable state synchronization for reconnecting players
- **UI Impact:**
  - Loading indicators during state recovery process
  - Progress bars showing sync completion
  - Recovery success/failure notifications
  - More reliable state consistency after reconnection
- **Files to create:**
  - `backend/api/websocket/message_queue.py` - Event queuing system

#### Frontend Tasks (Priority: High)

**Task 3.3: Enhanced UI Components** ✨ LOW PRIORITY

- [ ] Create host crown indicator
- [ ] Implement smooth transitions for bot/human switch
- [ ] Add connection quality indicator
- [ ] Create reconnection progress bar
- [ ] Add reconnection success animation (green checkmark ✅ fade)
- [ ] Create smooth fade transitions for overlay dismissal
- [ ] Implement stacking behavior for multiple toast notifications
- **Estimate:** 8 hours
- **Dependencies:** Week 2 frontend tasks
- **Scope:** Polish and professional UI elements for connection management
- **What It Does:**
  - **Connection quality indicators**: Visual network strength indicators
  - **Smooth transition animations**: Professional state change animations
  - **Progress bars**: Reconnection progress and countdown displays
  - **Professional polish**: Consistent styling and behavior across all connection features
- **Why We Need It:**
  - **Without enhanced UI**: Players confused about connection states, jarring experience when bot takes over, no visual feedback about connection issues
  - **With enhanced UI**: Professional, polished user experience with clear visual feedback for all connection states. Reduces user confusion and support requests.
- **What's Missing:**
  - Connection quality/latency indicators showing network strength
  - Professional animations for state changes
  - Polished progress bars and loading states
  - Consistent styling across all connection components
- **UI Components to Create/Modify:**
  - **Create:** Connection quality indicators
    - Network strength icons (signal bars, etc.)
    - Latency indicators showing connection quality
    - Visual feedback for connection health
  - **Enhance:** All connection-related components
    - Professional CSS animations for state transitions
    - Consistent color schemes and visual design
    - Smooth transitions for all connection state changes
  - **Add:** Progress and loading components
    - Reconnection progress bars with visual feedback
    - State change animations that are smooth and professional
    - Loading indicators for connection processes
- **UI Changes:**
  - Connection quality/latency indicators visible to players
  - Professional state change animations throughout the system
  - Polished progress bars for reconnection and loading states
  - Consistent, professional visual experience across all connection features
- **Implementation Approach:**
  - Add connection quality monitoring and visual indicators
  - Implement smooth CSS animations for all state changes
  - Create professional progress indicators and loading states
  - Ensure consistent user experience across all connection scenarios
- **Files to create:**
  - `frontend/src/components/HostIndicator.tsx` - Crown icon for host
  - `frontend/src/components/ConnectionQuality.tsx` - Network strength indicators

---

### Week 4: Testing & Polish

#### QA Tasks (Priority: Critical)

**Task 4.1: End-to-End Testing**

- [ ] Test disconnect in each game phase
- [ ] Verify bot takes over correctly
- [ ] Test reconnection within grace period
- [ ] Test reconnection after game ends
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
- [ ] Document reconnection behavior
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
- [ ] Connection recovery system complete
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
- Week 3: Host migration and connection recovery
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

**Week 1 Core Backend Infrastructure is COMPLETE!** The system now has full connection tracking, automatic bot activation on disconnect, and seamless reconnection handling.

**🎯 IMMEDIATE NEXT PRIORITIES (Week 1 Completion):**
1. **Task 1.2** - Enhanced WebSocket Disconnect Detection (backend reliability)
2. **Task 1.4** - Connection Status UI Components (🚨 CRITICAL - user feedback)
3. **Task 1.5** - WebSocket Event Handlers (🚨 CRITICAL - real-time updates)

**📋 DETAILED IMPLEMENTATION PLAN:**
- **Phase 1**: Complete core UI integration with visual feedback
- **Phase 2**: Add rich disconnect notifications and reconnection handling  
- **Phase 3**: Implement advanced features (host migration, spectator mode)

All tasks now include detailed scope definitions, UI component specifications, and implementation approaches for immediate development start.

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

## 📋 ACTUAL WORK NEEDED - SUMMARY

### **Already Exists (No Work Needed):**
- ✅ ConnectionManager with full tracking
- ✅ Bot activation on disconnect
- ✅ WebSocket event broadcasting
- ✅ PlayerAvatar with bot indicators
- ✅ ConnectionIndicator component
- ✅ useConnectionStatus hook
- ✅ NetworkService infrastructure

### **Needs Enhancement (Modify Existing):**
1. **Task 1.1**: Remove grace periods from ConnectionManager (2 hrs)
2. **Task 1.4**: Add "AI Playing" message to ConnectionIndicator (3 hrs)
3. **Task 1.4**: Add disconnect badges to PlayerAvatar (included above)

### **Genuinely New Features:**
1. **Task 2.1**: Browser close recovery with sessionStorage (8 hrs)
2. **Task 2.1**: Multi-tab detection with BroadcastChannel (included above)
3. **Task 3.1**: Host migration system (6 hrs)
4. **Task 2.4**: Toast notifications for events (4 hrs)

### **Total Effort:**
- Enhancements: ~5 hours
- New Features: ~18 hours
- Testing: ~7 hours
- **Total: ~30 hours (< 1 week with 2 developers)**

### **Recommended Approach:**
1. Start with quick wins (remove grace periods, enhance UI)
2. Add browser recovery features
3. Implement host migration
4. Polish and test

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
