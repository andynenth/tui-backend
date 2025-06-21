# AI_CONTEXT.md - Project Overview & Index

## ⚠️ Start Here Instead
For daily work → **Read AI_WORKING_DOC.md**  
This file is just the overview and historical record.

## Project Status
- ✅ **Game is playable** - All features work end-to-end
- 🔧 **Adding structure** - State machine for phase management

## Project Overview
**Working** multiplayer board game using FastAPI (backend) and PixiJS (frontend).
- Core gameplay complete: rooms, turns, scoring, bots
- Real-time updates via WebSocket
- Target: 2-3 concurrent games (MVP), scaling to 5-10
- **Current Focus**: Formalizing architecture for stability

**Current Status: Architecture Design Phase** - Planning implementation, not fixing existing code.

## 🎯 Current Task
**Organizing existing code with formal state management**
- The game WORKS - rooms, gameplay, bots all function
- Now adding state machine to prevent phase violations
- See **AI_WORKING_DOC.md** for detailed plan and daily tasks

## Document Map

### 📋 Game Design (in Project Knowledge)
- **`Rules`** - Complete game rules, piece values, play types, scoring formulas
- **`Game Flow - Preparation Phase`** - Deal, weak hands, redeal logic, starter determination
- **`Game Flow - Declaration Phase`** - Declaration order, restrictions, validation
- **`Game Flow - Turn Phase`** - Turn sequence, play requirements, winner determination
- **`Game Flow - Scoring Phase`** - Score calculation, multipliers, win conditions

### 🔧 Development Planning
- **`AI_WORKING_DOC.md`** - Current sprint plan, daily workflow, implementation guide
- **`AI_CONTEXT.md`** - This file - project overview and index

### 🔧 Implementation Files
**Existing Code** (in project - may be restructured):
- **`README.md`** - Tech stack, installation, project structure
- **`backend/engine/rules.py`** - Game rule implementations (exists)
- **`backend/engine/ai.py`** - Bot AI logic (exists)
- **Other backend files** - Various game engine components

**Note**: File paths may change during restructuring. When working with code, provide current file versions.

## Current Architecture Decisions

### Design Challenges We're Addressing
These are the challenges our architecture is designed to prevent (not current bugs):
1. **Phase Violations**: Preventing bots from acting during wrong phases
2. **Race Conditions**: Handling simultaneous actions properly
3. **State Synchronization**: Keeping all clients in sync
4. **Complex Game Flow**: Managing multiple phases with specific rules

### 1. State Synchronization
**Decision: Full State Broadcasts** (changed from delta/patch)
- Send complete game state on every update
- Version numbers + SHA256 checksums for validation
- Automatic desync recovery on next broadcast

### 2. Phase Transitions
**Decision: Locked transition periods**
- Flow: PHASE_ACTIVE → PHASE_ENDING → TRANSITION_LOCKED → PHASE_ACTIVE
- Queue messages during transitions, validate after
- ~300-600ms transition durations

### 3. Edge Case Handling
- **In-flight messages**: Queue, then validate for new phase
- **Mid-transition reconnects**: Full state sync + 2-3s grace period
- **Bot actions**: Pause immediately, re-evaluate in new phase
- **Timer conflicts**: Disconnection timer overrides decision timer

## Implementation Status

### ✅ What's Working
- Complete game engine (rules, AI, scoring)
- Room system (create, join, host management)
- WebSocket real-time updates
- Bot players with AI
- Full game flow from lobby to scoring
- Frontend with PixiJS scenes

### 🔧 What Needs Organization
- **Phase Management** - Currently spread across multiple files
- **WebSocket Protocol** - Messages work but need standardization
- **Bot Timing** - Bots can act during wrong phases
- **Error Handling** - Needs consistent patterns

### 📅 Current Sprint (See AI_WORKING_DOC.md)
Week 1-2: Create formal state machine and protocol

## Key Principles
- **Server Authority**: Server state is always correct
- **Fail Safe**: Maintain game flow with safe defaults
- **Reference Source**: Game flow diagrams and Rules file are authoritative

## When to Read What

### For Game Mechanics
→ Read `Rules` and relevant `Game Flow - *` files

### For Technical Implementation
→ Check actual code files in `backend/` and `frontend/`

### For Architecture Decisions
→ This file contains the key decisions (full context in our chat history)

## Testing Strategy
- Unit tests for phase logic
- Integration tests for transitions
- Bot vs bot stress testing
- Network simulation with tc netem

## Next Steps
1. Design state machine based on game flow diagrams
2. Design WebSocket protocol for full state broadcasts
3. Implement phase transition engine with sub-states