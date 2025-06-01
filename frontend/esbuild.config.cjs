// frontend/esbuild.config.cjs
const esbuild = require('esbuild');
require('dotenv').config({ path: '../.env' }); // 👈 โหลด .env จาก root

const entry = process.env.ESBUILD_ENTRY || './main.js';
const outfile = process.env.ESBUILD_OUT || '../backend/static/bundle.js';

esbuild.context({
  entryPoints: [entry],
  bundle: true,
  outfile,
  loader: { '.js': 'js' },
  minify: true,
  sourcemap: true,
}).then(ctx => {
  return ctx.watch();
}).then(() => {
  console.log(`👀 Watching for changes to ${entry}, output to ${outfile}`);
}).catch(() => process.exit(1));
