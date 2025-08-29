// frontend/esbuild.config.cjs
const esbuild = require('esbuild');
const postcss = require('postcss');
const tailwindcss = require('@tailwindcss/postcss'); // This is correct for Tailwind v4
const autoprefixer = require('autoprefixer');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: '../.env' });

const entry = process.env.ESBUILD_ENTRY || './main.js';
const outfile = process.env.ESBUILD_OUT || '../backend/static/bundle.js';

// Read version from package.json
const packageJson = require('./package.json');
const appVersion = packageJson.version;

// CSS processing plugin for all CSS files
const cssPlugin = {
  name: 'css',
  setup(build) {
    // Handle all CSS files
    build.onLoad({ filter: /\.css$/ }, async (args) => {
      const css = await fs.promises.readFile(args.path, 'utf8');

      // Process CSS with PostCSS and Tailwind
      const result = await postcss([
        tailwindcss, // Pass the imported module directly, not as a function call
        autoprefixer,
      ]).process(css, { from: args.path });

      return {
        contents: result.css,
        loader: 'css',
      };
    });
  },
};

const buildOptions = {
  entryPoints: [entry],
  bundle: true,
  outdir: '../backend/static',
  entryNames: 'bundle',
  chunkNames: 'chunks/[name]-[hash]',
  splitting: true, // Enable code splitting
  format: 'esm', // Required for splitting
  loader: {
    '.js': 'jsx',
    '.jsx': 'jsx',
    '.ts': 'ts',
    '.tsx': 'tsx',
    '.css': 'css',
    '.svg': 'dataurl',
  },
  jsx: 'automatic',
  minify: true,
  sourcemap: true,
  plugins: [cssPlugin],
  define: {
    '__APP_VERSION__': JSON.stringify(appVersion),
    'process.env.NODE_ENV': JSON.stringify(process.argv.includes('--production') ? 'production' : 'development'),
  },
  // Tree shaking and optimization
  treeShaking: true,
  // Target modern browsers for better optimization
  target: ['chrome90', 'firefox88', 'safari14', 'edge90'],
};

if (process.argv.includes('--production')) {
  // Production build - just build once with analysis
  esbuild
    .build({ ...buildOptions, metafile: true })
    .then((result) => {
      console.log('✅ Production build complete!');
      
      // Bundle analysis
      if (result.metafile) {
        console.log('\n📊 Bundle Analysis:');
        const analysis = esbuild.analyzeMetafileSync(result.metafile, {
          verbose: false,
          color: true
        });
        console.log(analysis);
        
        // Calculate bundle sizes
        const outputs = result.metafile.outputs;
        let totalSize = 0;
        let mainBundleSize = 0;
        let chunkCount = 0;
        
        Object.entries(outputs).forEach(([path, info]) => {
          const size = info.bytes;
          totalSize += size;
          
          if (path.includes('bundle.js')) {
            mainBundleSize = size;
          } else if (path.includes('chunks/')) {
            chunkCount++;
          }
        });
        
        console.log('\n🎯 Bundle Size Summary:');
        console.log(`Main bundle: ${(mainBundleSize / 1024).toFixed(1)}KB`);
        console.log(`Total size: ${(totalSize / 1024).toFixed(1)}KB`);
        console.log(`Code-split chunks: ${chunkCount}`);
        console.log(`Estimated compression (gzip): ~${((totalSize * 0.35) / 1024).toFixed(1)}KB`);
      }
    })
    .catch(() => process.exit(1));
} else {
  // Development - watch mode
  esbuild
    .context(buildOptions)
    .then((ctx) => {
      return ctx.watch();
    })
    .then(() => {
      console.log(
        `👀 Watching for changes to ${entry}, output to ../backend/static/`
      );
    })
    .catch(() => process.exit(1));
}
