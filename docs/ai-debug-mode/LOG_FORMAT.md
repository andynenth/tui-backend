# AI Debug Mode Log Format Documentation

## Overview

AI Debug Mode logs are stored as JSON files containing structured event data for game analysis. Each game generates a single log file with all events from that game.

## File Structure

```
logs/ai_debug/
├── game_1.json
├── game_2.json
├── multi_game.json    # Contains multiple games
└── stats.csv          # Exported statistics
```

## Log File Format

### Top-Level Structure

```json
{
  "game_id": "AI_123456",
  "timestamp": "2025-08-29T12:34:56.789Z",
  "log_level": "decision",
  "events": [...]
}
```

### Event Types

#### 1. Game Start Event

```json
{
  "event": "game_start",
  "game_id": "AI_123456",
  "players": ["Bot 1", "Bot 2", "Bot 3", "Bot 4"],
  "round_starter": "Bot 1",
  "initial_hands": null,  // Can be populated in detailed mode
  "timestamp": "2025-08-29T12:34:56.789Z"
}
```

#### 2. Declaration Event

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
  "hand_analysis": {
    "raw_hand": ["GENERAL_BLACK", "ADVISOR_RED", ...],
    "hand_strength": {
      "opener_count": 2,
      "strong_combos": ["THREE_OF_A_KIND"],
      "weak_pieces": 3,
      "average_piece_value": 7.5
    }
  },
  "decision_factors": {
    "has_general_red": false,
    "pile_room": 8,
    "field_strength": "normal",
    "forbidden_values": []
  },
  "decision": {
    "declared_value": 3,
    "reasoning": "Starter with 2 openers and 1 combos",
    "confidence": 0.8
  },
  "bugs_detected": [],  // Optional, populated if bugs found
  "timestamp": "2025-08-29T12:34:57.123Z",
  "game_id": "AI_123456"
}
```

#### 3. Turn Play Event

```json
{
  "event": "turn_play",
  "player": "Bot 1",
  "turn_data": {
    "turn_number": 1,
    "required_piece_count": null,
    "my_captured": 0,
    "my_declared": 3,
    "pieces_remaining": 8,
    "selected_play": ["GENERAL_BLACK"],
    "play_type": "SINGLE",
    "reasoning": "Must win - need 3 more piles",
    "am_i_starter": true,
    "current_winner": null,
    "piles_needed": 3
  },
  "timestamp": "2025-08-29T12:34:58.456Z",
  "game_id": "AI_123456"
}
```

#### 4. Round End Event

```json
{
  "event": "round_end",
  "round_number": 1,
  "player_performance": {
    "Bot 1": {
      "declared": 3,
      "captured": 3,
      "accuracy": 1.0,
      "score_gained": 16
    },
    "Bot 2": {
      "declared": 2,
      "captured": 1,
      "accuracy": 0.0,
      "score_gained": -2
    }
    // ... other players
  },
  "timestamp": "2025-08-29T12:35:10.789Z",
  "game_id": "AI_123456"
}
```

#### 5. Bug Detected Event

```json
{
  "event": "bug_detected",
  "bug_type": "zero_declaration_strong_hand",
  "severity": "medium",
  "player": "Bot 2",
  "phase": "declaration",
  "description": "Declared 0 with 2 openers available",
  "context": {
    "declaration": 0,
    "openers": 2,
    "zero_streak": 0
  },
  "suggested_fix": "Force minimum declaration (1-2) with 2+ openers",
  "timestamp": "2025-08-29T12:34:57.890Z",
  "game_id": "AI_123456"
}
```

#### 6. Game End Event

```json
{
  "event": "game_end",
  "game_id": "AI_123456",
  "winner": ["Bot 3"],
  "final_scores": {
    "Bot 1": 42,
    "Bot 2": 28,
    "Bot 3": 58,
    "Bot 4": 16
  },
  "rounds_played": 7,
  "game_duration": 45.2,
  "timestamp": "2025-08-29T12:35:42.123Z"
}
```

## Log Levels

### Summary Level
- Only game start/end events
- Round end summaries
- Final scores and winner

### Decision Level
- All summary events
- Declaration decisions with reasoning
- Turn play decisions with basic info
- Bug detection events

### Detailed Level
- All decision events
- Complete hand contents
- Full AI reasoning traces
- Performance metrics
- Debug information

## Analyzing Logs

### Using analyze_ai_logs.py

```bash
# Basic analysis
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json

# Export statistics
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json --export-stats stats.csv

# Save report
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json --output report.txt
```

### Manual Analysis with jq

```bash
# Count bugs by type
jq '.events[] | select(.event == "bug_detected") | .bug_type' game_1.json | sort | uniq -c

# Extract final scores
jq '.events[] | select(.event == "game_end") | .final_scores' game_1.json

# Find all zero declarations
jq '.events[] | select(.event == "declaration" and .decision.declared_value == 0)' game_1.json
```

## Extended Metrics

The `analyze_metrics.py` tool provides additional analysis:

```json
{
  "summary": {
    "total_games": 50,
    "avg_winning_score": 52.4,
    "avg_game_length": 6.8
  },
  "winning_scores": {
    "distribution": {
      "58": 2,
      "54": 1,
      "52": 1,
      "38": 1
    },
    "statistics": {
      "mean": 52.4,
      "median": 54.0,
      "min": 38,
      "max": 58
    }
  },
  "game_lengths": {
    "distribution": {
      "4": 1,
      "6": 1,
      "7": 2,
      "10": 1
    }
  }
}
```

## Best Practices

1. **Use appropriate log level**: Decision level for most analysis, detailed for debugging
2. **Regular cleanup**: Logs can grow large; archive old logs periodically
3. **Batch analysis**: Process multiple games together for statistical significance
4. **Version tracking**: Note AI version when comparing logs across changes