// vite.config.js
import { defineConfig } from "vite";

export default defineConfig({
  root: "frontend",
  server: {
    proxy: {
      '/api': 'http://localhost:5050',  // ให้ redirect ไป backend
      '/ws': {
        target: 'ws://localhost:5050',
        ws: true
      }
    }
  }
});
