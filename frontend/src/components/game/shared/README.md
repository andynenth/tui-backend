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