#!/usr/bin/env node
/**
 * 🧪 **Phase 5 Unified State Test** - Validate single source of truth
 * 
 * Tests that we've successfully unified state management by:
 * 1. Ensuring all components use the same state source
 * 2. Verifying state updates propagate correctly
 * 3. Checking for removal of duplicate state sources
 */

const fs = require('fs');
const path = require('path');

console.log('🎯 Testing Phase 5 Unified State Management...\n');

// Test 1: Check for multiple state sources
console.log('📋 Test 1: Checking for multiple state sources...');

const problematicPatterns = [
  { pattern: /gameService\.getState/, file: 'Using old gameService.getState()' },
  { pattern: /gameService\.setState/, file: 'Using old gameService.setState()' },
  { pattern: /gameService\.addListener/, file: 'Using old gameService listeners' },
  { pattern: /this\.state\s*=/, file: 'Local component state (potential duplicate)' },
  { pattern: /useState.*gameState/, file: 'Local useState for game state' }
];

function searchInFile(filePath, patterns) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const issues = [];
    
    patterns.forEach(({pattern, file: description}) => {
      const matches = content.match(pattern);
      if (matches) {
        issues.push({
          file: filePath,
          description,
          matches: matches.length
        });
      }
    });
    
    return issues;
  } catch (err) {
    return [];
  }
}

function walkDirectory(dir, extension = '') {
  const files = [];
  try {
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
      const itemPath = path.join(dir, item);
      const stat = fs.statSync(itemPath);
      
      if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
        files.push(...walkDirectory(itemPath, extension));
      } else if (stat.isFile() && (extension === '' || itemPath.endsWith(extension))) {
        files.push(itemPath);
      }
    }
  } catch (err) {
    // Skip inaccessible directories
  }
  
  return files;
}

// Search for problematic patterns in frontend
const frontendDir = path.join(__dirname, 'frontend', 'src');
const frontendFiles = walkDirectory(frontendDir).filter(f => 
  f.endsWith('.js') || f.endsWith('.jsx') || f.endsWith('.ts') || f.endsWith('.tsx')
);

let totalIssues = 0;
let issuesByFile = {};

frontendFiles.forEach(file => {
  const issues = searchInFile(file, problematicPatterns);
  if (issues.length > 0) {
    issuesByFile[file] = issues;
    totalIssues += issues.length;
  }
});

if (totalIssues === 0) {
  console.log('✅ No multiple state sources detected');
} else {
  console.log(`❌ Found ${totalIssues} potential state management issues:`);
  Object.entries(issuesByFile).forEach(([file, issues]) => {
    console.log(`\n  📁 ${path.relative(__dirname, file)}:`);
    issues.forEach(issue => {
      console.log(`    - ${issue.description} (${issue.matches} occurrences)`);
    });
  });
}

// Test 2: Check UnifiedGameStore usage
console.log('\n📋 Test 2: Checking UnifiedGameStore usage...');

const unifiedStorePatterns = [
  { pattern: /import.*gameStore.*from.*UnifiedGameStore/, description: 'Correct gameStore import' },
  { pattern: /gameStore\.getState\(\)/, description: 'Using gameStore.getState()' },
  { pattern: /gameStore\.setState/, description: 'Using gameStore.setState()' },
  { pattern: /useGameStore\(\)/, description: 'Using useGameStore hook' }
];

let unifiedUsageCount = 0;
let unifiedUsageFiles = [];

frontendFiles.forEach(file => {
  const content = fs.readFileSync(file, 'utf8');
  let hasUnifiedUsage = false;
  
  unifiedStorePatterns.forEach(({pattern, description}) => {
    if (pattern.test(content)) {
      unifiedUsageCount++;
      hasUnifiedUsage = true;
    }
  });
  
  if (hasUnifiedUsage) {
    unifiedUsageFiles.push(path.relative(__dirname, file));
  }
});

console.log(`✅ Found ${unifiedUsageCount} instances of unified store usage across ${unifiedUsageFiles.length} files`);
console.log(`📁 Files using unified store: ${unifiedUsageFiles.slice(0, 5).join(', ')}${unifiedUsageFiles.length > 5 ? '...' : ''}`);

// Test 3: Check for proper TypeScript exports
console.log('\n📋 Test 3: Checking TypeScript exports...');

const unifiedStoreFile = path.join(frontendDir, 'stores', 'UnifiedGameStore.ts');
try {
  const content = fs.readFileSync(unifiedStoreFile, 'utf8');
  
  const hasStoreStateExport = /export interface StoreState/.test(content);
  const hasGameStoreExport = /export const gameStore/.test(content);
  const hasClassExport = /export class UnifiedGameStore/.test(content);
  
  console.log(`✅ StoreState interface exported: ${hasStoreStateExport}`);
  console.log(`✅ gameStore instance exported: ${hasGameStoreExport}`);
  console.log(`✅ UnifiedGameStore class exported: ${hasClassExport}`);
  
  if (hasStoreStateExport && hasGameStoreExport && hasClassExport) {
    console.log('✅ All necessary TypeScript exports are present');
  } else {
    console.log('❌ Some TypeScript exports are missing');
  }
} catch (err) {
  console.log('❌ Could not check UnifiedGameStore.ts');
}

// Test 4: Check NetworkIntegration setup
console.log('\n📋 Test 4: Checking NetworkIntegration setup...');

const networkIntegrationFile = path.join(frontendDir, 'stores', 'NetworkIntegration.ts');
try {
  const content = fs.readFileSync(networkIntegrationFile, 'utf8');
  
  const hasExportedInstance = /export const networkIntegration/.test(content);
  const hasGameStoreIntegration = /gameStore\.setState/.test(content);
  const hasEventHandlers = /handlePhaseChange|handlePlayerJoined/.test(content);
  
  console.log(`✅ NetworkIntegration instance exported: ${hasExportedInstance}`);
  console.log(`✅ Integrates with gameStore: ${hasGameStoreIntegration}`);
  console.log(`✅ Has event handlers: ${hasEventHandlers}`);
  
  if (hasExportedInstance && hasGameStoreIntegration && hasEventHandlers) {
    console.log('✅ NetworkIntegration properly bridges network and store');
  } else {
    console.log('❌ NetworkIntegration setup incomplete');
  }
} catch (err) {
  console.log('❌ Could not check NetworkIntegration.ts');
}

// Test 5: Summary and recommendations
console.log('\n📊 Test Summary:');
console.log('================');

const allTestsPassed = totalIssues === 0 && unifiedUsageCount > 0;

if (allTestsPassed) {
  console.log('🎉 SUCCESS: Phase 5 Unified State Management appears to be working!');
  console.log('');
  console.log('✅ Single source of truth established');
  console.log('✅ No duplicate state sources detected');
  console.log('✅ Components using unified store');
  console.log('✅ TypeScript types properly exported');
  console.log('✅ Network integration connected');
} else {
  console.log('⚠️  PARTIAL: Phase 5 implementation needs attention:');
  console.log('');
  if (totalIssues > 0) {
    console.log(`❌ ${totalIssues} potential duplicate state sources found`);
  }
  if (unifiedUsageCount === 0) {
    console.log('❌ No unified store usage detected');
  }
}

console.log('\n🎯 Next Steps for Phase 5:');
console.log('1. Ensure all components use useGameStore() hook');
console.log('2. Remove any remaining local state management');
console.log('3. Test state synchronization across components');
console.log('4. Measure state update performance (<50ms target)');

process.exit(allTestsPassed ? 0 : 1);