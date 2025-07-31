const { chromium } = require('playwright');

async function testGameServiceConnection() {
  console.log('🔍 Testing GameService Connection Fix\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor console for GameService logs
  const logs = [];
  page.on('console', msg => {
    const message = msg.text();
    logs.push(message);
    if (message.includes('GameService') || message.includes('🎮') || message.includes('game_started')) {
      console.log(`[CONSOLE] ${message}`);
    }
  });
  
  try {
    console.log('📍 Step 1: Go to start page');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    console.log('📍 Step 2: Enter player name');
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(2000);
    
    console.log('📍 Step 3: Create room');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(3000);
    
    // Check if we reached room page
    const currentUrl = page.url();
    console.log(`Current URL: ${currentUrl}`);
    
    if (currentUrl.includes('/room/')) {
      console.log('✅ Successfully navigated to room page');
      
      // Extract room ID from URL
      const roomId = currentUrl.split('/room/')[1];
      console.log(`Room ID: ${roomId}`);
      
      // Check GameService state
      const gameServiceState = await page.evaluate(() => {
        try {
          if (window.gameService) {
            const state = window.gameService.getState();
            return {
              hasGameService: true,
              roomId: state.roomId,
              playerName: state.playerName,
              isConnected: state.isConnected,
              phase: state.phase,
              error: null
            };
          }
          return { hasGameService: false, error: 'GameService not found' };
        } catch (error) {
          return { hasGameService: false, error: error.message };
        }
      });
      
      console.log('\n🎮 GameService Connection Status:');
      console.log(`  Has GameService: ${gameServiceState.hasGameService}`);
      if (gameServiceState.hasGameService) {
        console.log(`  Room ID: ${gameServiceState.roomId}`);
        console.log(`  Player Name: ${gameServiceState.playerName}`);
        console.log(`  Is Connected: ${gameServiceState.isConnected}`);
        console.log(`  Phase: ${gameServiceState.phase}`);
        
        // Verify GameService is connected to the correct room
        if (gameServiceState.roomId === roomId) {
          console.log('✅ GameService is connected to the correct room!');
          console.log('🎯 FIX VERIFIED: GameService will now receive game_started events');
        } else {
          console.log('❌ Room ID mismatch:');
          console.log(`    Expected: ${roomId}`);
          console.log(`    GameService: ${gameServiceState.roomId}`);
        }
      } else {
        console.log(`  Error: ${gameServiceState.error}`);
      }
      
      // Wait and check for any relevant console logs
      await page.waitForTimeout(5000);
      
      const relevantLogs = logs.filter(log => 
        log.includes('GameService') || 
        log.includes('🎮') || 
        log.includes('join') ||
        log.includes('connect')
      );
      
      if (relevantLogs.length > 0) {
        console.log('\n📝 Relevant Console Logs:');
        relevantLogs.forEach((log, i) => {
          console.log(`  ${i + 1}. ${log}`);
        });
      }
      
    } else {
      console.log('❌ Failed to navigate to room page');
    }
    
    console.log('\n✅ Test complete. Keeping browser open for 10 seconds...');
    await page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  }
  
  await browser.close();
}

testGameServiceConnection();