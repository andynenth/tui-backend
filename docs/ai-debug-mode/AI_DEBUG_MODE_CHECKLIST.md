# AI Debug Mode Implementation Checklist

## Quick Start Tasks (Day 1)
- [ ] Create `backend/ai_debug_mode.py` with basic CLI structure
- [ ] Add `--games N` flag to run N games
- [ ] Add `--speed [fast|normal|slow]` flag for simulation speed
- [ ] Create simple all-bot room and auto-start game
- [ ] Output basic winner and scores to console

## Core Logging Tasks (Day 2-3)
- [ ] Create `backend/services/ai_logger.py` with JSON formatter
- [ ] Add `--log-level [summary|decision|detailed]` flag
- [ ] Log every declaration with:
  - [ ] Player hand
  - [ ] Previous declarations
  - [ ] Final declaration value
  - [ ] Calculation reasoning
- [ ] Log every turn play with:
  - [ ] Required piece count
  - [ ] Available plays
  - [ ] Selected play and why
  - [ ] Current pile counts vs targets
- [ ] Save logs to `logs/ai_debug/game_{timestamp}.json`

## Essential Metrics (Day 4-5)
- [ ] Track per-game statistics:
  - [ ] Winner and final scores
  - [ ] Rounds played
  - [ ] Declaration accuracy per player (declared vs actual)
  - [ ] Turn wins per player
- [ ] Create summary statistics across multiple games:
  - [ ] Win rate by starting position
  - [ ] Average declaration accuracy
  - [ ] Most common winning scores
  - [ ] Game length distribution

## Bug Detection Features (Week 2)
- [ ] Add `--detect-bugs` flag to enable extra validation
- [ ] Check for illegal moves:
  - [ ] Playing pieces not in hand
  - [ ] Wrong number of pieces
  - [ ] Invalid combinations
- [ ] Detect AI logic errors:
  - [ ] Declaring impossible values
  - [ ] Not following zero-streak rule
  - [ ] Making same decision in loops
- [ ] Flag suspicious patterns:
  - [ ] Always overcapturing
  - [ ] Never using strong pieces
  - [ ] Inconsistent strategies

## Analysis Tools (Week 2-3)
- [ ] Create `backend/tools/analyze_ai_logs.py` script
- [ ] Generate reports showing:
  - [ ] Decision patterns by game phase
  - [ ] Common mistakes
  - [ ] Performance trends
- [ ] Add `--export-stats stats.csv` option
- [ ] Create `--replay game_id` feature to review specific games

## Testing & Validation (Week 3)
- [ ] Create test scenarios in `tests/ai_debug/`
- [ ] Test edge cases:
  - [ ] All players declare 0
  - [ ] Weak hand redeals  
  - [ ] Perfect declaration rounds
  - [ ] Comeback victories
- [ ] Benchmark performance:
  - [ ] Games per second
  - [ ] Memory usage
  - [ ] Log file sizes

## Documentation & Examples
- [ ] Write usage examples in README
- [ ] Document log format for analysis
- [ ] Create example bug reports
- [ ] Add troubleshooting guide

## Optional Enhancements (Future)
- [ ] Web dashboard for real-time monitoring
- [ ] Compare different AI versions
- [ ] Machine learning dataset export
- [ ] Replay games with different AI settings
- [ ] Tournament mode with rankings

## Definition of Done
- [ ] Can run 1000 games unattended
- [ ] Catches known AI bugs automatically  
- [ ] Generates actionable improvement insights
- [ ] Performance allows rapid iteration
- [ ] Logs are parseable and analyzable