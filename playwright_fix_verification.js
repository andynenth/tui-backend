#!/usr/bin/env node

/**
 * Playwright Verification Test for Data Structure Fix
 * 
 * Tests the complete flow: Player 1 >> Enter Lobby >> Create Room >> Start Game
 * Validates that the data structure fix resolves the waiting page issue
 */

const { chromium } = require('playwright');

async function verifyDataStructureFix() {
  console.log('🎭 Playwright: Verifying Data Structure Fix');
  console.log('===========================================');
  
  let browser;
  let context;
  let page;
  
  try {
    // Launch browser
    browser = await chromium.launch({ 
      headless: false, 
      slowMo: 300,
      devtools: true // Open DevTools to see console
    });
    
    context = await browser.newContext();
    page = await context.newPage();
    
    // Track JavaScript errors and console events
    const jsErrors = [];
    const phaseEvents = [];
    const navigationEvents = [];
    
    page.on('console', msg => {
      const text = msg.text();
      console.log(`🟡 Console: ${text}`);
      
      if (text.includes('TypeError') && text.includes('players.map')) {
        console.log('❌ CRITICAL ERROR DETECTED:', text);
        jsErrors.push(text);
      } else if (text.includes('phase_change') || text.includes('PHASE_CHANGE')) {
        console.log('✅ PHASE EVENT DETECTED:', text);
        phaseEvents.push(text);
      }
    });
    
    page.on('pageerror', error => {
      console.log('❌ PAGE ERROR:', error.message);
      jsErrors.push(error.message);
    });
    
    // Track navigation
    page.on('framenavigated', frame => {
      if (frame === page.mainFrame()) {
        const url = frame.url();
        console.log(`🧭 Navigation: ${url}`);
        navigationEvents.push({ url, timestamp: Date.now() });
      }
    });
    
    const testStartTime = Date.now();
    
    // Step 1: Load home page
    console.log('\n📍 STEP 1: Loading home page');
    await page.goto('http://localhost:5050');
    await page.waitForSelector('input[placeholder*="name"]', { timeout: 15000 });
    console.log('✅ Home page loaded successfully');
    
    // Step 2: Enter player name and go to lobby
    console.log('\n📍 STEP 2: Entering lobby');
    await page.fill('input[placeholder*="name"]', 'PlaywrightTester');
    
    // Click ENTER LOBBY button
    await page.locator('text=ENTER LOBBY').click();
    await page.waitForURL('**/lobby', { timeout: 10000 });
    console.log('✅ Successfully entered lobby');
    
    // Step 3: Create room
    console.log('\n📍 STEP 3: Creating room');
    await page.locator('text=Create Room').click();
    await page.waitForURL('**/room/**', { timeout: 10000 });
    
    const roomUrl = page.url();
    const roomId = roomUrl.match(/room\/([A-Z0-9]+)/)?.[1] || 'UNKNOWN';
    console.log(`✅ Room created successfully: ${roomId}`);
    
    // Step 4: Start game with detailed monitoring
    console.log('\n📍 STEP 4: Starting game (CRITICAL TEST)');
    console.log('🔍 Monitoring for data structure fix...');
    
    const gameStartTime = Date.now();
    
    // Click Start Game button
    await page.locator('text=Start Game').click();
    console.log('🎯 Start Game button clicked');
    
    // Monitor the transition for 10 seconds
    let waitingPageDetected = false;
    let gamePageReached = false;
    let transitionTime = null;
    let finalOutcome = 'UNKNOWN';
    
    for (let second = 1; second <= 10; second++) {
      await page.waitForTimeout(1000);
      
      const currentUrl = page.url();
      console.log(`[${second}s] 📍 Current URL: ${currentUrl}`);
      
      // Check for waiting page modal
      const waitingModal = await page.locator('text=Waiting for Game').isVisible().catch(() => false);
      if (waitingModal && !waitingPageDetected) {
        waitingPageDetected = true;
        console.log(`[${second}s] ⏳ WAITING PAGE DETECTED`);
      }
      
      // Check if we've navigated to game page
      if (currentUrl.includes('/game/')) {
        if (!gamePageReached) {
          gamePageReached = true;
          transitionTime = Date.now() - gameStartTime;
          console.log(`[${second}s] 🎮 GAME PAGE REACHED! (${transitionTime}ms)`);
          finalOutcome = 'SUCCESS';
          break;
        }
      }
      
      // If still showing waiting page after 5 seconds, likely stuck
      if (waitingModal && second >= 5) {
        finalOutcome = 'STUCK_ON_WAITING';
        console.log(`[${second}s] ❌ STILL STUCK ON WAITING PAGE`);
      }
    }
    
    const totalTestTime = Date.now() - testStartTime;
    
    // Take final screenshot for evidence
    await page.screenshot({ 
      path: 'playwright_fix_verification_final.png', 
      fullPage: true 
    });
    
    // RESULTS ANALYSIS
    console.log('\n📊 PLAYWRIGHT VERIFICATION RESULTS');
    console.log('=====================================');
    console.log(`⏱️  Total Test Time: ${totalTestTime}ms`);
    console.log(`🎯 Final Outcome: ${finalOutcome}`);
    console.log(`⏳ Waiting Page Detected: ${waitingPageDetected ? 'YES' : 'NO'}`);
    console.log(`🎮 Game Page Reached: ${gamePageReached ? 'YES' : 'NO'}`);
    if (transitionTime) {
      console.log(`⚡ Transition Time: ${transitionTime}ms`);
    }
    console.log(`❌ JavaScript Errors: ${jsErrors.length}`);
    console.log(`✅ Phase Change Events: ${phaseEvents.length}`);
    console.log(`🧭 Navigation Events: ${navigationEvents.length}`);
    
    // ERROR ANALYSIS
    console.log('\n🔍 ERROR ANALYSIS');
    console.log('==================');
    if (jsErrors.length === 0) {
      console.log('✅ NO JAVASCRIPT ERRORS DETECTED!');
      console.log('✅ Data structure fix appears to be working');
    } else {
      console.log('❌ JavaScript errors found:');
      jsErrors.forEach(error => console.log(`   - ${error}`));
    }
    
    // PHASE EVENT ANALYSIS
    console.log('\n🔄 PHASE EVENT ANALYSIS');
    console.log('========================');
    if (phaseEvents.length > 0) {
      console.log('✅ Phase change events detected:');
      phaseEvents.forEach(event => console.log(`   - ${event}`));
    } else {
      console.log('❌ No phase change events detected');
    }
    
    // FINAL VERDICT
    console.log('\n🎯 FINAL VERDICT');
    console.log('================');
    
    if (jsErrors.length === 0 && gamePageReached && transitionTime < 2000) {
      console.log('🎉 DATA STRUCTURE FIX: SUCCESS!');
      console.log('✅ No JavaScript errors');
      console.log('✅ Fast navigation to game page');
      console.log('✅ Waiting page issue resolved');
      console.log('🚀 Fix is working correctly!');
    } else if (jsErrors.length > 0) {
      console.log('❌ DATA STRUCTURE FIX: FAILED');
      console.log('❌ JavaScript errors still present');
      console.log('❌ Fix did not resolve the issue');
    } else if (!gamePageReached) {
      console.log('🤔 DATA STRUCTURE FIX: PARTIAL');
      console.log('✅ No JavaScript errors');
      console.log('❌ Navigation still failing');
      console.log('⚠️  May need additional fixes');
    } else if (transitionTime > 5000) {
      console.log('⚠️  DATA STRUCTURE FIX: SLOW');
      console.log('✅ Eventually works');
      console.log('⚠️  But transition is very slow');
    } else {
      console.log('🤔 DATA STRUCTURE FIX: INCONCLUSIVE');
      console.log('⚠️  Results are mixed, need investigation');
    }
    
    // Keep browser open for manual inspection
    console.log('\n⏰ Keeping browser open for 30 seconds for manual inspection...');
    console.log('📱 DevTools are open - check Console tab for detailed logs');
    await page.waitForTimeout(30000);
    
  } catch (error) {
    console.error('🚫 Playwright test failed:', error.message);
    console.error('Stack:', error.stack);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Run the verification
if (require.main === module) {
  verifyDataStructureFix().catch(console.error);
}

module.exports = { verifyDataStructureFix };