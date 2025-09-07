# Play History UI Mockup Concepts

## Overview
UI/UX concepts for displaying play history data in the Liap Tui frontend, inspired by successful implementations from other games.

## Concept 1: Timeline View (Chess.com Style)

```
┌─────────────────────────────────────────────────────────────┐
│ Game: POKER-INSPIRED-2024 | Players: Daniel vs 3 AI        │
├─────────────────────────────────────────────────────────────┤
│ [Round 1] [Round 2] [Round 3] [Summary]                    │
├─────────────────────────────────────────────────────────────┤
│ Round 1 - Daniel Started (Red General)                      │
│                                                             │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│ │ Turn 1      │  │ Turn 2      │  │ Turn 3      │  ...    │
│ │ 4 pieces    │  │ GENERAL_RED │  │ 3 pieces    │         │
│ │ Daniel wins │  │ Daniel wins │  │ Phil wins   │         │
│ └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│ Declarations: Daniel(1) Phil(3) Doyle(2) Vanessa(2)        │
│ Final Score: Daniel +14, Phil +6, Doyle +4, Vanessa +4     │
└─────────────────────────────────────────────────────────────┘
```

### Features:
- Horizontal timeline of turns
- Click each turn for detailed view
- Round tabs for navigation
- Summary statistics per round

## Concept 2: Analytical Dashboard (Poker Tracker Style)

```
┌─────────────────────────────────────────────────────────────┐
│ Player Analysis: Daniel (Human)                             │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌──────────────────┐                   │
│ │ Win Rate        │ │ Declaration Stats │                  │
│ │ ████████ 67%    │ │ Avg: 1.5 piles   │                  │
│ │ Piles Won: 8/12 │ │ Success: 83%     │                  │
│ └─────────────────┘ └──────────────────┘                   │
│                                                             │
│ ┌─────────────────────────────────────┐                    │
│ │ Hand Strength vs Declaration        │                    │
│ │ Strong  ████████████ → 1-2 piles    │                    │
│ │ Medium  ██████ → 2-3 piles          │                    │
│ │ Weak    ██ → 0-1 piles              │                    │
│ └─────────────────────────────────────┘                    │
│                                                             │
│ Recent Games:                                               │
│ • vs 3 AI - Won (+14 pts) - "General dominance"           │
│ • vs 3 AI - Lost (-2 pts) - "Over-declared"               │
└─────────────────────────────────────────────────────────────┘
```

### Features:
- Player-focused statistics
- Visual charts and graphs
- Pattern recognition
- Historical performance

## Concept 3: Interactive Replay (Lichess Style)

```
┌─────────────────────────────────────────────────────────────┐
│ ◄◄ ◄ ▐▐ ► ►►  Turn 3/8  [Auto-play ▼]                    │
├─────────────────────────────────────────────────────────────┤
│ ┌───────────────────┐ ┌───────────────────────────────┐   │
│ │ Current Board     │ │ Move List                     │   │
│ │                   │ │ 1. Daniel: SOLDIER_RED (1)    │   │
│ │ Pile: 12 pieces   │ │ 2. Phil: SOLDIER_RED (1)     │   │
│ │ Current: Phil     │ │ 3. Doyle: SOLDIER_RED (1)    │   │
│ │ Playing: ADVISOR  │ │ 4. Vanessa: SOLDIER_RED (1)  │   │
│ │                   │ │ → Daniel wins (first player) │   │
│ │ [Show Animation]  │ │ 5. Daniel: GENERAL_RED ★     │   │
│ └───────────────────┘ └───────────────────────────────┘   │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ AI Analysis: "Phil should have played ADVISOR_RED   │   │
│ │ here to establish pile control early..."             │   │
│ └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Features:
- Step-by-step replay controls
- Visual board state
- Move annotations
- AI commentary

## Concept 4: Compact Mobile View (Hearthstone Style)

```
┌─────────────────────────┐
│ Recent Match            │
│ Won vs 3 AI (+14)      │
├─────────────────────────┤
│ Key Moments:            │
│ • Turn 1: 4-way tie    │
│ • Turn 2: GENERAL play │
│ • Turn 8: Final win    │
├─────────────────────────┤
│ Your Stats:             │
│ Declared: 1 ✓           │
│ Captured: 8 (!)         │
│ Multiplier: 1x          │
├─────────────────────────┤
│ [View Full] [Share]     │
└─────────────────────────┘
```

### Features:
- Mobile-optimized
- Key highlights only
- Quick stats
- Social sharing

## Concept 5: Heatmap Analysis (Chess Analysis Style)

```
┌─────────────────────────────────────────────────────────────┐
│ Declaration Success Heatmap                                 │
├─────────────────────────────────────────────────────────────┤
│         Declare 0  Declare 1  Declare 2  Declare 3         │
│ Pos 1   ████████   ████████   ██████     ████             │
│ Pos 2   ██████     ████████   ████████   ██████           │
│ Pos 3   ████       ██████     ████████   ████████         │
│ Pos 4   ██         ████       ██████     ████████         │
│                                                             │
│ Legend: ████ 80-100% ████ 60-80% ████ 40-60% ████ <40%    │
└─────────────────────────────────────────────────────────────┘
```

### Features:
- Visual pattern recognition
- Success rate by position/declaration
- Strategic insights
- Data-driven decisions

## Implementation Priority

### Phase 1: Basic History View
1. Simple turn-by-turn list (Concept 3 move list)
2. Round navigation tabs
3. Final scores display

### Phase 2: Analytics
1. Player statistics (Concept 2)
2. Declaration patterns
3. Win/loss tracking

### Phase 3: Interactive Features
1. Replay functionality (Concept 3)
2. AI analysis display
3. Alternative move suggestions

### Phase 4: Advanced Visualizations
1. Heatmaps (Concept 5)
2. Graphs and charts
3. Comparative analysis

## Technical Considerations

### Performance
- Paginate large histories
- Lazy load round details
- Cache processed statistics

### Responsive Design
- Desktop: Full analytical view
- Tablet: Simplified dashboard
- Mobile: Compact highlights (Concept 4)

### Accessibility
- Keyboard navigation for replay
- Screen reader support for statistics
- High contrast mode for visualizations

## User Stories

1. **"As a player, I want to review my last game to understand why I lost"**
   - Solution: Turn-by-turn replay with highlights

2. **"As a competitive player, I want to analyze my declaration patterns"**
   - Solution: Statistical dashboard with trends

3. **"As a learner, I want to see what the AI would have done"**
   - Solution: AI analysis overlay on moves

4. **"As a mobile user, I want quick game summaries"**
   - Solution: Compact mobile view

5. **"As a data enthusiast, I want to export my game history"**
   - Solution: Download options in various formats
