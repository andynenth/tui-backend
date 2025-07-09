# Shared Components Refactoring Plan

## Overview
This document outlines the plan to extract duplicated UI code into reusable shared components, improving maintainability and reducing code duplication in the Liap Tui frontend.

## Current State Analysis

### Identified Duplications
1. **Player Avatar** - Initial display in circles (4+ places)
2. **Piece Tray** - Hand display grid (3 places)
3. **Individual Piece** - Single piece display (5+ places)
4. **Countdown Timer** - Auto-advance timer (3 places)
5. **Score Display** - Formatted score with +/- (2+ places)

### Current Architecture Issues
- Copy-pasted code across phase components
- Inconsistent implementations of same UI pattern
- Changes require updating multiple files
- No clear location for shared components

## Implementation Strategy

### Phase 1: Minimal Structure Change (Current)
**Goal**: Extract shared components with minimal disruption

```
frontend/src/components/game/
├── shared/                    # NEW - Add only this folder
│   ├── PlayerAvatar.jsx
│   ├── PieceTray.jsx
│   ├── Piece.jsx
│   ├── CountdownTimer.jsx
│   └── ScoreDisplay.jsx
├── content/                   # Keep existing
│   ├── PreparationContent.jsx
│   ├── DeclarationContent.jsx
│   └── ...
├── GameContainer.jsx          # Keep existing
└── ...                        # Keep all other files
```

### Phase 2: Future Reorganization (After Learning)
**Goal**: Reorganize based on patterns that emerge

```
frontend/src/
├── features/
│   ├── game/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── utils/
│   └── shared/
│       ├── components/
│       └── hooks/
```

## Component Extraction Order

### 1. PlayerAvatar (Start Here)
**Why first**: Simplest component, low risk, high usage

**Current Usage**:
```jsx
// TurnResultsContent.jsx
<div className="tr-player-avatar">
  {getPlayerInitial(play.playerName)}
</div>

// ScoringContent.jsx
<div className="sc-player-avatar">
  {getPlayerInitial(score.playerName)}
</div>

// DeclarationContent.jsx
<div className="dec-player-avatar">
  {getPlayerInitial(player.name)}
</div>
```

**Planned API**:
```jsx
<PlayerAvatar 
  name="Alice"
  className="tr-player-avatar"  // Optional, defaults to "player-avatar"
  size="medium"                  // Optional: small, medium, large
/>
```

### 2. Individual Piece
**Why second**: Used by PieceTray, foundation component

**Current Variations**:
- Full piece with points (hand display)
- Mini piece (turn results)
- Clickable piece (turn phase)

**Planned API**:
```jsx
<Piece 
  piece={pieceObject}
  variant="full"         // full, mini, compact
  selected={false}
  onClick={handleClick}  // Optional
  interactive={true}     // Optional
/>
```

### 3. PieceTray
**Why third**: Builds on Piece component, eliminates most duplication

**Current Usage**: Preparation, Declaration, Turn phases

**Planned API**:
```jsx
<PieceTray 
  pieces={myHand}
  selectedPieces={[0, 2]}      // Optional - indices of selected
  onPieceClick={handleSelect}   // Optional
  interactive={isMyTurn}        // Optional
  layout="grid"                 // Optional: grid, row, compact
/>
```

### 4. CountdownTimer
**Why fourth**: More complex with behavior, good learning experience

**Current Usage**: Turn Results (5s), Scoring (5s), Game Over (10s)

**Planned API**:
```jsx
<CountdownTimer 
  initialTime={5}
  onComplete={handleContinue}
  message="Continuing in {time} seconds"  // Optional template
  autoStart={true}                        // Optional
/>
```

### 5. ScoreDisplay
**Why last**: Less frequently used, can wait

**Planned API**:
```jsx
<ScoreDisplay 
  value={-15}
  showSign={true}      // Shows +/-
  size="large"         // small, medium, large
  animate={true}       // Optional entrance animation
/>
```

## Implementation Guidelines

### Component Design Principles
1. **Props over Configuration**: Make behavior explicit through props
2. **Sensible Defaults**: Components should work with minimal props
3. **Composition over Complexity**: Prefer simple components that compose well
4. **Accessibility**: Include ARIA labels and keyboard support where needed

### Testing Strategy
- Create simple test for each shared component
- Test all variations/props
- Ensure backward compatibility

### Migration Process
For each component:
1. Create shared component with tests
2. Replace one usage and verify
3. Replace all other usages
4. Remove duplicate code
5. Document in this plan

## Success Metrics
- [ ] Zero duplicate implementations of common patterns
- [ ] All shared components have tests
- [ ] Reduced total lines of code by ~20%
- [ ] Single source of truth for each UI pattern

## Progress Tracking

### Phase 1: Component Extraction
- [ ] PlayerAvatar
  - [ ] Component created
  - [ ] Tests written
  - [ ] Replaced in TurnResultsContent
  - [ ] Replaced in ScoringContent
  - [ ] Replaced in DeclarationContent
  - [ ] Replaced in GameOverContent
  
- [ ] Piece
  - [ ] Component created
  - [ ] Tests written
  - [ ] All usages replaced
  
- [ ] PieceTray
  - [ ] Component created
  - [ ] Tests written
  - [ ] Replaced in PreparationContent
  - [ ] Replaced in DeclarationContent
  - [ ] Replaced in TurnContent
  
- [ ] CountdownTimer
  - [ ] Component created
  - [ ] Tests written
  - [ ] Replaced in all phases
  
- [ ] ScoreDisplay
  - [ ] Component created
  - [ ] Tests written
  - [ ] All usages replaced

### Phase 2: Architecture Decisions
- [ ] Evaluate wrapper pattern necessity
- [ ] Decide on final folder structure
- [ ] Plan TypeScript migration
- [ ] Consider state management options

## Notes
- Start small, learn, then expand
- Keep existing code working throughout
- Document decisions and learnings
- Prioritize developer experience

## Next Steps
1. Create `shared/` folder
2. Implement PlayerAvatar component
3. Write tests for PlayerAvatar
4. Replace first usage and verify
5. Continue with remaining usages

Last Updated: [Current Date]