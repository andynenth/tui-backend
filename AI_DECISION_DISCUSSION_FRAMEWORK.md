# AI Decision Logic Discussion Framework

## Purpose
Before implementing AI enhancements, we need to thoroughly discuss and validate the decision logic to ensure it aligns with good gameplay and is technically feasible.

## Discussion Structure

### 1. Current State Analysis
**Questions to Answer:**
- What decisions does the AI currently make well?
- Where does it fail or make suboptimal choices?
- What patterns do we see in bot vs human games?

**Discussion Format:**
- Review game logs/replays
- Identify specific scenarios where AI struggles
- Document current decision trees

### 2. Game Theory Analysis
**Questions to Answer:**
- What constitutes "optimal" play in Liap Tui?
- How do skilled human players approach decisions?
- What are the key decision points that determine game outcome?

**Topics to Explore:**
- **Risk vs Reward**: When to declare high vs low
- **Information Theory**: What can be inferred from opponent actions
- **Nash Equilibrium**: Are there dominant strategies?
- **Meta-game**: How does score position affect strategy?

### 3. Decision Logic Proposals

#### A. Declaration Logic Discussion
**Current Logic:**
```
Score = strong_combos + has_opening + is_first
Declare = clamp(score, 1, 7)
```

**Key Problems Identified (from AI_DECLARATION_ANALYSIS.md):**
1. Static Evaluation - same hand always gives same declaration
2. No Memory - doesn't learn from previous misses
3. Score Blindness - declares same when winning or losing
4. No Risk Assessment - doesn't adjust for game situation

**Specific Scenarios Where Current AI Fails:**
1. **Near Victory**: Bot with 47 points declares 4 (too risky)
2. **Far Behind**: Bot losing badly declares 2 (too conservative)
3. **After Missing**: Declared 4, got 1, declares 4 again next round
4. **With Multiplier**: Doesn't adjust for 2x/3x scoring rounds

**Proposed Simple Improvements:**
1. **Game State Awareness** (Simplest to implement)
   - If need <5 points to win: max declaration = 2
   - If behind by >20 points: add +1 to declaration
   - Keep current logic otherwise

2. **Basic Memory** (Medium complexity)
   - Track last round: if missed by 2+, reduce next declaration by 1
   - No complex history, just simple adjustment

3. **Slight Randomness** (Easy to implement)
   - 20% chance to declare ±1 from calculated value
   - Adds variety without complexity

#### B. Play Selection Logic Discussion
**Current Logic:**
```
Always play highest point combination
```

**Questions:**
1. When should AI save strong combinations?
2. How to decide between winning now vs setting up future wins?
3. Should AI ever "throw away" weak pieces strategically?

**Scenarios to Discuss:**
- Have 3 strong plays, need exactly 2 wins
- Opponent needs 1 pile, should force multi-piece plays
- Last turn of round, does order matter?

#### C. Redeal Logic Discussion
**Current Logic:**
```
Accept if max_piece <= 9 (with probability)
```

**Questions:**
1. Should consider combination potential?
2. How does game state affect redeal decision?
3. Is current threshold (9 points) optimal?

**Factors to Consider:**
- Hand shape (many pairs vs potential straights)
- Score position (risk tolerance)
- Round number (urgency)
- Multiplier impact

### 4. Implementation Feasibility

**Technical Constraints:**
- Performance (decision time <100ms)
- Memory usage (tracking opponent history)
- Code complexity (maintainability)

**Architecture Questions:**
- Should we use strategy pattern?
- How to make AI configurable?
- Where to store game history?

### 5. Testing Strategy

**How to Validate Improvements:**
- A/B testing (old AI vs new AI)
- Win rate analysis
- Decision quality metrics
- Human player feedback

**Test Scenarios:**
- Edge cases (last player declaration, etc.)
- Different game states (ahead/behind)
- Various hand strengths

## Discussion Format Options

### Option 1: Scenario-Based Discussion
Walk through specific game scenarios and discuss optimal decisions:
```
Scenario: Bot has 45 points (5 from winning), opponents have 30-35
Hand: [Strong straight + weak pieces]
Question: Declare conservatively (2) or normal (3)?
```

### Option 2: Component-Based Discussion
Discuss each decision component separately:
1. Declaration strategy session
2. Play selection session  
3. Redeal logic session

### Option 3: Mathematical Modeling
Create formal models for decisions:
- Expected value calculations
- Probability trees
- Minimax analysis

## Declaration-Specific Discussion Points

### What We Need to Decide:

1. **Minimal Game State Awareness - Yes or No?**
   - Pro: Fixes obvious bad decisions (declaring 4 when 2 points from winning)
   - Con: Adds complexity, makes AI less predictable for new players
   - **Recommendation**: Yes - just for extreme cases (near win/far behind)

2. **Simple Memory - Yes or No?**
   - Pro: More realistic, learns from mistakes
   - Con: More complex, harder to debug
   - **Recommendation**: Maybe - start without it, add if needed

3. **Random Variation - Yes or No?**
   - Pro: Less predictable, more fun
   - Con: Can make bad decisions randomly
   - **Recommendation**: Yes - small amount (±1 with 10-20% chance)

### Proposed Minimal Implementation:

```python
def improved_declaration(base_score, game_state):
    # 1. Calculate base score (current logic)
    score = base_score
    
    # 2. Simple game state adjustment
    if game_state.bot_score >= 48:  # Near victory
        score = min(score, 2)
    elif game_state.bot_score < 25 and game_state.leader_score > 40:  # Far behind
        score += 1
    
    # 3. Small random variation
    if random.random() < 0.15:  # 15% chance
        score += random.choice([-1, 1])
    
    # 4. Clamp and return
    return max(1, min(score, 7))
```

## Key Principles to Establish

1. **Keep It Simple**: Minimal changes that fix obvious issues
2. **Maintain Predictability**: New players should understand bot behavior
3. **Fun Over Optimal**: Better to be beatable than frustrating
4. **Easy to Maintain**: Avoid complex state tracking

## Output from Discussion

The discussion should produce:

1. **Decision Trees**: Clear logic for each decision type
2. **Priority List**: Which improvements to implement first
3. **Success Metrics**: How to measure improvement
4. **Implementation Plan**: Technical approach and timeline

## Declaration Discussion Outcomes

### Decisions Made:
1. ✅ **Add minimal game state awareness** - Only for extreme cases
2. ❓ **Skip memory for now** - Can add later if needed
3. ✅ **Add small random variation** - 15% chance of ±1

### Priority Order for Implementation:
1. **First**: Add game state awareness (biggest impact, easiest to test)
2. **Second**: Add random variation (simple, improves fun)
3. **Later**: Consider memory system if needed

### Success Metrics:
- **Fewer obvious mistakes**: No more declaring 4 when 2 points from winning
- **Better catch-up behavior**: Aggressive declarations when far behind
- **Slightly less predictable**: Random variation makes games more interesting
- **Still understandable**: New players can see why bot declared what it did

### Next Actions:
1. **Document current behavior** - Create test cases for specific scenarios
2. **Define exact thresholds** - When is "near victory"? When is "far behind"?
3. **Create prototype** - Implement minimal changes in a test branch
4. **Test specific scenarios** - Verify fixes for identified problems
5. **Measure impact** - Compare declaration accuracy before/after

### What We're NOT Doing (Yet):
- Complex opponent modeling
- Multi-round memory
- Sophisticated risk calculations
- Different bot personalities
- Machine learning or adaptive behavior

## Example Discussion Agenda

**Session 1: Current State Review (1 hour)**
- Demo current AI behavior
- Review player feedback
- Identify top 3 issues

**Session 2: Declaration Logic (1 hour)**
- Analyze declaration patterns
- Propose improvements
- Create decision tree

**Session 3: Play Selection Logic (1 hour)**
- Examine play patterns
- Discuss strategic concepts
- Design new algorithm

**Session 4: Technical Planning (1 hour)**
- Architecture decisions
- Performance considerations
- Testing approach

## Questions to Start Discussion

1. **What makes Liap Tui fun?** Should AI optimize for winning or create interesting games?

2. **How sophisticated should AI be?** Simple and predictable vs complex and surprising?

3. **What's the target player?** Casual players vs competitive players?

4. **How transparent should AI be?** Should players understand AI decisions?

5. **What's the development timeline?** Quick improvements vs long-term vision?

## Next Steps

1. Schedule discussion sessions
2. Gather gameplay data
3. Create test scenarios
4. Document decisions
5. Create implementation tickets