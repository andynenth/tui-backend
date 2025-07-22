// ===== FRONTEND VALIDATION =====
// frontend/src/utils/gameValidation.js

// Piece values for validation
const PIECE_VALUES = {
  GENERAL: 14,
  ADVISOR: 13,
  SOLDIER: 11,
  ELEPHANT: 10,
  CHARIOT: 9,
  CANNON: 8,
  HORSE: 7,
};

/**
 * Validates if a play is a valid combination
 */
export function isValidPlay(pieces) {
  if (!pieces || pieces.length === 0 || pieces.length > 6) return false;

  if (pieces.length === 1) return true; // SINGLE

  if (pieces.length === 2) {
    return isPair(pieces);
  }

  if (pieces.length === 3) {
    return isThreeOfAKind(pieces) || isStraight(pieces);
  }

  if (pieces.length === 4) {
    return isFourOfAKind(pieces) || isExtendedStraight(pieces);
  }

  if (pieces.length === 5) {
    return isFiveOfAKind(pieces) || isExtendedStraight5(pieces);
  }

  if (pieces.length === 6) {
    return isDoubleStraight(pieces);
  }

  return false;
}

/**
 * Get the value of a piece
 */
function getPieceValue(piece) {
  // Handle different piece formats
  if (piece.value !== undefined) return piece.value;
  if (piece.kind && PIECE_VALUES[piece.kind]) return PIECE_VALUES[piece.kind];
  return 0;
}

/**
 * Check if pieces form a pair (same value)
 */
function isPair(pieces) {
  if (pieces.length !== 2) return false;
  return getPieceValue(pieces[0]) === getPieceValue(pieces[1]);
}

function isThreeOfAKind(pieces) {
  if (pieces.length !== 3) return false;
  const value = getPieceValue(pieces[0]);
  return pieces.every((p) => getPieceValue(p) === value);
}

function isStraight(pieces) {
  const names = pieces.map((p) => p.kind);
  const validGroups = [
    ['GENERAL', 'ADVISOR', 'ELEPHANT'],
    ['CHARIOT', 'HORSE', 'CANNON'],
  ];
  return (
    pieces.every((p) => p.color === pieces[0].color) &&
    validGroups.some((group) => names.sort().join() === group.sort().join())
  );
}

function isFourOfAKind(pieces) {
  if (pieces.length !== 4) return false;
  const value = getPieceValue(pieces[0]);
  const allSameValue = pieces.every((p) => getPieceValue(p) === value);
  console.log('[isFourOfAKind] Check:', {
    firstPieceValue: value,
    allPieceValues: pieces.map((p) => getPieceValue(p)),
    result: allSameValue,
  });
  return allSameValue;
}

function isExtendedStraight(pieces) {
  const color = pieces[0].color;
  const names = pieces.map((p) => p.kind);
  const counter = {};
  names.forEach((name) => (counter[name] = (counter[name] || 0) + 1));

  const validGroups = [
    ['GENERAL', 'ADVISOR', 'ELEPHANT'],
    ['CHARIOT', 'HORSE', 'CANNON'],
  ];

  return (
    pieces.every((p) => p.color === color) &&
    validGroups.some(
      (group) =>
        names.every((n) => group.includes(n)) &&
        Object.keys(counter).length === 3 &&
        Object.values(counter).sort().join() === '1,1,2'
    )
  );
}

function isFiveOfAKind(pieces) {
  if (pieces.length !== 5) return false;
  const value = getPieceValue(pieces[0]);
  return pieces.every((p) => getPieceValue(p) === value);
}

function isExtendedStraight5(pieces) {
  const color = pieces[0].color;
  const names = pieces.map((p) => p.kind);
  const counter = {};
  names.forEach((name) => (counter[name] = (counter[name] || 0) + 1));

  const validGroups = [
    ['GENERAL', 'ADVISOR', 'ELEPHANT'],
    ['CHARIOT', 'HORSE', 'CANNON'],
  ];

  return (
    pieces.every((p) => p.color === color) &&
    validGroups.some((group) => names.every((n) => group.includes(n))) &&
    Object.values(counter).sort().join() === '1,2,2'
  );
}

function isDoubleStraight(pieces) {
  if (pieces.length !== 6) return false;

  const color = pieces[0].color;
  const names = pieces.map((p) => p.kind);
  const counter = {};
  names.forEach((name) => (counter[name] = (counter[name] || 0) + 1));

  return (
    pieces.every((p) => p.color === color) &&
    Object.keys(counter).sort().join() === 'CANNON,CHARIOT,HORSE' &&
    Object.values(counter).every((v) => v === 2)
  );
}

/**
 * Get the play type name for a set of pieces
 * Returns null if invalid or single piece
 */
export function getPlayType(pieces) {
  console.log('[getPlayType] Analyzing pieces:', {
    count: pieces?.length,
    pieces: JSON.stringify(
      pieces?.map((p) => ({
        kind: p.kind || p.type,
        color: p.color,
        value: p.value,
      }))
    ),
  });

  if (!pieces || pieces.length === 0) return null;
  if (pieces.length === 1) return 'SINGLE';

  // Check for pairs (by value)
  if (pieces.length === 2 && isPair(pieces)) {
    return 'PAIR';
  }

  // Check for three of a kind
  if (pieces.length === 3) {
    if (isThreeOfAKind(pieces)) return 'THREE_OF_A_KIND';
    if (isStraight(pieces)) return 'STRAIGHT';
  }

  // Check for four of a kind
  if (pieces.length === 4) {
    if (isFourOfAKind(pieces)) {
      console.log('[getPlayType] Detected FOUR_OF_A_KIND');
      return 'FOUR_OF_A_KIND';
    }
    if (isExtendedStraight(pieces)) {
      console.log('[getPlayType] Detected EXTENDED_STRAIGHT');
      return 'EXTENDED_STRAIGHT';
    }
  }

  // Check for five of a kind
  if (pieces.length === 5) {
    if (isFiveOfAKind(pieces)) return 'FIVE_OF_A_KIND';
    if (isExtendedStraight5(pieces)) return 'EXTENDED_STRAIGHT_5';
  }

  // Check for double straight
  if (pieces.length === 6 && isDoubleStraight(pieces)) {
    return 'DOUBLE_STRAIGHT';
  }

  return null; // Invalid combination
}
