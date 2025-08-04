#!/bin/bash

# Script to switch between legacy JSX and StyleX versions

echo "🎨 Switching to StyleX version..."

# Backup current main.js
cp main.js main.js.backup

# Update main.js to use StyleX version
cat > main.js << 'EOF'
import React from 'react';
import { createRoot } from 'react-dom/client';
import './src/styles/globals.css';
import App from './src/App.stylex';  // Using StyleX version

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />);
EOF

echo "✅ Switched to StyleX version!"
echo "📦 You'll see 'StyleX ✨' indicator in top-right corner"
echo ""
echo "To switch back to legacy, run: ./switch-to-legacy.sh"