// frontend/src/stylex-runtime.js

/**
 * StyleX Runtime Configuration
 * 
 * This module handles StyleX runtime setup and provides utilities
 * for integrating StyleX components with the existing application.
 */

import * as stylex from '@stylexjs/stylex';

// Runtime configuration
export const styleXConfig = {
  // Enable dev mode for better debugging
  dev: process.env.NODE_ENV !== 'production',
  
  // Test mode for component testing
  test: process.env.NODE_ENV === 'test',
  
  // Runtime classname prefix to avoid conflicts
  classNamePrefix: 'x',
  
  // Enable CSS variables for theming
  useRemForFontSize: true,
};

/**
 * Initialize StyleX runtime
 * Should be called once at app startup
 */
export function initializeStyleX() {
  // Log initialization in dev mode
  if (styleXConfig.dev) {
    console.log('🎨 StyleX Runtime initialized with config:', styleXConfig);
  }
  
  // Add StyleX root class to document
  document.documentElement.classList.add('stylex-root');
  
  // Set up CSS custom properties for theming
  setupCSSVariables();
}

/**
 * Set up CSS custom properties for StyleX theming
 */
function setupCSSVariables() {
  const root = document.documentElement;
  
  // Theme-aware custom properties
  const theme = localStorage.getItem('theme') || 'light';
  root.setAttribute('data-theme', theme);
  
  // Device pixel ratio for responsive images
  root.style.setProperty('--device-pixel-ratio', window.devicePixelRatio);
  
  // Viewport dimensions for responsive calculations
  root.style.setProperty('--viewport-width', `${window.innerWidth}px`);
  root.style.setProperty('--viewport-height', `${window.innerHeight}px`);
  
  // Update on resize
  window.addEventListener('resize', () => {
    root.style.setProperty('--viewport-width', `${window.innerWidth}px`);
    root.style.setProperty('--viewport-height', `${window.innerHeight}px`);
  });
}

/**
 * Helper to conditionally apply StyleX styles
 * @param {Object} styles - StyleX styles object
 * @param {Object} conditions - Object with condition keys and boolean values
 * @returns {Object} - Props object for spreading
 */
export function conditionalStyles(styles, conditions) {
  const activeStyles = [];
  
  Object.entries(conditions).forEach(([key, isActive]) => {
    if (isActive && styles[key]) {
      activeStyles.push(styles[key]);
    }
  });
  
  return stylex.props(...activeStyles);
}

/**
 * Merge StyleX styles with className prop for backward compatibility
 * @param {Array} stylexStyles - Array of StyleX style objects
 * @param {string} className - Optional className prop
 * @returns {Object} - Props object with merged styles
 */
export function mergeStyles(stylexStyles, className) {
  const stylexProps = stylex.props(...stylexStyles);
  
  if (className) {
    return {
      ...stylexProps,
      className: `${stylexProps.className || ''} ${className}`.trim(),
    };
  }
  
  return stylexProps;
}

/**
 * Create responsive style variants
 * @param {Object} baseStyle - Base StyleX style
 * @param {Object} breakpoints - Breakpoint-specific overrides
 * @returns {Object} - Responsive StyleX styles
 */
export function responsiveStyles(baseStyle, breakpoints = {}) {
  return stylex.create({
    base: baseStyle,
    ...Object.entries(breakpoints).reduce((acc, [breakpoint, overrides]) => {
      acc[breakpoint] = {
        [`@media (min-width: ${getBreakpointValue(breakpoint)})`]: overrides,
      };
      return acc;
    }, {}),
  });
}

/**
 * Get breakpoint value
 * @param {string} breakpoint - Breakpoint name
 * @returns {string} - Breakpoint value
 */
function getBreakpointValue(breakpoint) {
  const breakpoints = {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  };
  
  return breakpoints[breakpoint] || breakpoint;
}

/**
 * Performance monitoring for StyleX components
 * @param {string} componentName - Name of the component
 * @param {Function} fn - Function to measure
 * @returns {*} - Result of the function
 */
export function measureStyleXPerformance(componentName, fn) {
  if (!styleXConfig.dev) {
    return fn();
  }
  
  const startTime = performance.now();
  const result = fn();
  const endTime = performance.now();
  
  const duration = endTime - startTime;
  
  if (duration > 16) { // Log if render takes more than one frame
    console.warn(
      `⚠️ StyleX component ${componentName} took ${duration.toFixed(2)}ms to render`
    );
  }
  
  return result;
}

/**
 * Utility to extract StyleX variables for testing
 * @param {Object} tokens - StyleX tokens object
 * @returns {Object} - Extracted CSS variables
 */
export function extractStyleXVariables(tokens) {
  const variables = {};
  
  Object.entries(tokens).forEach(([key, value]) => {
    if (typeof value === 'object' && value.__stylex) {
      variables[key] = value.__stylex;
    } else {
      variables[key] = value;
    }
  });
  
  return variables;
}

/**
 * Create a styled component wrapper for gradual migration
 * @param {React.Component} Component - Component to wrap
 * @param {Object} defaultStyles - Default StyleX styles
 * @returns {React.Component} - Wrapped component
 */
export function withStyleX(Component, defaultStyles) {
  return function StyleXWrapper(props) {
    const { className, style, ...restProps } = props;
    
    const mergedProps = mergeStyles([defaultStyles], className);
    
    return (
      <Component
        {...restProps}
        {...mergedProps}
        style={{ ...mergedProps.style, ...style }}
      />
    );
  };
}

// Export stylex for convenience
export { stylex };

// Auto-initialize in browser environment
if (typeof window !== 'undefined') {
  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeStyleX);
  } else {
    initializeStyleX();
  }
}