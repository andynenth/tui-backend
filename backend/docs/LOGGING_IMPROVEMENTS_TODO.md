# Logging Improvements TODO

## Current State
The current AI logger captures:
- Game start with initial hands (detailed mode only)
- Round start/end with scores
- Declaration decisions (decision mode)
- Turn play decisions (decision mode)
- Bug detections
- Game end with summary

## Missing Critical Data

### 1. Turn-by-Turn Details
**Priority: HIGH**
- [ ] All players' plays for each turn (not just the AI making the decision)
- [ ] Turn winner and pile count updates
- [ ] Exact pieces played by each player
- [ ] Turn timing information

### 2. Game Context
**Priority: HIGH**
- [ ] Required piece count for each turn
- [ ] Current winning play before each decision
- [ ] Updated pile counts after each turn
- [ ] Player order for each turn

### 3. Complete Hand Tracking
**Priority: HIGH**
- [ ] Hand state after each play
- [ ] Available plays with rankings
- [ ] Invalid play attempts and reasons
- [ ] Piece disposal strategies

### 4. Declaration Context
**Priority: MEDIUM**
- [ ] Forbidden values (sum of 8 rule)
- [ ] Previous players' declarations in order
- [ ] Zero streak history for each player
- [ ] Pile room calculations

### 5. Special Events
**Priority: MEDIUM**
- [ ] Weak hand checks and redeal requests
- [ ] Redeal voting results
- [ ] Rule violation attempts
- [ ] Strategic plays (bluffs, baits)

### 6. Performance Metrics
**Priority: LOW**
- [ ] AI thinking time per decision
- [ ] Memory usage
- [ ] Cache effectiveness
- [ ] Strategy switches

## Implementation Plan

### Phase 1: Core Turn Data (Immediate)
1. Add `log_turn_result()` method to capture all plays and winner
2. Include complete game state in turn_play events
3. Add hand_after to show remaining pieces

### Phase 2: Enhanced Context (Next Sprint)
1. Add declaration phase complete state
2. Track available plays with full evaluation
3. Include timing metrics

### Phase 3: Advanced Analytics (Future)
1. Strategy tracking and switches
2. Learning indicators
3. Performance profiling

## Example Enhanced Turn Event
```json
{
  "event": "turn_complete",
  "round_number": 1,
  "turn_number": 3,
  "turn_plays": [
    {"player": "Bot 1", "play": ["GENERAL_RED"], "type": "SINGLE", "value": 14},
    {"player": "Bot 2", "play": ["SOLDIER_RED", "SOLDIER_BLACK"], "type": "INVALID", "value": 2},
    {"player": "Bot 3", "play": ["ADVISOR_BLACK"], "type": "SINGLE", "value": 12},
    {"player": "Bot 4", "play": ["ELEPHANT_RED"], "type": "SINGLE", "value": 10}
  ],
  "winner": "Bot 1",
  "pile_updates": {
    "Bot 1": {"before": 0, "after": 1},
    "Bot 2": {"before": 1, "after": 1},
    "Bot 3": {"before": 0, "after": 0},
    "Bot 4": {"before": 1, "after": 1}
  }
}
```

## Benefits
- Complete game replay capability
- Better bug detection and debugging
- AI strategy analysis
- Training data for ML models
- Performance optimization insights