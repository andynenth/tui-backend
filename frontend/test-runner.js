// ===== Create frontend/test-runner.js =====
// Simple test runner for manual verification during migration

import { promises as fs } from 'fs';
import path from 'path';

console.log('🧪 Running migration verification tests...\n');

// Test 1: Check that network module exists
console.log('1️⃣ Checking network module structure...');
try {
  const networkFiles = [
    './network/SocketManager.js',
    './network/ConnectionMonitor.js',
    './network/MessageQueue.js',
    './network/ReconnectionManager.js',
    './network/index.js',
    './network/adapters/LegacyAdapter.js'
  ];

  let allExist = true;
  for (const file of networkFiles) {
    try {
      await fs.access(file);
      console.log(`   ✅ ${file}`);
    } catch {
      console.log(`   ❌ ${file} - NOT FOUND`);
      allExist = false;
    }
  }

  if (!allExist) {
    console.log('\n❌ Network module structure incomplete!');
    process.exit(1);
  }
} catch (error) {
  console.error('Error checking network module:', error);
  process.exit(1);
}

// Test 2: Check for old socketManager imports
console.log('\n2️⃣ Checking for old socketManager imports...');
const filesToCheck = [
  './scenes/RoomScene.js',
  './scenes/LobbyScene.js', 
  './scenes/GameScene.js',
  './components/ConnectionStatus.js'
];

let hasOldImports = false;
for (const file of filesToCheck) {
  try {
    const content = await fs.readFile(file, 'utf-8');
    if (content.includes('from \'../socketManager.js\'') || 
        content.includes('from "../socketManager.js"')) {
      console.log(`   ❌ ${file} - Still using old import`);
      hasOldImports = true;
    } else if (content.includes('from \'../network/index.js\'') ||
               content.includes('from "../network/index.js"')) {
      console.log(`   ✅ ${file} - Using new import`);
    } else {
      console.log(`   ⚠️  ${file} - No socket imports found`);
    }
  } catch (error) {
    console.log(`   ⚠️  ${file} - Could not read file`);
  }
}

if (hasOldImports) {
  console.log('\n⚠️  Some files still use old imports!');
}

// Test 3: Check if old socketManager.js exists
console.log('\n3️⃣ Checking for old socketManager.js...');
try {
  await fs.access('./socketManager.js');
  console.log('   ⚠️  Old socketManager.js still exists');
  console.log('   Run: mv frontend/socketManager.js frontend/socketManager.old.js');
} catch {
  console.log('   ✅ Old socketManager.js has been removed/renamed');
}

console.log('\n✅ Migration verification complete!');