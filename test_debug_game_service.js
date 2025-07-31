const { chromium } = require('playwright');

async function debugGameService() {
  console.log('🔍 Debug GameService Event Handling\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Inject console monitoring script
  await page.addInitScript(() => {
    const originalConsoleLog = console.log;
    window.gameServiceDebugLogs = [];
    
    console.log = function(...args) {
      // Store game service related logs
      const message = args.join(' ');
      if (message.includes('🎮') || message.includes('GameService') || message.includes('game_started')) {
        window.gameServiceDebugLogs.push(message);
      }
      originalConsoleLog.apply(console, args);
    };
  });
  
  // Monitor WebSocket events
  let gameStartedEvents = [];
  
  page.on('websocket', ws => {
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        
        if (eventType === 'game_started') {
          gameStartedEvents.push(data);
          console.log('📨 WebSocket game_started event received:', JSON.stringify(data, null, 2));
        }
      } catch (e) {}
    });
  });

  try {
    console.log('📍 Step 1: Enter lobby');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[type="text"]', 'DebugPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(2000);
    console.log('  ✓ Entered lobby');
    
    console.log('\n📍 Step 2: Create room');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(3000);
    
    const roomCode = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/([A-Z]{4})/);
      return match ? match[1] : null;
    });
    console.log(`  ✓ Room created: ${roomCode}`);
    
    console.log('\n📍 Step 3: Add bots to fill room');
    for (let i = 0; i < 3; i++) {
      try {
        const addBotButtons = await page.$$('button:has-text("Add Bot")');
        if (addBotButtons.length > 0) {
          await addBotButtons[0].click();
          await page.waitForTimeout(2000); // Give more time for bot to be added
          console.log(`  ✓ Added bot ${i + 1}`);
        } else {
          console.log(`  ⚠️ No Add Bot button found for bot ${i + 1}`);
          break;
        }
      } catch (error) {
        console.log(`  ❌ Error adding bot ${i + 1}:`, error.message);
        break;
      }
    }
    
    console.log('\n📍 Step 4: Start game and monitor GameService');
    await page.waitForTimeout(2000); // Wait for room to be ready
    const startButton = await page.$('button:has-text("Start Game")');
    if (startButton) {
      await startButton.click();
      console.log('  ✓ Clicked Start Game button');
      
      // Wait for events
      await page.waitForTimeout(5000);
      
      // Check console logs for GameService activity
      const gameServiceLogs = await page.evaluate(() => window.gameServiceDebugLogs || []);
      
      console.log('\n📊 GAME SERVICE DEBUG RESULTS:');
      console.log(`WebSocket game_started events received: ${gameStartedEvents.length}`);
      console.log(`GameService console logs captured: ${gameServiceLogs.length}`);
      
      if (gameServiceLogs.length > 0) {
        console.log('\n🔍 GameService Logs:');
        gameServiceLogs.forEach((log, i) => {
          console.log(`  ${i + 1}. ${log}`);
        });
      } else {
        console.log('❌ No GameService logs captured - GameService may not be handling game_started events');
      }
      
      if (gameStartedEvents.length > 0) {
        console.log('\n📨 WebSocket Events Received:');
        gameStartedEvents.forEach((event, i) => {
          console.log(`  Event ${i + 1}:`, JSON.stringify(event, null, 4));
        });
      }
      
      // Check game state in browser
      const gameState = await page.evaluate(() => {
        // Try to access GameService state if available
        try {
          // Access via the services module
          if (window.gameService) {
            const state = window.gameService.getState ? window.gameService.getState() : null;
            return {
              hasGameService: true,
              gameState: state,
              serviceActive: true,
              roomId: state ? state.roomId : 'unknown',
              playerName: state ? state.playerName : 'unknown',
              isConnected: state ? state.isConnected : false
            };
          }
          return {
            hasGameService: false,
            serviceActive: false,
            error: 'GameService not found on window'
          };
        } catch (error) {
          return {
            hasGameService: false,
            serviceActive: false,
            error: error.message
          };
        }
      });
      
      console.log('\n🎮 Game State Check:');
      console.log('  Has GameService:', gameState.hasGameService);
      console.log('  Service Active:', gameState.serviceActive);
      
      if (gameState.hasGameService) {
        console.log('  Room ID:', gameState.roomId);
        console.log('  Player Name:', gameState.playerName);
        console.log('  Is Connected:', gameState.isConnected);
        
        if (gameState.gameState && gameState.gameState.phase) {
          console.log(`  Current Phase: ${gameState.gameState.phase}`);
          console.log(`  Current Round: ${gameState.gameState.currentRound}`);
        }
      } else {
        console.log('  Error:', gameState.error);
      }
      
    } else {
      console.log('❌ Start Game button not found');
    }
    
    console.log('\n✅ Debug complete. Keeping browser open for 30 seconds...');
    await page.waitForTimeout(30000);
    await browser.close();
    
  } catch (error) {
    console.error('❌ Debug error:', error.message);
    await browser.close();
  }
}

debugGameService();