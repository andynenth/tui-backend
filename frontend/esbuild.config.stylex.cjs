const esbuild = require('esbuild');
const path = require('path');
const fs = require('fs');

// Since esbuild-plugin is deprecated, we'll use a custom approach
// We'll compile StyleX using babel in a separate step

const isDev = process.env.NODE_ENV !== 'production';
const isProduction = !isDev;

// ESBuild configuration
const config = {
  entryPoints: ['./main.js'],
  bundle: true,
  outfile: '../backend/static/bundle.js',
  format: 'iife',
  platform: 'browser',
  target: 'es2020',
  minify: isProduction,
  sourcemap: true,
  loader: {
    '.js': 'jsx',
    '.jsx': 'jsx',
    '.ts': 'tsx',
    '.tsx': 'tsx',
    '.svg': 'text',
    '.png': 'dataurl',
    '.jpg': 'dataurl',
    '.jpeg': 'dataurl',
    '.gif': 'dataurl',
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
  },
  // We'll handle StyleX transformation separately
  plugins: [],
};

async function build() {
  try {
    // For now, build without StyleX transformation
    // We'll add StyleX support in the next step
    const result = await esbuild.build({
      ...config,
      metafile: true,
    });

    if (result.metafile) {
      const text = await esbuild.analyzeMetafile(result.metafile);
      console.log('Bundle analysis:', text);
    }

    console.log('✅ StyleX build configuration ready (test mode)');
  } catch (error) {
    console.error('❌ Build failed:', error);
    process.exit(1);
  }
}

// Watch mode for development
if (process.argv.includes('--watch')) {
  (async () => {
    const ctx = await esbuild.context(config);
    await ctx.watch();
    console.log('👀 Watching for changes (StyleX test mode)...');
  })();
} else {
  build();
}