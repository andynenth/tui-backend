# Game Log Structure Plan

## Overview
This document outlines the comprehensive data structure for recording all game events and AI decisions in JSON format for analysis, debugging, and machine learning purposes.

## Log Levels
- **summary**: Basic game flow and outcomes
- **decision**: + AI decision reasoning
- **detailed**: + Full context including hands, available plays, and calculations

## Comprehensive Event Structure

### 1. Game Initialization
```json
{
  "event": "game_start",
  "timestamp": "ISO-8601",
  "game_id": "unique_id",
  "game_metadata": {
    "version": "1.0",
    "mode": "ai_vs_ai|human_vs_ai|multiplayer",
    "settings": {
      "win_score": 50,
      "pieces_per_player": 8,
      "zero_declaration_limit": 2
    }
  },
  "players": [
    {
      "id": "player_id",
      "name": "Bot 1",
      "type": "ai|human",
      "ai_config": {
        "strategy": "aggressive|balanced|conservative",
        "difficulty": "easy|medium|hard"
      }
    }
  ],
  "initial_state": {
    "round_starter": "Bot 1",
    "dealer": "Bot 4",
    "hands": {
      "Bot 1": ["GENERAL_RED", "ADVISOR_BLACK", ...],
      "Bot 2": [...],
      "Bot 3": [...],
      "Bot 4": [...]
    }
  }
}
```

### 2. Round Events

#### Round Start
```json
{
  "event": "round_start",
  "timestamp": "ISO-8601",
  "round_number": 1,
  "round_starter": "Bot 1",
  "dealer": "Bot 4",
  "hands_dealt": {
    "Bot 1": ["SOLDIER_RED", "ELEPHANT_BLACK", ...],
    "Bot 2": [...],
    "Bot 3": [...],
    "Bot 4": [...]
  },
  "deck_state": {
    "remaining_pieces": 0,
    "shuffle_seed": "optional_for_replay"
  }
}
```

#### Declaration Phase
```json
{
  "event": "declaration",
  "timestamp": "ISO-8601",
  "round_number": 1,
  "player": "Bot 1",
  "declaration_order": 1,
  "game_state": {
    "previous_declarations": [],
    "zero_streak_count": 0,
    "pile_room": 8,
    "forbidden_values": []
  },
  "hand_analysis": {
    "raw_hand": ["GENERAL_RED", "ADVISOR_BLACK", ...],
    "opener_count": 2,
    "combo_count": 1,
    "weak_pieces": 3,
    "total_hand_value": 72,
    "possible_plays": [
      {"type": "opener", "pieces": ["GENERAL_RED"], "value": 14},
      {"type": "combo", "pieces": ["SOLDIER_RED", "SOLDIER_BLACK"], "value": 2}
    ]
  },
  "ai_reasoning": {
    "strategy": "balanced",
    "factors_considered": {
      "hand_strength": 0.7,
      "position_advantage": 0.5,
      "pile_room_constraint": 1.0,
      "zero_streak_risk": 0.0
    },
    "options_evaluated": [
      {"value": 0, "score": 0.2, "reason": "weak hand"},
      {"value": 1, "score": 0.8, "reason": "conservative target"},
      {"value": 2, "score": 0.6, "reason": "moderate risk"}
    ]
  },
  "decision": {
    "declared_value": 1,
    "confidence": 0.8,
    "reasoning": "Conservative declaration with 2 openers"
  },
  "timing": {
    "thinking_time_ms": 125,
    "total_time_ms": 150
  }
}
```

#### Turn Play Phase
```json
{
  "event": "turn_play",
  "timestamp": "ISO-8601",
  "round_number": 1,
  "turn_number": 1,
  "player": "Bot 1",
  "game_context": {
    "current_starter": "Bot 1",
    "required_piece_count": 1,
    "pieces_played_this_turn": [],
    "current_winning_play": null,
    "current_winner": null
  },
  "player_state": {
    "hand_before": ["GENERAL_RED", "ADVISOR_BLACK", ...],
    "pieces_in_hand": 8,
    "captured_piles": 0,
    "declared_target": 1,
    "piles_needed": 1,
    "at_target": false,
    "over_target": false
  },
  "available_plays": [
    {
      "play_type": "SINGLE",
      "pieces": ["GENERAL_RED"],
      "value": 14,
      "rank": 1,
      "beats_current": true
    },
    {
      "play_type": "SINGLE",
      "pieces": ["ADVISOR_BLACK"],
      "value": 12,
      "rank": 1,
      "beats_current": true
    },
    {
      "play_type": "PAIR",
      "pieces": ["SOLDIER_RED", "SOLDIER_BLACK"],
      "value": 2,
      "rank": 2,
      "beats_current": true
    }
  ],
  "ai_reasoning": {
    "situation_assessment": {
      "urgency": "low",
      "winning_probability": 0.7,
      "risk_level": "low"
    },
    "strategy": "opener_as_starter",
    "play_evaluation": [
      {
        "play": ["GENERAL_RED"],
        "score": 0.9,
        "reason": "Strong opener as starter"
      },
      {
        "play": ["SOLDIER_RED"],
        "score": 0.3,
        "reason": "Weak, save for later"
      }
    ]
  },
  "decision": {
    "selected_play": ["GENERAL_RED"],
    "play_type": "SINGLE",
    "play_value": 14,
    "reasoning": "Playing strong opener as turn starter",
    "expected_outcome": "likely_win"
  },
  "hand_after": ["ADVISOR_BLACK", "ELEPHANT_BLACK", ...],
  "timing": {
    "thinking_time_ms": 87,
    "total_time_ms": 95
  }
}
```

#### Turn Result
```json
{
  "event": "turn_result",
  "timestamp": "ISO-8601",
  "round_number": 1,
  "turn_number": 1,
  "all_plays": [
    {"player": "Bot 1", "play": ["GENERAL_RED"], "type": "SINGLE", "value": 14},
    {"player": "Bot 2", "play": ["ADVISOR_BLACK"], "type": "SINGLE", "value": 12},
    {"player": "Bot 3", "play": ["ELEPHANT_RED"], "type": "SINGLE", "value": 10},
    {"player": "Bot 4", "play": ["SOLDIER_BLACK"], "type": "SINGLE", "value": 2}
  ],
  "winner": "Bot 1",
  "winning_play": ["GENERAL_RED"],
  "pile_captured": true,
  "updated_pile_counts": {
    "Bot 1": 1,
    "Bot 2": 0,
    "Bot 3": 0,
    "Bot 4": 0
  }
}
```

### 3. Special Events

#### Weak Hand Redeal
```json
{
  "event": "weak_hand_check",
  "timestamp": "ISO-8601",
  "round_number": 1,
  "player": "Bot 2",
  "hand": ["SOLDIER_RED", "SOLDIER_BLACK", ...],
  "hand_analysis": {
    "highest_piece_value": 9,
    "total_value": 42,
    "qualifies_for_redeal": true
  },
  "decision": "request_redeal",
  "other_players_responses": {
    "Bot 1": "accept",
    "Bot 3": "decline",
    "Bot 4": "accept"
  },
  "redeal_approved": false,
  "reason": "Not all players accepted"
}
```

#### Rule Violations & Bugs
```json
{
  "event": "bug_detected",
  "timestamp": "ISO-8601",
  "bug_type": "playing_piece_not_in_hand",
  "severity": "critical",
  "player": "Bot 3",
  "phase": "turn_play",
  "context": {
    "round": 2,
    "turn": 4,
    "hand_before": ["SOLDIER_RED", "ELEPHANT_BLACK"],
    "attempted_play": ["GENERAL_RED"],
    "valid_plays": [["SOLDIER_RED"], ["ELEPHANT_BLACK"]]
  },
  "description": "Played GENERAL_RED which was not in hand",
  "suggested_fix": "Validate plays against current hand"
}
```

### 4. Round & Game Completion

#### Round End
```json
{
  "event": "round_end",
  "timestamp": "ISO-8601",
  "round_number": 1,
  "round_statistics": {
    "total_turns": 8,
    "duration_ms": 5234,
    "plays_by_type": {
      "SINGLE": 24,
      "PAIR": 6,
      "THREE_OF_A_KIND": 1,
      "STRAIGHT": 1
    }
  },
  "player_performance": {
    "Bot 1": {
      "declared": 1,
      "captured": 1,
      "score_change": 12,
      "accuracy": 1.0,
      "opener_usage": 0.5,
      "invalid_plays": 0
    }
  },
  "scoring_details": {
    "Bot 1": {"declared": 1, "captured": 1, "exact": true, "multiplier": 12, "score": 12},
    "Bot 2": {"declared": 3, "captured": 2, "exact": false, "penalty": -2, "score": -2}
  },
  "cumulative_scores": {
    "Bot 1": 12,
    "Bot 2": -2,
    "Bot 3": 8,
    "Bot 4": -4
  }
}
```

#### Game End
```json
{
  "event": "game_end",
  "timestamp": "ISO-8601",
  "game_id": "unique_id",
  "winner": "Bot 1",
  "final_scores": {
    "Bot 1": 52,
    "Bot 2": 38,
    "Bot 3": 24,
    "Bot 4": 16
  },
  "game_statistics": {
    "total_rounds": 5,
    "total_turns": 37,
    "duration_seconds": 45.3,
    "total_redeals": 1,
    "bugs_detected": 2
  },
  "player_statistics": {
    "Bot 1": {
      "rounds_won": 3,
      "declaration_accuracy": 0.75,
      "average_declared": 2.4,
      "average_captured": 2.1,
      "perfect_rounds": 2,
      "opener_efficiency": 0.82
    }
  },
  "ai_performance": {
    "decision_time_avg_ms": 95,
    "strategy_changes": 3,
    "learning_indicators": {
      "adaptation_score": 0.8,
      "mistake_reduction": 0.6
    }
  }
}
```

## Additional Tracking Recommendations

### 1. Performance Metrics
- Decision timing for each AI action
- Memory/CPU usage per turn
- Cache hit rates for repeated scenarios

### 2. Learning Data
- Success rate of different strategies
- Correlation between hand strength and declaration accuracy
- Optimal play patterns in different scenarios

### 3. Debug Information
- Random seed for reproducibility
- AI internal state snapshots
- Error traces and recovery attempts

### 4. Replay Support
- Include enough data to replay any game exactly
- Support for stepping through turns
- Ability to branch from any point

## Implementation Notes

1. **Compression**: For large-scale data collection, consider:
   - Storing hands as piece IDs instead of full names
   - Using abbreviated event types
   - Compressing repeated structures

2. **Privacy**: If human players involved:
   - Anonymize player names
   - Remove timing data that could identify players
   - Optional opt-out for detailed logging

3. **Versioning**: Include schema version for backward compatibility

4. **Real-time Streaming**: Support both batch and streaming writes for live analysis

This comprehensive logging will enable:
- Detailed AI behavior analysis
- Bug reproduction and fixing
- Machine learning training data
- Game replay and visualization
- Performance optimization
- Strategic pattern discovery
