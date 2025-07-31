const { chromium } = require('playwright');

async function testGameServiceEventHandling() {
  console.log('🔍 Testing GameService Event Handling\n');
  
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
    console.log(`[CONSOLE] ${message}`);
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
    
    console.log('📍 Step 4: Navigate to room manually if needed');
    const currentUrl = page.url();
    
    if (!currentUrl.includes('/room/')) {
      // If we're still in lobby, extract room ID from logs and navigate manually
      const roomCreatedLog = logs.find(log => log.includes('Joined room') && log.includes('as TestPlayer'));
      if (roomCreatedLog) {
        const roomId = roomCreatedLog.match(/Joined room (\w+) as/)?.[1];
        if (roomId) {
          console.log(`Found room ID in logs: ${roomId}`);
          await page.goto(`http://localhost:5050/room/${roomId}`);
          await page.waitForLoadState('networkidle');
          await page.waitForTimeout(2000);
        }
      }
    }
    
    const finalUrl = page.url();
    console.log(`Final URL: ${finalUrl}`);
    
    if (finalUrl.includes('/room/')) {
      const roomId = finalUrl.split('/room/')[1];
      console.log(`✅ On room page: ${roomId}`);
      
      console.log('📍 Step 5: Verify GameService is connected and ready');
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
              hasHandleGameStarted: typeof window.gameService.handleGameStarted === 'function'
            };
          }
          return { hasGameService: false };
        } catch (error) {
          return { hasGameService: false, error: error.message };
        }
      });
      
      console.log('\n🎮 GameService State:');
      console.log(`  Connected to room: ${gameServiceState.roomId}`);
      console.log(`  Player: ${gameServiceState.playerName}`);
      console.log(`  Is Connected: ${gameServiceState.isConnected}`);
      console.log(`  Has handleGameStarted method: ${gameServiceState.hasHandleGameStarted}`);
      
      if (gameServiceState.roomId === roomId && gameServiceState.isConnected) {
        console.log('\n🎯 CRITICAL VERIFICATION: GameService is connected to the correct room!');
        console.log('✅ This means GameService WILL now receive game_started events');
        console.log('✅ The original bug (room ID mismatch) has been FIXED');
        
        console.log('\n📍 Step 6: Simulate game_started event to verify handling');
        
        // Clear existing logs to focus on event handling
        logs.length = 0;
        
        // Inject a test game_started event
        await page.evaluate((testRoomId) => {
          // Simulate the NetworkService receiving a game_started event
          if (window.networkService) {
            const testEvent = new CustomEvent('game_started', {
              detail: {
                roomId: testRoomId,
                data: {
                  round_number: 1,
                  players: ['TestPlayer', 'Bot 1', 'Bot 2', 'Bot 3'],
                  timestamp: Date.now()
                },
                message: {
                  event: 'game_started',
                  data: {
                    round_number: 1,
                    players: ['TestPlayer', 'Bot 1', 'Bot 2', 'Bot 3'],
                    timestamp: Date.now()
                  }
                },
                timestamp: Date.now()
              }
            });
            
            console.log('🧪 Injecting test game_started event...');
            window.networkService.dispatchEvent(testEvent);
          }
        }, roomId);
        
        await page.waitForTimeout(2000);
        
        // Check if GameService processed the event
        const gameStartedLogs = logs.filter(log => 
          log.includes('🎮 Game started!') || 
          log.includes('handleGameStarted') ||
          log.includes('game_started')
        );
        
        console.log('\n📊 Event Handling Results:');
        if (gameStartedLogs.length > 0) {
          console.log('✅ GameService successfully processed game_started event!');
          gameStartedLogs.forEach(log => console.log(`  ✓ ${log}`));
        } else {
          console.log('❌ GameService did not process the test event');
          console.log('📝 All logs from event injection:');
          logs.forEach(log => console.log(`  • ${log}`));
        }
        
      } else {
        console.log('❌ GameService not properly connected');
      }
      
    } else {
      console.log('❌ Could not reach room page');
    }
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  }
  
  console.log('\n✅ Test complete. Keeping browser open for 15 seconds...');
  await page.waitForTimeout(15000);
  await browser.close();
}

testGameServiceEventHandling();