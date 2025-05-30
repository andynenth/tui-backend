// esbuild.config.js
const { build } = require('esbuild');

build({
  entryPoints: ['./frontend/main.js'],
  bundle: true,
  outfile: './build/bundle.js',
  loader: { '.js': 'js' },
  minify: true,
  sourcemap: false,
}).catch(() => process.exit(1));
