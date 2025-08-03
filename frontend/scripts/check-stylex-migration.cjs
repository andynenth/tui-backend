#!/usr/bin/env node

/**
 * Script to check the status of StyleX migration
 * Run with: node scripts/check-stylex-migration.js
 */

const fs = require('fs');
const path = require('path');

// Components that have been migrated to StyleX
const MIGRATED_COMPONENTS = [
  // Core components
  'Button',
  'Modal',
  'Input',
  'ToastNotification',
  'LoadingOverlay',
  
  // Game shared components
  'GamePiece',
  'PlayerAvatar',
  'PieceTray',
  'FooterTimer',
  'GameLayout',
  'GameContainer',
  
  // Game phase components
  'WaitingUI',
  'PreparationUI',
  'RoundStartUI',
  'DeclarationUI',
  'ScoringUI',
  'GameOverUI',
];

// Components still using old styling
const PENDING_COMPONENTS = [
  'TurnUI',
  'TurnResultsUI',
  'ConnectionIndicator',
  'ErrorBoundary',
];

// CSS files to be removed after migration
const CSS_FILES = [
  'src/styles/index.css',
  'src/styles/theme.css',
  'src/styles/base.css',
  'src/styles/components/',
  'src/styles/game/',
];

/**
 * Check if a file exists
 */
function checkFile(filePath) {
  return fs.existsSync(path.join(process.cwd(), filePath));
}

/**
 * Get file size in KB
 */
function getFileSize(filePath) {
  const fullPath = path.join(process.cwd(), filePath);
  if (fs.existsSync(fullPath)) {
    const stats = fs.statSync(fullPath);
    return (stats.size / 1024).toFixed(2);
  }
  return 0;
}

/**
 * Count lines in a file
 */
function countLines(filePath) {
  const fullPath = path.join(process.cwd(), filePath);
  if (fs.existsSync(fullPath)) {
    const content = fs.readFileSync(fullPath, 'utf8');
    return content.split('\n').length;
  }
  return 0;
}

/**
 * Find all CSS files in a directory
 */
function findCSSFiles(dir) {
  const files = [];
  
  if (!fs.existsSync(dir)) {
    return files;
  }
  
  function walk(currentDir) {
    const entries = fs.readdirSync(currentDir);
    
    entries.forEach(entry => {
      const fullPath = path.join(currentDir, entry);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory() && !entry.includes('node_modules')) {
        walk(fullPath);
      } else if (entry.endsWith('.css')) {
        files.push(fullPath);
      }
    });
  }
  
  walk(dir);
  return files;
}

/**
 * Main execution
 */
function main() {
  console.log('🎨 StyleX Migration Status Report\n');
  console.log('=' .repeat(60));
  
  // Check migrated components
  console.log('\n✅ Migrated Components:');
  let migratedCount = 0;
  MIGRATED_COMPONENTS.forEach(component => {
    const stylexPath = `src/components/${component}.stylex.jsx`;
    const gameStylexPath = `src/components/game/${component}.stylex.jsx`;
    const sharedStylexPath = `src/components/game/shared/${component}.stylex.jsx`;
    
    if (checkFile(stylexPath) || checkFile(gameStylexPath) || checkFile(sharedStylexPath)) {
      console.log(`   ✓ ${component}`);
      migratedCount++;
    } else {
      console.log(`   ⚠️  ${component} (StyleX file not found)`);
    }
  });
  
  // Check pending components
  console.log('\n⏳ Pending Components:');
  PENDING_COMPONENTS.forEach(component => {
    const jsxPath = `src/components/${component}.jsx`;
    const gameJsxPath = `src/components/game/${component}.jsx`;
    
    if (checkFile(jsxPath) || checkFile(gameJsxPath)) {
      console.log(`   • ${component}`);
    }
  });
  
  // Check CSS files
  console.log('\n📁 CSS Files Status:');
  const allCSSFiles = findCSSFiles('src');
  let totalCSSSize = 0;
  let totalCSSLines = 0;
  
  allCSSFiles.forEach(file => {
    const relativePath = path.relative(process.cwd(), file);
    const size = getFileSize(relativePath);
    const lines = countLines(relativePath);
    totalCSSSize += parseFloat(size);
    totalCSSLines += lines;
    console.log(`   • ${relativePath} (${size} KB, ${lines} lines)`);
  });
  
  // Check StyleX token files
  console.log('\n🎯 StyleX Design System:');
  const tokenFiles = [
    'src/design-system/tokens.stylex.js',
    'src/design-system/common.stylex.js',
    'src/design-system/utils.stylex.js',
  ];
  
  tokenFiles.forEach(file => {
    if (checkFile(file)) {
      const size = getFileSize(file);
      const lines = countLines(file);
      console.log(`   ✓ ${path.basename(file)} (${size} KB, ${lines} lines)`);
    } else {
      console.log(`   ✗ ${path.basename(file)} (not found)`);
    }
  });
  
  // Summary
  console.log('\n' + '=' .repeat(60));
  console.log('📊 Migration Summary:\n');
  console.log(`   Components migrated: ${migratedCount}/${MIGRATED_COMPONENTS.length}`);
  console.log(`   Components pending: ${PENDING_COMPONENTS.length}`);
  console.log(`   Progress: ${Math.round((migratedCount / (MIGRATED_COMPONENTS.length + PENDING_COMPONENTS.length)) * 100)}%`);
  console.log(`   CSS files remaining: ${allCSSFiles.length} (${totalCSSSize.toFixed(2)} KB, ${totalCSSLines} lines)`);
  
  // Recommendations
  console.log('\n💡 Next Steps:');
  if (PENDING_COMPONENTS.length > 0) {
    console.log('   1. Migrate remaining components to StyleX');
  }
  if (allCSSFiles.length > 0) {
    console.log('   2. Remove legacy CSS files after confirming StyleX is working');
  }
  console.log('   3. Run "npm run build" to create production bundle');
  console.log('   4. Test application thoroughly');
  console.log('   5. Remove Tailwind and PostCSS dependencies');
  
  // Build size comparison (if available)
  const distBundle = 'dist/bundle.js';
  const distStyles = 'dist/styles.css';
  
  if (checkFile(distBundle)) {
    console.log('\n📦 Current Bundle Sizes:');
    console.log(`   JavaScript: ${getFileSize(distBundle)} KB`);
    if (checkFile(distStyles)) {
      console.log(`   StyleX CSS: ${getFileSize(distStyles)} KB`);
    }
  }
}

// Run the script
main();