// ESBuild configuration with StyleX plugin
import * as esbuild from 'esbuild';
import styleXPlugin from '@stylexjs/esbuild-plugin';
import path from 'path';
import { fileURLToPath } from 'url';
import * as dotenv from 'dotenv';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: '../.env' });

const isDev = process.env.NODE_ENV !== 'production';
const entry = process.env.ESBUILD_ENTRY || './main.js';

// StyleX plugin configuration
const styleXOptions = {
  dev: isDev,
  test: false,
  unstable_moduleResolution: {
    type: 'commonJS',
    rootDir: __dirname,
  },
  generatedCSSFileName: path.join(__dirname, '../backend/static', 'stylex.css'),
  stylexImports: ['@stylexjs/stylex'],
  useCSSLayers: true,
  runtimeInjection: isDev,
  classNamePrefix: 'x',
  useRemForFontSize: false,
};

const buildOptions = {
  entryPoints: [entry],
  bundle: true,
  outdir: '../backend/static',
  entryNames: 'bundle',
  format: 'esm',
  platform: 'browser',
  target: 'es2020',
  minify: !isDev,
  sourcemap: true,
  metafile: true,
  loader: {
    '.js': 'jsx',
    '.jsx': 'jsx',
    '.ts': 'tsx',
    '.tsx': 'tsx',
    '.svg': 'dataurl',
    '.png': 'dataurl',
    '.jpg': 'dataurl',
    '.jpeg': 'dataurl',
    '.gif': 'dataurl',
    '.woff': 'dataurl',
    '.woff2': 'dataurl',
    '.ttf': 'dataurl',
    '.eot': 'dataurl',
  },
  jsx: 'automatic',
  plugins: [
    styleXPlugin(styleXOptions),
  ],
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
  },
  // Ignore CSS imports since StyleX handles styling
  external: [],
  logLevel: 'info',
};

// Build function with analysis
async function build() {
  try {
    console.log('🚀 Starting StyleX build...');
    const result = await esbuild.build(buildOptions);
    
    if (result.metafile) {
      // Analyze bundle
      const analysis = await esbuild.analyzeMetafile(result.metafile);
      console.log('📊 Bundle Analysis:');
      console.log(analysis);
      
      // Calculate bundle sizes
      const outputs = result.metafile.outputs;
      let jsSize = 0;
      let cssSize = 0;
      
      for (const [file, data] of Object.entries(outputs)) {
        if (file.endsWith('.js')) {
          jsSize += data.bytes;
        } else if (file.endsWith('.css')) {
          cssSize += data.bytes;
        }
      }
      
      console.log(`\n📦 Bundle Sizes:`);
      console.log(`  JS: ${(jsSize / 1024).toFixed(2)} KB`);
      console.log(`  CSS: ${(cssSize / 1024).toFixed(2)} KB`);
      console.log(`  Total: ${((jsSize + cssSize) / 1024).toFixed(2)} KB`);
    }
    
    console.log('✅ Build completed successfully!');
  } catch (error) {
    console.error('❌ Build failed:', error);
    process.exit(1);
  }
}

// Watch mode for development
async function watch() {
  try {
    console.log('👀 Starting watch mode with StyleX...');
    const ctx = await esbuild.context(buildOptions);
    await ctx.watch();
    console.log(`📁 Watching for changes to ${entry}`);
    console.log(`📂 Output directory: ../backend/static/`);
    console.log('🎨 StyleX compilation enabled');
  } catch (error) {
    console.error('❌ Watch mode failed:', error);
    process.exit(1);
  }
}

// Determine mode based on arguments
if (process.argv.includes('--production')) {
  process.env.NODE_ENV = 'production';
  build();
} else if (process.argv.includes('--watch')) {
  watch();
} else {
  // Default to watch mode in development
  watch();
}