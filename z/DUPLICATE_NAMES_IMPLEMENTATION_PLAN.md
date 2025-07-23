# Duplicate Guest Player Names Implementation Plan

## Overview

This plan addresses handling duplicate player names by assigning random avatar colors to ALL players, allowing names to be duplicated while maintaining visual distinction. Names will be truncated to 8 characters on display with full names shown on hover.

## Current State Analysis (Validated Against Code)

### Backend
1. **Player Model** (`backend/engine/player.py`):
   - Simple constructor: `def __init__(self, name, is_bot=False)`
   - No color or ID system exists
   - Only tracks: name, hand, score, is_bot, connection status

2. **Room Join Logic** (`backend/engine/room.py` lines 464-467):
   - Prevents duplicate names WITHIN a room
   - Raises `ValueError` if name already exists in room
   - No global name uniqueness check

3. **Room Manager** (`backend/engine/room_manager.py`):
   - No player tracking beyond room scope
   - Room IDs are 6-character hex strings

### Frontend
1. **Name Validation** (`frontend/src/contexts/AppContext.jsx` lines 107-112):
   - Length: 2-20 characters
   - Trimmed before validation

2. **Name Display** (`frontend/src/pages/RoomPage.jsx` line 228):
   - Full name displayed: `<div className="rp-playerName">{playerName}</div>`
   - CSS truncation exists: `text-overflow: ellipsis` (roompage.css line 294)

3. **Avatar System** (`frontend/src/components/game/shared/PlayerAvatar.jsx`):
   - Currently only has size variants and yellow theme
   - No color assignment system

## Implementation Tasks

### Phase 1: Backend - Add Avatar Color System

#### Task 1.1: Update Player Model
**File**: `backend/engine/player.py`

**Add after line 5**:
```python
import random
```

**Modify `__init__` method (lines 5-18)**:
```python
def __init__(self, name, is_bot=False):
    self.name = name
    self.hand = []
    self.score = 0
    self.declared = 0
    self.captured_piles = 0
    self.is_bot = is_bot
    self.zero_declares_in_a_row = 0
    
    # Add avatar color assignment
    self.avatar_color = self._assign_avatar_color()
    
    # ... rest of existing fields
```

**Add new method after `__init__`**:
```python
def _assign_avatar_color(self):
    """Assign a random avatar color to human players"""
    if self.is_bot:
        return None  # Bots don't get colors
    
    colors = ["blue", "purple", "orange", "red", "green", "teal", "pink", "yellow"]
    return random.choice(colors)
```

#### Task 1.2: Include Color in Room Data
**File**: `backend/engine/room.py`

**Modify `summary` method's `slot_info` function (lines 378-393)**:
```python
def slot_info(player: Optional[Player], slot_index: int):
    if player is None:
        return None
    return {
        "name": player.name,
        "is_bot": player.is_bot,
        "is_host": slot_index == 0,
        "avatar_color": getattr(player, 'avatar_color', None)  # Add this line
    }
```

#### Task 1.3: Remove Duplicate Name Check
**File**: `backend/engine/room.py`

**Comment out lines 464-467 in `join_room` method**:
```python
# Allow duplicate names - players distinguished by color
# for i, player in enumerate(self.players):
#     if player and player.name == player_name and not player.is_bot:
#         raise ValueError(f"Player '{player_name}' is already in this room.")
```

### Phase 2: Frontend - Implement Color System

#### Task 2.1: Add Color Palette CSS
**File**: Create new `frontend/src/styles/components/game/shared/player-colors.css`

```css
/* Player avatar color variants */
.player-avatar--color-blue {
  background: linear-gradient(145deg, #EBF5FF 0%, #DBEAFE 100%);
  border-color: #3B82F6;
  color: #1E40AF;
}

.player-avatar--color-purple {
  background: linear-gradient(145deg, #F3E8FF 0%, #E9D5FF 100%);
  border-color: #8B5CF6;
  color: #5B21B6;
}

.player-avatar--color-orange {
  background: linear-gradient(145deg, #FFF7ED 0%, #FED7AA 100%);
  border-color: #F97316;
  color: #C2410C;
}

.player-avatar--color-red {
  background: linear-gradient(145deg, #FEF2F2 0%, #FECACA 100%);
  border-color: #EF4444;
  color: #B91C1C;
}

.player-avatar--color-green {
  background: linear-gradient(145deg, #F0FDF4 0%, #D1FAE5 100%);
  border-color: #10B981;
  color: #047857;
}

.player-avatar--color-teal {
  background: linear-gradient(145deg, #F0FDFA 0%, #CCFBF1 100%);
  border-color: #14B8A6;
  color: #0F766E;
}

.player-avatar--color-pink {
  background: linear-gradient(145deg, #FDF2F8 0%, #FCE7F3 100%);
  border-color: #EC4899;
  color: #BE185D;
}

.player-avatar--color-yellow {
  background: linear-gradient(145deg, #FFFBEB 0%, #FEF3C7 100%);
  border-color: #F59E0B;
  color: #B45309;
}
```

#### Task 2.2: Import Color CSS
**File**: `frontend/main.js`

**Add after line 25** (with other CSS imports):
```javascript
import './src/styles/components/game/shared/player-colors.css';
```

#### Task 2.3: Update PlayerAvatar Component
**File**: `frontend/src/components/game/shared/PlayerAvatar.jsx`

**Add to props (line 24-33)**:
```javascript
const PlayerAvatar = ({
  name,
  isBot = false,
  isThinking = false,
  className = '',
  size = 'medium',
  theme = 'default',
  isDisconnected = false,
  showAIBadge = false,
  avatarColor = null,  // Add this prop
}) => {
```

**Update PropTypes (line 80-89)**:
```javascript
PlayerAvatar.propTypes = {
  name: PropTypes.string.isRequired,
  isBot: PropTypes.bool,
  isThinking: PropTypes.bool,
  className: PropTypes.string,
  size: PropTypes.oneOf(['mini', 'small', 'medium', 'large']),
  theme: PropTypes.oneOf(['default', 'yellow']),
  isDisconnected: PropTypes.bool,
  showAIBadge: PropTypes.bool,
  avatarColor: PropTypes.string,  // Add this
};
```

**Add color class logic after line 51**:
```javascript
// Get color class
const getColorClass = () => {
  if (!isBot && avatarColor) {
    return `player-avatar--color-${avatarColor}`;
  }
  return '';
};
```

**Update bot avatar div (line 58)**:
```javascript
className={`player-avatar player-avatar--bot ${getSizeClass()} ${getThemeClass()} ${getColorClass()} ${isThinking ? 'thinking' : ''} ${isDisconnected ? 'disconnected' : ''} ${className}`}
```

**Update human avatar div (line 71)**:
```javascript
className={`player-avatar ${getSizeClass()} ${getThemeClass()} ${getColorClass()} ${isDisconnected ? 'disconnected' : ''} ${className}`}
```

### Phase 3: Name Truncation Enhancement

#### Task 3.1: Create Name Display Component
**File**: Create `frontend/src/components/shared/TruncatedName.jsx`

```jsx
import React from 'react';
import PropTypes from 'prop-types';

const TruncatedName = ({ name, maxLength = 8, className = '' }) => {
  const displayName = name.length > maxLength
    ? name.substring(0, maxLength - 1) + '…'
    : name;

  return (
    <span className={`truncated-name ${className}`} title={name}>
      {displayName}
    </span>
  );
};

TruncatedName.propTypes = {
  name: PropTypes.string.isRequired,
  maxLength: PropTypes.number,
  className: PropTypes.string,
};

export default TruncatedName;
```

#### Task 3.2: Update RoomPage to Use Avatar Colors
**File**: `frontend/src/pages/RoomPage.jsx`

**Import TruncatedName (add after line 8)**:
```javascript
import TruncatedName from '../components/shared/TruncatedName';
```

**Update PlayerAvatar usage (lines 221-227)**:
```javascript
{!isEmpty && (
  <PlayerAvatar
    name={playerName}
    isBot={isBot}
    size="medium"
    avatarColor={player?.avatar_color}  // Add this
  />
)}
```

**Replace player name display (line 228)**:
```javascript
<TruncatedName name={playerName} className="rp-playerName" />
```

### Phase 4: Update WebSocket Events

#### Task 4.1: Include Color in Join Room Response
**File**: `backend/api/routes/ws.py`

**The room_update broadcast already includes full player data via `room.summary()`, so colors will be automatically included**

### Phase 5: Testing & Edge Cases

#### Task 5.1: Create Test Script
**File**: Create `backend/tests/test_duplicate_names.py`

```python
import pytest
from engine.room import Room
from engine.player import Player

def test_duplicate_names_allowed():
    """Test that duplicate names are allowed in a room"""
    room = Room("TEST123", "Host")
    
    # Should not raise error anymore
    room.join_room("John")
    room.join_room("John")  # Second John should be allowed
    
    # Check both players exist
    johns = [p for p in room.players if p and p.name == "John"]
    assert len(johns) == 2

def test_avatar_colors_assigned():
    """Test that avatar colors are assigned to human players"""
    player = Player("TestPlayer", is_bot=False)
    assert player.avatar_color is not None
    assert player.avatar_color in ["blue", "purple", "orange", "red", "green", "teal", "pink", "yellow"]

def test_bots_no_color():
    """Test that bots don't get avatar colors"""
    bot = Player("Bot 1", is_bot=True)
    assert bot.avatar_color is None

def test_room_summary_includes_colors():
    """Test that room summary includes avatar colors"""
    room = Room("TEST123", "Host")
    room.join_room("Player2")
    
    summary = room.summary()
    for player_data in summary["players"]:
        if player_data and not player_data["is_bot"]:
            assert "avatar_color" in player_data
```

## Rollback Plan

If issues arise:

1. **Backend**: 
   - Uncomment duplicate name check in `room.py` lines 464-467
   - Remove `avatar_color` from Player `__init__`
   - Remove `avatar_color` from room summary

2. **Frontend**:
   - Remove `avatarColor` prop from PlayerAvatar
   - Remove color CSS file import
   - Revert to simple name display

## Success Criteria

1. ✅ Multiple players can join with same name
2. ✅ Each player gets a random color from palette
3. ✅ Colors persist throughout game session
4. ✅ Names truncated to 8 characters with ellipsis
5. ✅ Full names visible on hover
6. ✅ Bots remain visually distinct (no colors)