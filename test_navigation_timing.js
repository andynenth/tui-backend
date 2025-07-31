const { chromium } = require('playwright');

async function navigationTimingAnalysis() {
  console.log('🕐 Navigation Timing Analysis for Waiting Page Investigation\n');
  console.log('Objective: Measure precise transition timing from room → waiting → game');
  console.log('Success Criteria: Millisecond-level timing logs for each phase\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();

  // Timing data structure
  const timingData = {
    startTime: null,
    roomCreated: null,
    startGameClicked: null,
    waitingPageSeen: null,
    gamePageReached: null,
    events: [],
    navigationSteps: []
  };

  // Monitor navigation with precise timing
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      const timestamp = Date.now();
      const url = frame.url();
      const path = new URL(url).pathname;
      
      const navigationEvent = {
        timestamp,
        path,
        relativeTime: timingData.startTime ? timestamp - timingData.startTime : 0
      };
      
      timingData.navigationSteps.push(navigationEvent);
      console.log(`🧭 Navigation [+${navigationEvent.relativeTime}ms]: ${path}`);
      
      // Track specific phases
      if (path.includes('/room/')) {
        timingData.roomCreated = timestamp;
      } else if (path.includes('/game/')) {
        timingData.gamePageReached = timestamp;
      }
    }
  });

  // Monitor WebSocket events with timing
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connected');
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        const timestamp = Date.now();
        const relativeTime = timingData.startTime ? timestamp - timingData.startTime : 0;
        
        timingData.events.push({
          direction: 'sent',
          event: eventType,
          timestamp,
          relativeTime,
          data
        });
        
        console.log(`📤 WS Send [+${relativeTime}ms]: ${eventType}`);
        
        if (eventType === 'start_game') {
          timingData.startGameClicked = timestamp;
        }
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        const timestamp = Date.now();
        const relativeTime = timingData.startTime ? timestamp - timingData.startTime : 0;
        
        timingData.events.push({
          direction: 'received',
          event: eventType,
          timestamp,
          relativeTime,
          data
        });
        
        console.log(`📥 WS Receive [+${relativeTime}ms]: ${eventType}`);
      } catch (e) {}
    });
  });

  // Monitor page content changes for waiting page detection
  let waitingPageCheckInterval;
  
  function startWaitingPageMonitoring() {
    waitingPageCheckInterval = setInterval(async () => {
      try {
        const pageText = await page.textContent('body');
        const timestamp = Date.now();
        const relativeTime = timingData.startTime ? timestamp - timingData.startTime : 0;
        
        if (pageText.includes('Waiting for game to start') || pageText.includes('waiting')) {
          if (!timingData.waitingPageSeen) {
            timingData.waitingPageSeen = timestamp;
            console.log(`⏳ Waiting Page Detected [+${relativeTime}ms]`);
          }
        }
      } catch (e) {
        // Page might be navigating, ignore errors
      }
    }, 50); // Check every 50ms for high precision
  }

  function stopWaitingPageMonitoring() {
    if (waitingPageCheckInterval) {
      clearInterval(waitingPageCheckInterval);
    }
  }

  try {
    timingData.startTime = Date.now();
    console.log('⏱️ Starting timing analysis...\n');

    // Step 1: Enter Lobby
    console.log('📍 Step 1: Enter Lobby');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[type="text"]', 'TimingTestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(2000);
    console.log('  ✓ Entered lobby');
    
    // Step 2: Create Room
    console.log('\n📍 Step 2: Create Room');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    const roomCode = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/[A-Z]{4}/);
      return match ? match[0] : null;
    });
    console.log(`  ✓ Room created: ${roomCode}`);
    
    // Step 3: Start Game with Monitoring
    console.log('\n📍 Step 3: Start Game with Timing Monitoring');
    const startButton = await page.$('button:has-text("Start")');
    
    if (startButton) {
      // Start monitoring for waiting page
      startWaitingPageMonitoring();
      
      const preClickTime = Date.now();
      await startButton.click();
      const postClickTime = Date.now();
      
      console.log(`  ✓ Start Game clicked [Button response: ${postClickTime - preClickTime}ms]`);
      
      // Monitor for 10 seconds with detailed timing
      console.log('\n🕐 Monitoring transition for 10 seconds...');
      
      for (let i = 0; i < 100; i++) { // 10 seconds, check every 100ms
        await page.waitForTimeout(100);
        
        const currentTime = Date.now();
        const elapsedSinceClick = currentTime - (timingData.startGameClicked || preClickTime);
        const pageText = await page.textContent('body');
        const currentUrl = page.url();
        
        // Check for game page
        if (currentUrl.includes('/game/') && !timingData.gamePageReached) {
          timingData.gamePageReached = currentTime;
          console.log(`🎮 Game Page Reached [+${elapsedSinceClick}ms after click]`);
          break;
        }
        
        // Check for specific states every second
        if (i % 10 === 0) { // Every 1 second
          const secondsElapsed = Math.floor(elapsedSinceClick / 1000);
          
          if (pageText.includes('Declaration') || pageText.includes('Choose')) {
            console.log(`  [${secondsElapsed}s] ✅ In game (Declaration phase)`);
          } else if (pageText.includes('Waiting') || pageText.includes('waiting')) {
            console.log(`  [${secondsElapsed}s] ⏳ On waiting page`);
          } else if (pageText.includes('room no longer exists')) {
            console.log(`  [${secondsElapsed}s] ❌ Room error`);
            break;
          } else {
            console.log(`  [${secondsElapsed}s] 🤔 State: ${currentUrl}`);
          }
        }
      }
      
      stopWaitingPageMonitoring();
    }

    // Generate comprehensive timing report
    console.log('\n📊 NAVIGATION TIMING ANALYSIS RESULTS\n');
    
    const totalTime = timingData.gamePageReached 
      ? timingData.gamePageReached - timingData.startTime
      : Date.now() - timingData.startTime;
    
    console.log('⏱️ TIMING SUMMARY:');
    console.log(`  Total flow time: ${totalTime}ms`);
    
    if (timingData.roomCreated) {
      console.log(`  Room creation: ${timingData.roomCreated - timingData.startTime}ms`);
    }
    
    if (timingData.startGameClicked) {
      console.log(`  Start game clicked: ${timingData.startGameClicked - timingData.startTime}ms`);
    }
    
    if (timingData.waitingPageSeen) {
      const waitingDuration = timingData.gamePageReached 
        ? timingData.gamePageReached - timingData.waitingPageSeen
        : Date.now() - timingData.waitingPageSeen;
      console.log(`  Waiting page first seen: ${timingData.waitingPageSeen - timingData.startTime}ms`);
      console.log(`  Waiting page duration: ${waitingDuration}ms`);
    }
    
    if (timingData.gamePageReached) {
      const transitionTime = timingData.gamePageReached - (timingData.startGameClicked || timingData.startTime);
      console.log(`  Game page reached: ${timingData.gamePageReached - timingData.startTime}ms`);
      console.log(`  Transition time (click → game): ${transitionTime}ms`);
    }

    console.log('\n🧭 NAVIGATION SEQUENCE:');
    timingData.navigationSteps.forEach((step, index) => {
      console.log(`  ${index + 1}. [+${step.relativeTime}ms] ${step.path}`);
    });

    console.log('\n📡 WEBSOCKET EVENT SEQUENCE:');
    const relevantEvents = timingData.events.filter(e => 
      ['start_game', 'game_started', 'phase_change'].includes(e.event)
    );
    
    relevantEvents.forEach((event, index) => {
      const direction = event.direction === 'sent' ? '📤' : '📥';
      console.log(`  ${index + 1}. [+${event.relativeTime}ms] ${direction} ${event.event}`);
    });

    // Analysis and conclusions
    console.log('\n🔍 ANALYSIS:');
    
    if (timingData.gamePageReached) {
      const transitionSpeed = timingData.gamePageReached - (timingData.startGameClicked || timingData.startTime);
      
      if (transitionSpeed < 500) {
        console.log(`  ✅ EXCELLENT: Fast transition (${transitionSpeed}ms)`);
        console.log('  The waiting page issue appears to be resolved');
      } else if (transitionSpeed < 2000) {
        console.log(`  ✅ GOOD: Reasonable transition (${transitionSpeed}ms)`);
        console.log('  Waiting page is brief, fix is working');
      } else {
        console.log(`  ⚠️ SLOW: Long transition (${transitionSpeed}ms)`);
        console.log('  Waiting page is visible for extended time');
      }
    } else {
      console.log('  ❌ ISSUE: Game page was not reached');
      console.log('  Waiting page issue may still exist');
    }

    if (timingData.waitingPageSeen && timingData.gamePageReached) {
      const waitingDuration = timingData.gamePageReached - timingData.waitingPageSeen;
      console.log(`  ⏳ Waiting page was visible for ${waitingDuration}ms`);
      
      if (waitingDuration < 200) {
        console.log('  ✅ PASS: Waiting page barely visible (< 200ms)');
      } else if (waitingDuration < 1000) {
        console.log('  ✅ ACCEPTABLE: Brief waiting page (< 1s)');
      } else {
        console.log('  ⚠️ CONCERNING: Extended waiting page (> 1s)');
      }
    }

    console.log('\n✅ Navigation timing analysis complete. Browser remains open for inspection.');
    
    // Save timing data to file
    const fs = require('fs');
    fs.writeFileSync(
      'navigation-timing-results.json',
      JSON.stringify(timingData, null, 2)
    );
    console.log('📁 Timing data saved to navigation-timing-results.json');
    
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Timing analysis error:', error.message);
    stopWaitingPageMonitoring();
  }
}

navigationTimingAnalysis().catch(console.error);