// frontend/stylex.config.js
// StyleX Configuration for the frontend application

module.exports = {
  // Define the root directory for StyleX
  rootDir: __dirname,
  
  // Build configuration
  build: {
    // Use the babel plugin for StyleX compilation
    type: 'babel',
    
    // Output configuration
    output: {
      // CSS file output location
      cssFileName: 'dist/styles.css',
      
      // JavaScript runtime injection
      jsFileName: 'dist/stylex-runtime.js',
    },
    
    // Optimization settings
    optimize: {
      // Enable minification in production
      minify: process.env.NODE_ENV === 'production',
      
      // Dead code elimination
      treeshake: true,
      
      // Atomic CSS generation
      atomicCSS: true,
    },
  },
  
  // Development configuration
  dev: {
    // Enable hot module replacement
    hmr: true,
    
    // Source maps for debugging
    sourceMaps: true,
    
    // Development-specific optimizations
    lazyCompilation: true,
  },
  
  // Theme configuration
  theme: {
    // Reference to design tokens
    tokensPath: './src/design-system/tokens.stylex.js',
    
    // Enable CSS variables for dynamic theming
    cssVariables: true,
  },
  
  // Compatibility settings
  compatibility: {
    // Support className prop during migration
    classNameProp: true,
    
    // Browser targets
    browsers: [
      'last 2 Chrome versions',
      'last 2 Firefox versions',
      'last 2 Safari versions',
      'last 2 Edge versions',
    ],
  },
  
  // Performance settings
  performance: {
    // Bundle size budget (in KB)
    maxBundleSize: 150,
    
    // Lazy loading for components
    lazyLoading: true,
    
    // Code splitting strategy
    splitChunks: {
      // Split vendor code
      vendor: true,
      
      // Split by route
      routes: true,
      
      // Minimum chunk size (in KB)
      minSize: 10,
    },
  },
  
  // Experimental features
  experimental: {
    // Enable new StyleX features
    modernSyntax: true,
    
    // Parallel compilation
    parallelCompilation: true,
    
    // Advanced tree shaking
    advancedTreeShaking: true,
  },
};