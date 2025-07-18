// Medieval theme piece assets
import GENERAL_RED from './GENERAL_RED.svg';
import GENERAL_BLACK from './GENERAL_BLACK.svg';
import ADVISOR_RED from './ADVISOR_RED.svg';
import ADVISOR_BLACK from './ADVISOR_BLACK.svg';
import ELEPHANT_RED from './ELEPHANT_RED.svg';
import ELEPHANT_BLACK from './ELEPHANT_BLACK.svg';
import HORSE_RED from './HORSE_RED.svg';
import HORSE_BLACK from './HORSE_BLACK.svg';
import CHARIOT_RED from './CHARIOT_RED.svg';
import CHARIOT_BLACK from './CHARIOT_BLACK.svg';
import CANNON_RED from './CANNON_RED.svg';
import CANNON_BLACK from './CANNON_BLACK.svg';
import SOLDIER_RED from './SOLDIER_RED.svg';
import SOLDIER_BLACK from './SOLDIER_BLACK.svg';

// Map piece names to their assets
const medievalPieces = {
  GENERAL_RED,
  GENERAL_BLACK,
  ADVISOR_RED,
  ADVISOR_BLACK,
  ELEPHANT_RED,
  ELEPHANT_BLACK,
  HORSE_RED,
  HORSE_BLACK,
  CHARIOT_RED,
  CHARIOT_BLACK,
  CANNON_RED,
  CANNON_BLACK,
  SOLDIER_RED,
  SOLDIER_BLACK,
};

// Export all pieces
export {
  GENERAL_RED,
  GENERAL_BLACK,
  ADVISOR_RED,
  ADVISOR_BLACK,
  ELEPHANT_RED,
  ELEPHANT_BLACK,
  HORSE_RED,
  HORSE_BLACK,
  CHARIOT_RED,
  CHARIOT_BLACK,
  CANNON_RED,
  CANNON_BLACK,
  SOLDIER_RED,
  SOLDIER_BLACK,
};

// Function to get piece asset by name
export const getPieceAsset = (pieceName) => {
  return medievalPieces[pieceName] || null;
};

export default medievalPieces;
