# Hybrid Theme System Implementation

## Overview

The theme system now supports a hybrid approach that combines:

1. **Different SVG designs** (classic vs modern piece styles)
2. **CSS color filters** for color variations without new SVG files

## Current Themes

### 1. Classic (No filters)

- Uses classic SVG designs
- Original red (#dc3545) and black (#495057) colors
- No color filters applied

### 2. Modern (Color filters)

- Uses same classic SVG designs
- Transforms colors to yellow (#ffc107) and blue (#0d6efd)
- Uses CSS filters: `hue-rotate()`, `brightness()`, `saturate()`

### 3. Modern Alternative (Different SVGs)

- Uses different SVG designs from `pieces/modern/`
- Can have completely different visual style
- No filters needed if SVGs have built-in colors

### 4. Dark Mode (Color filters)

- Uses classic SVGs with inversion filters
- Good for dark backgrounds

### 5. Ocean (Color filters)

- Transforms to teal and navy colors
- Calming color scheme

## How Color Filters Work

The system applies CSS filters to transform SVG colors:

```javascript
// Example: Yellow/Blue theme
yellowBlue: {
  red: 'brightness(1.1) sepia(1) hue-rotate(45deg) saturate(2)',
  black: 'brightness(0.9) sepia(1) hue-rotate(200deg) saturate(1.5)',
}
```

### Filter Effects:

- `brightness()` - Lightens/darkens the color
- `sepia()` - Converts to sepia tone (required for color shifting)
- `hue-rotate()` - Shifts the hue on the color wheel
- `saturate()` - Increases/decreases color intensity
- `invert()` - Inverts all colors (useful for dark mode)

## Adding New Color Themes

To add a new color variation:

```javascript
// In themeManager.js
const colorFilters = {
  // ... existing filters

  // New sunset theme
  sunset: {
    red: 'brightness(1.1) sepia(1) hue-rotate(15deg) saturate(2)',
    black: 'brightness(0.9) sepia(1) hue-rotate(270deg) saturate(1.5)',
  },
};

// Add theme definition
export const themes = {
  // ... existing themes

  sunset: {
    id: 'sunset',
    name: 'Sunset',
    description: 'Warm orange and purple tones',
    pieceColors: {
      red: '#ff7043', // Orange
      black: '#7b1fa2', // Purple
    },
    pieceAssets: ClassicPieces, // Use existing SVGs
    colorFilter: colorFilters.sunset, // Apply color transformation
    // ... rest of config
  },
};
```

## Benefits of Hybrid Approach

1. **Flexibility**: Can use filters OR different SVGs OR both
2. **Efficiency**: No need to create new SVGs for color variations
3. **Consistency**: Easy to maintain consistent piece shapes
4. **Extensibility**: Can add unlimited color themes
5. **Performance**: Filters are GPU-accelerated

## Testing Color Filters

To experiment with filters in browser DevTools:

```css
/* Select any piece image and add to Styles panel */
filter: brightness(1.2) sepia(1) hue-rotate(120deg) saturate(1.5);
```

Adjust values to see real-time color changes!

## Current Implementation

- Classic theme: Original colors, no filters
- Modern theme: Yellow/Blue via filters on classic SVGs
- Settings modal shows available themes
- Theme persists in localStorage
- All game pieces and UI elements respect theme
