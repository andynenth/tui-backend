# StyleX Migration Guide

## Overview

This guide explains how to use the StyleX components in the Liap-Tui frontend application. We've successfully migrated **65% of components** to StyleX while maintaining full backward compatibility.

## Quick Start

### Using StyleX Components

To use the StyleX version of components, simply import from the `.stylex` files:

```javascript
// Old way (still works)
import Button from './components/Button';

// New StyleX way
import Button from './components/Button.stylex';
```

### Running with StyleX

```bash
# Development with StyleX
cd frontend && npm run dev

# Build with StyleX
cd frontend && npm run build
```

## Migration Status

- ✅ **65% Complete** (52 of 80 components migrated)
- ✅ All core UI components migrated
- ✅ All game components migrated  
- ✅ All page components migrated
- ✅ Design system fully implemented
- ✅ Backward compatibility maintained

## Component Categories

### Core Components (✅ Complete)
- Button.stylex.jsx
- Input.stylex.jsx
- Modal.stylex.jsx
- LoadingOverlay.stylex.jsx
- ToastNotification.stylex.jsx
- ErrorBoundary.stylex.jsx

### Game Components (✅ Complete)
- All game UI components
- All game state components
- All game content components
- Game layout and containers

### Page Components (✅ Complete)
- StartPage.stylex.jsx
- LobbyPage.stylex.jsx
- RoomPage.stylex.jsx
- GamePage.stylex.jsx
- TutorialPage.stylex.jsx

### Application Root (✅ Complete)
- App.stylex.jsx
- main.stylex.js

## Design System

### Tokens
All design tokens are centralized in `design-system/tokens.stylex.js`:

```javascript
import { colors, spacing, typography, animations } from './design-system/tokens.stylex';
```

### Common Utilities
Reusable utility classes in `design-system/common.stylex.js`:

```javascript
import { flexCenter, absoluteFill, visuallyHidden } from './design-system/common.stylex';
```

### Helper Functions
StyleX utilities in `design-system/utils.stylex.js`:

```javascript
import { fadeIn, slideIn, createTransition } from './design-system/utils.stylex';
```

## Migration Patterns

### 1. Basic Component Migration

```javascript
// Before (Tailwind)
<div className="p-4 bg-gray-100 rounded-lg">

// After (StyleX)
const styles = stylex.create({
  container: {
    padding: spacing.md,
    backgroundColor: colors.gray100,
    borderRadius: spacing.md,
  }
});

<div {...stylex.props(styles.container)}>
```

### 2. Conditional Styling

```javascript
// StyleX conditional styling
const styles = stylex.create({
  button: {
    // base styles
  },
  primary: {
    backgroundColor: colors.primary,
  },
  disabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  }
});

<button {...stylex.props(
  styles.button,
  variant === 'primary' && styles.primary,
  disabled && styles.disabled
)}>
```

### 3. Backward Compatibility

All StyleX components accept an optional `className` prop for gradual migration:

```javascript
// StyleX component with Tailwind classes (during migration)
<Button.stylex className="additional-tailwind-class">
  Click me
</Button.stylex>
```

### 4. Animation Patterns

```javascript
const styles = stylex.create({
  animated: {
    animationName: animations.fadeIn,
    animationDuration: '300ms',
    animationTimingFunction: 'ease-out',
  }
});
```

### 5. Responsive Design

```javascript
const styles = stylex.create({
  container: {
    padding: spacing.sm,
    '@media (min-width: 768px)': {
      padding: spacing.md,
    },
    '@media (min-width: 1024px)': {
      padding: spacing.lg,
    }
  }
});
```

## Runtime Configuration

The StyleX runtime is configured in `src/stylex-runtime.js` and provides:

- Automatic initialization
- Theme integration
- Performance monitoring
- CSS variable setup
- Migration utilities

## Build Configuration

StyleX is integrated with ESBuild through:

1. **esbuild.config.stylex.cjs** - Build configuration with StyleX plugin
2. **stylex.config.js** - StyleX-specific configuration
3. **package.json** - Updated scripts for StyleX builds

## Best Practices

### DO ✅
- Use design tokens for all values
- Keep styles close to components
- Use semantic naming for style rules
- Leverage compile-time optimization
- Maintain backward compatibility during migration

### DON'T ❌
- Mix inline styles with StyleX
- Use arbitrary values instead of tokens
- Create deeply nested style objects
- Override StyleX styles with !important
- Remove className prop support until migration is complete

## Testing

### Component Testing
```javascript
// Test StyleX components
import Button from './components/Button.stylex';

test('Button renders with StyleX styles', () => {
  const { container } = render(<Button>Test</Button>);
  expect(container.firstChild).toHaveClass(/^x/); // StyleX classes start with 'x'
});
```

### Visual Testing
Use the test components for visual verification:
- `PlayerAvatarTest.stylex.jsx` - Test avatar states
- `test-stylex.jsx` - Test button variants

## Performance Benefits

StyleX provides:
- **Zero runtime overhead** - Styles compiled at build time
- **Automatic deduplication** - Shared atomic classes
- **Optimal bundle size** - Only used styles included
- **Type safety** - Full TypeScript support
- **Dead code elimination** - Unused styles removed

## Troubleshooting

### Common Issues

1. **Styles not applying**
   - Ensure you're using `{...stylex.props(styles.ruleName)}`
   - Check that StyleX plugin is enabled in build

2. **Build errors**
   - Run `npm install` to ensure all dependencies are installed
   - Check `stylex.config.js` configuration

3. **Missing design tokens**
   - Import from `design-system/tokens.stylex.js`
   - Ensure tokens file is properly exported

4. **Performance issues**
   - Use production build for performance testing
   - Enable optimizations in `stylex.config.js`

## Next Steps

### Phase 8: Cleanup (Pending)
- [ ] Remove Tailwind dependencies
- [ ] Remove old CSS files
- [ ] Update all imports to use StyleX components
- [ ] Performance testing and optimization

### Gradual Adoption Strategy
1. New components should be created with StyleX
2. Update imports gradually as components are tested
3. Remove Tailwind after all components migrated
4. Optimize bundle size with final cleanup

## Resources

- [StyleX Documentation](https://stylexjs.com/docs)
- [Migration Checklist](./STYLEX_MIGRATION_TRACKING_CHECKLIST.md)
- [Design System Tokens](./src/design-system/tokens.stylex.js)
- [Runtime Utilities](./src/stylex-runtime.js)