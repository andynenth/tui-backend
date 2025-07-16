# Theme System Implementation Plan

## Executive Summary

This document outlines the implementation plan for a theme system that allows players to customize the appearance of game pieces and UI elements in Liap TUI. The system will support two initial themes with the ability to easily extend to more themes in the future.

## Goals & Objectives

### Primary Goals
- Allow players to choose between different visual themes
- Change piece colors and display style (SVG vs Chinese characters)
- Apply theme colors to UI decorative elements
- Persist theme selection across sessions
- Keep implementation simple and maintainable

### Success Criteria
- Theme changes apply instantly without page reload
- Theme selection persists in localStorage
- All piece displays respect the selected theme
- UI animations use theme colors
- System is easily extensible for future themes

## System Architecture

### 1. Theme Structure

```javascript
const theme = {
  id: 'classic',                    // Unique identifier
  name: 'Classic',                  // Display name
  description: 'Traditional red and black pieces with SVG graphics',
  pieceColors: {
    red: '#dc3545',                // Color for red pieces
    black: '#495057'               // Color for black pieces
  },
  useSVG: true,                    // true = SVG images, false = Chinese characters
  uiElements: {
    startIcon: {                   // Start page animated icon
      main: '將',                  // Main circle character
      piece1: '帥',                // Top-right rotating piece
      piece2: '卒'                 // Bottom-left rotating piece
    },
    lobbyEmpty: '將'               // Empty lobby background character
  }
}
```

### 2. Available Themes

#### Classic Theme (Default)
- **ID**: `classic`
- **Colors**: Red (#dc3545), Black (#495057)
- **Display**: SVG images from existing assets
- **Description**: Traditional xiangqi appearance

#### Modern Blue Theme
- **ID**: `modern`
- **Colors**: Blue (#0d6efd), Green (#28a745)
- **Display**: Chinese characters (no images)
- **Description**: Fresh, modern color scheme

### 3. Technical Components

#### 3.1 Theme Manager (`utils/themeManager.js`)
```javascript
// Theme definitions
export const themes = { classic: {...}, modern: {...} };

// Get current theme from localStorage
export const getTheme = () => {
  const saved = localStorage.getItem('liap-tui-theme');
  return saved ? themes[saved] : themes.classic;
};

// Save theme and apply CSS variables
export const setTheme = (themeId) => {
  localStorage.setItem('liap-tui-theme', themeId);
  applyThemeColors(themes[themeId]);
};

// Apply theme colors to CSS variables
export const applyThemeColors = (theme) => {
  document.documentElement.style.setProperty('--piece-color-red', theme.pieceColors.red);
  document.documentElement.style.setProperty('--piece-color-black', theme.pieceColors.black);
  document.documentElement.style.setProperty('--ui-piece-red', theme.pieceColors.red);
  document.documentElement.style.setProperty('--ui-piece-black', theme.pieceColors.black);
};
```

#### 3.2 Theme Context (`contexts/ThemeContext.jsx`)
```javascript
const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [currentTheme, setCurrentTheme] = useState(() => getTheme());
  
  useEffect(() => {
    applyThemeColors(currentTheme);
  }, []);

  const changeTheme = (themeId) => {
    const theme = themes[themeId];
    setTheme(themeId);
    setCurrentTheme(theme);
  };

  return (
    <ThemeContext.Provider value={{ currentTheme, changeTheme, themes }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
```

#### 3.3 Settings UI Component
- Floating gear button (top-right of game containers)
- Modal with theme selection
- Preview of piece colors
- Apply/Cancel buttons

### 4. Integration Points

#### 4.1 GamePiece Component
```javascript
// Check theme for SVG vs character display
const displayContent = currentTheme.useSVG 
  ? <img src={getPieceSVG(piece)} alt={getPieceDisplay(piece)} />
  : getPieceDisplay(piece);
```

#### 4.2 CSS Variables
```css
/* Game pieces */
.game-piece.piece-red {
  color: var(--piece-color-red, #dc3545);
  border-color: color-mix(in srgb, var(--piece-color-red) 40%, transparent);
}

.game-piece.piece-black {
  color: var(--piece-color-black, #495057);
  border-color: color-mix(in srgb, var(--piece-color-black) 40%, transparent);
}

/* UI elements */
.sp-icon-piece-1 {
  color: var(--ui-piece-red, #dc3545);
}

.lp-emptyState {
  color: var(--ui-piece-black, #6c757d);
}
```

#### 4.3 UI Element Updates
- **StartPage**: Read theme for animated icon characters
- **LobbyPage**: Read theme for empty state character
- Both use `useTheme()` hook to access current theme

## Implementation Steps

### Phase 1: Core Theme System (2-3 hours)
1. Create `themeManager.js` with theme definitions
2. Create `ThemeContext.jsx` provider
3. Wrap App component with ThemeProvider
4. Update `pieceMapping.js` to check theme for SVG usage

### Phase 2: CSS Variable Integration (1-2 hours)
1. Update `game-piece.css` to use CSS variables
2. Update `startpage.css` for icon colors
3. Update `lobbypage.css` for empty state
4. Test color application

### Phase 3: Settings UI (2-3 hours)
1. Create settings button component
2. Create settings modal component
3. Add theme selection UI
4. Integrate with StartPage

### Phase 4: UI Element Integration (1-2 hours)
1. Update StartPage to use theme characters
2. Update LobbyPage empty state
3. Update GamePiece for dynamic rendering
4. Test all integration points

### Phase 5: Testing & Polish (1-2 hours)
1. Test theme persistence
2. Verify all pieces update correctly
3. Check UI element colors
4. Ensure smooth transitions

## File Changes Summary

### New Files
1. `frontend/src/utils/themeManager.js`
2. `frontend/src/contexts/ThemeContext.jsx`
3. `frontend/src/components/SettingsButton.jsx`
4. `frontend/src/components/SettingsModal.jsx`

### Modified Files
1. `frontend/src/App.jsx` - Wrap with ThemeProvider
2. `frontend/src/utils/pieceMapping.js` - Dynamic SVG check
3. `frontend/src/components/game/shared/GamePiece.jsx` - Theme integration
4. `frontend/src/pages/StartPage.jsx` - Settings button and theme
5. `frontend/src/pages/LobbyPage.jsx` - Theme for empty state
6. `frontend/src/styles/components/game/shared/game-piece.css` - CSS variables
7. `frontend/src/styles/components/startpage.css` - CSS variables
8. `frontend/src/styles/components/lobbypage.css` - CSS variables

## Storage Schema

### localStorage Keys
```javascript
{
  'liap-tui-theme': 'classic' | 'modern',  // Theme ID
}
```

## Future Extensibility

### Adding New Themes
1. Add theme definition to `themes` object
2. Include all required properties
3. Optionally add new piece assets
4. Theme automatically appears in settings

### Potential Future Themes
- **Dark Mode**: Dark backgrounds with neon pieces
- **Traditional Calligraphy**: Artistic brush-stroke characters
- **Seasonal**: Holiday-themed pieces and colors
- **High Contrast**: Accessibility-focused theme

### Advanced Features
- Custom theme creator
- Import/export themes
- Per-player theme in multiplayer
- Animated theme transitions

## Risk Mitigation

### Performance
- CSS variables update instantly
- No re-rendering of entire component tree
- Minimal localStorage usage

### Compatibility
- Fallback colors in CSS
- Theme validation on load
- Default to classic if corrupted

### User Experience
- Settings accessible from any page
- Clear preview of themes
- Instant visual feedback
- Persistent across sessions

## Success Metrics

1. **Technical**
   - Theme changes < 100ms
   - No performance degradation
   - Zero console errors

2. **User Experience**
   - Intuitive theme selection
   - Consistent application
   - Clear visual differences

3. **Maintainability**
   - Easy to add themes
   - Clean separation of concerns
   - Well-documented code

## Timeline

- **Total Estimate**: 8-12 hours
- **Priority**: Medium
- **Dependencies**: None
- **Testing**: 2 hours included

## Conclusion

This theme system provides a clean, extensible way for players to customize their visual experience while maintaining code quality and performance. The implementation focuses on simplicity and user experience, with room for future enhancements.