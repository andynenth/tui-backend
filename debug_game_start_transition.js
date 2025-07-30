const { chromium } = require('playwright');
const fs = require('fs').promises;

class TransitionDebugger {
  constructor() {
    this.findings = {
      websocketEvents: [],
      reactUpdates: [],
      navigationAttempts: [],
      errors: [],
      apiCalls: [],
      timeline: []
    };
    this.startTime = Date.now();
  }

  log(category, message, data = {}) {
    const entry = {
      timestamp: Date.now() - this.startTime,
      category,
      message,
      data
    };
    
    this.findings.timeline.push(entry);
    console.log(`[${entry.timestamp}ms] ${category}: ${message}`, data);
  }

  async generateDiagnosis() {
    const diagnosis = {
      summary: {
        duration: Date.now() - this.startTime,
        totalEvents: this.findings.timeline.length,
        errors: this.findings.errors.length
      },
      problems: [],
      recommendations: []
    };

    // Check for common issues
    
    // 1. Missing WebSocket events
    const wsEvents = this.findings.timeline.filter(e => e.category === 'websocket');
    const hasStartGameSent = wsEvents.some(e => e.data.type === 'start_game' && e.data.direction === 'sent');
    const hasGameStartedReceived = wsEvents.some(e => e.data.type === 'game_started' && e.data.direction === 'received');
    
    if (hasStartGameSent && !hasGameStartedReceived) {
      diagnosis.problems.push({
        severity: 'high',
        issue: 'start_game sent but no game_started received',
        description: 'The server is not responding to the start_game message'
      });
      diagnosis.recommendations.push('Check server WebSocket handler for start_game event');
    }

    // 2. Navigation issues
    const navAttempts = this.findings.timeline.filter(e => e.category === 'navigation');
    const successfulNav = navAttempts.some(e => e.data.success);
    
    if (!successfulNav && hasGameStartedReceived) {
      diagnosis.problems.push({
        severity: 'high',
        issue: 'game_started received but navigation failed',
        description: 'Frontend is not handling the game_started event properly'
      });
      diagnosis.recommendations.push('Check frontend WebSocket event handler for game_started');
    }

    // 3. React state issues
    const reactUpdates = this.findings.timeline.filter(e => e.category === 'react');
    const gameStateUpdates = reactUpdates.filter(e => e.data.gameState);
    
    if (gameStateUpdates.length === 0) {
      diagnosis.problems.push({
        severity: 'medium',
        issue: 'No game state updates in React',
        description: 'React components are not receiving or processing game state'
      });
    }

    // 4. API call issues
    const apiCalls = this.findings.timeline.filter(e => e.category === 'api');
    const failedCalls = apiCalls.filter(e => e.data.status >= 400);
    
    if (failedCalls.length > 0) {
      diagnosis.problems.push({
        severity: 'high',
        issue: `${failedCalls.length} failed API calls`,
        description: 'Backend API endpoints are returning errors',
        details: failedCalls
      });
    }

    return diagnosis;
  }
}

async function debugGameStartTransition() {
  const debuggerInstance = new TransitionDebugger();
  console.log('🔍 Game Start Transition Debugger\n');

  const browser = await chromium.launch({
    headless: false,
    devtools: true,
    args: ['--enable-logging', '--v=1']
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // Comprehensive event monitoring
  
  // 1. WebSocket monitoring
  page.on('websocket', ws => {
    debuggerInstance.log('websocket', 'WebSocket created', { url: ws.url() });

    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        debuggerInstance.log('websocket', `Sent: ${data.type}`, {
          type: data.type,
          direction: 'sent',
          payload: data.payload
        });
      } catch (e) {
        debuggerInstance.log('websocket', 'Sent non-JSON', { payload: event.payload });
      }
    });

    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        debuggerInstance.log('websocket', `Received: ${data.type}`, {
          type: data.type,
          direction: 'received',
          payload: data.payload
        });
      } catch (e) {
        debuggerInstance.log('websocket', 'Received non-JSON', { payload: event.payload });
      }
    });
  });

  // 2. Console monitoring
  page.on('console', msg => {
    if (msg.type() === 'error') {
      debuggerInstance.findings.errors.push({
        timestamp: Date.now() - debuggerInstance.startTime,
        text: msg.text(),
        location: msg.location()
      });
      debuggerInstance.log('console', 'Error', { text: msg.text() });
    } else if (msg.text().includes('Navigate') || msg.text().includes('Route')) {
      debuggerInstance.log('console', 'Navigation log', { text: msg.text() });
    }
  });

  // 3. Network monitoring
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      debuggerInstance.log('api', `Request: ${request.method()} ${request.url()}`, {
        method: request.method(),
        url: request.url()
      });
    }
  });

  page.on('response', response => {
    if (response.url().includes('/api/')) {
      debuggerInstance.log('api', `Response: ${response.status()} ${response.url()}`, {
        status: response.status(),
        url: response.url()
      });
    }
  });

  // 4. Page errors
  page.on('pageerror', error => {
    debuggerInstance.findings.errors.push({
      timestamp: Date.now() - debuggerInstance.startTime,
      message: error.message,
      stack: error.stack
    });
    debuggerInstance.log('error', 'Page error', { message: error.message });
  });

  // 5. Navigation monitoring
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      debuggerInstance.log('navigation', 'Navigation occurred', {
        url: frame.url(),
        success: true
      });
    }
  });

  try {
    // Navigate to app
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');

    // Inject debugging helpers
    await page.evaluate(() => {
      // Override history.pushState to monitor navigation attempts
      const originalPushState = window.history.pushState;
      window.history.pushState = function(...args) {
        console.log('Navigation attempt:', args[2]);
        window.postMessage({
          type: 'NAVIGATION_ATTEMPT',
          url: args[2],
          timestamp: Date.now()
        }, '*');
        return originalPushState.apply(this, args);
      };

      // Monitor React Router (if using react-router)
      window.__monitorRouter = () => {
        const event = new CustomEvent('routeChange', {
          detail: { pathname: window.location.pathname }
        });
        window.dispatchEvent(event);
      };
    });

    // Listen for custom events
    await page.evaluateOnNewDocument(() => {
      window.addEventListener('message', (event) => {
        if (event.data.type === 'NAVIGATION_ATTEMPT') {
          console.log('Navigation attempted to:', event.data.url);
        }
      });

      window.addEventListener('routeChange', (event) => {
        console.log('Route changed to:', event.detail.pathname);
      });
    });

    // Create room and get to waiting state
    debuggerInstance.log('setup', 'Creating room');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(1000);

    const roomCode = await page.textContent('[data-testid="room-code"]');
    debuggerInstance.log('setup', `Room created: ${roomCode}`);

    // Wait for start button
    const startButton = await page.waitForSelector('button:has-text("Start Game")', {
      state: 'visible'
    });

    // Monitor React state before start
    const beforeState = await page.evaluate(() => {
      const root = document.querySelector('#root');
      if (!root) return null;
      
      const fiberKey = Object.keys(root).find(key => key.startsWith('__reactFiber'));
      if (!fiberKey) return null;
      
      function extractGameInfo(fiber) {
        const info = {
          components: [],
          gameState: null,
          route: window.location.pathname
        };
        
        function traverse(node, depth = 0) {
          if (!node || depth > 10) return;
          
          if (node.elementType?.name) {
            info.components.push(node.elementType.name);
            
            if (node.memoizedProps?.gameState) {
              info.gameState = node.memoizedProps.gameState;
            }
          }
          
          if (node.child) traverse(node.child, depth + 1);
          if (node.sibling) traverse(node.sibling, depth);
        }
        
        traverse(fiber);
        return info;
      }
      
      return extractGameInfo(root[fiberKey]);
    });
    
    debuggerInstance.log('react', 'State before start', beforeState);

    // Set up monitoring loop
    console.log('\n🚀 Clicking Start Game...\n');
    
    let transitionDetected = false;
    const monitor = setInterval(async () => {
      const state = await page.evaluate(() => ({
        url: window.location.pathname,
        hasGameBoard: !!document.querySelector('[data-testid="game-board"]'),
        hasWaitingRoom: !!document.querySelector('[data-testid="waiting-room"]'),
        bodyText: document.body.innerText.substring(0, 200)
      }));
      
      debuggerInstance.log('monitor', 'Current state', state);
      
      if (state.hasGameBoard || state.url.includes('/game/')) {
        transitionDetected = true;
        clearInterval(monitor);
        debuggerInstance.log('success', '✅ Transition successful!');
      }
    }, 250);

    // Click start
    await startButton.click();
    debuggerInstance.log('action', 'Start button clicked');

    // Wait for transition or timeout
    await page.waitForTimeout(10000);
    clearInterval(monitor);

    if (!transitionDetected) {
      debuggerInstance.log('failure', '❌ Transition failed - timeout');
      
      // Get current state
      const finalState = await page.evaluate(() => {
        const state = {
          url: window.location.pathname,
          title: document.title,
          hasGameBoard: !!document.querySelector('[data-testid="game-board"]'),
          hasWaitingRoom: !!document.querySelector('[data-testid="waiting-room"]'),
          visibleText: document.body.innerText.substring(0, 500),
          // Check for specific error elements
          hasErrors: !!document.querySelector('.error, [class*="error"]'),
          // Get all button states
          buttons: Array.from(document.querySelectorAll('button')).map(btn => ({
            text: btn.innerText,
            disabled: btn.disabled
          }))
        };
        
        // Try to get React error boundary state
        const root = document.querySelector('#root');
        if (root) {
          const fiberKey = Object.keys(root).find(key => key.startsWith('__reactFiber'));
          if (fiberKey && root[fiberKey]) {
            const fiber = root[fiberKey];
            // Look for error boundary
            function findErrorBoundary(node) {
              if (!node) return null;
              if (node.elementType?.getDerivedStateFromError || node.elementType?.componentDidCatch) {
                return {
                  hasError: !!node.memoizedState?.hasError,
                  error: node.memoizedState?.error
                };
              }
              const child = findErrorBoundary(node.child);
              if (child) return child;
              return findErrorBoundary(node.sibling);
            }
            state.errorBoundary = findErrorBoundary(fiber);
          }
        }
        
        return state;
      });
      
      debuggerInstance.log('final_state', 'Final page state', finalState);
    }

    // Generate diagnosis
    console.log('\n📊 Generating diagnosis...\n');
    const diagnosis = await debuggerInstance.generateDiagnosis();
    
    // Print diagnosis
    console.log('🔍 DIAGNOSIS');
    console.log('============\n');
    
    if (diagnosis.problems.length === 0) {
      console.log('✅ No problems detected!');
    } else {
      console.log(`Found ${diagnosis.problems.length} problems:\n`);
      diagnosis.problems.forEach((problem, i) => {
        console.log(`${i + 1}. [${problem.severity.toUpperCase()}] ${problem.issue}`);
        console.log(`   ${problem.description}`);
        if (problem.details) {
          console.log(`   Details:`, problem.details);
        }
        console.log('');
      });
    }
    
    if (diagnosis.recommendations.length > 0) {
      console.log('\n💡 RECOMMENDATIONS');
      console.log('==================\n');
      diagnosis.recommendations.forEach((rec, i) => {
        console.log(`${i + 1}. ${rec}`);
      });
    }

    // Save full report
    const report = {
      diagnosis,
      findings: debuggerInstance.findings,
      timestamp: new Date().toISOString()
    };
    
    const reportPath = `transition-diagnosis-${Date.now()}.json`;
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    console.log(`\n📄 Full report saved to: ${reportPath}`);

    console.log('\n✅ Debugging complete. Browser remains open for inspection.');
    await new Promise(() => {});

  } catch (error) {
    console.error('❌ Debugger error:', error);
    debuggerInstance.log('error', 'Debugger error', { message: error.message, stack: error.stack });
  }
}

debugGameStartTransition().catch(console.error);