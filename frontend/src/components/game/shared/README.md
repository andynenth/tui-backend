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