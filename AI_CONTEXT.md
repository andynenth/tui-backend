# AI_CONTEXT.md - Liap Tui Project Index

## ⚠️ READ THIS FIRST
This project has basic game components but needs architecture design for multiplayer functionality. We're not fixing bugs - we're designing how to build the multiplayer system.

## Project Overview
Multiplayer board game implementation using FastAPI (backend) and PixiJS (frontend).
Target: 2-3 concurrent games (MVP), scaling to 5-10.

**Current Status: Architecture Design Phase** - Planning implementation, not fixing existing code.

## 🎯 Current Task
**We are DESIGNING the state machine architecture**, not debugging existing code.
- The game engine has basic components (rules.py, ai.py)
- Now designing how to integrate everything with proper phase management
- Next: Create state machine design, then WebSocket protocol

## Document Map

### 📋 Game Design (in Project Knowledge)
- **`Rules`** - Complete game rules, piece values, play types, scoring formulas
- **`Game Flow - Preparation Phase`** - Deal, weak hands, redeal logic, starter determination
- **`Game Flow - Declaration Phase`** - Declaration order, restrictions, validation
- **`Game Flow - Turn Phase`** - Turn sequence, play requirements, winner determination
- **`Game Flow - Scoring Phase`** - Score calculation, multipliers, win conditions

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

### ✅ What Exists
- Basic game engine with rules and AI
- README and project setup
- Game flow diagrams and rules documentation

### 🎨 What We're Designing
- **State Machine Architecture** - How phases transition with sub-states
- **WebSocket Protocol** - Message format for full state broadcasts
- **Integration Plan** - How existing components work together

### 📅 Implementation Roadmap (After Design Complete)
1. Core infrastructure (Week 1-2) - State management, phase transitions, timers
2. Game logic integration (Week 3-4) - Connect existing engine to new architecture
3. Resilience & monitoring (Week 5) - Reconnection, logging, monitoring
4. Testing & polish (Week 6) - Automated tests, UI polish

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