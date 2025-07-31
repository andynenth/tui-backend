#!/usr/bin/env node

/**
 * Validation test for the data structure mismatch fix
 * Tests: Player 1 >> Enter Lobby >> Create Room >> Start Game
 * Expected: Fast navigation to game page without getting stuck on waiting page
 */

const puppeteer = require('puppeteer');

async function testFixValidation() {
  console.log('🔬 Testing Data Structure Mismatch Fix');
  
  let browser;
  try {
    browser = await puppeteer.launch({ headless: false, slowMo: 100 });
    const page = await browser.newPage();
    
    // Monitor WebSocket events
    const wsEvents = [];
    page.on('response', response => {
      if (response.url().includes('websocket')) {
        console.log('📡 WebSocket activity detected');
      }
    });
    
    // Monitor console for errors
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('TypeError') || text.includes('players.map')) {
        console.log('❌ JavaScript Error:', text);
        wsEvents.push({ type: 'js_error', message: text, timestamp: Date.now() });
      } else if (text.includes('phase_change') || text.includes('PHASE_CHANGE')) {
        console.log('✅ Phase Change Event:', text);
        wsEvents.push({ type: 'phase_change', message: text, timestamp: Date.now() });
      }
    });
    
    const startTime = Date.now();
    
    // Step 1: Navigate to home
    console.log('📍 Step 1: Navigate to home page');
    await page.goto('http://localhost:5050');
    await page.waitForSelector('input[placeholder*="name"]', { timeout: 10000 });
    
    // Step 2: Enter name and go to lobby
    console.log('📍 Step 2: Enter lobby');
    await page.type('input[placeholder*="name"]', 'TestPlayer');
    // Click the Enter Lobby button
    const enterButton = await page.waitForSelector('button[type="submit"]');
    await enterButton.click();
    await page.waitForFunction(() => window.location.pathname.includes('lobby'), { timeout: 10000 });
    
    // Step 3: Create room
    console.log('📍 Step 3: Create room');
    const createButton = await page.waitForSelector('text="Create Room"');
    await createButton.click();
    await page.waitForFunction(() => window.location.pathname.includes('room'), { timeout: 10000 });
    
    const roomUrl = page.url();
    console.log('🏠 Room created:', roomUrl);
    
    // Step 4: Start game with timing monitoring
    console.log('📍 Step 4: Start game (monitoring for data structure fix)');
    const gameStartTime = Date.now();
    
    const startButton = await page.waitForSelector('text="Start Game"');
    await startButton.click();
    
    // Monitor for waiting page vs immediate navigation
    let waitingPageDetected = false;
    let gamePageReached = false;
    let finalResult = null;
    
    // Check for waiting page modal
    try {
      await page.waitForSelector('text="Waiting for Game"', { timeout: 1000 });
      waitingPageDetected = true;
      console.log('⏳ Waiting page detected');
      
      // Wait to see if it transitions or gets stuck
      try {
        await page.waitForFunction(() => window.location.pathname.includes('game'), { timeout: 5000 });
        gamePageReached = true;
        const transitionTime = Date.now() - gameStartTime;
        console.log(`✅ Transitioned to game page in ${transitionTime}ms`);
        finalResult = `SUCCESS: Quick transition (${transitionTime}ms)`;
      } catch (e) {
        console.log('❌ STUCK: Waiting page did not transition');
        finalResult = 'FAILED: Stuck on waiting page';
      }
    } catch (e) {
      // No waiting page detected - check if we went straight to game
      try {
        await page.waitForFunction(() => window.location.pathname.includes('game'), { timeout: 2000 });
        gamePageReached = true;
        const transitionTime = Date.now() - gameStartTime;
        console.log(`🚀 EXCELLENT: Direct navigation in ${transitionTime}ms`);
        finalResult = `EXCELLENT: Direct navigation (${transitionTime}ms)`;
      } catch (e2) {
        console.log('❌ FAILED: No transition detected');
        finalResult = 'FAILED: No navigation occurred';
      }
    }
    
    const totalTime = Date.now() - startTime;
    
    // Results Summary
    console.log('\n📊 FIX VALIDATION RESULTS');
    console.log('========================');
    console.log(`⏱️  Total Test Time: ${totalTime}ms`);
    console.log(`⏳ Waiting Page Detected: ${waitingPageDetected ? 'YES' : 'NO'}`);
    console.log(`🎮 Game Page Reached: ${gamePageReached ? 'YES' : 'NO'}`);
    console.log(`🔬 Final Result: ${finalResult}`);
    
    // JavaScript Error Analysis
    const jsErrors = wsEvents.filter(e => e.type === 'js_error');
    const phaseEvents = wsEvents.filter(e => e.type === 'phase_change');
    
    console.log('\n🧪 DATA STRUCTURE FIX ANALYSIS');
    console.log('==============================');
    console.log(`❌ JavaScript Errors: ${jsErrors.length}`);
    if (jsErrors.length > 0) {
      jsErrors.forEach(e => console.log(`   - ${e.message}`));
    }
    console.log(`✅ Phase Change Events: ${phaseEvents.length}`);
    if (phaseEvents.length > 0) {
      phaseEvents.forEach(e => console.log(`   - ${e.message}`));
    }
    
    console.log('\n🎯 CONCLUSION');
    console.log('=============');
    if (jsErrors.length === 0 && gamePageReached) {
      console.log('✅ DATA STRUCTURE FIX SUCCESSFUL!');
      console.log('✅ No more "TypeError: o.players.map is not a function"');
      console.log('✅ Game navigation works correctly');
    } else if (jsErrors.length > 0) {
      console.log('❌ Data structure issues still present');
      console.log('❌ Fix needs further refinement');
    } else {
      console.log('🤔 Navigation failed for unknown reasons');
    }
    
  } catch (error) {
    console.error('🚫 Test failed:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

if (require.main === module) {
  testFixValidation().catch(console.error);
}