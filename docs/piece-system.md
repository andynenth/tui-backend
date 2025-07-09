# Liap Tui Piece System Documentation

## Overview

The Liap Tui game uses traditional Chinese chess pieces with a unique reveal mechanism. This document details how pieces are represented, displayed, and animated throughout the game.

## Piece Types and Values

### Piece Hierarchy
The game uses 7 different piece types from Chinese chess, each with specific point values:

| Piece Type | Chinese Character | Red | Black | Point Value |
|------------|-------------------|-----|-------|-------------|
| GENERAL | 將/帥 | 帥 | 將 | 14 |
| ADVISOR | 士/仕 | 仕 | 士 | 13 |
| ELEPHANT | 相/象 | 相 | 象 | 10 |
| CHARIOT | 車/俥 | 俥 | 車 | 9 |
| HORSE | 馬/傌 | 傌 | 馬 | 7 |
| CANNON | 炮/砲 | 砲 | 炮 | 8 |
| SOLDIER | 兵/卒 | 兵 | 卒 | 11 |

### Distribution
- 32 total pieces (16 red, 16 black)
- Each player receives 8 pieces per round
- Pieces are randomly distributed at the start of each round

## Backend Representation

### Piece Format
The backend represents pieces in string format:
```
"PIECE_TYPE_COLOR(value)"
```

Examples:
- `"GENERAL_RED(14)"`
- `"HORSE_BLACK(7)"`
- `"SOLDIER_RED(11)"`

### Data Flow
1. **Dealing Phase**: Backend creates and distributes pieces
2. **Phase Changes**: Pieces sent via WebSocket in `players` data
3. **Turn Phase**: Players' moves tracked in `playerPieces` object

## Frontend Architecture

### Piece Data Structure
The frontend converts backend strings to objects:

```javascript
{
  type: "GENERAL",      // Piece type
  color: "red",         // "red" or "black"
  value: 14,            // Point value
  
  // Additional properties (depending on context):
  kind: "GENERAL",      // Alternative to type
  point: 14,            // Alternative to value
  displayName: "GENERAL RED"
}
```

### Utility Functions (`pieceMapping.js`)

#### `parsePiece(pieceData)`
Converts various piece formats to standardized object:
```javascript
// String input: "GENERAL_RED(14)"
// Object input: { kind: "GENERAL", color: "RED", point: 14 }
// Returns: { type: "GENERAL", color: "red", value: 14 }
```

#### `getPieceDisplay(pieceData)`
Returns the appropriate Chinese character for display:
```javascript
getPieceDisplay("GENERAL_RED(14)") // Returns "帥"
getPieceDisplay({ type: "HORSE", color: "black" }) // Returns "馬"
```

#### `getPieceColorClass(pieceData)`
Returns CSS class for piece coloring:
```javascript
getPieceColorClass({ color: "red" }) // Returns "piece-red"
getPieceColorClass({ color: "black" }) // Returns "piece-black"
```

## Component Architecture

### GamePiece Component
The main component for rendering pieces with multiple variants:

```jsx
<GamePiece
  piece={pieceObject}
  size="medium"        // mini, small, medium, large
  variant="default"    // default, table, selectable
  selected={false}     // Selection state
  flipped={false}      // Reveal state (table variant)
  showValue={true}     // Show point value
  onClick={handler}    // Click handler
/>
```

### Variants

#### Default Variant
- Used in: Hand display, scoring
- Shows: Chinese character + optional value
- Always visible (no flip animation)

#### Selectable Variant
- Used in: Player's hand during turn
- Shows: Chinese character + selection state
- Click to select/deselect for play

#### Table Variant
- Used in: Center play area
- Shows: "?" when face-down, character when face-up
- Supports flip animation

## Reveal Mechanism

### State Management
```javascript
const [flippedPieces, setFlippedPieces] = useState(new Set());
const hasFlippedThisTurn = useRef(false);
```

- `flippedPieces`: Set of piece IDs that are revealed
- `hasFlippedThisTurn`: Prevents multiple flip triggers

### Flip Timing
1. Players play pieces face-down
2. System tracks when all players have played
3. After 800ms delay, all pieces flip simultaneously
4. Pieces remain revealed until turn ends

### Piece Identification
Each piece has a unique ID: `${playerName}-${index}`
- Example: `"Alice-0"`, `"Bob-2"`
- Used to track which pieces should be flipped

## CSS Animation System

### 3D Transform Setup
```css
.game-piece--table {
  transform-style: preserve-3d;
  transition: transform 0.6s ease;
}

.game-piece--table.flipped {
  transform: rotateY(180deg);
}
```

### Face Structure
```css
.game-piece__face {
  position: absolute;
  backface-visibility: hidden;
}

.game-piece__face--back {
  /* Shows "?" symbol */
}

.game-piece__face--front {
  transform: rotateY(180deg);
  /* Shows actual piece */
}
```

### Color Isolation
```css
/* Colors only apply to non-table pieces and front faces */
.game-piece:not(.game-piece--table).piece-red { color: #DC3545; }
.game-piece__face--front.piece-red { color: #DC3545; }
```

## Play Flow Integration

### Turn Phase Sequence
1. **Play Selection**: Players select pieces from hand
2. **Submission**: Pieces placed face-down in center
3. **Waiting**: All pieces remain hidden
4. **Reveal**: Once all played, 800ms timer starts
5. **Flip**: All pieces flip to show values
6. **Resolution**: Winner determined, pieces collected
7. **Reset**: New turn begins, pieces cleared

### Hand Size Tracking
- Backend sends `hand_size` for each player
- Frontend displays remaining pieces as status icons
- Updates in real-time as pieces are played

## Security Considerations

### Information Hiding
1. **Backend**: Never sends other players' hand contents
2. **Frontend**: Face-down pieces show no identifying information
3. **Network**: Pieces only revealed after all players act

### State Validation
- Backend validates all piece plays
- Ensures correct piece count per player
- Prevents playing pieces not in hand

## Common Issues and Solutions

### Issue: Colors showing on face-down pieces
**Solution**: CSS selectors exclude table variant from color rules

### Issue: Pieces not flipping
**Solution**: Check `flippedPieces` state and piece ID generation

### Issue: Wrong Chinese characters
**Solution**: Verify piece type mapping in `PIECE_CHINESE_MAP`

### Issue: Hand size incorrect
**Solution**: Ensure backend sends `hand_size` in player data

## Future Enhancements

1. **Animation Improvements**
   - Staggered flip animations
   - Piece movement animations
   - Victory celebration effects

2. **Accessibility**
   - Screen reader support for pieces
   - High contrast mode
   - Piece tooltips

3. **Customization**
   - Alternative piece sets
   - Color themes
   - Animation speed settings