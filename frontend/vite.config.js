import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import styleX from '@stylexjs/rollup-plugin';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  plugins: [
    react(),
    styleX({
      // Compile StyleX files
      filename: 'assets/stylex.css',
      // Development mode
      dev: process.env.NODE_ENV !== 'production',
      // Use CSS layers for proper cascade control
      useCSSLayers: true,
      // Generate source maps
      generatedCSSFileName: path.resolve(__dirname, 'dist/assets/stylex.css'),
      // StyleX import paths
      stylexImports: ['@stylexjs/stylex'],
      // Babel runtime injection
      babelConfig: {
        presets: ['@babel/preset-react'],
        plugins: []
      }
    })
  ],
  
  // Development server configuration
  server: {
    port: 3001,
    open: false,
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
  },

  // Build configuration
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html')
      },
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          stylex: ['@stylexjs/stylex']
        }
      }
    }
  },

  // Resolve configuration
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'),
      '@design-system': path.resolve(__dirname, './src/design-system'),
      '@assets': path.resolve(__dirname, './src/assets'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@managers': path.resolve(__dirname, './src/managers'),
      '@network': path.resolve(__dirname, './src/network'),
      '@contexts': path.resolve(__dirname, './src/contexts'),
      '@phases': path.resolve(__dirname, './src/phases'),
      '@game': path.resolve(__dirname, './src/components/game')
    }
  },

  // CSS configuration
  css: {
    modules: {
      localsConvention: 'camelCase'
    }
  },

  // Optimizations
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', '@stylexjs/stylex']
  }
});