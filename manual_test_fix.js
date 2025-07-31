const { chromium } = require('playwright');

async function testGameStartFix() {
  console.log('🎯 Starting manual game start flow validation...');
  
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    // Step 1: Navigate to app
    console.log('📍 Step 1: Loading application...');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    // Step 2: Enter player name
    console.log('📍 Step 2: Looking for name input field...');
    const nameInput = page.locator('input[placeholder*="name"]').first();
    await nameInput.waitFor({ timeout: 10000 });
    
    await nameInput.fill('TestPlayer');
    console.log('✅ Name entered: TestPlayer');
    
    // Step 3: Enter lobby
    console.log('📍 Step 3: Clicking Enter Lobby...');
    const enterLobbyButton = page.locator('button:has-text("ENTER LOBBY")');
    await enterLobbyButton.click();
    
    // Wait for navigation
    await page.waitForURL(/\/(lobby|room)/, { timeout: 10000 });
    console.log('✅ Current URL:', page.url());
    
    // Step 4: Create room if in lobby
    if (page.url().includes('/lobby')) {
      console.log('📍 Step 4: Creating room...');
      const createButton = page.locator('button:has-text("Create Room")');
      await createButton.click();
      await page.waitForURL(/\/room/, { timeout: 10000 });
    }
    
    console.log('✅ Room URL:', page.url());
    
    // Step 5: Add bots
    console.log('📍 Step 5: Adding bots...');
    for (let i = 0; i < 3; i++) {
      const addBotButton = page.locator('button:has-text("Add Bot")').first();
      if (await addBotButton.isVisible({ timeout: 2000 })) {
        await addBotButton.click();
        await page.waitForTimeout(1000);
        console.log(`✅ Bot ${i + 1} added`);
      }
    }
    
    // Step 6: Start game - THE CRITICAL TEST
    console.log('📍 Step 6: Starting game...');
    const startButton = page.locator('button:has-text("Start Game")');
    await startButton.waitFor({ timeout: 10000 });
    
    const isEnabled = await startButton.isEnabled();
    console.log(`🔍 Start Game button enabled: ${isEnabled}`);
    
    if (isEnabled) {
      console.log('🚨 CRITICAL: Clicking Start Game...');
      
      // Monitor WebSocket events
      page.on('console', msg => {
        if (msg.text().includes('game_started') || msg.text().includes('phase_change')) {
          console.log(`🎮 WebSocket Event: ${msg.text()}`);
        }
      });
      
      await startButton.click();
      console.log('⏱️  Waiting for game page navigation...');
      
      try {
        await page.waitForURL(/\/game\//, { timeout: 30000 });
        console.log('✅ SUCCESS: Reached game page!');
        console.log('🎯 Final URL:', page.url());
        console.log('');
        console.log('🎮 GAME START FIX VALIDATION: PASSED ✅');
        console.log('🎯 PhaseChanged event fix is working correctly!');
        
      } catch (error) {
        console.log('❌ FAILED: Did not navigate to game page');
        console.log(`🔍 Current URL: ${page.url()}`);
        console.log('');
        console.log('🚨 GAME START BUG: Still exists or different issue');
        
        // Check for waiting page indicators
        const waitingElements = await page.locator('text=waiting').count();
        console.log(`🔍 Waiting elements found: ${waitingElements}`);
      }
    } else {
      console.log('❌ Start Game button is not enabled - room setup issue');
    }
    
    // Keep browser open for inspection
    console.log('🔍 Browser will stay open for 15 seconds for inspection...');
    await page.waitForTimeout(15000);
    
  } catch (error) {
    console.error('💥 Test error:', error.message);
  } finally {
    await browser.close();
  }
}

testGameStartFix();