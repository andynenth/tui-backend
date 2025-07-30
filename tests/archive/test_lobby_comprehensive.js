const { chromium } = require('playwright');
const fs = require('fs');

// Test Configuration
const TEST_CONFIG = {
  baseUrl: 'http://localhost:5050',
  timeout: 30000,
  headless: false,
  slowMo: 800,
  players: ['Andy', 'Alexanderium'],
  testDuration: 15000, // 15 seconds for observation
  retryAttempts: 3
};

// Global test results storage
let testResults = {
  testName: 'Lobby Auto-Update Comprehensive Test',
  startTime: null,
  endTime: null,
  messages: [],
  timeline: [],
  analysis: {},
  bugReport: null,
  performance: {},
  webSocketConnections: {},
  errors: []
};

/**
 * Capture and analyze WebSocket messages for a specific player
 */
async function captureWebSocketMessages(page, playerName) {
  const messages = [];
  
  console.log(`🔗 [${playerName}] Setting up WebSocket message capture...`);
  
  page.on('websocket', ws => {
    const wsUrl = ws.url();
    console.log(`🌐 [${playerName}] WebSocket connected: ${wsUrl}`);
    
    testResults.webSocketConnections[playerName] = {
      url: wsUrl,
      connectedAt: new Date().toISOString(),
      status: 'connected'
    };
    
    ws.on('framesent', data => {
      const timestamp = new Date().toISOString();
      const message = data.payload;
      
      try {
        const parsed = JSON.parse(message);
        const messageData = {
          type: 'sent',
          timestamp,
          player: playerName,
          message: parsed,
          raw: message,
          wsUrl
        };
        
        messages.push(messageData);
        testResults.messages.push(messageData);
        testResults.timeline.push({
          timestamp,
          player: playerName,
          direction: 'sent',
          event: parsed.event || parsed.action || 'unknown',
          message: parsed
        });
        
        console.log(`📤 [${playerName}] SENT: ${message}`);
      } catch (e) {
        console.error(`❌ [${playerName}] Failed to parse sent message:`, e.message);
        testResults.errors.push({
          type: 'parse_error',
          player: playerName,
          direction: 'sent',
          message: message,
          error: e.message,
          timestamp
        });
      }
    });
    
    ws.on('framereceived', data => {
      const timestamp = new Date().toISOString();
      const message = data.payload;
      
      try {
        const parsed = JSON.parse(message);
        const messageData = {
          type: 'received',
          timestamp,
          player: playerName,
          message: parsed,
          raw: message,
          wsUrl
        };
        
        messages.push(messageData);
        testResults.messages.push(messageData);
        testResults.timeline.push({
          timestamp,
          player: playerName,
          direction: 'received',
          event: parsed.event || parsed.action || 'unknown',
          message: parsed
        });
        
        console.log(`📥 [${playerName}] RECEIVED: ${message}`);
        
        // Special handling for critical events
        if (parsed.event === 'room_list_update' || parsed.event === 'room_created') {
          console.log(`🚨 [${playerName}] CRITICAL EVENT: ${parsed.event}`, parsed.data || parsed);
        }
        
      } catch (e) {
        console.error(`❌ [${playerName}] Failed to parse received message:`, e.message);
        testResults.errors.push({
          type: 'parse_error',
          player: playerName,
          direction: 'received',
          message: message,
          error: e.message,
          timestamp
        });
      }
    });
    
    ws.on('close', () => {
      console.log(`🔌 [${playerName}] WebSocket disconnected`);
      testResults.webSocketConnections[playerName].status = 'disconnected';
      testResults.webSocketConnections[playerName].disconnectedAt = new Date().toISOString();
    });
  });
  
  return messages;
}

/**
 * Robust lobby entry with comprehensive error handling
 */
async function enterLobby(page, playerName) {
  console.log(`🚀 [${playerName}] Starting lobby entry process...`);
  
  try {
    // Navigate to the application
    await page.goto(TEST_CONFIG.baseUrl, { waitUntil: 'networkidle' });
    console.log(`🌐 [${playerName}] Navigated to ${TEST_CONFIG.baseUrl}`);
    
    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Find and fill the name input
    const nameInput = await page.locator('input[type="text"]').first();
    await nameInput.waitFor({ state: 'visible', timeout: 10000 });
    await nameInput.fill(playerName);
    console.log(`✍️ [${playerName}] Entered name: ${playerName}`);
    
    // Find and click the start/enter button
    const startButton = await page.locator('button').filter({ 
      hasText: /play|start|enter|lobby|begin/i 
    }).first();
    await startButton.waitFor({ state: 'visible', timeout: 10000 });
    await startButton.click();
    console.log(`🔘 [${playerName}] Clicked start button`);
    
    // Wait for lobby to load
    await page.waitForTimeout(3000);
    
    // Verify we're in the lobby
    const lobbyIndicators = [
      page.locator('h1, h2, h3').filter({ hasText: /lobby/i }),
      page.locator('[class*="lobby"]'),
      page.locator('text=/create.*room/i'),
      page.locator('button').filter({ hasText: /create/i })
    ];
    
    let lobbyFound = false;
    for (const indicator of lobbyIndicators) {
      try {
        if (await indicator.first().isVisible({ timeout: 2000 })) {
          lobbyFound = true;
          break;
        }
      } catch (e) {
        // Continue checking other indicators
      }
    }
    
    if (!lobbyFound) {
      throw new Error(`${playerName} did not reach lobby - no lobby indicators found`);
    }
    
    console.log(`✅ [${playerName}] Successfully entered lobby`);
    
  } catch (error) {
    console.error(`❌ [${playerName}] Failed to enter lobby:`, error.message);
    testResults.errors.push({
      type: 'lobby_entry_error',
      player: playerName,
      error: error.message,
      timestamp: new Date().toISOString()
    });
    throw error;
  }
}

/**
 * Get current room count with detailed analysis
 */
async function getRoomCount(page, playerName) {
  try {
    console.log(`📊 [${playerName}] Counting rooms...`);
    
    // Wait a moment for any pending updates
    await page.waitForTimeout(500);
    
    // Multiple strategies to find rooms
    const roomSelectors = [
      '.room-item',
      '[class*="room-"]',
      '[data-testid*="room"]',
      'li:has-text("Room")',
      'div:has-text("Room")'
    ];
    
    let maxRoomCount = 0;
    let foundSelector = null;
    
    for (const selector of roomSelectors) {
      try {
        const elements = await page.locator(selector).all();
        if (elements.length > maxRoomCount) {
          maxRoomCount = elements.length;
          foundSelector = selector;
        }
      } catch (e) {
        // Continue with next selector
      }
    }
    
    // Check for "no rooms" messages
    const noRoomsSelectors = [
      'text=/no rooms/i',
      'text=/empty/i',
      'text=/0 rooms/i',
      '[class*="empty"]'
    ];
    
    let noRoomsFound = false;
    for (const selector of noRoomsSelectors) {
      try {
        if (await page.locator(selector).first().isVisible({ timeout: 1000 })) {
          noRoomsFound = true;
          break;
        }
      } catch (e) {
        // Continue checking
      }
    }
    
    if (noRoomsFound && maxRoomCount === 0) {
      console.log(`📋 [${playerName}] No rooms message detected`);
      return 0;
    }
    
    console.log(`📋 [${playerName}] Found ${maxRoomCount} rooms using selector: ${foundSelector || 'none'}`);
    
    // Take screenshot for debugging
    await page.screenshot({ 
      path: `lobby-${playerName.toLowerCase()}-${Date.now()}.png`,
      fullPage: true 
    });
    
    return maxRoomCount;
    
  } catch (error) {
    console.error(`❌ [${playerName}] Error counting rooms:`, error.message);
    testResults.errors.push({
      type: 'room_count_error',
      player: playerName,
      error: error.message,
      timestamp: new Date().toISOString()
    });
    return -1;
  }
}

/**
 * Create a room with comprehensive error handling
 */
async function createRoom(page, playerName, roomName) {
  console.log(`➕ [${playerName}] Creating room: ${roomName}`);
  
  try {
    // Find create button
    const createSelectors = [
      'button:has-text("Create")',
      'button:has-text("New")',
      '[data-testid*="create"]',
      'button[class*="create"]'
    ];
    
    let createButton = null;
    for (const selector of createSelectors) {
      try {
        const button = page.locator(selector).first();
        if (await button.isVisible({ timeout: 2000 })) {
          createButton = button;
          break;
        }
      } catch (e) {
        // Continue with next selector
      }
    }
    
    if (!createButton) {
      throw new Error('Create button not found');
    }
    
    await createButton.click();
    console.log(`🔘 [${playerName}] Clicked create button`);
    
    // Handle room name input if present
    await page.waitForTimeout(1000);
    
    const nameInputSelectors = [
      'input[placeholder*="room" i]',
      'input[placeholder*="name" i]',
      'input[type="text"]:visible'
    ];
    
    for (const selector of nameInputSelectors) {
      try {
        const input = page.locator(selector).first();
        if (await input.isVisible({ timeout: 2000 })) {
          await input.fill(roomName);
          console.log(`✍️ [${playerName}] Entered room name: ${roomName}`);
          break;
        }
      } catch (e) {
        // Continue with next selector
      }
    }
    
    // Look for confirmation button
    const confirmSelectors = [
      'button:has-text("Create")',
      'button:has-text("Confirm")',
      'button:has-text("OK")',
      'button:has-text("Submit")'
    ];
    
    for (const selector of confirmSelectors) {
      try {
        const button = page.locator(selector).first();
        if (await button.isVisible({ timeout: 2000 })) {
          await button.click();
          console.log(`🔘 [${playerName}] Clicked confirm button`);
          break;
        }
      } catch (e) {
        // Continue with next selector
      }
    }
    
    await page.waitForTimeout(2000);
    console.log(`✅ [${playerName}] Room creation process completed`);
    
  } catch (error) {
    console.error(`❌ [${playerName}] Failed to create room:`, error.message);
    testResults.errors.push({
      type: 'room_creation_error',
      player: playerName,
      roomName,
      error: error.message,
      timestamp: new Date().toISOString()
    });
    throw error;
  }
}

/**
 * Analyze test results and generate comprehensive report
 */
function analyzeTestResults() {
  console.log('\n🔍 Analyzing test results...');
  
  const analysis = {
    totalMessages: testResults.messages.length,
    messagesByPlayer: {},
    eventTypes: {},
    criticalEvents: [],
    roomListUpdates: [],
    roomCreatedEvents: [],
    performanceMetrics: {},
    webSocketHealth: {},
    errorSummary: {}
  };
  
  // Analyze messages by player
  testResults.messages.forEach(msg => {
    if (!analysis.messagesByPlayer[msg.player]) {
      analysis.messagesByPlayer[msg.player] = { sent: 0, received: 0 };
    }
    analysis.messagesByPlayer[msg.player][msg.type]++;
    
    // Count event types
    const event = msg.message?.event || msg.message?.action || 'unknown';
    analysis.eventTypes[event] = (analysis.eventTypes[event] || 0) + 1;
    
    // Track critical events
    if (['room_list_update', 'room_created', 'error', 'disconnect'].includes(event)) {
      analysis.criticalEvents.push({
        timestamp: msg.timestamp,
        player: msg.player,
        direction: msg.type,
        event,
        data: msg.message
      });
    }
    
    // Specific event tracking
    if (event === 'room_list_update') {
      analysis.roomListUpdates.push({
        timestamp: msg.timestamp,
        player: msg.player,
        direction: msg.type,
        roomCount: msg.message.data?.rooms?.length || 'unknown',
        data: msg.message
      });
    }
    
    if (event === 'room_created' || event === 'create_room') {
      analysis.roomCreatedEvents.push({
        timestamp: msg.timestamp,
        player: msg.player,
        direction: msg.type,
        data: msg.message
      });
    }
  });
  
  // WebSocket health analysis
  Object.keys(testResults.webSocketConnections).forEach(player => {
    const conn = testResults.webSocketConnections[player];
    analysis.webSocketHealth[player] = {
      status: conn.status,
      connectedAt: conn.connectedAt,
      disconnectedAt: conn.disconnectedAt || null,
      messagesSent: analysis.messagesByPlayer[player]?.sent || 0,
      messagesReceived: analysis.messagesByPlayer[player]?.received || 0
    };
  });
  
  // Error summary
  const errorTypes = {};
  testResults.errors.forEach(error => {
    errorTypes[error.type] = (errorTypes[error.type] || 0) + 1;
  });
  analysis.errorSummary = errorTypes;
  
  testResults.analysis = analysis;
  
  return analysis;
}

/**
 * Generate detailed bug report
 */
function generateBugReport(testPassed, initialCounts, finalCounts) {
  const analysis = testResults.analysis;
  
  let report = `
🐛 LOBBY AUTO-UPDATE TEST REPORT
═══════════════════════════════════════

📊 TEST SUMMARY:
- Status: ${testPassed ? '✅ PASSED' : '❌ FAILED'}
- Duration: ${((testResults.endTime - testResults.startTime) / 1000).toFixed(2)}s
- Players: ${TEST_CONFIG.players.join(', ')}
- Total Messages: ${analysis.totalMessages}
- Errors: ${testResults.errors.length}

📈 ROOM COUNT ANALYSIS:
- Andy Initial: ${initialCounts.Andy}
- Alexanderium Initial: ${initialCounts.Alexanderium}
- Andy Final: ${finalCounts.Andy}
- Alexanderium Final: ${finalCounts.Alexanderium}
- Expected Auto-Update: ${testPassed ? 'WORKING' : 'BROKEN'}

🌐 WEBSOCKET HEALTH:
${Object.entries(analysis.webSocketHealth).map(([player, health]) => 
  `- ${player}: ${health.status} (Sent: ${health.messagesSent}, Received: ${health.messagesReceived})`
).join('\n')}

📨 CRITICAL EVENTS:
- Room List Updates: ${analysis.roomListUpdates.length}
- Room Created Events: ${analysis.roomCreatedEvents.length}
- Total Critical Events: ${analysis.criticalEvents.length}

🔍 ROOM LIST UPDATE DETAILS:
${analysis.roomListUpdates.map(update => 
  `- ${update.timestamp} [${update.player}] ${update.direction}: ${update.roomCount} rooms`
).join('\n') || 'No room list updates detected'}

🚨 ERROR SUMMARY:
${Object.entries(analysis.errorSummary).map(([type, count]) => 
  `- ${type}: ${count}`
).join('\n') || 'No errors detected'}

📋 DETAILED TIMELINE:
${testResults.timeline.slice(0, 20).map(event => 
  `${event.timestamp} [${event.player}] ${event.direction}: ${event.event}`
).join('\n')}
${testResults.timeline.length > 20 ? `\n... and ${testResults.timeline.length - 20} more events` : ''}
`;

  if (!testPassed) {
    report += `

🐛 BUG DIAGNOSIS:
The lobby auto-update is NOT working correctly. Here's what we observed:

1. Andy created a room successfully
2. Alexanderium should have seen the room appear automatically
3. Room list update events: ${analysis.roomListUpdates.length}
4. Backend is ${analysis.roomListUpdates.length > 0 ? 'sending' : 'NOT sending'} room_list_update events

LIKELY CAUSES:
${analysis.roomListUpdates.length === 0 ? 
  '- Backend is not broadcasting room_list_update events\n- WebSocket connection issues\n- Event handling problems in the backend' :
  '- Frontend is not processing room_list_update events correctly\n- UI update issues\n- State management problems'
}

RECOMMENDED FIXES:
1. Check backend room broadcast logic
2. Verify WebSocket event handling
3. Debug frontend state updates
4. Test WebSocket connection stability
`;
  }
  
  return report;
}

/**
 * Main test function
 */
async function testLobbyAutoUpdate() {
  console.log('🚀 Starting Comprehensive Lobby Auto-Update Test...\n');
  
  testResults.startTime = Date.now();
  
  const browser = await chromium.launch({
    headless: TEST_CONFIG.headless,
    slowMo: TEST_CONFIG.slowMo
  });
  
  try {
    // Create separate contexts for each player
    const andyContext = await browser.newContext();
    const alexContext = await browser.newContext();
    
    const andyPage = await andyContext.newPage();
    const alexPage = await alexContext.newPage();
    
    // Set up message capture
    const andyMessages = await captureWebSocketMessages(andyPage, 'Andy');
    const alexMessages = await captureWebSocketMessages(alexPage, 'Alexanderium');
    
    console.log('═══ PHASE 1: LOBBY ENTRY ═══');
    
    // Both players enter lobby
    await Promise.all([
      enterLobby(andyPage, 'Andy'),
      enterLobby(alexPage, 'Alexanderium')
    ]);
    
    // Get initial room counts
    console.log('\n═══ PHASE 2: INITIAL STATE ═══');
    const initialCounts = {
      Andy: await getRoomCount(andyPage, 'Andy'),
      Alexanderium: await getRoomCount(alexPage, 'Alexanderium')
    };
    
    console.log(`📊 Initial room counts - Andy: ${initialCounts.Andy}, Alexanderium: ${initialCounts.Alexanderium}`);
    
    console.log('\n═══ PHASE 3: ROOM CREATION ═══');
    
    // Andy creates a room
    const roomName = `TestRoom_${Date.now()}`;
    await createRoom(andyPage, 'Andy', roomName);
    
    console.log('\n═══ PHASE 4: AUTO-UPDATE VERIFICATION ═══');
    
    // Wait for auto-update with multiple checks
    const checkInterval = 1000;
    const maxWaitTime = 10000;
    let waitTime = 0;
    let autoUpdateDetected = false;
    
    while (waitTime < maxWaitTime && !autoUpdateDetected) {
      await alexPage.waitForTimeout(checkInterval);
      waitTime += checkInterval;
      
      const currentAlexCount = await getRoomCount(alexPage, 'Alexanderium');
      if (currentAlexCount > initialCounts.Alexanderium) {
        autoUpdateDetected = true;
        console.log(`✅ Auto-update detected after ${waitTime}ms - Alexanderium now sees ${currentAlexCount} rooms`);
        break;
      }
      
      console.log(`⏱️ Waiting for auto-update... ${waitTime}ms elapsed (Alex sees ${currentAlexCount} rooms)`);
    }
    
    // Final room counts
    const finalCounts = {
      Andy: await getRoomCount(andyPage, 'Andy'),
      Alexanderium: await getRoomCount(alexPage, 'Alexanderium')
    };
    
    console.log(`📊 Final room counts - Andy: ${finalCounts.Andy}, Alexanderium: ${finalCounts.Alexanderium}`);
    
    console.log('\n═══ PHASE 5: ANALYSIS ═══');
    
    testResults.endTime = Date.now();
    
    // Analyze results
    const analysis = analyzeTestResults();
    const testPassed = finalCounts.Alexanderium > initialCounts.Alexanderium;
    
    // Generate comprehensive bug report
    const bugReport = generateBugReport(testPassed, initialCounts, finalCounts);
    testResults.bugReport = bugReport;
    
    console.log(bugReport);
    
    // Keep browsers open for inspection
    console.log('\n⏱️ Keeping browsers open for inspection...');
    await Promise.all([
      andyPage.waitForTimeout(TEST_CONFIG.testDuration),
      alexPage.waitForTimeout(TEST_CONFIG.testDuration)
    ]);
    
  } catch (error) {
    console.error('❌ Test execution failed:', error);
    testResults.errors.push({
      type: 'test_execution_error',
      error: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
    testResults.endTime = Date.now();
  } finally {
    // Save comprehensive test results
    const reportFilename = `lobby-test-report-${Date.now()}.json`;
    fs.writeFileSync(reportFilename, JSON.stringify(testResults, null, 2));
    console.log(`\n📄 Comprehensive test results saved to: ${reportFilename}`);
    
    // Save summary report
    const summaryFilename = `lobby-test-summary-${Date.now()}.md`;
    fs.writeFileSync(summaryFilename, testResults.bugReport || 'Test completed with errors');
    console.log(`📄 Test summary saved to: ${summaryFilename}`);
    
    await browser.close();
    console.log('🏁 Test completed successfully');
  }
}

// Export for use as module
module.exports = { testLobbyAutoUpdate, TEST_CONFIG };

// Run test if called directly
if (require.main === module) {
  testLobbyAutoUpdate().catch(console.error);
}