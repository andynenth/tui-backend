# SVG Piece Implementation Plan

## Executive Summary

This document outlines the implementation plan for replacing font-based Chinese character rendering with production-ready SVG assets in the Liap Tui xiangqi game. The migration will maintain 100% visual and functional compatibility while eliminating font dependencies and improving cross-platform consistency.

## Goals & Scope

### Primary Goals
- Replace Chinese character font rendering with SVG assets
- Maintain identical visual appearance and functionality
- Eliminate SimSun/宋体 font dependencies
- Improve cross-platform rendering consistency
- Enable easy rollback mechanism

### Scope
- **In Scope**: GamePiece component rendering, piece display utilities, CSS styling
- **Out of Scope**: Game logic, networking, state management, other UI components

### Success Criteria
- All game phases render pieces identically with SVG assets
- All interactive features (selection, hover, flipping) work unchanged
- No performance degradation
- Easy toggle between font and SVG rendering

## Current System Context

### Architecture Overview
- **Frontend**: React 19.1.0 with ESBuild bundling
- **Piece Rendering**: Centralized through single GamePiece component
- **Styling**: Unified CSS system with size variants and interactive states
- **Assets**: 14 SVG files already organized in `/frontend/src/assets/pieces/`

### Current Implementation
```jsx
// GamePiece.jsx line 85
<div className="game-piece__character">{getPieceDisplay(piece)}</div>
```

### Usage Points
- `TurnContent.jsx` - Turn phase gameplay
- `TurnResultsContent.jsx` - Result displays
- `PieceTray.jsx` - Hand display
- All use identical GamePiece component with consistent props

## Proposed Solution

### Technical Approach
Implement conditional rendering in the GamePiece component to support both font and SVG rendering modes, controlled by a feature flag. This approach provides:

- **Minimal code changes** (3 files total)
- **Zero breaking changes** to existing functionality
- **Instant rollback capability** via feature flag
- **Gradual migration path** for testing and deployment

### Architecture Benefits
- Leverages existing unified component architecture
- Maintains all current features (animations, interactions, sizing)
- No build configuration changes required
- ESBuild handles SVG imports natively

## Implementation Steps

### Phase 1: Utility Function Enhancement
**File**: `/frontend/src/utils/pieceMapping.js`

#### Sub-tasks:
1. **Add SVG import integration**
   ```javascript
   import * as PieceAssets from '../assets/pieces';
   ```

2. **Implement SVG piece lookup function**
   ```javascript
   export function getPieceSVG(pieceData) {
     const piece = parsePiece(pieceData);
     const fullType = `${piece.kind}_${piece.color?.toUpperCase()}`;
     return PieceAssets.getPieceAsset(fullType);
   }
   ```

3. **Add feature flag**
   ```javascript
   export const USE_SVG_PIECES = true; // Feature flag for easy toggle
   ```

### Phase 2: Component Integration
**File**: `/frontend/src/components/game/shared/GamePiece.jsx`

#### Sub-tasks:
1. **Import new utility functions**
   ```javascript
   import { getPieceDisplay, getPieceColorClass, formatPieceValue, getPieceSVG, USE_SVG_PIECES } from '../../../utils/pieceMapping';
   ```

2. **Implement conditional rendering**
   Replace line 85:
   ```jsx
   <div className="game-piece__character">
     {USE_SVG_PIECES ? (
       <img src={getPieceSVG(piece)} alt={getPieceDisplay(piece)} />
     ) : (
       getPieceDisplay(piece)
     )}
   </div>
   ```

3. **Update flippable piece rendering**
   Update line 76 for consistency:
   ```jsx
   <div className={`game-piece__face game-piece__face--front ${getPieceColorClass(piece)}`}>
     {USE_SVG_PIECES ? (
       <img src={getPieceSVG(piece)} alt={getPieceDisplay(piece)} />
     ) : (
       getPieceDisplay(piece)
     )}
   </div>
   ```

### Phase 3: CSS Styling Support
**File**: `/frontend/src/styles/components/game/shared/game-piece.css`

#### Sub-tasks:
1. **Add base image sizing**
   ```css
   /* SVG image sizing within game pieces */
   .game-piece img {
     width: 80%;
   }
   ```

2. **Add size variant support**
   ```css
   .game-piece--mini img { width: 60%; }
   .game-piece--small img { width: 65%; }
   .game-piece--medium img { width: 62%; }
   .game-piece--large img { width: 80%; }
   ```

### Phase 4: Testing & Validation

#### Sub-tasks:
1. **Unit Testing**
   - Test getPieceSVG function with all piece types
   - Verify feature flag toggle functionality
   - Test fallback behavior for invalid pieces

2. **Integration Testing**
   - Test all game phases (preparation, declaration, turn, scoring)
   - Verify all interactive features (selection, hover, flipping)
   - Test all size variants across different components
   - Validate animation compatibility

3. **Visual Regression Testing**
   - Compare SVG vs font rendering pixel-perfect
   - Test on different browsers/platforms
   - Verify accessibility (alt text, screen readers)

4. **Performance Testing**
   - Measure rendering performance vs font rendering
   - Verify bundle size impact
   - Test loading times

## Affected Files

### Modified Files (3)
1. **`/frontend/src/utils/pieceMapping.js`**
   - **Changes**: Add SVG import, getPieceSVG function, feature flag
   - **Risk Level**: Low (additive changes only)

2. **`/frontend/src/components/game/shared/GamePiece.jsx`**
   - **Changes**: Add conditional rendering for SVG vs text
   - **Risk Level**: Medium (core rendering logic)

3. **`/frontend/src/styles/components/game/shared/game-piece.css`**
   - **Changes**: Add image sizing rules
   - **Risk Level**: Low (additive CSS only)

### Dependencies (0 new)
- No new npm packages required
- No build configuration changes needed
- ESBuild already supports SVG imports

### Assets (already exist)
- **`/frontend/src/assets/pieces/`** - 14 SVG files with proper naming
- **`/frontend/src/assets/pieces/index.js`** - Import/export utilities

## Risk Assessment

### Low Risk
- Additive changes to utilities and CSS
- Feature flag allows instant rollback
- No external dependencies

### Medium Risk
- Core component modification requires thorough testing
- Conditional rendering adds complexity

### Mitigation Strategies
- Comprehensive testing across all usage scenarios
- Feature flag for immediate rollback if issues arise
- Gradual deployment with monitoring

## Success Metrics

### Functional Metrics
- ✅ All game phases render correctly with SVG pieces
- ✅ All interactive features work identically
- ✅ All size variants display properly
- ✅ Feature flag toggle works seamlessly

### Performance Metrics
- ✅ No degradation in rendering performance
- ✅ Bundle size impact < 5% increase
- ✅ Page load time unchanged

### Quality Metrics
- ✅ Zero visual regression
- ✅ Accessibility compliance maintained
- ✅ Cross-platform consistency improved

## Rollback Plan

### Immediate Rollback
```javascript
// In pieceMapping.js
export const USE_SVG_PIECES = false;
```

### Full Rollback
1. Revert the 3 modified files
2. Remove SVG assets if needed
3. Verify font rendering works correctly

## Timeline Estimate

- **Phase 1**: 2 hours (utility functions)
- **Phase 2**: 3 hours (component integration)
- **Phase 3**: 1 hour (CSS styling)
- **Phase 4**: 4 hours (testing & validation)
- **Total**: ~10 hours for complete implementation and testing

## Notes

- This plan leverages the existing unified architecture perfectly
- Minimal changes for maximum impact
- All assets are already prepared and organized
- Implementation maintains 100% backward compatibility