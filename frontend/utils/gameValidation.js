// ===== FRONTEND VALIDATION =====
// frontend/utils/gameValidation.js

//import { PIECE_POINTS } from './constants.js';

/**
 * Validates if a play is a valid combination
 */
export function isValidPlay(pieces) {
    if (!pieces || pieces.length === 0 || pieces.length > 6) return false;
    
    if (pieces.length === 1) return true; // SINGLE
    
    if (pieces.length === 2) {
        return pieces[0].name === pieces[1].name && pieces[0].color === pieces[1].color; // PAIR
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

function isThreeOfAKind(pieces) {
    return pieces.every(p => p.name === "SOLDIER" && p.color === pieces[0].color);
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
    return pieces.every(p => p.name === "SOLDIER" && p.color === pieces[0].color);
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
    return pieces.every(p => p.name === "SOLDIER" && p.color === pieces[0].color);
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