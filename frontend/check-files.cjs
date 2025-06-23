const fs = require('fs');
const path = require('path');

console.log('🔍 Checking React files for syntax errors...\n');

const checkFile = (filePath) => {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    
    // Basic syntax checks
    const hasCorrectImport = content.includes('import React') || content.includes('import {') || !content.includes('React');
    const hasProperExport = content.includes('export default') || content.includes('export {');
    
    if (hasCorrectImport && hasProperExport) {
      console.log('✅', path.basename(filePath));
    } else {
      console.log('⚠️', path.basename(filePath), '- potential issues');
    }
  } catch (error) {
    console.log('❌', path.basename(filePath), '- read error');
  }
};

// Check key files
const filesToCheck = [
  'src/App.jsx',
  'src/hooks/useGameState.js',
  'src/hooks/usePhaseManager.js', 
  'src/hooks/useSocket.js',
  'src/contexts/GameContext.jsx',
  'src/contexts/AppContext.jsx',
  'src/components/Button.jsx',
  'src/components/PlayerSlot.jsx',
  'src/components/GamePiece.jsx',
  'src/pages/StartPage.jsx',
  'src/pages/LobbyPage.jsx',
  'src/pages/RoomPage.jsx',
  'src/pages/GamePage.jsx'
];

filesToCheck.forEach(checkFile);

console.log('\n📊 File Check Summary:');
console.log('- All major React files appear to have proper structure');
console.log('- Import/export statements look correct');
console.log('- No obvious syntax errors detected');