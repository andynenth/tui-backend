# Dashboard Data Specification - Bot Decision Analysis

## Overview

This document defines **exactly what data** the Decision Analysis Dashboard will capture, analyze, and display based on the existing AI system in `backend/engine/ai.py`.

## 📊 **Core Data Sources**

### **Primary Data Source: AI Verbose Output**
The AI system already generates comprehensive decision data through verbose logging:

```python
# From ai.py lines 354-363 - STRATEGIC DECLARATION ANALYSIS
🎯 STRATEGIC DECLARATION ANALYSIS
Position: 2 (Starter: False)  
Previous declarations: [1, 0]
Pile room: 7
Field strength: weak
Has GENERAL_RED: False
Combo opportunity: True
Found 5 combos, 3 viable
Opener score: 1.0
Final declaration: 4
```

### **Secondary Data Sources**
- **Bot Play Decisions**: From `choose_best_play()` function
- **Game State Context**: Round number, phase, player position
- **Performance Metrics**: Decision timing, success rates
- **Game Outcomes**: Actual vs declared piles won

---

## 🎯 **Dashboard Display Sections**

### **Section 1: Real-Time Decision Feed**

**What it shows**: Live stream of bot decision-making process

**Data Points Displayed**:
- **Bot Name**: Which bot made the decision
- **Decision Type**: "Declaration", "Play", "Redeal Response"
- **Position**: Player position (0-3) and starter status
- **Previous Context**: Other players' declarations/actions
- **Timing**: Decision response time in milliseconds

**Visual Format**: 
```
🤖 Bot_Player_2 | DECLARATION | Position 2 (Non-starter) | 143ms
   Previous declarations: [1, 0]
   Decision: Declared 4 piles
   Reasoning: Strong combos available, weak field
```

---

### **Section 2: Strategic Decision Breakdown**

**What it shows**: Detailed analysis of the AI's 9-phase decision process

#### **Phase 1: Context Building**
- **Position in Order**: 0-3 (visual indicator)
- **Previous Declarations**: `[1, 0, 3]` with player names
- **Pile Room**: Available piles (0-8) with visual gauge
- **Field Strength**: "weak/normal/strong" with color coding
- **GENERAL_RED Status**: Has/doesn't have (special indicator)

#### **Phase 2-3: Combo Discovery**
- **Total Combos Found**: Count with breakdown by type
- **Strong Combos**: THREE_OF_A_KIND, STRAIGHT, FOUR_OF_A_KIND, etc.
- **Combo Filtering**: Which combos were filtered out and why
- **Combo Viability**: Viable vs total combos ratio

#### **Phase 4: Opener Analysis**
- **Opener Score**: Numerical score (0.0-4.0+)
- **Reliable Openers**: GENERAL (13-14), ADVISOR (11-12) pieces
- **Opener Count**: Number of strong opener pieces
- **Field Strength Impact**: How field affects opener reliability

#### **Phase 5-8: Declaration Logic**
- **Base Score**: Initial declaration calculation
- **Constraints Applied**: Forbidden declarations, must-declare-nonzero
- **Final Adjustment**: How constraints modified the declaration
- **Alternative Selection**: If original choice was forbidden

---

### **Section 3: Performance Analytics**

#### **Decision Timing Chart**
**Data Source**: Response time measurements
**Display**: Line chart showing bot response times over time
**Target Line**: 100ms threshold for optimal performance
**Alerts**: When response time > 200ms

#### **Declaration Accuracy Tracking**
**Data Source**: Declared vs actual piles won
**Display**: 
- **Success Rate**: % of accurate declarations
- **Over-Declaration**: When bot declared more than achieved
- **Under-Declaration**: When bot declared less than achieved
- **Trend Analysis**: Accuracy improvement over time

#### **Win Rate Correlation**
**Data Source**: Game outcomes vs decision patterns
**Display**:
- **Win Rate by Field Strength**: Performance in weak/normal/strong fields
- **Win Rate by Position**: Performance as starter vs non-starter
- **Declaration Value Success**: Which declaration values (0-8) perform best

---

### **Section 4: Strategic Pattern Analysis**

#### **Combo Utilization Heatmap**
**Data Source**: Combo types found vs used in declarations
**Display**: 
- **Heat Map**: Frequency of each combo type discovery
- **Utilization Rate**: How often discovered combos influence declarations
- **Success Rate**: Win rate when using each combo type

#### **Opponent Pattern Recognition**
**Data Source**: `analyze_opponent_patterns()` results
**Display**:
- **Low Declarer Detection**: When opponents have weak hands
- **High Declarer Detection**: When opponents have strong hands  
- **Singles-Only Rounds**: Rounds where only single pieces played
- **Response Strategy**: How bot adapts to opponent patterns

#### **GENERAL_RED Impact Analysis**
**Data Source**: Decisions when `has_general_red: True`
**Display**:
- **Declaration Behavior**: How GENERAL_RED affects declarations
- **Combo Strategy**: Preference for strongest combo only
- **Success Rate**: Win rate with vs without GENERAL_RED
- **Strategic Value**: Point advantage gained from GENERAL_RED

---

### **Section 5: Game Context Visualization**

#### **Round Progression Analysis**
**Display**:
- **Early Round Strategy**: Rounds 1-5 behavior patterns
- **Mid Game Adaptation**: Rounds 6-15 strategy evolution  
- **End Game Urgency**: Rounds 16-20 risk-taking patterns
- **Score Pressure Response**: Behavior when behind/ahead

#### **Position Strategy Matrix**
**Display**: 4x4 grid showing performance by position and starter status
- **Position 0 (Starter)**: First player advantages/challenges
- **Position 1-2 (Middle)**: Information advantage utilization
- **Position 3 (Last)**: Constraint handling and final decisions
- **Success Rates**: Win percentage by position

---

## 📈 **Advanced Analytics**

### **Machine Learning Insights** (Future Enhancement)
- **Pattern Recognition**: Identify subtle winning patterns
- **Opponent Modeling**: Learn opponent behavior patterns
- **Strategy Optimization**: Suggest improvements to AI logic
- **Anomaly Detection**: Identify unusual decision patterns

### **Comparative Analysis**
- **Bot vs Bot**: Performance comparison between different bot instances
- **Bot vs Human**: How bot decisions compare to human players
- **Strategy Evolution**: How bot performance changes over games
- **Meta-Game Analysis**: Adaptation to changing game environments

---

## 🔧 **Technical Data Structure**

### **BotDecisionData Class** (To be implemented)
```python
@dataclass
class BotDecisionData:
    # Basic Info
    bot_name: str
    decision_type: str  # 'declare', 'play', 'redeal'
    timestamp: float
    room_id: str
    
    # Game Context
    round_number: int
    position_in_order: int
    is_starter: bool
    
    # Decision Context (from verbose output)
    context: Dict[str, Any] = field(default_factory=dict)
    # Contains: previous_declarations, pile_room, field_strength, 
    #          has_general_red, combo_opportunity, combo_counts,
    #          opener_score, final_decision
    
    # Performance Metrics
    response_time_ms: float
    memory_usage_mb: float
    
    # Outcome Tracking (filled after round completion)
    actual_result: Optional[int] = None
    success: Optional[bool] = None
    points_gained: Optional[int] = None
```

### **Data Capture Points**

#### **Declaration Phase**
- **Location**: `bot_manager.py` lines 425-440 in `_bot_declare()`
- **Trigger**: After `ai.choose_declare()` completes
- **Data**: All verbose output from strategic analysis

#### **Play Phase**  
- **Location**: `bot_manager.py` in `_bot_play()` method
- **Trigger**: After `ai.choose_best_play()` completes
- **Data**: Play type, pieces selected, points gained

#### **Round Completion**
- **Location**: State machine scoring phase
- **Trigger**: After piles are awarded and scores calculated
- **Data**: Actual piles won, declaration accuracy, points gained

---

## 🎨 **UI/UX Specifications**

### **Dashboard Layout**
- **Header**: Room info, bot count, live/paused status
- **Main Panel**: 5 tabbed sections (Real-time, Breakdown, Performance, Patterns, Context)
- **Side Panel**: Quick stats, alerts, connection status
- **Footer**: Data export, settings, help

### **Real-Time Updates**
- **WebSocket Events**: `bot_decision`, `round_complete`, `game_over`
- **Update Frequency**: Immediate for decisions, 1s intervals for metrics
- **Data Retention**: Last 100 decisions in memory, full history in event store

### **Interactive Features**
- **Decision Replay**: Click any decision to see full analysis
- **Filter Controls**: By bot, decision type, time range, success/failure
- **Export Options**: CSV, JSON, PDF report generation
- **Comparison Mode**: Side-by-side analysis of multiple bots

---

## 📋 **Implementation Priority**

### **Phase 1: Core Data Capture** (Week 1)
1. **BotDecisionData structure** - Capture verbose AI output
2. **Event store integration** - Store decision data
3. **Basic API endpoints** - Serve historical data

### **Phase 2: Real-Time Display** (Week 2-3)  
1. **Live decision feed** - Real-time decision streaming
2. **Strategic breakdown** - 9-phase analysis visualization
3. **WebSocket integration** - Live dashboard updates

### **Phase 3: Analytics** (Week 4)
1. **Performance charts** - Timing, accuracy, win rates
2. **Pattern analysis** - Combo usage, strategic patterns
3. **Chart library integration** - Interactive visualizations

### **Phase 4: Polish** (Week 5)
1. **Settings integration** - Dashboard toggle in game settings
2. **Error handling** - Graceful failure management  
3. **Export features** - Data export and reporting

---

## 🔍 **Sample Dashboard Screenshots** (Conceptual)

### **Real-Time Feed**
```
🤖 BotAlice | DECLARATION | Pos 1 | 89ms | ✅ Success
   Context: Previous [2], Pile room: 6, Field: normal
   Found: 3 combos (2 viable), Opener score: 2.0
   Decision: Declared 3 piles → Actually won 3 ✅

🤖 BotBob | PLAY | Pos 2 | 134ms | Turn 3/8  
   Required: 2 pieces, Hand strength: Strong
   Played: STRAIGHT (ADVISOR_RED, GENERAL_BLACK) - 25pts
   Result: Won turn, gained 6 pieces
```

### **Strategic Breakdown Panel**
```
📊 Current Analysis: BotAlice Declaration (Round 5, Position 1)

🎯 Context Building
   Position: 1 of 4 (Non-starter) ●○○○
   Previous: [2] by BotCarol
   Pile Room: ████████░ (6/8 available)
   Field Strength: NORMAL 🟡
   GENERAL_RED: ❌ Not in hand

🃏 Combo Discovery  
   Total Found: 3 combos
   Strong Types: 1× THREE_OF_A_KIND, 1× STRAIGHT
   Filtered Out: None
   Viable: 2/3 combos (67%)

👑 Opener Analysis
   Opener Score: 2.0/4.0 ⭐⭐☆☆
   Reliable: ADVISOR_RED (11pts)
   Field Impact: +0.0 (normal field)
   
💯 Final Decision
   Base Score: 3
   Constraints: None applied
   Final: 3 piles declared
   Outcome: ✅ Won exactly 3 piles (+6 points)
```

This specification provides the **exact blueprint** for what the dashboard will analyze and display, making the implementation plan much more concrete and actionable.