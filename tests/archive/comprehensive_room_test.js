const { chromium } = require('playwright');

async function comprehensiveRoomTest() {
  console.log('🧪 Comprehensive Room Creation & Display Test...');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });
  
  try {
    // Create two contexts for two players
    const player1Context = await browser.newContext();
    const player2Context = await browser.newContext();
    
    const player1Page = await player1Context.newPage();
    const player2Page = await player2Context.newPage();
    
    // Set up enhanced logging
    player1Page.on('console', msg => {
      const text = msg.text();
      if (text.includes('room_list_update') || text.includes('Received room_list_update')) {
        console.log(`[P1] 🎯 ${msg.type()}: ${text}`);
      }
    });
    
    player2Page.on('console', msg => {
      const text = msg.text();
      if (text.includes('room_list_update') || text.includes('Received room_list_update')) {
        console.log(`[P2] 🎯 ${msg.type()}: ${text}`);
      }
    });
    
    // Capture WebSocket messages
    const p1Messages = [];
    const p2Messages = [];
    
    player1Page.on('websocket', ws => {
      ws.on('framereceived', data => {
        try {
          const message = JSON.parse(data.payload);
          if (message.event === 'room_list_update') {
            console.log(`[P1-WS] 📥 room_list_update:`, message.data);
            p1Messages.push(message);
          }
        } catch (e) {}
      });
    });
    
    player2Page.on('websocket', ws => {
      ws.on('framereceived', data => {
        try {
          const message = JSON.parse(data.payload);
          if (message.event === 'room_list_update') {
            console.log(`[P2-WS] 📥 room_list_update:`, message.data);
            p2Messages.push(message);
          }
        } catch (e) {}
      });
    });
    
    console.log('🔄 Phase 1: Both players entering lobby...');
    
    // Both players enter lobby
    await Promise.all([
      enterLobby(player1Page, 'Player1'),
      enterLobby(player2Page, 'Player2')
    ]);
    
    console.log('📊 Phase 2: Initial state check...');
    await checkInitialState(player1Page, player2Page);
    
    console.log('➕ Phase 3: Player 1 creates room...');
    await player1Page.click('button:has-text("Create")');
    
    // Wait for room creation to propagate
    await player1Page.waitForTimeout(3000);
    
    console.log('👀 Phase 4: Check Player 2 receives updates...');
    await checkPlayer2Updates(player2Page);
    
    console.log('🔄 Phase 5: Manual refresh test...');
    const refreshBtn = player2Page.locator('button[title="Refresh room list"]');
    if (await refreshBtn.isVisible()) {
      await refreshBtn.click();
      await player2Page.waitForTimeout(1000);
      await checkPlayer2Updates(player2Page);
    }
    
    console.log('📈 Phase 6: Final analysis...');
    console.log(`P1 WebSocket messages: ${p1Messages.length}`);
    console.log(`P2 WebSocket messages: ${p2Messages.length}`);
    
    // Keep open for manual inspection
    console.log('⏳ Keeping browsers open for 10 seconds...');
    await player1Page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

async function enterLobby(page, playerName) {
  await page.goto('http://localhost:5050');
  await page.waitForLoadState('networkidle');
  
  await page.fill('input[type="text"]', playerName);
  await page.click('button');
  
  // Wait for lobby to load
  await page.waitForTimeout(2000);
  
  // Verify we're in the lobby
  const lobbyTitle = page.locator('h1, h2').filter({ hasText: /lobby/i });
  if (!(await lobbyTitle.isVisible())) {
    throw new Error(`${playerName} failed to reach lobby`);
  }
  
  console.log(`✅ ${playerName} entered lobby`);
  
  // Set up debug monitoring
  await page.evaluate((name) => {
    console.log(`🔧 [${name}] Setting up debug monitoring...`);
    
    // Monitor React state
    window.getRoomState = () => {
      const roomCards = document.querySelectorAll('.lp-roomCard');
      const emptyState = document.querySelector('.lp-emptyState');
      const roomCount = document.querySelector('.lp-roomCount');
      const roomList = document.querySelector('.lp-roomList');
      
      return {
        roomCards: roomCards.length,
        emptyVisible: emptyState && window.getComputedStyle(emptyState).display !== 'none',
        roomCountText: roomCount?.textContent,
        roomListExists: !!roomList,
        roomListVisible: roomList && window.getComputedStyle(roomList).display !== 'none'
      };
    };
    
    // Log every time setRooms might be called (if we can intercept it)
    if (window.React) {
      console.log(`🔧 [${name}] React found, setting up state monitoring`);
    }
  }, playerName);
}

async function checkInitialState(player1Page, player2Page) {
  const p1State = await player1Page.evaluate(() => window.getRoomState());
  const p2State = await player2Page.evaluate(() => window.getRoomState());
  
  console.log('📊 Player 1 initial state:', p1State);
  console.log('📊 Player 2 initial state:', p2State);
}

async function checkPlayer2Updates(player2Page) {
  const state = await player2Page.evaluate(() => window.getRoomState());
  console.log('👀 Player 2 current state:', state);
  
  // Check connection status
  const connectionStatus = await player2Page.locator('.connection-status').textContent();
  console.log('🔗 Player 2 connection:', connectionStatus);
  
  // Check for any JavaScript errors
  const hasErrors = await player2Page.evaluate(() => {
    return !!window.lastError || !!window.onerror;
  });
  console.log('❌ Player 2 has JS errors:', hasErrors);
}

if (require.main === module) {
  comprehensiveRoomTest().catch(console.error);
}

module.exports = { comprehensiveRoomTest };