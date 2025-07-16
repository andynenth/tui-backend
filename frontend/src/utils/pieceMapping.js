/**
 * Piece Mapping Utility
 *
 * Maps game piece types to their Chinese character representations
 * Used throughout the UI to display pieces consistently
 * Now supports both font-based and SVG-based rendering
 */

// Import SVG assets for conditional rendering
import * as PieceAssets from '../assets/pieces';

// Piece type to Chinese character mapping (Traditional Chinese Chess)
export const PIECE_CHINESE_MAP = {
  GENERAL_RED: '帥',
  GENERAL_BLACK: '將',
  ADVISOR_RED: '仕',
  ADVISOR_BLACK: '士',
  ELEPHANT_RED: '相',
  ELEPHANT_BLACK: '象',
  CHARIOT_RED: '俥',
  CHARIOT_BLACK: '車',
  HORSE_RED: '傌',
  HORSE_BLACK: '馬',
  CANNON_RED: '炮',
  CANNON_BLACK: '砲',
  SOLDIER_RED: '兵',
  SOLDIER_BLACK: '卒',
};

// Simplified mapping without color suffix
export const PIECE_TYPE_MAP = {
  GENERAL: '帥/將',
  ADVISOR: '仕/士',
  ELEPHANT: '相/象',
  CHARIOT: '俥/車',
  HORSE: '傌/馬',
  CANNON: '炮/砲',
  SOLDIER: '兵/卒',
};

/**
 * Parse piece string from backend format
 * @param {string|Object} pieceData - Either "GENERAL_RED(14)" string or piece object
 * @returns {Object} Parsed piece object with kind, color, and value
 */
export function parsePiece(pieceData) {
  // If already an object
  if (typeof pieceData === 'object' && pieceData !== null) {
    // Already has kind property
    if (pieceData.kind) {
      return pieceData;
    }
  }

  // Parse string format: "GENERAL_RED(14)"
  if (typeof pieceData === 'string') {
    const match = pieceData.match(/^([A-Z]+)_([A-Z]+)\((\d+)\)$/);
    if (match) {
      const [, kind, color, value] = match;
      return {
        kind,
        color: color.toLowerCase(),
        value: parseInt(value, 10),
      };
    }
  }

  // Fallback
  return {
    kind: 'UNKNOWN',
    color: 'black',
    value: 0,
  };
}

/**
 * Get the Chinese character display for a piece
 * @param {string|Object} pieceData - Either piece string or object
 * @returns {string} The Chinese character for the piece
 */
export function getPieceDisplay(pieceData) {
  const piece = parsePiece(pieceData);

  if (!piece || !piece.kind) {
    return '?';
  }

  // Try full type with color first
  const fullType = `${piece.kind}_${piece.color?.toUpperCase()}`;
  if (PIECE_CHINESE_MAP[fullType]) {
    return PIECE_CHINESE_MAP[fullType];
  }

  // Try just the type
  if (PIECE_CHINESE_MAP[piece.kind]) {
    return PIECE_CHINESE_MAP[piece.kind];
  }

  // Try simplified type map
  const baseType = piece.kind.replace(/_RED|_BLACK/i, '');
  if (PIECE_TYPE_MAP[baseType]) {
    const chars = PIECE_TYPE_MAP[baseType].split('/');
    return piece.color?.toLowerCase() === 'red'
      ? chars[0]
      : chars[1] || chars[0];
  }

  // Fallback - use first character of type
  return piece.kind.charAt(0).toUpperCase();
}

/**
 * Get piece color class name
 * @param {string|Object} pieceData - Either piece string or object
 * @returns {string} CSS class name for piece color
 */
export function getPieceColorClass(pieceData) {
  // Handle direct color property
  if (pieceData && pieceData.color) {
    return `piece-${pieceData.color.toLowerCase()}`;
  }

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

/**
 * Get the SVG asset path for a piece
 * @deprecated Use getThemePieceSVG instead for theme-aware piece rendering
 * @param {string|Object} pieceData - Either piece string or object
 * @returns {string} The SVG asset path for the piece
 */
export function getPieceSVG(pieceData) {
  const piece = parsePiece(pieceData);

  if (!piece || !piece.kind) {
    return null;
  }

  // Create full type with color (e.g., "GENERAL_RED")
  const fullType = `${piece.kind}_${piece.color?.toUpperCase()}`;

  // Default to classic SVG assets
  return PieceAssets.getPieceAsset(fullType);
}

/**
 * Get the theme-aware SVG path for a piece
 * @param {Object} piece - Piece object with kind and color
 * @param {Object} theme - Theme object with pieceAssets
 * @returns {string} The SVG import for the piece
 */
export function getThemePieceSVG(piece, theme) {
  if (!piece || !piece.kind || !theme || !theme.pieceAssets) {
    return null;
  }

  const pieceType = `${piece.kind}_${piece.color.toUpperCase()}`;

  // Get the SVG from the theme's piece assets
  return theme.pieceAssets[pieceType] || null;
}

/**
 * Feature flag to control SVG vs font rendering
 * Set to false to use traditional font-based Chinese characters
 * Set to true to use SVG assets
 */
export const USE_SVG_PIECES = true;

// Export the mapping object for direct access if needed
export default PIECE_CHINESE_MAP;
