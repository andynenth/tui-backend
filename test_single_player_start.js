const { chromium } = require('playwright');

async function testSinglePlayerStart() {
  console.log('🎮 Testing Single Player Start Game Flow\n');
  console.log('Test Order:');
  console.log('1. Player 1 >> join lobby');
  console.log('2. Player 1 >> create room');
  console.log('3. Player 1 >> press start game button\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Track all important events
  const events = [];
  
  // Monitor WebSocket
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connected');
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log(`📤 WS Send: ${data.type}`);
        events.push({ 
          time: Date.now(), 
          type: 'ws_sent', 
          event: data.type,
          data: data 
        });
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log(`📥 WS Receive: ${data.type}`);
        events.push({ 
          time: Date.now(), 
          type: 'ws_received', 
          event: data.type,
          data: data 
        });
        
        // Key events to watch for
        if (data.type === 'game_started') {
          console.log('🎯 GAME_STARTED EVENT RECEIVED!');
        }
        if (data.type === 'game_state_updated') {
          console.log('🔄 Game state updated');
        }
      } catch (e) {}
    });
  });

  // Monitor navigation
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      const url = frame.url();
      console.log(`🧭 Navigation: ${url}`);
      events.push({ 
        time: Date.now(), 
        type: 'navigation', 
        url: url 
      });
    }
  });

  // Monitor errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`❌ Console Error: ${msg.text()}`);
      events.push({ 
        time: Date.now(), 
        type: 'error', 
        message: msg.text() 
      });
    }
  });

  try {
    // Step 1: Join lobby (navigate to app)
    console.log('\n📍 Step 1: Player 1 >> join lobby');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    // Take screenshot of initial state
    await page.screenshot({ path: 'debug-1-lobby.png' });
    
    // Look for lobby elements
    const hasCreateButton = await page.$('button:has-text("Create Room")');
    const hasJoinButton = await page.$('button:has-text("Join Room")');
    const hasNameInput = await page.$('input[type="text"]');
    
    console.log(`  ✓ Create Room button: ${hasCreateButton ? 'Found' : 'Not found'}`);
    console.log(`  ✓ Join Room button: ${hasJoinButton ? 'Found' : 'Not found'}`);
    console.log(`  ✓ Name input: ${hasNameInput ? 'Found' : 'Not found'}`);
    
    if (!hasNameInput) {
      // Try different selectors
      const inputs = await page.$$('input');
      console.log(`  Found ${inputs.length} input elements`);
      if (inputs.length > 0) {
        // Use first input
        await inputs[0].fill('Player1');
      }
    } else {
      await hasNameInput.fill('Player1');
    }
    
    // Step 2: Create room
    console.log('\n📍 Step 2: Player 1 >> create room');
    
    if (hasCreateButton) {
      await hasCreateButton.click();
      console.log('  ✓ Clicked Create Room button');
    } else {
      // Try different selector
      await page.click('button:text("Create Room")');
    }
    
    // Wait for room to be created
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'debug-2-room-created.png' });
    
    // Check room state
    const roomCode = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/[A-Z]{4}/);
      return match ? match[0] : null;
    });
    
    if (roomCode) {
      console.log(`  ✓ Room created with code: ${roomCode}`);
    }
    
    // Check if we're in waiting room
    const pageText = await page.textContent('body');
    const inWaitingRoom = pageText.includes('Waiting') || pageText.includes('waiting');
    console.log(`  ✓ In waiting room: ${inWaitingRoom ? 'Yes' : 'No'}`);
    
    // Step 3: Press start game button
    console.log('\n📍 Step 3: Player 1 >> press start game button');
    
    // Find start button with various selectors
    let startButton = await page.$('button:has-text("Start Game")');
    if (!startButton) {
      startButton = await page.$('button:has-text("Start")');
    }
    if (!startButton) {
      startButton = await page.$('#start-game-btn');
    }
    if (!startButton) {
      // Find all buttons and check
      const buttons = await page.$$('button');
      console.log(`  Found ${buttons.length} buttons`);
      for (let i = 0; i < buttons.length; i++) {
        const text = await buttons[i].textContent();
        console.log(`  Button ${i}: "${text}"`);
        if (text.toLowerCase().includes('start')) {
          startButton = buttons[i];
          break;
        }
      }
    }
    
    if (startButton) {
      console.log('  ✓ Start button found');
      
      // Set up monitoring before clicking
      const beforeUrl = page.url();
      console.log(`  Current URL: ${beforeUrl}`);
      
      // Click and wait for potential navigation
      const [response] = await Promise.all([
        page.waitForResponse(resp => resp.url().includes('/api/'), { timeout: 5000 }).catch(() => null),
        startButton.click()
      ]);
      
      console.log('  ✓ Start button clicked');
      
      if (response) {
        console.log(`  API Response: ${response.status()} ${response.url()}`);
      }
      
      // Wait and check what happens
      await page.waitForTimeout(5000);
      
      const afterUrl = page.url();
      console.log(`  URL after click: ${afterUrl}`);
      console.log(`  Navigation occurred: ${beforeUrl !== afterUrl ? 'Yes' : 'No'}`);
      
      // Take screenshot of final state
      await page.screenshot({ path: 'debug-3-after-start.png' });
      
      // Check final state
      const finalText = await page.textContent('body');
      const stillWaiting = finalText.includes('Waiting') || finalText.includes('waiting');
      const inGame = finalText.includes('Declaration') || finalText.includes('Game') || afterUrl.includes('/game/');
      
      console.log(`  Still in waiting room: ${stillWaiting ? 'Yes' : 'No'}`);
      console.log(`  In game: ${inGame ? 'Yes' : 'No'}`);
      
    } else {
      console.log('  ❌ Start button not found!');
      console.log('  Page content preview:');
      console.log(pageText.substring(0, 500));
    }
    
    // Final analysis
    console.log('\n📊 Event Summary:');
    console.log('─'.repeat(50));
    
    // Group events by type
    const eventSummary = {};
    events.forEach(e => {
      const key = e.type === 'ws_sent' || e.type === 'ws_received' 
        ? `${e.type}: ${e.event}` 
        : e.type;
      eventSummary[key] = (eventSummary[key] || 0) + 1;
    });
    
    Object.entries(eventSummary).forEach(([key, count]) => {
      console.log(`  ${key}: ${count}`);
    });
    
    // Check for critical missing events
    const hasGameStartedEvent = events.some(e => 
      e.type === 'ws_received' && e.event === 'game_started'
    );
    const hasStartGameRequest = events.some(e => 
      e.type === 'ws_sent' && e.event === 'start_game'
    );
    
    console.log('\n🔍 Diagnostics:');
    console.log(`  Start game request sent: ${hasStartGameRequest ? '✅ Yes' : '❌ No'}`);
    console.log(`  Game started event received: ${hasGameStartedEvent ? '✅ Yes' : '❌ No'}`);
    
    if (!hasStartGameRequest) {
      console.log('\n⚠️  Issue: Start game request was not sent via WebSocket');
      console.log('  Possible causes:');
      console.log('  - Button click handler not working');
      console.log('  - WebSocket not connected');
      console.log('  - Authorization issue');
    }
    
    if (hasStartGameRequest && !hasGameStartedEvent) {
      console.log('\n⚠️  Issue: Server did not respond with game_started event');
      console.log('  Possible causes:');
      console.log('  - Server-side error');
      console.log('  - Not enough players');
      console.log('  - Game already started');
    }
    
    console.log('\n✅ Test complete. Browser remains open for inspection.');
    console.log('Screenshots saved: debug-1-lobby.png, debug-2-room-created.png, debug-3-after-start.png');
    console.log('Press Ctrl+C to exit.');
    
    // Keep browser open
    await new Promise(() => {});
    
  } catch (error) {
    console.error('\n❌ Test error:', error.message);
    await page.screenshot({ path: 'debug-error.png' });
  }
}

testSinglePlayerStart().catch(console.error);