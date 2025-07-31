/**
 * 🕵️ **Waiting Page Detection Test**
 * 
 * PlaywrightValidator Agent - Task 2: Create Waiting Page Detection Test
 * 
 * MISSION: Determine exactly what the user sees during game start transition
 * 
 * Success Criteria:
 * - Can detect and time waiting page visibility
 * - Timestamped screenshots showing waiting page duration
 * - Implement precise timing detection for waiting page visibility
 * - Test complete flow: Enter Lobby >> Create Room >> Start Game
 * 
 * Time Estimate: 45 minutes
 * Expected Outcome: Timestamped evidence of waiting page behavior
 */

const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');

// Test Configuration
const CONFIG = {
  BASE_URL: 'http://localhost:5050',
  SCREENSHOT_DIR: './test-results/waiting-page-detection',
  MONITORING_INTERVAL: 50, // Check every 50ms for precise timing
  MAX_MONITORING_TIME: 30000, // Monitor for maximum 30 seconds
  TIMESTAMP_FORMAT: 'YYYY-MM-DD_HH-mm-ss-SSS',
  PLAYER_NAME: 'WaitingPageTester'
};

// Global state for monitoring
let monitoringSession = {
  startTime: null,
  waitingPageDetected: false,
  waitingPageStartTime: null,
  waitingPageEndTime: null,
  waitingPageDuration: 0,
  screenshots: [],
  urlTransitions: [],
  wsEvents: [],
  domStateChanges: [],
  visibilityTimeline: []
};

async function testWaitingPageDetection() {
  console.log('🕵️ === WAITING PAGE DETECTION TEST ===');
  console.log('Mission: Detect and time waiting page visibility during game start');
  console.log('Flow: Enter Lobby >> Create Room >> Start Game >> Monitor Waiting Page\n');

  // Ensure screenshot directory exists
  await fs.mkdir(CONFIG.SCREENSHOT_DIR, { recursive: true });
  console.log(`📁 Screenshots will be saved to: ${CONFIG.SCREENSHOT_DIR}`);

  const browser = await chromium.launch({
    headless: false,
    devtools: true,
    args: [
      '--enable-logging',
      '--v=1',
      '--disable-web-security',
      '--no-sandbox'
    ]
  });

  const page = await browser.newPage();

  // Initialize monitoring session
  monitoringSession.startTime = Date.now();
  const sessionId = `waiting-detection-${monitoringSession.startTime}`;
  
  console.log(`🔬 Monitoring Session ID: ${sessionId}`);

  try {
    // Set up comprehensive monitoring
    await setupWaitingPageMonitoring(page, sessionId);

    // Execute the test flow
    await executeGameStartFlow(page, sessionId);

    // Generate comprehensive report
    const report = await generateDetectionReport(sessionId);
    console.log('\n📊 === WAITING PAGE DETECTION RESULTS ===');
    console.log(report.summary);

    console.log('\n✅ Waiting page detection test completed.');
    console.log('🔍 Browser remains open for manual inspection.');
    
    // Keep browser open for inspection
    await new Promise(() => {});

  } catch (error) {
    console.error('💥 Test execution error:', error);
    await captureErrorState(page, sessionId, error);
    throw error;
  }
}

async function setupWaitingPageMonitoring(page, sessionId) {
  console.log('🔧 Setting up comprehensive waiting page monitoring...');

  // 1. WebSocket Event Monitoring
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connection detected');
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        const timestamp = Date.now();
        
        monitoringSession.wsEvents.push({
          timestamp,
          relativeTime: timestamp - monitoringSession.startTime,
          direction: 'sent',
          event: eventType,
          data: data
        });
        
        console.log(`📤 [${timestamp - monitoringSession.startTime}ms] WS Send: ${eventType}`);
      } catch (e) {
        // Ignore parsing errors
      }
    });

    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        const timestamp = Date.now();
        
        monitoringSession.wsEvents.push({
          timestamp,
          relativeTime: timestamp - monitoringSession.startTime,
          direction: 'received',
          event: eventType,
          data: data
        });
        
        console.log(`📥 [${timestamp - monitoringSession.startTime}ms] WS Receive: ${eventType}`);
        
        // Special handling for game_started event
        if (eventType === 'game_started') {
          console.log('🎯 GAME_STARTED EVENT DETECTED!');
          monitoringSession.gameStartedEventTime = timestamp;
        }
      } catch (e) {
        // Ignore parsing errors
      }
    });
  });

  // 2. URL Navigation Monitoring
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      const timestamp = Date.now();
      const url = frame.url();
      const path = new URL(url).pathname;
      
      monitoringSession.urlTransitions.push({
        timestamp,
        relativeTime: timestamp - monitoringSession.startTime,
        url: url,
        path: path
      });
      
      console.log(`🧭 [${timestamp - monitoringSession.startTime}ms] Navigation: ${path}`);
    }
  });

  // 3. Console Error Monitoring
  page.on('console', msg => {
    const timestamp = Date.now();
    
    if (msg.type() === 'error') {
      console.log(`❌ [${timestamp - monitoringSession.startTime}ms] Console Error: ${msg.text()}`);
    }
    
    // Log phase_change events specifically
    if (msg.text().includes('phase_change') || msg.text().includes('PhaseChanged')) {
      console.log(`🔄 [${timestamp - monitoringSession.startTime}ms] Phase Change: ${msg.text()}`);
    }
  });

  // 4. Inject monitoring script into page
  await page.addInitScript(() => {
    window.waitingPageMonitor = {
      startTime: Date.now(),
      observations: [],
      currentState: 'unknown',
      waitingPageVisible: false,
      gamePageVisible: false
    };

    // Monitor DOM mutations for waiting page detection
    const observer = new MutationObserver((mutations) => {
      const timestamp = Date.now();
      
      mutations.forEach((mutation) => {
        // Check for waiting page indicators
        const waitingIndicators = [
          'waiting for game to start',
          'waiting for players',
          'loading game',
          'preparing game',
          'initializing'
        ];
        
        const gameIndicators = [
          'declaration phase',
          'choose your play',
          'game started',
          'your turn',
          'round'
        ];
        
        const currentBody = document.body.innerText.toLowerCase();
        
        const hasWaitingIndicator = waitingIndicators.some(indicator => 
          currentBody.includes(indicator)
        );
        
        const hasGameIndicator = gameIndicators.some(indicator => 
          currentBody.includes(indicator)
        );
        
        if (hasWaitingIndicator && !window.waitingPageMonitor.waitingPageVisible) {
          window.waitingPageMonitor.waitingPageVisible = true;
          window.waitingPageMonitor.waitingPageStartTime = timestamp;
          window.waitingPageMonitor.currentState = 'waiting';
          
          window.waitingPageMonitor.observations.push({
            timestamp,
            relativeTime: timestamp - window.waitingPageMonitor.startTime,
            event: 'waiting_page_detected',
            url: window.location.href,
            bodyText: currentBody.substring(0, 200)
          });
          
          console.log(`🔍 WAITING PAGE DETECTED at ${timestamp - window.waitingPageMonitor.startTime}ms`);
        }
        
        if (hasGameIndicator && window.waitingPageMonitor.waitingPageVisible && !window.waitingPageMonitor.gamePageVisible) {
          window.waitingPageMonitor.gamePageVisible = true;
          window.waitingPageMonitor.waitingPageEndTime = timestamp;
          window.waitingPageMonitor.currentState = 'game';
          
          const duration = timestamp - window.waitingPageMonitor.waitingPageStartTime;
          
          window.waitingPageMonitor.observations.push({
            timestamp,
            relativeTime: timestamp - window.waitingPageMonitor.startTime,
            event: 'game_page_detected',
            url: window.location.href,
            waitingPageDuration: duration,
            bodyText: currentBody.substring(0, 200)
          });
          
          console.log(`🎮 GAME PAGE DETECTED at ${timestamp - window.waitingPageMonitor.startTime}ms`);
          console.log(`⏱️  WAITING PAGE DURATION: ${duration}ms`);
        }
      });
    });
    
    // Start observing when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        observer.observe(document.body, {
          childList: true,
          subtree: true,
          characterData: true
        });
      });
    } else {
      observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
      });
    }
  });

  console.log('✅ Comprehensive monitoring setup complete');
}

async function executeGameStartFlow(page, sessionId) {
  console.log('\n🎮 === EXECUTING GAME START FLOW ===');

  // Step 1: Navigate to application
  console.log('📍 Step 1: Navigating to application...');
  await page.goto(CONFIG.BASE_URL);
  await page.waitForLoadState('networkidle');
  
  await captureTimestampedScreenshot(page, sessionId, '01-app-loaded');
  console.log('  ✅ Application loaded');

  // Step 2: Enter Lobby
  console.log('📍 Step 2: Entering lobby...');
  await page.fill('input[type="text"]', CONFIG.PLAYER_NAME);
  await page.click('button:has-text("Enter Lobby")');
  await page.waitForTimeout(2000);
  
  await captureTimestampedScreenshot(page, sessionId, '02-lobby-entered');
  console.log('  ✅ Entered lobby');

  // Step 3: Create Room
  console.log('📍 Step 3: Creating room...');
  await page.click('button:has-text("Create Room")');
  await page.waitForTimeout(2000);
  
  const roomCode = await page.$eval('body', body => {
    const text = body.innerText;
    const match = text.match(/[A-Z]{4}/);
    return match ? match[0] : null;
  });
  
  await captureTimestampedScreenshot(page, sessionId, '03-room-created');
  console.log(`  ✅ Room created: ${roomCode}`);

  // Step 4: Add bots (trigger full room scenario)
  console.log('📍 Step 4: Adding bots to fill room...');
  
  // Add 3 bots for 4-player game
  for (let i = 0; i < 3; i++) {
    const addBotButton = await page.$('button:has-text("Add Bot")');
    if (addBotButton) {
      await addBotButton.click();
      await page.waitForTimeout(1000);
      console.log(`  🤖 Bot ${i + 1} added`);
    }
  }
  
  await captureTimestampedScreenshot(page, sessionId, '04-bots-added');
  console.log('  ✅ All bots added, room ready to start');

  // Step 5: Start Game with Intensive Monitoring
  console.log('📍 Step 5: Starting game with intensive monitoring...');
  
  const startButton = await page.$('button:has-text("Start")');
  if (!startButton) {
    throw new Error('Start button not found');
  }

  const isEnabled = await startButton.isEnabled();
  if (!isEnabled) {
    throw new Error('Start button is not enabled');
  }

  console.log('🚨 CLICKING START BUTTON - Beginning intensive monitoring...');
  
  // Capture pre-start state
  await captureTimestampedScreenshot(page, sessionId, '05-pre-start');
  
  // Start monitoring loop BEFORE clicking start
  const monitoringPromise = startIntensiveMonitoring(page, sessionId);
  
  // Click start button
  const startClickTime = Date.now();
  monitoringSession.startClickTime = startClickTime;
  
  await startButton.click();
  console.log(`⏱️  START CLICKED at ${startClickTime - monitoringSession.startTime}ms`);
  
  // Wait for monitoring to complete
  await monitoringPromise;
  
  console.log('✅ Game start flow and monitoring completed');
}

async function startIntensiveMonitoring(page, sessionId) {
  console.log('🔬 Starting intensive waiting page monitoring...');
  
  const monitoringEndTime = Date.now() + CONFIG.MAX_MONITORING_TIME;
  let intervalCount = 0;
  
  while (Date.now() < monitoringEndTime) {
    const currentTime = Date.now();
    const relativeTime = currentTime - monitoringSession.startTime;
    const postClickTime = currentTime - monitoringSession.startClickTime;
    
    intervalCount++;
    
    // Capture page state
    const currentUrl = page.url();
    const currentPath = new URL(currentUrl).pathname;
    
    // Get DOM monitoring data
    const domData = await page.evaluate(() => {
      return {
        observations: window.waitingPageMonitor ? window.waitingPageMonitor.observations : [],
        currentState: window.waitingPageMonitor ? window.waitingPageMonitor.currentState : 'unknown',
        waitingPageVisible: window.waitingPageMonitor ? window.waitingPageMonitor.waitingPageVisible : false,
        gamePageVisible: window.waitingPageMonitor ? window.waitingPageMonitor.gamePageVisible : false,
        bodyText: document.body.innerText.toLowerCase().substring(0, 300)
      };
    });
    
    // Check for waiting page indicators in current content
    const waitingIndicators = [
      'waiting for game to start',
      'waiting for players',
      'loading game',
      'preparing game',
      'initializing'
    ];
    
    const gameIndicators = [
      'declaration phase',
      'choose your play',
      'game started',
      'your turn',
      'round'
    ];
    
    const hasWaitingText = waitingIndicators.some(indicator => 
      domData.bodyText.includes(indicator)
    );
    
    const hasGameText = gameIndicators.some(indicator => 
      domData.bodyText.includes(indicator)
    );
    
    // Record visibility state
    const visibilityState = {
      timestamp: currentTime,
      relativeTime: relativeTime,
      postClickTime: postClickTime,
      interval: intervalCount,
      url: currentUrl,
      path: currentPath,
      hasWaitingText: hasWaitingText,
      hasGameText: hasGameText,
      waitingPageVisible: domData.waitingPageVisible,
      gamePageVisible: domData.gamePageVisible,
      currentState: domData.currentState
    };
    
    monitoringSession.visibilityTimeline.push(visibilityState);
    
    // Log significant state changes
    if (hasWaitingText && !monitoringSession.waitingPageDetected) {
      monitoringSession.waitingPageDetected = true;
      monitoringSession.waitingPageStartTime = currentTime;
      
      console.log(`🔍 WAITING PAGE DETECTED at +${postClickTime}ms after start click`);
      await captureTimestampedScreenshot(page, sessionId, `waiting-detected-${postClickTime}ms`);
    }
    
    if (hasGameText && monitoringSession.waitingPageDetected && !monitoringSession.waitingPageEndTime) {
      monitoringSession.waitingPageEndTime = currentTime;
      monitoringSession.waitingPageDuration = monitoringSession.waitingPageEndTime - monitoringSession.waitingPageStartTime;
      
      console.log(`🎮 GAME PAGE DETECTED at +${postClickTime}ms after start click`);
      console.log(`⏱️  WAITING PAGE VISIBLE FOR: ${monitoringSession.waitingPageDuration}ms`);
      await captureTimestampedScreenshot(page, sessionId, `game-detected-${postClickTime}ms`);
    }
    
    // Take periodic screenshots during critical periods
    if (postClickTime <= 5000 && intervalCount % 10 === 0) { // Every 500ms for first 5 seconds
      await captureTimestampedScreenshot(page, sessionId, `monitor-${postClickTime}ms`);
    }
    
    // Log progress every second
    if (intervalCount % 20 === 0) { // Every 1000ms
      console.log(`📊 [+${postClickTime}ms] State: ${domData.currentState}, Wait: ${hasWaitingText}, Game: ${hasGameText}, URL: ${currentPath}`);
    }
    
    // Break early if we've detected the game page
    if (hasGameText && monitoringSession.waitingPageEndTime) {
      console.log('✅ Game transition detected, ending monitoring early');
      break;
    }
    
    // Wait for next interval
    await page.waitForTimeout(CONFIG.MONITORING_INTERVAL);
  }
  
  console.log('🏁 Intensive monitoring completed');
  
  // Capture final state
  await captureTimestampedScreenshot(page, sessionId, 'final-state');
}

async function captureTimestampedScreenshot(page, sessionId, stepName) {
  const timestamp = Date.now();
  const relativeTime = timestamp - monitoringSession.startTime;
  const filename = `${sessionId}-${stepName}-${relativeTime}ms.png`;
  const screenshotPath = path.join(CONFIG.SCREENSHOT_DIR, filename);
  
  try {
    await page.screenshot({ 
      path: screenshotPath,
      fullPage: true 
    });
    
    monitoringSession.screenshots.push({
      timestamp,
      relativeTime,
      stepName,
      filename,
      path: screenshotPath
    });
    
    console.log(`📸 [+${relativeTime}ms] Screenshot: ${filename}`);
  } catch (error) {
    console.error(`❌ Failed to capture screenshot ${stepName}:`, error.message);
  }
}

async function generateDetectionReport(sessionId) {
  const reportTimestamp = Date.now();
  const totalTestTime = reportTimestamp - monitoringSession.startTime;
  
  const report = {
    sessionId: sessionId,
    testDuration: totalTestTime,
    timestamp: new Date().toISOString(),
    
    waitingPageAnalysis: {
      detected: monitoringSession.waitingPageDetected,
      startTime: monitoringSession.waitingPageStartTime,
      endTime: monitoringSession.waitingPageEndTime,
      duration: monitoringSession.waitingPageDuration,
      visibleDuration: monitoringSession.waitingPageDuration || 0
    },
    
    transitionTiming: {
      startClickTime: monitoringSession.startClickTime,
      gameStartedEventTime: monitoringSession.gameStartedEventTime || null,
      totalTransitionTime: monitoringSession.waitingPageEndTime ? 
        (monitoringSession.waitingPageEndTime - monitoringSession.startClickTime) : null
    },
    
    statistics: {
      totalScreenshots: monitoringSession.screenshots.length,
      totalUrlTransitions: monitoringSession.urlTransitions.length,
      totalWsEvents: monitoringSession.wsEvents.length,
      totalVisibilityChecks: monitoringSession.visibilityTimeline.length
    },
    
    visibilityTimeline: monitoringSession.visibilityTimeline,
    websocketEvents: monitoringSession.wsEvents,
    urlTransitions: monitoringSession.urlTransitions,
    screenshots: monitoringSession.screenshots,
    
    summary: generateSummaryText()
  };
  
  // Save detailed report
  const reportPath = path.join(CONFIG.SCREENSHOT_DIR, `${sessionId}-detection-report.json`);
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
  
  console.log(`📋 Detection report saved: ${reportPath}`);
  return report;
}

function generateSummaryText() {
  const summary = [];
  
  summary.push('🕵️ WAITING PAGE DETECTION RESULTS:');
  summary.push('');
  
  if (monitoringSession.waitingPageDetected) {
    summary.push(`✅ Waiting page detected: YES`);
    summary.push(`⏱️  Waiting page duration: ${monitoringSession.waitingPageDuration}ms`);
    
    if (monitoringSession.waitingPageDuration < 500) {
      summary.push(`🟢 RESULT: Waiting page visible for <500ms - ACCEPTABLE`);
    } else if (monitoringSession.waitingPageDuration < 2000) {
      summary.push(`🟡 RESULT: Waiting page visible for ${monitoringSession.waitingPageDuration}ms - NOTICEABLE`);
    } else {
      summary.push(`🔴 RESULT: Waiting page visible for ${monitoringSession.waitingPageDuration}ms - PROBLEMATIC`);
    }
  } else {
    summary.push(`❌ Waiting page detected: NO`);
    summary.push(`🤔 RESULT: No waiting page detected - either bypassed or different UI`);
  }
  
  summary.push('');
  summary.push(`📊 Total monitoring time: ${Date.now() - monitoringSession.startTime}ms`);
  summary.push(`📸 Screenshots captured: ${monitoringSession.screenshots.length}`);
  summary.push(`📡 WebSocket events: ${monitoringSession.wsEvents.length}`);
  summary.push(`🧭 URL transitions: ${monitoringSession.urlTransitions.length}`);
  
  return summary.join('\n');
}

async function captureErrorState(page, sessionId, error) {
  console.log('💥 Capturing error state...');
  
  try {
    await captureTimestampedScreenshot(page, sessionId, 'ERROR-state');
    
    const errorReport = {
      sessionId: sessionId,
      timestamp: new Date().toISOString(),
      error: {
        message: error.message,
        stack: error.stack
      },
      finalState: {
        url: page.url(),
        visibilityTimeline: monitoringSession.visibilityTimeline,
        wsEvents: monitoringSession.wsEvents,
        screenshots: monitoringSession.screenshots
      }
    };
    
    const errorPath = path.join(CONFIG.SCREENSHOT_DIR, `${sessionId}-ERROR-report.json`);
    await fs.writeFile(errorPath, JSON.stringify(errorReport, null, 2));
    
    console.log(`💾 Error report saved: ${errorPath}`);
  } catch (e) {
    console.error('Failed to capture error state:', e.message);
  }
}

// Execute the test
testWaitingPageDetection().catch(console.error);