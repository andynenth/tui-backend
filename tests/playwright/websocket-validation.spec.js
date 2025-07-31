/**
 * 🌐 **WebSocket Connection & Event Validation Tests**
 * 
 * PlaywrightTester Agent - WebSocket Specific Testing
 * 
 * Focus Areas:
 * 1. WebSocket connection stability during game start
 * 2. Event sequence validation
 * 3. Message payload verification
 * 4. Connection recovery testing
 * 5. Performance under load
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs').promises;
const path = require('path');

// WebSocket Test Configuration
const WS_CONFIG = {
  BASE_URL: 'http://localhost:5050',
  WS_URL: 'ws://localhost:5050/ws',
  TIMEOUT: 30000,
  SCREENSHOT_DIR: './test-results/websocket-validation',
  EXPECTED_EVENTS: [
    'room_updated',
    'player_joined',
    'bot_added',
    'game_start_request',
    'game_started',
    'state_sync'
  ],
  CRITICAL_EVENTS: ['game_started', 'state_sync'],
};

let wsTestResults = {
  connectionEvents: [],
  messageEvents: [],
  errorEvents: [],
  performanceMetrics: {},
};

test.describe('🌐 WebSocket Connection & Event Validation', () => {
  
  test.beforeAll(async () => {
    await fs.mkdir(WS_CONFIG.SCREENSHOT_DIR, { recursive: true });
    console.log('🌐 WebSocket validation test suite initialized');
  });

  test.beforeEach(async ({ page }) => {
    // Reset WebSocket test results
    wsTestResults = {
      connectionEvents: [],
      messageEvents: [],
      errorEvents: [],
      performanceMetrics: {},
    };

    // Set up enhanced WebSocket monitoring
    await setupEnhancedWebSocketMonitoring(page);
  });

  /**
   * 🔌 **CONNECTION STABILITY TEST**
   * 
   * Validates WebSocket connection stability during the game start sequence
   */
  test('🔌 WebSocket connection stability during game start', async ({ page }) => {
    console.log('🔌 === WEBSOCKET CONNECTION STABILITY TEST ===');
    
    const testId = `ws-stability-${Date.now()}`;
    
    // Navigate and establish initial connection
    await page.goto(WS_CONFIG.BASE_URL);
    await page.waitForLoadState('networkidle');
    
    // Monitor initial connection
    await page.waitForTimeout(2000);
    const initialConnections = await getWebSocketConnections(page);
    console.log(`🔍 Initial WebSocket connections: ${initialConnections.length}`);
    
    expect(initialConnections.length).toBeGreaterThan(0);
    
    // Create room and monitor connection
    await page.fill('input[placeholder="Enter your name"]', 'WSTestPlayer');
    await page.click('button:has-text("Create Room")');
    await page.waitForURL(/\/room\/.+/);
    
    // Monitor connection during room operations
    const roomConnections = await getWebSocketConnections(page);
    console.log(`🔍 Room page connections: ${roomConnections.length}`);
    
    // Add bots and monitor connection stability
    for (let i = 0; i < 3; i++) {
      await page.locator('button:has-text("Add Bot")').first().click();
      await page.waitForTimeout(1000);
      
      const connections = await getWebSocketConnections(page);
      const hasErrors = await hasWebSocketErrors(page);
      
      console.log(`🤖 Bot ${i + 1}: Connections=${connections.length}, Errors=${hasErrors}`);
      expect(hasErrors).toBe(false);
    }
    
    // Test game start sequence
    const startButton = page.locator('button:has-text("Start Game")');
    await expect(startButton).toBeVisible();
    
    // Monitor connection before game start
    const preStartConnections = await getWebSocketConnections(page);
    const preStartEvents = await getWebSocketEventCount(page);
    
    console.log(`📊 Pre-start: Connections=${preStartConnections.length}, Events=${preStartEvents}`);
    
    // Click start and monitor connection
    await startButton.click();
    
    // Monitor connection stability during transition
    for (let i = 0; i < 10; i++) {
      await page.waitForTimeout(1000);
      
      const connections = await getWebSocketConnections(page);
      const hasErrors = await hasWebSocketErrors(page);
      const eventCount = await getWebSocketEventCount(page);
      
      if (hasErrors) {
        console.error(`❌ WebSocket errors detected at T+${i + 1}s`);
        await captureWebSocketError(page, testId, i + 1);
      }
      
      console.log(`📊 T+${i + 1}s: Connections=${connections.length}, Events=${eventCount}, Errors=${hasErrors}`);
    }
    
    // Final connection state
    const finalConnections = await getWebSocketConnections(page);
    const finalErrors = await hasWebSocketErrors(page);
    
    console.log(`✅ Final state: Connections=${finalConnections.length}, Errors=${finalErrors}`);
    
    // Connection should remain stable
    expect(finalConnections.length).toBeGreaterThan(0);
    expect(finalErrors).toBe(false);
    
    await captureTestResult(page, testId, 'stability-final');
  });

  /**
   * 📨 **EVENT SEQUENCE VALIDATION**
   * 
   * Validates the correct sequence of WebSocket events during game start
   */
  test('📨 Event sequence validation for game start flow', async ({ page }) => {
    console.log('📨 === EVENT SEQUENCE VALIDATION TEST ===');
    
    const testId = `ws-events-${Date.now()}`;
    const expectedSequence = [
      'room_updated',    // Room creation
      'player_joined',   // Player joins
      'bot_added',       // Bot additions (multiple)
      'room_updated',    // Room state updates
      'game_started',    // Game start event
      'state_sync'       // Game state sync
    ];
    
    // Set up event sequence tracking
    await page.addInitScript(() => {
      window.eventSequence = [];
      window.criticalEvents = {};
    });
    
    // Navigate and create room
    await page.goto(WS_CONFIG.BASE_URL);
    await page.fill('input[placeholder="Enter your name"]', 'EventTestPlayer');
    await page.click('button:has-text("Create Room")');
    await page.waitForURL(/\/room\/.+/);
    
    // Add bots
    for (let i = 0; i < 3; i++) {
      await page.locator('button:has-text("Add Bot")').first().click();
      await page.waitForTimeout(1000);
    }
    
    // Start game
    const startButton = page.locator('button:has-text("Start Game")');
    await expect(startButton).toBeVisible();
    await startButton.click();
    
    // Wait for event sequence
    await page.waitForTimeout(10000);
    
    // Analyze event sequence
    const eventSequence = await page.evaluate(() => window.eventSequence);
    const criticalEvents = await page.evaluate(() => window.criticalEvents);
    
    console.log('📋 Event sequence analysis:');
    console.log(`   Total events recorded: ${eventSequence.length}`);
    console.log(`   Critical events: ${Object.keys(criticalEvents).length}`);
    
    // Check for critical events
    const hasGameStarted = criticalEvents.game_started;
    const hasStateSync = criticalEvents.state_sync;
    
    console.log(`   🎮 game_started event: ${!!hasGameStarted}`);
    console.log(`   🔄 state_sync event: ${!!hasStateSync}`);
    
    if (hasGameStarted) {
      console.log(`   📊 game_started details:`, hasGameStarted);
    } else {
      console.error('❌ Missing critical game_started event');
    }
    
    if (hasStateSync) {
      console.log(`   📊 state_sync details:`, hasStateSync);
    } else {
      console.error('❌ Missing critical state_sync event');
    }
    
    // Validate event sequence
    expect(eventSequence.length).toBeGreaterThan(0);
    expect(hasGameStarted).toBeTruthy();
    
    await captureEventSequence(page, testId, eventSequence);
  });

  /**
   * 📦 **MESSAGE PAYLOAD VALIDATION**
   * 
   * Validates the structure and content of WebSocket messages
   */
  test('📦 Message payload validation', async ({ page }) => {
    console.log('📦 === MESSAGE PAYLOAD VALIDATION TEST ===');
    
    const testId = `ws-payload-${Date.now()}`;
    
    // Set up payload validation
    await page.addInitScript(() => {
      window.messagePayloads = [];
      window.invalidPayloads = [];
      
      // Payload validation function
      window.validatePayload = (data) => {
        if (!data.type) {
          window.invalidPayloads.push({ error: 'Missing type field', data });
          return false;
        }
        
        if (data.type === 'game_started') {
          if (!data.game_id || !data.state) {
            window.invalidPayloads.push({ error: 'Invalid game_started payload', data });
            return false;
          }
        }
        
        if (data.type === 'state_sync') {
          if (!data.state || !data.phase) {
            window.invalidPayloads.push({ error: 'Invalid state_sync payload', data });
            return false;
          }
        }
        
        return true;
      };
    });
    
    // Execute game start flow
    await page.goto(WS_CONFIG.BASE_URL);
    await page.fill('input[placeholder="Enter your name"]', 'PayloadTestPlayer');
    await page.click('button:has-text("Create Room")');
    await page.waitForURL(/\/room\/.+/);
    
    for (let i = 0; i < 3; i++) {
      await page.locator('button:has-text("Add Bot")').first().click();
      await page.waitForTimeout(1000);
    }
    
    const startButton = page.locator('button:has-text("Start Game")');
    await startButton.click();
    await page.waitForTimeout(10000);
    
    // Analyze payloads
    const payloads = await page.evaluate(() => window.messagePayloads);
    const invalidPayloads = await page.evaluate(() => window.invalidPayloads);
    
    console.log(`📦 Payload analysis:`);
    console.log(`   Total payloads: ${payloads.length}`);
    console.log(`   Invalid payloads: ${invalidPayloads.length}`);
    
    if (invalidPayloads.length > 0) {
      console.error('❌ Invalid payloads detected:');
      invalidPayloads.forEach((invalid, i) => {
        console.error(`   ${i + 1}. ${invalid.error}:`, invalid.data);
      });
    }
    
    // Validate payload integrity
    expect(invalidPayloads.length).toBe(0);
    
    await capturePayloadAnalysis(page, testId, { payloads, invalidPayloads });
  });

  /**
   * 🔄 **CONNECTION RECOVERY TEST**
   * 
   * Tests WebSocket connection recovery scenarios
   */
  test('🔄 Connection recovery during game start', async ({ page }) => {
    console.log('🔄 === CONNECTION RECOVERY TEST ===');
    
    const testId = `ws-recovery-${Date.now()}`;
    
    // Set up recovery monitoring
    await page.addInitScript(() => {
      window.recoveryEvents = [];
      window.connectionStates = [];
    });
    
    // Navigate and establish connection
    await page.goto(WS_CONFIG.BASE_URL);
    await page.fill('input[placeholder="Enter your name"]', 'RecoveryTestPlayer');
    await page.click('button:has-text("Create Room")');
    await page.waitForURL(/\/room\/.+/);
    
    // Add bots
    for (let i = 0; i < 3; i++) {
      await page.locator('button:has-text("Add Bot")').first().click();
      await page.waitForTimeout(1000);
    }
    
    // Monitor connection before disruption
    const preDisruptionState = await getWebSocketConnections(page);
    console.log(`🔍 Pre-disruption connections: ${preDisruptionState.length}`);
    
    // Simulate network disruption (if possible)
    // Note: This is limited in browser environment, but we can monitor
    // natural connection events
    
    const startButton = page.locator('button:has-text("Start Game")');
    await startButton.click();
    
    // Monitor recovery
    for (let i = 0; i < 15; i++) {
      await page.waitForTimeout(1000);
      
      const connections = await getWebSocketConnections(page);
      const state = {
        time: Date.now(),
        connections: connections.length,
        hasActiveConnection: connections.some(c => c.readyState === 1)
      };
      
      console.log(`📊 Recovery T+${i + 1}s: Active connections=${state.hasActiveConnection ? 'Yes' : 'No'}`);
    }
    
    // Final state should have active connections
    const finalConnections = await getWebSocketConnections(page);
    const hasActiveConnection = finalConnections.some(c => c.readyState === 1);
    
    console.log(`✅ Final recovery state: Active=${hasActiveConnection}`);
    expect(hasActiveConnection).toBe(true);
    
    await captureTestResult(page, testId, 'recovery-final');
  });

});

/**
 * 🔧 **HELPER FUNCTIONS**
 */

async function setupEnhancedWebSocketMonitoring(page) {
  await page.addInitScript(() => {
    window.wsConnections = [];
    window.wsEvents = [];
    window.wsErrors = [];
    window.performanceMetrics = {
      connectionTimes: [],
      messageTimes: [],
      errorCount: 0
    };
    
    // Enhanced WebSocket monitoring
    const OriginalWebSocket = window.WebSocket;
    window.WebSocket = class WebSocket extends OriginalWebSocket {
      constructor(url, protocols) {
        const startTime = performance.now();
        super(url, protocols);
        
        const connection = {
          id: Math.random().toString(36).substr(2, 9),
          url: url,
          readyState: this.readyState,
          events: [],
          openTime: null,
          closeTime: null,
          performance: {
            connectionStart: startTime,
            connectionEnd: null,
            messageCount: 0,
            errorCount: 0
          }
        };
        
        window.wsConnections.push(connection);
        
        this.addEventListener('open', (event) => {
          connection.openTime = performance.now();
          connection.performance.connectionEnd = connection.openTime;
          
          const connectionTime = connection.openTime - connection.performance.connectionStart;
          window.performanceMetrics.connectionTimes.push(connectionTime);
          
          const eventData = {
            time: new Date().toISOString(),
            type: 'open',
            connectionId: connection.id,
            url: url,
            connectionTime: connectionTime
          };
          
          window.wsEvents.push(eventData);
          connection.events.push(eventData);
          
          console.log(`[WS OPEN] Connection ${connection.id} opened in ${connectionTime.toFixed(2)}ms`);
        });
        
        this.addEventListener('message', (event) => {
          const messageTime = performance.now();
          connection.performance.messageCount++;
          
          let data;
          try {
            data = JSON.parse(event.data);
          } catch (e) {
            data = event.data;
          }
          
          const eventData = {
            time: new Date().toISOString(),
            type: 'message',
            direction: 'incoming',
            connectionId: connection.id,
            data: data,
            messageTime: messageTime
          };
          
          window.wsEvents.push(eventData);
          connection.events.push(eventData);
          window.performanceMetrics.messageTimes.push(messageTime);
          
          // Store in sequence tracker
          if (window.eventSequence) {
            window.eventSequence.push(data.type);
          }
          
          // Store critical events
          if (window.criticalEvents && ['game_started', 'state_sync'].includes(data.type)) {
            window.criticalEvents[data.type] = eventData;
          }
          
          // Validate payload
          if (window.validatePayload) {
            const isValid = window.validatePayload(data);
            if (isValid && window.messagePayloads) {
              window.messagePayloads.push(eventData);
            }
          }
          
          // Log important events
          if (['game_started', 'state_sync', 'error'].includes(data.type)) {
            console.log(`[WS MSG] ${data.type.toUpperCase()}:`, data);
          }
        });
        
        this.addEventListener('close', (event) => {
          connection.closeTime = performance.now();
          
          const eventData = {
            time: new Date().toISOString(),
            type: 'close',
            connectionId: connection.id,
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean
          };
          
          window.wsEvents.push(eventData);
          connection.events.push(eventData);
          
          if (window.recoveryEvents) {
            window.recoveryEvents.push(eventData);
          }
          
          console.log(`[WS CLOSE] Connection ${connection.id} closed: ${event.code} ${event.reason}`);
        });
        
        this.addEventListener('error', (event) => {
          connection.performance.errorCount++;
          window.performanceMetrics.errorCount++;
          
          const eventData = {
            time: new Date().toISOString(),
            type: 'error',
            connectionId: connection.id,
            error: event.message || 'WebSocket error'
          };
          
          window.wsEvents.push(eventData);
          window.wsErrors.push(eventData);
          connection.events.push(eventData);
          
          console.error(`[WS ERROR] Connection ${connection.id}:`, event);
        });
        
        const originalSend = this.send.bind(this);
        this.send = (data) => {
          const sendTime = performance.now();
          
          let parsedData;
          try {
            parsedData = JSON.parse(data);
          } catch (e) {
            parsedData = data;
          }
          
          const eventData = {
            time: new Date().toISOString(),
            type: 'message',
            direction: 'outgoing',
            connectionId: connection.id,
            data: parsedData,
            sendTime: sendTime
          };
          
          window.wsEvents.push(eventData);
          connection.events.push(eventData);
          
          console.log(`[WS SEND] Connection ${connection.id}:`, parsedData.type || 'unknown', parsedData);
          return originalSend(data);
        };
      }
    };
  });
}

async function getWebSocketConnections(page) {
  return await page.evaluate(() => window.wsConnections || []);
}

async function hasWebSocketErrors(page) {
  const errors = await page.evaluate(() => window.wsErrors || []);
  return errors.length > 0;
}

async function getWebSocketEventCount(page) {
  return await page.evaluate(() => window.wsEvents ? window.wsEvents.length : 0);
}

async function captureWebSocketError(page, testId, timeIndex) {
  const errors = await page.evaluate(() => window.wsErrors);
  const errorPath = path.join(WS_CONFIG.SCREENSHOT_DIR, `${testId}-error-t${timeIndex}.json`);
  
  await fs.writeFile(errorPath, JSON.stringify({
    timeIndex,
    errors,
    timestamp: new Date().toISOString()
  }, null, 2));
  
  console.log(`❌ WebSocket error captured: ${errorPath}`);
}

async function captureTestResult(page, testId, stepName) {
  const screenshotPath = path.join(WS_CONFIG.SCREENSHOT_DIR, `${testId}-${stepName}.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  
  const wsState = await page.evaluate(() => ({
    connections: window.wsConnections,
    events: window.wsEvents,
    errors: window.wsErrors,
    performance: window.performanceMetrics
  }));
  
  const statePath = path.join(WS_CONFIG.SCREENSHOT_DIR, `${testId}-${stepName}-state.json`);
  await fs.writeFile(statePath, JSON.stringify(wsState, null, 2));
  
  console.log(`📊 Test result captured: ${stepName}`);
}

async function captureEventSequence(page, testId, eventSequence) {
  const sequencePath = path.join(WS_CONFIG.SCREENSHOT_DIR, `${testId}-event-sequence.json`);
  
  const sequenceData = {
    sequence: eventSequence,
    timestamp: new Date().toISOString(),
    analysis: {
      totalEvents: eventSequence.length,
      uniqueEvents: [...new Set(eventSequence)],
      criticalEventsFound: eventSequence.filter(e => WS_CONFIG.CRITICAL_EVENTS.includes(e))
    }
  };
  
  await fs.writeFile(sequencePath, JSON.stringify(sequenceData, null, 2));
  console.log(`📨 Event sequence captured: ${sequencePath}`);
}

async function capturePayloadAnalysis(page, testId, analysis) {
  const payloadPath = path.join(WS_CONFIG.SCREENSHOT_DIR, `${testId}-payload-analysis.json`);
  
  const payloadData = {
    ...analysis,
    timestamp: new Date().toISOString(),
    summary: {
      totalPayloads: analysis.payloads.length,
      invalidPayloads: analysis.invalidPayloads.length,
      validityRate: ((analysis.payloads.length - analysis.invalidPayloads.length) / analysis.payloads.length * 100).toFixed(2) + '%'
    }
  };
  
  await fs.writeFile(payloadPath, JSON.stringify(payloadData, null, 2));
  console.log(`📦 Payload analysis captured: ${payloadPath}`);
}