# Play History Feature

## Overview
The Play History feature provides admin-only access to comprehensive game history for analysis and debugging. It displays detailed information about game rounds, player decisions, and scoring.

## Access
- **URL Pattern**: `http://localhost:5050/history/{roomId}`
- **Access Type**: Admin-only (direct URL access)
- **Authentication**: None required (future versions may add authentication)
- **Navigation**: No user-facing links (admins must know/bookmark the URL)

## Features

### 1. Game Header
- Room ID and current round display
- Round selector dropdown for navigation
- Total turns and round winner information

### 2. Player Overview
- 4-player grid layout showing:
  - Player names and types (human/bot)
  - Declared pile count
  - Actual captured pieces
  - Round score with color coding (green for positive, red for negative)
  - Starter player highlighted with gold ring

### 3. Declaration Phase
- Shows all player declarations
- Displays initial hand for each player
- Color-coded pieces (red/black)

### 4. Turn Timeline
- Turn-by-turn play history
- For each turn:
  - Turn number and special indicators (e.g., "Triple Play Showdown")
  - Winner announcement
  - Play cards for all 4 players showing:
    - Hand before play
    - Pieces played
    - Captured count
    - Winner highlight

### 5. Round Summary
- Final scores sorted by ranking
- Score breakdown: declared, captured, base score, multiplier, final score
- Winner highlighted
- Bonus display (if any)

## Technical Implementation

### Architecture
```
PlayHistoryPage/
├── PlayHistoryPage.jsx     # Main component with state management
├── index.jsx               # Export wrapper
└── README.md              # This documentation
```

### Data Flow
1. **Route Parameter**: Extract `roomId` from URL
2. **API Call**: Fetch data from `/api/rooms/{roomId}/play-history`
3. **Data Validation**: Validate response structure
4. **Immutability**: Deep freeze data to prevent mutations
5. **State Management**: Track selected round locally

### Key Components
- **usePlayHistory Hook**: Manages data fetching, loading, and error states
- **playHistoryService**: API service with error handling
- **Validation**: Type guards for data integrity
- **Immutability Helpers**: Ensure data cannot be mutated

### Error Handling
- Network errors with retry capability
- 404 for non-existent rooms
- Invalid data structure detection
- User-friendly error messages

## Usage Examples

### Accessing Game History
```
http://localhost:5050/history/23BEBA
```

### Switching Rounds
Use the round selector dropdown in the header to navigate between rounds.

### Analyzing Player Performance
- Compare declared vs captured pieces
- Review turn-by-turn decisions
- Identify winning strategies

## Development

### Running Tests
```bash
# Run all tests
npm test

# Run specific test file
npm test PlayHistoryPage.test.jsx
npm test usePlayHistory.test.ts
npm test playHistoryService.test.ts
```

### Mock Data
For development without backend:
```javascript
import { mockPlayHistory } from '../../mocks/playHistoryMock';
// Use mockPlayHistory instead of API call
```

### Styling
- Uses Tailwind CSS exclusively
- Dark theme with game-specific colors
- Responsive grid layouts
- No custom CSS files needed

## Future Enhancements
1. **Authentication**: Add admin login requirement
2. **Export**: Allow data export to CSV/JSON
3. **Analytics**: Add graphs and statistics
4. **Filters**: Filter by player, date range, etc.
5. **Mobile**: Optimize for mobile admin access
6. **Real-time**: WebSocket for live game monitoring

## Troubleshooting

### Page Shows "Loading..." Forever
- Check if backend server is running
- Verify the room ID exists
- Check browser console for errors

### "Game history not found"
- Room ID doesn't exist
- Game may have been deleted
- Check URL for typos

### Data Not Updating
- Refresh the page (data is fetched once on load)
- Check if game is still in progress

## API Reference

### GET /api/rooms/{roomId}/play-history
Returns complete game history including:
- Room metadata
- Player information
- All rounds with:
  - Declarations
  - Turns with plays
  - Scoring details
  - Winners and bonuses

See `backend/api/docs/PLAY_HISTORY_API.md` for complete API documentation.