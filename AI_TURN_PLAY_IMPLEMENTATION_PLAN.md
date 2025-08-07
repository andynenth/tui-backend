# AI Turn Play Implementation Plan

## Overview
This document outlines the implementation plan for improving AI turn play strategy based on requirements in AI_TURN_PLAY_REQUIREMENTS.md. All tasks are derived from the existing codebase with no assumptions.

## Critical Bug Fix

### Task 1: Fix Pile Counting Bug in game.py
- [x] **File**: `backend/engine/game.py` line 406
- [x] **Current**: `self.pile_counts[turn_result.winner.player.name] += 1`
- [x] **Fix to**: `self.pile_counts[turn_result.winner.player.name] += len(turn_result.winner.pieces)`
- [x] **Verification**: Ensure winner captures X piles when winning X-piece turn
- [x] **Note**: State machine (turn_state.py) already implements this correctly
- [x] **Completed**: Fixed in commit 5ab6e260

## Phase 1: Foundation - Core Data Structures

### Task 2: Create AI Turn Strategy Module
- [ ] **Create file**: `backend/engine/ai_turn_strategy.py`
- [ ] **Import dependencies**:
  ```python
  from dataclasses import dataclass
  from typing import List, Dict, Optional, Tuple
  from backend.engine.piece import Piece
  from backend.engine.rules import get_play_type, is_valid_play
  ```

### Task 3: Define Turn Play Context
- [ ] **In**: `ai_turn_strategy.py`
- [ ] **Create dataclass**: `TurnPlayContext` with fields:
  - `my_name: str` - Bot's name for self-identification
  - `my_hand: List[Piece]` - Current bot hand
  - `my_captured: int` - Piles already captured
  - `my_declared: int` - Target pile count
  - `required_piece_count: Optional[int]` - From game state
  - `turn_number: int` - Current turn in round
  - `pieces_per_player: int` - Remaining pieces per player
  - `am_i_starter: bool` - Leading this turn?
  - `current_plays: List[Dict]` - This turn's plays so far
  - `revealed_pieces: List[Piece]` - All face-up played pieces
  - `player_states: Dict[str, Dict]` - All players' captured/declared

### Task 4: Create Strategic Plan Structure
- [ ] **In**: `ai_turn_strategy.py`
- [ ] **Create dataclass**: `StrategicPlan` with fields:
  - `target_remaining: int` - Piles still needed (declared - captured)
  - `valid_combos: List[Tuple[str, List[Piece]]]` - All valid plays
  - `opener_pieces: List[Piece]` - Pieces with point >= 11
  - `urgency_level: str` - "low", "medium", "high", "critical"

## Phase 2: Basic Decision Making

### Task 5: Implement Core Decision Function
- [ ] **In**: `ai_turn_strategy.py`
- [ ] **Create function**: `choose_strategic_play(hand: List[Piece], context: TurnPlayContext) -> List[Piece]`
- [ ] **Initial logic**:
  ```python
  # Check if at declared target
  if context.my_captured == context.my_declared:
      return avoid_overcapture_strategy(hand, context)
  
  # For now, delegate to existing logic
  from backend.engine.ai import choose_best_play
  return choose_best_play(hand, context.required_piece_count)
  ```

### Task 6: Implement Overcapture Avoidance
- [ ] **In**: `ai_turn_strategy.py`
- [ ] **Create function**: `avoid_overcapture_strategy(hand: List[Piece], context: TurnPlayContext) -> List[Piece]`
- [ ] **Logic**:
  - Find weakest valid combination of required_piece_count
  - If no valid combo, return weakest pieces (will forfeit)
  - Sort pieces by point value ascending
  - Return first N pieces where N = required_piece_count

### Task 7: Create Test for Overcapture Avoidance
- [ ] **Create directory**: `tests/ai_turn_play/`
- [ ] **Create file**: `tests/ai_turn_play/test_overcapture.py`
- [ ] **Test case**:
  ```python
  def test_avoid_overcapture_when_at_target():
      hand = [Piece("GENERAL_RED"), Piece("SOLDIER_BLACK"), Piece("SOLDIER_BLACK")]
      context = TurnPlayContext(
          my_hand=hand,
          my_captured=2,
          my_declared=2,
          required_piece_count=2,
          # ... other fields
      )
      result = choose_strategic_play(hand, context)
      # Should return two SOLDIER_BLACK pieces
      assert all(p.name == "SOLDIER" for p in result)
  ```

## Phase 3: Integration with Bot Manager

### Task 8: Update Bot Manager to Build Context
- [ ] **File**: `backend/engine/bot_manager.py`
- [ ] **In method**: `_bot_play()` (around line 638)
- [ ] **Add context building**:
  ```python
  # Build turn play context
  game = self.game
  context = TurnPlayContext(
      my_name=bot.name,
      my_hand=bot.hand,
      my_captured=game.pile_counts.get(bot.name, 0),
      my_declared=bot.declared,
      required_piece_count=required_piece_count,
      turn_number=game.turn_number,
      pieces_per_player=len(bot.hand),
      am_i_starter=(self.current_turn_starter == bot.name),
      current_plays=[],  # TODO: Get from state machine
      revealed_pieces=[],  # TODO: Track revealed pieces
      player_states={p.name: {"captured": game.pile_counts.get(p.name, 0), 
                              "declared": p.declared} for p in game.players}
  )
  ```

### Task 8a: Implement Turn History Tracking
- [ ] **File**: `backend/engine/game.py`
- [ ] **Add field**: `turn_history_this_round = []`
- [ ] **Update**: Store all turns with plays, winners, and pile counts
- [ ] **Clear**: Reset in preparation_state.py when dealing new round

### Task 9: Update Bot Manager to Use Strategic Play
- [ ] **File**: `backend/engine/bot_manager.py`
- [ ] **Replace** (line 664):
  ```python
  selected = ai.choose_best_play(bot.hand, required_count=required_piece_count, verbose=True)
  ```
- [ ] **With**:
  ```python
  from backend.engine.ai_turn_strategy import choose_strategic_play
  selected = choose_strategic_play(bot.hand, context=context)
  ```

### Task 10: Add Import Fallback
- [ ] **File**: `backend/engine/ai.py`
- [ ] **Add compatibility wrapper**:
  ```python
  def choose_best_play_with_context(hand: list, context=None, required_count=None, verbose=True):
      """Wrapper to support both old and new AI interfaces"""
      if context is not None:
          from backend.engine.ai_turn_strategy import choose_strategic_play
          return choose_strategic_play(hand, context)
      else:
          return choose_best_play(hand, required_count, verbose)
  ```

### Task 10a: Add Defensive Checks
- [ ] **File**: `backend/engine/bot_manager.py`
- [ ] **Add check**: `if hasattr(self, '_extract_revealed_pieces')` before calling
- [ ] **Default values**: Ensure is_valid defaults match between files (True)
- [ ] **Validation**: Check method existence before calling

## Phase 4: Target Achievement Strategy

### Task 11: Implement Target Planning
- [ ] **In**: `ai_turn_strategy.py`
- [ ] **Create function**: `generate_strategic_plan(hand: List[Piece], context: TurnPlayContext) -> StrategicPlan`
- [ ] **Logic**:
  - Calculate target_remaining = declared - captured
  - Find all valid combinations using existing `find_all_valid_combos()`
  - Identify openers (pieces with point >= 11)
  - Assess urgency based on pieces remaining

### Task 12: Implement Starter Strategy
- [ ] **In**: `ai_turn_strategy.py`
- [ ] **Create function**: `execute_starter_strategy(plan: StrategicPlan, context: TurnPlayContext) -> List[Piece]`
- [ ] **Decision tree**:
  - If urgency critical AND have combo that captures needed piles: play it
  - If have reliable opener AND target_remaining > 1: play opener
  - Otherwise: play weakest valid combination

### Task 13: Test Target Achievement
- [ ] **Create file**: `tests/ai_turn_play/test_target_achievement.py`
- [ ] **Test case**: Opener strategy
- [ ] **Test case**: Urgent capture scenario
- [ ] **Test case**: Normal progression

## Phase 5: Responder Strategy

### Task 14: Implement Responder Logic
- [ ] **In**: `ai_turn_strategy.py`
- [ ] **Create function**: `execute_responder_strategy(plan: StrategicPlan, context: TurnPlayContext) -> List[Piece]`
- [ ] **Logic**:
  - Analyze current winning play from context.current_plays
  - Check if we can beat it
  - Check if we should beat it (helps reach target)
  - If yes to both: play winning combination
  - Otherwise: play weakest pieces

### Task 15: Implement Play Comparison
- [ ] **In**: `ai_turn_strategy.py`
- [ ] **Create function**: `can_beat_play(my_pieces: List[Piece], opponent_pieces: List[Piece]) -> bool`
- [ ] **Use**: `compare_plays()` from rules.py

## Phase 6: Advanced Features

### Strategic Priority Order
1. Opponent Disruption (highest priority)
2. Overcapture Avoidance
3. Target Achievement
4. Burden Disposal (lowest priority)

### Task 16: Track Revealed Pieces
- [ ] **In**: `backend/engine/state_machine/states/turn_state.py`
- [ ] **Store**: Turn history with is_valid flag (default True)
- [ ] **Extract**: Filter only valid plays (is_valid=True) for revealed pieces
- [ ] **Note**: Forfeit plays have is_valid=False and should be excluded
- [ ] **Pass**: To context when building

### Task 17: Implement Opponent Disruption
- [ ] **In**: `ai_turn_strategy.py`
- [ ] **Create function**: `check_opponent_disruption(hand: List[Piece], context: TurnPlayContext) -> Optional[List[Piece]]`
- [ ] **Logic**:
  - Check if any opponent would transition from captured < declared to captured = declared THIS TURN
  - Calculate: if opponent wins current turn, would they reach target?
  - If yes AND we can win: play pieces to disrupt
  - Return disruption pieces or None

### Task 18: Add Burden Disposal Logic
- [ ] **In**: `ai_turn_strategy.py`
- [ ] **Enhance**: Starter strategy to identify burden pieces
- [ ] **Logic**: Pieces that don't contribute to any winning combo for remaining targets

## Testing & Validation

### Task 19: Create Integration Tests
- [ ] **File**: `tests/ai_turn_play/test_integration.py`
- [ ] **Test**: Full game scenarios with new AI
- [ ] **Verify**: No game breaking bugs
- [ ] **Check**: Pile counting is correct

### Task 20: Performance Testing
- [ ] **Measure**: Decision time for strategic play
- [ ] **Target**: < 100ms per decision
- [ ] **Profile**: Identify any bottlenecks

## Rollout Plan

### Phase 1 Completion Checklist
- [x] Pile counting bug fixed (commit 5ab6e260)
- [ ] Basic strategic module created
- [ ] Overcapture avoidance working
- [ ] Tests passing

### Phase 2 Completion Checklist
- [ ] Bot manager integrated
- [ ] Target achievement working
- [ ] Starter strategies implemented
- [ ] No game-breaking issues

### Phase 3 Completion Checklist
- [ ] Responder logic complete
- [ ] Advanced features added
- [ ] All tests passing
- [ ] Performance acceptable

## Risk Mitigation

1. **Backward Compatibility**: Keep original `choose_best_play()` functional
2. **Gradual Rollout**: Use feature flag or gradual integration
3. **Extensive Testing**: Test each phase before moving to next
4. **Fallback Logic**: If strategic play fails, fall back to original logic

## Success Criteria

Based on AI_TURN_PLAY_REQUIREMENTS.md:
- [ ] Target Achievement Rate: ≥70%
- [ ] Overcapture Avoidance: ≥95% when at target
- [ ] Valid Play Rate: 100%
- [ ] Decision Speed: <100ms
- [ ] No game-breaking bugs introduced