# Game Engine Audit

## Overview
This document contains detailed analysis of all game engine components including core game logic, player management, AI systems, and game rules.

---

## 1. `/backend/engine/game.py`

**Status**: ✅ Checked  
**Purpose**: Core game logic implementation. Manages game state, rounds, scoring, deck dealing, and player actions. Contains business rules for the Liap Tui card game.

**Classes/Functions**:

- `Game` class - Main game logic coordinator
- `__init__()` - Initializes game with players and win conditions
- **Event-driven methods**:
  - `get_weak_hand_players()` - Identifies players eligible for redeal
  - `has_weak_hand_players()` - Quick weak hand check
  - `execute_redeal_for_player()` - Performs redeal for specific player
  - `get_game_phase_info()` - Returns current game phase data
  - `get_declaration_eligible_players()` - Gets players who need to declare
  - `validate_player_declaration()` - Validates declaration input
  - `record_player_declaration()` - Records player declaration
  - `get_turn_eligible_players()` - Gets players who can play pieces
  - `validate_turn_play()` - Validates piece play attempt
- **Core game methods**:
  - `play_turn()` - Processes piece play and determines turn winner
  - `request_redeal()` - Handles redeal requests
  - `get_player()` - Player lookup by name
  - `get_player_order_from()` - Calculates turn order from starting player
  - `all_players_declared()` - Checks if declaration phase complete
  - `_is_game_over()` - Win condition checking
- **Deck dealing methods**:
  - `deal_pieces()` - **Key method**: Main dealing entry point (called by PREPARATION state)
  - `_deal_pieces()` - Standard random dealing
  - `_prepare_deck_and_hands()` - Deck setup and hand clearing
  - `_categorize_pieces()` - Sorts pieces by type for special deals
  - `_fill_remaining_slots()` - Fills hands after special dealing
  - `_deal_weak_hand()` - Forces weak hands for testing
  - `_deal_weak_hand_legacy()` - **Dead Code**: Old weak hand implementation
  - `_deal_guaranteed_no_redeal()` - Forces no-redeal scenario for testing
  - `_deal_double_straight()` - Forces specific play type for testing
  - `_generate_new_hand_for_player()` - Redeal implementation

**Dead Code**:

- `_deal_weak_hand_legacy()` method (lines 629-634) - Old implementation, superseded by current version
- Unused interface parameter in constructor (line 19) - Intended for CLI/GUI adaptation but not implemented

**Dependencies**:

- Imports:
  - `engine.ai` - AI player logic (alias import)
  - `engine.piece.Piece` - Game piece representation
  - `engine.player.Player` - Player entity management
  - `engine.rules` (get_play_type, get_valid_declares, is_valid_play) - Game rule validation
  - `engine.scoring.calculate_round_scores` - Score calculation logic
  - `engine.turn_resolution` (TurnPlay, resolve_turn) - Turn outcome determination
  - `engine.win_conditions` (WinConditionType, get_winners, is_game_over) - Win condition logic
- Used by:
  - `backend.engine.room.py` - Room creates Game instance (line 204)
  - `backend.engine.state_machine.game_state_machine.py` - State machine operates on Game instance

---

## 2. `/backend/engine/player.py`

**Status**: ✅ Checked  
**Purpose**: Player entity class representing individual players in the game. Manages player state, hand, score, and game statistics.

**Classes/Functions**:

- `Player` class - Main player entity
- `__init__()` - Initializes player with name and bot status
- `has_red_general()` - Checks if player has RED GENERAL piece (determines first round starter)
- `__repr__()` - String representation for debugging
- `record_declaration()` - Records player's pile count declaration
- `reset_for_next_round()` - Resets round-specific state while preserving game stats

**Dead Code**:

- None identified - All methods appear to be used

**Dependencies**:

- Imports: None - Pure Python class
- Used by:
  - `backend.engine.room.py` - Creates Player instances (lines 52, 56, 416, 418, 442, 448)
  - `backend.engine.game.py` - Operates on Player instances throughout game logic
  - `backend.engine.state_machine.game_state_machine.py` - Accesses player data for broadcasting

---

## 3. `/backend/engine/piece.py`

**Status**: ✅ Checked  
**Purpose**: **Game Piece Entity**: Represents individual game pieces with their properties, point values, and deck creation logic.

**Classes/Functions**:

- `Piece` class - Main piece entity
- `__init__()` - Initializes piece with kind and point value
- `__repr__()` - String representation for debugging
- `name` property - Extracts piece name from kind (e.g., "GENERAL")
- `color` property - Extracts piece color from kind (e.g., "RED")
- `build_deck()` - **Key static method**: Creates full deck of 32 pieces

**Dead Code**:

- None identified - All methods are used

**Dependencies**:

- Imports:
  - `engine.constants.PIECE_POINTS` - Point values for all piece types
- Used by:
  - `backend.engine.game.py` - Uses Piece for deck creation and gameplay
  - `backend.engine.player.py` - Players have hands containing Piece instances

---

## 4. `/backend/engine/ai.py`

**Status**: ✅ Checked  
**Purpose**: **Bot AI Logic**: Implements AI decision-making algorithms for bot players including declaration choices and piece play selection.

**Classes/Functions**:

- `find_all_valid_combos()` - Finds all valid piece combinations from a hand
- `choose_declare()` - **Key function**: AI declaration logic with position awareness
- `pieces_exist_in_hand()` - Validates if pieces exist in hand for play
- `choose_best_play()` - **Key function**: AI piece selection logic for turns

**Dead Code**:

- None identified - All functions are used by bot manager

**Dependencies**:

- Imports:
  - `engine.rules` (get_play_type, is_valid_play) - Game rule validation
  - `collections.Counter` - For counting piece types
  - `itertools.combinations` - For generating piece combinations
- Used by:
  - `backend.engine.bot_manager.py` - Uses AI functions for bot decisions
  - `backend.engine.game.py` - Imports as alias (line 6)

---

## 5. `/backend/engine/rules.py`

**Status**: ✅ Checked  
**Purpose**: **Game Rules Engine**: Implements all game rules including play validation, play type determination, and declaration validation. Defines play type hierarchy and comparison logic.

**Classes/Functions**:

**Play Type Detection**:
- `get_play_type()` - **Key function**: Determines play type from piece list (returns: SINGLE, PAIR, THREE_OF_A_KIND, STRAIGHT, FOUR_OF_A_KIND, EXTENDED_STRAIGHT, EXTENDED_STRAIGHT_5, FIVE_OF_A_KIND, DOUBLE_STRAIGHT, or INVALID)
- `is_valid_play()` - Validates if pieces form a valid play

**Individual Play Type Validators**:
- `is_pair()` - Validates pairs (same name and color)
- `is_three_of_a_kind()` - Validates three soldiers of same color
- `is_straight()` - Validates straights (GENERAL-ADVISOR-ELEPHANT or CHARIOT-HORSE-CANNON)
- `is_four_of_a_kind()` - Validates four soldiers of same color
- `is_extended_straight()` - Validates 4-piece extended straights with one duplicate
- `is_extended_straight_5()` - Validates 5-piece extended straights with 2-2-1 distribution
- `is_five_of_a_kind()` - Validates five soldiers of same color
- `is_double_straight()` - **Strongest play**: Validates double straights (2 CHARIOTs, 2 HORSEs, 2 CANNONs)

**Play Comparison**:
- `compare_plays()` - **Key function**: Compares two plays of same type to determine winner
- `PLAY_TYPE_PRIORITY` - Priority order for play types (higher index = stronger)

**Declaration Logic**:
- `get_valid_declares()` - Determines valid declaration options for a player with constraints:
  - Total declarations must NOT equal 8
  - Players with 2 consecutive 0 declarations must declare ≥1

**Dead Code**:

- None identified - All functions are actively used

**Dependencies**:

- Imports:
  - `collections.Counter` - For counting piece names in validation
- Used by:
  - `backend.engine.game.py` - Uses for play validation and declaration logic
  - `backend.engine.ai.py` - Uses for AI decision making
  - `backend.engine.turn_resolution.py` - Uses compare_plays for winner determination

---

## 6. `/backend/engine/scoring.py`

**Status**: ✅ Checked  
**Purpose**: **Round Scoring Logic**: Implements scoring calculations based on declared vs actual pile counts with redeal multipliers and perfect round tracking.

**Classes/Functions**:

- `calculate_score()` - **Key function**: Calculates base score from declared vs actual piles
- `calculate_round_scores()` - **Key function**: Applies scoring to all players at round end

**Scoring Rules**:
- Declared 0, actual 0: +3 bonus points
- Declared 0, actual > 0: -actual penalty
- Declared == actual (non-zero): declared + 5 bonus
- Otherwise: -abs(declared - actual) penalty
- All scores multiplied by redeal_multiplier

**Dead Code**:

- None identified - Both functions are used

**Dependencies**:

- Imports: None - Pure calculation logic
- Used by:
  - `backend.engine.game.py` - Imports calculate_round_scores for round completion

---

## 7. `/backend/engine/turn_resolution.py`

**Status**: ✅ Checked  
**Purpose**: **Turn Resolution System**: Handles turn play evaluation and winner determination using play comparison logic.

**Classes/Functions**:

- `TurnPlay` - Dataclass representing one player's turn action
- `TurnResult` - Dataclass encapsulating full turn result with all plays and winner
- `resolve_turn()` - **Key function**: Evaluates all plays and determines turn winner

**Data Structures**:
- `TurnPlay` - Contains player, pieces, and validity
- `TurnResult` - Contains all plays and winning play

**Dead Code**:

- None identified - All components are used

**Dependencies**:

- Imports:
  - `engine.piece.Piece` - For piece data structures
  - `engine.player.Player` - For player references
  - `engine.rules.compare_plays` - For play comparison logic
- Used by:
  - `backend.engine.game.py` - Imports TurnPlay and resolve_turn for turn processing

---

## 8. `/backend/engine/win_conditions.py`

**Status**: ✅ Checked  
**Purpose**: **Win Condition Logic**: Implements game end conditions and winner determination based on different win condition types.

**Classes/Functions**:

- `WinConditionType` - Enum defining win conditions:
  - `FIRST_TO_REACH_50` - First player to reach 50+ points
  - `AFTER_20_ROUNDS` - Game ends after 20 rounds
  - `EXACTLY_50_POINTS` - Only exact 50 points wins
- `is_game_over()` - **Key function**: Checks if game should end based on win condition
- `get_winners()` - **Key function**: Determines winner(s) based on win condition and scores

**Dead Code**:

- `WinConditionType.AFTER_20_ROUNDS` vs `MOST_POINTS_AFTER_20_ROUNDS` inconsistency in get_winners() function (line 46) - appears to be a typo

**Dependencies**:

- Imports:
  - `enum.Enum` - For win condition enumeration
- Used by:
  - `backend.engine.game.py` - Imports WinConditionType, get_winners, is_game_over for game completion logic

---

## 9. `/backend/engine/constants.py`

**Status**: ✅ Checked  
**Purpose**: **Game Constants**: Defines point values for all game pieces used in play comparison and strength determination.

**Classes/Functions**:

- `PIECE_POINTS` - Dictionary mapping piece types to point values:
  - RED pieces: GENERAL_RED (14), ADVISOR_RED (12), ELEPHANT_RED (10), CHARIOT_RED (8), HORSE_RED (6), CANNON_RED (4), SOLDIER_RED (2)
  - BLACK pieces: GENERAL_BLACK (13), ADVISOR_BLACK (11), ELEPHANT_BLACK (9), CHARIOT_BLACK (7), HORSE_BLACK (5), CANNON_BLACK (3), SOLDIER_BLACK (1)

**Note**: Higher numbers = stronger pieces, RED pieces are generally stronger than BLACK pieces of the same type.

**Dead Code**:

- File header comment incorrectly says "main.py" instead of "constants.py" - minor documentation issue

**Dependencies**:

- Imports: None - Pure data constants
- Used by:
  - `backend.engine.piece.py` - Imports PIECE_POINTS for piece initialization

---

## Summary

The game engine is well-structured with clear separation of concerns:

- **Core Game Logic**: Comprehensive game state management and rule enforcement
- **Player Management**: Complete player entity with scoring and statistics
- **AI System**: Sophisticated bot decision-making for declarations and plays
- **Rules Engine**: Complete implementation of all play types and validation
- **Scoring System**: Accurate scoring with multipliers and perfect round tracking
- **Turn Resolution**: Robust turn evaluation and winner determination
- **Win Conditions**: Flexible win condition system with multiple game modes
- **Constants**: Centralized piece values for consistent game balance

**Key Strengths**:
- Complete implementation of all game rules and play types
- Sophisticated AI with strategic decision-making
- Flexible win condition system
- Comprehensive scoring with multipliers and bonuses
- Clean separation of concerns between components

**Areas for Improvement**:
- Fix header comment in constants.py
- Remove legacy dead code in game.py
- Fix win condition type inconsistency in win_conditions.py
- Consider consolidating some of the dealing test methods