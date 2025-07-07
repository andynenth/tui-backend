/**
 * Piece Mapping Utility
 * 
 * Maps game piece types to their Chinese character representations
 * Used throughout the UI to display pieces consistently
 */

// Piece type to Chinese character mapping
export const PIECE_CHINESE_MAP = {
  'GENERAL_RED': '将',
  'GENERAL_BLACK': '帅',
  'ADVISOR_RED': '士',
  'ADVISOR_BLACK': '士',
  'ELEPHANT_RED': '象',
  'ELEPHANT_BLACK': '相',
  'CHARIOT_RED': '车',
  'CHARIOT_BLACK': '車',
  'HORSE_RED': '马',
  'HORSE_BLACK': '馬',
  'CANNON_RED': '炮',
  'CANNON_BLACK': '砲',
  'SOLDIER_RED': '兵',
  'SOLDIER_BLACK': '卒'
};

// Simplified mapping without color suffix
export const PIECE_TYPE_MAP = {
  'GENERAL': '将/帅',
  'ADVISOR': '士',
  'ELEPHANT': '象/相',
  'CHARIOT': '车',
  'HORSE': '马',
  'CANNON': '炮',
  'SOLDIER': '兵/卒'
};

/**
 * Parse piece string from backend format
 * @param {string|Object} pieceData - Either "GENERAL_RED(14)" string or piece object
 * @returns {Object} Parsed piece object with type, color, and value
 */
export function parsePiece(pieceData) {
  // If already an object
  if (typeof pieceData === 'object' && pieceData !== null) {
    // Handle GameService format: { color, point, kind, name }
    if (pieceData.kind) {
      return {
        type: pieceData.kind,
        color: pieceData.color.toLowerCase(),
        value: pieceData.point
      };
    }
    // Already in correct format
    if (pieceData.type) {
      return pieceData;
    }
  }

  // Parse string format: "GENERAL_RED(14)"
  if (typeof pieceData === 'string') {
    const match = pieceData.match(/^([A-Z]+)_([A-Z]+)\((\d+)\)$/);
    if (match) {
      const [, type, color, value] = match;
      return {
        type,
        color: color.toLowerCase(),
        value: parseInt(value, 10)
      };
    }
  }

  // Fallback
  return {
    type: 'UNKNOWN',
    color: 'black',
    value: 0
  };
}

/**
 * Get the Chinese character display for a piece
 * @param {string|Object} pieceData - Either piece string or object
 * @returns {string} The Chinese character for the piece
 */
export function getPieceDisplay(pieceData) {
  const piece = parsePiece(pieceData);
  
  if (!piece || !piece.type) {
    return '?';
  }

  // Try full type with color first
  const fullType = `${piece.type}_${piece.color?.toUpperCase()}`;
  if (PIECE_CHINESE_MAP[fullType]) {
    return PIECE_CHINESE_MAP[fullType];
  }

  // Try just the type
  if (PIECE_CHINESE_MAP[piece.type]) {
    return PIECE_CHINESE_MAP[piece.type];
  }

  // Try simplified type map
  const baseType = piece.type.replace(/_RED|_BLACK/i, '');
  if (PIECE_TYPE_MAP[baseType]) {
    const chars = PIECE_TYPE_MAP[baseType].split('/');
    return piece.color?.toLowerCase() === 'red' ? chars[0] : chars[1] || chars[0];
  }

  // Fallback - use first character of type
  return piece.type.charAt(0).toUpperCase();
}

/**
 * Get piece color class name
 * @param {string|Object} pieceData - Either piece string or object
 * @returns {string} CSS class name for piece color
 */
export function getPieceColorClass(pieceData) {
  const piece = parsePiece(pieceData);
  if (!piece || !piece.color) {
    return 'piece-unknown';
  }
  return `piece-${piece.color.toLowerCase()}`;
}

/**
 * Format piece value for display
 * @param {string|Object} pieceData - Either piece string or object
 * @returns {string} Formatted value
 */
export function formatPieceValue(pieceData) {
  const piece = parsePiece(pieceData);
  if (piece.value === undefined || piece.value === null) {
    return '0';
  }
  return piece.value.toString();
}

// Export the mapping object for direct access if needed
export default PIECE_CHINESE_MAP;