// frontend/game/validators/PlayValidator.js

/**
 * Client-side play validation
 * Provides fast feedback without server round-trip
 * 
 * Note: This mirrors backend validation logic
 * Server has final authority on play validity
 */
export class PlayValidator {
  constructor() {
    // Play type definitions
    this.PLAY_TYPES = {
      SINGLE: 'SINGLE',
      PAIR: 'PAIR',
      THREE_OF_A_KIND: 'THREE_OF_A_KIND',
      STRAIGHT: 'STRAIGHT',
      FOUR_OF_A_KIND: 'FOUR_OF_A_KIND',
      EXTENDED_STRAIGHT: 'EXTENDED_STRAIGHT',
      EXTENDED_STRAIGHT_5: 'EXTENDED_STRAIGHT_5',
      FIVE_OF_A_KIND: 'FIVE_OF_A_KIND',
      DOUBLE_STRAIGHT: 'DOUBLE_STRAIGHT',
      INVALID: 'INVALID'
    };
    
    // Valid groups for straights
    this.STRAIGHT_GROUPS = [
      ['GENERAL', 'ADVISOR', 'ELEPHANT'],
      ['CHARIOT', 'HORSE', 'CANNON']
    ];
  }

  /**
   * Validate a play
   * @param {Array} pieces - Array of piece objects with name and color
   * @returns {Object} { valid: boolean, type: string, message?: string }
   */
  validatePlay(pieces) {
    if (!pieces || pieces.length === 0) {
      return { valid: false, type: this.PLAY_TYPES.INVALID, message: 'No pieces selected' };
    }
    
    if (pieces.length > 6) {
      return { valid: false, type: this.PLAY_TYPES.INVALID, message: 'Maximum 6 pieces allowed' };
    }
    
    const playType = this.getPlayType(pieces);
    const valid = playType !== this.PLAY_TYPES.INVALID;
    
    return {
      valid,
      type: playType,
      message: valid ? undefined : 'Invalid combination'
    };
  }

  /**
   * Get the type of play
   */
  getPlayType(pieces) {
    switch (pieces.length) {
      case 1:
        return this.PLAY_TYPES.SINGLE;
        
      case 2:
        return this.isPair(pieces) ? this.PLAY_TYPES.PAIR : this.PLAY_TYPES.INVALID;
        
      case 3:
        if (this.isThreeOfAKind(pieces)) return this.PLAY_TYPES.THREE_OF_A_KIND;
        if (this.isStraight(pieces)) return this.PLAY_TYPES.STRAIGHT;
        return this.PLAY_TYPES.INVALID;
        
      case 4:
        if (this.isFourOfAKind(pieces)) return this.PLAY_TYPES.FOUR_OF_A_KIND;
        if (this.isExtendedStraight(pieces)) return this.PLAY_TYPES.EXTENDED_STRAIGHT;
        return this.PLAY_TYPES.INVALID;
        
      case 5:
        if (this.isFiveOfAKind(pieces)) return this.PLAY_TYPES.FIVE_OF_A_KIND;
        if (this.isExtendedStraight5(pieces)) return this.PLAY_TYPES.EXTENDED_STRAIGHT_5;
        return this.PLAY_TYPES.INVALID;
        
      case 6:
        return this.isDoubleStraight(pieces) ? this.PLAY_TYPES.DOUBLE_STRAIGHT : this.PLAY_TYPES.INVALID;
        
      default:
        return this.PLAY_TYPES.INVALID;
    }
  }

  /**
   * Parse piece string to get name and color
   */
  parsePiece(pieceStr) {
    // Handle format like "GENERAL_RED(14)"
    const match = pieceStr.match(/^([A-Z]+)_([A-Z]+)(?:\(\d+\))?$/);
    if (match) {
      return { name: match[1], color: match[2] };
    }
    
    // Handle already parsed pieces
    if (pieceStr.name && pieceStr.color) {
      return pieceStr;
    }
    
    return null;
  }

  /**
   * Check if pieces form a pair
   */
  isPair(pieces) {
    if (pieces.length !== 2) return false;
    
    const p1 = this.parsePiece(pieces[0]);
    const p2 = this.parsePiece(pieces[1]);
    
    if (!p1 || !p2) return false;
    
    return p1.name === p2.name && p1.color === p2.color;
  }

  /**
   * Check if pieces form three of a kind (3 soldiers same color)
   */
  isThreeOfAKind(pieces) {
    if (pieces.length !== 3) return false;
    
    const parsed = pieces.map(p => this.parsePiece(p));
    if (parsed.some(p => !p)) return false;
    
    const firstColor = parsed[0].color;
    return parsed.every(p => p.name === 'SOLDIER' && p.color === firstColor);
  }

  /**
   * Check if pieces form a straight
   */
  isStraight(pieces) {
    if (pieces.length !== 3) return false;
    
    const parsed = pieces.map(p => this.parsePiece(p));
    if (parsed.some(p => !p)) return false;
    
    // All must be same color
    const firstColor = parsed[0].color;
    if (!parsed.every(p => p.color === firstColor)) return false;
    
    // Check if names match any valid group
    const names = parsed.map(p => p.name).sort();
    
    return this.STRAIGHT_GROUPS.some(group => {
      const sortedGroup = [...group].sort();
      return JSON.stringify(names) === JSON.stringify(sortedGroup);
    });
  }

  /**
   * Check if pieces form four of a kind (4 soldiers same color)
   */
  isFourOfAKind(pieces) {
    if (pieces.length !== 4) return false;
    
    const parsed = pieces.map(p => this.parsePiece(p));
    if (parsed.some(p => !p)) return false;
    
    const firstColor = parsed[0].color;
    return parsed.every(p => p.name === 'SOLDIER' && p.color === firstColor);
  }

  /**
   * Check if pieces form an extended straight (4 from group with 1 duplicate)
   */
  isExtendedStraight(pieces) {
    if (pieces.length !== 4) return false;
    
    const parsed = pieces.map(p => this.parsePiece(p));
    if (parsed.some(p => !p)) return false;
    
    // All must be same color
    const firstColor = parsed[0].color;
    if (!parsed.every(p => p.color === firstColor)) return false;
    
    // Count each piece type
    const counts = {};
    parsed.forEach(p => {
      counts[p.name] = (counts[p.name] || 0) + 1;
    });
    
    // Must have exactly one duplicate
    const countValues = Object.values(counts);
    if (!countValues.includes(2) || countValues.filter(v => v === 2).length !== 1) {
      return false;
    }
    
    // Check if all pieces belong to same valid group
    const uniqueNames = Object.keys(counts);
    return this.STRAIGHT_GROUPS.some(group => 
      uniqueNames.every(name => group.includes(name))
    );
  }

  /**
   * Check if pieces form five of a kind (5 soldiers same color)
   */
  isFiveOfAKind(pieces) {
    if (pieces.length !== 5) return false;
    
    const parsed = pieces.map(p => this.parsePiece(p));
    if (parsed.some(p => !p)) return false;
    
    const firstColor = parsed[0].color;
    return parsed.every(p => p.name === 'SOLDIER' && p.color === firstColor);
  }

  /**
   * Check if pieces form extended straight 5 (5 from group with 2 duplicates)
   */
  isExtendedStraight5(pieces) {
    if (pieces.length !== 5) return false;
    
    const parsed = pieces.map(p => this.parsePiece(p));
    if (parsed.some(p => !p)) return false;
    
    // All must be same color
    const firstColor = parsed[0].color;
    if (!parsed.every(p => p.color === firstColor)) return false;
    
    // Count each piece type
    const counts = {};
    parsed.forEach(p => {
      counts[p.name] = (counts[p.name] || 0) + 1;
    });
    
    // Must have pattern: [1, 2, 2] when sorted
    const countValues = Object.values(counts).sort();
    if (JSON.stringify(countValues) !== JSON.stringify([1, 2, 2])) {
      return false;
    }
    
    // Check if all pieces belong to same valid group
    const uniqueNames = Object.keys(counts);
    return this.STRAIGHT_GROUPS.some(group => 
      uniqueNames.every(name => group.includes(name))
    );
  }

  /**
   * Check if pieces form double straight (2 each of CHARIOT, HORSE, CANNON)
   */
  isDoubleStraight(pieces) {
    if (pieces.length !== 6) return false;
    
    const parsed = pieces.map(p => this.parsePiece(p));
    if (parsed.some(p => !p)) return false;
    
    // All must be same color
    const firstColor = parsed[0].color;
    if (!parsed.every(p => p.color === firstColor)) return false;
    
    // Count each piece type
    const counts = {};
    parsed.forEach(p => {
      counts[p.name] = (counts[p.name] || 0) + 1;
    });
    
    // Must have exactly these pieces
    const required = { 'CHARIOT': 2, 'HORSE': 2, 'CANNON': 2 };
    
    return Object.keys(required).every(name => counts[name] === required[name]) &&
           Object.keys(counts).length === 3;
  }

  /**
   * Get a description of the play type
   */
  getPlayTypeDescription(playType) {
    const descriptions = {
      [this.PLAY_TYPES.SINGLE]: 'Single piece',
      [this.PLAY_TYPES.PAIR]: 'Pair',
      [this.PLAY_TYPES.THREE_OF_A_KIND]: 'Three of a kind',
      [this.PLAY_TYPES.STRAIGHT]: 'Straight',
      [this.PLAY_TYPES.FOUR_OF_A_KIND]: 'Four of a kind',
      [this.PLAY_TYPES.EXTENDED_STRAIGHT]: 'Extended straight',
      [this.PLAY_TYPES.EXTENDED_STRAIGHT_5]: 'Extended straight (5)',
      [this.PLAY_TYPES.FIVE_OF_A_KIND]: 'Five of a kind',
      [this.PLAY_TYPES.DOUBLE_STRAIGHT]: 'Double straight',
      [this.PLAY_TYPES.INVALID]: 'Invalid'
    };
    
    return descriptions[playType] || 'Unknown';
  }

  /**
   * Quick validation for UI feedback
   */
  canPlayPieces(pieces, requiredCount = null) {
    // Check count requirement
    if (requiredCount !== null && pieces.length !== requiredCount) {
      return {
        canPlay: false,
        reason: `Must play exactly ${requiredCount} pieces`
      };
    }
    
    // Check play validity
    const validation = this.validatePlay(pieces);
    
    return {
      canPlay: validation.valid,
      reason: validation.message || 'Invalid combination',
      playType: validation.type
    };
  }
}

// Create singleton instance
export const playValidator = new PlayValidator();