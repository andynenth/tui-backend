# Play History Implementation Plan

## Overview
This document outlines the implementation plan for adding a Play History feature to the Liap Tui game. The feature will allow players to view detailed game history, analyze past rounds, and review player performance.

## Current Architecture Analysis

### Frontend Structure
- **Framework**: React 19.1.0 with TypeScript
- **Routing**: React Router v6
- **State Management**: React Contexts and custom hooks
- **API Communication**: WebSocket for game operations (no REST calls currently)
- **Component Organization**: Pages, Components, Services pattern

### Backend API
- **Endpoint**: `/api/rooms/{room_id}/play-history` (REST API)
- **Data Format**: Comprehensive game history with rounds, turns, declarations, and scoring
- **Performance**: Sub-1s response time requirement

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

#### 1.1 Create REST API Service Layer
**Location**: `frontend/src/services/api/`

```
frontend/src/services/api/
├── apiClient.ts          # Base HTTP client with error handling
├── playHistoryService.ts # Play history specific API calls
└── types/               # TypeScript interfaces
    └── playHistory.ts   # Type definitions matching backend
```

**Key Tasks**:
- [ ] Create base API client with fetch wrapper
- [ ] Implement error handling and retry logic
- [ ] Add authentication headers if needed
- [ ] Create TypeScript interfaces for API responses

#### 1.2 Add Routing
**Location**: `frontend/src/App.jsx`

```jsx
// Add new routes
<Route path="/history/:roomId" element={
  <ProtectedRoute requirePlayerName>
    <PlayHistoryPage />
  </ProtectedRoute>
} />
<Route path="/history/:roomId/round/:roundNumber" element={
  <ProtectedRoute requirePlayerName>
    <RoundDetailPage />
  </ProtectedRoute>
} />
```

### Phase 2: Component Architecture (Week 1-2)

#### 2.1 Page Components
**Location**: `frontend/src/pages/`

```
frontend/src/pages/
├── PlayHistoryPage/
│   ├── index.jsx
│   ├── PlayHistoryPage.jsx
│   └── styles.css
└── RoundDetailPage/
    ├── index.jsx
    ├── RoundDetailPage.jsx
    └── styles.css
```

#### 2.2 Feature Components
**Location**: `frontend/src/components/play-history/`

```
frontend/src/components/play-history/
├── RoundSelector/          # Round navigation dropdown
├── PlayerComparison/       # 4-player comparison grid
├── TurnTimeline/          # Turn-by-turn visualization
├── DeclarationAnalysis/   # Declaration vs actual performance
├── RoundSummaryDashboard/ # Comprehensive round metrics
├── HandDisplay/           # Show initial hands and decisions
└── shared/
    ├── PlayerCard.jsx     # Reusable player info card
    ├── PieceDisplay.jsx   # Piece visualization
    └── ScoreDisplay.jsx   # Score formatting
```

### Phase 3: State Management (Week 2)

#### 3.1 Custom Hooks
**Location**: `frontend/src/hooks/`

```typescript
// usePlayHistory.ts
export const usePlayHistory = (roomId: string) => {
  const [history, setHistory] = useState<PlayHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [selectedRound, setSelectedRound] = useState(1);

  // Fetch logic, caching, error handling
  return { history, loading, error, selectedRound, setSelectedRound };
};
```

#### 3.2 Context (Optional)
**Location**: `frontend/src/contexts/`

```typescript
// PlayHistoryContext.tsx - if sharing across multiple components
interface PlayHistoryContextType {
  history: PlayHistory | null;
  selectedRound: number;
  selectedTurn: number | null;
  setSelectedRound: (round: number) => void;
  setSelectedTurn: (turn: number | null) => void;
}
```

### Phase 4: UI Implementation (Week 2-3)

#### 4.1 Navigation Integration
- Add "View History" button in GamePage after game ends
- Add history link in room lobby for completed games
- Add navigation breadcrumbs in history pages

#### 4.2 Responsive Design
- Mobile-first approach with breakpoints
- Collapsible sections for mobile
- Touch-friendly interactions

#### 4.3 Loading States
- Skeleton screens while fetching data
- Progressive loading for large histories
- Error boundaries for graceful failures

### Phase 5: Features by Priority (Week 3-4)

#### Priority 1: Core Views
1. **Round Timeline View** (`1_round_timeline_v2.html` as reference)
   - Round selector in header
   - Initial hands display
   - Declaration phase visualization
   - Turn-by-turn timeline with winner highlights

2. **Player Comparison View** (`3_player_comparison.html` as reference)
   - Side-by-side player statistics
   - Performance metrics
   - Declaration accuracy

#### Priority 2: Advanced Analytics
3. **Turn Analysis** (`2_turn_by_turn_analysis.html` as reference)
   - Detailed play-by-play breakdown
   - Hand state changes
   - Strategic decision points

4. **Round Summary Dashboard** (`4_round_summary_dashboard.html` as reference)
   - Key metrics and visualizations
   - Turn progression charts
   - Timeline of key moments

5. **Declaration Performance** (`5_declaration_performance.html` as reference)
   - Visual comparison of declared vs actual
   - Performance analysis
   - Strategic insights

### Phase 6: Performance & Polish (Week 4)

#### 6.1 Optimization
- [ ] Implement data caching strategy
- [ ] Add pagination for multiple rounds
- [ ] Optimize bundle size with code splitting
- [ ] Add virtual scrolling for long lists

#### 6.2 User Experience
- [ ] Add animations and transitions
- [ ] Implement keyboard navigation
- [ ] Add tooltips and help text
- [ ] Include print-friendly styles

#### 6.3 Testing
- [ ] Unit tests for services and utilities
- [ ] Component tests with React Testing Library
- [ ] Integration tests for API calls
- [ ] E2E tests with Playwright

## Technical Decisions

### 1. Data Fetching Strategy
- **Initial Load**: Fetch full game history on page mount
- **Caching**: Cache in memory with 5-minute TTL
- **Round Selection**: Filter cached data client-side
- **Error Handling**: Show retry button on failure

### 2. Styling Approach
- Use existing project CSS patterns
- Create modular component styles
- Implement dark theme support
- Ensure consistency with game UI

### 3. State Management
- Local component state for UI interactions
- Custom hooks for data fetching
- Context only if needed for deep prop drilling
- No additional state libraries needed

### 4. Type Safety
- Full TypeScript interfaces for API responses
- Strict typing for all components
- Runtime validation for API data
- Proper error types

## Migration Path

### From Mockups to Components
1. Extract styles from HTML mockups
2. Convert to React components with props
3. Add interactivity and state
4. Connect to real API data
5. Add loading and error states

### Integration Points
- **Navigation**: Add links from game end screen
- **Room Page**: Show history for completed games
- **Lobby**: Mark rooms with available history
- **Profile**: Future feature - player statistics

## Success Metrics
- Page load time < 1 second
- API response time < 1 second
- Mobile-friendly responsive design
- Zero runtime errors in production
- Positive user feedback on usability

## Timeline Summary
- **Week 1**: Core infrastructure and routing
- **Week 2**: Component architecture and state
- **Week 3**: UI implementation of core views
- **Week 4**: Advanced features and polish

## Next Steps
1. Review and approve implementation plan
2. Create detailed component specifications
3. Set up development branch
4. Begin Phase 1 implementation
5. Regular progress reviews
