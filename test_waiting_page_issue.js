const { chromium } = require('playwright');

async function testWaitingPageIssue() {
  console.log('🔍 Testing Current State: Waiting Page → Game Page Transition\n');
  console.log('Test Flow:');
  console.log('1. Enter Lobby');
  console.log('2. Create Room'); 
  console.log('3. Start Game');
  console.log('4. Check if game progresses beyond waiting page\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor WebSocket for game_started event
  const wsEvents = [];
  let gameStartedReceived = false;
  
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connected');
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        console.log(`📤 WS Send: ${eventType}`);
        wsEvents.push({ direction: 'sent', event: eventType, data });
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        console.log(`📥 WS Receive: ${eventType}`);
        wsEvents.push({ direction: 'received', event: eventType, data });
        
        if (eventType === 'game_started') {
          gameStartedReceived = true;
          console.log('🎯 GAME_STARTED EVENT RECEIVED!');
        }
      } catch (e) {}
    });
  });

  // Monitor navigation
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      const url = frame.url();
      const path = new URL(url).pathname;
      console.log(`🧭 Navigation: ${path}`);
    }
  });

  // Monitor console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`❌ Console Error: ${msg.text()}`);
    }
  });

  try {
    // Step 1: Enter Lobby
    console.log('📍 Step 1: Enter Lobby');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(2000);
    console.log('  ✓ Entered lobby');
    
    // Step 2: Create Room
    console.log('\n📍 Step 2: Create Room');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    const roomCode = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/[A-Z]{4}/);
      return match ? match[0] : null;
    });
    console.log(`  ✓ Room created: ${roomCode}`);
    
    // Step 3: Start Game
    console.log('\n📍 Step 3: Start Game');
    const startButton = await page.$('button:has-text("Start")');
    
    if (startButton) {
      // Clear previous events to focus on start game sequence
      wsEvents.length = 0;
      gameStartedReceived = false;
      
      await startButton.click();
      console.log('  ✓ Clicked Start Game button');
      
      // Wait and monitor what happens
      await page.waitForTimeout(5000);
      
      // Check current state
      const currentUrl = page.url();
      const currentPath = new URL(currentUrl).pathname;
      const pageText = await page.textContent('body');
      
      console.log('\n📊 Current State After Start Game:');
      console.log(`  URL: ${currentPath}`);
      console.log(`  Game Started Event: ${gameStartedReceived ? '✅ Yes' : '❌ No'}`);
      
      // Check for error messages
      if (pageText.includes('room no longer exists')) {
        console.log('  ❌ Room Error: "This game room no longer exists"');
        console.log('  Status: ISSUE STILL EXISTS');
        
        // Wait for auto-redirect
        console.log('  ⏳ Waiting for auto-redirect...');
        try {
          await page.waitForURL('http://localhost:5050/', { timeout: 15000 });
          console.log('  ✓ Auto-redirected to start page');
        } catch (e) {
          console.log('  ⚠️ No auto-redirect occurred');
        }
        
      } else if (pageText.includes('Waiting') || pageText.includes('waiting')) {
        console.log('  ⚠️ Status: STUCK ON WAITING PAGE');
        console.log('  Issue: Game does not progress beyond waiting');
        
      } else if (pageText.includes('Declaration') || pageText.includes('Choose')) {
        console.log('  ✅ Status: SUCCESSFULLY ENTERED GAME!');
        console.log('  Game progressed to actual gameplay');
        
      } else {
        console.log('  🤔 Status: UNKNOWN STATE');
        console.log(`  Page content preview: ${pageText.substring(0, 200)}`);
      }
      
      // Analyze WebSocket events during start game
      console.log('\n📊 WebSocket Events During Start Game:');
      const startGameSent = wsEvents.some(e => 
        e.direction === 'sent' && e.event === 'start_game'
      );
      const gameStartedRcvd = wsEvents.some(e => 
        e.direction === 'received' && e.event === 'game_started'
      );
      
      console.log(`  start_game sent: ${startGameSent ? '✅' : '❌'}`);
      console.log(`  game_started received: ${gameStartedRcvd ? '✅' : '❌'}`);
      
      if (startGameSent && !gameStartedRcvd) {
        console.log('  ⚠️ Server did not respond with game_started');
        console.log('  This indicates a backend issue');
      }
      
      if (!startGameSent) {
        console.log('  ⚠️ start_game message was not sent');
        console.log('  This indicates a frontend issue');
      }
      
    } else {
      console.log('  ❌ Start Game button not found');
    }
    
    console.log('\n🔍 Investigation Summary:');
    if (gameStartedReceived) {
      console.log('  ✅ Game transition works correctly');
      console.log('  The waiting page issue appears to be resolved');
    } else {
      console.log('  ❌ Game transition still has issues');
      console.log('  Further investigation needed into:');
      console.log('    - Room persistence in backend');
      console.log('    - WebSocket message handling');
      console.log('    - Game state initialization');
    }
    
    console.log('\n✅ Test complete. Browser remains open for inspection.');
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  }
}

testWaitingPageIssue().catch(console.error);