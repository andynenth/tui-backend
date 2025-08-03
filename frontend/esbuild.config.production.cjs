const esbuild = require('esbuild');
const stylexPlugin = require('@stylexjs/esbuild-plugin').default;
const path = require('path');
const fs = require('fs');

// Clean output directory
const outdir = 'dist';
if (fs.existsSync(outdir)) {
  fs.rmSync(outdir, { recursive: true, force: true });
}
fs.mkdirSync(outdir, { recursive: true });

// Copy public assets
const publicDir = 'public';
if (fs.existsSync(publicDir)) {
  fs.cpSync(publicDir, outdir, { recursive: true });
}

// Copy index.html and update paths for production
let indexHtml = fs.readFileSync('index.html', 'utf8');
indexHtml = indexHtml
  .replace('/main.js', '/bundle.js')
  .replace('<!-- StyleX styles will be injected here -->', '<link rel="stylesheet" href="/styles.css">');
fs.writeFileSync(path.join(outdir, 'index.html'), indexHtml);

// Build configuration
esbuild.build({
  entryPoints: ['main.js'],
  bundle: true,
  minify: true,
  sourcemap: true,
  outfile: 'dist/bundle.js',
  platform: 'browser',
  target: ['es2020'],
  loader: {
    '.js': 'jsx',
    '.jsx': 'jsx',
    '.svg': 'file',
    '.png': 'file',
    '.jpg': 'file',
    '.jpeg': 'file',
    '.gif': 'file',
    '.woff': 'file',
    '.woff2': 'file',
    '.ttf': 'file',
    '.eot': 'file',
  },
  define: {
    'process.env.NODE_ENV': '"production"',
  },
  plugins: [
    stylexPlugin({
      dev: false,
      generatedCSSFileName: 'dist/styles.css',
      stylexImports: ['@stylexjs/stylex'],
      unstable_moduleResolution: {
        type: 'commonJS',
        rootDir: __dirname,
      },
    }),
  ],
  metafile: true,
}).then(result => {
  // Write metafile for bundle analysis
  fs.writeFileSync('dist/meta.json', JSON.stringify(result.metafile));
  
  // Calculate bundle sizes
  const jsSize = fs.statSync('dist/bundle.js').size;
  const cssSize = fs.existsSync('dist/styles.css') ? fs.statSync('dist/styles.css').size : 0;
  
  console.log('✅ Production build complete!');
  console.log('📦 Bundle sizes:');
  console.log(`   JavaScript: ${(jsSize / 1024).toFixed(2)} KB`);
  console.log(`   CSS: ${(cssSize / 1024).toFixed(2)} KB`);
  console.log(`   Total: ${((jsSize + cssSize) / 1024).toFixed(2)} KB`);
  
  // Analyze imports
  const outputs = result.metafile.outputs;
  const mainOutput = outputs['dist/bundle.js'];
  if (mainOutput && mainOutput.imports) {
    const stylexImports = mainOutput.imports.filter(imp => 
      imp.path.includes('stylex')
    );
    console.log(`\n📊 StyleX components included: ${stylexImports.length}`);
  }
}).catch(() => process.exit(1));