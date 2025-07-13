/**
 * Play Type Matching Utilities
 * 
 * Determines if a player's play matches the starter's declared play type
 * Used for selective piece reveal animations
 */

import { getPlayType } from './gameValidation';

/**
 * Checks if a player's pieces match the starter's play type
 * 
 * @param {Array} playerPieces - The pieces played by a player
 * @param {string} starterPlayType - The play type declared by the starter
 * @returns {boolean} - True if the play types match, false otherwise
 */
export function doesPlayMatchStarterType(playerPieces, starterPlayType) {
  // Handle edge cases
  if (!playerPieces || !starterPlayType) {
    return false;
  }
  
  // Get the play type of the player's pieces
  const playerPlayType = getPlayType(playerPieces);
  
  // Handle invalid or unknown play types
  if (!playerPlayType || playerPlayType === 'INVALID' || playerPlayType === 'UNKNOWN') {
    return false;
  }
  
  // Special case: SINGLE always matches (any single piece is valid)
  if (starterPlayType === 'SINGLE' && playerPieces.length === 1) {
    return true;
  }
  
  // Compare play types
  return playerPlayType === starterPlayType;
}

/**
 * Determines which pieces should be revealed based on play type matching
 * 
 * @param {Object} playerPieces - Object mapping player names to their pieces
 * @param {string} starterPlayType - The play type declared by the starter
 * @param {string} starterName - Name of the player who started this turn
 * @returns {Set} - Set of piece IDs that should be revealed
 */
export function determinePiecesToReveal(playerPieces, starterPlayType, starterName) {
  const piecesToReveal = new Set();
  
  if (!playerPieces || !starterPlayType) {
    return piecesToReveal;
  }
  
  Object.entries(playerPieces).forEach(([playerName, pieces]) => {
    if (!pieces || pieces.length === 0) {
      return;
    }
    
    // Always reveal starter's pieces
    if (playerName === starterName) {
      pieces.forEach((_, idx) => {
        piecesToReveal.add(`${playerName}-${idx}`);
      });
      return;
    }
    
    // Check if player's play matches starter's type
    if (doesPlayMatchStarterType(pieces, starterPlayType)) {
      pieces.forEach((_, idx) => {
        piecesToReveal.add(`${playerName}-${idx}`);
      });
    }
  });
  
  return piecesToReveal;
}

/**
 * Calculates animation delay for staggered reveal effect
 * 
 * @param {string} playerName - Name of the player
 * @param {Array} players - Array of all players in order
 * @param {number} baseDelay - Base delay in milliseconds (default: 0)
 * @param {number} staggerDelay - Delay between players in milliseconds (default: 100)
 * @returns {number} - Animation delay in milliseconds
 */
export function calculateRevealDelay(playerName, players, baseDelay = 0, staggerDelay = 100) {
  const playerIndex = players.findIndex(p => p.name === playerName);
  if (playerIndex === -1) {
    return baseDelay;
  }
  
  return baseDelay + (playerIndex * staggerDelay);
}

/**
 * Gets a display message for why pieces weren't revealed
 * 
 * @param {Array} playerPieces - The pieces that weren't revealed
 * @param {string} starterPlayType - The required play type
 * @returns {string} - User-friendly message
 */
export function getNonMatchMessage(playerPieces, starterPlayType) {
  const playerPlayType = getPlayType(playerPieces);
  
  if (!playerPlayType || playerPlayType === 'INVALID') {
    return 'Invalid combination';
  }
  
  if (playerPlayType === 'UNKNOWN') {
    return 'Unknown play type';
  }
  
  return `${playerPlayType} doesn't match ${starterPlayType}`;
}