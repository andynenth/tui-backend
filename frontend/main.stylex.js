// frontend/main.stylex.js

import React from 'react';
import { createRoot } from 'react-dom/client';
import './src/styles/globals.css'; // Keep for now during migration
import App from './src/App.stylex';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />);