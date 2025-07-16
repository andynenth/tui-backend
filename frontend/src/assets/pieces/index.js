/**
 * SVG Piece Assets Index
 * 
 * This file provides easy imports for all xiangqi piece SVGs.
 * SVG files are named to match the constants in backend/engine/constants.py
 * 
 * Usage:
 *   import { GENERAL_RED, CHARIOT_BLACK } from './assets/pieces';
 *   import * as PieceAssets from './assets/pieces';
 */

// Import all SVG files
import GENERAL_RED from './GENERAL_RED.svg';
import GENERAL_BLACK from './GENERAL_BLACK.svg';
import ADVISOR_RED from './ADVISOR_RED.svg';
import ADVISOR_BLACK from './ADVISOR_BLACK.svg';
import ELEPHANT_RED from './ELEPHANT_RED.svg';
import ELEPHANT_BLACK from './ELEPHANT_BLACK.svg';
import CHARIOT_RED from './CHARIOT_RED.svg';
import CHARIOT_BLACK from './CHARIOT_BLACK.svg';
import HORSE_RED from './HORSE_RED.svg';
import HORSE_BLACK from './HORSE_BLACK.svg';
import CANNON_RED from './CANNON_RED.svg';
import CANNON_BLACK from './CANNON_BLACK.svg';
import SOLDIER_RED from './SOLDIER_RED.svg';
import SOLDIER_BLACK from './SOLDIER_BLACK.svg';

// Export individual pieces
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