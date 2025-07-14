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

esbuild
  .context({
    entryPoints: [entry],
    bundle: true,
    outdir: '../backend/static',
    entryNames: 'bundle',
    loader: {
      '.js': 'jsx',
      '.jsx': 'jsx',
      '.ts': 'ts',
      '.tsx': 'tsx',
      '.css': 'css',
    },
    jsx: 'automatic',
    minify: true,
    sourcemap: true,
    plugins: [cssPlugin],
  })
  .then((ctx) => {
    return ctx.watch();
  })
  .then(() => {
    console.log(
      `👀 Watching for changes to ${entry}, output to ../backend/static/`
    );
  })
  .catch(() => process.exit(1));
