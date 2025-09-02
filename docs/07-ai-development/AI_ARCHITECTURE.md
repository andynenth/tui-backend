# AI Architecture Guide

## Overview

The Liap Tui AI system is a sophisticated decision-making framework that enables bots to play strategically competitive games. The architecture consists of two main decision phases: **Declaration Strategy** and **Turn Play Strategy**, each with its own context-aware decision engine.

## Architecture Diagram

```
┌─────────────────────┐
│  Game State Input   │
└──────────┬──────────┘
           │
     ┌─────▼──────┐
     │  Context   │
     │ Evaluation │
     └─────┬──────┘
           │
    ┌──────▼──────────┐
    │ Decision Phase  │
    ├─────────────────┤
    │ • Declaration   │
    │ • Turn Play     │
    └─────┬───────────┘
          │
    ┌─────▼────────────┐
    │ Strategy Engine  │
    ├──────────────────┤
    │ • Field Analysis │
    │ • Hand Strength  │
    │ • Role Planning  │
    └─────┬────────────┘
          │
    ┌─────▼─────────┐
    │   AI Logger   │
    │ (Debug/Trace) │
    └─────┬─────────┘
          │
    ┌─────▼─────────┐
    │ Bug Detector  │
    │  (Validation) │
    └───────────────┘
```

## Core Components

### 1. AI Engine (`backend/engine/ai.py`)

The main AI module containing declaration strategies and helper functions.

#### Key Data Structures

```python
@dataclass
class DeclarationContext:
    """Context for declaration decisions"""
    position_in_order: int      # 0-3 (player position)
    previous_declarations: List[int]  # Earlier player declarations
    is_starter: bool           # Has turn advantage
    pile_room: int            # Available piles (8 - sum)
    field_strength: str       # "weak", "normal", "strong"
    has_general_red: bool     # Special rule override
    opponent_patterns: Dict   # Strategic analysis
```

#### Strategic Constants

```python
# Strong combo types that beat PAIR in hierarchy
STRONG_COMBO_TYPES = {
    "THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"
}

# Threshold for PAIR strength (HORSE_RED pair = 12 points)
STRONG_PAIR_THRESHOLD = 12

# Combos that starters prefer over individual pieces
STARTER_PREFERRED_COMBOS = [
    "THREE_OF_A_KIND", "STRAIGHT", "FOUR_OF_A_KIND",
    "EXTENDED_STRAIGHT", "FIVE_OF_A_KIND", "DOUBLE_STRAIGHT"
]
```

### 2. Turn Strategy (`backend/engine/ai_turn_strategy.py`)

Handles piece playing decisions during the turn phase.

#### Key Data Structures

```python
@dataclass
class TurnPlayContext:
    """Context for turn play decisions"""
    my_name: str              # Bot identifier
    my_hand: List[Piece]      # Current pieces
    my_captured: int          # Piles already won
    my_declared: int          # Target pile count
    required_piece_count: Optional[int]  # Match starter's count
    turn_number: int          # Current turn
    am_i_starter: bool        # Leading this turn
    required_play_type: Optional[str]    # Must match type
    player_states: Dict       # All players' status
```

```python
@dataclass
class StrategicPlan:
    """Strategic plan for turn objectives"""
    target_remaining: int     # Piles still needed
    valid_combos: List[Tuple[str, List[Piece]]]
    opener_pieces: List[Piece]  # High-value pieces (≥11)
    urgency_level: str        # "low", "medium", "high", "critical"
    assigned_openers: List[Piece]
    assigned_combos: List[Tuple[str, List[Piece]]]
    reserve_pieces: List[Piece]
    burden_pieces: List[Piece]
    main_plan_size: int
    plan_impossible: bool
```

## Decision Algorithms

### Declaration Strategy V2

The declaration system uses a multi-factor analysis:

1. **Pile Room Calculation**
   ```python
   def calculate_pile_room(previous_declarations, has_general_red):
       # Special rule: GENERAL_RED ignores non-starter declarations
       # Overflow rule: If sum > 8, ignore last declaration
       # Forces competition instead of lockout
   ```

2. **Field Strength Assessment**
   ```python
   def assess_field_strength(previous_declarations):
       # "weak": avg ≤ 2.0
       # "normal": 2.0 < avg < 3.5
       # "strong": avg ≥ 3.5
   ```

3. **Opponent Pattern Analysis**
   - Tracks low declarers (0-1 piles)
   - Identifies high declarers (4+ piles)
   - Detects combo opportunities
   - Predicts singles-only games

### Turn Play Strategy

The turn play system uses strategic planning:

1. **Urgency Calculation**
   - Based on piles needed vs. turns remaining
   - Factors in hand strength and combo availability
   
2. **Overcapture Avoidance**
   ```python
   @dataclass
   class OvercaptureConstraints:
       max_safe_pieces: int      # Safe play limit
       avoid_piece_counts: List[int]  # Risky counts
       risky_play_types: List[str]    # Winning combos
       risk_level: str           # Risk assessment
   ```

3. **Never-Win Combo Detection**
   - All-BLACK straights (3+5+7 minimum)
   - SOLDIER_BLACK pairs (1+1 minimum)
   - Multiple SOLDIER_BLACK combinations

## AI Decision Flow

### Declaration Phase

```python
def choose_declare_strategic_v2(context):
    # 1. Calculate pile room and constraints
    # 2. Assess field strength
    # 3. Analyze opponent patterns
    # 4. Count strong combos and openers
    # 5. Apply position-based strategy
    # 6. Return declaration (0-8)
```

### Turn Play Phase

```python
def strategic_turn_play(context):
    # 1. Build strategic plan
    # 2. Check overcapture constraints
    # 3. Filter valid plays
    # 4. Apply role-based selection
    # 5. Handle special cases (opener timing)
    # 6. Return optimal play
```

## Logging and Debugging

### AI Logger (`backend/services/ai_logger.py`)

Provides structured logging with three levels:
- **summary**: Game outcomes only
- **decision**: + AI decisions and rationale
- **detailed**: + Full game context

### Bug Detector (`backend/services/ai_bug_detector.py`)

Automatically detects:
- Invalid plays
- Suboptimal decisions
- Logic errors
- Never-win combos

## Strategy Patterns

### 1. Starter Strategy
- Prefer strong combos over individual openers
- Set favorable piece counts for the turn
- Consider field strength when opening

### 2. Responder Strategy
- Must match starter's piece count and type
- Balance between winning and avoiding overcapture
- Strategic passing when appropriate

### 3. Position-Based Adjustments
- Early positions: More aggressive declarations
- Later positions: Adaptive to pile room
- Last position: Cannot declare sum of 8

### 4. Special Rules
- GENERAL_RED: Ignores non-starter declarations
- Zero streak: Must declare non-zero after 2 zeros
- Last player rule: Sum cannot equal 8

## Performance Considerations

1. **Decision Speed**: All decisions made in <100ms
2. **Memory Usage**: Minimal state tracking
3. **Parallel Processing**: Independent bot decisions
4. **Caching**: Combo calculations cached per hand

## Common AI Patterns

### Aggressive Bot
- High declarations (4-6)
- Plays strong combos early
- Takes calculated risks

### Conservative Bot
- Low declarations (1-3)
- Saves openers for late game
- Avoids overcapture

### Adaptive Bot
- Adjusts to opponent patterns
- Flexible declaration strategy
- Balances risk and reward

## Integration Points

1. **Game Engine**: Receives game state, returns decisions
2. **WebSocket**: Decisions transmitted as game actions
3. **Debug Mode**: Standalone testing without infrastructure
4. **Regression Tests**: Validates behavior consistency

## Future Enhancements

1. Machine learning integration
2. Opponent modeling
3. Long-term strategy planning
4. Personality customization
5. Difficulty levels