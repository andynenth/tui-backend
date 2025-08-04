import * as stylex from '@stylexjs/stylex';

// Color System (from theme.css)
export const colors = stylex.defineVars({
  // Primary Colors
  primary: '#0d6efd',
  primaryDark: '#0056b3',
  success: '#28a745',
  successLight: '#20c997',
  warning: '#ffc107',
  warningDark: '#ff9800',
  danger: '#dc3545',
  dangerDark: '#c82333',
  
  // Neutral Colors
  gray50: '#f8f9fa',
  gray100: '#e9ecef',
  gray200: '#dee2e6',
  gray300: '#ced4da',
  gray400: '#adb5bd',
  gray500: '#6c757d',
  gray600: '#495057',
  gray700: '#343a40',
  gray800: '#212529',
  
  // White & Black
  white: '#ffffff',
  black: '#000000',
  
  // Game-specific colors (from game components)
  feltGreen: 'rgba(34, 139, 34, 0.15)',
  feltBorder: 'rgba(34, 139, 34, 0.2)',
  woodLight: '#e8d5b7',
  woodMid: '#d4a574',
  woodDark: '#c19a6b',
  
  // Text colors
  textPrimary: '#212529',
  textSecondary: '#495057',
  textMuted: '#6c757d',
  textLight: '#adb5bd',
  textWhite: '#ffffff',
});

// Spacing System
export const spacing = stylex.defineVars({
  none: '0px',
  xxs: '2px',
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '20px',
  xxl: '24px',
  xxxl: '32px',
  xxxxl: '48px',
});

// Typography System
export const typography = stylex.defineVars({
  // Font Families
  fontPrimary: '"Plus Jakarta Sans", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
  fontSerif: '"Crimson Pro", serif',
  
  // Font Sizes
  textXs: '10px',
  textSm: '12px',
  textMd: '14px',
  textBase: '16px',
  textLg: '18px',
  textXl: '20px',
  text2xl: '24px',
  text3xl: '30px',
  text4xl: '36px',
  text5xl: '48px',
  
  // Line Heights
  lineHeightTight: '1.25',
  lineHeightNormal: '1.5',
  lineHeightRelaxed: '1.75',
  lineHeightLoose: '2',
  
  // Font Weights
  weightThin: '300',
  weightNormal: '400',
  weightMedium: '500',
  weightSemibold: '600',
  weightBold: '700',
  
  // Letter Spacing
  trackingTight: '-0.5px',
  trackingNormal: '0px',
  trackingWide: '0.3px',
  trackingWider: '0.5px',
  trackingWidest: '1px',
});

// Animation System
export const motion = stylex.defineVars({
  // Durations
  durationInstant: '50ms',
  durationFast: '150ms',
  durationBase: '300ms',
  durationSlow: '500ms',
  durationSlowest: '1000ms',
  
  // Easings
  easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
  easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
  easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easeBounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
});

// Layout System
export const layout = stylex.defineVars({
  // Container
  containerWidth: 'min(100vw, 56.25vh)',
  containerHeight: 'min(100vh, 177.78vw)',
  containerMaxWidth: '400px',
  containerMaxHeight: '711px',
  
  // Border Radius
  radiusNone: '0px',
  radiusXs: '2px',
  radiusSm: '6px',
  radiusMd: '10px',
  radiusLg: '16px',
  radiusXl: '20px',
  radiusFull: '9999px',
  
  // Z-Index
  zBase: '0',
  zDropdown: '1000',
  zSticky: '1020',
  zFixed: '1030',
  zModalBackdrop: '1040',
  zModal: '1050',
  zPopover: '1060',
  zTooltip: '1070',
});

// Shadows
export const shadows = stylex.defineVars({
  none: 'none',
  sm: '0 2px 6px rgba(0, 0, 0, 0.04)',
  md: '0 4px 12px rgba(0, 0, 0, 0.08)',
  lg: '0 8px 20px rgba(0, 0, 0, 0.12)',
  xl: '0 20px 40px rgba(0, 0, 0, 0.15)',
  insetWhite: 'inset 0 1px 0 rgba(255, 255, 255, 1)',
  border: '0 0 0 1px rgba(255, 255, 255, 0.9)',
  
  // Colored shadows
  primaryGlow: '0 4px 8px rgba(13, 110, 253, 0.2)',
  successGlow: '0 4px 8px rgba(40, 167, 69, 0.2)',
  warningGlow: '0 4px 8px rgba(255, 193, 7, 0.2)',
  dangerGlow: '0 4px 8px rgba(220, 53, 69, 0.2)',
});

// Gradients (as individual components for composition)
export const gradients = stylex.defineVars({
  // Primary gradients
  gray: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 25%, #dee2e6 50%, #ced4da 75%, #adb5bd 100%)',
  success: 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
  warning: 'linear-gradient(135deg, #ffc107 0%, #ff9800 100%)',
  danger: 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)',
  primary: 'linear-gradient(135deg, #0d6efd 0%, #0056b3 100%)',
  white: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
  
  // Table/Wood textures
  wood: 'linear-gradient(135deg, #e8d5b7 0%, #d4a574 50%, #c19a6b 100%)',
  woodTexture: 'linear-gradient(90deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%, rgba(0, 0, 0, 0.1) 100%)',
  
  // Paper texture
  paper: 'radial-gradient(circle at 25% 25%, rgba(255, 255, 255, 0.1) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(0, 0, 0, 0.02) 0%, transparent 50%)',
});