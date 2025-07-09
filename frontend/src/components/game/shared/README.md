# Shared Game Components

This directory contains reusable components that are shared across different game phases.

## Components

### PlayerAvatar
A circular avatar component that displays player initials.

**Usage:**
```jsx
import { PlayerAvatar } from '../shared';

<PlayerAvatar 
  name="John"
  size="medium"  // small | medium | large
  className="custom-class"
/>
```

**Props:**
- `name` (string, required) - Player name to extract initial from
- `size` (string, optional) - Avatar size: 'small', 'medium', or 'large' (default: 'medium')
- `className` (string, optional) - Additional CSS classes

**CSS Classes:**
- `.player-avatar` - Base class
- `.player-avatar--small` - Small size (24x24px)
- `.player-avatar--medium` - Medium size (32x32px)
- `.player-avatar--large` - Large size (36x36px)
- `.player-avatar.active` - Active player state
- `.player-avatar.winner` - Winner state

### GamePiece
A unified component for rendering game pieces across all phases with support for different sizes, variants, and states.

**Usage:**
```jsx
import { GamePiece } from '../shared';

// Basic piece
<GamePiece 
  piece={piece}
  size="medium"
/>

// Selectable piece with value
<GamePiece 
  piece={piece}
  size="large"
  variant="selectable"
  selected={isSelected}
  showValue
  onClick={handleSelect}
/>

// Table piece with flip animation
<GamePiece 
  piece={piece}
  size="small"
  variant="table"
  flipped={isFlipped}
/>
```

**Props:**
- `piece` (object, required) - The piece data containing type, color, and value
- `size` (string, optional) - Piece size: 'mini', 'small', 'medium', 'large' (default: 'medium')
- `variant` (string, optional) - Display variant: 'default', 'table', 'selectable' (default: 'default')
- `selected` (boolean, optional) - Whether the piece is selected (for selectable variant)
- `flipped` (boolean, optional) - Whether the piece is flipped (for table variant)
- `showValue` (boolean, optional) - Whether to show the piece value/points
- `onClick` (function, optional) - Click handler function
- `className` (string, optional) - Additional CSS classes
- `animationDelay` (number, optional) - Animation delay in seconds for staggered effects

**Size Specifications:**
- `.game-piece--mini` - 24x24px (for compact displays)
- `.game-piece--small` - 32x32px (for table pieces)
- `.game-piece--medium` - 44x44px (default size)
- `.game-piece--large` - 62x62px (for player hand)

**Variants:**
- `default` - Standard piece display
- `selectable` - Adds hover effects and selection state
- `table` - Adds flip animation support for revealing pieces

### PieceTray
A unified component for displaying the player's hand of pieces with consistent styling across all game phases.

**Usage:**
```jsx
import { PieceTray } from '../shared';

// Basic tray
<PieceTray 
  pieces={myHand}
  showValues
/>

// Active turn with selection
<PieceTray 
  pieces={myHand}
  variant="active"
  showValues
  onPieceClick={handlePieceSelect}
  selectedPieces={selectedPieces}
/>

// With animation
<PieceTray 
  pieces={myHand}
  showValues
  animateAppear
/>

// Fixed positioning
<PieceTray 
  pieces={myHand}
  variant="fixed"
  showValues
  animateAppear
/>
```

**Props:**
- `pieces` (array) - Array of piece objects to display
- `variant` (string, optional) - Display variant: 'default', 'active', or 'fixed' (default: 'default')
- `onPieceClick` (function, optional) - Click handler for pieces (receives piece and index)
- `selectedPieces` (array, optional) - Array of selected piece IDs for highlighting
- `showValues` (boolean, optional) - Whether to show piece values (default: true)
- `animateAppear` (boolean, optional) - Whether to animate pieces appearing (default: false)
- `className` (string, optional) - Additional CSS classes for the container

**Variants:**
- `default` - Standard positioning within document flow
- `active` - Highlighted with yellow border for player's turn
- `fixed` - Absolutely positioned at bottom of container (useful for consistent positioning)

**Features:**
- Consistent 4-column grid layout
- Active variant with yellow highlight for player's turn
- Automatic piece selection state management
- Staggered animation support
- Responsive design

### FooterTimer
A countdown timer component that displays across game phases and executes a callback when complete.

**Usage:**
```jsx
import { FooterTimer } from '../shared';

// Inline countdown (turn results, scoring)
<FooterTimer 
  prefix="Continuing in"
  onComplete={handleContinue}
  variant="inline"
/>

// Fixed footer countdown (game over)
<FooterTimer 
  duration={10}
  prefix="Returning to lobby in"
  suffix="seconds..."
  onComplete={returnToLobby}
  variant="footer"
/>
```

**Props:**
- `duration` (number, optional) - Initial countdown value in seconds (default: 5)
- `onComplete` (function) - Callback function when countdown reaches 0
- `prefix` (string, optional) - Text to display before the countdown
- `suffix` (string, optional) - Text to display after the countdown (default: "seconds")
- `variant` (string, optional) - Display variant: 'inline' or 'footer' (default: 'inline')
- `className` (string, optional) - Additional CSS classes

**Features:**
- Auto-starts countdown on mount
- Inline variant for embedding in content
- Footer variant with fixed positioning at bottom
- Consistent styling across all game phases
- Ensures proper navigation (e.g., return to lobby)