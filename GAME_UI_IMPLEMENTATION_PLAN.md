# Game UI Implementation Plan

## Overview
Update the frontend game UI to match the provided mockup designs exactly, using custom CSS following the existing room management pattern. Implementation will use a hybrid approach that maintains backend compatibility while creating new visual components.

## Architecture Decision
- **Approach**: Hybrid (shared layout + phase-specific content)
- **Styling**: Custom CSS following existing pattern (no Tailwind for game UI)
- **State Management**: Keep existing GameService/hooks unchanged
- **Backend**: No changes required

## Implementation Phases

### Phase 1: Foundation Setup (Day 1) ✅ COMPLETED
**Goal**: Create the base structure and shared components

#### Detailed Tasks:

##### 1.1 Create Directory Structure
- [x] Create `frontend/src/styles/components/game/` directory
- [x] Create empty CSS files:
  - [x] `_variables.css`
  - [x] `_animations.css` 
  - [x] `gamelayout.css`

##### 1.2 Setup CSS Variables
- [ ] In `_variables.css`, add game-specific variables:
  - [ ] Gradient definitions from mockups
  - [ ] Game-specific spacing values
  - [ ] Animation durations
  - [ ] Z-index layers
- [ ] Import `_variables.css` in `globals.css`

##### 1.3 Setup Animation Keyframes
- [ ] In `_animations.css`, create keyframes:
  - [ ] `@keyframes dealing` (card animation)
  - [ ] `@keyframes progress` (progress bar)
  - [ ] `@keyframes slideIn` (panel slides)
  - [ ] `@keyframes pieceAppear` (piece fade-in)
  - [ ] `@keyframes bounceIn` (badge appear)
  - [ ] `@keyframes flipIn` (title change)
  - [ ] `@keyframes confetti-fall` (for later)
- [ ] Import `_animations.css` in `globals.css`

##### 1.4 Create GameLayout Component Structure
- [ ] Create `frontend/src/components/game/GameLayout.jsx`
- [ ] Add component skeleton with props interface
- [ ] Add prop validation with PropTypes

##### 1.5 Implement GameLayout Container
- [ ] Add main container div with `gl-game-container` class
- [ ] Import and link `gamelayout.css`
- [ ] Add container styles in CSS:
  - [ ] Fixed dimensions (9:16 ratio)
  - [ ] Background gradients
  - [ ] Border and shadows
  - [ ] Border radius

##### 1.6 Implement Round Indicator
- [ ] Add round indicator JSX in top-right
- [ ] Create `.gl-round-indicator` styles:
  - [ ] Positioning (absolute)
  - [ ] Background gradient
  - [ ] Typography
  - [ ] Shadow effects
- [ ] Connect to `roundNumber` prop

##### 1.7 Implement Multiplier Badge
- [ ] Add conditional multiplier badge JSX
- [ ] Create `.gl-multiplier-badge` styles:
  - [ ] Red gradient background
  - [ ] Positioning (top-left)
  - [ ] Show/hide logic
- [ ] Add `show` class animation

##### 1.8 Implement Phase Header
- [ ] Add phase header section JSX
- [ ] Create header styles:
  - [ ] `.gl-phase-header` container
  - [ ] `.gl-phase-title` with Crimson Pro font
  - [ ] `.gl-phase-subtitle` styling
  - [ ] Header gradient background
  - [ ] Bottom border with pseudo-element
- [ ] Add phase title/subtitle helper functions

##### 1.9 Add Content Area
- [ ] Add content section container
- [ ] Create `.gl-content-section` styles
- [ ] Add `{children}` prop rendering
- [ ] Set up proper flex layout

##### 1.10 Update GameContainer
- [ ] Import GameLayout component
- [ ] Wrap preparation phase return:
  - [ ] Keep existing PreparationUI for now
  - [ ] Wrap in GameLayout
  - [ ] Pass required props
- [ ] Test that it renders without breaking

#### Deliverables:
- GameLayout.jsx component
- Base CSS files (_variables.css, _animations.css, gamelayout.css)
- Updated GameContainer with layout wrapper
- All animations defined and ready to use

---

### Phase 2: Preparation Phase (Day 2) ✅ COMPLETED
**Goal**: Implement preparation phase with dealing animation and weak hand UI

#### Detailed Tasks:

##### 2.1 Create Piece Mapping Utility
- [x] Create `frontend/src/utils/pieceMapping.js`
- [ ] Add piece type to Chinese character mapping:
  - [ ] Map GENERAL_RED → "将"
  - [ ] Map GENERAL_BLACK → "帅"
  - [ ] Map ADVISOR → "士"
  - [ ] Map ELEPHANT → "象"
  - [ ] Map CHARIOT → "车"
  - [ ] Map HORSE → "马"
  - [ ] Map CANNON → "炮"
  - [ ] Map SOLDIER → "兵/卒"
- [ ] Add helper function `getPieceDisplay(piece)`
- [ ] Export mapping object and helper

##### 2.2 Create PreparationContent Component
- [ ] Create `frontend/src/components/game/content/PreparationContent.jsx`
- [ ] Add component skeleton
- [ ] Add PropTypes for all props
- [ ] Import piece mapping utility

##### 2.3 Create Preparation CSS
- [ ] Create `frontend/src/styles/components/game/preparation.css`
- [ ] Import in PreparationContent component
- [ ] Add CSS prefix comment `/* gp- prefix */`

##### 2.4 Implement Dealing State
- [ ] Add `showDealing` local state (default true)
- [ ] Add `dealingComplete` state
- [ ] Create dealing container JSX structure
- [ ] Add dealing container styles:
  - [ ] `.gp-dealing-container` layout
  - [ ] `.gp-dealing-icon` positioning
  - [ ] `.gp-dealing-message` text
  - [ ] `.gp-dealing-status` subtext

##### 2.5 Implement Card Stack Animation
- [ ] Create card stack JSX (3 divs)
- [ ] Add `.gp-card-stack` styles:
  - [ ] Circle shape with borders
  - [ ] Question mark pseudo-element
  - [ ] Gradient background
- [ ] Apply dealing animation:
  - [ ] Different delays for each stack
  - [ ] Opacity variations
  - [ ] Transform animations

##### 2.6 Implement Progress Bar
- [ ] Add progress bar JSX structure
- [ ] Create progress styles:
  - [ ] `.gp-progress-container` wrapper
  - [ ] `.gp-progress-bar` track
  - [ ] `.gp-progress-fill` animated fill
- [ ] Link animation to dealing duration

##### 2.7 Setup Auto-transition from Dealing
- [ ] Add useEffect for timing
- [ ] Set 3.5s timeout to hide dealing
- [ ] Update `showDealing` state
- [ ] Transition to hand display

##### 2.8 Implement Weak Hand Alert
- [ ] Add weak hand alert JSX structure
- [ ] Create alert styles:
  - [ ] `.gp-weak-hand-alert` container
  - [ ] Yellow gradient background
  - [ ] `.gp-alert-title` with icon
  - [ ] `.gp-alert-message` text
  - [ ] `.gp-alert-buttons` layout
- [ ] Add show/hide logic based on props

##### 2.9 Style Alert Buttons
- [ ] Create button styles:
  - [ ] `.gp-alert-button` base
  - [ ] `.gp-alert-button.primary` (yellow)
  - [ ] `.gp-alert-button.secondary` (gray)
- [ ] Add hover states
- [ ] Connect to action handlers

##### 2.10 Implement Hand Section
- [ ] Add hand section JSX structure
- [ ] Create hand section styles:
  - [ ] `.gp-hand-section` container
  - [ ] Background gradient
  - [ ] Top border styling
  - [ ] Pseudo-element decoration
- [ ] Add pieces tray grid layout

##### 2.11 Implement Game Pieces
- [ ] Create piece rendering logic
- [ ] Map pieces using pieceMapping utility
- [ ] Create piece styles:
  - [ ] `.gp-piece` base styles
  - [ ] Circle shape with aspect ratio
  - [ ] `.gp-piece.red` color variant
  - [ ] `.gp-piece.black` color variant
- [ ] Add shadow and border effects

##### 2.12 Add Piece Content
- [ ] Implement piece character display
- [ ] Add `.gp-piece-character` styles
- [ ] Add `.gp-piece-points` badge
- [ ] Style points display

##### 2.13 Implement Piece Animations
- [ ] Add staggered animation delays
- [ ] Apply `pieceAppear` animation
- [ ] Set initial opacity to 0
- [ ] Animate to full opacity/scale

##### 2.14 Handle Edge Cases
- [ ] Handle empty hand
- [ ] Handle no weak players
- [ ] Add loading state if needed
- [ ] Test with different player counts

##### 2.15 Integration Testing
- [ ] Update GameContainer to use PreparationContent
- [ ] Remove GameLayout wrapper temporarily
- [ ] Test dealing animation timing
- [ ] Test weak hand alert display
- [ ] Verify piece display with Chinese characters
- [ ] Test responsive behavior

#### Deliverables:
- PreparationContent.jsx component
- preparation.css with all animations
- pieceMapping.js utility
- Working dealing animation (3.5s)
- Weak hand alert functionality
- Animated piece display with Chinese characters

---

### Phase 3: Declaration Phase (Days 2-3) ✅ COMPLETED
**Goal**: Implement declaration UI with sliding panel

#### Tasks:
- [x] Create DeclarationContent component
- [x] Create declaration.css with:
  - Player list styling
  - Declaration panel (sliding tray)
  - Option grid layout
  - Status badges

- [x] Implement features:
  - Player rows with status (waiting/declaring/declared)
  - Declaration options 0-8
  - Disabled options based on rules
  - Sliding panel animation
  - Zero streak warnings

#### Deliverables:
- DeclarationContent.jsx
- declaration.css
- Working declaration panel with animations

---

### Phase 4: Turn Phase (Days 3-4) ✅ COMPLETED
**Goal**: Implement complex table layout with piece playing

#### Tasks Completed:
- [x] Create TurnContent component with full turn phase UI
- [x] Create turn.css with all required styles
- [x] Implement circular table with grid pattern
- [x] Create player piece areas for all 4 positions
- [x] Add player summary bars with stats
- [x] Implement piece selection and confirmation panel
- [x] Add piece flip animations after all players have played
- [x] Fix turn indicator to show player stats instead of turn number
- [x] Remove bottom player summary bar (duplicate)
- [x] Update confirm panel text to show requirements
- [x] Remove play type display from turn UI
- [x] Fix pieces tray to always show 2 rows

#### Backend Fixes Implemented:
- [x] Added play type calculation from pieces
- [x] Added play value calculation using PIECE_POINTS
- [x] Added combination validation (only for starters)
- [x] Added ownership validation
- [x] Added immediate piece removal
- [x] Added validation error feedback
- [x] Added hand size consistency checks
- [x] Fixed validation to allow non-starters to play any pieces

#### Deliverables:
- TurnContent.jsx with complete functionality
- turn.css with all animations
- Backend validation system (8 fixes)
- Working piece selection, play, and flip animations

---

### Phase 5: Results & Scoring (Days 4-5)
**Goal**: Implement turn results and scoring displays

#### Turn Results Tasks:

##### 5.1 Create TurnResultsContent Component
- [ ] Create `frontend/src/components/game/content/TurnResultsContent.jsx`
- [ ] Add component skeleton with PropTypes
- [ ] Import from GameContainer for turn_results phase
- [ ] Add props: turnWinner, winningPlay, playerStats, players

##### 5.2 Create Turn Results CSS
- [ ] Create `frontend/src/styles/components/game/turnresults.css`
- [ ] Import in TurnResultsContent component
- [ ] Import in globals.css
- [ ] Add CSS prefix comment `/* tr- prefix */`

##### 5.3 Implement Winner Display
- [ ] Create winner section with crown icon
- [ ] Add `.tr-winner-section` container styles
- [ ] Add `.tr-crown-icon` with bounce animation
- [ ] Add `.tr-winner-name` typography
- [ ] Add `.tr-winner-subtitle` for "won this turn" text

##### 5.4 Implement Winning Play Display
- [ ] Create pieces display area
- [ ] Add `.tr-winning-play` container
- [ ] Map pieces using getPieceDisplay utility
- [ ] Add `.tr-piece` styles (similar to turn phase)
- [ ] Show play type if available

##### 5.5 Implement Pile Count Display
- [ ] Add pile count section
- [ ] Create `.tr-pile-count` styles
- [ ] Show number of piles won
- [ ] Add pile icon/visual indicator

##### 5.6 Implement Auto-transition Timer
- [ ] Add countdown state (7 seconds)
- [ ] Create useEffect for countdown
- [ ] Add `.tr-timer` progress bar
- [ ] Animate progress bar countdown
- [ ] Trigger phase transition at 0

##### 5.7 Add Continue Button
- [ ] Add manual continue button
- [ ] Style with `.tr-continue-button`
- [ ] Connect to phase transition
- [ ] Show remaining time on button

#### Scoring Tasks:

##### 5.8 Create ScoringContent Component
- [ ] Create `frontend/src/components/game/content/ScoringContent.jsx`
- [ ] Add component skeleton with PropTypes
- [ ] Import from GameContainer for scoring phase
- [ ] Add props: playerScores, roundScores, multipliers

##### 5.9 Create Scoring CSS
- [ ] Create `frontend/src/styles/components/game/scoring.css`
- [ ] Import in ScoringContent component
- [ ] Import in globals.css
- [ ] Add CSS prefix comment `/* sc- prefix */`

##### 5.10 Implement Score Cards Layout
- [ ] Create 2x2 grid for 4 players
- [ ] Add `.sc-score-grid` container
- [ ] Add `.sc-score-card` for each player
- [ ] Add player avatar and name section
- [ ] Style cards with gradients and shadows

##### 5.11 Implement Score Details
- [ ] Add declared vs actual piles display
- [ ] Create `.sc-piles-row` with two values
- [ ] Add `.sc-declared` and `.sc-actual` styles
- [ ] Show difference indicator (arrow/symbol)

##### 5.12 Implement Points Calculation
- [ ] Add points section to each card
- [ ] Show base points calculation
- [ ] Add multiplier indicator if active
- [ ] Animate point changes
- [ ] Highlight positive/negative scores

##### 5.13 Implement Total Scores
- [ ] Add total score section
- [ ] Create `.sc-total-score` prominent display
- [ ] Add score change animation
- [ ] Show running total
- [ ] Highlight score leaders

##### 5.14 Add Round Summary
- [ ] Add round complete message
- [ ] Show current standings
- [ ] Add continue to next round button
- [ ] Handle game over condition check

#### Deliverables:
- TurnResultsContent.jsx with winner display and auto-transition
- turnresults.css with all animations
- ScoringContent.jsx with score calculations
- scoring.css with card layout and animations

---

### Phase 6: Game Over (Day 5)
**Goal**: Implement game over with celebrations

#### Tasks:

##### 6.1 Create GameOverContent Component
- [ ] Create `frontend/src/components/game/content/GameOverContent.jsx`
- [ ] Add component skeleton with PropTypes
- [ ] Import from GameContainer for game_over phase
- [ ] Add props: winner, finalScores, players, gameStats

##### 6.2 Create Game Over CSS
- [ ] Create `frontend/src/styles/components/game/gameover.css`
- [ ] Import in GameOverContent component
- [ ] Import in globals.css
- [ ] Add CSS prefix comment `/* go- prefix */`

##### 6.3 Implement Confetti Animation
- [ ] Create confetti particles (50+ divs)
- [ ] Add `.go-confetti-container` for positioning
- [ ] Add `.go-confetti` particle styles
- [ ] Create different colors/sizes variants
- [ ] Add falling animation with rotation
- [ ] Randomize delays and positions
- [ ] Use CSS transforms for performance

##### 6.4 Implement Trophy Display
- [ ] Create trophy section
- [ ] Add `.go-trophy-container` centering
- [ ] Add `.go-trophy` SVG or emoji (🏆)
- [ ] Add bounce-in animation
- [ ] Add glow/shine effect
- [ ] Scale animation on appear

##### 6.5 Implement Winner Announcement
- [ ] Add winner name display
- [ ] Create `.go-winner-name` large text
- [ ] Add "Champion!" or similar subtitle
- [ ] Add text appear animation
- [ ] Add celebration message

##### 6.6 Implement Final Rankings
- [ ] Create rankings list
- [ ] Add `.go-rankings` container
- [ ] Add `.go-rank-item` for each player
- [ ] Show position numbers (1st, 2nd, etc)
- [ ] Add medal icons for top 3
- [ ] Show final scores
- [ ] Add staggered appear animation

##### 6.7 Style Medal Indicators
- [ ] Create medal icons (🥇🥈🥉)
- [ ] Add `.go-medal` styles
- [ ] Add shine animation
- [ ] Different colors for each position
- [ ] Only show for top 3 players

##### 6.8 Implement Auto-redirect Timer
- [ ] Add countdown state (10 seconds)
- [ ] Create useEffect for countdown
- [ ] Add `.go-countdown` display
- [ ] Show "Returning to lobby in X..."
- [ ] Redirect to /lobby at 0

##### 6.9 Add Manual Actions
- [ ] Add "Return to Lobby" button
- [ ] Add "Play Again" button (if applicable)
- [ ] Style with `.go-action-button`
- [ ] Add hover effects

##### 6.10 Add Game Statistics
- [ ] Show game duration
- [ ] Show total rounds played
- [ ] Show highest single score
- [ ] Any other interesting stats
- [ ] Style with `.go-stats` section

#### Deliverables:
- GameOverContent.jsx with complete celebration UI
- gameover.css with all animations
- Working confetti animation
- Auto-redirect to lobby functionality
- Responsive layout for all screen sizes

---

### Phase 7: Integration & Polish (Day 6)
**Goal**: Complete integration and polish animations

#### Tasks:
- [ ] Update all imports in GameContainer
- [ ] Test all phase transitions
- [ ] Verify WebSocket data flow
- [ ] Polish animations and transitions
- [ ] Test responsive behavior
- [ ] Add error states
- [ ] Performance optimization

#### Testing Checklist:
- [ ] All phases render correctly
- [ ] Animations are smooth
- [ ] Chinese characters display properly
- [ ] Container maintains 9:16 ratio
- [ ] No console errors
- [ ] WebSocket events handled
- [ ] State updates reflect in UI

---

## Technical Specifications

### CSS Naming Convention
```css
.gl-*   /* GameLayout */
.gp-*   /* Preparation phase */
.gd-*   /* Declaration phase */
.gt-*   /* Turn phase */
.gtr-*  /* Turn results */
.gs-*   /* Scoring phase */
.go-*   /* Game over */
```

### Key Design Elements
1. **Fonts**: Plus Jakarta Sans, Crimson Pro (already in theme.css)
2. **Container**: 9:16 aspect ratio, max 400x711px
3. **Colors**: Use existing theme variables
4. **Shadows**: Multiple layers as in mockups
5. **Animations**: Smooth cubic-bezier transitions

### File Structure (Final)
```
frontend/
├── src/
│   ├── components/
│   │   └── game/
│   │       ├── GameContainer.jsx (modified)
│   │       ├── GameLayout.jsx (new)
│   │       └── content/
│   │           ├── PreparationContent.jsx
│   │           ├── DeclarationContent.jsx
│   │           ├── TurnContent.jsx
│   │           ├── TurnResultsContent.jsx
│   │           ├── ScoringContent.jsx
│   │           └── GameOverContent.jsx
│   ├── styles/
│   │   └── components/
│   │       └── game/
│   │           ├── _variables.css
│   │           ├── _animations.css
│   │           ├── gamelayout.css
│   │           ├── preparation.css
│   │           ├── declaration.css
│   │           ├── turn.css
│   │           ├── turnresults.css
│   │           ├── scoring.css
│   │           └── gameover.css
│   └── utils/
│       └── pieceMapping.js
```

---

## Success Criteria
- ✅ Visual match to mockups (pixel-perfect)
- ✅ All animations working smoothly
- ✅ Chinese characters displaying correctly
- ✅ Fixed 9:16 container responsive
- ✅ No backend changes required
- ✅ Existing game logic preserved
- ✅ WebSocket events handled correctly
- ✅ Smooth phase transitions

## Notes
- Reuse existing theme.css variables where possible
- Follow established CSS patterns from room management
- Keep Tailwind for non-game components
- Test on various screen sizes
- Ensure accessibility (motion preferences)

## Progress Tracking
Use this document to track completion of each phase. Check off tasks as they are completed and note any issues or changes needed.

**Start Date**: ___________
**Target Completion**: ___________
**Actual Completion**: ___________

## COMPLETED WORK (Moved from UI_IMPLEMENTATION_PLAN.md)

### Phase 1: Foundation Setup ✅ COMPLETED
All CSS foundation work was completed including:
- Created `/frontend/src/styles/components/game/` directory structure
- Created `_variables.css` with CSS variables for colors, gradients, shadows, spacing
- Created `_animations.css` with keyframes for all animations
- Implemented GameLayout component with 9:16 aspect ratio container
- Set up proper CSS organization without CSS modules (ESBuild limitation)
- Updated globals.css to import all CSS files

### Phase 2: Preparation Phase ✅ COMPLETED
Successfully implemented preparation phase UI:
- Created PreparationContent component with dealing animation
- Implemented weak hand alert with proper styling
- Created piece mapping utility for Chinese character display
- Fixed all styling to match mockup exactly (light gray/white theme)
- Removed all Tailwind UI headers and enterprise banners
- Converted all inline styles to CSS classes
- Centered game container properly on screen
- Fixed round display (removed hardcoded "/20")

### Phase 3: Declaration Phase ✅ COMPLETED
- Created `/frontend/src/styles/components/game/declaration.css`
- Created DeclarationContent component structure
- Implemented number selection grid (0-8)
- Added total pile count validation (must not equal 8)
- Added consecutive zeros restriction
- Styled confirm/clear buttons with gradients
- Verified panel only shows during player's turn

### Phase 4: Turn Phase ✅ COMPLETED
- Created `/frontend/src/styles/components/game/turn.css`
- Created TurnContent component
- Implemented circular table layout with grid pattern
- Positioned player seats around table
- Added current player indicator
- Created center pile display
- Implemented piece selection from hand
- Added "Play Pieces" and "Pass" button functionality
- Added selected pieces display area

### Phase 5: Results & Scoring ✅ COMPLETED

#### Turn Results Tasks ✅ COMPLETED
- [x] Create TurnResultsContent component
- [x] Create turnresults.css
- [x] Display all players' played pieces
- [x] Highlight winner with crown animation
- [x] Show winning play pieces
- [x] Implement auto-advance timer (5 seconds)
- [x] Show next turn/round starter info

#### Scoring Tasks ✅ COMPLETED  
- [x] Update ScoringUI to use ScoringContent component
- [x] Update scoring.css with exact mockup styles
- [x] Build score cards layout with all details
- [x] Display declared vs actual piles
- [x] Show hit/penalty values with color coding
- [x] Display bonus points (special blue for 0/0)
- [x] Show multiplier when applicable
- [x] Implement auto-countdown timer

### Key Learnings & Blockers Encountered

#### Phase 5 Specific Blockers:
1. **Component Structure Consistency**
   - **Problem**: ScoringUI still used old Tailwind UI instead of new pattern
   - **Solution**: Updated to use ScoringContent component wrapper pattern
   
2. **Data Mapping**
   - **Problem**: Backend data structure different from UI expectations
   - **Solution**: Transform data in wrapper component before passing to content
   
3. **CSS Import**
   - **Problem**: scoring.css wasn't imported in globals.css
   - **Solution**: Added import to ensure styles load
   
4. **Special Score Display**
   - **Problem**: Zero/zero scores needed special blue color coding
   - **Solution**: Added value-blue class and special case logic

#### Phase 4 Specific Blockers:
1. **Backend Data Format Mismatch**
   - **Problem**: Play data had `play.pieces` but UI expected `play.cards`
   - **Solution**: Fixed by using correct property name from backend data
   
2. **Play Type Always "unknown"**
   - **Problem**: Backend wasn't calculating play types, just passing through "unknown"
   - **Solution**: Implemented play type calculation using existing `get_play_type()` function
   
3. **Piece Attribute Error**
   - **Problem**: Code used `piece.type` but Piece object has `piece.name`
   - **Solution**: Fixed to use correct attribute names (name, color, kind)
   
4. **Bot Invalid Plays Blocking UI**
   - **Problem**: Bots playing invalid combinations caused alert popups
   - **Solution**: Updated validation to only check combinations for turn starters
   
5. **Delayed Piece Removal**
   - **Problem**: Pieces only removed after turn completion, causing incorrect hand displays
   - **Solution**: Implemented immediate piece removal when played

#### General Blockers (from earlier phases):
1. **CSS Module Import Issues**
   - **Problem**: ESBuild doesn't support CSS modules out of the box
   - **Solution**: Used regular CSS imports with prefixed class names (gl-, gp-, etc.)
   
2. **Component State Mismatch**
   - **Problem**: Pieces showing "?" - GameService creates different object format than UI expects
   - **Solution**: Updated parsePiece() to handle multiple formats
   
3. **Old UI Persistence**
   - **Problem**: Tailwind headers still showing after changes
   - **Solution**: Found and removed Layout wrapper, updated App.jsx
   
4. **Weak Hand Alert Logic**
   - **Problem**: Complex conditions preventing alert from showing
   - **Solution**: Simplified logic and added debug logging

#### Process Improvements Applied:
1. **Read First, Code Second**: Always read existing code and mockups before implementing
2. **Test Incrementally**: Build and test after each component change
3. **No Inline Styles**: Create CSS classes from the start
4. **Trace Data Flow**: When debugging, follow data from source to display
5. **Check Build Output**: Verify changes are in the built files
6. **Understand Game Rules**: Validate implementation against actual game rules (e.g., starter vs non-starter)
7. **Check Backend Data Structure**: Always verify actual data format before using
8. **Test with Bots**: Ensure UI handles both human and bot actions gracefully
9. **Document Backend Changes**: Keep BACKEND_VALIDATION_FIXES.md updated

### Technical Decisions Made:
1. **No CSS Modules** - ESBuild limitation led to prefix-based naming (gl-, gp-, etc.)
2. **Component Structure** - Separate content components for each phase
3. **Data Handling** - Flexible parsing to handle multiple backend formats
4. **Style Organization** - All styles in CSS files, no inline styles
5. **Sliding Panel Pattern** - Declaration panel slides up only during player's turn
6. **Table Layout** - Fixed positioning for circular game table visualization
7. **Selection State** - Local state for piece selection with visual feedback
8. **Validation Logic** - Client-side validation matching backend rules

### Best Practices Established:
1. **Component Structure**:
   - Always create wrapper UI + content component pattern
   - Keep state management in content components
   - Pass minimal props from wrapper to content

2. **CSS Organization**:
   - One CSS file per phase with consistent prefix
   - Import in globals.css immediately after creation
   - No inline styles - use CSS classes

3. **Development Process**:
   - Read mockup HTML first
   - Create CSS file
   - Create content component
   - Update wrapper component
   - Test incrementally
   - Rebuild and verify

4. **Common Patterns**:
   - Use `show` class for conditional visibility
   - Local state for UI interactions
   - Proper prop validation with PropTypes
   - Consistent naming conventions

### Recommendations for Phases 5 & 6:

1. **Data Validation First**:
   - Check exact data structure from backend before coding
   - Log phase_data to console to see actual format
   - Don't assume property names - verify them

2. **Test with Real Game Flow**:
   - Test turn_results with actual turn completion data
   - Ensure scoring calculations match backend logic
   - Verify game_over receives winner data correctly

3. **Animation Performance**:
   - Use CSS transforms for confetti (not position)
   - Limit particle count based on device performance
   - Add prefers-reduced-motion checks

4. **Error Handling**:
   - Handle missing data gracefully (winner might be null)
   - Add fallbacks for missing player stats
   - Ensure timers clean up on unmount

5. **Cross-Phase Testing**:
   - Test transition from turn → turn_results → turn
   - Test transition from scoring → preparation (new round)
   - Test scoring → game_over transition

6. **Backend Integration Points**:
   - Turn Results: turnWinner, winningPlay, pilesWon
   - Scoring: playerScores, roundScores, multipliers
   - Game Over: winner, finalScores, gameStats