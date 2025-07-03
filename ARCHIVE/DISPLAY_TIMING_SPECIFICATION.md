# Display Timing Specification

**Date**: 2025-06-30  
**Branch**: event-driven  
**Status**: MANDATORY IMPLEMENTATION REQUIREMENT

## 🎯 Critical Implementation Requirement

**MANDATORY APPROACH: Frontend-Driven Display Timing**

All display timing (turn results, scoring displays, etc.) MUST be handled by the frontend. The backend MUST NOT use `asyncio.sleep()` or any delays for display purposes.

## ❌ PROHIBITED Backend Patterns

**These patterns are FORBIDDEN in the event-driven implementation:**

```python
# ❌ FORBIDDEN: Backend display delays
async def handle_turn_completion(self):
    # Process turn logic
    await self._process_turn()
    
    # ❌ FORBIDDEN: Backend waiting for display
    await asyncio.sleep(7.0)  # NEVER DO THIS
    
    # ❌ FORBIDDEN: Display flags in logic
    self.display_delay_complete = False
    asyncio.create_task(self._display_delay())  # NEVER DO THIS
    
    # ❌ FORBIDDEN: Logic waiting for display
    while not self.display_delay_complete:
        await asyncio.sleep(0.1)  # NEVER DO THIS

# ❌ FORBIDDEN: Display delay methods in state classes
async def _start_display_delay(self):
    await asyncio.sleep(7.0)
    self.display_delay_complete = True

# ❌ FORBIDDEN: Timer-based state transitions
async def check_transition_conditions(self):
    if self.scores_calculated and self.display_delay_complete:  # WRONG
        return GamePhase.PREPARATION
```

**Why These Are Forbidden:**
- Creates race conditions between timers and polling
- Blocks game logic unnecessarily
- Causes frontend delays and poor UX
- Makes testing difficult
- Violates event-driven principles

## ✅ MANDATORY Backend Pattern

**This is the ONLY acceptable backend approach:**

```python
class EventDrivenStateMachine:
    async def handle_turn_completion(self, turn_data: Dict):
        """CORRECT: Immediate logic + frontend display delegation"""
        
        # 1. ✅ IMMEDIATE: Process all game logic (NO DELAYS)
        winner = await self._determine_turn_winner(turn_data)
        await self._transfer_pieces_to_winner(winner, turn_data["pieces"])
        next_state = self._determine_next_state()
        
        # 2. ✅ IMMEDIATE: Broadcast results with display metadata
        await self.broadcast_event("turn_completed", {
            # Game data
            "winner": winner.name,
            "turn_results": self._get_turn_results(),
            
            # Frontend display instructions (NOT backend timing)
            "display": {
                "type": "turn_results",
                "show_for_seconds": 7.0,
                "auto_advance": True,
                "can_skip": True,
                "next_phase": next_state.value
            },
            
            # Logic status
            "logic_complete": True,
            "immediate": True
        })
        
        # 3. ✅ IMMEDIATE: Transition backend state
        await self._immediate_transition_to(next_state, "Turn completed")
        
        # ✅ DONE: Backend processing complete
        # Frontend handles all display timing independently

    async def handle_scoring_completion(self, scores: Dict):
        """CORRECT: Immediate scoring + frontend display delegation"""
        
        # 1. ✅ IMMEDIATE: Calculate scores and check win condition
        final_scores = await self._calculate_round_scores(scores)
        game_complete = await self._check_win_condition(final_scores)
        next_state = GamePhase.GAME_END if game_complete else GamePhase.PREPARATION
        
        # 2. ✅ IMMEDIATE: Broadcast with frontend instructions
        await self.broadcast_event("scoring_completed", {
            "scores": final_scores,
            "game_complete": game_complete,
            
            # Frontend display instructions
            "display": {
                "type": "scoring_display", 
                "show_for_seconds": 7.0,
                "auto_advance": True,
                "can_skip": True,
                "next_phase": next_state.value
            },
            
            "logic_complete": True,
            "immediate": True
        })
        
        # 3. ✅ IMMEDIATE: Transition backend state  
        await self._immediate_transition_to(next_state, "Scoring complete")
```

## ✅ MANDATORY Frontend Implementation

**Frontend MUST implement display timing control:**

```javascript
class FrontendDisplayManager {
    constructor(gameEventManager) {
        this.gameEventManager = gameEventManager;
        this.activeDisplays = new Map();
        this.setupMandatoryEventHandlers();
    }
    
    setupMandatoryEventHandlers() {
        // ✅ REQUIRED: Handle backend events with frontend timing
        this.gameEventManager.on('turn_completed', (data) => {
            this.handleTurnResults(data);
        });
        
        this.gameEventManager.on('scoring_completed', (data) => {
            this.handleScoringDisplay(data);  
        });
    }
    
    handleTurnResults(data) {
        // ✅ REQUIRED: Show results immediately
        this.renderTurnResultsPage(data.turn_results);
        
        // ✅ REQUIRED: Frontend controls timing (NOT backend)
        const displayConfig = data.display;
        const displayTimer = setTimeout(() => {
            this.advanceToNextPhase(displayConfig.next_phase);
        }, displayConfig.show_for_seconds * 1000);
        
        // ✅ REQUIRED: Store for user control
        const displayId = `turn_results_${Date.now()}`;
        this.activeDisplays.set(displayId, {
            timer: displayTimer,
            config: displayConfig,
            startTime: Date.now()
        });
        
        // ✅ REQUIRED: Add skip functionality
        if (displayConfig.can_skip) {
            this.addSkipButton(displayId);
        }
    }
    
    handleScoringDisplay(data) {
        // ✅ REQUIRED: Show scoring immediately
        this.renderScoringPage(data.scores);
        
        // ✅ REQUIRED: Frontend timing control
        const displayConfig = data.display;
        const displayTimer = setTimeout(() => {
            this.advanceToNextPhase(displayConfig.next_phase);
        }, displayConfig.show_for_seconds * 1000);
        
        const displayId = `scoring_display_${Date.now()}`;
        this.activeDisplays.set(displayId, {
            timer: displayTimer,
            config: displayConfig,
            startTime: Date.now()
        });
        
        if (displayConfig.can_skip) {
            this.addSkipButton(displayId);
        }
    }
    
    skipCurrentDisplay() {
        // ✅ REQUIRED: Allow users to skip timing
        for (const [displayId, display] of this.activeDisplays) {
            if (display.config.can_skip) {
                clearTimeout(display.timer);
                this.advanceToNextPhase(display.config.next_phase);
                this.activeDisplays.delete(displayId);
                break;
            }
        }
    }
    
    addSkipButton(displayId) {
        // ✅ REQUIRED: User control over display timing
        const skipButton = document.createElement('button');
        skipButton.textContent = 'Skip (Space)';
        skipButton.onclick = () => this.skipCurrentDisplay();
        
        // Add keyboard shortcut
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.activeDisplays.has(displayId)) {
                e.preventDefault();
                this.skipCurrentDisplay();
            }
        });
        
        this.gameUI.addSkipButton(skipButton);
    }
}
```

## 🧪 MANDATORY Testing Requirements

**Backend tests MUST verify no display delays:**

```python
class TestNoBackendDisplayDelays:
    async def test_turn_completion_immediate(self):
        """VERIFY: Turn completion processes immediately"""
        
        sm = EventDrivenStateMachine()
        
        # Time the entire turn completion
        start_time = time.perf_counter()
        result = await sm.handle_turn_completion(test_turn_data)
        elapsed = time.perf_counter() - start_time
        
        # ✅ MUST complete in <10ms (no display delays)
        assert elapsed < 0.01, f"Turn completion too slow: {elapsed:.3f}s"
        assert result["immediate"] == True
        assert "display" in result  # Has frontend instructions
        assert result["logic_complete"] == True
    
    async def test_scoring_completion_immediate(self):
        """VERIFY: Scoring completion processes immediately"""
        
        sm = EventDrivenStateMachine()
        
        start_time = time.perf_counter()
        result = await sm.handle_scoring_completion(test_scores)
        elapsed = time.perf_counter() - start_time
        
        # ✅ MUST complete in <10ms (no display delays)
        assert elapsed < 0.01, f"Scoring completion too slow: {elapsed:.3f}s"
        assert result["immediate"] == True
        assert result["logic_complete"] == True
    
    async def test_no_asyncio_sleep_in_states(self):
        """VERIFY: No asyncio.sleep() used for display timing"""
        
        # ✅ MUST NOT find any display-related asyncio.sleep()
        import ast
        import os
        
        for state_file in os.listdir("backend/engine/state_machine/states/"):
            if state_file.endswith(".py"):
                with open(f"backend/engine/state_machine/states/{state_file}") as f:
                    tree = ast.parse(f.read())
                
                # Check for forbidden patterns
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if hasattr(node.func, 'attr') and node.func.attr == 'sleep':
                            # Found asyncio.sleep() - check context
                            assert False, f"Found asyncio.sleep() in {state_file} - FORBIDDEN for display timing"
    
    async def test_no_display_flags_in_logic(self):
        """VERIFY: No display completion flags in state logic"""
        
        sm = EventDrivenStateMachine()
        
        # ✅ MUST NOT have display-related flags
        forbidden_attributes = [
            'display_delay_complete',
            'display_timer',
            'show_results_timer',
            'scoring_display_complete'
        ]
        
        for state in sm.states.values():
            for attr in forbidden_attributes:
                assert not hasattr(state, attr), f"Forbidden display attribute {attr} found in {state.__class__.__name__}"
```

**Frontend tests MUST verify display control:**

```javascript
class TestFrontendDisplayControl {
    test('frontend controls turn results timing', async () => {
        const displayManager = new FrontendDisplayManager(mockEventManager);
        
        const turnData = {
            turn_results: { winner: 'player1' },
            display: {
                show_for_seconds: 7.0,
                can_skip: true,
                next_phase: 'scoring'
            }
        };
        
        // ✅ MUST show results immediately
        const startTime = Date.now();
        displayManager.handleTurnResults(turnData);
        
        // ✅ MUST have active display
        expect(displayManager.activeDisplays.size).toBe(1);
        
        // ✅ MUST advance after timeout
        await new Promise(resolve => setTimeout(resolve, 7100));
        expect(displayManager.activeDisplays.size).toBe(0);
    });
    
    test('user can skip display timing', () => {
        const displayManager = new FrontendDisplayManager(mockEventManager);
        
        const turnData = {
            turn_results: { winner: 'player1' },
            display: { can_skip: true, next_phase: 'scoring' }
        };
        
        displayManager.handleTurnResults(turnData);
        expect(displayManager.activeDisplays.size).toBe(1);
        
        // ✅ MUST allow skip
        displayManager.skipCurrentDisplay();
        expect(displayManager.activeDisplays.size).toBe(0);
    });
}
```

## 📋 Implementation Checklist

**Backend Requirements:**
- [ ] ✅ Remove ALL `asyncio.sleep()` from state classes
- [ ] ✅ Remove ALL display delay flags (`display_delay_complete`, etc.)
- [ ] ✅ Remove ALL display timer methods (`_start_display_delay`, etc.)
- [ ] ✅ Implement immediate logic processing for turn completion
- [ ] ✅ Implement immediate logic processing for scoring completion
- [ ] ✅ Add display metadata to all event broadcasts
- [ ] ✅ Ensure state transitions happen immediately after logic

**Frontend Requirements:**
- [ ] ✅ Implement `FrontendDisplayManager` class
- [ ] ✅ Handle `turn_completed` events with frontend timing
- [ ] ✅ Handle `scoring_completed` events with frontend timing
- [ ] ✅ Add skip functionality for all display phases
- [ ] ✅ Add keyboard shortcuts for skipping
- [ ] ✅ Implement auto-advance timers in frontend
- [ ] ✅ Clean up display timers properly

**Testing Requirements:**
- [ ] ✅ Verify backend processing <10ms for all events
- [ ] ✅ Verify no `asyncio.sleep()` in state machine
- [ ] ✅ Verify no display flags in backend logic
- [ ] ✅ Verify frontend display timing works correctly
- [ ] ✅ Verify skip functionality works
- [ ] ✅ Verify auto-advance timing works

## 🚨 Critical Success Criteria

**MUST ACHIEVE:**
1. **Backend Speed**: All game logic processing <10ms
2. **No Backend Delays**: Zero `asyncio.sleep()` for display purposes
3. **Frontend Control**: All display timing controlled by frontend
4. **User Control**: Users can skip display phases
5. **Immediate Logic**: Game state transitions happen immediately

**MUST AVOID:**
1. **Backend Display Delays**: Any backend waiting for display timing
2. **Race Conditions**: Timer conflicts between backend and frontend
3. **Blocking Logic**: Game logic waiting for UI timing
4. **Poor UX**: Delays in responding to user actions

---

**Implementation Rule**: Backend processes logic immediately and provides display metadata. Frontend controls all timing and display duration. This separation ensures optimal performance and user experience while eliminating race conditions.