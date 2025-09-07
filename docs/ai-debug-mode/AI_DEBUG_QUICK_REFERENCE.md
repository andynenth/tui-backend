# AI Debug Mode - Quick Reference

## 🚀 Most Common Commands

```bash
# Run 1 game with default settings
python backend/ai_debug_simple.py

# Run 10 games with detailed logs
python backend/ai_debug_simple.py --games 10 --log-level detailed

# Run 100 games quickly for stats
python backend/ai_debug_simple.py --games 100 --log-level summary

# Analyze all logs
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json

# Run performance benchmark
python backend/tools/benchmark_quiet.py --games 100
```

## 📊 Analysis Commands

```bash
# Basic analysis with statistics
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json

# Export to CSV
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json --export-stats stats.csv

# Extended metrics (scores, game lengths)
python backend/tools/analyze_metrics.py logs/ai_debug/*.json

# Find specific bugs
grep "zero_declaration_strong_hand" logs/ai_debug/*.json
```

## 🧪 Testing Commands

```bash
# Run all tests
python tests/ai_debug/run_all_tests.py

# Run edge case tests
python tests/ai_debug/edge_cases/test_all_zero_declarations.py

# Run regression tests
python tests/ai_debug/regression/test_zero_declaration_bug.py
```

## 🔍 Bug Detection

```bash
# Check for bugs in recent games
python backend/tools/analyze_ai_logs.py logs/ai_debug/*.json | grep -C3 "BUG"

# Count bug occurrences
grep -c "bug_detected" logs/ai_debug/*.json

# Find games with specific bugs
grep -l "over_aggressive_declaration" logs/ai_debug/*.json
```

## 📈 Before/After Comparison

```bash
# Before changes
python backend/ai_debug_simple.py --games 100 --output before.json
python backend/tools/analyze_ai_logs.py before.json > before.txt

# After changes
python backend/ai_debug_simple.py --games 100 --output after.json
python backend/tools/analyze_ai_logs.py after.json > after.txt

# Compare
diff before.txt after.txt
```

## 🎯 Log Levels

- **summary**: Game results only (fastest)
- **decision**: AI decisions + bug detection (default)
- **detailed**: Full game state (debugging)

## 📁 File Locations

- **Logs**: `logs/ai_debug/`
- **Tools**: `backend/tools/`
- **Tests**: `tests/ai_debug/`
- **Main Script**: `backend/ai_debug_simple.py`

## 💡 Pro Tips

1. Use `--log-level summary` for performance testing
2. Use `--log-level decision` for bug hunting
3. Run at least 50 games for statistical significance
4. Always baseline before making AI changes
5. Check bug reports after every AI modification

## 🐛 Known Bugs to Watch For

1. **zero_declaration_strong_hand** - Declares 0 with good cards
2. **over_aggressive_declaration** - Declares too high
3. **pile_room_ignored** - Doesn't track pile capacity
4. **opener_wasted** - Uses high cards inefficiently
5. **not_playing_to_win** - Doesn't maximize when winning

## 📊 Expected Performance

- **Speed**: ~7 games/second
- **Memory**: ~7KB per game
- **Log Size**: ~15KB per game (decision level)

## ⚠️ Common Issues

```bash
# If import error: run from project root
cd /path/to/liap-tui

# If log directory missing
mkdir -p logs/ai_debug

# If memory issues with many games
python backend/ai_debug_simple.py --games 50 --log-level summary
```
