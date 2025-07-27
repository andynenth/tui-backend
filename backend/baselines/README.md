# Migration Performance Baselines

This directory contains performance baseline data captured during Phase 6.1.4: Migration Monitoring Activation.

## Baseline Files

- `quick_baseline_test.json` - Quick test baseline (10 minutes)
- `migration_baseline_YYYYMMDD_HHMMSS.json` - Full baseline captures (24-48 hours)

## Baseline Metrics

### System Metrics
- Memory usage (RSS/VMS)
- CPU utilization
- Memory growth rate
- Garbage collection statistics
- Thread count

### Game Metrics
- Active games
- Games per hour
- Average game duration
- Player win rates
- WebSocket connections

### Alert Thresholds
Based on baseline data analysis:
- Memory usage alert: 120% of baseline max
- CPU usage alert: 150% of baseline max
- Response time alert: 50ms (fixed requirement)
- Error rate alert: 0.5% (fixed requirement)

## Usage

```bash
# Capture quick test baseline
python capture_performance_baseline.py --quick

# Capture 24-hour baseline
python capture_performance_baseline.py --duration=24h

# Capture 48-hour baseline (recommended)
python capture_performance_baseline.py --duration=48h --interval=5
```