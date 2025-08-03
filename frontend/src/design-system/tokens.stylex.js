// Design tokens for Liap Tui game
import * as stylex from '@stylexjs/stylex';

// Color System - extracted from theme.css and tailwind.config.js
export const colors = stylex.defineVars({
  // Core Palette
  primary: '#1e40af',
  primaryHover: '#1e3a8a',
  primaryActive: '#1e3370',
  primaryDark: '#0056b3',
  
  secondary: '#7c3aed',
  secondaryHover: '#6d28d9',
  secondaryActive: '#5b21b6',
  
  // Semantic Colors
  success: '#059669',
  successLight: '#10b981',
  successDark: '#047857',
  
  warning: '#d97706',
  warningLight: '#f59e0b',
  warningDark: '#b45309',
  
  danger: '#dc2626',
  dangerLight: '#ef4444',
  dangerDark: '#b91c1c',
  
  // Game Theme Colors (from Tailwind config)
  background: '#1e1e2e',
  backgroundAlt: '#262637',
  surface: '#313244',
  surfaceHover: '#3a3b4d',
  border: '#45475a',
  
  // Text Colors
  text: '#cdd6f4',
  textMuted: '#a6adc8',
  textDim: '#585b70',
  textLight: '#ffffff',
  textDark: '#000000',
  
  // Game Piece Colors
  pieceRed: '#f38ba8',
  pieceBlack: '#585b70',
  pieceGold: '#f9e2af',
  pieceSilver: '#a6adc8',
  
  // Player Slot Colors
  slotEmpty: '#45475a',
  slotHost: '#f9e2af',
  slotPlayer: '#74c0fc',
  slotBot: '#cba6f7',
  slotCurrent: '#a6e3a1',
  
  // Status Colors
  online: '#a6e3a1',
  offline: '#f38ba8',
  away: '#f9e2af',
  
  // Neutral Colors (from theme.css)
  gray50: '#f8f9fa',
  gray100: '#e9ecef',
  gray200: '#dee2e6',
  gray300: '#ced4da',
  gray400: '#adb5bd',
  gray500: '#6c757d',
  gray600: '#495057',
  gray700: '#343a40',
  gray800: '#212529',
  gray900: '#000000',
  
  // Special Effects
  glowBlue: 'rgba(59, 130, 246, 0.6)',
  glowPurple: 'rgba(124, 58, 237, 0.6)',
  glowGold: 'rgba(249, 226, 175, 0.6)',
  
  // Table/Surface Colors
  felt: 'rgba(34, 139, 34, 0.15)',
  feltBorder: 'rgba(34, 139, 34, 0.2)',
  wood: '#d4a574',
  woodDark: '#c19a6b',
  woodLight: '#e8d5b7',
});

// Spacing System
export const spacing = stylex.defineVars({
  none: '0px',
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
  xxxl: '64px',
  // Custom spacing from Tailwind
  18: '4.5rem',
  22: '5.5rem',
  88: '22rem',
  96: '24rem',
});

// Typography System
export const typography = stylex.defineVars({
  // Font Families
  fontPrimary: '"Plus Jakarta Sans", system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
  fontSerif: '"Crimson Pro", serif',
  fontGame: '"Inter", system-ui, sans-serif',
  fontMono: '"JetBrains Mono", "Courier New", monospace',
  
  // Font Sizes
  textXs: '12px',
  textSm: '14px',
  textMd: '16px',
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
  weightLight: '300',
  weightNormal: '400',
  weightMedium: '500',
  weightSemibold: '600',
  weightBold: '700',
  
  // Letter Spacing
  trackingTight: '-0.025em',
  trackingNormal: '0',
  trackingWide: '0.025em',
});

// Animation System
export const motion = stylex.defineVars({
  // Durations
  durationInstant: '50ms',
  durationFast: '150ms',
  durationNormal: '300ms',
  durationSlow: '500ms',
  durationSlowest: '1000ms',
  
  // Easings
  easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
  easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
  easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easeBounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  easeElastic: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  
  // Transitions (from theme.css)
  transitionBase: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  transitionFast: 'all 0.15s ease',
});

// Layout System
export const layout = stylex.defineVars({
  // Breakpoints
  breakpointSm: '640px',
  breakpointMd: '768px',
  breakpointLg: '1024px',
  breakpointXl: '1280px',
  breakpoint2xl: '1536px',
  
  // Container
  containerSm: '640px',
  containerMd: '768px',
  containerLg: '1024px',
  containerXl: '1280px',
  container2xl: '1536px',
  containerGame: 'min(100vw, 56.25vh)', // From theme.css
  
  // Border Radius
  radiusNone: '0px',
  radiusSm: '4px',
  radiusMd: '8px',
  radiusLg: '12px',
  radiusXl: '16px',
  radius2xl: '24px',
  radiusFull: '9999px',
  
  // Z-Index layers
  zBase: '0',
  zDropdown: '1000',
  zSticky: '1020',
  zFixed: '1030',
  zModalBackdrop: '1040',
  zModal: '1050',
  zPopover: '1060',
  zTooltip: '1070',
  zNotification: '1080',
  zMax: '9999',
});

// Shadows
export const shadows = stylex.defineVars({
  none: 'none',
  sm: '0 2px 6px rgba(0, 0, 0, 0.04)',
  md: '0 4px 12px rgba(0, 0, 0, 0.08)',
  lg: '0 8px 20px rgba(0, 0, 0, 0.12)',
  xl: '0 20px 40px rgba(0, 0, 0, 0.15)',
  xxl: '0 25px 50px rgba(0, 0, 0, 0.25)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  
  // Custom shadows from theme.css
  insetWhite: 'inset 0 1px 0 rgba(255, 255, 255, 1)',
  border: '0 0 0 1px rgba(255, 255, 255, 0.9)',
  
  // Game-specific shadows (from Tailwind)
  game: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  gameLg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  piece: '0 2px 8px rgba(0, 0, 0, 0.15)',
  pieceHover: '0 4px 12px rgba(0, 0, 0, 0.2)',
  
  // Glow effects
  glow: '0 0 20px rgba(59, 130, 246, 0.6)',
  glowStrong: '0 0 30px rgba(124, 58, 237, 0.8)',
  pieceGlow: '0 0 15px rgba(249, 226, 175, 0.6)',
  pulseGlow: '0 0 10px rgba(59, 130, 246, 0.5)',
});

// Gradients (from theme.css)
export const gradients = stylex.defineVars({
  gray: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 25%, #dee2e6 50%, #ced4da 75%, #adb5bd 100%)',
  success: 'linear-gradient(135deg, #28a745 0%, #20c997 100%)',
  warning: 'linear-gradient(135deg, #ffc107 0%, #ff9800 100%)',
  danger: 'linear-gradient(135deg, #dc3545 0%, #c82333 100%)',
  primary: 'linear-gradient(135deg, #0d6efd 0%, #0056b3 100%)',
  white: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
  
  // Table/wood textures
  wood: 'linear-gradient(135deg, #e8d5b7 0%, #d4a574 50%, #c19a6b 100%)',
  woodTexture: 'linear-gradient(90deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%, rgba(0, 0, 0, 0.1) 100%)',
  
  // Paper texture
  paper: 'radial-gradient(circle at 25% 25%, rgba(255, 255, 255, 0.1) 0%, transparent 50%), radial-gradient(circle at 75% 75%, rgba(0, 0, 0, 0.02) 0%, transparent 50%)',
  
  // Container gradient
  container: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%), radial-gradient(circle at 20% 30%, rgba(255, 193, 7, 0.03) 0%, transparent 70%), radial-gradient(circle at 80% 70%, rgba(13, 110, 253, 0.02) 0%, transparent 70%)',
  
  // Button gradients (from Button.jsx)
  buttonPrimary: 'linear-gradient(to right, #2563eb, #1d4ed8)',
  buttonPrimaryHover: 'linear-gradient(to right, #1d4ed8, #1e40af)',
  buttonSecondary: 'linear-gradient(to right, #e5e7eb, #d1d5db)',
  buttonSecondaryHover: 'linear-gradient(to right, #d1d5db, #9ca3af)',
  buttonSuccess: 'linear-gradient(to right, #059669, #047857)',
  buttonDanger: 'linear-gradient(to right, #dc2626, #b91c1c)',
});

// Backdrop filters
export const backdrop = stylex.defineVars({
  blur: '8px',
  blurSm: '4px',
  blurMd: '12px',
  blurLg: '16px',
  blurXl: '24px',
});