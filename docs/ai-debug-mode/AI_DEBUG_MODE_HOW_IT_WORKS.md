# How AI Debug Mode Works - Technical Deep Dive

## Overview

AI Debug Mode is a synchronous, simplified version of the Liap Tui game that runs entirely locally without WebSocket infrastructure. It allows rapid testing and analysis of AI behavior by running games directly through the game engine.

## Architecture

```
┌─────────────────────┐
│  ai_debug_simple.py │  ← Entry point
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   SimpleAIGame      │  ← Game orchestrator
├─────────────────────┤
│ - setup_game()      │
│ - run_game()        │
│ - resolve_turn()    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│   Game Engine       │────▶│   AI Engine         │
├─────────────────────┤     ├─────────────────────┤
│ - game.py           │     │ - ai.py             │
│ - player.py         │     │ - choose_declare()  │
│ - piece.py          │     │ - choose_play()     │
└─────────────────────┘     └─────────────────────┘
           │
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│   AILogger          │────▶│   AIBugDetector     │
├─────────────────────┤     ├─────────────────────┤
│ - log_event()       │     │ - detect_bugs()     │
│ - save_logs()       │     │ - analyze_patterns()│
└─────────────────────┘     └─────────────────────┘
```

## Core Components

### 1. SimpleAIGame Class (`ai_debug_simple.py`)

This is the main orchestrator that:

```python
class SimpleAIGame:
    def __init__(self, ai_logger: AILogger, verbose: bool = False):
        self.ai_logger = ai_logger
        self.verbose = verbose
        self.game = None
        self.game_id = f"AI_{int(time.time() * 1000) % 1000000}"
```

**Key responsibilities:**
- Creates 4 AI players
- Manages game flow (rounds, phases, turns)
- Calls AI decision-making functions
- Resolves turn winners
- Handles scoring

### 2. Game Flow

The game follows this sequence:

```python
def run_game(self) -> Dict:
    self.setup_game()  # Create 4 AI players
    
    while not is_game_over(self.game) and rounds_played < 10:
        # 1. Deal pieces
        self.game.deal_pieces()
        
        # 2. Declaration Phase
        self._run_declaration_phase()
        
        # 3. Turn Phase (8 turns)
        self._run_turn_phase()
        
        # 4. Scoring Phase
        self._run_scoring_phase()
        
        rounds_played += 1
```

### 3. AI Decision Making

#### Declaration Phase

```python
def _run_declaration_phase(self):
    for i, player in enumerate(self.game.players):
        # Get AI decision
        declaration_value = choose_declare_strategic_v2(
            hand=player.hand,
            game=self.game,
            player_index=i,
            verbose=self.verbose
        )
        
        # Log the decision with context
        self.ai_logger.log_declaration(
            player_name=player.name,
            declaration_data={
                'hand_analysis': analyze_hand(player.hand),
                'decision': {
                    'declared_value': declaration_value,
                    'reasoning': get_reasoning(...)
                }
            }
        )
```

#### Turn Phase

```python
def _run_turn_phase(self):
    for turn_number in range(1, 9):
        for player in turn_order:
            # Get AI play decision
            selected_pieces = choose_turn_play_strategic_v3(
                hand=player.hand,
                game=self.game,
                player_name=player.name,
                turn_number=turn_number,
                verbose=self.verbose
            )
            
            # Create and validate turn play
            turn_play = TurnPlay(
                player=player,
                pieces=selected_pieces,
                is_valid=validate_play(...)
            )
```

### 4. Logging System

The AILogger captures everything:

```python
class AILogger:
    def log_event(self, event_data: Dict[str, Any]):
        event_data['timestamp'] = datetime.utcnow().isoformat()
        event_data['game_id'] = self.current_game_id
        self.events.append(event_data)
```

**Log Levels:**
- **Summary**: Just game results
- **Decision**: AI choices + reasoning
- **Detailed**: Full game state at each step

### 5. Bug Detection

The AIBugDetector analyzes decisions in real-time:

```python
def check_declaration_bugs(self, player_name: str, declaration_data: Dict):
    bugs = []
    
    # Check for zero declaration with strong hand
    if declaration == 0 and opener_count >= 2:
        bugs.append(BugReport(
            bug_type="zero_declaration_strong_hand",
            severity=BugSeverity.HIGH,
            description="Declared 0 with 2+ openers"
        ))
    
    return bugs
```

## Data Flow

### 1. Input Flow

```
Command Line Args → SimpleAIGame → Game Engine → AI Functions
     --games 10         Create         Deal         choose_declare()
     --log-level        Players        Pieces       choose_play()
```

### 2. Decision Flow

```
AI receives:          AI analyzes:           AI returns:
- Player hand    →    - Hand strength    →   - Declaration value
- Game state          - Other players         - Selected pieces
- Turn context        - Win conditions        - Play reasoning
```

### 3. Logging Flow

```
AI Decision → AILogger → Bug Detector → JSON File
              ↓          ↓               ↓
              Events     Bug Reports     logs/ai_debug/game_*.json
```

## Key Differences from Normal Game

### 1. No WebSocket Infrastructure

**Normal Game:**
```python
# WebSocket message handling
async def handle_play(room_id: str, data: dict):
    await state_machine.process_action(...)
    await broadcast(room_id, "phase_change", ...)
```

**AI Debug Mode:**
```python
# Direct function calls
selected = choose_turn_play_strategic_v3(...)
turn_play = TurnPlay(player, selected, is_valid)
```

### 2. Synchronous Execution

**Normal Game:**
- Asynchronous event handling
- Waits for player input
- Real-time updates via WebSocket

**AI Debug Mode:**
- Synchronous function calls
- Immediate AI decisions
- Batch processing of games

### 3. Simplified State Management

**Normal Game:**
- Enterprise state machine
- Event sourcing
- Automatic broadcasting

**AI Debug Mode:**
- Direct state updates
- Local game object
- File-based logging

## Performance Characteristics

### Speed Analysis

```
Component               Time (ms)    % of Total
─────────────────────────────────────────────
Game Setup             2-3          2%
Declaration Phase      5-10         7%
Turn Phase (8 turns)   100-120      80%
Scoring Phase          2-3          2%
Logging                10-15        9%
─────────────────────────────────────────────
Total per game         ~140ms       100%
```

This gives us ~7 games/second throughput.

### Memory Usage

```
Per Game:
- Game object: ~3KB
- Player data: ~1KB × 4 = 4KB
- Log events: ~7KB (decision level)
- Total: ~14KB/game in memory
```

## AI Decision Process

### Declaration Strategy

1. **Analyze Hand Strength**
   ```python
   opener_count = count_openers(hand)  # GENERAL, ADVISOR
   combo_count = count_combos(hand)    # Pairs, straights
   weak_pieces = count_weak(hand)      # SOLDIER, CANNON
   ```

2. **Consider Position**
   ```python
   if is_starter:
       base_declaration = opener_count + (combo_count // 2)
   else:
       # Adjust based on previous declarations
       pile_room = 8 - sum(previous_declarations)
   ```

3. **Apply Strategy**
   ```python
   if pile_room <= 3 and not is_last_player:
       # Conservative when pile room is tight
       declaration = min(declaration, 1)
   ```

### Turn Play Strategy

1. **Assess Situation**
   ```python
   piles_needed = declared - captured
   turns_remaining = 8 - turn_number
   urgency = calculate_urgency(piles_needed, turns_remaining)
   ```

2. **Choose Play Type**
   ```python
   if urgency == "CRITICAL":
       # Must try to win turns
       play_strongest_valid_combo()
   elif urgency == "COMFORTABLE":
       # Can afford to dump weak pieces
       play_weakest_valid_pieces()
   ```

3. **Execute Play**
   ```python
   selected_pieces = select_best_play(valid_plays, strategy)
   ```

## Output Format

### JSON Log Structure

```json
{
  "game_id": "AI_123456",
  "timestamp": "2025-08-30T10:00:00Z",
  "log_level": "decision",
  "events": [
    {
      "event": "declaration",
      "player": "Bot 1",
      "decision": {
        "declared_value": 3,
        "reasoning": "Starter with 2 openers"
      },
      "hand_analysis": {
        "opener_count": 2,
        "combo_count": 1
      },
      "bugs_detected": []
    }
  ]
}
```

## Analysis Tools Integration

The log files are designed for easy analysis:

```python
# analyze_ai_logs.py reads JSON logs
for event in log_data['events']:
    if event['event'] == 'declaration':
        track_declaration_pattern(event)
    elif event['event'] == 'bug_detected':
        count_bug_occurrence(event)
```

## Summary

AI Debug Mode works by:

1. **Bypassing WebSocket complexity** - Direct function calls instead of async messaging
2. **Running games synchronously** - No waiting for network or user input
3. **Logging everything** - Structured JSON logs for analysis
4. **Detecting bugs automatically** - Real-time pattern analysis
5. **Enabling rapid iteration** - 7 games/second for quick testing

This design allows developers to:
- Test AI changes quickly
- Find bugs systematically
- Analyze patterns statistically
- Improve AI strategy iteratively

The key insight is that by removing the networking layer and running everything locally, we can test hundreds of games in minutes instead of hours.