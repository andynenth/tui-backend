const { chromium } = require('playwright');

async function testWaitingPageWithRetry() {
  console.log('🔍 Testing Waiting Page Issue with Retry Logic\n');
  console.log('Strategy:');
  console.log('1. First attempt: Handle "room no longer exists" error');
  console.log('2. Wait for auto-redirect to start page');
  console.log('3. Second attempt: Run test sequence again');
  console.log('4. Check if game progresses properly on second try\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor WebSocket events
  const wsEvents = [];
  let gameStartedCount = 0;
  
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connected');
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        console.log(`📤 WS Send: ${eventType}`);
        wsEvents.push({ direction: 'sent', event: eventType, timestamp: Date.now() });
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        console.log(`📥 WS Receive: ${eventType}`);
        wsEvents.push({ direction: 'received', event: eventType, timestamp: Date.now() });
        
        if (eventType === 'game_started') {
          gameStartedCount++;
          console.log(`🎯 GAME_STARTED EVENT #${gameStartedCount}`);
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

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`❌ Console Error: ${msg.text()}`);
    }
  });

  async function runTestSequence(attemptNumber) {
    console.log(`\n📍 ATTEMPT ${attemptNumber}: Running test sequence`);
    
    // Clear events for this attempt
    const startTime = Date.now();
    
    // Step 1: Enter Lobby
    console.log('  Step 1: Enter Lobby');
    if (page.url() !== 'http://localhost:5050/') {
      await page.goto('http://localhost:5050');
      await page.waitForLoadState('networkidle');
    }
    
    await page.fill('input[type="text"]', `TestPlayer${attemptNumber}`);
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(2000);
    console.log('    ✓ Entered lobby');
    
    // Step 2: Create Room
    console.log('  Step 2: Create Room');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    const roomCode = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/[A-Z]{4}/);
      return match ? match[0] : null;
    });
    console.log(`    ✓ Room created: ${roomCode}`);
    
    // Step 3: Start Game
    console.log('  Step 3: Start Game');
    const startButton = await page.$('button:has-text("Start")');
    
    if (startButton) {
      await startButton.click();
      console.log('    ✓ Clicked Start Game button');
      
      // Wait and monitor what happens
      await page.waitForTimeout(8000);
      
      // Check current state
      const currentUrl = page.url();
      const currentPath = new URL(currentUrl).pathname;
      const pageText = await page.textContent('body');
      
      console.log(`  📊 Result for Attempt ${attemptNumber}:`);
      console.log(`    Current URL: ${currentPath}`);
      
      // Get events from this attempt
      const attemptEvents = wsEvents.filter(e => e.timestamp >= startTime);
      const gameStartedInAttempt = attemptEvents.filter(e => 
        e.direction === 'received' && e.event === 'game_started'
      ).length;
      
      console.log(`    game_started events: ${gameStartedInAttempt}`);
      
      if (pageText.includes('room no longer exists')) {
        console.log('    ❌ Status: ROOM ERROR - "room no longer exists"');
        return 'room_error';
        
      } else if (pageText.includes('Waiting') || pageText.includes('waiting')) {
        console.log('    ⚠️ Status: STUCK ON WAITING PAGE');
        return 'waiting_stuck';
        
      } else if (pageText.includes('Declaration') || pageText.includes('Choose') || pageText.includes('declare')) {
        console.log('    ✅ Status: SUCCESSFULLY ENTERED GAME!');
        console.log('    Game progressed to Declaration phase');
        return 'success';
        
      } else if (currentPath === '/') {
        console.log('    ↩️ Status: REDIRECTED TO START PAGE');
        return 'redirected';
        
      } else {
        console.log('    🤔 Status: UNKNOWN STATE');
        console.log(`    Page content: ${pageText.substring(0, 100)}...`);
        return 'unknown';
      }
    } else {
      console.log('    ❌ Start Game button not found');
      return 'no_button';
    }
  }

  try {
    // First Attempt
    const result1 = await runTestSequence(1);
    
    if (result1 === 'room_error' || result1 === 'redirected') {
      console.log('\n⏳ Waiting for auto-redirect to complete...');
      
      // Wait for redirect to start page
      try {
        await page.waitForURL('http://localhost:5050/', { timeout: 20000 });
        console.log('✓ Auto-redirect completed');
      } catch (e) {
        console.log('⚠️ Auto-redirect timeout, but continuing...');
      }
      
      // Wait a bit more for any cleanup
      await page.waitForTimeout(3000);
      
      // Second Attempt
      console.log('\n🔄 Running second attempt after redirect...');
      const result2 = await runTestSequence(2);
      
      if (result2 === 'success') {
        console.log('\n🎉 SUCCESS! Game works on second attempt');
        console.log('This confirms the issue is with initial room persistence');
      } else if (result2 === 'room_error') {
        console.log('\n❌ Still getting room error on second attempt');
        console.log('This indicates a persistent server-side issue');
      } else {
        console.log(`\n⚠️ Second attempt result: ${result2}`);
        console.log('Issue may be intermittent or require investigation');
      }
      
    } else if (result1 === 'success') {
      console.log('\n🎉 EXCELLENT! Game worked on first attempt');
      console.log('The waiting page issue appears to be resolved');
      
    } else {
      console.log(`\n⚠️ Unexpected first attempt result: ${result1}`);
    }
    
    // Final Analysis
    console.log('\n📊 Final Analysis:');
    console.log(`Total game_started events received: ${gameStartedCount}`);
    console.log(`Total WebSocket events: ${wsEvents.length}`);
    
    // Check pattern of events
    const startGameEvents = wsEvents.filter(e => e.event === 'start_game').length;
    const gameStartedEvents = wsEvents.filter(e => e.event === 'game_started').length;
    
    console.log(`start_game sent: ${startGameEvents}`);
    console.log(`game_started received: ${gameStartedEvents}`);
    
    if (gameStartedEvents > 0) {
      console.log('\n✅ WebSocket communication is working');
      console.log('The issue is likely room persistence after game_started');
    } else {
      console.log('\n❌ No game_started events received');
      console.log('The issue is in the game start flow');
    }
    
    console.log('\n✅ Test complete. Browser remains open for inspection.');
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  }
}

testWaitingPageWithRetry().catch(console.error);