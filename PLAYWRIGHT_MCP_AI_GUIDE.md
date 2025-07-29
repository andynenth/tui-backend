# AI Guide: Using Playwright MCP for Testing

## Table of Contents
1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Core Concepts](#core-concepts)
4. [Test Structure Patterns](#test-structure-patterns)
5. [WebSocket Message Capture](#websocket-message-capture)
6. [Multi-Browser Testing](#multi-browser-testing)
7. [Common Testing Scenarios](#common-testing-scenarios)
8. [Debugging & Analysis](#debugging--analysis)
9. [Best Practices](#best-practices)
10. [Real-World Example](#real-world-example)

## Overview

Playwright MCP (Model Context Protocol) enables AI assistants to create sophisticated browser automation tests. This guide teaches AI how to:

- Test real-time applications with WebSocket communication
- Simulate multiple users simultaneously
- Capture and analyze network traffic
- Generate detailed test reports
- Debug complex frontend-backend interactions

## Installation & Setup

### 1. Install Playwright MCP

```bash
# Install Playwright as a dependency
npm install playwright

# Install Playwright browsers
npx playwright install chromium

# Create package.json with test scripts (optional)
{
  "scripts": {
    "test:playwright": "node your_test_file.js"
  },
  "dependencies": {
    "playwright": "^1.40.0"
  }
}
```

### 2. Basic Test Structure

Create a JavaScript file with this basic structure:

```javascript
const { chromium } = require('playwright');

async function myTest() {
  const browser = await chromium.launch({
    headless: false,  // Set to true for CI/automated runs
    slowMo: 500      // Slow down actions for visibility
  });

  try {
    const page = await browser.newPage();
    // Your test code here
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
}

myTest().catch(console.error);
```

## Core Concepts

### Browser Contexts vs Pages

```javascript
// One browser can have multiple contexts (like different users)
const browser = await chromium.launch();
const userAContext = await browser.newContext();
const userBContext = await browser.newContext();

const userAPage = await userAContext.newPage();
const userBPage = await userBContext.newPage();
```

### Element Interaction Patterns

```javascript
// Wait for elements to be ready before interacting
await page.waitForLoadState('networkidle');

// Robust element selection
const button = await page.locator('button').filter({ hasText: /submit|save/i });
await button.click();

// Input handling
const input = await page.locator('input[type="text"]').first();
await input.fill('test value');
```

## Test Structure Patterns

### 1. Configuration Object Pattern

```javascript
const TEST_CONFIG = {
  baseUrl: 'http://localhost:3000',
  timeout: 30000,
  headless: false,
  slowMo: 500,
  users: {
    alice: 'Alice',
    bob: 'Bob'
  }
};
```

### 2. Helper Functions Pattern

```javascript
async function navigateToApp(page, userName) {
  await page.goto(TEST_CONFIG.baseUrl);
  await page.waitForLoadState('networkidle');
  
  const nameInput = await page.locator('input[type="text"]').first();
  await nameInput.fill(userName);
  
  const startButton = await page.locator('button').filter({ hasText: /start|enter/i });
  await startButton.click();
  
  await page.waitForTimeout(1000);
}

async function getRoomCount(page) {
  try {
    const rooms = await page.locator('.room-item, [class*="room"]').all();
    return rooms.length;
  } catch (error) {
    return 0;
  }
}
```

### 3. Test Phases Pattern

```javascript
async function multiUserTest() {
  console.log('=== PHASE 1: Setup ===');
  // Setup code
  
  console.log('=== PHASE 2: User Actions ===');
  // Main test actions
  
  console.log('=== PHASE 3: Verification ===');
  // Assertions and verification
  
  console.log('=== PHASE 4: Cleanup ===');
  // Cleanup and analysis
}
```

## WebSocket Message Capture

### Real-Time Message Monitoring

```javascript
async function captureWebSocketMessages(page, playerName) {
  const messages = [];
  
  page.on('websocket', ws => {
    console.log(`🔗 [${playerName}] WebSocket connection: ${ws.url()}`);
    
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
      } catch (e) {
        messages.push({
          type: 'sent',
          timestamp,
          player: playerName,
          message: message,
          raw: message,
          parseError: true
        });
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
      } catch (e) {
        messages.push({
          type: 'received',
          timestamp,
          player: playerName,
          message: message,
          raw: message,
          parseError: true
        });
      }
    });
  });
  
  return messages;
}
```

### Message Analysis

```javascript
function analyzeMessages(messages) {
  const analysis = {
    totalMessages: messages.length,
    sentCount: messages.filter(m => m.type === 'sent').length,
    receivedCount: messages.filter(m => m.type === 'received').length,
    eventTypes: {},
    timeline: []
  };
  
  messages.forEach(msg => {
    if (msg.message && msg.message.event) {
      const eventType = msg.message.event;
      analysis.eventTypes[eventType] = (analysis.eventTypes[eventType] || 0) + 1;
    }
    
    analysis.timeline.push({
      timestamp: msg.timestamp,
      player: msg.player,
      direction: msg.type,
      event: msg.message?.event || 'unknown'
    });
  });
  
  return analysis;
}
```

## Multi-Browser Testing

### Simulating Multiple Users

```javascript
async function testMultiUser() {
  const browser = await chromium.launch({ headless: false });
  
  try {
    // Create separate contexts for each user
    const aliceContext = await browser.newContext();
    const bobContext = await browser.newContext();
    
    const alicePage = await aliceContext.newPage();
    const bobPage = await bobContext.newPage();
    
    // Set up message capture for both users
    const aliceMessages = await captureWebSocketMessages(alicePage, 'Alice');
    const bobMessages = await captureWebSocketMessages(bobPage, 'Bob');
    
    // Both users enter the app simultaneously
    await Promise.all([
      navigateToApp(alicePage, 'Alice'),
      navigateToApp(bobPage, 'Bob')
    ]);
    
    // Alice performs an action
    await performAction(alicePage, 'create_room');
    
    // Wait for Bob to see the change
    await bobPage.waitForTimeout(2000);
    
    // Verify Bob received the update
    const bobRoomCount = await getRoomCount(bobPage);
    console.log(`Bob sees ${bobRoomCount} rooms`);
    
    // Generate report
    const report = {
      alice: analyzeMessages(aliceMessages),
      bob: analyzeMessages(bobMessages),
      testResult: bobRoomCount > 0 ? 'PASS' : 'FAIL'
    };
    
    console.log('Test Report:', JSON.stringify(report, null, 2));
    
  } finally {
    await browser.close();
  }
}
```

## Common Testing Scenarios

### 1. Real-Time Updates Test

```javascript
async function testRealTimeUpdates() {
  // Test that changes from one user appear instantly for other users
  const browser = await chromium.launch({ headless: false });
  
  const userA = await browser.newContext();
  const userB = await browser.newContext();
  
  const pageA = await userA.newPage();
  const pageB = await userB.newPage();
  
  // Both users connect
  await Promise.all([
    navigateToApp(pageA, 'UserA'),
    navigateToApp(pageB, 'UserB')
  ]);
  
  // Get initial state
  const initialCount = await getRoomCount(pageB);
  
  // UserA creates something
  await createRoom(pageA, 'Test Room');
  
  // Check if UserB sees the change immediately
  await pageB.waitForTimeout(1000);
  const updatedCount = await getRoomCount(pageB);
  
  const testPassed = updatedCount > initialCount;
  console.log(`Real-time update test: ${testPassed ? 'PASS' : 'FAIL'}`);
  
  await browser.close();
}
```

### 2. Network Disconnection Simulation

```javascript
async function testNetworkResilience() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  await navigateToApp(page, 'TestUser');
  
  // Simulate network disconnection
  await page.route('**/*', route => route.abort());
  
  // Try to perform an action
  const actionResult = await tryAction(page);
  
  // Re-enable network
  await page.unroute('**/*');
  
  // Verify recovery
  await page.waitForTimeout(2000);
  const recovered = await checkConnection(page);
  
  console.log(`Network resilience test: ${recovered ? 'PASS' : 'FAIL'}`);
  
  await browser.close();
}
```

### 3. Load Testing (Multiple Users)

```javascript
async function testMultipleUsers(userCount = 5) {
  const browser = await chromium.launch();
  const users = [];
  
  // Create multiple user contexts
  for (let i = 0; i < userCount; i++) {
    const context = await browser.newContext();
    const page = await context.newPage();
    users.push({
      name: `User${i + 1}`,
      page,
      messages: await captureWebSocketMessages(page, `User${i + 1}`)
    });
  }
  
  // All users connect simultaneously
  await Promise.all(
    users.map(user => navigateToApp(user.page, user.name))
  );
  
  // Simulate concurrent actions
  await Promise.all(
    users.map((user, index) => {
      if (index === 0) return createRoom(user.page, 'Main Room');
      return joinRoom(user.page, 'Main Room');
    })
  );
  
  // Verify all users see consistent state
  const roomCounts = await Promise.all(
    users.map(user => getRoomCount(user.page))
  );
  
  const allConsistent = roomCounts.every(count => count === roomCounts[0]);
  console.log(`Load test (${userCount} users): ${allConsistent ? 'PASS' : 'FAIL'}`);
  
  await browser.close();
}
```

## Debugging & Analysis

### Comprehensive Test Report Generation

```javascript
function generateTestReport(testData) {
  const report = {
    testName: testData.name,
    timestamp: new Date().toISOString(),
    duration: testData.endTime - testData.startTime,
    result: testData.success ? 'PASS' : 'FAIL',
    users: testData.users.map(user => ({
      name: user.name,
      messageCount: user.messages.length,
      eventsReceived: user.messages.filter(m => m.type === 'received').length,
      eventsSent: user.messages.filter(m => m.type === 'sent').length,
      errors: user.messages.filter(m => m.parseError).length
    })),
    timeline: testData.messages.sort((a, b) => 
      new Date(a.timestamp) - new Date(b.timestamp)
    ),
    analysis: {
      criticalEvents: findCriticalEvents(testData.messages),
      performanceMetrics: calculatePerformanceMetrics(testData.messages),
      errorPatterns: findErrorPatterns(testData.messages)
    }
  };
  
  return report;
}

function findCriticalEvents(messages) {
  return messages.filter(msg => 
    msg.message?.event && 
    ['room_created', 'room_list_update', 'error', 'disconnect'].includes(msg.message.event)
  );
}

function calculatePerformanceMetrics(messages) {
  const events = messages.filter(m => m.message?.event);
  const responseTime = calculateAverageResponseTime(events);
  
  return {
    averageResponseTime: responseTime,
    totalEvents: events.length,
    eventsPerSecond: events.length / getTestDurationSeconds(messages)
  };
}
```

### Error Detection and Reporting

```javascript
function detectIssues(testResults) {
  const issues = [];
  
  // Check for missing messages
  const expectedEvents = ['room_list_update', 'room_created'];
  expectedEvents.forEach(eventType => {
    const found = testResults.messages.some(m => m.message?.event === eventType);
    if (!found) {
      issues.push({
        type: 'missing_event',
        event: eventType,
        severity: 'high'
      });
    }
  });
  
  // Check for delayed responses
  const responseDelays = calculateResponseDelays(testResults.messages);
  responseDelays.forEach(delay => {
    if (delay.duration > 5000) { // 5 second threshold
      issues.push({
        type: 'slow_response',
        duration: delay.duration,
        event: delay.event,
        severity: 'medium'
      });
    }
  });
  
  // Check for WebSocket disconnections
  const disconnections = testResults.messages.filter(m => 
    m.message?.event === 'disconnect' || m.message?.event === 'error'
  );
  
  if (disconnections.length > 0) {
    issues.push({
      type: 'connection_issues',
      count: disconnections.length,
      severity: 'high'
    });
  }
  
  return issues;
}
```

## Best Practices

### 1. Robust Element Selection

```javascript
// ❌ Fragile - depends on specific CSS classes
await page.locator('.btn-primary').click();

// ✅ Robust - uses semantic content
await page.locator('button').filter({ hasText: /create|add/i }).first().click();

// ✅ Even better - multiple fallback strategies
const createButton = await page.locator('button').filter({ hasText: /create/i }).first()
  .or(page.locator('[data-testid="create-button"]'))
  .or(page.locator('#create-btn'));
await createButton.click();
```

### 2. Wait Strategies

```javascript
// ❌ Unreliable - fixed timeouts
await page.waitForTimeout(5000);

// ✅ Better - wait for specific conditions
await page.waitForLoadState('networkidle');
await page.waitForSelector('.room-list');

// ✅ Best - wait for application state
await page.waitForFunction(() => {
  return document.querySelectorAll('.room-item').length > 0;
});
```

### 3. Error Handling

```javascript
async function robustAction(page, actionName, actionFn) {
  const maxRetries = 3;
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`Attempting ${actionName} (attempt ${attempt}/${maxRetries})`);
      await actionFn();
      console.log(`✅ ${actionName} succeeded`);
      return;
    } catch (error) {
      lastError = error;
      console.log(`❌ ${actionName} failed (attempt ${attempt}): ${error.message}`);
      
      if (attempt < maxRetries) {
        await page.waitForTimeout(1000 * attempt); // Exponential backoff
      }
    }
  }
  
  throw new Error(`${actionName} failed after ${maxRetries} attempts. Last error: ${lastError.message}`);
}
```

### 4. Test Data Management

```javascript
const TEST_DATA = {
  users: [
    { name: 'Alice', role: 'host' },
    { name: 'Bob', role: 'player' },
    { name: 'Charlie', role: 'observer' }
  ],
  rooms: [
    { name: 'Test Room 1', maxPlayers: 4 },
    { name: 'Test Room 2', maxPlayers: 2 }
  ],
  actions: {
    createRoom: { timeout: 5000, retries: 2 },
    joinRoom: { timeout: 3000, retries: 3 }
  }
};
```

## Real-World Example

Here's a complete example based on testing a multiplayer lobby system:

```javascript
const { chromium } = require('playwright');
const fs = require('fs');

const TEST_CONFIG = {
  baseUrl: 'http://localhost:5050',
  timeout: 30000,
  headless: false,
  slowMo: 500,
  players: ['Andy', 'Alexanderium']
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

async function testLobbyAutoUpdate() {
  console.log('🚀 Starting Lobby Auto-Update Test...');
  
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
    
    console.log('\n=== PHASE 1: Both players enter lobby ===');
    
    // Both players enter lobby simultaneously
    await Promise.all([
      enterLobby(andyPage, 'Andy'),
      enterLobby(alexPage, 'Alexanderium')
    ]);
    
    // Get initial room counts
    const initialAndyCount = await getRoomCount(andyPage, 'Andy');
    const initialAlexCount = await getRoomCount(alexPage, 'Alexanderium');
    
    console.log(`📊 Initial room counts - Andy: ${initialAndyCount}, Alex: ${initialAlexCount}`);
    
    console.log('\n=== PHASE 2: Andy creates room ===');
    
    // Andy creates a room
    const roomName = `TestRoom_${Date.now()}`;
    await createRoom(andyPage, 'Andy', roomName);
    
    console.log('\n=== PHASE 3: Check if Alex sees the room automatically ===');
    
    // Wait for potential auto-update
    await alexPage.waitForTimeout(3000);
    
    // Check if Alex sees the new room
    const postCreateAlexCount = await getRoomCount(alexPage, 'Alexanderium');
    
    console.log(`📊 Post-creation room count - Alex: ${postCreateAlexCount}`);
    
    // Analyze results
    const autoUpdateWorked = postCreateAlexCount > initialAlexCount;
    
    console.log('\n=== ANALYSIS ===');
    
    const analysis = {
      initialRoomCount: initialAlexCount,
      postCreateRoomCount: postCreateAlexCount,
      autoUpdateWorked,
      roomListUpdateMessages: testResults.timeline.filter(msg => 
        msg.message && msg.message.event === 'room_list_update'
      ),
      roomCreatedMessages: testResults.timeline.filter(msg => 
        msg.message && (msg.message.event === 'room_created' || msg.message.action === 'create_room')
      )
    };
    
    testResults.analysis = analysis;
    
    // Generate bug report
    let bugReport = '';
    
    if (autoUpdateWorked) {
      bugReport = `✅ SUCCESS: Auto-update is working correctly!
Alexanderium automatically saw Andy's room appear in the lobby.

Room List Update Messages: ${analysis.roomListUpdateMessages.length}
Room Created Messages: ${analysis.roomCreatedMessages.length}`;
    } else {
      bugReport = `🐛 BUG CONFIRMED: Lobby Auto-Update Failure

Initial State: ${analysis.initialRoomCount} rooms
After Andy creates room: ${analysis.postCreateRoomCount} rooms (should be ${analysis.initialRoomCount + 1})

❌ Auto-update failed: Alexanderium did not see Andy's room automatically
📨 Room list update messages: ${analysis.roomListUpdateMessages.length}
📨 Room created messages: ${analysis.roomCreatedMessages.length}

WebSocket Message Analysis:
${analysis.roomListUpdateMessages.map(msg => 
  `- ${msg.timestamp} [${msg.player}] ${msg.direction}: ${msg.message.event} - ${
    msg.message.data && msg.message.data.rooms ? msg.message.data.rooms.length : 'unknown'
  } rooms`
).join('\n')}`;
    }
    
    testResults.bugReport = bugReport;
    
    console.log('\n' + bugReport);
    
    // Keep browsers open for inspection
    console.log('\n⏱️ Keeping browsers open for 10 seconds for inspection...');
    await andyPage.waitForTimeout(10000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
    testResults.error = error.message;
  } finally {
    // Save detailed test results
    fs.writeFileSync('lobby-test-report.json', JSON.stringify(testResults, null, 2));
    console.log('\n📄 Detailed test results saved to: lobby-test-report.json');
    
    await browser.close();
    console.log('🏁 Test completed');
  }
}

// Helper function for assertions
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
```

## Key Takeaways for AI

1. **Always capture WebSocket messages** when testing real-time applications
2. **Use multiple browser contexts** to simulate different users
3. **Wait for application state**, not fixed timeouts
4. **Generate comprehensive reports** with timeline analysis
5. **Handle errors gracefully** with retry mechanisms
6. **Test both happy path and edge cases**
7. **Save test artifacts** for debugging and analysis
8. **Use semantic selectors** that are resilient to UI changes

This guide provides a foundation for AI assistants to create sophisticated, real-world browser tests using Playwright MCP.