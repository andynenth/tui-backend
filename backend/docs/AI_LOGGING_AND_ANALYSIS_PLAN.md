# AI Logging and Analysis Plan

## Overview

This document describes the actual data we can capture from the AI system and the analysis tools we can build based on this real data. No assumptions are made about future capabilities - only what is currently available in the codebase.

## Currently Available Data

### 1. Game Initialization
```json
{
  "event": "game_start",
  "game_id": "AI_123456",
  "players": ["Bot 1", "Bot 2", "Bot 3", "Bot 4"],
  "round_starter": "Bot 2",
  "initial_hands": {
    "Bot 1": ["GENERAL_RED", "SOLDIER_BLACK", ...],
    "Bot 2": ["ADVISOR_BLACK", "HORSE_RED", ...],
    "Bot 3": ["ELEPHANT_RED", "CANNON_BLACK", ...],
    "Bot 4": ["CHARIOT_RED", "SOLDIER_RED", ...]
  }
}
```
**Available**: Player names, round starter, all initial hands
**NOT Available**: Deck order, dealing sequence

### 2. Declaration Phase
```json
{
  "event": "declaration",
  "player": "Bot 1",
  "phase_data": {
    "position": 0,
    "previous_declarations": [],
    "is_starter": true,
    "zero_streak": 0
  },
  "decision": {
    "declared_value": 2,
    "reasoning": "Strong hand with multiple combos"
  }
}
```
**Available**: Position in order, previous declarations, zero streak, final declaration, reasoning
**NOT Available**: Real-time validation, forbidden values calculation, other players' thought process

### 3. Turn Play Decisions
```json
{
  "event": "turn_play",
  "player": "Bot 1",
  "turn_context": {
    "turn_number": 3,
    "required_pieces": 1,
    "current_winner": "Bot 3",
    "am_starter": false
  },
  "my_situation": {
    "captured_piles": 0,
    "declared_target": 2,
    "piles_needed": 2,
    "pieces_remaining": 6
  },
  "play_decision": {
    "selected_play": ["GENERAL_RED"],
    "play_type": "SINGLE",
    "reasoning": "Must win with opener"
  },
  "hand_before": ["GENERAL_RED", "ADVISOR_BLACK", "HORSE_RED", ...]
}
```
**Available**: Current AI's play, hand before play, game state from AI's perspective
**NOT Available**: Other players' plays this turn, turn winner, updated pile counts

### 4. Round Results
```json
{
  "event": "round_end",
  "round_number": 1,
  "player_performance": {
    "Bot 1": {"declared": 2, "captured": 1, "accuracy": 0.5, "score_gained": -2},
    "Bot 2": {"declared": 3, "captured": 3, "accuracy": 1.0, "score_gained": 16},
    "Bot 3": {"declared": 0, "captured": 2, "accuracy": 0.0, "score_gained": -4},
    "Bot 4": {"declared": 1, "captured": 2, "accuracy": 0.5, "score_gained": -2}
  }
}
```
**Available**: Final declared vs captured, accuracy, score changes
**NOT Available**: Turn-by-turn progression, winning plays

### 5. Bug Detection
```json
{
  "event": "bug_detected",
  "bug_type": "playing_piece_not_in_hand",
  "severity": "critical",
  "player": "Bot 1",
  "phase": "turn_play",
  "description": "Played GENERAL_RED which was not in hand"
}
```
**Available**: Rule violations, strategic anomalies with context
**NOT Available**: Root cause analysis, AI internal state

## Analysis Tools We Can Build

### 1. Declaration Analyzer
```python
def analyze_declarations(game_logs):
    """Analyze declaration patterns from available data"""
    return {
        'position_impact': calculate_position_advantage(),
        'zero_streak_patterns': track_zero_declaration_usage(),
        'declaration_accuracy': compare_declared_vs_captured(),
        'starter_advantage': measure_first_player_benefits()
    }
```

### 2. Play Pattern Detector
```python
def detect_play_patterns(game_logs):
    """Identify patterns in AI play decisions"""
    return {
        'opener_usage': track_high_value_piece_timing(),
        'combo_preferences': analyze_combination_choices(),
        'disposal_strategies': identify_invalid_play_patterns(),
        'critical_moments': find_must_win_situations()
    }
```

### 3. Hand Strength Evaluator
```python
def evaluate_hand_strength(game_logs):
    """Analyze initial hand quality and outcomes"""
    return {
        'weak_hand_frequency': count_no_strong_piece_hands(),
        'hand_strength_correlation': relate_hand_quality_to_score(),
        'piece_distribution': analyze_piece_type_balance()
    }
```

### 4. Rule Violation Tracker
```python
def track_rule_violations(game_logs):
    """Monitor rule violations from bug detection"""
    return {
        'violation_types': count_by_bug_type(),
        'player_compliance': violations_per_player(),
        'phase_violations': violations_by_game_phase()
    }
```

### 5. Performance Metrics
```python
def calculate_performance_metrics(game_logs):
    """Measure AI performance from available data"""
    return {
        'win_rates': calculate_player_win_percentages(),
        'average_scores': compute_score_statistics(),
        'declaration_success': measure_prediction_accuracy(),
        'round_efficiency': analyze_rounds_to_win()
    }
```

## What We CANNOT Analyze (Without Additional Logging)

1. **Turn Resolution Details**
   - Who won each turn
   - All players' plays in the same turn
   - Turn-by-turn pile count changes

2. **Complete Game Flow**
   - Full turn sequence
   - Player elimination order
   - Momentum shifts

3. **Strategic Depth**
   - Bluffing patterns (need all players' plays)
   - Counter-play strategies
   - Turn timing optimization

4. **AI Decision Process**
   - Alternative plays considered
   - Evaluation scores for each option
   - Strategy switching logic

## Implementation Priority

### Phase 1: Immediate Value (Current Data)
1. Declaration accuracy analyzer
2. Hand strength evaluator  
3. Rule violation tracker
4. Basic performance metrics

### Phase 2: Enhanced Logging Required
1. Add turn result logging
2. Capture all players' plays per turn
3. Track pile count changes
4. Record turn winners

### Phase 3: Deep Analysis (Future)
1. Strategy pattern recognition
2. Learning curve analysis
3. Opponent modeling
4. Meta-game evolution

## Analysis Script Structure

```python
# analyze_ai_games.py
class AIGameAnalyzer:
    def __init__(self, log_directory):
        self.games = self.load_game_logs(log_directory)
    
    def analyze_all(self):
        """Run all available analyses on current data"""
        return {
            'games_analyzed': len(self.games),
            'declaration_analysis': self.analyze_declarations(),
            'play_patterns': self.detect_play_patterns(),
            'hand_evaluation': self.evaluate_hands(),
            'rule_compliance': self.check_violations(),
            'performance': self.calculate_metrics()
        }
    
    # Individual analysis methods using ONLY available data
```

## Validation Requirements

All analysis tools must:
1. Use only data fields that exist in current logs
2. Handle missing data gracefully
3. Not assume information we don't capture
4. Clearly document data limitations
5. Produce actionable insights from available data

## Summary

This plan focuses on maximizing value from currently available data while clearly identifying gaps. No assumptions are made about data we cannot capture. The analysis tools are designed to work with the actual log structure produced by the current AI system.