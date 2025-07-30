const { chromium } = require('playwright');

const TEST_CONFIG = {
  baseUrl: 'http://localhost:5050',
  timeout: 30000,
  headless: false,
  slowMo: 500
};

let testResults = {
  messages: [],
  timeline: [],
  analysis: {},
  bugReport: null
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
        messages.push({
          type: 'sent',
          timestamp,
          player: playerName,
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
        console.error(`Parse error for ${playerName}:`, e);
      }
    });
    
    ws.on('framereceived', data => {
      const timestamp = new Date().toISOString();
      const message = data.payload;
      console.log(`📥 [${playerName}] Received: ${message}`);
      
      try {
        const parsed = JSON.parse(message);
        messages.push({
          type: 'received',
          timestamp,
          player: playerName,
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

async function getRoomCount(page, playerName) {
  try {
    const roomElements = await page.locator('.room-item, [class*="room-"]').all();
    const noRoomsMsg = await page.locator('text=/no rooms|empty/i').first();
    
    if (await noRoomsMsg.isVisible()) {
      console.log(`📋 [${playerName}] No rooms available`);
      return 0;
    }
    
    console.log(`📋 [${playerName}] Found ${roomElements.length} rooms`);
    return roomElements.length;
  } catch (error) {
    console.log(`❌ [${playerName}] Error counting rooms: ${error.message}`);
    return -1;
  }
}

async function createRoom(page, playerName, roomName) {
  console.log(`➕ [${playerName}] Creating room: ${roomName}`);
  
  const createBtn = await page.locator('button').filter({ hasText: /create/i }).first();
  await createBtn.click();
  
  // Handle room name input if present
  const roomNameInput = await page.locator('input[placeholder*="room" i], input[placeholder*="name" i]').first();
  if (await roomNameInput.isVisible({ timeout: 2000 })) {
    await roomNameInput.fill(roomName);
  }
  
  // Confirm creation
  const confirmBtn = await page.locator('button').filter({ hasText: /create|confirm|ok/i }).first();
  if (await confirmBtn.isVisible({ timeout: 2000 })) {
    await confirmBtn.click();
  }
  
  await page.waitForTimeout(1000);
  console.log(`✅ [${playerName}] Room creation completed`);
}

async function testRoomCreationVisibility() {
  console.log('🚀 Starting Room Creation Visibility Test...');
  
  const browser = await chromium.launch({
    headless: TEST_CONFIG.headless,
    slowMo: TEST_CONFIG.slowMo
  });
  
  try {
    // Create separate contexts for each player
    const player1Context = await browser.newContext();
    const player2Context = await browser.newContext();
    
    const player1Page = await player1Context.newPage();
    const player2Page = await player2Context.newPage();
    
    // Set up message capture
    const player1Messages = await captureWebSocketMessages(player1Page, 'Player1');
    const player2Messages = await captureWebSocketMessages(player2Page, 'Player2');
    
    console.log('\n=== PHASE 1: Player 1 joins lobby ===');
    
    // Player 1 enters lobby
    await enterLobby(player1Page, 'Player1');
    
    // Get initial room count for Player 1
    const initialPlayer1Count = await getRoomCount(player1Page, 'Player1');
    console.log(`📊 Player 1 initial room count: ${initialPlayer1Count}`);
    
    console.log('\n=== PHASE 2: Player 1 creates room ===');
    
    // Player 1 creates a room
    const roomName = `TestRoom_${Date.now()}`;
    await createRoom(player1Page, 'Player1', roomName);
    
    // Verify Player 1 can see the room they created
    await player1Page.waitForTimeout(2000);
    const postCreatePlayer1Count = await getRoomCount(player1Page, 'Player1');
    console.log(`📊 Player 1 post-creation room count: ${postCreatePlayer1Count}`);
    
    console.log('\n=== PHASE 3: Player 2 joins lobby ===');
    
    // Player 2 enters lobby
    await enterLobby(player2Page, 'Player2');
    
    console.log('\n=== PHASE 4: Player 2 should see the created room ===');
    
    // Wait for potential auto-update
    await player2Page.waitForTimeout(3000);
    
    // Check if Player 2 sees the room
    const player2RoomCount = await getRoomCount(player2Page, 'Player2');
    console.log(`📊 Player 2 room count: ${player2RoomCount}`);
    
    // Analyze results
    const roomVisibilityWorked = player2RoomCount > 0;
    
    console.log('\n=== ANALYSIS ===');
    
    const analysis = {
      player1InitialCount: initialPlayer1Count,
      player1PostCreateCount: postCreatePlayer1Count,
      player2FinalCount: player2RoomCount,
      roomCreationWorked: postCreatePlayer1Count > initialPlayer1Count,
      roomVisibilityWorked,
      roomListUpdateMessages: testResults.timeline.filter(msg => 
        msg.message && msg.message.event === 'room_list_update'
      ),
      roomCreatedMessages: testResults.timeline.filter(msg => 
        msg.message && (msg.message.event === 'room_created' || msg.message.event === 'create_room')
      )
    };
    
    testResults.analysis = analysis;
    
    // Generate test report
    let testReport = '';
    
    if (analysis.roomCreationWorked && analysis.roomVisibilityWorked) {
      testReport = `✅ SUCCESS: Room creation and visibility working correctly!
      
Player 1 created room: ${analysis.roomCreationWorked ? 'YES' : 'NO'} (${analysis.player1InitialCount} → ${analysis.player1PostCreateCount})
Player 2 sees room: ${analysis.roomVisibilityWorked ? 'YES' : 'NO'} (${analysis.player2FinalCount} rooms visible)

Room List Update Messages: ${analysis.roomListUpdateMessages.length}
Room Created Messages: ${analysis.roomCreatedMessages.length}`;
    } else {
      testReport = `🐛 ISSUE DETECTED: Room Creation/Visibility Problem
      
Player 1 room creation: ${analysis.roomCreationWorked ? '✅ WORKS' : '❌ FAILED'} (${analysis.player1InitialCount} → ${analysis.player1PostCreateCount})
Player 2 room visibility: ${analysis.roomVisibilityWorked ? '✅ WORKS' : '❌ FAILED'} (${analysis.player2FinalCount} rooms visible)

❌ Issue: ${!analysis.roomCreationWorked ? 'Player 1 cannot create rooms' : 'Player 2 cannot see created rooms'}
📨 Room list update messages: ${analysis.roomListUpdateMessages.length}
📨 Room created messages: ${analysis.roomCreatedMessages.length}

WebSocket Message Analysis:
${analysis.roomListUpdateMessages.map(msg => 
  `- ${msg.timestamp} [${msg.player}] ${msg.direction}: ${msg.message.event} - ${
    msg.message.data && msg.message.data.rooms ? msg.message.data.rooms.length : 'unknown'
  } rooms`
).join('\n')}`;
    }
    
    testResults.bugReport = testReport;
    
    console.log('\n' + testReport);
    
    // Keep browsers open for inspection
    console.log('\n⏱️ Keeping browsers open for 15 seconds for inspection...');
    await player1Page.waitForTimeout(15000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    testResults.error = error.message;
  } finally {
    // Save detailed test results
    const fs = require('fs');
    fs.writeFileSync('room-creation-test-report.json', JSON.stringify(testResults, null, 2));
    console.log('\n📄 Detailed test results saved to: room-creation-test-report.json');
    
    await browser.close();
    console.log('🏁 Test completed');
  }
}

// Run the test
if (require.main === module) {
  testRoomCreationVisibility().catch(console.error);
}

module.exports = { testRoomCreationVisibility };