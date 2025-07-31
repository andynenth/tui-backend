const { chromium } = require('playwright');

async function testPiecesDisplay() {
  console.log('🎮 Starting Liap Tui pieces display test...\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 50
  });
  
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'log' && msg.text().includes('GameService')) {
      console.log('📋 Console:', msg.text());
    }
  });
  
  try {
    // 1. Go to home page
    console.log('1️⃣ Navigating to home page...');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    // 2. Enter player name
    console.log('2️⃣ Entering player name...');
    await page.fill('input[placeholder="Enter your name"]', 'Player1');
    
    // 3. Click Enter Lobby
    console.log('3️⃣ Clicking Enter Lobby...');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForURL('**/lobby');
    
    // 4. Create a new room
    console.log('4️⃣ Creating new room...');
    await page.click('button:has-text("Create Room")');
    await page.waitForURL('**/room/**');
    
    // Get room code
    const roomUrl = page.url();
    const roomCode = roomUrl.split('/').pop();
    console.log(`   ✅ Room created with code: ${roomCode}`);
    
    // 5. Add a bot
    console.log('5️⃣ Adding bot player...');
    await page.click('button:has-text("Add Bot")');
    await page.waitForTimeout(500);
    
    // 6. Start the game
    console.log('6️⃣ Starting game...');
    await page.click('button:has-text("Start Game")');
    
    // Wait for navigation to game page
    console.log('7️⃣ Waiting for game page...');
    await page.waitForURL('**/game/**', { timeout: 10000 });
    console.log('   ✅ Navigated to game page');
    
    // Wait for preparation phase (dealing animation)
    console.log('8️⃣ Waiting for preparation phase...');
    await page.waitForTimeout(4000); // Wait for dealing animation
    
    // Check for pieces
    console.log('9️⃣ Checking for pieces display...\n');
    
    // Check if PieceTray exists
    const pieceTrayExists = await page.locator('.piece-tray').count() > 0;
    console.log(`📊 PieceTray component exists: ${pieceTrayExists}`);
    
    // Count pieces
    const pieceCount = await page.locator('.piece-tray .game-piece').count();
    console.log(`📊 Number of pieces found: ${pieceCount}`);
    
    if (pieceCount > 0) {
      console.log('\n✅ SUCCESS: Pieces are displayed correctly!\n');
      
      // Get details of each piece
      console.log('📋 Piece details:');
      for (let i = 0; i < pieceCount; i++) {
        const piece = page.locator('.piece-tray .game-piece').nth(i);
        const classes = await piece.getAttribute('class');
        const isRed = classes.includes('red');
        const character = await piece.locator('.game-piece__character').textContent();
        const value = await piece.locator('.game-piece__value').textContent();
        
        console.log(`   Piece ${i + 1}: ${character} (${isRed ? 'RED' : 'BLACK'}) - Value: ${value}`);
      }
    } else {
      console.log('\n❌ FAILED: No pieces found!\n');
      
      // Debug information
      const gameState = await page.evaluate(() => {
        const gs = window.gameService;
        if (gs) {
          const state = gs.getState();
          return {
            phase: state.phase,
            myHandLength: state.myHand?.length || 0,
            myHand: state.myHand || []
          };
        }
        return null;
      });
      
      console.log('🔍 Debug info:');
      console.log('   Game state:', JSON.stringify(gameState, null, 2));
      
      // Take screenshot
      await page.screenshot({ path: 'pieces-display-debug.png' });
      console.log('   Screenshot saved: pieces-display-debug.png');
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    await page.screenshot({ path: 'test-error.png' });
  } finally {
    await browser.close();
    console.log('\n🏁 Test completed');
  }
}

// Run the test
testPiecesDisplay().catch(console.error);