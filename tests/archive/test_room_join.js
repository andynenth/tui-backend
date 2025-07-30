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
  
  await page.waitForTimeout(2000);
  console.log(`✅ [${playerName}] Room creation completed`);
}

async function joinRoom(page, playerName, roomCode) {
  console.log(`🚪 [${playerName}] Attempting to join room: ${roomCode}`);
  
  // Try to find a join button or room to click
  const joinBtn = await page.locator('button').filter({ hasText: /join/i }).first();
  if (await joinBtn.isVisible({ timeout: 2000 })) {
    await joinBtn.click();
    
    // Look for room code input
    const roomCodeInput = await page.locator('input[placeholder*="code" i], input[placeholder*="room" i]').first();
    if (await roomCodeInput.isVisible({ timeout: 2000 })) {
      await roomCodeInput.fill(roomCode);
      
      // Find join/confirm button
      const confirmJoinBtn = await page.locator('button').filter({ hasText: /join|confirm|ok/i }).first();
      if (await confirmJoinBtn.isVisible({ timeout: 2000 })) {
        await confirmJoinBtn.click();
      }
    }
  } else {
    // Alternative: try clicking directly on a room
    const roomElement = await page.locator(`text=${roomCode}, [data-room-code="${roomCode}"]`).first();
    if (await roomElement.isVisible({ timeout: 2000 })) {
      await roomElement.click();
    } else {
      console.log(`❌ [${playerName}] Could not find room or join button`);
    }
  }
  
  await page.waitForTimeout(3000);
  console.log(`🔍 [${playerName}] Join attempt completed`);
}

async function checkForErrors(page, playerName) {
  // Look for error messages
  const errorMessages = await page.locator('text=/error|lobby error|failed/i').all();
  if (errorMessages.length > 0) {
    for (const error of errorMessages) {
      const errorText = await error.textContent();
      console.log(`❌ [${playerName}] Error found: ${errorText}`);
    }
    return true;
  }
  return false;
}

async function testRoomJoin() {
  console.log('🚀 Starting Room Join Test...');
  
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
    
    console.log('\n=== PHASE 1: Player 1 creates room ===');
    
    // Player 1 enters lobby and creates room
    await enterLobby(player1Page, 'Player1');
    const roomName = `TestRoom_${Date.now()}`;
    await createRoom(player1Page, 'Player1', roomName);
    
    // Extract room code from WebSocket messages
    let roomCode = null;
    const roomCreatedMsg = testResults.timeline.find(msg => 
      msg.message && msg.message.event === 'room_created' && msg.player === 'Player1'
    );
    if (roomCreatedMsg && roomCreatedMsg.message.data) {
      roomCode = roomCreatedMsg.message.data.room_code;
      console.log(`🔑 Room code extracted: ${roomCode}`);
    } else {
      console.log(`❌ Could not extract room code from messages`);
    }
    
    console.log('\n=== PHASE 2: Player 2 attempts to join room ===');
    
    // Player 2 enters lobby
    await enterLobby(player2Page, 'Player2');
    
    // Check for any errors before join attempt
    await checkForErrors(player2Page, 'Player2');
    
    if (roomCode) {
      // Player 2 attempts to join the room
      await joinRoom(player2Page, 'Player2', roomCode);
      
      // Check for join success/failure
      await page.waitForTimeout(3000);
      
      // Check for errors after join attempt
      const hasErrors = await checkForErrors(player2Page, 'Player2');
      
      // Check if Player 2 successfully joined (look for room page indicators)
      const inRoom = await player2Page.locator('h1, h2').filter({ hasText: /room|game/i }).isVisible();
      const backToLobbyBtn = await player2Page.locator('button').filter({ hasText: /lobby|back/i }).isVisible();
      
      console.log(`🎯 [Player2] In room page: ${inRoom}`);
      console.log(`🏠 [Player2] Back to lobby button visible: ${backToLobbyBtn}`);
      
      const joinSuccessful = inRoom || backToLobbyBtn;
      
      console.log('\n=== ANALYSIS ===');
      
      const analysis = {
        roomCode,
        joinSuccessful,
        hasErrors,
        joinMessages: testResults.timeline.filter(msg => 
          msg.message && (msg.message.event === 'join_room' || msg.message.event === 'room_joined')
        ),
        errorMessages: testResults.timeline.filter(msg => 
          msg.message && msg.message.event === 'error'
        )
      };
      
      testResults.analysis = analysis;
      
      // Generate test report
      let testReport = '';
      
      if (joinSuccessful && !hasErrors) {
        testReport = `✅ SUCCESS: Room join functionality working!
        
Room code: ${roomCode}
Join successful: ${joinSuccessful ? 'YES' : 'NO'}
Errors detected: ${hasErrors ? 'YES' : 'NO'}

Join Messages: ${analysis.joinMessages.length}
Error Messages: ${analysis.errorMessages.length}`;
      } else {
        testReport = `🐛 ISSUE DETECTED: Room Join Problem
        
Room code: ${roomCode}
Join successful: ${joinSuccessful ? '✅ YES' : '❌ NO'}
Errors detected: ${hasErrors ? '❌ YES' : '✅ NO'}

❌ Issue: ${hasErrors ? 'Join errors occurred' : 'Join did not complete successfully'}
📨 Join messages: ${analysis.joinMessages.length}
📨 Error messages: ${analysis.errorMessages.length}

Error Messages:
${analysis.errorMessages.map(msg => 
  `- ${msg.timestamp} [${msg.player}]: ${JSON.stringify(msg.message.data)}`
).join('\n')}`;
      }
      
      testResults.bugReport = testReport;
      console.log('\n' + testReport);
    } else {
      console.log('\n❌ Cannot test join - no room code available');
    }
    
    // Keep browsers open for inspection
    console.log('\n⏱️ Keeping browsers open for 15 seconds for inspection...');
    await player1Page.waitForTimeout(15000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    testResults.error = error.message;
  } finally {
    // Save detailed test results
    const fs = require('fs');
    fs.writeFileSync('room-join-test-report.json', JSON.stringify(testResults, null, 2));
    console.log('\n📄 Detailed test results saved to: room-join-test-report.json');
    
    await browser.close();
    console.log('🏁 Test completed');
  }
}

// Run the test
if (require.main === module) {
  testRoomJoin().catch(console.error);
}

module.exports = { testRoomJoin };