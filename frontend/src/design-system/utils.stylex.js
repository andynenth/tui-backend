import * as stylex from '@stylexjs/stylex';

// Responsive breakpoints
export const media = {
  sm: '@media (min-width: 640px)',
  md: '@media (min-width: 768px)',
  lg: '@media (min-width: 1024px)',
  xl: '@media (min-width: 1280px)',
  xxl: '@media (min-width: 1536px)',
};

// Helper to apply conditional styles
export function applyStyles(...styles) {
  // Filter out falsy values and apply stylex.props
  return stylex.props(...styles.filter(Boolean));
}

// Helper for creating responsive styles
export function createResponsiveStyle(baseStyle, responsiveStyles = {}) {
  const styles = { ...baseStyle };
  
  Object.entries(responsiveStyles).forEach(([breakpoint, style]) => {
    if (media[breakpoint]) {
      styles[media[breakpoint]] = style;
    }
  });
  
  return styles;
}

// Helper for creating variant styles
export function createVariants(baseStyles, variants = {}) {
  return {
    base: baseStyles,
    ...variants,
  };
}

// Helper to combine style objects with conditional logic
export function conditionalStyle(condition, trueStyle, falseStyle = null) {
  return condition ? trueStyle : falseStyle;
}

// Helper for creating themed styles
export function createThemedStyle(lightStyle, darkStyle) {
  return {
    ...lightStyle,
    '@media (prefers-color-scheme: dark)': darkStyle,
  };
}

// Helper for creating animation keyframes
export function createAnimation(name, keyframes) {
  return stylex.keyframes(keyframes);
}

// Common animations
export const animations = {
  fadeIn: stylex.keyframes({
    '0%': {
      opacity: 0,
    },
    '100%': {
      opacity: 1,
    },
  }),
  
  fadeOut: stylex.keyframes({
    '0%': {
      opacity: 1,
    },
    '100%': {
      opacity: 0,
    },
  }),
  
  slideIn: stylex.keyframes({
    '0%': {
      transform: 'translateY(-20px)',
      opacity: 0,
    },
    '100%': {
      transform: 'translateY(0)',
      opacity: 1,
    },
  }),
  
  slideOut: stylex.keyframes({
    '0%': {
      transform: 'translateY(0)',
      opacity: 1,
    },
    '100%': {
      transform: 'translateY(-20px)',
      opacity: 0,
    },
  }),
  
  scaleIn: stylex.keyframes({
    '0%': {
      transform: 'scale(0.95)',
      opacity: 0,
    },
    '100%': {
      transform: 'scale(1)',
      opacity: 1,
    },
  }),
  
  spin: stylex.keyframes({
    '0%': {
      transform: 'rotate(0deg)',
    },
    '100%': {
      transform: 'rotate(360deg)',
    },
  }),
  
  pulse: stylex.keyframes({
    '0%, 100%': {
      opacity: 1,
    },
    '50%': {
      opacity: 0.5,
    },
  }),
  
  float: stylex.keyframes({
    '0%, 100%': {
      transform: 'translateY(0) rotate(0deg)',
    },
    '33%': {
      transform: 'translateY(-10px) rotate(5deg)',
    },
    '66%': {
      transform: 'translateY(-5px) rotate(-3deg)',
    },
  }),
};

// Helper for combining multiple style sources during migration
export function combineStyles(stylexStyles, classNames = '') {
  const stylexProps = applyStyles(...(Array.isArray(stylexStyles) ? stylexStyles : [stylexStyles]));
  
  // During migration, allow combining with existing CSS classes
  if (classNames) {
    return {
      ...stylexProps,
      className: `${stylexProps.className || ''} ${classNames}`.trim(),
    };
  }
  
  return stylexProps;
}

// Helper for creating component-specific styles with variants
export function createComponentStyles(name, styles) {
  const created = stylex.create({
    [name]: styles.base || {},
    ...Object.entries(styles.variants || {}).reduce((acc, [key, value]) => {
      acc[`${name}_${key}`] = value;
      return acc;
    }, {}),
  });
  
  return {
    ...created,
    apply: (variant) => {
      if (variant && created[`${name}_${variant}`]) {
        return stylex.props(created[name], created[`${name}_${variant}`]);
      }
      return stylex.props(created[name]);
    },
  };
}

// Export all utilities
export default {
  media,
  applyStyles,
  createResponsiveStyle,
  createVariants,
  conditionalStyle,
  createThemedStyle,
  createAnimation,
  animations,
  combineStyles,
  createComponentStyles,
};