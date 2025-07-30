const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

class WebSocketDebugger {
  constructor() {
    this.wsMessages = [];
    this.events = [];
    this.startTime = Date.now();
  }

  logEvent(type, data, extra = {}) {
    const event = {
      timestamp: Date.now() - this.startTime,
      type,
      data,
      ...extra
    };
    this.events.push(event);
    console.log(`[${event.timestamp}ms] ${type}:`, data);
  }

  logWsMessage(direction, data) {
    const message = {
      timestamp: Date.now() - this.startTime,
      direction,
      data,
      parsed: null
    };

    try {
      message.parsed = JSON.parse(data);
    } catch (e) {
      // Not JSON
    }

    this.wsMessages.push(message);
    console.log(`[${message.timestamp}ms] WS ${direction}:`, message.parsed || data);
  }

  async generateReport() {
    const report = {
      summary: {
        totalEvents: this.events.length,
        totalWsMessages: this.wsMessages.length,
        duration: Date.now() - this.startTime,
        startTime: new Date(this.startTime).toISOString()
      },
      events: this.events,
      wsMessages: this.wsMessages,
      timeline: this.generateTimeline(),
      analysis: this.analyzeFlow()
    };

    const reportPath = path.join(__dirname, `ws-debug-report-${Date.now()}.json`);
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    console.log(`\nReport saved to: ${reportPath}`);

    return report;
  }

  generateTimeline() {
    const allEvents = [
      ...this.events.map(e => ({ ...e, source: 'app' })),
      ...this.wsMessages.map(m => ({
        timestamp: m.timestamp,
        type: `ws_${m.direction}`,
        data: m.parsed || m.data,
        source: 'websocket'
      }))
    ].sort((a, b) => a.timestamp - b.timestamp);

    return allEvents;
  }

  analyzeFlow() {
    const analysis = {
      missingEvents: [],
      unexpectedEvents: [],
      stateTransitions: [],
      potentialIssues: []
    };

    // Expected events after start button click
    const expectedEvents = ['game_started', 'game_state_updated', 'player_joined'];
    const receivedEvents = this.wsMessages
      .filter(m => m.direction === 'received' && m.parsed?.type)
      .map(m => m.parsed.type);

    expectedEvents.forEach(event => {
      if (!receivedEvents.includes(event)) {
        analysis.missingEvents.push(event);
      }
    });

    // Check for state transitions
    const gameStartedMsg = this.wsMessages.find(
      m => m.direction === 'received' && m.parsed?.type === 'game_started'
    );

    if (gameStartedMsg) {
      analysis.stateTransitions.push({
        event: 'game_started',
        timestamp: gameStartedMsg.timestamp,
        hasNavigationFollowed: this.events.some(
          e => e.type === 'navigation' && e.timestamp > gameStartedMsg.timestamp
        )
      });
    }

    // Identify potential issues
    if (analysis.missingEvents.length > 0) {
      analysis.potentialIssues.push(
        `Missing expected WebSocket events: ${analysis.missingEvents.join(', ')}`
      );
    }

    const lastWsMessage = this.wsMessages[this.wsMessages.length - 1];
    if (lastWsMessage && Date.now() - this.startTime - lastWsMessage.timestamp > 5000) {
      analysis.potentialIssues.push('No WebSocket activity for over 5 seconds');
    }

    return analysis;
  }
}

async function debugWebSocketTransition() {
  const debugger = new WebSocketDebugger();
  console.log('🔍 WebSocket Transition Debugger Starting...\n');

  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable WebSocket interception
  await page.route('**/*', route => route.continue());

  // Intercept WebSocket connections
  page.on('websocket', ws => {
    debugger.logEvent('websocket_created', { url: ws.url() });

    ws.on('framesent', event => {
      debugger.logWsMessage('sent', event.payload);
    });

    ws.on('framereceived', event => {
      debugger.logWsMessage('received', event.payload);
    });

    ws.on('close', () => {
      debugger.logEvent('websocket_closed', { url: ws.url() });
    });
  });

  // Monitor console messages
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.text().includes('WebSocket') || msg.text().includes('game')) {
      debugger.logEvent('console', {
        type: msg.type(),
        text: msg.text()
      });
    }
  });

  // Monitor network requests
  page.on('request', request => {
    if (request.url().includes('/api/') || request.url().includes('game')) {
      debugger.logEvent('network_request', {
        url: request.url(),
        method: request.method()
      });
    }
  });

  page.on('response', response => {
    if (response.url().includes('/api/') || response.url().includes('game')) {
      debugger.logEvent('network_response', {
        url: response.url(),
        status: response.status()
      });
    }
  });

  try {
    console.log('📱 Navigating to homepage...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Create/Join room flow
    console.log('\n🏠 Creating room...');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(1000);

    const roomCodeElement = await page.waitForSelector('[data-testid="room-code"]', {
      timeout: 10000
    });
    const roomCode = await roomCodeElement.textContent();
    console.log(`Room created with code: ${roomCode}`);

    // Monitor React state before clicking start
    console.log('\n🔍 Checking initial React state...');
    const initialState = await page.evaluate(() => {
      const rootElement = document.querySelector('#root');
      if (!rootElement || !rootElement._reactRootContainer) {
        return { error: 'React root not found' };
      }

      // Try to find React fiber
      const fiberKey = Object.keys(rootElement).find(key => key.startsWith('__reactFiber'));
      if (!fiberKey) {
        return { error: 'React fiber not found' };
      }

      // Extract game state from React components
      const fiber = rootElement[fiberKey];
      let currentFiber = fiber;
      const components = [];

      while (currentFiber) {
        if (currentFiber.memoizedProps || currentFiber.memoizedState) {
          components.push({
            type: currentFiber.elementType?.name || 'Unknown',
            props: currentFiber.memoizedProps,
            state: currentFiber.memoizedState
          });
        }
        currentFiber = currentFiber.child || currentFiber.sibling;
      }

      return { components };
    });
    debugger.logEvent('react_state_initial', initialState);

    // Wait for start button to be ready
    console.log('\n⏳ Waiting for game to be ready...');
    const startButton = await page.waitForSelector('button:has-text("Start Game")', {
      state: 'visible',
      timeout: 10000
    });

    // Set up monitoring for the transition
    console.log('\n🚀 Clicking Start Game button and monitoring transition...');
    
    // Monitor for navigation
    const navigationPromise = page.waitForURL('**/game/**', { 
      timeout: 15000 
    }).catch(e => {
      debugger.logEvent('navigation_timeout', { error: e.message });
      return null;
    });

    // Click the start button
    await startButton.click();
    debugger.logEvent('start_button_clicked', { timestamp: Date.now() });

    // Monitor React state changes
    for (let i = 0; i < 10; i++) {
      await page.waitForTimeout(500);
      
      const currentState = await page.evaluate(() => {
        // Check if we're still on waiting page or moved to game
        const url = window.location.pathname;
        const waitingElement = document.querySelector('[data-testid="waiting-room"]');
        const gameElement = document.querySelector('[data-testid="game-board"]');
        
        return {
          url,
          onWaitingPage: !!waitingElement,
          onGamePage: !!gameElement,
          reactComponents: (() => {
            const rootElement = document.querySelector('#root');
            if (!rootElement) return null;
            
            const fiberKey = Object.keys(rootElement).find(key => key.startsWith('__reactFiber'));
            if (!fiberKey) return null;
            
            const fiber = rootElement[fiberKey];
            const gameComponent = findGameComponent(fiber);
            
            function findGameComponent(node) {
              if (!node) return null;
              
              if (node.elementType?.name === 'Game' || 
                  node.elementType?.name === 'WaitingRoom' ||
                  node.memoizedProps?.gameState) {
                return {
                  name: node.elementType?.name,
                  props: node.memoizedProps,
                  state: node.memoizedState
                };
              }
              
              const child = findGameComponent(node.child);
              if (child) return child;
              
              return findGameComponent(node.sibling);
            }
          })()
        };
      });
      
      debugger.logEvent('state_check', currentState, { iteration: i + 1 });
      
      if (currentState.onGamePage) {
        debugger.logEvent('game_page_detected', { afterMs: (i + 1) * 500 });
        break;
      }
    }

    // Wait for navigation result
    const navResult = await navigationPromise;
    if (navResult === null) {
      debugger.logEvent('navigation_failed', { 
        currentUrl: page.url(),
        timeout: true 
      });
    } else {
      debugger.logEvent('navigation_completed', { 
        newUrl: page.url() 
      });
    }

    // Final state check
    const finalState = await page.evaluate(() => {
      return {
        url: window.location.pathname,
        title: document.title,
        hasGameBoard: !!document.querySelector('[data-testid="game-board"]'),
        hasWaitingRoom: !!document.querySelector('[data-testid="waiting-room"]'),
        bodyText: document.body.innerText.substring(0, 500)
      };
    });
    debugger.logEvent('final_state', finalState);

    // Generate report
    console.log('\n📊 Generating debug report...');
    const report = await debugger.generateReport();

    // Print analysis summary
    console.log('\n🔍 Analysis Summary:');
    console.log('==================');
    console.log(`Total Events: ${report.summary.totalEvents}`);
    console.log(`WebSocket Messages: ${report.summary.totalWsMessages}`);
    console.log(`Duration: ${report.summary.duration}ms`);
    
    if (report.analysis.missingEvents.length > 0) {
      console.log(`\n❌ Missing Events: ${report.analysis.missingEvents.join(', ')}`);
    }
    
    if (report.analysis.potentialIssues.length > 0) {
      console.log('\n⚠️  Potential Issues:');
      report.analysis.potentialIssues.forEach(issue => {
        console.log(`  - ${issue}`);
      });
    }

    // Keep browser open for manual inspection
    console.log('\n✅ Debug session complete. Browser will remain open for inspection.');
    console.log('Press Ctrl+C to exit.');
    
    await new Promise(() => {}); // Keep script running

  } catch (error) {
    console.error('❌ Error during debugging:', error);
    debugger.logEvent('error', { 
      message: error.message,
      stack: error.stack 
    });
    
    await debugger.generateReport();
  }
}

// Run the debugger
debugWebSocketTransition().catch(console.error);