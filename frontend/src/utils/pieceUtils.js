/**
 * Utility functions for piece operations
 */

/**
 * Sort pieces by color (red first) and then by point value (highest first)
 * @param {Array} pieces - Array of piece objects with color and point properties
 * @returns {Array} New sorted array of pieces
 */
export const sortPieces = (pieces) => {
  if (!pieces || !Array.isArray(pieces)) {
    return [];
  }
  
  return [...pieces].sort((a, b) => {
    // First sort by color: red before black
    if (a.color !== b.color) {
      return a.color === 'red' ? -1 : 1;
    }
    // Then sort by point value: higher first
    return b.point - a.point;
  });
};