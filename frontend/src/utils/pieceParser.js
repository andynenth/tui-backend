/**
 * Piece Parser Utility
 * 
 * Parses piece string representations from the backend into proper objects
 * Backend sends pieces as strings like "ELEPHANT_BLACK(9)"
 * This converts them to objects like {kind: "ELEPHANT", color: "BLACK", value: 9}
 */

/**
 * Parse a single piece string into an object
 * @param {string} pieceStr - String like "ELEPHANT_BLACK(9)"
 * @returns {Object} Parsed piece object with kind, color, and value
 */
export function parsePieceString(pieceStr) {
  if (!pieceStr || typeof pieceStr !== 'string') {
    return null;
  }
  
  // Match pattern: PIECE_COLOR(value)
  const match = pieceStr.match(/^([A-Z]+)_(RED|BLACK)\((\d+)\)$/);
  if (!match) {
    console.warn('[parsePieceString] Invalid piece format:', pieceStr);
    return null;
  }
  
  const [, kind, color, valueStr] = match;
  return {
    kind,
    color: color.toLowerCase(), // Convert to lowercase to match frontend expectations
    value: parseInt(valueStr, 10),
    type: kind // Some components use 'type' instead of 'kind'
  };
}

/**
 * Parse an array of piece strings
 * @param {Array} pieces - Array of piece strings or already parsed objects
 * @returns {Array} Array of parsed piece objects
 */
export function parsePieces(pieces) {
  if (!Array.isArray(pieces)) {
    return [];
  }
  
  return pieces.map(piece => {
    // If already an object with required properties, return as-is
    if (typeof piece === 'object' && piece !== null && 
        (piece.kind || piece.type) && piece.color && piece.value !== undefined) {
      return piece;
    }
    
    // If it's a string, parse it
    if (typeof piece === 'string') {
      return parsePieceString(piece);
    }
    
    return null;
  }).filter(piece => piece !== null);
}

/**
 * Parse turn play data to ensure pieces are objects
 * @param {Object} playData - Turn play data from backend
 * @returns {Object} Play data with parsed pieces
 */
export function parseTurnPlay(playData) {
  if (!playData || typeof playData !== 'object') {
    return playData;
  }
  
  // Create a copy to avoid mutating the original
  const parsed = { ...playData };
  
  // Parse pieces if they exist
  if (parsed.pieces) {
    parsed.pieces = parsePieces(parsed.pieces);
  }
  
  // Also check for cards property (backward compatibility)
  if (parsed.cards) {
    parsed.cards = parsePieces(parsed.cards);
  }
  
  return parsed;
}