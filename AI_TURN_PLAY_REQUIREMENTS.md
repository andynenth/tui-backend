# AI Turn Play Requirements Specification

## 1. Core Objective
The AI must play pieces strategically to capture exactly the number of piles it declared, while following all game rules.

## 2. Fundamental Constraints

### 2.1 Game Rules (MUST follow)
- Must play exactly the required number of pieces each turn
- Can only play valid combinations or forfeit (invalid play)
- Cannot play pieces not in hand
- Winner of X-piece turn captures X piles

### 2.2 Strategic Goals (SHOULD achieve)
- Capture exactly declared number of piles (primary goal)
- Avoid capturing more than declared (overcapture)
- Minimize score loss when unable to meet declaration

## 3. Required Strategic Capabilities

### 3.1 Game State Awareness
- Track own captured/declared status
- Track all opponents' captured/declared status
- Remember all revealed (face-up) pieces
- Calculate remaining pieces and urgency

### 3.2 Hand Evaluation
- Identify valid combinations (pairs, straights, etc.)
- Categorize pieces as:
  - **Openers**: High-value pieces (11+ points) for turn control
  - **Main combos**: Combinations planned for capturing piles
  - **Burden pieces**: Pieces to dispose of

### 3.3 Strategic Planning
- Create primary plan to reach declared target
- Identify backup plans if primary fails
- Assess urgency based on remaining turns
- Adapt plan when circumstances change

## 4. Turn Decision Logic

### 4.1 As Turn Starter (Leading)
The AI must decide between:
- **Play opener**: Use high piece to win and control next turn (only when strategically beneficial, not automatically)
- **Execute combo**: Play planned combination immediately
- **Dispose burden**: Play weak pieces that don't contribute to main plan, setting piece count that opponents must follow
- **Set up opportunity**: Play specific count to enable future combos

### 4.2 As Responder
The AI must decide between:
- **Win if beneficial**: Beat current play if it helps reach target
- **Strategic forfeit**: Deliberately lose to avoid overcapture
- **Dispose burden**: Use opportunity to discard unwanted pieces

### 4.3 Critical Situations
- **At declared target**: Must avoid winning any turns
- **One turn remaining**: Must attempt to capture exactly remaining needed piles (if need 3 and must play 3, try to win; if need 2 but must play 3, likely cannot achieve target)
- **Opponent at target**: Play low-value pieces to bait them into winning and overcapturing

## 5. Advanced Strategies

### 5.1 Opener Management
- Evaluate opener reliability based on revealed pieces
- Hold openers for critical moments vs. use early
- Consider field strength when playing openers

### 5.2 Burden Management
- Identify pieces that don't fit main plan
- Dispose burden without disrupting strategy
- Balance between early and late disposal

### 5.3 Opponent Awareness
- Predict opponent strategies from declarations
- Recognize when opponents are at/near targets
- Exploit opponent constraints

### 5.4 Plan Adaptation
- Recognize when original plan is failing
- Switch to backup plans smoothly
- Recalculate paths to target mid-game

## 6. Decision Examples

[To be added after AI structure is finalized]

## 7. Success Metrics

### 7.1 Primary Metrics
- **Target Achievement Rate**: ≥70% achieve exact declared piles
- **Overcapture Avoidance**: ≥95% avoid exceeding declaration when at target
- **Valid Play Rate**: 100% (never attempt invalid plays unintentionally)

### 7.2 Quality Metrics
- **Strategic Variety**: Not always play highest value
- **Adaptation Success**: Successfully change plans when needed
- **Decision Speed**: <100ms per decision

### 7.3 Behavioral Metrics
- **Opener Usage**: Use openers strategically, not wastefully
- **Burden Disposal**: Efficiently remove unwanted pieces
- **Opponent Disruption**: Successfully force opponent mistakes

## 8. Edge Cases to Handle

1. **No valid plays**: Must forfeit appropriately
2. **Multiple equally good options**: Have consistent tie-breaking
3. **Impossible targets**: Minimize score loss gracefully
4. **Complex multi-opponent scenarios**: Consider all opponents
5. **Last piece constraints**: Handle endgame correctly

## 9. Implementation Priorities

1. **Phase 1**: Core decision making (play vs forfeit)
2. **Phase 2**: Target achievement strategies
3. **Phase 3**: Overcapture avoidance
4. **Phase 4**: Opponent modeling
5. **Phase 5**: Advanced adaptation

## 10. Non-Functional Requirements

- **Performance**: Decisions in <100ms
- **Deterministic**: Same situation → same decision
- **Explainable**: Can output reasoning for decisions
- **Testable**: Clear inputs/outputs for testing
- **Maintainable**: Modular strategy components