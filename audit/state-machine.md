# State Machine Audit

## Overview
This document contains detailed analysis of the complete state machine system including the core coordinator, enterprise architecture base class, and all game state implementations.

---

## 1. `/backend/engine/state_machine/game_state_machine.py`

**Status**: ✅ Checked  
**Purpose**: Central coordinator for game state management. Handles phase transitions, action queuing, and coordinates all game state logic through an enterprise architecture pattern.

**Classes/Functions**:

- `GameStateMachine` class - Main state machine coordinator
- `__init__()` - Initializes state machine with game instance and states
- `start()` - **Key method**: Starts state machine in PREPARATION phase (called by room.py line 223)
- `stop()` - Gracefully stops state machine and cleans up resources
- `handle_action()` - Queues player actions for asynchronous processing
- `_process_loop()` - Main processing loop (0.5s polling) for actions and transitions
- `process_pending_actions()` - Processes queued actions through current state
- `_transition_to()` - Handles phase transitions with validation
- `get_current_phase()` - Returns current GamePhase
- `get_allowed_actions()` - Returns valid ActionTypes for current state
- `get_phase_data()` - Returns JSON-serializable phase data
- `_broadcast_phase_change_with_hands()` - **Dead Code**: Commented out due to enterprise auto-broadcasting
- `broadcast_event()` - Sends WebSocket events via callback
- `_notify_bot_manager()` - Triggers bot actions on phase changes
- `_notify_bot_manager_data_change()` - **Enterprise**: Auto-bot triggering on data updates
- `_store_phase_change_event()` - Event sourcing for replay capability
- `store_game_event()` - Public event storage interface
- `_notify_bot_manager_action_rejected/accepted/failed()` - Bot feedback system
- `force_end_game()` - Emergency game termination

**Dead Code**:

- `_broadcast_phase_change_with_hands()` method implementation (lines 296-331) - Superseded by enterprise auto-broadcasting in base_state.py
- Commented broadcast call in `_transition_to()` (lines 233-235)

**Dependencies**:

- Imports:
  - `.action_queue.ActionQueue` - Action queuing and event storage
  - `.base_state.GameState` - Base class for all game states
  - `.core` (ActionType, GameAction, GamePhase) - Core game enums and data structures
  - `.states` (DeclarationState, PreparationState, ScoringState, TurnState) - Game phase implementations
  - `.states.game_over_state.GameOverState` - Game completion state
  - `.states.round_start_state.RoundStartState` - Round announcement state
  - `.states.turn_results_state.TurnResultsState` - Turn outcome state
  - `.states.waiting_state.WaitingState` - Initial waiting state
  - `..bot_manager.BotManager` (dynamic import) - Bot AI coordination
  - `...room_manager.room_manager` (dynamic import) - Room management
- Used by:
  - `backend.engine.room.py` - Room creates and manages state machine instance

---

## 2. `/backend/engine/state_machine/core.py`

**Status**: ✅ Checked  
**Purpose**: Core data structures and enums for the game state machine. Defines game phases, action types, and the GameAction data structure.

**Classes/Functions**:

- `GameStateError` - Custom exception for state machine errors
- `GamePhase` - Enum defining all game phases (WAITING, PREPARATION, ROUND_START, DECLARATION, TURN, TURN_RESULTS, SCORING, GAME_OVER)
- `ActionType` - Enum defining all possible player/system actions
- `GameAction` - Dataclass representing a game action with player, type, payload, and metadata
- `__post_init__()` - Ensures GameAction has timestamp

**Dead Code**:

- `PLAYER_DISCONNECT`, `PLAYER_RECONNECT` ActionTypes - Defined but not used in current implementation
- `VIEW_SCORES`, `CONTINUE_ROUND` ActionTypes - Appear to be legacy/unused actions

**Dependencies**:

- Imports:
  - `dataclasses.dataclass` - For GameAction structure
  - `datetime.datetime` - For action timestamps
  - `enum.Enum` - For phase and action enums
  - `typing` - For type hints
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Uses all enum types and GameAction
  - `backend.api.routes.ws.py` - Imports ActionType and GameAction for WebSocket handlers
  - All state machine state classes - Use GamePhase and ActionType enums

---

## 3. `/backend/engine/state_machine/base_state.py`

**Status**: ✅ Checked  
**Purpose**: **Enterprise Architecture**: Abstract base class for all game states. Implements automatic broadcasting system and common state lifecycle management.

**Classes/Functions**:

- `GameState` - Abstract base class for all game states
- `__init__()` - Initializes state with state machine reference and enterprise features
- `phase_name` property - Abstract property for state identification
- `next_phases` property - Abstract property for valid transitions
- `on_enter()` - **Key method**: Called when entering state, triggers _setup_phase()
- `on_exit()` - **Key method**: Called when exiting state, triggers _cleanup_phase()
- `_setup_phase()` - Abstract method for state-specific initialization
- `_cleanup_phase()` - Abstract method for state-specific cleanup
- `handle_action()` - Routes actions through validation and processing
- `_validate_action()` - Abstract method for action validation
- `_process_action()` - Abstract method for action processing
- `check_transition_conditions()` - Abstract method for transition logic
- `update_phase_data()` - **Enterprise**: Automatic broadcasting on state changes
- `broadcast_custom_event()` - **Enterprise**: Custom event broadcasting
- `get_change_history()` - **Enterprise**: Event sourcing support

**Dead Code**:

- None identified - Enterprise architecture is actively used

**Dependencies**:

- Imports:
  - `.core` (ActionType, GameAction, GamePhase) - Core state machine types
- Used by:
  - `backend.engine.state_machine.states.preparation_state.py` - Extends GameState
  - All other state classes - All extend GameState base class

---

## 4. `/backend/engine/state_machine/action_queue.py`

**Status**: ✅ Checked  
**Purpose**: **Action Processing System**: Manages asynchronous action queuing and processing with event persistence. Handles player actions with sequence tracking and replay capability.

**Classes/Functions**:

- `ActionQueue` class - Main action queuing system
- `__init__()` - Initializes queue with optional room_id for persistence
- `add_action()` - **Key method**: Adds action to queue with sequence ID
- `process_actions()` - **Key method**: Processes all queued actions and returns as list
- `has_pending_actions()` - Checks if actions are waiting to be processed
- `_store_action_event()` - Stores action in EventStore for persistence
- `store_state_event()` - Stores arbitrary state events for replay capability

**Dead Code**:

- Previous async generator approach mentioned in comments (line 38-39) - replaced with list-based approach

**Dependencies**:

- Imports:
  - `.core.GameAction` - Action data structure
  - `api.services.event_store.event_store` (optional) - Event persistence
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Uses action queue for processing (line 35, 173)

---

## 5. `/backend/engine/state_machine/states/__init__.py`

**Status**: ✅ Checked  
**Purpose**: State module entry point that exports all game state classes for use by the state machine coordinator.

**Classes/Functions**:

- Module exports:
  - `DeclarationState` - Declaration phase implementation
  - `PreparationState` - Preparation phase implementation  
  - `TurnState` - Turn phase implementation
  - `ScoringState` - Scoring phase implementation
  - `RoundStartState` - Round start phase implementation

**Dead Code**:

- None identified - Pure module interface

**Dependencies**:

- Imports:
  - `.declaration_state.DeclarationState` - Declaration phase
  - `.preparation_state.PreparationState` - Preparation phase
  - `.round_start_state.RoundStartState` - Round start phase
  - `.scoring_state.ScoringState` - Scoring phase
  - `.turn_state.TurnState` - Turn phase
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Imports all state classes

---

## 6. `/backend/engine/state_machine/states/preparation_state.py`

**Status**: ✅ Checked  
**Purpose**: **Critical start_game flow**: First state entered when game starts. Handles card dealing, weak hand detection, redeal requests, and starter determination.

**Classes/Functions**:

- `PreparationState` class - Extends GameState base class
- `phase_name` property - Returns GamePhase.PREPARATION
- `next_phases` property - Returns [GamePhase.ROUND_START]
- `__init__()` - Initializes state with allowed actions and phase data
- `_setup_phase()` - **Key method**: Called when entering state, deals cards
- `_cleanup_phase()` - Called when exiting state, determines starter
- `_deal_cards()` - **Key method**: Deals cards and checks for weak hands
- `_validate_action()` - Validates incoming actions
- `_process_action()` - Routes actions to appropriate handlers
- `_handle_redeal_decision()` - Processes redeal accept/decline decisions
- `_process_all_decisions()` - Processes all redeal decisions when complete
- `_monitor_decision_timeout()` - Monitors timeout for redeal decisions
- `_force_timeout_decisions()` - Forces decision timeout
- `_handle_player_disconnect()` - Handles player disconnection
- `_handle_player_reconnect()` - Handles player reconnection
- `_determine_starter()` - Determines who starts the round
- `_all_weak_decisions_received()` - Checks if all weak players decided
- `_get_first_accepter_by_play_order()` - Gets first player to accept redeal
- `_count_acceptances()` - Counts redeal acceptances
- `_validate_state_consistency()` - Validates internal state
- `_notify_weak_hands()` - Notifies about weak hands
- `_broadcast_decision_update()` - Broadcasts decision status
- `check_transition_conditions()` - Determines when to transition to next phase

**Dead Code**:

- Commented sequential system variables (lines 45-47) - Old single-player redeal system
- Some unused logging statements

**Dependencies**:

- Imports:
  - `..base_state.GameState` - Base class for all states
  - `..core` (ActionType, GameAction, GamePhase) - Core state machine types
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Instantiated in states dict (line 45)

---

## 7. `/backend/engine/state_machine/states/declaration_state.py`

**Status**: ✅ Checked  
**Purpose**: **Declaration Phase**: Handles player declarations for target pile counts with validation and turn order management.

**Classes/Functions**:

- `DeclarationState` class - Extends GameState base class
- `phase_name` property - Returns GamePhase.DECLARATION
- `next_phases` property - Returns [GamePhase.TURN]
- `__init__()` - Initializes state with allowed actions
- `_setup_phase()` - **Key method**: Sets up declaration order and current declarer
- `_cleanup_phase()` - Copies declarations to game object
- `_validate_action()` - Validates declaration actions and player turns
- `_process_action()` - Routes actions to appropriate handlers
- `_handle_declaration()` - **Key method**: Processes player declarations
- `_get_current_declarer()` - Gets current player who should declare
- `_get_next_declarer()` - Gets next player in declaration order
- `_check_declaration_restrictions()` - Validates declaration rules
- `check_transition_conditions()` - Checks if all players have declared

**Dead Code**:

- Simplified `_check_declaration_restrictions()` method (line 178) - placeholder for game-specific rules

**Dependencies**:

- Imports:
  - `..base_state.GameState` - Base class for all states
  - `..core` (ActionType, GameAction, GamePhase) - Core state machine types
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Instantiated in states dict

---

## 8. `/backend/engine/state_machine/states/turn_state.py`

**Status**: ✅ Checked  
**Purpose**: **Turn Phase**: Handles turn-based piece playing with validation, winner determination, and pile distribution. Most complex state with extensive game logic.

**Classes/Functions**:

- `TurnState` class - Extends GameState base class
- `phase_name` property - Returns GamePhase.TURN
- `next_phases` property - Returns [GamePhase.TURN_RESULTS]
- `__init__()` - Initializes state with allowed actions and turn tracking
- `_setup_phase()` - **Key method**: Initializes turn phase and starts first turn
- `_cleanup_phase()` - Finalizes turn phase before transition
- `_validate_action()` - Validates play pieces actions
- `_process_action()` - Routes actions to appropriate handlers
- `_validate_play_pieces()` - **Key method**: Validates piece plays (turn order, piece count, combinations)
- `_handle_play_pieces()` - **Key method**: Processes valid piece plays
- `_start_new_turn()` - Starts new turn with current starter
- `_complete_turn()` - Completes current turn and determines winner
- `_determine_turn_winner()` - Determines winner using turn resolution logic
- `_get_turn_resolution_data()` - Gets comprehensive turn resolution data
- `_award_piles()` - Awards piles to turn winner
- `_process_turn_completion()` - Processes turn completion and checks for round end
- `_handle_player_disconnect()` - Handles disconnection during turns
- `_handle_player_reconnect()` - Handles reconnection during turns
- `_handle_timeout()` - Handles turn timeouts
- `_auto_play_for_player()` - Auto-plays for disconnected/timed-out players
- `start_next_turn_if_needed()` - Starts next turn if conditions met
- `restart_turn_for_testing()` - Testing method for turn restart
- `_validate_hand_size_consistency()` - **Critical**: Validates hand size consistency
- `_handle_critical_game_error()` - Handles critical game state errors

**Dead Code**:

- Legacy broadcast methods (lines 842-846, 924-926) - Superseded by enterprise methods
- Commented piece removal section (lines 606-618) - Pieces now removed immediately

**Dependencies**:

- Imports:
  - `...constants.PIECE_POINTS` - Piece point values
  - `...player.Player` - Player entities
  - `...rules.get_play_type` - Play type validation
  - `...turn_resolution` (TurnPlay, TurnResult, resolve_turn) - Turn resolution logic
  - `..base_state.GameState` - Base class for all states
  - `..core` (ActionType, GameAction, GamePhase, GameStateError) - Core state machine types
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Instantiated in states dict

---

## 9. `/backend/engine/state_machine/states/scoring_state.py`

**Status**: ✅ Checked  
**Purpose**: **Scoring Phase**: Handles score calculation, winner determination, and round completion with display timing and game-over detection.

**Classes/Functions**:

- `ScoringState` class - Extends GameState base class
- `phase_name` property - Returns GamePhase.SCORING
- `next_phases` property - Returns [GamePhase.PREPARATION, GamePhase.GAME_OVER]
- `__init__()` - Initializes state with allowed actions and scoring data
- `_setup_phase()` - **Key method**: Calculates scores, checks winners, starts display delay
- `_cleanup_phase()` - Saves scoring results and prepares next round
- `_validate_action()` - Validates scoring phase actions
- `_process_action()` - Routes actions to appropriate handlers
- `_calculate_round_scores()` - **Key method**: Calculates scores for all players
- `_check_game_winner()` - Checks if any player won the game (≥50 points)
- `_prepare_next_round()` - Prepares game state for next round
- `_start_display_delay()` - Provides 7-second display delay before transition
- `_handle_view_scores()` - Handles score viewing requests
- `_handle_player_disconnect()` - Handles disconnection during scoring
- `_handle_player_reconnect()` - Handles reconnection during scoring
- `check_transition_conditions()` - Checks if ready to transition after display delay

**Dead Code**:

- Debug print statements throughout the file - should be removed for production

**Dependencies**:

- Imports:
  - `...scoring.calculate_score` - Score calculation logic
  - `..base_state.GameState` - Base class for all states
  - `..core` (ActionType, GameAction, GamePhase) - Core state machine types
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Instantiated in states dict

---

## 10. `/backend/engine/state_machine/states/round_start_state.py`

**Status**: ✅ Checked  
**Purpose**: **Round Start Phase**: Displays round information and starter details with automatic transition to Declaration phase.

**Classes/Functions**:

- `RoundStartState` class - Extends GameState base class
- `phase_name` property - Returns GamePhase.ROUND_START
- `next_phases` property - Returns [GamePhase.DECLARATION]
- `__init__()` - Initializes state with allowed actions and display timing
- `_setup_phase()` - **Key method**: Displays round information and starts timer
- `_cleanup_phase()` - Logs transition to Declaration phase
- `_validate_action()` - Validates round start phase actions
- `_process_action()` - Routes actions to appropriate handlers
- `_handle_player_disconnect()` - Handles disconnection during round start
- `_handle_player_reconnect()` - Handles reconnection during round start
- `check_transition_conditions()` - Checks if display time elapsed (5 seconds)

**Dead Code**:

- None identified - Simple display state

**Dependencies**:

- Imports:
  - `..base_state.GameState` - Base class for all states
  - `..core` (ActionType, GameAction, GamePhase) - Core state machine types
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Instantiated in states dict

---

## 11. `/backend/engine/state_machine/states/turn_results_state.py`

**Status**: ✅ Checked  
**Purpose**: **Turn Results Phase**: Displays turn completion results with automatic transition after display period.

**Classes/Functions**:

- `TurnResultsState` class - Extends GameState base class
- `phase_name` property - Returns GamePhase.TURN_RESULTS
- `next_phases` property - Returns [GamePhase.TURN, GamePhase.SCORING]
- `__init__()` - Initializes state with display timing and result data
- `_setup_phase()` - **Key method**: Loads turn results and starts auto-transition
- `_load_turn_results()` - Loads turn result data from previous state
- `_check_all_hands_empty()` - Checks if round is complete
- `_start_auto_transition()` - Starts 7-second auto-transition timer
- `_auto_transition_after_delay()` - Handles automatic transition after delay
- `_cleanup_phase()` - Cleans up turn results state
- `_validate_action()` - Validates turn results phase actions
- `_process_action()` - Routes actions to appropriate handlers
- `handle_action()` - Handles turn results phase actions
- `check_transition_conditions()` - Checks if auto-transition completed

**Dead Code**:

- None identified - All methods are used for turn results display

**Dependencies**:

- Imports:
  - `..base_state.GameState` - Base class for all states
  - `..core` (ActionType, GameAction, GamePhase) - Core state machine types
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Instantiated in states dict

---

## 12. `/backend/engine/state_machine/states/waiting_state.py`

**Status**: ✅ Checked  
**Purpose**: **Waiting Phase**: Handles room setup, player connection management, and readiness validation before game start.

**Classes/Functions**:

- `WaitingState` class - Extends GameState base class
- `phase_name` property - Returns GamePhase.WAITING
- `next_phases` property - Returns [GamePhase.PREPARATION]
- `__init__()` - Initializes state with connection tracking
- `_setup_phase()` - **Key method**: Initializes room state and broadcasts waiting state
- `_initialize_room_state()` - Initializes room state from current configuration
- `_broadcast_waiting_state()` - Broadcasts waiting state to all clients
- `_can_start_game()` - Checks if game can be started
- `_cleanup_phase()` - Cleans up waiting state before transition
- `_validate_action()` - Validates waiting phase actions
- `_process_action()` - Routes actions to appropriate handlers
- `_handle_player_disconnect()` - Handles disconnection during waiting
- `_handle_player_reconnect()` - Handles reconnection during waiting
- `_handle_game_start_request()` - Handles game start requests
- `handle_action()` - Handles waiting phase actions
- `check_transition_conditions()` - Checks if ready to start game

**Dead Code**:

- None identified - All methods are used for waiting room management

**Dependencies**:

- Imports:
  - `..base_state.GameState` - Base class for all states
  - `..core` (ActionType, GameAction, GamePhase) - Core state machine types
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Instantiated in states dict

---

## 13. `/backend/engine/state_machine/states/game_over_state.py`

**Status**: ✅ Checked  
**Purpose**: **Game Over Phase**: Terminal state handling final rankings, game statistics, and completion data presentation.

**Classes/Functions**:

- `GameOverState` class - Extends GameState base class
- `phase_name` property - Returns GamePhase.GAME_OVER
- `next_phases` property - Returns [] (terminal state)
- `__init__()` - Initializes state with allowed actions
- `_setup_phase()` - **Key method**: Prepares final data for display
- `_cleanup_phase()` - Minimal cleanup for terminal state
- `_validate_action()` - Validates game over phase actions
- `_process_action()` - Routes actions to appropriate handlers
- `_calculate_final_rankings()` - Calculates final player rankings
- `_calculate_game_statistics()` - Calculates game statistics
- `check_transition_conditions()` - Returns None (terminal state)

**Dead Code**:

- None identified - Terminal state with minimal functionality

**Dependencies**:

- Imports:
  - `engine.win_conditions.get_winners` - Winner determination
  - `..base_state.GameState` - Base class for all states
  - `..core` (ActionType, GameAction, GamePhase) - Core state machine types
- Used by:
  - `backend.engine.state_machine.game_state_machine.py` - Instantiated in states dict

---

## Summary

The state machine system is comprehensively implemented with enterprise architecture:

- **Core Coordinator**: Robust state machine with action queuing and transition management
- **Enterprise Base Class**: Automatic broadcasting and event sourcing capabilities
- **Complete Game Flow**: All 8 game phases fully implemented with proper transitions
- **Action Processing**: Comprehensive action validation and processing system
- **Error Handling**: Critical error detection and recovery mechanisms
- **Bot Integration**: Seamless bot action triggering through enterprise architecture
- **Event Sourcing**: Complete event persistence and replay capabilities

**Key Strengths**:
- Enterprise architecture with automatic broadcasting eliminates manual broadcast errors
- Complete game state coverage from waiting room to game over
- Robust error handling with critical game state validation
- Comprehensive action validation and processing
- Seamless bot integration through event-driven architecture
- Event sourcing for debugging and replay capabilities

**Areas for Improvement**:
- Remove debug print statements in scoring_state.py
- Clean up dead code in turn_state.py (legacy broadcast methods)
- Consider consolidating some validation logic across states
- Remove unused ActionType enums in core.py
- Standardize error handling patterns across all states