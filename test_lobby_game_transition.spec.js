const { test, expect } = require('@playwright/test');
const fs = require('fs').promises;
const path = require('path');

// Configuration
const BASE_URL = 'http://localhost:5050';
const ROOM_NAME = `TestRoom_${Date.now()}`;
const PLAYER_NAMES = ['Alice', 'Bob', 'Charlie', 'David'];
const WEBSOCKET_TIMEOUT = 30000;
const SCREENSHOT_DIR = './test-screenshots';

// Test state tracking
let wsEvents = [];
let consoleMessages = [];
let networkRequests = [];
let errorLogs = [];

test.describe('Lobby to Game Transition Debugging', () => {
  test.beforeAll(async () => {
    // Create screenshot directory
    await fs.mkdir(SCREENSHOT_DIR, { recursive: true });
  });

  test.beforeEach(async ({ page }) => {
    // Reset event tracking
    wsEvents = [];
    consoleMessages = [];
    networkRequests = [];
    errorLogs = [];

    // Set up console message tracking
    page.on('console', async (msg) => {
      const logEntry = {
        time: new Date().toISOString(),
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      };
      
      consoleMessages.push(logEntry);
      
      // Log errors immediately
      if (msg.type() === 'error') {
        console.error(`[CONSOLE ERROR] ${msg.text()}`);
        errorLogs.push(logEntry);
      }
    });

    // Set up page error tracking
    page.on('pageerror', (error) => {
      const errorEntry = {
        time: new Date().toISOString(),
        message: error.message,
        stack: error.stack
      };
      errorLogs.push(errorEntry);
      console.error(`[PAGE ERROR]`, error);
    });

    // Set up network request tracking
    page.on('request', (request) => {
      if (request.url().includes('/ws') || request.url().includes('websocket')) {
        networkRequests.push({
          time: new Date().toISOString(),
          method: request.method(),
          url: request.url(),
          type: 'websocket'
        });
      }
    });

    // Set up WebSocket event interception
    await page.addInitScript(() => {
      window.wsEvents = [];
      window.wsConnections = [];
      
      // Override WebSocket constructor
      const OriginalWebSocket = window.WebSocket;
      window.WebSocket = class WebSocket extends OriginalWebSocket {
        constructor(url, protocols) {
          super(url, protocols);
          
          const connection = {
            url: url,
            readyState: this.readyState,
            events: [],
            openTime: null,
            closeTime: null
          };
          
          window.wsConnections.push(connection);
          
          // Track open event
          this.addEventListener('open', (event) => {
            connection.openTime = new Date().toISOString();
            connection.readyState = this.readyState;
            
            const eventData = {
              time: new Date().toISOString(),
              type: 'open',
              url: url,
              readyState: this.readyState
            };
            
            window.wsEvents.push(eventData);
            connection.events.push(eventData);
            console.log('[WS] Connection opened:', url);
          });
          
          // Track message events
          this.addEventListener('message', (event) => {
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
              data: data,
              raw: event.data
            };
            
            window.wsEvents.push(eventData);
            connection.events.push(eventData);
            
            // Log important events
            if (data.type === 'game_started' || data.type === 'state_sync' || data.type === 'error') {
              console.log(`[WS MESSAGE] ${data.type}:`, data);
            }
          });
          
          // Track close event
          this.addEventListener('close', (event) => {
            connection.closeTime = new Date().toISOString();
            connection.readyState = this.readyState;
            
            const eventData = {
              time: new Date().toISOString(),
              type: 'close',
              code: event.code,
              reason: event.reason,
              wasClean: event.wasClean
            };
            
            window.wsEvents.push(eventData);
            connection.events.push(eventData);
            console.log('[WS] Connection closed:', event.code, event.reason);
          });
          
          // Track error event
          this.addEventListener('error', (event) => {
            const eventData = {
              time: new Date().toISOString(),
              type: 'error',
              error: event.message || 'WebSocket error'
            };
            
            window.wsEvents.push(eventData);
            connection.events.push(eventData);
            console.error('[WS ERROR]', event);
          });
          
          // Override send to track outgoing messages
          const originalSend = this.send.bind(this);
          this.send = (data) => {
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
              data: parsedData,
              raw: data
            };
            
            window.wsEvents.push(eventData);
            connection.events.push(eventData);
            
            console.log('[WS SEND]', parsedData.type || 'unknown', parsedData);
            return originalSend(data);
          };
        }
      };
    });
  });

  test('Complete lobby to game transition flow', async ({ page }) => {
    console.log('=== Starting Lobby to Game Transition Test ===');
    
    // Step 1: Navigate to lobby and create room
    console.log('Step 1: Creating room...');
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    // Enter player name and create room
    await page.fill('input[placeholder="Enter your name"]', PLAYER_NAMES[0]);
    await page.click('button:has-text("Create Room")');
    
    // Wait for room creation
    await page.waitForURL(/\/room\/.+/, { timeout: 10000 });
    const roomUrl = page.url();
    const roomCode = roomUrl.split('/').pop();
    console.log(`Room created with code: ${roomCode}`);
    
    // Take screenshot of initial room state
    await page.screenshot({ 
      path: path.join(SCREENSHOT_DIR, '01-room-created.png'),
      fullPage: true 
    });
    
    // Step 2: Add bots to fill the room
    console.log('Step 2: Adding bots...');
    for (let i = 1; i < 4; i++) {
      const botButton = page.locator(`button:has-text("Add Bot")`).first();
      await botButton.click();
      await page.waitForTimeout(500);
      
      // Log WebSocket events after each bot
      const events = await page.evaluate(() => window.wsEvents);
      const botEvents = events.filter(e => 
        e.time > new Date(Date.now() - 1000).toISOString()
      );
      console.log(`Bot ${i} events:`, botEvents);
    }
    
    await page.screenshot({ 
      path: path.join(SCREENSHOT_DIR, '02-bots-added.png'),
      fullPage: true 
    });
    
    // Step 3: Verify room is full and start button is visible
    console.log('Step 3: Checking start button...');
    const startButton = page.locator('button:has-text("Start Game")');
    await expect(startButton).toBeVisible({ timeout: 5000 });
    
    const isStartButtonEnabled = await startButton.isEnabled();
    console.log(`Start button enabled: ${isStartButtonEnabled}`);
    
    // Get current WebSocket state
    const wsState = await page.evaluate(() => ({
      connections: window.wsConnections,
      totalEvents: window.wsEvents.length,
      recentEvents: window.wsEvents.slice(-10)
    }));
    console.log('WebSocket state before start:', wsState);
    
    // Step 4: Click start button and monitor transition
    console.log('Step 4: Clicking start button...');
    await page.screenshot({ 
      path: path.join(SCREENSHOT_DIR, '03-before-start.png'),
      fullPage: true 
    });
    
    // Set up promise to wait for game_started event
    const gameStartedPromise = page.evaluate(() => {
      return new Promise((resolve) => {
        const checkInterval = setInterval(() => {
          const gameStartedEvent = window.wsEvents.find(e => 
            e.data && e.data.type === 'game_started'
          );
          if (gameStartedEvent) {
            clearInterval(checkInterval);
            resolve(gameStartedEvent);
          }
        }, 100);
        
        // Timeout after 30 seconds
        setTimeout(() => {
          clearInterval(checkInterval);
          resolve(null);
        }, 30000);
      });
    });
    
    // Click start button
    await startButton.click();
    
    // Wait for response
    console.log('Waiting for game_started event...');
    const gameStartedEvent = await gameStartedPromise;
    
    if (gameStartedEvent) {
      console.log('Game started event received:', gameStartedEvent);
    } else {
      console.log('No game_started event received within timeout');
    }
    
    // Take screenshots during waiting period
    for (let i = 0; i < 5; i++) {
      await page.waitForTimeout(2000);
      await page.screenshot({ 
        path: path.join(SCREENSHOT_DIR, `04-waiting-${i+1}.png`),
        fullPage: true 
      });
      
      // Check current URL
      const currentUrl = page.url();
      console.log(`After ${(i+1)*2}s - Current URL: ${currentUrl}`);
      
      // Check for any error messages on page
      const errorElements = await page.locator('.error, .toast-error, [class*="error"]').all();
      if (errorElements.length > 0) {
        console.log(`Found ${errorElements.length} error elements on page`);
        for (const element of errorElements) {
          const text = await element.textContent();
          console.log(`Error element text: ${text}`);
        }
      }
    }
    
    // Step 5: Analyze final state
    console.log('Step 5: Analyzing final state...');
    
    // Get all WebSocket events
    const allWsEvents = await page.evaluate(() => window.wsEvents);
    wsEvents = allWsEvents;
    
    // Get final URL
    const finalUrl = page.url();
    console.log(`Final URL: ${finalUrl}`);
    
    // Check if we're on game page
    const isOnGamePage = finalUrl.includes('/game/');
    console.log(`Reached game page: ${isOnGamePage}`);
    
    // Get page content for debugging
    const pageContent = await page.content();
    const hasWaitingIndicator = pageContent.includes('waiting') || pageContent.includes('Waiting');
    const hasGameContent = pageContent.includes('game') || pageContent.includes('Game');
    
    console.log(`Page has waiting indicator: ${hasWaitingIndicator}`);
    console.log(`Page has game content: ${hasGameContent}`);
    
    // Final screenshot
    await page.screenshot({ 
      path: path.join(SCREENSHOT_DIR, '05-final-state.png'),
      fullPage: true 
    });
    
    // Generate detailed report
    await generateReport({
      roomCode,
      wsEvents,
      consoleMessages,
      errorLogs,
      networkRequests,
      finalUrl,
      isOnGamePage,
      hasWaitingIndicator,
      hasGameContent
    });
  });
});

async function generateReport(data) {
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      roomCode: data.roomCode,
      totalWsEvents: data.wsEvents.length,
      totalConsoleMessages: data.consoleMessages.length,
      totalErrors: data.errorLogs.length,
      reachedGamePage: data.isOnGamePage,
      stuckOnWaiting: data.hasWaitingIndicator && !data.isOnGamePage
    },
    
    // Analyze WebSocket events
    wsAnalysis: {
      totalEvents: data.wsEvents.length,
      eventTypes: countEventTypes(data.wsEvents),
      gameStartedEvents: data.wsEvents.filter(e => e.data?.type === 'game_started'),
      stateSyncEvents: data.wsEvents.filter(e => e.data?.type === 'state_sync'),
      errorEvents: data.wsEvents.filter(e => e.type === 'error' || e.data?.type === 'error'),
      lastEvents: data.wsEvents.slice(-20)
    },
    
    // Console analysis
    consoleAnalysis: {
      errors: data.consoleMessages.filter(m => m.type === 'error'),
      warnings: data.consoleMessages.filter(m => m.type === 'warning'),
      importantLogs: data.consoleMessages.filter(m => 
        m.text.includes('game') || 
        m.text.includes('start') || 
        m.text.includes('error') ||
        m.text.includes('WS')
      )
    },
    
    // Error analysis
    errors: data.errorLogs,
    
    // Final state
    finalState: {
      url: data.finalUrl,
      isOnGamePage: data.isOnGamePage,
      hasWaitingIndicator: data.hasWaitingIndicator,
      hasGameContent: data.hasGameContent
    },
    
    // Potential issues identified
    issues: identifyIssues(data)
  };
  
  // Write report to file
  const reportPath = path.join(SCREENSHOT_DIR, 'test-report.json');
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  
  // Print summary
  console.log('\n=== TEST REPORT SUMMARY ===');
  console.log(`Room Code: ${report.summary.roomCode}`);
  console.log(`Total WebSocket Events: ${report.summary.totalWsEvents}`);
  console.log(`Reached Game Page: ${report.summary.reachedGamePage}`);
  console.log(`Stuck on Waiting: ${report.summary.stuckOnWaiting}`);
  console.log(`Errors Found: ${report.summary.totalErrors}`);
  
  if (report.issues.length > 0) {
    console.log('\nIdentified Issues:');
    report.issues.forEach((issue, i) => {
      console.log(`${i + 1}. ${issue}`);
    });
  }
  
  console.log(`\nFull report saved to: ${reportPath}`);
  console.log(`Screenshots saved to: ${SCREENSHOT_DIR}`);
}

function countEventTypes(events) {
  const types = {};
  events.forEach(event => {
    if (event.data && event.data.type) {
      types[event.data.type] = (types[event.data.type] || 0) + 1;
    } else if (event.type) {
      types[event.type] = (types[event.type] || 0) + 1;
    }
  });
  return types;
}

function identifyIssues(data) {
  const issues = [];
  
  // Check if game_started event was received
  const gameStartedEvents = data.wsEvents.filter(e => e.data?.type === 'game_started');
  if (gameStartedEvents.length === 0) {
    issues.push('No game_started event received from server');
  }
  
  // Check if there were WebSocket errors
  const wsErrors = data.wsEvents.filter(e => e.type === 'error');
  if (wsErrors.length > 0) {
    issues.push(`WebSocket errors detected: ${wsErrors.length}`);
  }
  
  // Check if stuck on waiting
  if (data.hasWaitingIndicator && !data.isOnGamePage) {
    issues.push('Application stuck on waiting state, did not transition to game page');
  }
  
  // Check for navigation issues
  if (gameStartedEvents.length > 0 && !data.isOnGamePage) {
    issues.push('Received game_started event but failed to navigate to game page');
  }
  
  // Check for console errors
  const consoleErrors = data.consoleMessages.filter(m => m.type === 'error');
  if (consoleErrors.length > 0) {
    issues.push(`Console errors detected: ${consoleErrors.length}`);
    
    // Identify unique error messages
    const uniqueErrors = new Set(consoleErrors.map(e => e.text));
    uniqueErrors.forEach(error => {
      issues.push(`  - ${error}`);
    });
  }
  
  // Check for missing state sync
  const stateSyncEvents = data.wsEvents.filter(e => e.data?.type === 'state_sync');
  if (stateSyncEvents.length === 0) {
    issues.push('No state_sync events received');
  }
  
  // Check WebSocket connection stability
  const wsCloseEvents = data.wsEvents.filter(e => e.type === 'close');
  if (wsCloseEvents.length > 0) {
    issues.push(`WebSocket connection closed ${wsCloseEvents.length} time(s)`);
  }
  
  return issues;
}