# # AI_CONTEXT.md - Liap Tui Game Architecture
# Overview
This document captures all architectural decisions and planning for the Liap Tui multiplayer board game implementation using FastAPI (backend) and PixiJS (frontend).
# Core Problems Identified
**1** **Phase Violations**: Bots declaring during redeal phase
**2** **Race Conditions**: Multiple actions happening simultaneously
**3** **State Synchronization**: Keeping all clients in sync
**4** **Complex Game Flow**: Multiple phases with specific rules and restrictions

⠀Technology Stack (from README.md)
* **Backend**: FastAPI (Python 3.11+) with built-in WebSocket support
* **Frontend**: PixiJS 8.x with @pixi/ui components
* **Build**: ESBuild for bundling
* **Language**: Pure JavaScript frontend (no TypeScript)
* **Deployment**: Single container Docker deployment

⠀Architectural Decisions
### 1. Phase Transitions
**Choice: Option B - Transition periods with locked states**
* Transition periods act as "airlocks" between phases
* No actions accepted during transitions (450-800ms total)
* Prevents race conditions at phase boundaries
* Flow: Current Phase → [LOCK] → Transition Period → [UNLOCK] → Next Phase

⠀2. Bot Timing Strategy
**Choice: Option A - Fixed delays per action type**
* Quick Actions: 500-1000ms (acknowledging changes)
* Medium Actions: 1500-3000ms (redeal decisions, declarations)
* Complex Actions: 2000-4000ms (analyzing plays)
* Strategic Actions: 3000-5000ms (critical moments)
* Includes variance to prevent mechanical feel

⠀3. Conflict Resolution
**Choice: Option C - Phase-specific rules**
* Each phase has tailored conflict resolution
* Key clarifications from user:
  * Multiple redeal requests: Process by player order (not first-come)
  * ALL weak players must decide (phase doesn't end on first accept)
  * Two separate timers: Decision timer (10s) and Disconnection timer (30s)
  * Invalid plays auto-select random valid pieces (not auto-lose)
  * Turn winner ambiguity: By game rules (valid > type > points > player order)

⠀4. State Synchronization
**Choice: Option B - Delta/patch updates**
* Send only changes, not full state
* Operations: SET, ADD, REMOVE, UPDATE, PATCH
* Sequence tracking for ordering and recovery
* Full state only on: join/reconnect, major transitions, errors
* Target: <500 bytes per delta, <5KB full state

⠀5. Error Handling
**Choice: Option A - Fail fast and notify**
* Immediate error detection and processing stop
* Clear notifications to affected parties
* No automatic recovery that could cause inconsistencies
* Four severity levels: Information, Warning, Error, Critical
* Complete logging for debugging

⠀Project Requirements
### Scale & Performance
* **Concurrent Games**: 5-10 games (small scale launch)
* **Acceptable Latency**: 200-1000ms for actions
* **Disconnection Handling**: 30-second reconnection window
* **Bot Replacement**: After timeout, replace with AI

⠀Complexity & Extensibility
* **Architecture Focus**: Fat Server / Thin Client
* **Rules**: Data-driven where possible
* **Testing**: Extensive automated testing
* **New Features**: Rare - focus on performance and stability

⠀Timer Specifications
| **Timer Type** | **Duration** | **Timeout Action** |
|:-:|:-:|:-:|
| **Decision Timers** |  |  |
| Redeal Decision | 10 seconds | Auto-decline |
| Declaration | 15 seconds | Random valid choice |
| Turn Play | 15 seconds | Random valid pieces |
| **Disconnection Timer** |  |  |
| All Phases | 30 seconds | Replace with bot |
| **Special Timers** |  |  |
| Game Abandoned | 30 seconds | Archive game |
# Phase Transition Durations
* PREPARATION → DECLARATION: ~300ms
* DECLARATION → TURN: ~400ms
* TURN → SCORING: ~500ms
* SCORING → PREPARATION: ~600ms
* PREPARATION → REDEAL: ~200ms
* REDEAL → PREPARATION: ~400ms

⠀Important Game Rule Clarifications
**1** **Redeal Phase**:
	* Every weak player must decide (or timeout)
	* Phase doesn't end on first accept
	* Process decisions in player order
**2** **Declaration Phase**:
	* Last player cannot make total = 8
	* If system error allows it: alert devs, force reselection
**3** **Turn Phase**:
	* Invalid plays get random valid pieces (not auto-lose)
	* Piece count mismatch: reject and retry
	* Turn winner by: valid > type > points > player order

⠀Next Steps
1 Implementation priorities (to be discussed)
2 Specific edge case handling
3 Testing strategy
4 Deployment planning

⠀Key Principles
* **Server Authority**: Server state is always correct
* **Phase Integrity**: No actions cross phase boundaries
* **Fail Safe**: When in doubt, maintain game flow with safe defaults
* **Clear Communication**: Every error has user-friendly messaging
* **Performance First**: Optimize for 5-10 concurrent games initially
