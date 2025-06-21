# AI_WORKING_DOC.md - Liap Tui Development Guide
## 📖 How to Use This Document
**Start HERE for daily work.** This has everything needed for current tasks.
* AI_CONTEXT.md = Historical decisions (check only if confused about past choices)
* This doc = What to do NOW

⠀🎯 Quick Context
**Project**: Liap Tui multiplayer board game (FastAPI + PixiJS)**Status**: Core game WORKS. Refactoring to prevent bugs by design.**Current Task**: Replace scattered phase logic with state pattern architecture **Philosophy**: Don't fix bugs - make them impossible
## 📁 Essential Files to Check
Based on what you're working on:
- Game mechanics → Read Rules + Game Flow files
- Current implementation → Check backend/api/routes/routes.py
- Bot issues → Check backend/engine/bot_manager.py
- Project history → Check AI_CONTEXT.md (only if needed)
## 🏗️ Refactoring Goals (Prevention by Design)
**1** **Phase violations impossible** → State machine with strict transitions
**2** **Race conditions prevented** → Single source of truth + queued actions
**3** **Phase logic centralized** → All phase code in one place

⠀❌ Not "Fixing Bugs" But "Making Bugs Impossible"
The current code works but allows these issues. We're refactoring so they CAN'T happen.
## 🎯 Architectural Vision
Current Architecture:          Target Architecture:
┌─────────────────┐           ┌─────────────────┐
│ Scattered Logic │           │  State Machine  │
├─────────────────┤           ├─────────────────┤
│ routes.py       │           │ ┌─────────────┐ │
│ bot_manager.py  │    →      │ │ PhaseStates │ │
│ game.py         │           │ └─────────────┘ │
│ (phase checks   │           │ ┌─────────────┐ │
│  everywhere)    │           │ │ActionQueue  │ │
└─────────────────┘           │ └─────────────┘ │
                              └─────────────────┘
## 📊 Before & After Example
### Before (Current Code - Allows Bugs):
# routes.py
async def declare(player_name, value):
    if game.phase != "declaration":  # Bug possible!
        return error
    # declaration logic...

# bot_manager.py  
async def bot_action():
    if game.phase == "declaration":  # Duplicate check!
        # bot declaration...
    
# game.py
def process_action():
    if self.phase == "declaration":  # More duplication!
        # process...
### After (Refactored - Bugs Impossible):
class DeclarationState:
    """Can ONLY exist during declaration phase"""
    
    async def handle_player_action(self, action):
        # No phase check needed - we're IN declaration
        if action.type == "declare":
            return await self.process_declaration(action)
        # Invalid action for this state
        return InvalidActionError()

# Bot can't act in wrong phase - state doesn't exist!
# No duplicate checks - single source of truth!
# Race conditions impossible - queued actions!
## 🎯 Current Sprint (Weeks 1-2)
### Goal: Refactor to State Pattern Architecture
Transform scattered phase logic into a clean state machine that makes bugs impossible by design.
### Task 1: State Machine Design
# Goal: Make phase violations IMPOSSIBLE by design
class GameStateMachine:
    def __init__(self):
        self.current_state = None
        self.transition_lock = asyncio.Lock()
        
    async def transition(self, to_state):
        async with self.transition_lock:  # Prevents race conditions
            if not self.can_transition(to_state):
                raise InvalidTransition()  # Makes invalid transitions impossible
            
            # Queue all actions during transition
            await self.pause_all_actions()
            await self.exit_current_state()
            await self.enter_new_state(to_state)
            await self.resume_actions()

# Each state encapsulates ALL logic for that phase
class TurnState(GameState):
    def __init__(self):
        self.allowed_actions = ['play_pieces', 'timeout']
        
    async def handle_action(self, action):
        # Can ONLY handle turn actions - others impossible
        if action.type not in self.allowed_actions:
            return  # Ignore - not error
            
        return await self.process_turn_action(action)
### Task 2: WebSocket Protocol
// Standardize ALL messages to this format
{
  "version": "1.0",
  "type": "PHASE_TRANSITION|PLAYER_ACTION|GAME_UPDATE",
  "payload": {...},
  "timestamp": 1234567890,
  "sequence": 1
}
### Task 3: Phase Manager
# Complete refactoring example
class PhaseManager:
    def __init__(self):
        self.states = {
            'preparation': PreparationState(),
            'declaration': DeclarationState(),
            'turn': TurnState(),
            'scoring': ScoringState()
        }
        self.current_state = None
        self.action_queue = ActionQueue()
        
    async def handle_action(self, action):
        # ALL actions go through here - no direct access
        await self.action_queue.add(action)
        
    async def process_queue(self):
        # Single processor - no race conditions
        while action := await self.action_queue.get():
            await self.current_state.handle(action)
## 📋 Implementation Checklist
### Week 1: Architecture Foundation
* [ ] Design state pattern for phases
* [ ] Create abstract State base class
* [ ] Implement state transition logic
* [ ] Design action queue system
* [ ] Create phase state classes

⠀Week 2: Refactoring Integration
* [ ] Extract phase logic from routes.py → State classes
* [ ] Extract bot logic from bot_manager.py → State classes
* [ ] Replace all if phase == checks → State pattern
* [ ] Add transition locks to prevent races
* [ ] Test refactored architecture with bots

⠀Week 3-4: Solidify Architecture
* [ ] Add comprehensive state tests
* [ ] Implement state persistence
* [ ] Add monitoring to state transitions
* [ ] Performance test the new architecture
* [ ] Document the new patterns

⠀🚫 NOT Doing (Scope Limit)
* ❌ Tournaments
* ❌ Spectator mode
* ❌ Ranking system
* ❌ Payment/monetization
* ❌ Complex social features
* ❌ Fixing bugs in current code (we're replacing the architecture)
* ❌ Adding features before architecture is solid

⠀✅ Success Criteria
**1** **Architectural**: Phase violations impossible by design
**2** **Centralized**: All phase logic in state classes
**3** **Thread-safe**: Race conditions prevented by queuing
**4** **Clear boundaries**: Each state handles only its actions
**5** **Maintainable**: Easy to add new features without bugs

⠀💻 Refactoring Patterns
### Pattern 1: Impossible Invalid States
# OLD: Checking phase everywhere
if game.phase == 'declaration' and player.declared == 0:
    # Do declaration logic

# NEW: State pattern makes invalid states impossible
class DeclarationState:
    def on_enter(self):
        # Set up only what's valid for declaration
    
    def handle_action(self, action):
        # Can ONLY handle declaration actions
### Pattern 2: Centralized Phase Logic
# OLD: Phase logic scattered
# routes.py: if phase == 'turn'...
# bot_manager.py: if phase == 'turn'...
# game.py: if phase == 'turn'...

# NEW: Single source of truth
class TurnState:
    def can_play(self, player, pieces):
        # ALL turn validation here
    
    def execute_play(self, player, pieces):
        # ALL turn execution here
### Pattern 3: Action Queuing
# OLD: Race conditions from concurrent actions
async def handle_action(action):
    # Multiple actions can interfere
    if game.phase == "turn":  # Player A checks
        # Player B transitions to scoring here!
        game.process_turn()  # Wrong phase now!

# NEW: Queued execution prevents races
class ActionQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.processing = False
        
    async def add(self, action):
        await self.queue.put(action)
        if not self.processing:
            asyncio.create_task(self.process())
    
    async def process(self):
        self.processing = True
        while not self.queue.empty():
            action = await self.queue.get()
            # Sequential processing - no races!
            await self.state_machine.handle(action)
        self.processing = False
## 🔄 Daily Workflow
**1** **Start**: Read this doc + identify refactoring target
**2** **Analyze**: Find all code related to that phase/feature
**3** **Design**: Create state class for that logic
**4** **Refactor**: Move code into state pattern
**5** **Test**: Verify bugs now impossible
**6** **Document**: Update architecture docs

⠀🎮 Testing Commands
# Test state transitions
python test_state_machine.py --transitions

# Test action queuing (race conditions)
python test_concurrent_actions.py --players=4 --actions=100

# Test phase encapsulation
python test_phase_isolation.py --invalid-actions

# Full architecture test
python test_refactored_game.py --bots=4 --games=3
## 📝 Key Decisions Made
**1** **State Pattern Architecture** - Each phase is a state class
**2** **Action Queue** - All actions queued, processed sequentially
**3** **No Direct Phase Access** - Only through state machine
**4** **Full State Broadcasts** - Simpler than deltas
**5** **Refactor > Fix** - Replace problematic patterns entirely

⠀⚡ Architectural Solutions
**Bot acting in wrong phase?** → Move bot logic into state class → State class only exists during valid phase
**Race condition occurring?** → Add action to queue instead of direct execution → Process queue with single consumer
**Phase logic scattered?** → Find all if phase == statements → Move that logic to corresponding state class
**Complex phase transition?** → Break into: exit_state → transition → enter_state → Each step atomic and validated
**New feature needed?** → Add new state or extend existing state → No changes to core flow needed
## 💡 Why This Architecture Wins
### Makes Bugs Impossible
* Phase violations? State doesn't exist in wrong phase
* Race conditions? Sequential queue processing
* Invalid actions? State only handles its own actions

⠀Easier to Maintain
* Add feature? Extend a state class
* Fix bug? It's isolated to one state
* Understand flow? Read state transitions

⠀Better for Teams
* Clear boundaries between phases
* No stepping on each other's code
* Easy to test in isolation

⠀🎯 Remember
* **Working game exists** - preserve functionality
* **Refactor for prevention** - make bugs impossible, don't fix them
* **Architecture over patches** - solve root causes
* **Test constantly** - ensure refactoring doesn't break features
* **Incremental changes** - one pattern at a time

⠀
**Last Updated**: When starting new session **Next Review**: After State Machine architecture complete
