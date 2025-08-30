# AI Debug Mode Implementation Plan

## Overview
This document outlines the implementation of an AI debug mode for the Liap Tui game, enabling AI-only games for testing, debugging, and improving AI decision-making algorithms.

## Goals
1. **Visibility**: Full transparency into AI decision-making process
2. **Reproducibility**: Ability to replay and analyze specific game scenarios
3. **Performance Analysis**: Measure AI effectiveness and identify weaknesses
4. **Bug Detection**: Catch edge cases and logical errors in AI implementation
5. **Strategy Evolution**: Data-driven improvements to AI algorithms

## Essential Logging Requirements

### 1. Decision Context Logging
Every AI decision must log:
```json
{
  "timestamp": "2025-08-29T10:30:45.123Z",
  "game_id": "ABC123",
  "round": 1,
  "turn": 3,
  "player": "Bot 2",
  "decision_type": "declaration|play|redeal",
  "game_context": {
    "scores": {"Bot 1": 0, "Bot 2": 0, "Bot 3": 0, "Bot 4": 0},
    "round_number": 1,
    "phase": "declaration",
    "my_position": 2,
    "is_starter": false
  }
}
```

### 2. Declaration Phase Logging
```json
{
  "hand_analysis": {
    "raw_hand": ["SOLDIER_BLACK", "HORSE_RED", "ELEPHANT_BLACK", ...],
    "hand_strength": {
      "opener_count": 2,
      "strong_combos": ["THREE_OF_A_KIND(SOLDIER)", "PAIR(HORSE)"],
      "weak_pieces": 3,
      "average_piece_value": 5.2
    }
  },
  "decision_factors": {
    "previous_declarations": [2, 3],
    "pile_room": 3,
    "field_strength": "normal",
    "has_general_red": false,
    "zero_streak": 0,
    "forbidden_values": [3]
  },
  "decision_process": {
    "initial_calculation": 4,
    "adjustments": ["reduced due to pile_room"],
    "final_declaration": 3
  },
  "confidence": 0.85
}
```

### 3. Turn Play Logging
```json
{
  "turn_context": {
    "turn_number": 5,
    "required_pieces": 2,
    "current_winner": "Bot 1",
    "previous_plays": {
      "Bot 1": ["ADVISOR_BLACK", "ADVISOR_RED"],
      "Bot 3": ["ELEPHANT_BLACK", "ELEPHANT_RED"]
    }
  },
  "my_situation": {
    "captured_piles": 2,
    "declared_target": 3,
    "piles_needed": 1,
    "urgency_level": "high",
    "pieces_remaining": 4
  },
  "play_decision": {
    "available_plays": [
      {"type": "PAIR", "pieces": ["HORSE_BLACK", "HORSE_RED"], "strength": 10},
      {"type": "SINGLE+SINGLE", "pieces": ["GENERAL_BLACK", "SOLDIER_RED"], "strength": 14}
    ],
    "selected_play": "PAIR",
    "reasoning": "Need to win, PAIR is sufficient against current play",
    "alternative_considered": "Could play GENERAL but saving for critical turn"
  }
}
```

### 4. Game Outcome Logging
```json
{
  "game_summary": {
    "winner": "Bot 3",
    "final_scores": {"Bot 1": 23, "Bot 2": 18, "Bot 3": 51, "Bot 4": 35},
    "rounds_played": 3,
    "game_duration_ms": 45000
  },
  "player_performance": {
    "Bot 1": {
      "declaration_accuracy": 0.67,  // declared vs actual piles won
      "turns_won": 8,
      "perfect_rounds": 1,
      "overcapture_incidents": 2,
      "undercapture_incidents": 1
    }
  }
}
```

## Implementation Tasks

### Phase 1: Core Infrastructure (Week 1)

#### Task 1.1: Create AI Debug Mode Entry Point
**File**: `backend/ai_debug_mode.py`
- [ ] Create CLI argument parser
- [ ] Define configuration options (games, speed, logging level)
- [ ])Initialize logging system
- [ ] Create main game loop

#### Task 1.2: Setup Logging Infrastructure
**File**: `backend/services/ai_logger.py`
- [ ] Create structured logger with JSON output
- [ ] Define log levels (SUMMARY, DECISION, DETAILED, TRACE)
- [ ] Implement file rotation for large simulations
- [ ] Add console output formatter for real-time viewing

#### Task 1.3: Create AI Room Factory
**File**: `backend/engine/ai_room_factory.py`
- [ ] Create method to generate all-bot rooms
- [ ] Configure bot names and initial state
- [ ] Bypass human player requirements
- [ ] Auto-start game after room creation

### Phase 2: Enhanced AI Logging (Week 1-2)

#### Task 2.1: Enhance Declaration Logging
**File**: `backend/engine/ai.py` (modify existing)
- [ ] Add decision context capture before `choose_declare`
- [ ] Log all intermediate calculations
- [ ] Record forbidden value adjustments
- [ ] Track confidence scores

#### Task 2.2: Enhance Turn Play Logging  
**File**: `backend/engine/ai_turn_strategy.py` (modify existing)
- [ ] Log complete TurnPlayContext
- [ ] Record all available plays considered
- [ ] Explain play selection reasoning
- [ ] Track urgency calculations

#### Task 2.3: Create Decision Analyzer
**File**: `backend/services/ai_decision_analyzer.py`
- [ ] Parse AI decisions from logs
- [ ] Identify decision patterns
- [ ] Flag suspicious decisions for review
- [ ] Generate decision quality metrics

### Phase 3: Game Flow Integration (Week 2)

#### Task 3.1: Integrate with State Machine
**Files**: `backend/engine/state_machine/*`
- [ ] Add debug mode flags to state transitions
- [ ] Capture state machine events for AI games
- [ ] Log phase transitions with full context
- [ ] Track timing of bot decisions

#### Task 3.2: Modify Bot Manager
**File**: `backend/engine/bot_manager.py`
- [ ] Add debug mode awareness
- [ ] Increase logging verbosity in debug mode
- [ ] Remove delays for fast simulation
- [ ] Add decision replay capability

#### Task 3.3: Create Game Recorder
**File**: `backend/services/ai_game_recorder.py`
- [ ] Save complete game state at each decision point
- [ ] Enable game replay functionality
- [ ] Export games in analyzable format
- [ ] Create game diff tool for comparing runs

### Phase 4: Analysis Tools (Week 2-3)

#### Task 4.1: Create Statistics Collector
**File**: `backend/services/ai_statistics.py`
- [ ] Track win rates by position
- [ ] Measure declaration accuracy
- [ ] Analyze common winning patterns
- [ ] Identify AI weaknesses

#### Task 4.2: Build Bug Detector
**File**: `backend/services/ai_bug_detector.py`
- [ ] Detect illegal moves
- [ ] Find inconsistent decisions
- [ ] Identify infinite loops
- [ ] Flag edge case failures

#### Task 4.3: Create Performance Analyzer
**File**: `backend/services/ai_performance_analyzer.py`
- [ ] Measure decision speed
- [ ] Track memory usage
- [ ] Identify performance bottlenecks
- [ ] Generate optimization recommendations

### Phase 5: Visualization and Reporting (Week 3)

#### Task 5.1: Create Report Generator
**File**: `backend/services/ai_report_generator.py`
- [ ] Generate HTML reports with charts
- [ ] Create decision tree visualizations
- [ ] Export CSV for external analysis
- [ ] Build comparison reports between AI versions

#### Task 5.2: Add Real-time Monitor
**File**: `backend/services/ai_game_monitor.py`
- [ ] Create terminal UI for live games
- [ ] Show AI thinking process in real-time
- [ ] Highlight interesting decisions
- [ ] Enable pause/resume for analysis

#### Task 5.3: Build Test Suite
**File**: `tests/ai_debug/`
- [ ] Create regression tests for AI decisions
- [ ] Build scenario-based test cases
- [ ] Add performance benchmarks
- [ ] Create edge case validators

## Bug Detection Metrics

### 1. Decision Consistency
- **Same situation, different decision**: Flag when AI makes different choices in identical scenarios
- **Confidence flip-flops**: Detect rapid changes in decision confidence
- **Strategy abandonment**: Identify when AI abandons winning strategies

### 2. Rule Violations
- **Illegal declarations**: Last player sum = 8, zero streak violations
- **Invalid plays**: Wrong piece counts, non-existent combinations
- **State confusion**: Playing pieces not in hand, wrong phase actions

### 3. Performance Issues
- **Decision loops**: Same evaluation repeated multiple times
- **Memory leaks**: Increasing memory usage over games
- **Timeout risks**: Decisions taking too long

### 4. Strategic Failures
- **Overcapture tendency**: Winning more piles than declared
- **Undercapture pattern**: Consistently failing to meet targets
- **Resource mismanagement**: Wasting strong pieces early
- **Poor opener usage**: Not maximizing control opportunities

## Success Metrics

### 1. AI Quality Metrics
- **Decision accuracy**: % of optimal decisions made
- **Win rate balance**: All positions should win 20-30% 
- **Declaration accuracy**: Declared vs actual within ±1
- **Resource efficiency**: Optimal piece usage

### 2. Game Quality Metrics
- **Game length**: Average 3-5 rounds
- **Score distribution**: Winner 50-80 points
- **Comeback frequency**: Trailing players can recover
- **Strategy diversity**: Multiple winning approaches

### 3. Technical Metrics
- **Decision speed**: <100ms per decision
- **Memory usage**: <50MB per game
- **CPU usage**: <10% per game
- **Log size**: <1MB per game

## Usage Examples

### Basic Simulation
```bash
# Run 10 games with standard settings
python backend/ai_debug_mode.py --games 10

# Output: Summary statistics and key insights
```

### Detailed Analysis
```bash
# Single game with full logging
python backend/ai_debug_mode.py --games 1 --log-level DETAILED --output game_analysis.json

# Output: Complete decision tree with reasoning
```

### Performance Testing
```bash
# High-speed simulation for statistics
python backend/ai_debug_mode.py --games 1000 --speed fast --stats-only

# Output: Statistical analysis report
```

### Bug Hunting
```bash
# Run with bug detection enabled
python backend/ai_debug_mode.py --games 100 --detect-bugs --stop-on-error

# Output: Bug report with reproduction steps
```

### Strategy Comparison
```bash
# Compare different AI versions
python backend/ai_debug_mode.py --games 100 --ai-version v1 --compare-with v2

# Output: Comparative analysis report
```

## Next Steps

1. **Prioritize Tasks**: Start with Phase 1 for basic functionality
2. **Iterative Development**: Build minimal version first, enhance gradually
3. **Early Testing**: Use debug mode immediately to find obvious bugs
4. **Continuous Improvement**: Refine logging based on actual debugging needs
5. **Documentation**: Keep examples of interesting games and decisions

## Appendix: Key Decisions to Log

### Declaration Phase
1. Why did AI declare 0? (weak hand analysis)
2. How does position affect declaration?
3. When does AI use forbidden value logic?
4. How accurate are pile count predictions?

### Turn Phase  
1. When does AI play defensively vs aggressively?
2. How does AI handle must-win situations?
3. When does AI sacrifice rounds?
4. How well does AI predict opponent plays?

### Strategic Decisions
1. Opener usage timing
2. Combo preservation vs immediate use
3. Resource management across rounds
4. Adaptation to opponent patterns

This comprehensive logging will provide the visibility needed to improve AI decision-making and create a more challenging and realistic game experience.