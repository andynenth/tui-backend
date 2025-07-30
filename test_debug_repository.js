const { chromium } = require('playwright');

const TEST_CONFIG = {
  baseUrl: 'http://localhost:5050',
  timeout: 30000,
  headless: false,
  slowMo: 500
};

async function captureWebSocketMessages(page, playerName) {
  const messages = [];
  
  page.on('websocket', ws => {
    console.log(`🔗 [${playerName}] WebSocket connected: ${ws.url()}`);
    
    ws.on('framesent', data => {
      const timestamp = new Date().toISOString();
      const message = data.payload;
      console.log(`📤 [${playerName}] Sent: ${message}`);
      
      try {
        const parsed = JSON.parse(message);
        messages.push({ type: 'sent', timestamp, player: playerName, message: parsed, raw: message });
      } catch (e) {
        console.error(`Parse error for ${playerName}:`, e);
      }
    });
    
    ws.on('framereceived', data => {
      const timestamp = new Date().toISOString();
      const message = data.payload;
      console.log(`📥 [${playerName}] Received: ${message}`);
      
      try {
        const parsed = JSON.parse(message);
        messages.push({ type: 'received', timestamp, player: playerName, message: parsed, raw: message });
      } catch (e) {
        console.error(`Parse error for ${playerName}:`, e);
      }
    });
  });
  
  return messages;
}

async function enterLobby(page, playerName) {
  console.log(`🚀 [${playerName}] Entering lobby...`);
  
  await page.goto(TEST_CONFIG.baseUrl);
  await page.waitForLoadState('networkidle');
  
  const nameInput = await page.locator('input[type="text"]').first();
  await nameInput.fill(playerName);
  
  const startButton = await page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
  await startButton.click();
  
  await page.waitForTimeout(2000);
  
  const lobbyTitle = await page.locator('h1, h2').filter({ hasText: /lobby/i }).first();
  if (!(await lobbyTitle.isVisible())) {
    throw new Error(`${playerName} failed to reach lobby`);
  }
  
  console.log(`✅ [${playerName}] Successfully entered lobby`);
}

async function debugRepositorySharing() {
  console.log('🚀 Starting Repository Debug Test...');
  
  const browser = await chromium.launch({
    headless: TEST_CONFIG.headless,
    slowMo: TEST_CONFIG.slowMo
  });
  
  try {
    // Create TWO separate contexts to simulate different users
    const player1Context = await browser.newContext();
    const player2Context = await browser.newContext();
    
    const player1Page = await player1Context.newPage();
    const player2Page = await player2Context.newPage();
    
    // Set up message capture
    const player1Messages = await captureWebSocketMessages(player1Page, 'Player1');
    const player2Messages = await captureWebSocketMessages(player2Page, 'Player2');
    
    console.log('\n=== STEP 1: Both players enter lobby ===');
    
    // Both players enter lobby
    await enterLobby(player1Page, 'Player1');
    await enterLobby(player2Page, 'Player2');
    
    console.log('\n=== STEP 2: Player 1 creates room ===');
    
    // Player 1 creates room
    const createBtn = await player1Page.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    
    // Wait for room creation
    await player1Page.waitForTimeout(3000);
    
    console.log('\n=== STEP 3: Player 2 requests room list ===');
    
    // Player 2 manually requests room list to see current state
    await player2Page.evaluate(() => {
      // Send get_rooms event via WebSocket
      if (window.gameClient && window.gameClient.socket) {
        window.gameClient.socket.send(JSON.stringify({
          event: 'get_rooms',
          data: {},
          sequence: 999,
          timestamp: Date.now(),
          id: 'debug-request'
        }));
      }
    });
    
    // Wait for response
    await player2Page.waitForTimeout(2000);
    
    console.log('\n=== ANALYSIS ===');
    console.log(`📨 Player 1 total messages: ${player1Messages.length}`);
    console.log(`📨 Player 2 total messages: ${player2Messages.length}`);
    
    // Find room_list_update messages
    const player1RoomUpdates = player1Messages.filter(m => 
      m.type === 'received' && m.message.event === 'room_list_update'
    );
    const player2RoomUpdates = player2Messages.filter(m => 
      m.type === 'received' && m.message.event === 'room_list_update'
    );
    
    console.log(`\n📋 Player 1 room_list_update messages: ${player1RoomUpdates.length}`);
    player1RoomUpdates.forEach((msg, i) => {
      const roomCount = msg.message.data.rooms ? msg.message.data.rooms.length : 0;
      console.log(`  ${i+1}. ${msg.timestamp}: ${roomCount} rooms`);
    });
    
    console.log(`\n📋 Player 2 room_list_update messages: ${player2RoomUpdates.length}`);
    player2RoomUpdates.forEach((msg, i) => {
      const roomCount = msg.message.data.rooms ? msg.message.data.rooms.length : 0;
      console.log(`  ${i+1}. ${msg.timestamp}: ${roomCount} rooms`);
    });
    
    // Check if both players see the same final room count
    const player1LastUpdate = player1RoomUpdates[player1RoomUpdates.length - 1];
    const player2LastUpdate = player2RoomUpdates[player2RoomUpdates.length - 1];
    
    const player1FinalCount = player1LastUpdate ? player1LastUpdate.message.data.rooms.length : 0;
    const player2FinalCount = player2LastUpdate ? player2LastUpdate.message.data.rooms.length : 0;
    
    console.log(`\n🎯 FINAL ANALYSIS:`);
    console.log(`   Player 1 final room count: ${player1FinalCount}`);
    console.log(`   Player 2 final room count: ${player2FinalCount}`);
    
    if (player1FinalCount === player2FinalCount && player1FinalCount > 0) {
      console.log(`   ✅ SUCCESS: Repository sharing is working!`);
    } else if (player1FinalCount > 0 && player2FinalCount === 0) {
      console.log(`   ❌ ISSUE: Repository instances are still separate!`);
    } else {
      console.log(`   ❓ UNCLEAR: Both players see same count (${player1FinalCount})`);
    }
    
    // Keep browsers open for inspection
    console.log('\n⏱️ Keeping browsers open for 10 seconds for inspection...');
    await player1Page.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
    console.log('🏁 Test completed');
  }
}

// Run the test
if (require.main === module) {
  debugRepositorySharing().catch(console.error);
}

module.exports = { debugRepositorySharing };