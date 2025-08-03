#!/usr/bin/env node

/**
 * Script to update component imports to use StyleX versions
 * Run with: node scripts/update-stylex-imports.js
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

// Directories to search for files
const SEARCH_DIRS = [
  'src/pages',
  'src/components',
  'src/hooks',
];

// File extensions to process
const FILE_EXTENSIONS = ['.js', '.jsx', '.ts', '.tsx'];

/**
 * Recursively find all files in a directory
 */
function findFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      // Skip node_modules and build directories
      if (!file.includes('node_modules') && !file.includes('build') && !file.includes('dist')) {
        findFiles(filePath, fileList);
      }
    } else if (FILE_EXTENSIONS.some(ext => filePath.endsWith(ext))) {
      fileList.push(filePath);
    }
  });
  
  return fileList;
}

/**
 * Update imports in a single file
 */
function updateFileImports(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;
  
  MIGRATED_COMPONENTS.forEach(component => {
    // Match various import patterns
    const patterns = [
      // import Component from './Component'
      new RegExp(`(import\\s+${component}\\s+from\\s+['"])(\\..*?/${component})(['"])`, 'g'),
      // import Component from '../Component'
      new RegExp(`(import\\s+${component}\\s+from\\s+['"])(\\..*?/${component})(['"])`, 'g'),
      // import { Component } from './shared'
      new RegExp(`(import\\s+{[^}]*${component}[^}]*}\\s+from\\s+['"])(\\..*?/shared)(['"])`, 'g'),
    ];
    
    patterns.forEach(pattern => {
      const matches = content.match(pattern);
      if (matches) {
        matches.forEach(match => {
          // Don't update if it already has .stylex extension
          if (!match.includes('.stylex')) {
            const newMatch = match.replace(
              new RegExp(`(['"])(\\..*?/${component})(['"])`, 'g'),
              `$1$2.stylex$3`
            );
            
            // Special handling for shared imports
            if (match.includes('/shared')) {
              // Check if we need to update the shared import
              // For now, keep shared imports as-is since shared/index might handle it
              return;
            }
            
            content = content.replace(match, newMatch);
            modified = true;
            console.log(`  Updated: ${component} import in ${path.basename(filePath)}`);
          }
        });
      }
    });
  });
  
  if (modified) {
    fs.writeFileSync(filePath, content, 'utf8');
    return true;
  }
  
  return false;
}

/**
 * Main execution
 */
function main() {
  console.log('🎨 Updating component imports to use StyleX versions...\n');
  
  let totalFiles = 0;
  let updatedFiles = 0;
  
  SEARCH_DIRS.forEach(dir => {
    const fullPath = path.join(process.cwd(), dir);
    
    if (!fs.existsSync(fullPath)) {
      console.log(`⚠️  Directory not found: ${dir}`);
      return;
    }
    
    console.log(`📁 Searching in ${dir}...`);
    const files = findFiles(fullPath);
    
    files.forEach(file => {
      totalFiles++;
      if (updateFileImports(file)) {
        updatedFiles++;
      }
    });
  });
  
  console.log('\n✅ Import update complete!');
  console.log(`   Total files scanned: ${totalFiles}`);
  console.log(`   Files updated: ${updatedFiles}`);
  console.log('\n📝 Next steps:');
  console.log('   1. Run "npm run build" to test the build');
  console.log('   2. Run "npm run lint" to check for any issues');
  console.log('   3. Test the application thoroughly');
}

// Run the script
main();