# AI Debug Mode User Guide

## Overview

AI Debug Mode is a powerful tool for testing and analyzing AI behavior in Liap Tui without the overhead of WebSocket infrastructure. It runs games synchronously with all AI players, providing detailed logging and analysis capabilities.

## Quick Start

```bash
# Run a single AI game with default settings
python backend/ai_debug_simple.py

# Run 10 games with detailed logging
python backend/ai_debug_simple.py --games 10 --log-level detailed

# Run 100 games quickly for statistical analysis
python backend/ai_debug_simple.py --games 100 --log-level summary
```

## Command Line Options

### Basic Options

- `--games N` - Number of games to simulate (default: 1)
- `--log-level [summary|decision|detailed]` - Logging verbosity (default: decision)
- `--verbose` - Show detailed AI reasoning in console output
- `--output FILE` - Custom output file (default: logs/ai_debug/game_{timestamp}.json)

### Examples

```bash
# Run 50 games with decision-level logging
python backend/ai_debug_simple.py --games 50 --log-level decision

# Run games with verbose console output for debugging
python backend/ai_debug_simple.py --games 5 --verbose

# Save logs to a specific file
python backend/ai_debug_simple.py --games 10 --output logs/ai_debug/test_run.json
```

## Log Levels Explained

### Summary Level
- Minimal logging for performance testing
- Records only game start/end and round summaries
- Best for: Running many games quickly, statistical analysis

### Decision Level (Default)
- Records all AI decisions with reasoning
- Includes declaration logic and turn play choices
- Automatically detects and logs AI bugs
- Best for: Understanding AI behavior, bug detection

### Detailed Level
- Complete game state at every decision point
- Full hand contents and available plays
- Comprehensive debugging information
- Best for: Deep debugging, understanding specific issues

## Analyzing Results

### Basic Analysis

```bash
# Analyze all games in the log directory
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json

# Analyze specific games
python backend/tools/analyze_ai_logs.py logs/ai_debug/game_1.json logs/ai_debug/game_2.json

# Export statistics to CSV
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json --export-stats stats.csv
```

### Advanced Analysis

```bash
# Get extended metrics (winning scores, game lengths)
python backend/tools/analyze_metrics.py logs/ai_debug/*.json

# Search for specific bugs
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json | grep "zero_declaration"

# Compare before/after AI changes
python backend/tools/analyze_ai_logs.py before/*.json > before.txt
python backend/tools/analyze_ai_logs.py after/*.json > after.txt
diff before.txt after.txt
```

## Performance Benchmarking

### Quick Benchmark

```bash
# Run performance benchmark with different log levels
python backend/tools/benchmark_quiet.py --mode levels

# Benchmark a specific number of games
python backend/tools/benchmark_quiet.py --games 100
```

### Performance Metrics
- **Throughput**: ~7 games/second (may vary by hardware)
- **Memory Usage**: ~7KB per game
- **Log Size**: ~15KB per game with decision-level logging

## Bug Detection

AI Debug Mode automatically detects common AI bugs:

### Detected Bug Types

1. **Zero Declaration with Strong Hand**
   - AI declares 0 despite having 2+ openers
   - Severity: HIGH
   - Impact: AI plays too conservatively

2. **Over-Aggressive Declaration**
   - AI declares 6+ with weak hand
   - Severity: MEDIUM
   - Impact: AI often fails to meet declaration

3. **Ignoring Pile Room**
   - AI doesn't consider remaining pile capacity
   - Severity: MEDIUM
   - Impact: Suboptimal late-game decisions

4. **Wasting Openers**
   - AI uses high-value pieces inefficiently
   - Severity: LOW
   - Impact: Missed winning opportunities

5. **Not Playing to Win**
   - AI doesn't maximize when close to winning score
   - Severity: HIGH
   - Impact: Games last longer than necessary

### Finding Bugs

```bash
# Run games and check for bugs
python backend/ai_debug_simple.py --games 50 --log-level decision

# Analyze bug frequency
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json

# Look for specific bug patterns
grep -r "zero_declaration_strong_hand" logs/ai_debug/
```

## Testing AI Changes

### Before Making Changes

```bash
# Create baseline
mkdir baseline
python backend/ai_debug_simple.py --games 100 --output baseline/games.json
python backend/tools/analyze_ai_logs.py baseline/games.json > baseline/analysis.txt
```

### After Making Changes

```bash
# Test changes
mkdir after_changes
python backend/ai_debug_simple.py --games 100 --output after_changes/games.json
python backend/tools/analyze_ai_logs.py after_changes/games.json > after_changes/analysis.txt

# Compare results
diff baseline/analysis.txt after_changes/analysis.txt
```

## Common Use Cases

### 1. Quick AI Behavior Check

```bash
# See what AI is doing in a few games
python backend/ai_debug_simple.py --games 3 --verbose
```

### 2. Statistical Analysis

```bash
# Run many games for statistics
python backend/ai_debug_simple.py --games 500 --log-level summary
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json --export-stats ai_performance.csv
```

### 3. Bug Investigation

```bash
# Detailed logging to catch bugs
python backend/ai_debug_simple.py --games 20 --log-level detailed
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json | grep -A5 -B5 "BUG"
```

### 4. Performance Testing

```bash
# Benchmark current performance
python backend/tools/benchmark_quiet.py --games 1000
```

### 5. Regression Testing

```bash
# Run edge case tests
python tests/ai_debug/run_all_tests.py

# Run specific regression test
python tests/ai_debug/regression/test_zero_declaration_bug.py
```

## Tips and Best Practices

### For Best Performance
- Use `--log-level summary` when running many games
- Disable verbose output with large game counts
- Process logs in batches if analyzing thousands of games

### For Bug Detection
- Use `--log-level decision` (default) for optimal bug detection
- Run at least 50-100 games to find intermittent bugs
- Check the bug summary in analysis output

### For AI Development
- Always create a baseline before making changes
- Test edge cases with specific hand configurations
- Use regression tests to ensure bugs don't return
- Document significant findings in AI_IMPROVEMENT_INSIGHTS.md

## Log File Format

Logs are stored as JSON in `logs/ai_debug/` with this structure:

```json
{
  "game_id": "AI_123456",
  "timestamp": "2025-08-29T12:34:56.789Z",
  "log_level": "decision",
  "events": [
    {
      "event": "game_start",
      "players": ["Bot 1", "Bot 2", "Bot 3", "Bot 4"],
      ...
    },
    {
      "event": "declaration",
      "player": "Bot 1",
      "decision": {
        "declared_value": 3,
        "reasoning": "Starter with 2 openers and 1 combos"
      },
      ...
    }
  ]
}
```

See [LOG_FORMAT.md](LOG_FORMAT.md) for complete format documentation.

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Run from project root
   cd /path/to/liap-tui
   python backend/ai_debug_simple.py
   ```

2. **Log Directory Not Found**
   ```bash
   # Create log directory
   mkdir -p logs/ai_debug
   ```

3. **Memory Issues with Many Games**
   ```bash
   # Run in smaller batches
   python backend/ai_debug_simple.py --games 100 --output batch1.json
   python backend/ai_debug_simple.py --games 100 --output batch2.json
   ```

See [AI_DEBUG_TROUBLESHOOTING.md](AI_DEBUG_TROUBLESHOOTING.md) for more solutions.

## Next Steps

- Read [AI_IMPROVEMENT_INSIGHTS.md](AI_IMPROVEMENT_INSIGHTS.md) for AI strategy analysis
- Check [AI_DEBUG_MODE_PLAN.md](AI_DEBUG_MODE_PLAN.md) for implementation details
- Review test cases in `tests/ai_debug/` for examples
- Explore analysis tools in `backend/tools/` for custom analysis