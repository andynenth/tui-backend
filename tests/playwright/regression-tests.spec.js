/**
 * 🔄 **Regression Test Suite - Game Start Flow**
 * 
 * PlaywrightTester Agent - Regression Prevention & Fix Validation
 * 
 * Purpose:
 * - Prevent future regressions of the game start bug
 * - Validate fixes remain stable over time
 * - Test edge cases and boundary conditions
 * - Performance regression detection
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs').promises;
const path = require('path');

// Regression Test Configuration
const REGRESSION_CONFIG = {
  BASE_URL: 'http://localhost:5050',
  SCREENSHOT_DIR: './test-results/regression-tests',
  SCENARIOS: {
    SINGLE_PLAYER_BOTS: 'single-player-with-bots',
    PARTIAL_ROOM: 'partial-room-scenario',
    RAPID_CLICKS: 'rapid-start-clicks',
    NETWORK_DELAY: 'network-delay-simulation',
    CONCURRENT_ROOMS: 'concurrent-room-creation'
  },
  PERFORMANCE_THRESHOLDS: {
    GAME_START_TIME: 5000,  // 5 seconds max
    WEBSOCKET_RESPONSE: 2000, // 2 seconds max
    PAGE_TRANSITION: 3000   // 3 seconds max
  }
};

let regressionResults = {
  scenarios: {},
  performanceMetrics: {},
  bugDetections: []
};

test.describe('🔄 Regression Test Suite - Game Start Flow', () => {
  
  test.beforeAll(async () => {
    await fs.mkdir(REGRESSION_CONFIG.SCREENSHOT_DIR, { recursive: true });
    console.log('🔄 Regression test suite initialized');
    
    // Initialize regression tracking
    regressionResults = {
      scenarios: {},
      performanceMetrics: {},
      bugDetections: [],
      testSuiteStart: Date.now()
    };
  });

  test.afterAll(async () => {
    // Generate regression report
    await generateRegressionReport(regressionResults);
  });

  /**
   * 🎯 **PRIMARY REGRESSION TEST**
   * 
   * Ensures the main bug scenario remains fixed
   */
  test('🎯 PRIMARY: Game start works - no regression of stuck waiting page', async ({ page }) => {
    console.log('🎯 === PRIMARY REGRESSION TEST ===');
    
    const scenario = REGRESSION_CONFIG.SCENARIOS.SINGLE_PLAYER_BOTS;
    const testStart = Date.now();
    
    try {
      // Setup performance monitoring
      const performanceData = await setupPerformanceMonitoring(page);
      
      // Execute the previously buggy scenario
      await page.goto(REGRESSION_CONFIG.BASE_URL);
      await page.fill('input[placeholder="Enter your name"]', 'RegressionTestUser');
      await page.click('button:has-text("Create Room")');
      await page.waitForURL(/\/room\/.+/, { timeout: 10000 });
      
      const roomCode = page.url().split('/').pop();
      console.log(`🏠 Room created: ${roomCode}`);
      
      // Add bots (the scenario that previously caused the bug)
      for (let i = 0; i < 3; i++) {
        await page.locator('button:has-text("Add Bot")').first().click();
        await page.waitForTimeout(500);
      }
      
      // Start game - this should NOT get stuck
      const startButton = page.locator('button:has-text("Start Game")');
      await expect(startButton).toBeVisible({ timeout: 10000 });
      
      const gameStartTime = Date.now();
      console.log('🚀 Starting game - monitoring for regression...');
      
      // Set up success monitoring
      const gameStartPromise = page.evaluate(() => {
        return new Promise((resolve) => {
          const checkInterval = setInterval(() => {
            const gameStartedEvent = window.wsEvents?.find(e => 
              e.data && e.data.type === 'game_started'
            );
            if (gameStartedEvent) {
              clearInterval(checkInterval);
              resolve(gameStartedEvent);
            }
          }, 100);
          
          setTimeout(() => {
            clearInterval(checkInterval);
            resolve(null);
          }, REGRESSION_CONFIG.PERFORMANCE_THRESHOLDS.GAME_START_TIME);
        });
      });
      
      await startButton.click();
      
      // Wait for successful game start
      const gameStartedEvent = await gameStartPromise;
      const gameStartDuration = Date.now() - gameStartTime;
      
      // Check final state
      const finalUrl = page.url();
      const onGamePage = finalUrl.includes('/game/');
      const hasWaitingText = await page.locator('text=waiting', { timeout: 1000 }).count().catch(() => 0);
      
      console.log('📊 Regression test results:');
      console.log(`   Game started event: ${!!gameStartedEvent}`);
      console.log(`   Reached game page: ${onGamePage}`);
      console.log(`   Has waiting text: ${hasWaitingText > 0}`);
      console.log(`   Start duration: ${gameStartDuration}ms`);
      
      // Store scenario results
      regressionResults.scenarios[scenario] = {
        success: !!gameStartedEvent && onGamePage,
        gameStartedEvent: !!gameStartedEvent,
        reachedGamePage: onGamePage,
        hasWaitingText: hasWaitingText > 0,
        duration: gameStartDuration,
        roomCode: roomCode,
        timestamp: new Date().toISOString()
      };
      
      // Performance regression check
      if (gameStartDuration > REGRESSION_CONFIG.PERFORMANCE_THRESHOLDS.GAME_START_TIME) {
        console.warn(`⚠️  Performance regression: Game start took ${gameStartDuration}ms (threshold: ${REGRESSION_CONFIG.PERFORMANCE_THRESHOLDS.GAME_START_TIME}ms)`);
        regressionResults.bugDetections.push({
          type: 'performance_regression',
          scenario: scenario,
          duration: gameStartDuration,
          threshold: REGRESSION_CONFIG.PERFORMANCE_THRESHOLDS.GAME_START_TIME
        });
      }
      
      // REGRESSION ASSERTIONS
      expect(gameStartedEvent, 'Game should start successfully (no WebSocket regression)').toBeTruthy();
      expect(onGamePage, 'Should reach game page (no navigation regression)').toBe(true);
      expect(hasWaitingText, 'Should not be stuck on waiting page (no UI regression)').toBe(false);
      expect(gameStartDuration, 'Game start should be performant (no performance regression)').toBeLessThan(REGRESSION_CONFIG.PERFORMANCE_THRESHOLDS.GAME_START_TIME);
      
      console.log('✅ PRIMARY REGRESSION TEST PASSED - Bug remains fixed');
      
    } catch (error) {
      console.error('💥 REGRESSION DETECTED:', error.message);
      
      regressionResults.bugDetections.push({
        type: 'functional_regression',
        scenario: scenario,
        error: error.message,
        timestamp: new Date().toISOString()
      });
      
      // Take failure screenshot
      await page.screenshot({ 
        path: path.join(REGRESSION_CONFIG.SCREENSHOT_DIR, `${scenario}-REGRESSION-FAILURE.png`),
        fullPage: true 
      });
      
      throw new Error(`REGRESSION DETECTED in ${scenario}: ${error.message}`);
    }
  });

  /**
   * 🔀 **EDGE CASE REGRESSION TESTS**
   */
  test('🔀 Edge case: Rapid start button clicks', async ({ page }) => {
    console.log('🔀 === RAPID CLICKS REGRESSION TEST ===');
    
    const scenario = REGRESSION_CONFIG.SCENARIOS.RAPID_CLICKS;
    
    await page.goto(REGRESSION_CONFIG.BASE_URL);
    await page.fill('input[placeholder="Enter your name"]', 'RapidClickUser');
    await page.click('button:has-text("Create Room")');
    await page.waitForURL(/\/room\/.+/);
    
    // Add bots
    for (let i = 0; i < 3; i++) {
      await page.locator('button:has-text("Add Bot")').first().click();
      await page.waitForTimeout(300);
    }
    
    const startButton = page.locator('button:has-text("Start Game")');
    await expect(startButton).toBeVisible();
    
    // Rapid clicks test - should handle gracefully
    console.log('🔄 Testing rapid start button clicks...');
    
    // Click multiple times rapidly
    for (let i = 0; i < 5; i++) {
      await startButton.click({ timeout: 1000 }).catch(() => {
        console.log(`   Click ${i + 1} may have been ignored (expected)`);
      });
      await page.waitForTimeout(100);
    }
    
    // Wait for resolution
    await page.waitForTimeout(5000);
    
    const finalUrl = page.url();
    const onGamePage = finalUrl.includes('/game/');
    const hasErrors = await page.locator('.error, [class*="error"]').count();
    
    console.log(`📊 Rapid clicks results: Game page=${onGamePage}, Errors=${hasErrors}`);
    
    regressionResults.scenarios[scenario] = {
      success: onGamePage && hasErrors === 0,
      reachedGamePage: onGamePage,
      errorCount: hasErrors,
      timestamp: new Date().toISOString()
    };
    
    // Should handle rapid clicks gracefully
    expect(hasErrors).toBe(0);
    expect(onGamePage).toBe(true);
    
    console.log('✅ Rapid clicks handled gracefully');
  });

  test('🔀 Edge case: Partial room scenario', async ({ page }) => {
    console.log('🔀 === PARTIAL ROOM REGRESSION TEST ===');
    
    const scenario = REGRESSION_CONFIG.SCENARIOS.PARTIAL_ROOM;
    
    await page.goto(REGRESSION_CONFIG.BASE_URL);
    await page.fill('input[placeholder="Enter your name"]', 'PartialRoomUser');
    await page.click('button:has-text("Create Room")');
    await page.waitForURL(/\/room\/.+/);
    
    // Add only 1 bot (partial room)
    await page.locator('button:has-text("Add Bot")').first().click();
    await page.waitForTimeout(1000);
    
    const startButton = page.locator('button:has-text("Start Game")');
    const isVisible = await startButton.isVisible({ timeout: 5000 });
    
    if (isVisible) {
      const isEnabled = await startButton.isEnabled();
      console.log(`🔍 Start button in partial room: visible=${isVisible}, enabled=${isEnabled}`);
      
      if (isEnabled) {
        // If enabled, clicking should handle gracefully
        await startButton.click();
        await page.waitForTimeout(2000);
        
        const hasErrorMessage = await page.locator('text=need more players', { timeout: 2000 }).count().catch(() => 0);
        const remainsOnRoomPage = page.url().includes('/room/');
        
        console.log(`   Error message shown: ${hasErrorMessage > 0}`);
        console.log(`   Remains on room page: ${remainsOnRoomPage}`);
        
        regressionResults.scenarios[scenario] = {
          success: hasErrorMessage > 0 || remainsOnRoomPage,
          handledGracefully: true,
          errorMessageShown: hasErrorMessage > 0,
          timestamp: new Date().toISOString()
        };
        
        // Should show error or remain on room page
        expect(hasErrorMessage > 0 || remainsOnRoomPage).toBe(true);
      } else {
        regressionResults.scenarios[scenario] = {
          success: true,
          startButtonDisabled: true,
          timestamp: new Date().toISOString()
        };
        
        console.log('✅ Start button properly disabled in partial room');
      }
    }
  });

  /**
   * 📊 **PERFORMANCE REGRESSION TESTS**
   */
  test('📊 Performance regression: Game start timing', async ({ page }) => {
    console.log('📊 === PERFORMANCE REGRESSION TEST ===');
    
    const performanceResults = [];
    
    // Run multiple iterations to get average performance
    for (let iteration = 1; iteration <= 3; iteration++) {
      console.log(`🔄 Performance iteration ${iteration}/3`);
      
      const iterationStart = Date.now();
      
      await page.goto(REGRESSION_CONFIG.BASE_URL);
      await page.fill('input[placeholder="Enter your name"]', `PerfUser${iteration}`);
      await page.click('button:has-text("Create Room")');
      await page.waitForURL(/\/room\/.+/);
      
      const roomSetupTime = Date.now() - iterationStart;
      
      // Add bots
      const botStart = Date.now();
      for (let i = 0; i < 3; i++) {
        await page.locator('button:has-text("Add Bot")').first().click();
        await page.waitForTimeout(200);
      }
      const botSetupTime = Date.now() - botStart;
      
      // Start game
      const gameStartBegin = Date.now();
      const startButton = page.locator('button:has-text("Start Game")');
      await startButton.click();
      
      // Wait for game start
      const gameStartedPromise = page.evaluate(() => {
        return new Promise((resolve) => {
          const start = Date.now();
          const checkInterval = setInterval(() => {
            const gameStartedEvent = window.wsEvents?.find(e => 
              e.data && e.data.type === 'game_started'
            );
            if (gameStartedEvent) {
              clearInterval(checkInterval);
              resolve(Date.now() - start);
            }
            if (Date.now() - start > 10000) {
              clearInterval(checkInterval);
              resolve(null);
            }
          }, 100);
        });
      });
      
      const gameStartTime = await gameStartedPromise;
      const totalIterationTime = Date.now() - iterationStart;
      
      const result = {
        iteration,
        roomSetupTime,
        botSetupTime,
        gameStartTime,
        totalTime: totalIterationTime,
        success: !!gameStartTime
      };
      
      performanceResults.push(result);
      console.log(`   Iteration ${iteration}: Room=${roomSetupTime}ms, Bots=${botSetupTime}ms, GameStart=${gameStartTime}ms, Total=${totalIterationTime}ms`);
      
      // Reset for next iteration
      if (iteration < 3) {
        await page.goto('about:blank');
        await page.waitForTimeout(1000);
      }
    }
    
    // Analyze performance results
    const avgGameStartTime = performanceResults
      .filter(r => r.gameStartTime)
      .reduce((sum, r) => sum + r.gameStartTime, 0) / performanceResults.length;
    
    const avgTotalTime = performanceResults
      .reduce((sum, r) => sum + r.totalTime, 0) / performanceResults.length;
    
    console.log(`📊 Performance analysis:`);
    console.log(`   Average game start time: ${avgGameStartTime.toFixed(0)}ms`);
    console.log(`   Average total time: ${avgTotalTime.toFixed(0)}ms`);
    console.log(`   Success rate: ${performanceResults.filter(r => r.success).length}/3`);
    
    regressionResults.performanceMetrics = {
      avgGameStartTime,
      avgTotalTime,
      successRate: performanceResults.filter(r => r.success).length / 3,
      iterations: performanceResults,
      timestamp: new Date().toISOString()
    };
    
    // Performance regression checks
    expect(avgGameStartTime, 'Game start time should meet performance threshold').toBeLessThan(REGRESSION_CONFIG.PERFORMANCE_THRESHOLDS.GAME_START_TIME);
    expect(performanceResults.filter(r => r.success).length, 'All iterations should succeed').toBe(3);
    
    console.log('✅ Performance regression test passed');
  });

});

/**
 * 🔧 **HELPER FUNCTIONS**
 */

async function setupPerformanceMonitoring(page) {
  await page.addInitScript(() => {
    window.performanceMarks = [];
    window.mark = (name) => {
      const mark = { name, time: performance.now(), timestamp: Date.now() };
      window.performanceMarks.push(mark);
      return mark;
    };
    window.measure = (start, end) => {
      const startMark = window.performanceMarks.find(m => m.name === start);
      const endMark = window.performanceMarks.find(m => m.name === end);
      if (startMark && endMark) {
        return endMark.time - startMark.time;
      }
      return null;
    };
  });
  
  return { setupComplete: true };
}

async function generateRegressionReport(results) {
  const report = {
    testSuite: 'Game Start Flow Regression Tests',
    timestamp: new Date().toISOString(),
    duration: Date.now() - results.testSuiteStart,
    summary: {
      totalScenarios: Object.keys(results.scenarios).length,
      successfulScenarios: Object.values(results.scenarios).filter(s => s.success).length,
      regressionDetected: results.bugDetections.length > 0,
      performanceIssues: results.bugDetections.filter(b => b.type === 'performance_regression').length
    },
    scenarios: results.scenarios,
    performanceMetrics: results.performanceMetrics,
    bugDetections: results.bugDetections,
    recommendations: generateRegressionRecommendations(results)
  };
  
  const reportPath = path.join(REGRESSION_CONFIG.SCREENSHOT_DIR, 'regression-report.json');
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  
  console.log('\n🔄 === REGRESSION TEST SUMMARY ===');
  console.log(`📊 Scenarios tested: ${report.summary.totalScenarios}`);
  console.log(`✅ Successful scenarios: ${report.summary.successfulScenarios}`);
  console.log(`🚨 Regressions detected: ${results.bugDetections.length}`);
  console.log(`⚡ Performance issues: ${report.summary.performanceIssues}`);
  
  if (results.bugDetections.length > 0) {
    console.log('\n🚨 DETECTED REGRESSIONS:');
    results.bugDetections.forEach((bug, i) => {
      console.log(`   ${i + 1}. ${bug.type} in ${bug.scenario}`);
    });
  } else {
    console.log('\n✅ NO REGRESSIONS DETECTED - All tests passed');
  }
  
  console.log(`\n📋 Full report: ${reportPath}`);
  
  return report;
}

function generateRegressionRecommendations(results) {
  const recommendations = [];
  
  if (results.bugDetections.length > 0) {
    recommendations.push('Immediate investigation required - regressions detected');
    
    const functionalRegressions = results.bugDetections.filter(b => b.type === 'functional_regression');
    const performanceRegressions = results.bugDetections.filter(b => b.type === 'performance_regression');
    
    if (functionalRegressions.length > 0) {
      recommendations.push('Review recent code changes that may have reintroduced the game start bug');
      recommendations.push('Check WebSocket event handling and game state management');
    }
    
    if (performanceRegressions.length > 0) {
      recommendations.push('Profile game start performance and optimize bottlenecks');
      recommendations.push('Review recent changes to WebSocket handling or bot management');
    }
  } else {
    recommendations.push('Continue regular regression testing');
    recommendations.push('Monitor performance metrics for trends');
    recommendations.push('Update test scenarios as new features are added');
  }
  
  return recommendations;
}