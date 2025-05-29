// frontend/vite.config.js

import { defineConfig } from 'vite';

export default defineConfig({
  root: '.', // เดิมอาจเป็น 'frontend'
  server: {
    proxy: {
      '/api': 'http://localhost:5050',
    },
  },
});
