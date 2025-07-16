/**
 * SVG Piece Assets Index
 *
 * This file provides imports for xiangqi piece SVGs.
 * It maintains backward compatibility while supporting themed pieces.
 *
 * Usage:
 *   import { GENERAL_RED, CHARIOT_BLACK } from './assets/pieces';
 *   import * as PieceAssets from './assets/pieces';
 *   import ClassicPieces from './assets/pieces/classic';
 *   import ModernPieces from './assets/pieces/modern';
 */

// For backward compatibility, import and re-export classic pieces
import {
  GENERAL_RED,
  GENERAL_BLACK,
  ADVISOR_RED,
  ADVISOR_BLACK,
  ELEPHANT_RED,
  ELEPHANT_BLACK,
  CHARIOT_RED,
  CHARIOT_BLACK,
  HORSE_RED,
  HORSE_BLACK,
  CANNON_RED,
  CANNON_BLACK,
  SOLDIER_RED,
  SOLDIER_BLACK,
} from './classic';

// Export individual pieces for backward compatibility
export {
  GENERAL_RED,
  GENERAL_BLACK,
  ADVISOR_RED,
  ADVISOR_BLACK,
  ELEPHANT_RED,
  ELEPHANT_BLACK,
  CHARIOT_RED,
  CHARIOT_BLACK,
  HORSE_RED,
  HORSE_BLACK,
  CANNON_RED,
  CANNON_BLACK,
  SOLDIER_RED,
  SOLDIER_BLACK,
};

// Export as object for dynamic access
export const PIECE_ASSETS = {
  GENERAL_RED,
  GENERAL_BLACK,
  ADVISOR_RED,
  ADVISOR_BLACK,
  ELEPHANT_RED,
  ELEPHANT_BLACK,
  CHARIOT_RED,
  CHARIOT_BLACK,
  HORSE_RED,
  HORSE_BLACK,
  CANNON_RED,
  CANNON_BLACK,
  SOLDIER_RED,
  SOLDIER_BLACK,
};

// Mapping from backend constants to SVG assets
export const getPieceAsset = (pieceType) => {
  return PIECE_ASSETS[pieceType] || null;
};

// Default export
export default PIECE_ASSETS;
