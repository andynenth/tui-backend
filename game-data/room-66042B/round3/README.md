# Round 3 Game Data - Room 66042B

## Overview
This directory contains game data extracted from Castellan game room 66042B, specifically focusing on Round 3 for AI analysis.

## Game Details
- **Room ID**: 66042B
- **Date Extracted**: August 28, 2025
- **Round Number**: 3 (out of 3 total rounds)
- **Players**:
  - Alexanderium (Human)
  - Bot 2 (AI)
  - Bot 3 (AI)
  - Bot 4 (AI)

## Files

### full_api_response.json
Complete API response from `/api/rooms/66042B/play-history?rounds=3`
- Contains all rounds data (but filtered to round 3)
- Includes metadata about the game session
- File size: ~228KB

### round3_extracted.json
Extracted and cleaned data for Round 3 only
- Contains only Round 3 turn history
- Includes player information
- Optimized for AI analysis
- File size: ~27KB

## Round 3 Summary
- **Starter**: Alexanderium
- **Start Time**: 2025-08-28T07:08:12.097077
- **Total Turns**: 3
- **Notable**: This was the final round of the game

## Usage
Use `round3_extracted.json` for:
- AI move analysis
- Strategy evaluation
- Bot decision pattern analysis
- Game flow visualization

## Data Source
Retrieved from: https://castellan.andynenth.dev/api/rooms/66042B/play-history
