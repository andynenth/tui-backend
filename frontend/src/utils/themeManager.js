// Import SVG assets for different themes
import * as ClassicPieces from '../assets/pieces/classic';
import * as ModernPieces from '../assets/pieces/modern';
import * as MedievalPieces from '../assets/pieces/medieval';

// Theme definitions and management
export const themes = {
  classic: {
    id: 'classic',
    name: 'Classic',
    description: 'Traditional red and black pieces with SVG graphics',
    pieceColors: {
      red: '#dc3545',
      black: '#495057',
    },
    pieceStyle: 'classic',
    pieceAssets: ClassicPieces, // Reference to classic SVG set
    uiElements: {
      startIcon: {
        main: ClassicPieces.GENERAL_RED,
        piece1: ClassicPieces.HORSE_RED,
        piece2: ClassicPieces.SOLDIER_BLACK,
      },
      lobbyEmpty: ClassicPieces.GENERAL_BLACK,
    },
  },
  modern: {
    id: 'modern',
    name: 'Modern',
    description: 'Fresh yellow and blue color scheme',
    pieceColors: {
      red: '#ffc107', // Yellow
      black: '#0d6efd', // Blue
    },
    pieceStyle: 'modern',
    pieceAssets: ModernPieces, // Uses modern SVGs with fixed colors
    uiElements: {
      startIcon: {
        main: ModernPieces.GENERAL_RED,
        piece1: ModernPieces.CANNON_BLACK,
        piece2: ModernPieces.SOLDIER_BLACK,
      },
      lobbyEmpty: ModernPieces.GENERAL_BLACK,
    },
  },
  medieval: {
    id: 'medieval',
    name: 'Medieval',
    description: 'Medieval-style pieces with classic colors',
    pieceColors: {
      red: '#dc3545', // Same as classic red
      black: '#495057', // Same as classic black
    },
    pieceStyle: 'medieval',
    pieceAssets: MedievalPieces, // Reference to medieval SVG set
    uiElements: {
      startIcon: {
        main: MedievalPieces.GENERAL_RED,
        piece1: MedievalPieces.HORSE_RED,
        piece2: MedievalPieces.SOLDIER_BLACK,
      },
      lobbyEmpty: MedievalPieces.GENERAL_BLACK,
    },
  },
};

// Get current theme from localStorage
export const getTheme = () => {
  const saved = localStorage.getItem('liap-tui-theme');
  return saved && themes[saved] ? themes[saved] : themes.classic;
};

// Save theme
export const setTheme = (themeId) => {
  if (!themes[themeId]) {
    console.error(`Theme ${themeId} not found`);
    return false;
  }

  localStorage.setItem('liap-tui-theme', themeId);
  applyThemeColors(themes[themeId]);
  return true;
};

// Apply theme colors to CSS variables (for UI elements only)
export const applyThemeColors = (theme) => {
  const root = document.documentElement;

  // Add theme class to root element
  root.className = `theme-${theme.id}`;

  // Piece colors for UI elements (borders, value badges)
  root.style.setProperty('--piece-color-red', theme.pieceColors.red);
  root.style.setProperty('--piece-color-black', theme.pieceColors.black);

  // UI element colors (for decorative pieces)
  root.style.setProperty('--ui-piece-red', theme.pieceColors.red);
  root.style.setProperty('--ui-piece-black', theme.pieceColors.black);
};

// Initialize theme on page load
export const initializeTheme = () => {
  const currentTheme = getTheme();
  applyThemeColors(currentTheme);
  return currentTheme;
};

// Get all available themes
export const getAllThemes = () => {
  return Object.values(themes);
};

// Get theme by ID
export const getThemeById = (themeId) => {
  return themes[themeId] || null;
};
