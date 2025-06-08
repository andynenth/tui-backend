// frontend/utils/playValidation.js

/**
 * Validates if a play is valid based on game rules
 * This mirrors the backend validation logic
 */
export function validatePlay(pieces, isFirstPlayer, requiredCount) {
  // Basic validation
  if (!pieces || pieces.length === 0) {
    return { valid: false, error: "No pieces selected" };
  }
  
  if (pieces.length > 6) {
    return { valid: false, error: "Cannot play more than 6 pieces" };
  }
  
  // First player can play 1-6 pieces
  if (isFirstPlayer) {
    if (pieces.length < 1 || pieces.length > 6) {
      return { valid: false, error: "First player must play 1-6 pieces" };
    }
  } else {
    // Other players must match the count
    if (requiredCount && pieces.length !== requiredCount) {
      return { valid: false, error: `Must play exactly ${requiredCount} pieces` };
    }
  }
  
  // Check for valid combinations
  const playType = getPlayType(pieces);
  
  if (playType === "INVALID") {
    return { valid: false, error: "Invalid combination of pieces" };
  }
  
  return { valid: true, type: playType };
}

/**
 * Determine the type of play based on pieces
 */
export function getPlayType(pieces) {
  if (pieces.length === 1) {
    return "SINGLE";
  }
  
  if (pieces.length === 2) {
    if (isPair(pieces)) {
      return "PAIR";
    }
  }
  
  if (pieces.length === 3) {
    if (isThreeOfAKind(pieces)) {
      return "THREE_OF_A_KIND";
    }
    if (isStraight(pieces)) {
      return "STRAIGHT";
    }
  }
  
  if (pieces.length === 4) {
    if (isFourOfAKind(pieces)) {
      return "FOUR_OF_A_KIND";
    }
    if (isExtendedStraight(pieces)) {
      return "EXTENDED_STRAIGHT";
    }
  }
  
  if (pieces.length === 5) {
    if (isFiveOfAKind(pieces)) {
      return "FIVE_OF_A_KIND";
    }
    if (isExtendedStraight5(pieces)) {
      return "EXTENDED_STRAIGHT_5";
    }
  }
  
  if (pieces.length === 6) {
    if (isDoubleStraight(pieces)) {
      return "DOUBLE_STRAIGHT";
    }
  }
  
  return "INVALID";
}

/**
 * Parse a piece string like "GENERAL_RED(14)" into components
 */
export function parsePiece(pieceStr) {
  const match = pieceStr.match(/^(.+?)_(RED|BLACK)\((\d+)\)$/);
  if (!match) {
    return { name: "UNKNOWN", color: "UNKNOWN", points: 0 };
  }
  
  return {
    name: match[1],
    color: match[2],
    points: parseInt(match[3])
  };
}

/**
 * Check if pieces form a valid pair
 */
function isPair(pieces) {
  if (pieces.length !== 2) return false;
  
  const p1 = parsePiece(pieces[0]);
  const p2 = parsePiece(pieces[1]);
  
  return p1.name === p2.name && p1.color === p2.color;
}

/**
 * Check if pieces form three of a kind (3 soldiers of same color)
 */
function isThreeOfAKind(pieces) {
  if (pieces.length !== 3) return false;
  
  const parsed = pieces.map(p => parsePiece(p));
  return parsed.every(p => p.name === "SOLDIER" && p.color === parsed[0].color);
}

/**
 * Check if pieces form a straight (3 consecutive pieces of same color)
 */
function isStraight(pieces) {
  if (pieces.length !== 3) return false;
  
  const parsed = pieces.map(p => parsePiece(p));
  const names = parsed.map(p => p.name).sort();
  const color = parsed[0].color;
  
  // Check if all same color
  if (!parsed.every(p => p.color === color)) return false;
  
  // Valid straight combinations
  const validStraights = [
    ["ADVISOR", "ELEPHANT", "GENERAL"],
    ["CANNON", "CHARIOT", "HORSE"]
  ];
  
  return validStraights.some(straight => 
    JSON.stringify(straight) === JSON.stringify(names)
  );
}

/**
 * Check if pieces form four of a kind (4 soldiers of same color)
 */
function isFourOfAKind(pieces) {
  if (pieces.length !== 4) return false;
  
  const parsed = pieces.map(p => parsePiece(p));
  return parsed.every(p => p.name === "SOLDIER" && p.color === parsed[0].color);
}

/**
 * Check if pieces form an extended straight (4 pieces with 1 duplicate)
 */
function isExtendedStraight(pieces) {
  if (pieces.length !== 4) return false;
  
  const parsed = pieces.map(p => parsePiece(p));
  const color = parsed[0].color;
  
  // Check if all same color
  if (!parsed.every(p => p.color === color)) return false;
  
  // Count occurrences of each piece name
  const nameCounts = {};
  parsed.forEach(p => {
    nameCounts[p.name] = (nameCounts[p.name] || 0) + 1;
  });
  
  // Must have exactly one duplicate
  const counts = Object.values(nameCounts);
  if (!counts.includes(2) || counts.filter(c => c === 2).length !== 1) {
    return false;
  }
  
  // Check if pieces belong to valid groups
  const names = Object.keys(nameCounts);
  const validGroups = [
    ["GENERAL", "ADVISOR", "ELEPHANT"],
    ["CHARIOT", "HORSE", "CANNON"]
  ];
  
  return validGroups.some(group => 
    names.every(name => group.includes(name))
  );
}

/**
 * Check if pieces form five of a kind (5 soldiers of same color)
 */
function isFiveOfAKind(pieces) {
  if (pieces.length !== 5) return false;
  
  const parsed = pieces.map(p => parsePiece(p));
  return parsed.every(p => p.name === "SOLDIER" && p.color === parsed[0].color);
}

/**
 * Check if pieces form an extended straight of 5 (5 pieces with 2 duplicates)
 */
function isExtendedStraight5(pieces) {
  if (pieces.length !== 5) return false;
  
  const parsed = pieces.map(p => parsePiece(p));
  const color = parsed[0].color;
  
  // Check if all same color
  if (!parsed.every(p => p.color === color)) return false;
  
  // Count occurrences of each piece name
  const nameCounts = {};
  parsed.forEach(p => {
    nameCounts[p.name] = (nameCounts[p.name] || 0) + 1;
  });
  
  // Must have pattern: 1, 2, 2 (one single, two pairs)
  const counts = Object.values(nameCounts).sort();
  if (JSON.stringify(counts) !== JSON.stringify([1, 2, 2])) {
    return false;
  }
  
  // Check if pieces belong to valid groups
  const names = Object.keys(nameCounts);
  const validGroups = [
    ["GENERAL", "ADVISOR", "ELEPHANT"],
    ["CHARIOT", "HORSE", "CANNON"]
  ];
  
  return validGroups.some(group => 
    names.every(name => group.includes(name))
  );
}

/**
 * Check if pieces form a double straight (2 of each: CHARIOT, HORSE, CANNON)
 */
function isDoubleStraight(pieces) {
  if (pieces.length !== 6) return false;
  
  const parsed = pieces.map(p => parsePiece(p));
  const color = parsed[0].color;
  
  // Check if all same color
  if (!parsed.every(p => p.color === color)) return false;
  
  // Count occurrences of each piece name
  const nameCounts = {};
  parsed.forEach(p => {
    nameCounts[p.name] = (nameCounts[p.name] || 0) + 1;
  });
  
  // Must have exactly 2 of each: CHARIOT, HORSE, CANNON
  const required = { "CHARIOT": 2, "HORSE": 2, "CANNON": 2 };
  
  return Object.keys(required).every(name => 
    nameCounts[name] === required[name]
  ) && Object.keys(nameCounts).length === 3;
}

/**
 * Get a user-friendly error message for play validation
 */
export function getPlayErrorMessage(pieces, isFirstPlayer, requiredCount) {
  const validation = validatePlay(pieces, isFirstPlayer, requiredCount);
  
  if (!validation.valid) {
    return validation.error;
  }
  
  return null;
}