# Complete Guide to esbuild-css-modules-plugin

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Configuration Options](#configuration-options)
5. [Advanced Usage](#advanced-usage)
6. [How It Works Internally](#how-it-works-internally)
7. [Common Issues and Solutions](#common-issues-and-solutions)
8. [Migration Guide](#migration-guide)
9. [Alternatives](#alternatives)

## Introduction

The `esbuild-css-modules-plugin` is a third-party plugin that adds CSS Modules support to esbuild, which doesn't natively support this feature. CSS Modules provide locally scoped CSS by default, solving the global namespace problem in CSS.

### What are CSS Modules?

CSS Modules are CSS files where all class names and animation names are scoped locally by default. This means:
- Classes are unique to the component
- No accidental style conflicts
- Explicit dependencies between components and styles

## Installation

```bash
npm install --save-dev esbuild-css-modules-plugin
# or
yarn add -D esbuild-css-modules-plugin
# or
pnpm add -D esbuild-css-modules-plugin
```

## Basic Usage

### 1. Setup in esbuild config

```javascript
// esbuild.config.js
const esbuild = require('esbuild');
const cssModulesPlugin = require('esbuild-css-modules-plugin');

esbuild.build({
  entryPoints: ['src/index.js'],
  bundle: true,
  outfile: 'dist/bundle.js',
  plugins: [
    cssModulesPlugin()
  ],
});
```

### 2. Create a CSS Module

```css
/* Button.module.css */
.button {
  padding: 10px 20px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
}

.primary {
  background-color: #007bff;
  color: white;
}

.secondary {
  background-color: #6c757d;
  color: white;
}

/* Composition */
.large {
  composes: button;
  padding: 15px 30px;
  font-size: 18px;
}
```

### 3. Use in JavaScript/React

```javascript
// Button.jsx
import React from 'react';
import styles from './Button.module.css';

const Button = ({ variant = 'primary', size, children }) => {
  const className = [
    styles.button,
    styles[variant],
    size === 'large' && styles.large
  ].filter(Boolean).join(' ');

  return (
    <button className={className}>
      {children}
    </button>
  );
};

// The imported styles object looks like:
// {
//   button: "Button_button__3xKp2",
//   primary: "Button_primary__1jIm5",
//   secondary: "Button_secondary__2pLk8",
//   large: "Button_large__3mDn1"
// }
```

## Configuration Options

```javascript
cssModulesPlugin({
  // Inject styles into page (default: true)
  inject: true,
  
  // How to handle CSS class names
  localsConvention: 'camelCase', // 'camelCase' | 'camelCaseOnly' | 'dashes' | 'dashesOnly'
  
  // Pattern for generating scoped names
  generateScopedName: '[name]__[local]___[hash:base64:5]',
  // Other patterns:
  // '[hash:base64:8]' - Just hash (shortest)
  // '[path][name]__[local]' - Include path
  // '[folder]__[local]___[hash:base64:5]' - Include folder
  // Custom function also supported
  
  // CSS Modules behavior
  mode: 'local', // 'local' | 'global' | 'pure'
  
  // PostCSS plugins
  postcss: {
    plugins: [
      require('autoprefixer'),
      require('postcss-nested')
    ]
  },
  
  // File pattern matching
  pattern: /\.module\.css$/,
  
  // Root directory for resolving paths
  rootDir: process.cwd(),
  
  // Export globals
  exportGlobals: false,
  
  // Custom resolver for @import and composes
  resolve: {
    alias: {
      '@styles': path.resolve(__dirname, 'src/styles')
    }
  }
})
```

### Configuration Options Explained

#### `inject` (boolean)
- `true`: Automatically injects styles into the document
- `false`: Returns CSS as a string for manual handling

#### `localsConvention` (string)
Transforms CSS class names for JavaScript:
```css
/* CSS */
.btn-primary { }
.my_button { }

/* JavaScript with different conventions */
// camelCase: { btnPrimary, myButton }
// camelCaseOnly: { btnPrimary, myButton } (no originals)
// dashes: { 'btn-primary', btnPrimary, my_button }
// dashesOnly: { 'btn-primary', my_button } (no transform)
```

#### `generateScopedName` (string | function)
Controls the generated class names:

**String patterns:**
- `[name]` - CSS filename
- `[local]` - Original class name
- `[hash]` - Content hash
- `[hash:base64:5]` - Base64 hash, 5 chars
- `[folder]` - Parent folder name
- `[path]` - Relative path

**Function:**
```javascript
generateScopedName: (name, filename, css) => {
  // Custom logic
  return `myapp_${name}_${hash(css).substring(0, 5)}`;
}
```

#### `mode` (string)
- `local`: Default CSS Modules behavior
- `global`: All classes are global
- `pure`: No side effects, must handle CSS manually

## Advanced Usage

### 1. Global Styles

```css
/* styles.module.css */

/* Local by default */
.localClass {
  color: blue;
}

/* Explicitly global */
:global(.globalClass) {
  color: red;
}

/* Global block */
:global {
  .header {
    background: white;
  }
  
  body {
    margin: 0;
  }
}
```

### 2. Composition

```css
/* base.module.css */
.baseButton {
  padding: 10px;
  border: none;
  cursor: pointer;
}

/* button.module.css */
.primary {
  composes: baseButton from './base.module.css';
  background: blue;
  color: white;
}

/* Multiple compositions */
.special {
  composes: primary;
  composes: animated from './animations.module.css';
  font-weight: bold;
}
```

### 3. Values Export

```css
/* colors.module.css */
@value primary: #007bff;
@value secondary: #6c757d;
@value small: 10px;
@value medium: 20px;
@value large: 30px;

.button {
  padding: small medium;
  background: primary;
}
```

```javascript
import styles, { primary, medium } from './colors.module.css';

console.log(primary); // "#007bff"
console.log(medium);  // "20px"
```

### 4. Custom PostCSS Configuration

```javascript
cssModulesPlugin({
  postcss: {
    plugins: [
      require('postcss-import')({
        path: ['src/styles']
      }),
      require('postcss-mixins'),
      require('postcss-nested'),
      require('autoprefixer'),
      require('cssnano')({
        preset: 'default'
      })
    ]
  }
})
```

### 5. TypeScript Support

Create type definitions for CSS Modules:

```typescript
// css-modules.d.ts
declare module '*.module.css' {
  const classes: { readonly [key: string]: string };
  export default classes;
}

// For named exports with @value
declare module '*.module.css' {
  const classes: { readonly [key: string]: string };
  export default classes;
  export const primary: string;
  export const secondary: string;
}
```

### 6. Dynamic Class Names

```javascript
import styles from './Component.module.css';

function Component({ state, size }) {
  // Using template literals
  const className = `${styles.base} ${styles[`state-${state}`]} ${styles[size]}`;
  
  // Using classnames library
  import cx from 'classnames';
  const className = cx(
    styles.base,
    styles[`state-${state}`],
    {
      [styles.large]: size === 'large',
      [styles.active]: state === 'active'
    }
  );
  
  return <div className={className} />;
}
```

## How It Works Internally

### 1. File Detection
The plugin intercepts imports/requires that match the pattern (default: `/\.module\.css$/`)

### 2. CSS Parsing
- Reads the CSS file
- Parses it using PostCSS
- Identifies all local classes, IDs, and @keyframes

### 3. Name Transformation
- Generates unique names based on `generateScopedName`
- Creates a mapping object: `{ originalName: uniqueName }`

### 4. CSS Rewriting
- Replaces all local selectors with unique names
- Preserves :global() selectors
- Handles composition by inlining composed styles

### 5. JavaScript Generation
Generates JavaScript code that:
- Exports the mapping object as default
- Optionally injects styles into the document
- Exports any @value declarations as named exports

### 6. Example Transformation

**Input CSS:**
```css
.button { color: blue; }
.active { font-weight: bold; }
```

**Generated CSS:**
```css
.Button_button__x7d9s { color: blue; }
.Button_active__k3n2m { font-weight: bold; }
```

**Generated JavaScript:**
```javascript
const styles = {
  "button": "Button_button__x7d9s",
  "active": "Button_active__k3n2m"
};

// If inject: true
const style = document.createElement('style');
style.textContent = `
  .Button_button__x7d9s { color: blue; }
  .Button_active__k3n2m { font-weight: bold; }
`;
document.head.appendChild(style);

export default styles;
```

## Common Issues and Solutions

### 1. Classes Not Being Scoped

**Issue:** Classes appear global instead of scoped

**Solution:**
```javascript
// Check pattern matches your files
cssModulesPlugin({
  pattern: /\.module\.css$/, // Must match your naming convention
})
```

### 2. Import Not Working

**Issue:** `Cannot find module './styles.module.css'`

**Solution:**
```javascript
// Ensure correct loader configuration
esbuild.build({
  loader: {
    '.css': 'text', // Required for CSS Modules
  },
  plugins: [cssModulesPlugin()]
})
```

### 3. Composition Not Resolving

**Issue:** `composes: base from './base.css'` not working

**Solution:**
```javascript
cssModulesPlugin({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    },
    extensions: ['.css', '.module.css']
  }
})
```

### 4. PostCSS Plugins Not Applied

**Issue:** Nested selectors or variables not working

**Solution:**
```javascript
cssModulesPlugin({
  postcss: {
    plugins: [
      require('postcss-nested'),
      require('postcss-simple-vars')
    ]
  }
})
```

### 5. TypeScript Errors

**Issue:** TypeScript can't find module declarations

**Solution:**
```typescript
// tsconfig.json
{
  "compilerOptions": {
    "typeRoots": ["./src/types", "./node_modules/@types"]
  }
}

// src/types/css-modules.d.ts
declare module '*.module.css' {
  const classes: { readonly [key: string]: string };
  export default classes;
}
```

## Migration Guide

### From Global CSS to CSS Modules

1. **Rename files:**
   ```bash
   mv Button.css Button.module.css
   ```

2. **Update imports:**
   ```javascript
   // Before
   import './Button.css';
   
   // After
   import styles from './Button.module.css';
   ```

3. **Update class usage:**
   ```javascript
   // Before
   <button className="button primary large">
   
   // After
   <button className={`${styles.button} ${styles.primary} ${styles.large}`}>
   ```

### From CSS Modules to Regular CSS

1. **Generate prefixed classes:**
   ```javascript
   // Script to extract and prefix classes
   const postcss = require('postcss');
   const fs = require('fs');
   
   const css = fs.readFileSync('Button.module.css', 'utf8');
   const result = postcss.parse(css);
   
   result.walkRules(rule => {
     rule.selector = rule.selector.replace(/\.(\w+)/g, '.button-$1');
   });
   
   fs.writeFileSync('Button.css', result.toString());
   ```

2. **Update imports:**
   ```javascript
   // Remove styles import
   // import styles from './Button.module.css';
   import './Button.css';
   ```

3. **Update class usage:**
   ```javascript
   // Before
   <button className={styles.button}>
   
   // After
   <button className="button-button">
   ```

## Alternatives

### 1. PostCSS Modules
More control but requires additional setup:
```javascript
const postcss = require('postcss');
const postcssModules = require('postcss-modules');

// Manual processing
postcss([
  postcssModules({
    getJSON: (cssFileName, json) => {
      // Handle the mapping
    }
  })
]).process(css);
```

### 2. Vanilla Extract
Type-safe CSS with zero runtime:
```typescript
// styles.css.ts
import { style } from '@vanilla-extract/css';

export const button = style({
  padding: '10px 20px',
  borderRadius: '4px'
});
```

### 3. CSS-in-JS Libraries
- Emotion
- Styled-components
- Stitches

### 4. Manual Prefixing
Simple but requires discipline:
```css
/* Button.css */
.button-root { }
.button-primary { }
.button-large { }
```

## Best Practices

1. **Consistent Naming:** Use `.module.css` suffix consistently
2. **Composition Over Duplication:** Use `composes` for shared styles
3. **Meaningful Names:** Use descriptive class names since they're local
4. **Type Safety:** Generate TypeScript definitions for better DX
5. **Performance:** Use `inject: false` for SSR or when bundling CSS separately
6. **Organization:** Keep CSS modules close to their components

## Conclusion

The `esbuild-css-modules-plugin` brings the power of CSS Modules to esbuild, providing locally scoped CSS with minimal configuration. While it adds some complexity to the build process, it solves many CSS maintainability issues in large applications. However, for simpler projects or when build complexity is a concern, alternatives like manual prefixing or other CSS methodologies might be more appropriate.