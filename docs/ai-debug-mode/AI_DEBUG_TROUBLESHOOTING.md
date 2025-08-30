# AI Debug Mode Troubleshooting Guide

## Common Issues and Solutions

### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'backend'`

**Solution**:
```bash
# Make sure you're in the project root
cd /path/to/liap-tui

# Run from project root
python backend/ai_debug_simple.py

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 2. Missing Dependencies

**Problem**: `ImportError: cannot import name 'AILogger'`

**Solution**:
```bash
# Install all requirements
pip install -r requirements.txt

# Or use virtual environment
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Log Directory Not Found

**Problem**: `FileNotFoundError: logs/ai_debug/`

**Solution**:
```bash
# Create log directory
mkdir -p logs/ai_debug

# Or let the script create it
python backend/ai_debug_simple.py --games 1
```

### 4. Memory Issues with Large Games

**Problem**: Memory usage grows too high with many games

**Solution**:
```bash
# Run in smaller batches
python backend/ai_debug_simple.py --games 100 --output batch1.json
python backend/ai_debug_simple.py --games 100 --output batch2.json

# Use summary level logging
python backend/ai_debug_simple.py --games 1000 --log-level summary

# Analyze in chunks
python backend/tools/analyze_ai_logs.py logs/ai_debug/game_[1-5]*.json
```

### 5. Slow Performance

**Problem**: Games running slower than expected

**Solution**:
```bash
# Use quiet benchmark mode
python backend/tools/benchmark_quiet.py --games 100

# Disable verbose output
python backend/ai_debug_simple.py --games 100 --log-level summary

# Check for performance bottlenecks
python -m cProfile backend/ai_debug_simple.py --games 10
```

### 6. Inconsistent Results

**Problem**: AI behavior changes between runs

**Solution**:
```bash
# Set random seed for reproducibility
PYTHONHASHSEED=0 python backend/ai_debug_simple.py --games 10

# Run multiple batches for statistical significance
for i in {1..5}; do
    python backend/ai_debug_simple.py --games 100 --output batch_$i.json
done

# Analyze all batches together
python backend/tools/analyze_ai_logs.py batch_*.json
```

### 7. Test Failures

**Problem**: Tests failing with unexpected AI behavior

**Solution**:
```bash
# Run specific test with verbose output
python tests/ai_debug/edge_cases/test_zero_declaration.py -v

# Check if AI logic has changed
git diff backend/engine/ai.py

# Run regression tests
python tests/ai_debug/regression/test_zero_declaration_bug.py
```

### 8. JSON Parsing Errors

**Problem**: `json.decoder.JSONDecodeError` when analyzing logs

**Solution**:
```bash
# Check log file format
head -n 20 logs/ai_debug/game_1.json

# Validate JSON
python -m json.tool logs/ai_debug/game_1.json > /dev/null

# Clean up corrupted logs
find logs/ai_debug -name "*.json" -exec python -m json.tool {} \; 2>&1 | grep -B1 "Error"
```

## Performance Optimization Tips

### 1. Reduce Logging Overhead

```python
# Use summary level for large batches
ai_logger = AILogger('summary', None)  # No file output

# Disable AI reasoning output
verbose = False
```

### 2. Batch Processing

```bash
# Process games in parallel
parallel -j 4 python backend/ai_debug_simple.py --games 25 --output batch_{}.json ::: 1 2 3 4

# Combine results
python backend/tools/analyze_ai_logs.py batch_*.json
```

### 3. Memory Management

```python
# Clear game state between runs
import gc
gc.collect()

# Use generators for large log analysis
def process_logs_streaming(files):
    for file in files:
        with open(file) as f:
            yield json.load(f)
```

## Debugging AI Issues

### 1. Enable Detailed Logging

```bash
# Maximum verbosity
python backend/ai_debug_simple.py --games 1 --log-level detailed --verbose
```

### 2. Trace Specific Decisions

```python
# Add breakpoints in ai.py
import pdb; pdb.set_trace()

# Or use print debugging
print(f"DEBUG: hand={hand}, declaration={score}")
```

### 3. Compare Before/After

```bash
# Save baseline
git stash
python backend/ai_debug_simple.py --games 100 --output baseline.json

# Apply changes
git stash pop
python backend/ai_debug_simple.py --games 100 --output changed.json

# Compare
python backend/tools/analyze_ai_logs.py baseline.json > baseline.txt
python backend/tools/analyze_ai_logs.py changed.json > changed.txt
diff baseline.txt changed.txt
```

## Known Limitations

1. **No Network Play**: AI Debug Mode runs locally only
2. **No UI Visualization**: Terminal output only
3. **Simplified Game State**: Some WebSocket features not available
4. **Single-threaded**: Games run sequentially

## Getting Help

1. Check existing logs for error patterns
2. Run with `--verbose` flag for more details
3. Review test cases for expected behavior
4. Check [AI_IMPROVEMENT_INSIGHTS.md](AI_IMPROVEMENT_INSIGHTS.md) for known issues

## Reporting Issues

When reporting AI Debug Mode issues, include:

1. **Command used**: Full command with all flags
2. **Error message**: Complete error output
3. **Environment**: Python version, OS, virtual env
4. **Log samples**: Relevant portions of game logs
5. **Expected vs Actual**: What should happen vs what happened

Example issue report:
```
Command: python backend/ai_debug_simple.py --games 10 --log-level detailed
Error: KeyError: 'SOLDIER_BLUE'
Environment: Python 3.11, macOS, venv activated
Expected: Game runs successfully
Actual: Crashes on first declaration
```