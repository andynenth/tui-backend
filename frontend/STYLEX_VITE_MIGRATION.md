# StyleX + Vite Migration Documentation

## Overview
This document captures the complete journey of migrating from esbuild to Vite with StyleX support, including all issues encountered, solutions applied, and current state as of August 4, 2025.

## Migration Timeline

### Phase 1: Initial StyleX Migration (Previous Session)
- Successfully converted all CSS files to StyleX syntax
- Created `.stylex.jsx` files for all components
- Commit: `0e38a58a` - "StyleX Migration complete"

### Phase 2: Failed esbuild Integration (Current Session)
- **Attempted**: Use esbuild with Babel plugin for StyleX transformation
- **Result**: Failed due to fundamental incompatibilities
- **Issues**:
  - esbuild cannot handle deep AST transformations required by StyleX
  - Module system conflicts (Babel outputting CommonJS in ESM project)
  - Token imports not resolving properly
  - Syntax errors throughout components

### Phase 3: Vite Migration (Current Session)
- **Decision**: Switch to Vite with official StyleX Rollup plugin
- **Result**: Successful build and dev server startup
- **Status**: WebSocket connection issue remaining

## Technical Issues Encountered

### 1. StyleX Syntax Restrictions

StyleX has strict requirements that differ from regular CSS:

#### ❌ Invalid StyleX Syntax
```javascript
// Shorthand properties not allowed
background: 'linear-gradient(135deg, #0d6efd 0%, #0056b3 100%)'
border: '1px solid #dee2e6'

// Keyframes must use percentage strings
from: { opacity: 0 }
to: { opacity: 1 }

// Template literals had issues
borderColor: `${colors.gray300}`
```

#### ✅ Valid StyleX Syntax
```javascript
// Must expand shorthands
backgroundImage: 'linear-gradient(135deg, #0d6efd 0%, #0056b3 100%)'
borderWidth: '1px',
borderStyle: 'solid',
borderColor: '#dee2e6'

// Must use percentage strings
'0%': { opacity: 0 }
'100%': { opacity: 1 }

// Direct string values
borderColor: '#dee2e6'
```

### 2. Build Tool Limitations

#### esbuild Limitations
- Cannot perform deep AST transformations
- Limited plugin API for compile-time transformations
- Not suitable for CSS-in-JS solutions requiring code transformation

#### Vite Advantages
- Rollup-based plugin system
- Official StyleX Rollup plugin support
- Better handling of compile-time transformations

### 3. Module System Issues

```javascript
// package.json has "type": "module" (ESM)
// But Babel was outputting CommonJS

// Config files needed .cjs extension
postcss.config.js → postcss.config.cjs

// Entry point needed .jsx extension for Vite
main.js → main.jsx
```

## Current State

### ✅ What's Working
1. **Vite Development Server**: Starts successfully on port 3001
2. **Production Build**: Completes without errors
3. **StyleX Compilation**: All components compile with fixed syntax
4. **Hot Module Replacement**: Working with Vite
5. **Asset Handling**: SVG imports and other assets load correctly

### ❌ What's Not Working
1. **WebSocket Connection**: 
   - Frontend tries to connect to `ws://localhost:3001/ws/lobby`
   - Should connect to `ws://localhost:5050/ws/lobby` (backend)
   - Fix already applied in `constants.ts` but needs testing

2. **Design Token System**:
   - Token imports don't work with current Rollup plugin setup
   - All token values are currently inlined as strings
   - Lost centralized design system benefits

### ⚠️ Warnings (Non-Critical)
1. Empty chunk warning: "Generated an empty chunk: 'stylex'"
2. Dynamic import warning for sessionStorage.js

## File Changes Made

### 1. Build Configuration
```javascript
// vite.config.js (NEW)
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import styleX from '@stylexjs/rollup-plugin';

export default defineConfig({
  plugins: [
    react(),
    styleX({
      filename: 'assets/stylex.css',
      dev: process.env.NODE_ENV !== 'production',
      useCSSLayers: true,
      stylexImports: ['@stylexjs/stylex'],
    })
  ],
  server: {
    port: 3001,
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
});
```

### 2. Package.json Scripts
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build && cp -r dist/* ../backend/static/",
    "preview": "vite preview"
  }
}
```

### 3. WebSocket URL Fix
```typescript
// src/constants.ts
get WEBSOCKET_BASE_URL(): string {
  if (typeof window !== 'undefined') {
    // In development, always use the backend port 5050
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'ws://localhost:5050/ws';
    }
    // In production, use the same host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws`;
  }
  return 'ws://localhost:5050/ws';
}
```

### 4. Fixed StyleX Components (38 files total)
All components were fixed for:
- Expanded shorthand properties
- Converted keyframes to percentage syntax
- Fixed template literal issues
- Inlined token values

## Automated Fix Scripts Created

### fix-stylex-for-vite.js
- Replaced background shorthands
- Fixed border shorthands
- Converted keyframes from/to syntax
- Inlined token values

### fix-template-literals.js
- Fixed unnecessary template literal wrapping
- Cleaned up malformed string concatenations

## Next Steps

### 1. Immediate Tasks
- [ ] Test WebSocket connection with the fix applied
- [ ] Verify game functionality end-to-end
- [ ] Check all StyleX styles are rendering correctly

### 2. Medium-term Improvements
- [ ] Investigate proper token system integration with Rollup plugin
- [ ] Consider creating a build-time token resolution system
- [ ] Add StyleX ESLint plugin for syntax validation

### 3. Long-term Considerations
- [ ] Document StyleX patterns for team knowledge sharing
- [ ] Create StyleX component templates
- [ ] Consider migration to Next.js for better StyleX support

## Lessons Learned

### 1. Tool Compatibility Research
- Always verify build tool capabilities before migration
- Check for official plugin support
- Test with minimal proof of concept first

### 2. CSS-in-JS Constraints
- Each CSS-in-JS solution has unique syntax requirements
- Document all restrictions before starting migration
- Create automated tools for systematic fixes

### 3. Development Environment
- Test full stack integration immediately
- Document all service ports clearly
- Use environment-specific configurations

### 4. Migration Strategy
- Keep clean git history with reset strategy
- Automate repetitive fixes
- Test incrementally

## Quick Reference

### Start Development
```bash
# Terminal 1: Backend
docker-compose -f docker-compose.dev.yml up

# Terminal 2: Frontend
cd frontend && npm run dev

# Browser
http://localhost:3001
```

### Debug Commands
```bash
# Check backend health
curl http://localhost:5050/api/health

# View backend logs
curl http://localhost:5050/api/debug/logs | jq

# Build for production
cd frontend && npm run build
```

### Common Issues
1. **Module not found**: Check file extensions (.jsx for React files)
2. **StyleX syntax error**: Expand shorthands, use string values
3. **WebSocket connection failed**: Verify backend is running on 5050
4. **Token import errors**: Currently must inline values

## Dependencies Installed
```json
{
  "devDependencies": {
    "vite": "^7.0.6",
    "@vitejs/plugin-react": "^4.7.0",
    "@stylexjs/rollup-plugin": "^0.15.2"
  }
}
```

## Important Notes
- Backend runs on port **5050** (not 8000 as initially thought)
- Frontend dev server runs on port **3001**
- All StyleX components use `.stylex.jsx` extension
- Design tokens are temporarily inlined until proper integration is implemented

---

**Created**: August 4, 2025  
**Last Commit**: Current HEAD (after Vite migration)  
**Author**: Claude + User collaboration  
**Purpose**: Document StyleX + Vite migration for future reference