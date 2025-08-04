#!/bin/bash

# Script to switch back to legacy JSX version

echo "🏛️ Switching to legacy JSX version..."

# Update main.js to use legacy version
cat > main.js << 'EOF'
import React from 'react';
import { createRoot } from 'react-dom/client';
import './src/styles/globals.css';
import App from './src/App.jsx';  // Using legacy JSX version

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />);
EOF

echo "✅ Switched to legacy JSX version!"
echo "📦 You'll see 'Legacy JSX 🏛️' indicator in top-right corner"
echo ""
echo "To switch to StyleX, run: ./switch-to-stylex.sh"