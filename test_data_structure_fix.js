#!/usr/bin/env node

const puppeteer = require('puppeteer');

async function testDataStructureFix() {
  console.log('🔬 Testing Data Structure Mismatch Fix');
  
  let browser;
  try {
    browser = await puppeteer.launch({ headless: false, slowMo: 200 });
    const page = await browser.newPage();
    
    // Monitor console for JavaScript errors
    const errors = [];
    const phaseEvents = [];
    
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('TypeError') && text.includes('players.map')) {
        console.log('❌ CRITICAL: Data structure error found:', text);
        errors.push(text);
      } else if (text.includes('phase_change') || text.includes('PHASE_CHANGE')) {
        console.log('✅ Phase change event detected:', text);
        phaseEvents.push(text);
      }
    });
    
    const startTime = Date.now();
    
    // Step 1: Home page
    console.log('📍 Step 1: Loading home page');
    await page.goto('http://localhost:5050');
    await page.waitForSelector('input[placeholder*="name"]', { timeout: 10000 });
    
    // Step 2: Enter lobby
    console.log('📍 Step 2: Enter lobby');
    await page.type('input[placeholder*="name"]', 'TestPlayer');
    await page.click('button:contains("ENTER LOBBY")');
    await page.waitForFunction(() => window.location.pathname.includes('lobby'), { timeout: 10000 });
    
    // Step 3: Create room
    console.log('📍 Step 3: Create room');
    await page.click('button:contains("Create Room")');
    await page.waitForFunction(() => window.location.pathname.includes('room'), { timeout: 10000 });
    
    console.log('🏠 Room created, URL:', page.url());
    
    // Step 4: Start game with detailed monitoring
    console.log('📍 Step 4: Start game (monitoring for data structure issue)');
    const gameStartTime = Date.now();
    
    await page.click('button:contains("Start Game")');
    
    // Monitor for 10 seconds to see what happens
    let outcome = 'UNKNOWN';
    let transitionTime = null;
    
    for (let i = 0; i < 10; i++) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const currentUrl = page.url();
      console.log(`[${i+1}s] Current URL: ${currentUrl}`);
      
      if (currentUrl.includes('/game/')) {
        transitionTime = Date.now() - gameStartTime;
        outcome = 'SUCCESS_NAVIGATION';
        console.log(`✅ SUCCESS: Navigated to game page in ${transitionTime}ms`);
        break;
      }
      
      // Check if waiting modal is visible
      const waitingVisible = await page.evaluate(() => {
        const waitingText = document.querySelector('*:contains("Waiting for Game")');
        return waitingText ? true : false;
      });
      
      if (waitingVisible && i > 3) {
        outcome = 'STUCK_ON_WAITING';
        console.log('❌ STUCK: Still showing waiting page');
        break;
      }
    }
    
    const totalTime = Date.now() - startTime;
    
    // Results
    console.log('\n📊 DATA STRUCTURE FIX VALIDATION RESULTS');
    console.log('=========================================');
    console.log(`⏱️  Total Test Time: ${totalTime}ms`);
    console.log(`🎮 Final Outcome: ${outcome}`);
    if (transitionTime) {
      console.log(`⚡ Navigation Time: ${transitionTime}ms`);
    }
    console.log(`❌ JavaScript Errors: ${errors.length}`);
    console.log(`✅ Phase Change Events: ${phaseEvents.length}`);
    
    console.log('\n🧪 ERROR ANALYSIS');
    console.log('==================');
    if (errors.length === 0) {
      console.log('✅ NO DATA STRUCTURE ERRORS FOUND!');
      console.log('✅ Fix appears to be working correctly');
    } else {
      console.log('❌ Data structure errors still present:');
      errors.forEach(error => console.log(`   - ${error}`));
    }
    
    console.log('\n🎯 FINAL CONCLUSION');
    console.log('===================');
    if (errors.length === 0 && outcome === 'SUCCESS_NAVIGATION') {
      console.log('🎉 DATA STRUCTURE FIX: SUCCESS!');
      console.log('✅ Backend now sends correct array format');
      console.log('✅ Frontend processes without errors');
      console.log('✅ Game navigation works properly');
    } else if (errors.length > 0) {
      console.log('❌ DATA STRUCTURE FIX: FAILED');
      console.log('❌ Still has JavaScript errors');
    } else if (outcome === 'STUCK_ON_WAITING') {
      console.log('🤔 DATA STRUCTURE FIX: PARTIAL');
      console.log('✅ No JavaScript errors, but navigation still fails');
    } else {
      console.log('🤔 DATA STRUCTURE FIX: INCONCLUSIVE');
      console.log('⚠️  Need to investigate further');
    }
    
  } catch (error) {
    console.error('🚫 Test failed:', error.message);
  } finally {
    if (browser) {
      console.log('\n⏰ Keeping browser open for 30 seconds for manual inspection...');
      await new Promise(resolve => setTimeout(resolve, 30000));
      await browser.close();
    }
  }
}

if (require.main === module) {
  testDataStructureFix().catch(console.error);
}