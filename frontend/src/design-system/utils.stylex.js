// Utility functions and helpers for StyleX
import * as stylex from '@stylexjs/stylex';
import { layout } from './tokens.stylex';

// Responsive media queries
export const media = {
  sm: `@media (min-width: ${layout.breakpointSm})`,
  md: `@media (min-width: ${layout.breakpointMd})`,
  lg: `@media (min-width: ${layout.breakpointLg})`,
  xl: `@media (min-width: ${layout.breakpointXl})`,
  '2xl': `@media (min-width: ${layout.breakpoint2xl})`,
  
  // Custom queries
  mobile: '@media (max-width: 639px)',
  tablet: `@media (min-width: ${layout.breakpointSm}) and (max-width: 1023px)`,
  desktop: `@media (min-width: ${layout.breakpointLg})`,
  
  // Feature queries
  hover: '@media (hover: hover)',
  touch: '@media (hover: none) and (pointer: coarse)',
  reducedMotion: '@media (prefers-reduced-motion: reduce)',
  dark: '@media (prefers-color-scheme: dark)',
  light: '@media (prefers-color-scheme: light)',
};

// Helper to apply multiple styles conditionally
export function applyStyles(...styles) {
  return stylex.props(...styles.filter(Boolean));
}

// Helper to create dynamic styles with runtime values
export function createDynamicStyle(property, value) {
  if (!value) return null;
  
  return stylex.create({
    dynamic: {
      [property]: value,
    },
  });
}

// Helper to create variant styles
export function createVariant(baseStyles, variants) {
  return (variant, additionalStyles = []) => {
    const variantStyle = variants[variant] || {};
    return stylex.props(
      baseStyles,
      variantStyle,
      ...additionalStyles
    );
  };
}

// Helper to combine style props with className (for migration period)
export function combineStyles(stylexStyles, className = '') {
  const stylexProps = Array.isArray(stylexStyles) 
    ? stylex.props(...stylexStyles)
    : stylex.props(stylexStyles);
  
  if (className) {
    return {
      ...stylexProps,
      className: `${stylexProps.className || ''} ${className}`.trim(),
    };
  }
  
  return stylexProps;
}

// Helper for conditional styles
export function conditionalStyle(condition, trueStyle, falseStyle = null) {
  if (condition) return trueStyle;
  return falseStyle;
}

// Helper to create responsive styles
export function responsive(styles) {
  const responsiveStyles = {};
  
  Object.entries(styles).forEach(([breakpoint, style]) => {
    if (media[breakpoint]) {
      responsiveStyles[media[breakpoint]] = style;
    } else {
      responsiveStyles[breakpoint] = style;
    }
  });
  
  return responsiveStyles;
}

// Helper to merge multiple style objects
export function mergeStyles(...styleObjects) {
  const merged = {};
  
  styleObjects.forEach(obj => {
    if (obj) {
      Object.assign(merged, obj);
    }
  });
  
  return merged;
}

// Helper to create hover/focus/active states
export function interactionStates(baseState, hoverState = {}, activeState = {}, focusState = {}) {
  return {
    ...baseState,
    ':hover': hoverState,
    ':active': activeState,
    ':focus': focusState,
    ':focus-visible': focusState,
  };
}

// Helper to create disabled state
export function disabledState(styles = {}) {
  return {
    ':disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
      pointerEvents: 'none',
      ...styles,
    },
  };
}

// Helper for animation keyframes
export function createAnimation(name, keyframes, duration = '300ms', easing = 'ease-in-out') {
  const animation = stylex.keyframes(keyframes);
  
  return {
    animationName: animation,
    animationDuration: duration,
    animationTimingFunction: easing,
    animationFillMode: 'both',
  };
}

// Helper to extract theme values at runtime (for dynamic theming)
export function getThemeValue(token) {
  // This would be used with CSS custom properties for runtime theming
  return `var(--${token})`;
}

// Helper to create grid layouts
export function gridLayout(columns, rows, gap) {
  const layout = {
    display: 'grid',
  };
  
  if (columns) {
    layout.gridTemplateColumns = typeof columns === 'number' 
      ? `repeat(${columns}, 1fr)` 
      : columns;
  }
  
  if (rows) {
    layout.gridTemplateRows = typeof rows === 'number' 
      ? `repeat(${rows}, 1fr)` 
      : rows;
  }
  
  if (gap) {
    layout.gap = gap;
  }
  
  return layout;
}

// Helper to create flex layouts
export function flexLayout(direction = 'row', justify = 'flex-start', align = 'stretch', gap = null) {
  const layout = {
    display: 'flex',
    flexDirection: direction,
    justifyContent: justify,
    alignItems: align,
  };
  
  if (gap) {
    layout.gap = gap;
  }
  
  return layout;
}

// Helper for aspect ratios
export function aspectRatio(ratio) {
  const [width, height] = ratio.split(':').map(Number);
  return {
    aspectRatio: `${width} / ${height}`,
    '@supports not (aspect-ratio: 1)': {
      '&::before': {
        content: '""',
        display: 'block',
        paddingTop: `${(height / width) * 100}%`,
      },
    },
  };
}

// Helper for truncating text
export function truncate(lines = 1) {
  if (lines === 1) {
    return {
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      whiteSpace: 'nowrap',
    };
  }
  
  return {
    overflow: 'hidden',
    display: '-webkit-box',
    WebkitLineClamp: lines,
    WebkitBoxOrient: 'vertical',
    textOverflow: 'ellipsis',
  };
}

// Helper for creating transitions
export function createTransition(properties = ['all'], duration = '300ms', easing = 'ease-in-out', delay = '0ms') {
  const transitionValue = properties
    .map(prop => `${prop} ${duration} ${easing} ${delay}`)
    .join(', ');
  
  return {
    transition: transitionValue,
  };
}

// Helper for creating transforms
export function transform(transforms = {}) {
  const transformValues = [];
  
  if (transforms.translateX) transformValues.push(`translateX(${transforms.translateX})`);
  if (transforms.translateY) transformValues.push(`translateY(${transforms.translateY})`);
  if (transforms.rotate) transformValues.push(`rotate(${transforms.rotate})`);
  if (transforms.scale) transformValues.push(`scale(${transforms.scale})`);
  if (transforms.skewX) transformValues.push(`skewX(${transforms.skewX})`);
  if (transforms.skewY) transformValues.push(`skewY(${transforms.skewY})`);
  
  return {
    transform: transformValues.join(' '),
  };
}

// Helper for creating gradients
export function linearGradient(direction, ...colorStops) {
  const gradient = `linear-gradient(${direction}, ${colorStops.join(', ')})`;
  return {
    background: gradient,
    backgroundImage: gradient,
  };
}

export function radialGradient(shape, ...colorStops) {
  const gradient = `radial-gradient(${shape}, ${colorStops.join(', ')})`;
  return {
    background: gradient,
    backgroundImage: gradient,
  };
}

// Export all helpers as a single object for convenience
export const helpers = {
  applyStyles,
  createDynamicStyle,
  createVariant,
  combineStyles,
  conditionalStyle,
  responsive,
  mergeStyles,
  interactionStates,
  disabledState,
  createAnimation,
  getThemeValue,
  gridLayout,
  flexLayout,
  aspectRatio,
  truncate,
  createTransition,
  transform,
  linearGradient,
  radialGradient,
};