# TurnPlayContext Data Sources Analysis

## Overview
This document traces each field in the `TurnPlayContext` to verify if the data is properly sourced and functional.

## Field-by-Field Analysis

### 1. `my_name` ✅ WORKING
- **Source**: `bot.name`
- **Path**: Direct from Player object
- **Status**: ✅ Fully functional
- **Code**: Line 700 in bot_manager.py
```python
my_name=bot.name,
```

### 2. `my_hand` ✅ WORKING
- **Source**: `bot.hand`
- **Path**: Direct from Player object
- **Status**: ✅ Fully functional
- **Code**: Line 701 in bot_manager.py
```python
my_hand=bot.hand,
```

### 3. `my_captured` ✅ WORKING
- **Source**: `pile_counts.get(bot.name, 0)`
- **Path**: 
  1. `game_state.pile_counts` (if exists)
  2. Initialized in game.py line 45
  3. Updated in turn_state.py `_award_piles()` method
- **Status**: ✅ Fully functional
- **Code**: Lines 681-682, 702 in bot_manager.py
```python
pile_counts = game_state.pile_counts if hasattr(game_state, 'pile_counts') else {}
bot_captured = pile_counts.get(bot.name, 0)
```

### 4. `my_declared` ✅ WORKING
- **Source**: `bot.declared`
- **Path**: Direct from Player object
- **Status**: ✅ Fully functional
- **Code**: Line 703 in bot_manager.py
```python
my_declared=bot.declared,
```

### 5. `required_piece_count` ✅ WORKING
- **Source**: 
  1. Primary: `phase_data.get("required_piece_count")`
  2. Fallback: `game_state.required_piece_count`
- **Path**: Set by turn starter in turn_state.py
- **Status**: ✅ Fully functional
- **Code**: Lines 651-657, 704 in bot_manager.py
```python
if self.state_machine:
    phase_data = self.state_machine.get_phase_data()
    required_piece_count = phase_data.get("required_piece_count")
else:
    game_state = self._get_game_state()
    required_piece_count = getattr(game_state, "required_piece_count", None)
```

### 6. `turn_number` ✅ WORKING
- **Source**: `game_state.turn_number`
- **Path**: Incremented in turn_state.py `_start_new_turn()`
- **Status**: ✅ Fully functional
- **Code**: Line 705 in bot_manager.py
```python
turn_number=getattr(game_state, 'turn_number', 0),
```

### 7. `pieces_per_player` ✅ WORKING
- **Source**: `len(bot.hand)`
- **Path**: Direct calculation from current hand
- **Status**: ✅ Fully functional
- **Code**: Line 706 in bot_manager.py
```python
pieces_per_player=len(bot.hand),
```

### 8. `am_i_starter` ✅ WORKING
- **Source**: `(current_turn_starter == bot.name)`
- **Path**: 
  1. Primary: `phase_data.get("current_turn_starter")`
  2. Fallback: `game_state.last_turn_winner.name`
- **Status**: ✅ Fully functional
- **Code**: Lines 672-677, 707 in bot_manager.py
```python
current_turn_starter = None
if self.state_machine:
    phase_data = self.state_machine.get_phase_data()
    current_turn_starter = phase_data.get("current_turn_starter")
if not current_turn_starter and hasattr(game_state, "last_turn_winner"):
    current_turn_starter = getattr(game_state.last_turn_winner, "name", None) if game_state.last_turn_winner else None

am_i_starter=(current_turn_starter == bot.name),
```

### 9. `current_plays` ❌ NOT IMPLEMENTED
- **Source**: Empty list `[]`
- **Status**: ❌ TODO - Not implemented
- **Code**: Line 708 in bot_manager.py
```python
current_plays=[],  # TODO: Get from state machine
```
- **What it should contain**: List of plays made so far this turn
- **Potential source**: `phase_data.get("turn_plays", {})`
- **Impact**: AI cannot see what other players have played this turn

### 10. `revealed_pieces` ❌ NOT IMPLEMENTED
- **Source**: Empty list `[]`
- **Status**: ❌ TODO - Not implemented
- **Code**: Line 709 in bot_manager.py
```python
revealed_pieces=[],  # TODO: Track revealed pieces
```
- **What it should contain**: All pieces that have been played face-up in previous turns
- **Potential source**: Would need to track from `turn_history_this_round` in game.py
- **Impact**: AI cannot use card counting strategies

### 11. `player_states` ✅ WORKING
- **Source**: Dictionary comprehension from game_state.players
- **Path**: 
  - `captured`: From `pile_counts.get(p.name, 0)`
  - `declared`: From `p.declared`
- **Status**: ✅ Fully functional
- **Code**: Lines 710-711 in bot_manager.py
```python
player_states={p.name: {"captured": pile_counts.get(p.name, 0), 
                        "declared": p.declared} for p in game_state.players}
```

## Summary

### Working Fields (9/11) ✅
1. `my_name` - Player name
2. `my_hand` - Current hand
3. `my_captured` - Piles captured
4. `my_declared` - Target declaration
5. `required_piece_count` - Pieces to play
6. `turn_number` - Current turn
7. `pieces_per_player` - Hand size
8. `am_i_starter` - Starter status
9. `player_states` - All players' status

### Not Implemented (2/11) ❌
1. `current_plays` - Should show plays made this turn
2. `revealed_pieces` - Should track all face-up pieces from previous turns

## Implementation Suggestions

### For `current_plays`:
```python
# In bot_manager.py around line 708
if self.state_machine:
    phase_data = self.state_machine.get_phase_data()
    turn_plays = phase_data.get("turn_plays", {})
    current_plays = []
    for player_name, play_data in turn_plays.items():
        current_plays.append({
            'player': player_name,
            'pieces': play_data.get('pieces', []),
            'play_type': play_data.get('play_type', 'UNKNOWN'),
            'play_value': play_data.get('play_value', 0)
        })
else:
    current_plays = []
```

### For `revealed_pieces`:
```python
# In bot_manager.py around line 709
revealed_pieces = []
if hasattr(game_state, 'turn_history_this_round'):
    for turn_summary in game_state.turn_history_this_round:
        for play in turn_summary.get('plays', []):
            revealed_pieces.extend(play.get('pieces', []))
```

## Impact of Missing Data

1. **`current_plays`**: Without this, the AI cannot:
   - See what the starter played (when responding)
   - See what previous players played this turn
   - Make informed decisions based on current turn state

2. **`revealed_pieces`**: Without this, the AI cannot:
   - Count cards that have been played
   - Estimate what pieces opponents might have
   - Make probability-based decisions

However, the AI still functions well with the 9 working fields, as evidenced by the strategic play system's effectiveness.