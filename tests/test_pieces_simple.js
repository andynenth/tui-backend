const { chromium } = require('playwright');

async function testPiecesDisplay() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // Enable console logging for our debug messages
  page.on('console', msg => {
    const text = msg.text();
    if (msg.type() === 'log' && (
      text.includes('🎴') || 
      text.includes('🃏') || 
      text.includes('📡') || 
      text.includes('🎯') ||
      text.includes('🎮')
    )) {
      console.log('📋 Console:', text);
    }
  });
  
  try {
    // Navigate and enter name
    await page.goto('http://localhost:5050');
    await page.waitForTimeout(1000);
    
    // Enter name
    const nameInput = await page.waitForSelector('input[type="text"]');
    await nameInput.fill('TestPlayer');
    
    // Enter lobby
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1000);
    
    // Create room
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(1000);
    
    // Start game (NO BOT NEEDED)
    await page.click('button:has-text("Start Game")');
    
    // Wait for game page
    await page.waitForURL('**/game/**', { timeout: 5000 });
    console.log('✅ Navigated to game page');
    
    // Wait for preparation phase
    console.log('⏳ Waiting for preparation phase...');
    
    // Wait for the waiting UI to disappear and preparation to start
    try {
      await page.waitForSelector('.preparation-content', { timeout: 10000 });
      console.log('✅ Preparation phase detected');
    } catch (e) {
      console.log('❌ Preparation phase not found');
    }
    
    // Additional wait for dealing animation
    await page.waitForTimeout(4000);
    
    // Check for pieces in different ways
    const piecesByClass = await page.locator('.game-piece').count();
    const piecesInTray = await page.locator('.piece-tray .game-piece').count();
    const pieceCharacters = await page.locator('.game-piece__character').count();
    
    console.log(`\n📊 Pieces found:`);
    console.log(`   By .game-piece class: ${piecesByClass}`);
    console.log(`   In .piece-tray: ${piecesInTray}`);
    console.log(`   By .game-piece__character: ${pieceCharacters}`);
    
    const pieces = piecesByClass;
    
    if (pieces > 0) {
      console.log('✅ SUCCESS: Pieces are displayed!');
      
      // Check game state
      const gameState = await page.evaluate(() => {
        const gs = window.gameService;
        if (gs) {
          const state = gs.getState();
          return {
            phase: state.phase,
            handLength: state.myHand?.length || 0
          };
        }
        return null;
      });
      console.log('Game state:', gameState);
    } else {
      console.log('❌ No pieces found');
      
      // Debug
      const html = await page.content();
      console.log('Has piece-tray:', html.includes('piece-tray'));
      console.log('Has game-piece:', html.includes('game-piece'));
      
      // Check what UI is actually showing
      const uiInfo = await page.evaluate(() => {
        const waitingUI = document.querySelector('.waiting-container');
        const waitingText = waitingUI?.querySelector('.waiting-message')?.textContent;
        const gameLayout = document.querySelector('.game-layout');
        const phase = gameLayout?.getAttribute('data-phase');
        return {
          hasWaitingUI: !!waitingUI,
          waitingMessage: waitingText || 'none',
          hasGameLayout: !!gameLayout,
          dataPhase: phase || 'none'
        };
      });
      console.log('\nUI info:', uiInfo);
      
      // Take a screenshot for debugging
      await page.screenshot({ path: 'pieces-not-showing.png' });
      console.log('\nScreenshot saved as pieces-not-showing.png');
      
      // Check what's in the piece tray
      const pieceTrayHTML = await page.locator('.piece-tray').innerHTML();
      console.log('\nPieceTray HTML length:', pieceTrayHTML.length);
      console.log('Contains grid:', pieceTrayHTML.includes('piece-tray__grid'));
    }
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await page.waitForTimeout(2000);
    await browser.close();
  }
}

testPiecesDisplay();