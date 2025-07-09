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
    HORSE: 7
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
    if (piece.point !== undefined) return piece.point;
    if (piece.type && PIECE_VALUES[piece.type]) return PIECE_VALUES[piece.type];
    if (piece.kind && PIECE_VALUES[piece.kind]) return PIECE_VALUES[piece.kind];
    if (piece.name && PIECE_VALUES[piece.name]) return PIECE_VALUES[piece.name];
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
    return pieces.every(p => getPieceValue(p) === value);
}

function isStraight(pieces) {
    const names = pieces.map(p => p.name);
    const validGroups = [
        ["GENERAL", "ADVISOR", "ELEPHANT"],
        ["CHARIOT", "HORSE", "CANNON"]
    ];
    return pieces.every(p => p.color === pieces[0].color) &&
           validGroups.some(group => names.sort().join() === group.sort().join());
}

function isFourOfAKind(pieces) {
    if (pieces.length !== 4) return false;
    const value = getPieceValue(pieces[0]);
    return pieces.every(p => getPieceValue(p) === value);
}

function isExtendedStraight(pieces) {
    const color = pieces[0].color;
    const names = pieces.map(p => p.name);
    const counter = {};
    names.forEach(name => counter[name] = (counter[name] || 0) + 1);
    
    const validGroups = [
        ["GENERAL", "ADVISOR", "ELEPHANT"],
        ["CHARIOT", "HORSE", "CANNON"]
    ];
    
    return pieces.every(p => p.color === color) &&
           validGroups.some(group => 
               names.every(n => group.includes(n)) &&
               Object.values(counter).some(v => v === 2)
           );
}

function isFiveOfAKind(pieces) {
    if (pieces.length !== 5) return false;
    const value = getPieceValue(pieces[0]);
    return pieces.every(p => getPieceValue(p) === value);
}

function isExtendedStraight5(pieces) {
    const color = pieces[0].color;
    const names = pieces.map(p => p.name);
    const counter = {};
    names.forEach(name => counter[name] = (counter[name] || 0) + 1);
    
    const validGroups = [
        ["GENERAL", "ADVISOR", "ELEPHANT"],
        ["CHARIOT", "HORSE", "CANNON"]
    ];
    
    return pieces.every(p => p.color === color) &&
           validGroups.some(group => names.every(n => group.includes(n))) &&
           Object.values(counter).sort().join() === "1,2,2";
}

function isDoubleStraight(pieces) {
    if (pieces.length !== 6) return false;
    
    const color = pieces[0].color;
    const names = pieces.map(p => p.name);
    const counter = {};
    names.forEach(name => counter[name] = (counter[name] || 0) + 1);
    
    return pieces.every(p => p.color === color) &&
           Object.keys(counter).sort().join() === "CANNON,CHARIOT,HORSE" &&
           Object.values(counter).every(v => v === 2);
}

/**
 * Get the play type name for a set of pieces
 * Returns null if invalid or single piece
 */
export function getPlayType(pieces) {
    if (!pieces || pieces.length === 0) return null;
    if (pieces.length === 1) return null; // Don't show type for single piece
    
    // Check for pairs (by value)
    if (pieces.length === 2 && isPair(pieces)) {
        return "Pair";
    }
    
    // Check for three of a kind
    if (pieces.length === 3) {
        if (isThreeOfAKind(pieces)) return "Three of a Kind";
        if (isStraight(pieces)) return "Straight";
    }
    
    // Check for four of a kind
    if (pieces.length === 4) {
        if (isFourOfAKind(pieces)) return "Four of a Kind";
        if (isExtendedStraight(pieces)) return "Extended Straight";
    }
    
    // Check for five of a kind
    if (pieces.length === 5) {
        if (isFiveOfAKind(pieces)) return "Five of a Kind";
        if (isExtendedStraight5(pieces)) return "Extended Straight";
    }
    
    // Check for double straight
    if (pieces.length === 6 && isDoubleStraight(pieces)) {
        return "Double Straight";
    }
    
    return null; // Invalid combination
}