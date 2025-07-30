const { chromium } = require('playwright');
const fs = require('fs');

// Test configuration
const TEST_CONFIG = {
  baseUrl: 'http://localhost:5050',
  timeout: 30000,
  headless: false, // Set to true for headless mode
  slowMo: 500,
  andyName: 'Andy',
  alexanderiumName: 'Alexanderium'
};

// Store captured WebSocket messages and analysis
let testResults = {
  andyMessages: [],
  alexanderiumMessages: [],
  timeline: [],
  analysis: {},
  bugReport: null
};

async function captureWebSocketMessages(page, playerName) {
  const messages = [];
  
  // Capture WebSocket frames
  page.on('websocket', ws => {
    console.log(`🔗 [${playerName}] WebSocket connection established: ${ws.url()}`);
    
    ws.on('framesent', data => {
      const message = data.payload;
      const timestamp = new Date().toISOString();
      console.log(`📤 [${playerName}] Sent: ${message}`);
      
      try {
        const parsed = JSON.parse(message);
        messages.push({
          type: 'sent',
          timestamp,
          message: parsed,
          raw: message
        });
        testResults.timeline.push({
          timestamp,
          player: playerName,
          direction: 'sent',
          message: parsed
        });
      } catch (e) {
        messages.push({
          type: 'sent',
          timestamp,
          message: message,
          raw: message,
          parseError: true
        });
      }
    });
    
    ws.on('framereceived', data => {
      const message = data.payload;
      const timestamp = new Date().toISOString();
      console.log(`📥 [${playerName}] Received: ${message}`);
      
      try {
        const parsed = JSON.parse(message);
        messages.push({
          type: 'received',
          timestamp,
          message: parsed,
          raw: message
        });
        testResults.timeline.push({
          timestamp,
          player: playerName,
          direction: 'received',
          message: parsed
        });
      } catch (e) {
        messages.push({
          type: 'received',
          timestamp,
          message: message,
          raw: message,
          parseError: true
        });
      }
    });
  });
  
  return messages;
}

async function enterLobby(page, playerName) {
  console.log(`🚀 [${playerName}] Starting lobby entry...`);
  
  // Navigate to the application
  await page.goto(TEST_CONFIG.baseUrl);
  await page.waitForLoadState('networkidle');
  
  console.log(`📝 [${playerName}] Looking for player name input...`);
  
  // Enter player name
  const playerNameInput = await page.locator('input[type="text"]').first();
  await playerNameInput.fill(playerName);
  
  // Click start/enter button
  const startButton = await page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
  await startButton.click();
  
  // Wait for lobby to load
  await page.waitForTimeout(2000);
  
  // Verify we're in the lobby
  const lobbyTitle = await page.locator('h1, h2').filter({ hasText: /lobby/i }).first();
  await expect(lobbyTitle).toBeVisible();
  
  console.log(`✅ [${playerName}] Successfully entered lobby`);
  return true;
}

async function getRoomCount(page, playerName) {
  try {
    // Look for room list or "No rooms" message
    const roomElements = await page.locator('.lp-roomList .room-item, [class*="room-"], .room').all();
    const noRoomsMsg = await page.locator('text=/no rooms|empty/i').first();
    
    if (await noRoomsMsg.isVisible()) {
      console.log(`📋 [${playerName}] Lobby shows: No rooms available`);
      return 0;
    }
    
    const count = roomElements.length;
    console.log(`📋 [${playerName}] Current room count: ${count}`);
    return count;
  } catch (error) {
    console.log(`❌ [${playerName}] Error counting rooms: ${error.message}`);
    return -1;
  }
}

async function createRoom(page, playerName, roomName) {
  console.log(`➕ [${playerName}] Creating room: ${roomName}`);
  
  // Click create room button
  const createRoomBtn = await page.locator('button').filter({ hasText: /create/i }).first();
  await createRoomBtn.click();
  
  // Fill room name if there's an input
  const roomNameInput = await page.locator('input[placeholder*="room" i], input[placeholder*="name" i]').first();
  if (await roomNameInput.isVisible({ timeout: 2000 })) {
    await roomNameInput.fill(roomName);
  }
  
  // Confirm creation
  const confirmBtn = await page.locator('button').filter({ hasText: /create|confirm|ok/i }).first();
  if (await confirmBtn.isVisible({ timeout: 2000 })) {
    await confirmBtn.click();
  }
  
  console.log(`✅ [${playerName}] Room creation initiated`);
  
  // Wait a bit for the room to be created
  await page.waitForTimeout(1000);
}

async function testLobbyAutoUpdate() {
  console.log('🚀 Starting Lobby Auto-Update Test...');
  
  const browser = await chromium.launch({
    headless: TEST_CONFIG.headless,
    slowMo: TEST_CONFIG.slowMo
  });
  
  try {
    // Create two browser contexts for two players
    const andyContext = await browser.newContext();
    const alexanderiumContext = await browser.newContext();
    
    const andyPage = await andyContext.newPage();
    const alexanderiumPage = await alexanderiumContext.newPage();
    
    // Set up WebSocket message capture
    const andyMessages = await captureWebSocketMessages(andyPage, TEST_CONFIG.andyName);
    const alexanderiumMessages = await captureWebSocketMessages(alexanderiumPage, TEST_CONFIG.alexanderiumName);
    
    testResults.andyMessages = andyMessages;
    testResults.alexanderiumMessages = alexanderiumMessages;
    
    console.log('\n=== PHASE 1: Both players enter lobby ===');
    
    // Both players enter lobby
    await Promise.all([
      enterLobby(andyPage, TEST_CONFIG.andyName),
      enterLobby(alexanderiumPage, TEST_CONFIG.alexanderiumName)
    ]);
    
    // Initial room counts
    const initialAndyCount = await getRoomCount(andyPage, TEST_CONFIG.andyName);
    const initialAlexCount = await getRoomCount(alexanderiumPage, TEST_CONFIG.alexanderiumName);
    
    console.log(`📊 Initial room counts - Andy: ${initialAndyCount}, Alexanderium: ${initialAlexCount}`);
    
    console.log('\n=== PHASE 2: Andy creates room ===');
    
    // Andy creates a room
    const roomName = `AndyRoom_${Date.now()}`;
    await createRoom(andyPage, TEST_CONFIG.andyName, roomName);
    
    console.log('\n=== PHASE 3: Check if Alexanderium sees the room automatically ===');
    
    // Wait for potential auto-update
    await alexanderiumPage.waitForTimeout(3000);
    
    // Check room counts after creation
    const postCreateAlexCount = await getRoomCount(alexanderiumPage, TEST_CONFIG.alexanderiumName);
    
    console.log(`📊 Post-creation room count - Alexanderium: ${postCreateAlexCount}`);
    
    // Test the bug: Auto-update should work but doesn't
    const autoUpdateWorked = postCreateAlexCount > initialAlexCount;
    
    console.log('\n=== PHASE 4: Manual refresh test ===');
    
    // Test manual refresh to see if backend has the data
    await alexanderiumPage.reload();
    await enterLobby(alexanderiumPage, `${TEST_CONFIG.alexanderiumName}_Refresh`);
    await alexanderiumPage.waitForTimeout(1000);
    
    const manualRefreshCount = await getRoomCount(alexanderiumPage, `${TEST_CONFIG.alexanderiumName}_Refresh`);
    
    console.log(`📊 Manual refresh room count: ${manualRefreshCount}`);
    
    console.log('\n=== ANALYSIS ===');
    
    // Analyze the results
    const analysis = {
      initialRoomCount: initialAlexCount,
      postCreateRoomCount: postCreateAlexCount,
      manualRefreshRoomCount: manualRefreshCount,
      autoUpdateWorked,
      backendHasData: manualRefreshRoomCount > initialAlexCount,
      bugConfirmed: !autoUpdateWorked && (manualRefreshRoomCount > initialAlexCount),
      roomListUpdateMessages: [],
      roomCreatedMessages: []
    };
    
    // Analyze WebSocket messages
    testResults.timeline.forEach(msg => {
      if (msg.message && msg.message.type === 'room_list_update') {
        analysis.roomListUpdateMessages.push({
          timestamp: msg.timestamp,
          player: msg.player,
          direction: msg.direction,
          roomCount: msg.message.data && msg.message.data.rooms ? msg.message.data.rooms.length : 'unknown',
          rooms: msg.message.data && msg.message.data.rooms ? msg.message.data.rooms : []
        });
      }
      
      if (msg.message && (msg.message.type === 'room_created' || msg.message.action === 'create_room')) {
        analysis.roomCreatedMessages.push({
          timestamp: msg.timestamp,
          player: msg.player,
          direction: msg.direction,
          message: msg.message
        });
      }
    });
    
    testResults.analysis = analysis;
    
    // Generate bug report
    let bugReport = '';
    
    if (analysis.bugConfirmed) {
      bugReport = `🐛 BUG CONFIRMED: Lobby Auto-Update Failure
      
Initial State: ${analysis.initialRoomCount} rooms
After Andy creates room: ${analysis.postCreateRoomCount} rooms (should be ${analysis.initialRoomCount + 1})
After manual refresh: ${analysis.manualRefreshRoomCount} rooms

❌ Auto-update failed: Alexanderium did not see Andy's room automatically
✅ Backend has data: Manual refresh shows the room exists
📨 Room list update messages: ${analysis.roomListUpdateMessages.length}

ROOT CAUSE: The backend has the room data but either:
1. Not sending room_list_update events after room creation
2. Sending room_list_update with empty rooms array (0 rooms)
3. Alexanderium is not receiving/processing the updates correctly

WebSocket Messages Analysis:
${analysis.roomListUpdateMessages.map(msg => 
  `- ${msg.timestamp} [${msg.player}] ${msg.direction}: ${msg.roomCount} rooms`
).join('\n')}`;
    } else if (analysis.autoUpdateWorked) {
      bugReport = `✅ SUCCESS: Auto-update is working correctly!
Alexanderium saw Andy's room automatically appear in the lobby.`;
    } else {
      bugReport = `⚠️ INCONCLUSIVE: Need more data to determine the issue.`;
    }
    
    testResults.bugReport = bugReport;
    
    console.log('\n' + bugReport);
    
    // Keep browsers open for manual inspection
    console.log('\n⏱️ Keeping browsers open for 15 seconds for manual inspection...');
    await andyPage.waitForTimeout(15000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    testResults.error = error.message;
  } finally {
    // Save detailed test results
    fs.writeFileSync('lobby-bug-report.json', JSON.stringify(testResults, null, 2));
    console.log('\n📄 Detailed test results saved to: lobby-bug-report.json');
    
    await browser.close();
    console.log('🏁 Test completed');
  }
}

// Helper function for Playwright expect
const expect = (locator) => ({
  toBeVisible: async (options = {}) => {
    const isVisible = await locator.isVisible(options);
    if (!isVisible) {
      throw new Error(`Element not visible: ${locator}`);
    }
  }
});

// Run the test
if (require.main === module) {
  testLobbyAutoUpdate().catch(console.error);
}

module.exports = { testLobbyAutoUpdate };