const { chromium } = require('playwright');

async function testPiecesAfterBackendFix() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Enable console logging for debug messages
  page.on('console', msg => {
    const text = msg.text();
    if (msg.type() === 'log' && (
      text.includes('🎴') || 
      text.includes('🃏') || 
      text.includes('📡') || 
      text.includes('🎯') ||
      text.includes('🎮') ||
      text.includes('GameService') ||
      text.includes('myHand') ||
      text.includes('phase_change')
    )) {
      console.log('📋 Console:', text);
    }
  });
  
  try {
    console.log('🚀 Testing pieces display after backend fix...\n');
    
    // Navigate and enter name
    await page.goto('http://localhost:5050');
    await page.waitForTimeout(1000);
    
    // Enter name
    const nameInput = await page.waitForSelector('input[type="text"]');
    await nameInput.fill('TestPlayer');
    console.log('✅ Entered player name');
    
    // Enter lobby
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1000);
    console.log('✅ Entered lobby');
    
    // Create room
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(1000);
    console.log('✅ Created room');
    
    // Start game (NO BOT NEEDED)
    console.log('🎮 Starting game...');
    await page.click('button:has-text("Start Game")');
    
    // Wait for game page
    await page.waitForURL('**/game/**', { timeout: 5000 });
    console.log('✅ Navigated to game page');
    
    // Wait for preparation phase
    console.log('⏳ Waiting for preparation phase...');
    
    // Wait for preparation UI
    try {
      await page.waitForSelector('.preparation-content', { timeout: 10000 });
      console.log('✅ Preparation phase detected');
    } catch (e) {
      console.log('❌ Preparation phase not found');
    }
    
    // Wait for dealing animation
    await page.waitForTimeout(4000);
    
    // Check for pieces
    const piecesByClass = await page.locator('.game-piece').count();
    const piecesInTray = await page.locator('.piece-tray .game-piece').count();
    const pieceCharacters = await page.locator('.game-piece__character').count();
    
    console.log(`\n📊 Pieces found:`);
    console.log(`   By .game-piece class: ${piecesByClass}`);
    console.log(`   In .piece-tray: ${piecesInTray}`);
    console.log(`   By .game-piece__character: ${pieceCharacters}`);
    
    const totalPieces = piecesByClass;
    
    if (totalPieces > 0) {
      console.log(`\n✅ SUCCESS: ${totalPieces} pieces are displayed!`);
      console.log('🎉 Backend fix is working - pieces are now visible!\n');
      
      // Get piece details
      const pieceDetails = await page.evaluate(() => {
        const pieces = document.querySelectorAll('.game-piece');
        const details = [];
        pieces.forEach((piece, i) => {
          const character = piece.querySelector('.game-piece__character');
          const value = piece.querySelector('.game-piece__value');
          details.push({
            index: i,
            character: character?.textContent || 'unknown',
            value: value?.textContent || 'unknown',
            color: piece.classList.contains('game-piece--red') ? 'red' : 'black'
          });
        });
        return details;
      });
      
      console.log('Piece details:');
      pieceDetails.slice(0, 3).forEach(p => {
        console.log(`   Piece ${p.index + 1}: ${p.character} (${p.value}) - ${p.color}`);
      });
      if (pieceDetails.length > 3) {
        console.log(`   ... and ${pieceDetails.length - 3} more pieces`);
      }
      
      // Check game state
      const gameState = await page.evaluate(() => {
        const gs = window.gameService;
        if (gs) {
          const state = gs.getState();
          return {
            phase: state.phase,
            handLength: state.myHand?.length || 0,
            playerName: state.playerName
          };
        }
        return null;
      });
      console.log('\nGame state:', gameState);
      
    } else {
      console.log('\n❌ FAILED: No pieces found');
      console.log('The backend fix may not be working correctly.\n');
      
      // Debug info
      const debugInfo = await page.evaluate(() => {
        const gs = window.gameService;
        if (gs) {
          const state = gs.getState();
          return {
            phase: state.phase,
            myHandLength: state.myHand?.length || 0,
            myHand: state.myHand,
            playerName: state.playerName,
            players: state.players
          };
        }
        return { error: 'gameService not found' };
      });
      console.log('Debug info:', JSON.stringify(debugInfo, null, 2));
      
      // Take screenshot
      await page.screenshot({ path: 'backend-fix-test.png' });
      console.log('\nScreenshot saved as backend-fix-test.png');
    }
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
    console.log('\n🏁 Test completed');
  }
}

// Run the test
testPiecesAfterBackendFix();