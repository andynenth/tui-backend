# AI Debug Mode - Comprehensive Guide

## Overview

The AI Debug Mode provides a powerful framework for testing and analyzing AI behavior without the full WebSocket infrastructure. It enables rapid iteration, performance testing, and detailed decision analysis through direct game execution.

### Key Benefits
- **Direct Execution**: Bypasses WebSocket layer for speed
- **Detailed Logging**: Captures every decision and state change
- **Performance Metrics**: Tracks execution time and decision speed
- **Bug Detection**: Automatic identification of AI issues
- **Statistical Analysis**: Run multiple games for pattern detection

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

## Quick Start

```bash
# Run a single AI game with default settings
python backend/ai_debug_simple.py

# Run 10 games with detailed logging
python backend/ai_debug_simple.py --games 10 --log-level detailed

# Run 100 games quickly for statistical analysis
python backend/ai_debug_simple.py --games 100 --log-level summary

# View a game log in human-readable format
python backend/tools/read_ai_game_log.py AI_393635
```

## Command Line Options

### Basic Options
- `--games N` - Number of games to simulate (default: 1)
- `--log-level [summary|decision|detailed]` - Logging verbosity (default: decision)
- `--verbose` - Show detailed AI reasoning in console output
- `--output FILE` - Custom output file (default: logs/ai_debug/game_{timestamp}.json)
- `--seed NUMBER` - Random seed for reproducible testing

### Advanced Options
- `--profile` - Enable performance profiling
- `--no-detection` - Disable automatic bug detection
- `--max-rounds` - Limit rounds per game (default: unlimited)

### Examples

```bash
# Run 50 games with decision-level logging
python backend/ai_debug_simple.py --games 50 --log-level decision

# Run games with verbose console output for debugging
python backend/ai_debug_simple.py --games 5 --verbose

# Save logs to a specific file
python backend/ai_debug_simple.py --games 10 --output logs/ai_debug/test_run.json

# Reproducible test run
python backend/ai_debug_simple.py --games 3 --seed 12345 --log-level detailed
```

## Log Levels Explained

### Summary Level
- Minimal logging for performance testing
- Records only game start/end and round summaries
- Includes complete turn results with all plays and winners
- Best for: Statistical analysis, performance testing

### Decision Level
- Logs AI decision points and chosen actions
- Includes scoring calculations and pile tracking
- Shows turn results with winning plays
- Best for: General debugging, AI behavior analysis

### Detailed Level
- Complete game state at each phase
- All AI evaluations and reasoning
- Full hand visibility for analysis
- Best for: Deep debugging, algorithm development

## Components

### 1. AI Debug Simple (`backend/ai_debug_simple.py`)

The main debug runner that executes games with all AI players.

#### Key Features
- Direct game engine integration
- Structured JSON logging
- Real-time bug detection
- Performance profiling support

#### Implementation Details
```python
# Simplified game loop
game = Game()
for player_name in ["AI_1", "AI_2", "AI_3", "AI_4"]:
    game.add_player(player_name)

while not game.is_finished():
    # Direct AI decision making
    action = ai_player.decide(game_state)
    game.process_action(action)
    logger.log_decision(action, reasoning)
```

### 2. AI Logger (`backend/engine/ai_logger.py`)

Structured logging system for AI decisions and game events.

#### Log Structure
```json
{
    "session_id": "DEBUG_20240115_143022",
    "games": [
        {
            "game_id": "AI_123456",
            "start_time": "2024-01-15T14:30:22",
            "players": ["AI_1", "AI_2", "AI_3", "AI_4"],
            "rounds": [
                {
                    "round_number": 1,
                    "redeal_multiplier": 1.0,
                    "events": [...]
                }
            ]
        }
    ]
}
```

#### Key Methods
- `log_game_start()` - Initialize new game log
- `log_decision()` - Record AI decision with reasoning
- `log_bug_detected()` - Flag potential issues
- `write_summary()` - Generate game statistics

### 3. Bug Detection System

Automatic detection of common AI issues.

#### Detected Issues
1. **Invalid Plays** - AI attempts illegal moves
2. **Suboptimal Decisions** - Obviously poor choices
3. **Timing Violations** - Decisions taking too long
4. **State Corruption** - Inconsistent game state
5. **Logic Errors** - AI reasoning failures

#### Bug Report Format
```json
{
    "bug_type": "INVALID_PLAY",
    "severity": "HIGH",
    "round": 3,
    "turn": 5,
    "player": "AI_2",
    "description": "Attempted to play 3 pieces when 2 required",
    "game_state": {...},
    "ai_reasoning": {...}
}
```

## Analysis Tools

### 1. Log Reader (`backend/tools/read_ai_game_log.py`)

Human-readable log viewer with filtering options.

```bash
# View full game log
python backend/tools/read_ai_game_log.py AI_123456

# Show only round 3
python backend/tools/read_ai_game_log.py AI_123456 --round 3

# Filter by player
python backend/tools/read_ai_game_log.py AI_123456 --player AI_2

# Show only bugs
python backend/tools/read_ai_game_log.py AI_123456 --bugs-only
```

### 2. Statistics Generator (`backend/tools/ai_stats.py`)

Analyze patterns across multiple games.

```bash
# Generate statistics from log directory
python backend/tools/ai_stats.py logs/ai_debug/

# Compare AI versions
python backend/tools/ai_stats.py --compare v1.0 v2.0

# Export to CSV
python backend/tools/ai_stats.py --export stats.csv
```

### 3. Performance Analyzer

Track AI decision timing and resource usage.

```python
# In debug mode with profiling
python backend/ai_debug_simple.py --games 10 --profile

# Generates performance report:
# - Average decision time per phase
# - Memory usage patterns
# - CPU utilization
# - Bottleneck identification
```

## Common Use Cases

### 1. Testing New AI Logic
```bash
# Run small test batch with detailed logging
python backend/ai_debug_simple.py --games 5 --log-level detailed --verbose

# Check for bugs in the output
grep -i "bug" logs/ai_debug/game_*.json
```

### 2. Performance Benchmarking
```bash
# Run many games quickly
python backend/ai_debug_simple.py --games 1000 --log-level summary

# Analyze statistics
python backend/tools/ai_stats.py logs/ai_debug/
```

### 3. Debugging Specific Scenarios
```bash
# Reproducible test case
python backend/ai_debug_simple.py --seed 42 --games 1 --log-level detailed

# Step through the log
python backend/tools/read_ai_game_log.py AI_* --interactive
```

### 4. Regression Testing
```bash
# Run standard test suite
./scripts/ai_regression_test.sh

# Compare with baseline
python backend/tools/ai_stats.py --compare baseline current
```

## Best Practices

### 1. Logging Strategy
- Use `summary` level for large-scale testing
- Use `decision` level for general development
- Use `detailed` level only for specific bug investigation
- Always include timestamps and game IDs

### 2. Performance Optimization
- Disable verbose output for bulk runs
- Use summary logging for statistics gathering
- Profile periodically to catch performance regressions
- Clean up old logs regularly

### 3. Bug Investigation
- Start with decision-level logs
- Use seed for reproducible cases
- Check bug detection reports first
- Compare with known good behavior

### 4. Development Workflow
1. Make AI changes
2. Run small test batch (5-10 games)
3. Check for bugs and anomalies
4. Run larger batch (100+ games)
5. Compare statistics with baseline
6. Profile if performance concerns

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   # Ensure you're in the project root
   cd /path/to/liap-tui
   # Run from project root
   python backend/ai_debug_simple.py
   ```

2. **Memory issues with large batches**
   ```bash
   # Use summary logging
   python backend/ai_debug_simple.py --games 1000 --log-level summary
   # Or process in batches
   for i in {1..10}; do
       python backend/ai_debug_simple.py --games 100
   done
   ```

3. **Log files getting too large**
   ```bash
   # Rotate logs
   mv logs/ai_debug logs/ai_debug.old
   mkdir logs/ai_debug
   ```

### Debug Tips

1. **AI Making Poor Decisions**
   - Check decision logs for reasoning
   - Verify game state is correct
   - Look for pattern in bad decisions
   - Use detailed logging for specific games

2. **Performance Issues**
   - Profile with `--profile` flag
   - Check for expensive operations in hot paths
   - Verify caching is working correctly
   - Monitor memory usage

3. **Inconsistent Results**
   - Use fixed seed for testing
   - Check for race conditions (shouldn't exist in debug mode)
   - Verify AI version consistency
   - Look for environmental factors

## Integration with Development

### CI/CD Pipeline
```yaml
# Example GitHub Actions integration
ai-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - name: Run AI regression tests
      run: |
        python backend/ai_debug_simple.py --games 100 --log-level summary
        python backend/tools/ai_stats.py --check-regression
```

### Pre-commit Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
echo "Running AI smoke tests..."
python backend/ai_debug_simple.py --games 5 --log-level decision
if [ $? -ne 0 ]; then
    echo "AI tests failed!"
    exit 1
fi
```

## Advanced Topics

### Custom AI Players
```python
# Create custom AI for testing
class TestAI(AIPlayer):
    def make_decision(self, game_state):
        # Custom logic here
        return decision

# Register in debug mode
debug_runner.register_ai("TestAI", TestAI())
```

### Event Injection
```python
# Test specific scenarios
debug_runner.inject_event({
    "type": "force_weak_hand",
    "player": "AI_1",
    "round": 2
})
```

### Parallel Execution
```python
# Run games in parallel (experimental)
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(run_game, seed) for seed in range(100)]
    results = [f.result() for f in futures]
```

## Related Documentation

- [AI Architecture](../07-ai-development/AI_ARCHITECTURE.md) - Overall AI system design
- [AI Testing Strategy](../testing/AI_TESTING_STRATEGY.md) - Comprehensive testing approach
- [Bug Tracking](../testing/AI_TEST_CASES.md) - Known issues and test cases
- [Performance Guide](../08-operations/PERFORMANCE_MONITORING.md) - System performance monitoring

## Version History

- **v2.0** (Current) - Structured logging, bug detection, performance profiling
- **v1.0** - Basic debug runner with console output
- **v0.5** - Initial prototype

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review existing bug reports
3. Run with detailed logging
4. Create minimal reproduction case
5. File issue with logs attached