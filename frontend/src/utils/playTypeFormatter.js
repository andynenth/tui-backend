/**
 * Format play type constants into user-friendly display names
 */
export function formatPlayType(playType) {
  const typeMap = {
    SINGLE: 'Single',
    PAIR: 'Pair',
    THREE_OF_A_KIND: 'Three of a Kind',
    STRAIGHT: 'Straight',
    FOUR_OF_A_KIND: 'Four of a Kind',
    EXTENDED_STRAIGHT: 'Extended Straight',
    EXTENDED_STRAIGHT_5: 'Five-Card Straight',
    FIVE_OF_A_KIND: 'Five of a Kind',
    DOUBLE_STRAIGHT: 'Double Straight',
    INVALID: 'Invalid Play',
    UNKNOWN: 'Unknown',
  };

  return typeMap[playType] || playType;
}

/**
 * Get play type description/rules
 */
export function getPlayTypeDescription(playType) {
  const descriptions = {
    SINGLE: '1 piece',
    PAIR: '2 of the same name and color',
    THREE_OF_A_KIND: '3 SOLDIERs of the same color',
    STRAIGHT: '3 cards from valid group (same color)',
    FOUR_OF_A_KIND: '4 SOLDIERs of the same color',
    EXTENDED_STRAIGHT: '4 cards from valid group with 1 duplicate',
    EXTENDED_STRAIGHT_5: '5 cards from valid group with 2 duplicates',
    FIVE_OF_A_KIND: '5 SOLDIERs of the same color',
    DOUBLE_STRAIGHT: '2 CHARIOTs, 2 HORSEs, 2 CANNONs (same color)',
  };

  return descriptions[playType] || '';
}
