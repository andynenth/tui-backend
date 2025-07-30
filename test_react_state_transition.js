const { chromium } = require('playwright');
const fs = require('fs').promises;

async function monitorReactStateTransition() {
  console.log('🔍 React State Transition Monitor\n');

  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  // Inject React DevTools hook
  await page.addInitScript(() => {
    window.__REACT_DEVTOOLS_GLOBAL_HOOK__ = {
      onCommitFiberRoot: (id, root) => {
        window.__reactFiberRoot = root;
        window.postMessage({ type: 'REACT_COMMIT', timestamp: Date.now() }, '*');
      },
      inject: () => {},
      checkDCE: () => {},
      onCommitFiberUnmount: () => {},
    };
  });

  // Listen for React commits
  await page.evaluateOnNewDocument(() => {
    window.__reactStateHistory = [];
    
    window.addEventListener('message', (event) => {
      if (event.data.type === 'REACT_COMMIT') {
        const state = captureReactState();
        window.__reactStateHistory.push({
          timestamp: event.data.timestamp,
          state
        });
      }
    });

    function captureReactState() {
      const root = window.__reactFiberRoot;
      if (!root) return null;

      const state = {
        components: [],
        routing: {
          pathname: window.location.pathname,
          search: window.location.search
        }
      };

      function traverseFiber(fiber, depth = 0) {
        if (!fiber || depth > 10) return;

        // Look for interesting components
        const interestingComponents = ['Game', 'WaitingRoom', 'GameBoard', 'App', 'Router'];
        
        if (fiber.elementType?.name && interestingComponents.includes(fiber.elementType.name)) {
          state.components.push({
            name: fiber.elementType.name,
            props: sanitizeProps(fiber.memoizedProps),
            state: fiber.memoizedState,
            depth
          });
        }

        // Look for hooks that might contain game state
        if (fiber.memoizedState && fiber.elementType?.name) {
          let hookState = fiber.memoizedState;
          const hooks = [];
          
          while (hookState) {
            if (hookState.memoizedState !== undefined) {
              hooks.push(hookState.memoizedState);
            }
            hookState = hookState.next;
          }
          
          if (hooks.length > 0 && fiber.elementType.name.includes('Game')) {
            state.components.push({
              name: `${fiber.elementType.name}_hooks`,
              hooks: hooks,
              depth
            });
          }
        }

        if (fiber.child) traverseFiber(fiber.child, depth + 1);
        if (fiber.sibling) traverseFiber(fiber.sibling, depth);
      }

      function sanitizeProps(props) {
        if (!props) return null;
        const safe = {};
        
        ['gameState', 'roomCode', 'playerId', 'isHost', 'players', 'currentPhase', 'gameStarted']
          .forEach(key => {
            if (props[key] !== undefined) {
              safe[key] = props[key];
            }
          });
        
        return safe;
      }

      traverseFiber(root.current);
      return state;
    }
  });

  try {
    console.log('📱 Navigating to homepage...');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Create room
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(1000);

    const roomCode = await page.textContent('[data-testid="room-code"]');
    console.log(`Room created: ${roomCode}\n`);

    // Start monitoring before clicking start
    console.log('🎯 Setting up state monitoring...');
    
    // Clear history
    await page.evaluate(() => {
      window.__reactStateHistory = [];
      window.__transitionStarted = false;
    });

    // Wait for start button
    const startButton = await page.waitForSelector('button:has-text("Start Game")', {
      state: 'visible'
    });

    console.log('🚀 Clicking Start Game and monitoring state changes...\n');

    // Set up continuous monitoring
    const stateMonitor = setInterval(async () => {
      const snapshot = await page.evaluate(() => {
        const history = window.__reactStateHistory;
        const currentUrl = window.location.pathname;
        const hasGameBoard = !!document.querySelector('[data-testid="game-board"]');
        const hasWaitingRoom = !!document.querySelector('[data-testid="waiting-room"]');
        
        // Get current React state
        const root = document.querySelector('#root');
        const fiberKey = root ? Object.keys(root).find(key => key.startsWith('__reactFiber')) : null;
        
        let currentGameState = null;
        if (fiberKey && root[fiberKey]) {
          const fiber = root[fiberKey];
          
          function findGameState(node) {
            if (!node) return null;
            
            if (node.memoizedProps?.gameState) {
              return node.memoizedProps.gameState;
            }
            
            const child = findGameState(node.child);
            if (child) return child;
            
            return findGameState(node.sibling);
          }
          
          currentGameState = findGameState(fiber);
        }
        
        return {
          historyLength: history.length,
          currentUrl,
          hasGameBoard,
          hasWaitingRoom,
          currentGameState,
          lastCommit: history[history.length - 1]
        };
      });

      console.log(`[Monitor] URL: ${snapshot.currentUrl}, GameBoard: ${snapshot.hasGameBoard}, WaitingRoom: ${snapshot.hasWaitingRoom}`);
      
      if (snapshot.currentGameState) {
        console.log(`[Monitor] Game State:`, snapshot.currentGameState);
      }
      
      if (snapshot.hasGameBoard) {
        console.log('✅ Game board detected! Transition successful.');
        clearInterval(stateMonitor);
      }
    }, 500);

    // Click start button
    await startButton.click();
    
    await page.evaluate(() => {
      window.__transitionStarted = true;
    });

    // Wait up to 10 seconds for transition
    await page.waitForTimeout(10000);
    clearInterval(stateMonitor);

    // Get final analysis
    console.log('\n📊 Analyzing React state history...\n');
    
    const analysis = await page.evaluate(() => {
      const history = window.__reactStateHistory;
      
      const analysis = {
        totalCommits: history.length,
        componentChanges: {},
        stateTransitions: [],
        routeChanges: []
      };

      // Track component appearances
      history.forEach((snapshot, index) => {
        snapshot.state?.components.forEach(comp => {
          if (!analysis.componentChanges[comp.name]) {
            analysis.componentChanges[comp.name] = {
              firstSeen: index,
              count: 0,
              states: []
            };
          }
          analysis.componentChanges[comp.name].count++;
          analysis.componentChanges[comp.name].states.push({
            index,
            props: comp.props,
            state: comp.state
          });
        });

        // Track route changes
        if (index > 0) {
          const prevRoute = history[index - 1].state?.routing.pathname;
          const currRoute = snapshot.state?.routing.pathname;
          if (prevRoute !== currRoute) {
            analysis.routeChanges.push({
              from: prevRoute,
              to: currRoute,
              atCommit: index
            });
          }
        }
      });

      // Find game state transitions
      history.forEach((snapshot, index) => {
        const gameComp = snapshot.state?.components.find(c => c.name === 'Game' || c.name.includes('Game'));
        if (gameComp?.props?.gameState) {
          analysis.stateTransitions.push({
            commit: index,
            timestamp: snapshot.timestamp,
            gameState: gameComp.props.gameState
          });
        }
      });

      return analysis;
    });

    console.log('📈 Component Activity:');
    Object.entries(analysis.componentChanges).forEach(([name, data]) => {
      console.log(`   ${name}: ${data.count} renders (first at commit ${data.firstSeen})`);
    });

    console.log('\n🔄 Route Changes:');
    if (analysis.routeChanges.length === 0) {
      console.log('   ❌ No route changes detected!');
    } else {
      analysis.routeChanges.forEach(change => {
        console.log(`   ${change.from} → ${change.to} (commit ${change.atCommit})`);
      });
    }

    console.log('\n🎮 Game State Transitions:');
    if (analysis.stateTransitions.length === 0) {
      console.log('   ❌ No game state transitions detected!');
    } else {
      analysis.stateTransitions.forEach(trans => {
        console.log(`   Commit ${trans.commit}: ${JSON.stringify(trans.gameState)}`);
      });
    }

    // Save detailed report
    const detailedHistory = await page.evaluate(() => window.__reactStateHistory);
    const report = {
      summary: analysis,
      history: detailedHistory,
      finalUrl: page.url(),
      timestamp: new Date().toISOString()
    };

    const reportPath = `react-state-report-${Date.now()}.json`;
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    console.log(`\n📄 Detailed report saved to: ${reportPath}`);

    console.log('\n✅ Monitoring complete. Browser will remain open.');
    await new Promise(() => {});

  } catch (error) {
    console.error('❌ Error:', error);
  }
}

monitorReactStateTransition().catch(console.error);