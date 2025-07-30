const { chromium } = require('playwright');

async function testCorrectFlow() {
  console.log('🎮 Testing Correct Game Flow\n');
  console.log('Flow:');
  console.log('1. Enter player name');
  console.log('2. Click "Enter Lobby" to join lobby');
  console.log('3. Create room in lobby');
  console.log('4. Press start game button\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Track WebSocket events
  const wsEvents = [];
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connected');
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log(`📤 WS Send: ${data.type}`);
        wsEvents.push({ type: 'sent', event: data.type, data });
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log(`📥 WS Receive: ${data.type}`);
        wsEvents.push({ type: 'received', event: data.type, data });
        
        if (data.type === 'game_started') {
          console.log('🎯 GAME_STARTED EVENT RECEIVED!');
          console.log('Payload:', JSON.stringify(data.payload, null, 2));
        }
      } catch (e) {}
    });
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`❌ Console Error: ${msg.text()}`);
    }
  });

  try {
    // Navigate to main page
    console.log('📍 Step 1: Navigate to main page');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'flow-1-main-page.png' });
    
    // Enter player name
    console.log('\n📍 Step 2: Enter player name');
    const nameInput = await page.waitForSelector('input[type="text"]');
    await nameInput.fill('Player1');
    console.log('  ✓ Entered name: Player1');
    
    // Click Enter Lobby button
    console.log('\n📍 Step 3: Click "Enter Lobby" to join lobby');
    const enterLobbyButton = await page.waitForSelector('button:has-text("Enter Lobby")');
    await enterLobbyButton.click();
    console.log('  ✓ Clicked Enter Lobby button');
    
    // Wait for lobby to load
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'flow-2-in-lobby.png' });
    
    // Check if we're in lobby
    const lobbyText = await page.textContent('body');
    console.log('  ✓ Lobby loaded');
    
    // Create room
    console.log('\n📍 Step 4: Create room in lobby');
    const createRoomButton = await page.waitForSelector('button:has-text("Create Room")', { timeout: 5000 });
    if (createRoomButton) {
      await createRoomButton.click();
      console.log('  ✓ Clicked Create Room button');
    } else {
      console.log('  ❌ Create Room button not found');
      console.log('  Page content:', lobbyText.substring(0, 200));
    }
    
    // Wait for room creation
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'flow-3-room-created.png' });
    
    // Get room code
    const roomCode = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/[A-Z]{4}/);
      return match ? match[0] : null;
    });
    
    if (roomCode) {
      console.log(`  ✓ Room created with code: ${roomCode}`);
    }
    
    // Press start game button
    console.log('\n📍 Step 5: Press start game button');
    
    // Try multiple selectors for start button
    let startButton = await page.$('button:has-text("Start Game")') ||
                     await page.$('button:has-text("Start")') ||
                     await page.$('#start-game-btn');
    
    if (!startButton) {
      // Find all buttons and look for start
      const buttons = await page.$$('button');
      for (const btn of buttons) {
        const text = await btn.textContent();
        if (text.toLowerCase().includes('start')) {
          startButton = btn;
          console.log(`  Found button with text: "${text}"`);
          break;
        }
      }
    }
    
    if (startButton) {
      const beforeUrl = page.url();
      console.log(`  Current URL: ${beforeUrl}`);
      
      await startButton.click();
      console.log('  ✓ Clicked Start Game button');
      
      // Wait for potential transition
      await page.waitForTimeout(5000);
      
      const afterUrl = page.url();
      console.log(`  URL after click: ${afterUrl}`);
      console.log(`  Navigation occurred: ${beforeUrl !== afterUrl ? 'Yes' : 'No'}`);
      
      await page.screenshot({ path: 'flow-4-after-start.png' });
      
      // Check final state
      const finalText = await page.textContent('body');
      const inGame = afterUrl.includes('/game/') || finalText.includes('Declaration') || finalText.includes('Preparation');
      
      if (inGame) {
        console.log('  ✅ Successfully transitioned to game!');
      } else {
        console.log('  ❌ Still in waiting room');
      }
      
    } else {
      console.log('  ❌ Start button not found');
      const pageContent = await page.textContent('body');
      console.log('  Current page:', pageContent.substring(0, 300));
    }
    
    // Analyze WebSocket events
    console.log('\n📊 WebSocket Event Summary:');
    const eventCounts = {};
    wsEvents.forEach(e => {
      const key = `${e.type}: ${e.event}`;
      eventCounts[key] = (eventCounts[key] || 0) + 1;
    });
    
    Object.entries(eventCounts).forEach(([key, count]) => {
      console.log(`  ${key}: ${count}`);
    });
    
    // Check for critical events
    const hasJoinLobby = wsEvents.some(e => e.type === 'sent' && e.event === 'join_lobby');
    const hasCreateRoom = wsEvents.some(e => e.type === 'sent' && e.event === 'create_room');
    const hasStartGame = wsEvents.some(e => e.type === 'sent' && e.event === 'start_game');
    const hasGameStarted = wsEvents.some(e => e.type === 'received' && e.event === 'game_started');
    
    console.log('\n🔍 Critical Events Check:');
    console.log(`  Join lobby sent: ${hasJoinLobby ? '✅' : '❌'}`);
    console.log(`  Create room sent: ${hasCreateRoom ? '✅' : '❌'}`);
    console.log(`  Start game sent: ${hasStartGame ? '✅' : '❌'}`);
    console.log(`  Game started received: ${hasGameStarted ? '✅' : '❌'}`);
    
    if (hasStartGame && !hasGameStarted) {
      console.log('\n⚠️  Issue identified: Start game was sent but no game_started response');
      console.log('  This indicates a server-side issue preventing game start');
    }
    
    console.log('\n✅ Test complete. Check screenshots:');
    console.log('  - flow-1-main-page.png');
    console.log('  - flow-2-in-lobby.png');
    console.log('  - flow-3-room-created.png');
    console.log('  - flow-4-after-start.png');
    console.log('\nBrowser remains open for inspection.');
    
    await new Promise(() => {});
    
  } catch (error) {
    console.error('\n❌ Test error:', error.message);
    await page.screenshot({ path: 'flow-error.png' });
  }
}

testCorrectFlow().catch(console.error);