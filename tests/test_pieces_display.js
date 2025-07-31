const { chromium } = require('playwright');

async function testPiecesDisplay() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('🧪 Testing pieces display in preparation phase...\n');
  
  try {
    // Navigate to home page
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    // Fill player name first
    console.log('📝 Entering player name...');
    await page.fill('input[type="text"]', 'TestPlayer');
    
    // Enter lobby
    console.log('📍 Entering lobby...');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForLoadState('networkidle');
    
    // Create room
    console.log('📝 Creating room...');
    await page.click('button:has-text("Create Room")');
    await page.waitForLoadState('networkidle');
    
    // Get room code
    const roomCode = page.url().split('/').pop();
    console.log(`✅ Room created: ${roomCode}`);
    
    // Add bot
    await page.click('button:has-text("Add Bot")');
    await page.waitForTimeout(500);
    
    // Start game
    await page.click('button:has-text("Start Game")');
    console.log('✅ Game started');
    
    // Wait for navigation to game page
    await page.waitForURL(/\/game\//);
    console.log('✅ Navigated to game page');
    
    // Wait for preparation phase
    await page.waitForTimeout(2000);
    
    // Check for pieces in the PieceTray
    const pieces = await page.locator('.piece-tray .game-piece').count();
    console.log(`\n📊 Pieces found: ${pieces}`);
    
    if (pieces > 0) {
      console.log('✅ SUCCESS: Pieces are displayed in preparation phase!');
      
      // Get details of first few pieces
      for (let i = 0; i < Math.min(3, pieces); i++) {
        const pieceElement = page.locator('.piece-tray .game-piece').nth(i);
        const character = await pieceElement.locator('.game-piece__character').textContent();
        const value = await pieceElement.locator('.game-piece__value').textContent();
        const classes = await pieceElement.getAttribute('class');
        const color = classes.includes('red') ? 'red' : 'black';
        console.log(`   Piece ${i + 1}: ${character} (${color}) - Value: ${value}`);
      }
    } else {
      console.log('❌ FAILED: No pieces found in preparation phase');
      
      // Debug info
      const pieceTrayExists = await page.locator('.piece-tray').count();
      console.log(`   PieceTray component exists: ${pieceTrayExists > 0}`);
      
      const gamePhase = await page.evaluate(() => {
        const gameService = window.gameService;
        return gameService ? gameService.getState().phase : 'unknown';
      });
      console.log(`   Current game phase: ${gamePhase}`);
      
      const myHand = await page.evaluate(() => {
        const gameService = window.gameService;
        return gameService ? gameService.getState().myHand : [];
      });
      console.log(`   myHand length: ${myHand.length}`);
      console.log(`   myHand data:`, JSON.stringify(myHand, null, 2));
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

testPiecesDisplay();