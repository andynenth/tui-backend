# Test Execution Plan: Redeal Decision Toggle Bug (REDEAL-001)

## Executive Summary

**Test Plan ID**: REDEAL-001-PLAN  
**Bug Report**: [REDEAL_DECISION_TOGGLE_BUG.md](../bug-reports/REDEAL_DECISION_TOGGLE_BUG.md)  
**Test Objective**: Validate fix for redeal decision toggle not appearing  
**Test Environment**: Playwright MCP + Local Development Server  
**Test Date**: 2025-01-31  

---

## Visual Evidence of Bug

### Current State (Bug Present)
![Bug Evidence Screenshot](../../playwright-mcp-output/redeal-bug-evidence.png)

**Screenshot Analysis**:
- ✅ **Phase**: "Preparation Phase" displayed correctly
- ✅ **Player Hand**: 8 pieces visible (General=14, Elephant=10, Soldiers=2, Advisor=11, Horse=5, Soldiers=1)
- ✅ **Weak Hand Detected**: Hand contains pieces ≤11, no piece >13 points
- ❌ **Missing UI**: **NO redeal decision buttons visible**
- ❌ **Missing Alert**: **NO "Weak Hand Detected" warning**

### Expected State (After Fix)
```
┌─────────────────────────────────────┐
│         Preparation Phase           │
│                                     │
│  ⚠️ Weak Hand Detected              │
│  No piece greater than 11 points.   │
│  Would you like to request a redeal?│
│                                     │
│  Warning: 2x penalty if you redeal! │
│                                     │
│  [Request Redeal] [Keep Hand]       │
│                                     │
│  [Player Hand: 8 pieces displayed]  │
└─────────────────────────────────────┘
```

---

## Test Evidence Collection

### Browser Console Evidence
From previous analysis, the following console logs confirm the bug:

```javascript
// ✅ EVENTS RECEIVED
[LOG] 🔍 [DEBUG] GameService received network event: weak_hands_found
[LOG] 🔍 [DEBUG] processGameEvent called with eventType: weak_hands_found {players: Array(1)}

// ✅ HAND DATA AVAILABLE  
[LOG] 🎴 PreparationUI received myHand: [8 pieces]
[LOG] 🎮 GameContainer: gameState.myHand length: 8

// ❌ UI STATE FLAGS NOT UPDATED
// Missing logs for: isMyHandWeak, isMyDecision calculations
// These should appear after weak_hands_found events
```

### Network Event Evidence
WebSocket messages show:
- `weak_hands_found` events are received
- Player data includes weak hand information
- No corresponding UI state updates

---

## Test Suite Organization

### 1. Unit Tests (`GameService.redeal.test.js`)
**Purpose**: Test the core bug fix in `handleWeakHandsFound` method

#### Test Categories:
```
├── Core Bug Fix Tests (T001-T005)
│   ├── T001: Calculate isMyHandWeak for weak hand
│   ├── T002: Calculate isMyHandWeak for strong hand  
│   ├── T003: Calculate isMyDecision in sequential mode
│   ├── T004: Calculate isMyDecision in simultaneous mode
│   └── T005: Calculate handValue and highestCardValue
├── Edge Cases (T006-T008)
│   ├── T006: Handle empty myHand gracefully
│   ├── T007: Handle missing playerName gracefully
│   └── T008: Handle malformed event data
├── Integration Tests (T009-T010)
│   ├── T009: Enable redeal UI for weak hand player
│   └── T010: Disable redeal UI for strong hand player
└── Regression Tests (T011-T012)
    ├── T011: Maintain existing functionality
    └── T012: Work correctly in non-preparation phases
```

**Execution Command**:
```bash
npm test -- GameService.redeal.test.js
```

### 2. Integration Tests (`redeal-decision.test.js`)
**Purpose**: Test UI component integration and rendering

#### Test Categories:
```
├── PreparationContent Rendering (I001-I005)
│   ├── I001: Render redeal UI for weak hand player
│   ├── I002: NOT render redeal UI for strong hand player
│   ├── I003: Handle redeal button clicks correctly
│   ├── I004: Show correct multiplier penalty warning
│   └── I005: Handle simultaneous mode correctly
├── Props Passing (I006)
│   └── I006: Pass all props correctly to PreparationContent
├── GameContainer Props (I007-I008)
│   ├── I007: Calculate preparation props with fixed UI flags
│   └── I008: Handle empty preparation props gracefully
├── Error Handling (I009)
│   └── I009: Handle rendering errors gracefully
└── Animation Integration (I010-I011)
    ├── I010: Show redeal UI after dealing animation
    └── I011: Handle redeal animation correctly
```

**Execution Command**:
```bash
npm test -- redeal-decision.test.js
```

### 3. End-to-End Tests (`redeal-workflow.test.js`)
**Purpose**: Test complete user workflow with real browser

#### Test Categories:
```
├── Complete Workflows (E001-E002)
│   ├── E001: Accept redeal workflow
│   └── E002: Decline redeal workflow
├── Multiplayer Tests (E003)
│   └── E003: Sequential mode with multiple players
├── Debug & Performance (E004-E005)
│   ├── E004: Debug data collection
│   └── E005: Performance testing
```

**Execution Command**:
```bash
npx playwright test redeal-workflow.test.js
```

---

## Test Execution Strategy

### Phase 1: Pre-Fix Validation (Prove Bug Exists)
**Objective**: Collect evidence that bug exists before applying fix

```bash
# 1. Run current system with debug logging
npm start &
npm run test:e2e:debug

# 2. Execute debug script in browser
node scripts/debug-redeal-bug.js

# 3. Collect evidence
# - Screenshots showing missing UI
# - Console logs showing missing state updates
# - Network event logs showing received events
```

**Expected Results**:
- ❌ Unit tests FAIL (isMyHandWeak, isMyDecision not calculated)
- ❌ Integration tests FAIL (redeal UI not rendered)
- ❌ E2E tests FAIL (no redeal buttons visible)

### Phase 2: Fix Implementation
**Objective**: Apply the fix to `handleWeakHandsFound` method

```typescript
// File: frontend/src/services/GameService.ts
// Lines: 1232-1238 (BEFORE)
private handleWeakHandsFound(state: GameState, data: any): GameState {
  return {
    ...state,
    weakHands: data.weak_hands || [],
    currentWeakPlayer: data.current_weak_player || null,
  };
}

// Lines: 1232-1260 (AFTER - FIXED)
private handleWeakHandsFound(state: GameState, data: any): GameState {
  console.log('🔍 [DEBUG] handleWeakHandsFound received:', data);
  
  const newState = {
    ...state,
    weakHands: data.weak_hands || [],
    currentWeakPlayer: data.current_weak_player || null,
  };

  // ✅ FIX: Calculate weak hand UI state (same as handlePhaseChange)
  if (newState.myHand.length > 0) {
    newState.isMyHandWeak = this.calculateWeakHand(newState.myHand);
    newState.handValue = this.calculateHandValue(newState.myHand);
    newState.highestCardValue = this.calculateHighestCardValue(newState.myHand);
  }

  // ✅ FIX: Determine if it's my decision
  if (newState.simultaneousMode && newState.playerName) {
    newState.isMyDecision = newState.weakPlayersAwaiting.includes(
      newState.playerName
    );
  } else if (newState.currentWeakPlayer && newState.playerName) {
    newState.isMyDecision = newState.currentWeakPlayer === newState.playerName;
  }

  console.log('🔍 [DEBUG] handleWeakHandsFound calculated UI state:');
  console.log('  - isMyHandWeak:', newState.isMyHandWeak);
  console.log('  - isMyDecision:', newState.isMyDecision);

  return newState;
}
```

### Phase 3: Post-Fix Validation (Prove Bug Fixed)
**Objective**: Verify all tests pass after applying fix

```bash
# 1. Run all test suites
npm test
npm run test:integration  
npm run test:e2e

# 2. Manual verification
npm start &
# Navigate to preparation phase and verify redeal UI appears

# 3. Performance testing
npm run test:performance
```

**Expected Results**:
- ✅ Unit tests PASS (state calculations work correctly)
- ✅ Integration tests PASS (UI renders properly)
- ✅ E2E tests PASS (full workflow functional)

---

## Test Data & Mock States

### Mock Game States for Testing

```javascript
// Weak Hand State (Should show redeal UI)
const WEAK_HAND_STATE = {
  phase: 'preparation',
  playerName: 'TestPlayer',
  myHand: [
    { kind: 'SOLDIER', color: 'red', value: 2 },
    { kind: 'SOLDIER', color: 'black', value: 1 },
    { kind: 'ADVISOR', color: 'red', value: 8 },
    { kind: 'HORSE', color: 'black', value: 5 },
    { kind: 'CANNON', color: 'red', value: 7 },
    { kind: 'CHARIOT', color: 'black', value: 9 },
    { kind: 'ELEPHANT', color: 'red', value: 6 },
    { kind: 'GENERAL', color: 'black', value: 3 },
  ],
  weakHands: ['TestPlayer'],
  currentWeakPlayer: 'TestPlayer',
  // BUG: These should be true but are false
  isMyHandWeak: false, // ❌ Should be true  
  isMyDecision: false, // ❌ Should be true
};

// Strong Hand State (Should NOT show redeal UI)
const STRONG_HAND_STATE = {
  phase: 'preparation',
  playerName: 'TestPlayer',
  myHand: [
    { kind: 'GENERAL', color: 'red', value: 14 },
    { kind: 'ADVISOR', color: 'black', value: 11 },
    { kind: 'ELEPHANT', color: 'red', value: 10 },
    // ... more strong pieces
  ],
  weakHands: ['Bot2'], // TestPlayer not in weak hands
  currentWeakPlayer: 'Bot2',
  isMyHandWeak: false, // ✅ Correct
  isMyDecision: false, // ✅ Correct
};
```

### Network Event Simulation

```javascript
// Simulate weak_hands_found event
const WEAK_HANDS_FOUND_EVENT = {
  eventType: 'weak_hands_found',
  roomId: 'TEST_ROOM',
  data: {
    weak_hands: ['TestPlayer', 'Bot3'],
    current_weak_player: 'TestPlayer',
    round_number: 1,
    players: ['TestPlayer', 'Bot2', 'Bot3', 'Bot4']
  }
};
```

---

## Success Criteria

### Functional Criteria
- ✅ Redeal decision UI appears for players with weak hands
- ✅ UI shows correct penalty multiplier warning
- ✅ Accept/Decline buttons function correctly  
- ✅ Works in both sequential and simultaneous modes
- ✅ UI disappears after player makes decision
- ✅ Game continues correctly after redeal decision

### Technical Criteria
- ✅ `isMyHandWeak` calculated correctly in `handleWeakHandsFound`
- ✅ `isMyDecision` calculated correctly in `handleWeakHandsFound`
- ✅ `handValue` and `highestCardValue` updated appropriately
- ✅ No performance regression (< 50ms additional processing time)
- ✅ All existing functionality preserved
- ✅ Error handling maintains robustness

### Test Coverage Criteria
- ✅ Unit test coverage > 95% for modified methods
- ✅ Integration test coverage for all UI scenarios
- ✅ E2E test coverage for complete user workflows
- ✅ Edge case coverage (empty hands, missing data, etc.)

---

## Risk Assessment & Mitigation

### High-Risk Areas
1. **State Synchronization**: Multiple handlers updating same flags
2. **Performance Impact**: Additional calculations on every weak_hands_found event
3. **Backward Compatibility**: Changes to core game state management

### Mitigation Strategies
1. **Comprehensive Testing**: Full test coverage as outlined above
2. **Gradual Rollout**: Feature flag for controlled deployment
3. **Monitoring**: Debug logging and performance metrics
4. **Rollback Plan**: Easy revert to previous version if issues arise

---

## Execution Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| **Pre-Fix Testing** | 1 hour | Run existing tests, collect bug evidence |
| **Fix Implementation** | 1 hour | Code changes, debug logging, local testing |
| **Unit Testing** | 1 hour | Run and validate all unit tests |
| **Integration Testing** | 1 hour | Component integration validation |
| **E2E Testing** | 2 hours | Full workflow testing with Playwright |
| **Performance Testing** | 30 min | Benchmark and validate performance |
| **Documentation** | 30 min | Update docs and create deployment notes |
| **Total** | **7 hours** | Complete test execution and validation |

---

## Deliverables

### Test Artifacts
1. **Test Results Report**: Pass/fail status for all test categories
2. **Performance Benchmark**: Before/after performance comparison
3. **Bug Evidence Package**: Screenshots, logs, and debug data
4. **Coverage Report**: Code coverage metrics for modified areas

### Code Artifacts  
1. **Fixed GameService.ts**: Updated `handleWeakHandsFound` method
2. **Test Suite**: Complete unit, integration, and E2E tests
3. **Debug Scripts**: Reusable debugging and monitoring tools
4. **Documentation**: Updated bug report with resolution details

### Deployment Artifacts
1. **Deployment Guide**: Step-by-step fix application
2. **Rollback Plan**: Instructions for reverting changes if needed
3. **Monitoring Setup**: Debug logging and error tracking
4. **User Communication**: Release notes explaining the fix

---

This test plan provides comprehensive validation that the redeal decision toggle bug is fixed correctly and completely, with full evidence collection and risk mitigation.