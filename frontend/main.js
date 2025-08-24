import React from 'react';
import { createRoot } from 'react-dom/client';
import './src/styles/globals.css';
import App from './src/App.jsx';
import { initializeIOSDebugger } from './src/utils/iosDebug.js';

// Initialize iOS debugging before app starts
initializeIOSDebugger();

const container = document.getElementById('root');
if (!container) {
  console.error('Failed to find root element');
  document.body.innerHTML = '<div style="padding: 20px; color: red;">Error: Root element not found</div>';
} else {
  try {
    const root = createRoot(container);
    root.render(<App />);
    console.log('App rendered successfully');
  } catch (error) {
    console.error('Failed to render app:', error);
    document.body.innerHTML = `<div style="padding: 20px; color: red;">Error: ${error.message}</div>`;
  }
}
