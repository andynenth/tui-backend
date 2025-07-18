# Disconnect Handling Development Plan

## Executive Summary
This plan implements a robust disconnection handling system for Liap Tui, ensuring games continue smoothly when players disconnect. The system includes AI player substitution, reconnection grace periods, and host migration.

## Project Timeline
**Total Duration:** 6 weeks  
**Team Size:** 2-3 developers (1 backend, 1 frontend, 1 QA/support)  
**Start Date:** [To be determined]  

## Milestones Overview

### Milestone 1: Foundation & Infrastructure (Week 1)
Core connection tracking and AI framework

### Milestone 2: Basic Disconnect Handling (Week 2)
Turn timeouts and simple AI integration

### Milestone 3: Phase-Specific Logic (Week 3-4)
Handling disconnects in each game phase

### Milestone 4: Advanced Features (Week 5)
Host migration and reconnection logic

### Milestone 5: Polish & Testing (Week 6)
UI improvements and comprehensive testing

---

## Detailed Task Breakdown

### Week 1: Foundation & Infrastructure

#### Backend Tasks (Priority: Critical)

**Task 1.1: Player Connection Tracking System**
- [ ] Create `PlayerConnection` class with status tracking
- [ ] Add connection status to player model
- [ ] Implement connection state machine (connected/disconnected/reconnecting)
- [ ] Add disconnect timestamp tracking
- [ ] Create reconnection deadline logic
- **Estimate:** 8 hours
- **Dependencies:** None
- **Files to modify:** 
  - `backend/engine/player.py`
  - `backend/api/websocket/connection_manager.py`

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

**Task 1.3: AI Player Framework**
- [ ] Create `AIPlayer` base class
- [ ] Implement basic decision interfaces
- [ ] Add difficulty level support (easy/medium/hard)
- [ ] Create AI player factory
- [ ] Add AI flag to player model
- **Estimate:** 10 hours
- **Dependencies:** None
- **Files to create:**
  - `backend/engine/ai/base_ai.py`
  - `backend/engine/ai/ai_factory.py`

#### Frontend Tasks (Priority: High)

**Task 1.4: Connection Status UI Components**
- [ ] Create `PlayerStatus` TypeScript interface
- [ ] Build `ConnectionIndicator` component
- [ ] Add connection status to player avatars
- [ ] Create reconnection countdown timer
- [ ] Implement connection status store
- **Estimate:** 8 hours
- **Dependencies:** None
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

### Week 2: Basic Disconnect Handling

#### Backend Tasks (Priority: Critical)

**Task 2.1: Turn Timer System**
- [ ] Implement configurable turn timers
- [ ] Create timer start/stop/pause logic
- [ ] Add timeout callbacks
- [ ] Integrate with state machine
- [ ] Handle timer events in WebSocket
- **Estimate:** 8 hours
- **Dependencies:** Week 1 backend tasks
- **Files to create:**
  - `backend/engine/timers/turn_timer.py`
  - `backend/engine/timers/timer_manager.py`

**Task 2.2: Basic AI Turn Logic**
- [ ] Implement AI piece selection algorithm
- [ ] Create basic strategy patterns
- [ ] Add random decision fallback
- [ ] Integrate with turn state
- [ ] Test AI decision timing
- **Estimate:** 12 hours
- **Dependencies:** Task 1.3, Task 2.1
- **Files to create:**
  - `backend/engine/ai/turn_ai.py`
  - `backend/engine/ai/strategies/basic_strategy.py`

**Task 2.3: Disconnect During Turn Phase**
- [ ] Detect when current player disconnects
- [ ] Start AI takeover timer
- [ ] Implement AI turn execution
- [ ] Broadcast AI action events
- [ ] Update game state properly
- **Estimate:** 10 hours
- **Dependencies:** Task 2.1, Task 2.2
- **Files to modify:**
  - `backend/engine/state_machine/states/turn_state.py`

#### Frontend Tasks (Priority: High)

**Task 2.4: Turn Timer UI**
- [ ] Create countdown timer component
- [ ] Add timer to active player indicator
- [ ] Implement timer animations
- [ ] Add audio alerts for low time
- [ ] Handle timer expiration UI
- **Estimate:** 8 hours
- **Dependencies:** Task 1.5
- **Files to create:**
  - `frontend/src/components/TurnTimer.tsx`
  - `frontend/src/components/TimerBar.tsx`

**Task 2.5: AI Player Indicators**
- [ ] Add AI badge to player avatars
- [ ] Create "AI thinking" animation
- [ ] Show AI decision notifications
- [ ] Update player list with AI status
- [ ] Add AI difficulty display
- **Estimate:** 6 hours
- **Dependencies:** Task 1.4
- **Files to modify:**
  - `frontend/src/components/PlayerAvatar.tsx`
  - `frontend/src/components/PlayerList.tsx`

---

### Week 3: Phase-Specific Handling (Part 1)

#### Backend Tasks (Priority: High)

**Task 3.1: Preparation Phase Disconnect Handling**
- [ ] Handle disconnect during card dealing
- [ ] Auto-vote logic for weak hand decisions
- [ ] Implement vote timeout system
- [ ] Continue game flow smoothly
- [ ] Test edge cases
- **Estimate:** 10 hours
- **Dependencies:** Week 2 backend tasks
- **Files to modify:**
  - `backend/engine/state_machine/states/preparation_state.py`

**Task 3.2: AI Weak Hand Decision**
- [ ] Analyze hand strength algorithm
- [ ] Implement AI weak hand voting
- [ ] Add configurable AI aggressiveness
- [ ] Test various hand scenarios
- [ ] Document AI decision logic
- **Estimate:** 8 hours
- **Dependencies:** Task 1.3, Task 3.1
- **Files to create:**
  - `backend/engine/ai/preparation_ai.py`

**Task 3.3: Declaration Phase Disconnect Handling**
- [ ] Detect disconnect during declaration
- [ ] Implement declaration timeout
- [ ] Start AI declaration timer
- [ ] Handle partial declarations
- [ ] Maintain declaration order
- **Estimate:** 10 hours
- **Dependencies:** Week 2 backend tasks
- **Files to modify:**
  - `backend/engine/state_machine/states/declaration_state.py`

#### Frontend Tasks (Priority: High)

**Task 3.4: Disconnect Notifications**
- [ ] Create disconnect banner component
- [ ] Add player disconnect toasts
- [ ] Show reconnection countdown
- [ ] Implement notification queue
- [ ] Add notification preferences
- **Estimate:** 8 hours
- **Dependencies:** Week 2 frontend tasks
- **Files to create:**
  - `frontend/src/components/DisconnectBanner.tsx`
  - `frontend/src/components/NotificationToast.tsx`

---

### Week 4: Phase-Specific Handling (Part 2) & Testing

#### Backend Tasks (Priority: High)

**Task 4.1: AI Declaration Logic**
- [ ] Implement hand analysis for declarations
- [ ] Create declaration strategy patterns
- [ ] Add bluffing logic for hard AI
- [ ] Test declaration distributions
- [ ] Fine-tune AI parameters
- **Estimate:** 12 hours
- **Dependencies:** Task 3.3
- **Files to create:**
  - `backend/engine/ai/declaration_ai.py`
  - `backend/engine/ai/strategies/declaration_strategy.py`

**Task 4.2: Scoring Phase Continuity**
- [ ] Ensure scoring continues with disconnected players
- [ ] Handle score animation timing
- [ ] Manage round transition with AI players
- [ ] Test multi-round scenarios
- [ ] Document scoring edge cases
- **Estimate:** 6 hours
- **Dependencies:** Previous backend tasks
- **Files to modify:**
  - `backend/engine/state_machine/states/scoring_state.py`

**Task 4.3: Reconnection Handler**
- [ ] Implement reconnection detection
- [ ] Create state restoration logic
- [ ] Handle mid-action reconnections
- [ ] Sync game state to reconnected player
- [ ] Test various reconnection timings
- **Estimate:** 10 hours
- **Dependencies:** All previous backend tasks
- **Files to create:**
  - `backend/api/websocket/reconnection_handler.py`

#### QA Tasks (Priority: Critical)

**Task 4.4: Integration Testing Suite**
- [ ] Create disconnect simulation tests
- [ ] Test each phase disconnect scenario
- [ ] Verify AI decision consistency
- [ ] Test reconnection in all phases
- [ ] Create automated test runner
- **Estimate:** 16 hours
- **Dependencies:** All previous tasks
- **Files to create:**
  - `backend/tests/test_disconnect_handling.py`
  - `backend/tests/test_ai_decisions.py`

---

### Week 5: Advanced Features

#### Backend Tasks (Priority: Medium)

**Task 5.1: Host Migration System**
- [ ] Implement host selection algorithm
- [ ] Create host migration protocol
- [ ] Handle host privileges transfer
- [ ] Update room management
- [ ] Test edge cases
- **Estimate:** 10 hours
- **Dependencies:** Basic disconnect handling
- **Files to modify:**
  - `backend/api/websocket/room_manager.py`
  - `backend/models/room.py`

**Task 5.2: Message Queue for Disconnected Players**
- [ ] Create message buffer system
- [ ] Implement message replay on reconnect
- [ ] Handle message expiration
- [ ] Test buffer overflow scenarios
- [ ] Add message priority system
- **Estimate:** 8 hours
- **Dependencies:** Task 4.3
- **Files to create:**
  - `backend/api/websocket/message_queue.py`

**Task 5.3: Spectator Mode**
- [ ] Create spectator player type
- [ ] Implement view-only permissions
- [ ] Handle late reconnection as spectator
- [ ] Add spectator UI elements
- [ ] Test spectator interactions
- **Estimate:** 8 hours
- **Dependencies:** Task 4.3
- **Files to modify:**
  - `backend/engine/player.py`
  - `backend/api/websocket/handlers.py`

#### Frontend Tasks (Priority: Medium)

**Task 5.4: Host Migration UI**
- [ ] Create host crown indicator
- [ ] Add host change notifications
- [ ] Update room controls for new host
- [ ] Implement smooth transition effects
- [ ] Test host UI permissions
- **Estimate:** 6 hours
- **Dependencies:** Task 5.1
- **Files to modify:**
  - `frontend/src/components/RoomControls.tsx`
  - `frontend/src/components/PlayerList.tsx`

**Task 5.5: Reconnection UI Flow**
- [ ] Create reconnection screen
- [ ] Show game state during reconnect
- [ ] Implement progress indicators
- [ ] Add reconnection error handling
- [ ] Test various network conditions
- **Estimate:** 8 hours
- **Dependencies:** Task 4.3
- **Files to create:**
  - `frontend/src/components/ReconnectionScreen.tsx`

---

### Week 6: Polish, Testing & Documentation

#### Backend Tasks (Priority: Medium)

**Task 6.1: Performance Optimization**
- [ ] Profile disconnect handling code
- [ ] Optimize AI decision algorithms
- [ ] Reduce message broadcasting overhead
- [ ] Implement connection pooling
- [ ] Add performance metrics
- **Estimate:** 8 hours
- **Dependencies:** All features complete
- **Files to modify:** Various

**Task 6.2: Configuration System**
- [ ] Add configurable timeouts
- [ ] Create room-specific settings
- [ ] Implement AI difficulty per room
- [ ] Add feature flags
- [ ] Create admin controls
- **Estimate:** 6 hours
- **Dependencies:** All features complete
- **Files to create:**
  - `backend/config/disconnect_settings.py`

#### Frontend Tasks (Priority: Medium)

**Task 6.3: UI Polish**
- [ ] Refine disconnect animations
- [ ] Improve notification styling
- [ ] Add accessibility features
- [ ] Implement responsive design fixes
- [ ] Create loading states
- **Estimate:** 10 hours
- **Dependencies:** All UI components complete
- **Files to modify:** Various components

**Task 6.4: Error Handling UI**
- [ ] Create error boundary components
- [ ] Add graceful degradation
- [ ] Implement retry mechanisms
- [ ] Show helpful error messages
- [ ] Test error scenarios
- **Estimate:** 6 hours
- **Dependencies:** All features complete
- **Files to create:**
  - `frontend/src/components/ErrorBoundary.tsx`

#### QA & Documentation Tasks (Priority: High)

**Task 6.5: End-to-End Testing**
- [ ] Create E2E test scenarios
- [ ] Test on various devices
- [ ] Simulate poor network conditions
- [ ] Verify cross-browser compatibility
- [ ] Create regression test suite
- **Estimate:** 12 hours
- **Dependencies:** All features complete

**Task 6.6: Documentation**
- [ ] Update API documentation
- [ ] Create disconnect handling guide
- [ ] Document AI behavior
- [ ] Add troubleshooting section
- [ ] Create video demos
- **Estimate:** 8 hours
- **Dependencies:** All features complete

---

## Dependencies Matrix

### Critical Path Dependencies
1. **Connection Tracking (1.1)** → All disconnect detection features
2. **AI Framework (1.3)** → All AI decision features
3. **Turn Timer (2.1)** → Turn-based disconnect handling
4. **WebSocket Events (1.5)** → All frontend disconnect features

### Backend Dependencies
- State machine modifications depend on AI implementation
- Host migration depends on room manager updates
- Message queue depends on reconnection handler

### Frontend Dependencies
- All UI components depend on connection status store
- Disconnect notifications depend on WebSocket events
- Host migration UI depends on backend implementation

---

## Risk Mitigation

### Technical Risks
1. **WebSocket Stability**
   - Mitigation: Implement heartbeat system
   - Fallback: HTTP polling for critical updates

2. **AI Performance**
   - Mitigation: Pre-calculate common scenarios
   - Fallback: Simple random decisions

3. **State Synchronization**
   - Mitigation: Implement state versioning
   - Fallback: Force full state refresh

### Schedule Risks
1. **AI Complexity**
   - Buffer: Additional week for AI tuning
   - Option: Ship with basic AI, enhance later

2. **Testing Coverage**
   - Mitigation: Automated testing from week 1
   - Buffer: Dedicated QA week

---

## Success Criteria

### Week 1 Deliverables
- [ ] Connection tracking operational
- [ ] Basic AI framework ready
- [ ] UI shows connection status

### Week 2 Deliverables
- [ ] Turn timeouts working
- [ ] AI can make basic turns
- [ ] Timer UI implemented

### Week 3-4 Deliverables
- [ ] All phases handle disconnects
- [ ] AI makes reasonable decisions
- [ ] Notifications working smoothly

### Week 5 Deliverables
- [ ] Host migration functional
- [ ] Reconnection working reliably
- [ ] Spectator mode available

### Week 6 Deliverables
- [ ] All tests passing
- [ ] Performance acceptable
- [ ] Documentation complete

---

## Team Assignments

### Backend Developer
- Weeks 1-2: Core infrastructure and AI framework
- Weeks 3-4: Phase-specific implementations
- Week 5: Advanced features
- Week 6: Optimization and support

### Frontend Developer
- Week 1: Connection UI components
- Weeks 2-3: Timer and notification UI
- Weeks 4-5: Reconnection flows
- Week 6: Polish and error handling

### QA Engineer
- Weeks 1-3: Test planning and unit tests
- Week 4: Integration testing
- Weeks 5-6: E2E testing and documentation

---

## Notes for Project Management Tools

### Jira/Trello Setup
1. Create epic: "Disconnect Handling System"
2. Create sprints for each week
3. Add tasks with estimates and dependencies
4. Set up automation for status updates
5. Create dashboard for progress tracking

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