# AI Debug Mode Guide

## Overview

The AI Debug Mode provides a powerful framework for testing and analyzing AI behavior without the full WebSocket infrastructure. It enables rapid iteration, performance testing, and detailed decision analysis through direct game execution.

## Architecture

```
┌────────────────────┐
│ ai_debug_simple.py │
├────────────────────┤
│ • Direct execution │
│ • No WebSocket     │
│ • Pure game logic  │
└─────────┬──────────┘
          │
    ┌─────▼─────────┐
    │  Game Engine  │
    │  (Direct API) │
    └─────┬─────────┘
          │
    ┌─────▼─────────┐     ┌──────────────┐
    │   AI Logger   │────►│  JSON Logs   │
    │ (Structured)  │     │ (Detailed)   │
    └─────┬─────────┘     └──────────────┘
          │
    ┌─────▼─────────┐     ┌──────────────┐
    │ Bug Detector  │────►│ Bug Reports  │
    │ (Automatic)   │     │ (Severity)   │
    └───────────────┘     └──────────────┘
```

## Components

### 1. AI Debug Simple (`backend/ai_debug_simple.py`)

The main debug runner that executes games with all AI players.

#### Key Features

- **Direct Execution**: Bypasses WebSocket layer for speed
- **Detailed Logging**: Captures every decision and state change
- **Performance Metrics**: Tracks execution time and decision speed
- **Bug Detection**: Automatic identification of AI issues

#### Usage

```bash
# Run a single game with detailed logging
python backend/ai_debug_simple.py --games 1 --log-level detailed

# Run multiple games with summary
python backend/ai_debug_simple.py --games 100 --log-level summary

# Run with specific output file
python backend/ai_debug_simple.py --games 10 --output game_analysis.json

# Benchmark performance
python backend/tools/benchmark_ai_debug.py
```

#### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--games` | 1 | Number of games to run |
| `--log-level` | summary | Logging detail: summary, decision, detailed |
| `--output` | auto | Output file path (auto generates timestamp) |
| `--verbose` | False | Enable console output |

### 2. AI Logger (`backend/services/ai_logger.py`)

Structured logging system for AI decisions.

#### Log Levels

1. **Summary Level** (Default)
   - Game start/end events
   - Final scores and winners
   - Basic statistics

2. **Decision Level**
   - All summary events
   - AI declaration decisions with reasoning
   - AI play decisions with context
   - Strategic plan details

3. **Detailed Level**
   - All decision events
   - Full game state at each decision
   - Hand contents and possibilities
   - Performance metrics

#### Log Structure

```json
{
    "game_id": "AI_123456",
    "start_time": "2025-09-02T10:30:00Z",
    "events": [
        {
            "type": "game_start",
            "timestamp": 1693654200.123,
            "data": {
                "players": ["Bot 1", "Bot 2", "Bot 3", "Bot 4"],
                "round": 1
            }
        },
        {
            "type": "ai_decision",
            "timestamp": 1693654201.456,
            "player": "Bot 1",
            "phase": "declaration",
            "decision": 3,
            "reasoning": {
                "hand_strength": "strong",
                "combo_count": 2,
                "opener_count": 3,
                "position": 0,
                "pile_room": 8
            },
            "context": {
                "previous_declarations": [],
                "field_strength": "normal"
            }
        }
    ],
    "summary": {
        "winner": "Bot 2",
        "final_scores": {"Bot 1": 25, "Bot 2": 51, "Bot 3": 18, "Bot 4": 32},
        "rounds_played": 3,
        "total_duration_ms": 4523
    }
}
```

### 3. AI Bug Detector (`backend/services/ai_bug_detector.py`)

Automatic detection of AI bugs and issues.

#### Bug Categories

1. **Invalid Plays**
   - Playing pieces not in hand
   - Invalid combination types
   - Rule violations

2. **Suboptimal Decisions**
   - Never-win combo plays
   - Poor declaration choices
   - Missed winning opportunities

3. **Logic Errors**
   - Incorrect pile counting
   - Wrong play type matching
   - State inconsistencies

#### Bug Severity Levels

```python
class BugSeverity(Enum):
    CRITICAL = "critical"   # Game-breaking bugs
    HIGH = "high"          # Serious strategy flaws
    MEDIUM = "medium"      # Suboptimal but playable
    LOW = "low"            # Minor improvements
```

## Common Use Cases

### 1. Testing New AI Strategies

```python
# Modify AI strategy in ai.py or ai_turn_strategy.py
# Run debug mode to test changes
python backend/ai_debug_simple.py --games 50 --log-level decision

# Analyze results
python analyze_ai_logs.py logs/ai_debug/game_*.json
```

### 2. Debugging Specific Scenarios

```python
# Create test scenario in SimpleAIGame
def setup_game(self):
    # Custom setup for specific scenario
    players = []
    for i in range(4):
        player = Player(f"Bot {i + 1}", is_bot=True)
        # Set specific hands or conditions
        if i == 0:
            player.hand = [/* specific pieces */]
        players.append(player)
```

### 3. Performance Benchmarking

```bash
# Run benchmark suite
python backend/tools/benchmark_ai_debug.py

# Output:
# Games: 100
# Avg game duration: 4.23s
# Avg decision time: 0.8ms
# Total failures: 0
```

### 4. Regression Testing

```bash
# Run all AI regression tests
python tests/ai_regression/run_all_regression_tests.py

# Run specific test
pytest tests/ai_regression/test_never_win_combo.py -v
```

## Analyzing AI Logs

### Finding Patterns

```python
# Load and analyze logs
import json
from pathlib import Path

def analyze_declarations(log_file):
    with open(log_file) as f:
        data = json.load(f)
    
    declarations = {}
    for event in data['events']:
        if event['type'] == 'ai_decision' and event['phase'] == 'declaration':
            player = event['player']
            decision = event['decision']
            declarations.setdefault(player, []).append(decision)
    
    # Calculate averages
    for player, decls in declarations.items():
        avg = sum(decls) / len(decls)
        print(f"{player}: avg declaration = {avg:.2f}")
```

### Identifying Issues

```python
def find_never_win_plays(log_file):
    with open(log_file) as f:
        data = json.load(f)
    
    issues = []
    for event in data['events']:
        if event.get('bugs'):
            for bug in event['bugs']:
                if 'never-win' in bug['description']:
                    issues.append({
                        'player': event['player'],
                        'turn': event.get('turn_number'),
                        'bug': bug
                    })
    return issues
```

## Best Practices

### 1. Systematic Testing

- Run multiple games for statistical significance
- Test edge cases explicitly
- Compare before/after metrics

### 2. Log Analysis

- Use decision level for strategy analysis
- Use detailed level for bug investigation
- Archive important test results

### 3. Performance Monitoring

- Track decision time trends
- Monitor memory usage
- Identify bottlenecks

### 4. Bug Documentation

- Document reproduction steps
- Include log excerpts
- Track fix verification

## Integration with Development

### 1. Pre-commit Testing

```bash
# Add to pre-commit hook
python backend/ai_debug_simple.py --games 10 --log-level summary
if [ $? -ne 0 ]; then
    echo "AI tests failed"
    exit 1
fi
```

### 2. Continuous Integration

```yaml
# GitHub Actions example
- name: Run AI Tests
  run: |
    python backend/ai_debug_simple.py --games 100
    python tests/ai_regression/run_all_regression_tests.py
```

### 3. Performance Tracking

```python
# Track performance over time
results = []
for commit in git_commits:
    checkout(commit)
    result = run_benchmark()
    results.append({
        'commit': commit,
        'avg_game_time': result['avg_time'],
        'decision_time': result['avg_decision']
    })
plot_performance_trend(results)
```

## Troubleshooting

### Common Issues

1. **ImportError**: Ensure you're in the project root
   ```bash
   cd /path/to/liap-tui
   python backend/ai_debug_simple.py
   ```

2. **Log Directory Missing**: Auto-created but check permissions
   ```bash
   mkdir -p logs/ai_debug
   ```

3. **Memory Issues**: Reduce game count or log level
   ```bash
   python backend/ai_debug_simple.py --games 10 --log-level summary
   ```

### Debug Tips

1. **Isolate Issues**: Create minimal reproduction
2. **Compare Logs**: Diff good vs bad behavior
3. **Use Breakpoints**: Debug specific decisions
4. **Check Regression**: Run test suite after fixes

## Future Enhancements

1. **Visual Analysis**: Graphical log visualization
2. **Real-time Monitoring**: Live game observation
3. **AI Comparison**: Side-by-side strategy testing
4. **Custom Scenarios**: Scriptable test cases
5. **Performance Profiling**: Detailed bottleneck analysis