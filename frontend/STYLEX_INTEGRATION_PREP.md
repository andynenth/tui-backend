# StyleX Integration Preparation Checklist

## 📋 Pre-Integration Checklist

### 1. **Backup & Version Control**
- [ ] Commit all current changes
- [ ] Create a new branch: `feature/stylex-migration`
- [ ] Tag current version: `pre-stylex-migration`

### 2. **Dependencies to Install**

```bash
# Core StyleX packages
npm install --save @stylexjs/stylex

# Build-time dependencies
npm install --save-dev @stylexjs/esbuild-plugin @stylexjs/babel-plugin

# Optional but recommended for better DX
npm install --save-dev @stylexjs/eslint-plugin
```

### 3. **Current CSS Audit**

Before starting, document your current CSS:

```bash
# Run these commands to get baseline metrics
find src -name "*.css" | wc -l  # Count CSS files (currently 29)
wc -l src/styles/**/*.css       # Count CSS lines (currently 4,007)
du -sh dist/*.css               # Check production bundle size
```

### 4. **Extract Design Tokens**

Create a `src/styles/tokens.stylex.js` file with your design system:

```javascript
import * as stylex from '@stylexjs/stylex';

// Extract from your theme.css and Tailwind config
export const colors = stylex.defineVars({
  // Game colors from your current setup
  gamePrimary: '#1e40af',
  gameSecondary: '#7c3aed',
  gameSuccess: '#059669',
  gameWarning: '#d97706',
  gameDanger: '#dc2626',
  gameBackground: '#1e1e2e',
  gameSurface: '#313244',
  gameText: '#cdd6f4',
  
  // Piece colors
  pieceRed: '#f38ba8',
  pieceBlack: '#585b70',
  pieceGold: '#f9e2af',
  pieceSilver: '#a6adc8',
  
  // Slot colors
  slotEmpty: '#45475a',
  slotHost: '#f9e2af',
  slotPlayer: '#74c0fc',
  slotBot: '#89b4fa',
});

export const spacing = stylex.defineVars({
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
});

export const typography = stylex.defineVars({
  fontFamily: '"Plus Jakarta Sans", system-ui, -apple-system, sans-serif',
  fontSizeXs: '12px',
  fontSizeSm: '14px',
  fontSizeMd: '16px',
  fontSizeLg: '18px',
  fontSizeXl: '24px',
  fontSizeXxl: '32px',
});

export const animations = stylex.defineVars({
  durationFast: '150ms',
  durationNormal: '300ms',
  durationSlow: '500ms',
  easingDefault: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easingBounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
});

export const shadows = stylex.defineVars({
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1)',
});

export const radii = stylex.defineVars({
  sm: '4px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  full: '9999px',
});
```

### 5. **Configure ESBuild**

Update your `esbuild.config.js`:

```javascript
import * as esbuild from 'esbuild';
import styleXPlugin from '@stylexjs/esbuild-plugin';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const config = {
  entryPoints: ['src/main.js'],
  bundle: true,
  outdir: 'dist',
  format: 'esm',
  platform: 'browser',
  target: 'es2020',
  minify: process.env.NODE_ENV === 'production',
  sourcemap: true,
  plugins: [
    styleXPlugin({
      // Dev mode for better debugging
      dev: process.env.NODE_ENV !== 'production',
      // Generate a separate CSS file
      generatedCSSFileName: 'styles.css',
      // Include source maps
      stylexImports: ['@stylexjs/stylex'],
      // Use CSS layers for better cascade control
      useCSSLayers: true,
      // Runtime injection for development
      runtimeInjection: process.env.NODE_ENV !== 'production',
      // Absolute path resolution
      unstable_moduleResolution: {
        type: 'commonJS',
        rootDir: __dirname,
      },
    }),
    // Your other plugins...
  ],
};

// Build function
async function build() {
  try {
    await esbuild.build(config);
    console.log('✅ Build completed successfully');
  } catch (error) {
    console.error('❌ Build failed:', error);
    process.exit(1);
  }
}

// Watch mode for development
if (process.argv.includes('--watch')) {
  const ctx = await esbuild.context(config);
  await ctx.watch();
  console.log('👀 Watching for changes...');
} else {
  build();
}
```

### 6. **TypeScript Configuration**

If using TypeScript, update `tsconfig.json`:

```json
{
  "compilerOptions": {
    // ... existing options
    "types": ["@stylexjs/stylex"],
    "moduleResolution": "bundler",
    "jsx": "react-jsx"
  }
}
```

### 7. **ESLint Configuration**

Add StyleX ESLint plugin to `.eslintrc.js`:

```javascript
module.exports = {
  // ... existing config
  plugins: ['@stylexjs'],
  rules: {
    '@stylexjs/valid-styles': 'error',
    '@stylexjs/sort-keys': 'warn',
  },
};
```

### 8. **Create Migration Utilities**

Create `src/utils/stylesMigration.js` for gradual migration:

```javascript
import * as stylex from '@stylexjs/stylex';

// Utility to combine StyleX with existing classes during migration
export function combineStyles(stylexStyles, classNames = '') {
  const stylexProps = stylex.props(...(Array.isArray(stylexStyles) ? stylexStyles : [stylexStyles]));
  
  if (classNames) {
    return {
      ...stylexProps,
      className: `${stylexProps.className || ''} ${classNames}`.trim(),
    };
  }
  
  return stylexProps;
}

// Helper for conditional styles
export function conditionalStyle(condition, trueStyle, falseStyle = null) {
  if (condition) return trueStyle;
  return falseStyle;
}
```

### 9. **Create Common Styles Library**

Create `src/styles/common.stylex.js`:

```javascript
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, shadows, radii } from './tokens.stylex';

// Common utility styles
export const flex = stylex.create({
  row: {
    display: 'flex',
    flexDirection: 'row',
  },
  column: {
    display: 'flex',
    flexDirection: 'column',
  },
  center: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  between: {
    display: 'flex',
    justifyContent: 'space-between',
  },
  wrap: {
    flexWrap: 'wrap',
  },
});

export const text = stylex.create({
  // Typography variants
  xs: {
    fontSize: typography.fontSizeXs,
  },
  sm: {
    fontSize: typography.fontSizeSm,
  },
  md: {
    fontSize: typography.fontSizeMd,
  },
  lg: {
    fontSize: typography.fontSizeLg,
  },
  xl: {
    fontSize: typography.fontSizeXl,
  },
  
  // Text alignment
  left: { textAlign: 'left' },
  center: { textAlign: 'center' },
  right: { textAlign: 'right' },
  
  // Font weight
  normal: { fontWeight: 400 },
  medium: { fontWeight: 500 },
  semibold: { fontWeight: 600 },
  bold: { fontWeight: 700 },
});

export const spacing = stylex.create({
  // Padding utilities
  p0: { padding: 0 },
  pxs: { padding: spacing.xs },
  psm: { padding: spacing.sm },
  pmd: { padding: spacing.md },
  plg: { padding: spacing.lg },
  pxl: { padding: spacing.xl },
  
  // Margin utilities
  m0: { margin: 0 },
  mxs: { margin: spacing.xs },
  msm: { margin: spacing.sm },
  mmd: { margin: spacing.md },
  mlg: { margin: spacing.lg },
  mxl: { margin: spacing.xl },
  
  // Gap for flexbox
  gapxs: { gap: spacing.xs },
  gapsm: { gap: spacing.sm },
  gapmd: { gap: spacing.md },
  gaplg: { gap: spacing.lg },
});
```

### 10. **Migration Order Strategy**

Prioritize components for migration:

```markdown
## Phase 1: Foundation (Day 1)
1. Button component
2. Modal component
3. Toast notifications
4. Common layouts

## Phase 2: Game UI (Day 2)
1. PlayerAvatar
2. GamePiece
3. PieceTray
4. GameLayout

## Phase 3: Game States (Day 3)
1. Preparation phase
2. Declaration phase
3. Turn phase
4. Scoring phase

## Phase 4: Cleanup (Day 4)
1. Remove old CSS files
2. Remove Tailwind
3. Remove PostCSS
4. Update build scripts
```

### 11. **Testing Strategy**

Prepare tests for the migration:

```javascript
// src/styles/__tests__/stylex.test.js
import * as stylex from '@stylexjs/stylex';
import { colors, spacing } from '../tokens.stylex';

describe('StyleX Token System', () => {
  test('colors are defined correctly', () => {
    expect(colors.gamePrimary).toBeDefined();
    expect(colors.gameBackground).toBeDefined();
  });
  
  test('spacing values are consistent', () => {
    expect(spacing.md).toBe('16px');
    expect(spacing.lg).toBe('24px');
  });
});
```

### 12. **Performance Monitoring**

Set up metrics to track improvement:

```javascript
// src/utils/performanceMonitor.js
export function measureCSSPerformance() {
  const perfData = {
    cssParseTime: 0,
    cssRenderTime: 0,
    totalStyleSheets: document.styleSheets.length,
    totalRules: 0,
  };
  
  // Count total CSS rules
  for (let sheet of document.styleSheets) {
    try {
      perfData.totalRules += sheet.cssRules.length;
    } catch (e) {
      // Cross-origin stylesheets
    }
  }
  
  // Measure paint timing
  const paintMetrics = performance.getEntriesByType('paint');
  
  console.table({
    'Before Migration': {
      'CSS Files': 29,
      'CSS Lines': 4007,
      'Bundle Size': '~150KB',
      'Total Rules': perfData.totalRules,
    },
    'After Migration (Expected)': {
      'CSS Files': 1,
      'CSS Lines': 'N/A (compiled)',
      'Bundle Size': '~40KB',
      'Total Rules': 'Optimized',
    },
  });
  
  return perfData;
}
```

### 13. **Rollback Plan**

Keep the ability to rollback:

```bash
# Create a backup branch
git checkout -b backup/pre-stylex

# If rollback needed
git checkout main
git reset --hard backup/pre-stylex
```

### 14. **Development Workflow**

Update package.json scripts:

```json
{
  "scripts": {
    "dev": "NODE_ENV=development node esbuild.config.js --watch",
    "build": "NODE_ENV=production node esbuild.config.js",
    "build:analyze": "NODE_ENV=production ANALYZE=true node esbuild.config.js",
    "lint:styles": "eslint --ext .js,.jsx --rule '@stylexjs/valid-styles: error' src/",
    "migrate:component": "node scripts/migrateComponent.js"
  }
}
```

### 15. **Component Migration Template**

Use this template for migrating components:

```javascript
// Before (old-component.jsx)
import './old-component.css';

function OldComponent({ isActive, variant }) {
  return (
    <div className={`component ${isActive ? 'active' : ''} ${variant}`}>
      <span className="component-text">Hello</span>
    </div>
  );
}

// After (new-component.jsx)
import * as stylex from '@stylexjs/stylex';
import { colors, spacing } from '../../styles/tokens.stylex';

const styles = stylex.create({
  container: {
    padding: spacing.md,
    backgroundColor: colors.gameSurface,
    borderRadius: '8px',
  },
  active: {
    backgroundColor: colors.gamePrimary,
    transform: 'scale(1.02)',
  },
  text: {
    color: colors.gameText,
    fontSize: '16px',
  },
  // Variants
  primary: {
    backgroundColor: colors.gamePrimary,
  },
  secondary: {
    backgroundColor: colors.gameSecondary,
  },
});

function NewComponent({ isActive, variant = 'primary' }) {
  return (
    <div {...stylex.props(
      styles.container,
      isActive && styles.active,
      styles[variant]
    )}>
      <span {...stylex.props(styles.text)}>Hello</span>
    </div>
  );
}
```

## 📝 Final Preparation Checklist

- [ ] All current work committed
- [ ] New feature branch created
- [ ] Dependencies installed
- [ ] Build configuration updated
- [ ] Design tokens extracted
- [ ] Common styles created
- [ ] Migration utilities prepared
- [ ] Test strategy defined
- [ ] Team notified of migration
- [ ] Rollback plan documented

## 🚀 Ready to Start!

Once all items are checked, you're ready to begin the StyleX migration. Start with the Button component as your proof of concept.

---

*Remember: The goal is gradual migration. Both systems can coexist during the transition.*