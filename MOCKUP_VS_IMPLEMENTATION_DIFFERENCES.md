# Mockup vs Implementation Differences

## Key Visual Differences Found

### 1. StartPage Issues

**Mockup Features Missing:**
- **Game Icon with rotating pieces**: The mockup has a yellow circle with Chinese characters and two rotating smaller pieces
- **Floating background pieces**: The mockup has subtle floating game pieces (🎲, ♠️, etc.) in the background
- **Primary button color**: Mockup uses yellow/orange gradient, but implementation uses blue
- **Loading spinner**: Not implemented in the React component
- **"Continue as previous player" button**: Secondary button for returning players

### 2. RoomPage Issues

**Mockup Features Missing:**
- **Player badges placement**: Should have an empty badges div even when no badges
- **Control button styling**: Start button should be green, not the current color
- **Room status text**: Should show different messages based on player count
- **Seat numbering**: Missing "Seat 1", "Seat 2" labels above player cards

### 3. LobbyPage Issues

**Mockup Features Missing:**
- **Refresh button animation**: Should show ✓ checkmark briefly after refresh
- **Last updated timer**: Should show "Xs ago" or "Xm ago"
- **Room card hover effects**: More pronounced shadow and border color change
- **Empty state styling**: When no rooms available

## CSS Variables Not Matching

The mockups use specific gradients and colors that aren't properly defined in the CSS:

1. **Button gradients**: 
   - Primary (yellow): `linear-gradient(135deg, #FFC107 0%, #FF9800 100%)`
   - Success (green): `linear-gradient(135deg, #28A745 0%, #20C997 100%)`

2. **Background textures**: More subtle paper texture overlay

3. **Shadow effects**: Mockups have more layered shadows

## Fixes Needed

### 1. Update StartPage.jsx
- Add floating pieces background
- Implement the game icon with rotating pieces
- Add continue as previous player functionality
- Fix primary button color to yellow/orange

### 2. Update RoomPage.jsx  
- Add seat numbers above player cards
- Fix start button to use green gradient
- Ensure player badges div is always present

### 3. Update LobbyPage.jsx
- Implement refresh animation feedback
- Add last updated timer functionality
- Enhance hover effects on room cards

### 4. Update CSS files
- Add missing gradients to theme.css
- Fix button color classes
- Add animation keyframes for floating and rotating elements