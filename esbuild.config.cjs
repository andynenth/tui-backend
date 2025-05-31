// esbuild.config.cjs
const esbuild = require('esbuild');

esbuild.context({
  entryPoints: ['./frontend/main.js'],
  bundle: true,
  outfile: './build/bundle.js',
  loader: { '.js': 'js' },
  minify: true,
  sourcemap: false,
}).then(ctx => {
  return ctx.watch();
}).then(() => {
  console.log('👀 Watching for changes...');
}).catch(() => process.exit(1));
