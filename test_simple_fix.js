#!/usr/bin/env node

const puppeteer = require('puppeteer');

async function testSimpleFix() {
  console.log('🔬 Testing Data Structure Fix');
  
  let browser;
  try {
    browser = await puppeteer.launch({ headless: false, slowMo: 300 });
    const page = await browser.newPage();
    
    // Monitor JavaScript errors
    const jsErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error' || (msg.text() && msg.text().includes('TypeError'))) {
        console.log('❌ JS Error:', msg.text());
        jsErrors.push(msg.text());
      }
      if (msg.text() && msg.text().includes('phase_change')) {
        console.log('✅ Phase event:', msg.text());
      }
    });
    
    // Step 1: Home
    console.log('📍 Step 1: Home page');
    await page.goto('http://localhost:5050');
    await page.waitForSelector('input');
    
    // Step 2: Enter name and go to lobby
    console.log('📍 Step 2: Enter lobby');
    await page.type('input', 'TestPlayer');
    
    // Find and click ENTER LOBBY button
    const buttons = await page.$$('button');
    for (const button of buttons) {
      const text = await page.evaluate(el => el.textContent, button);
      if (text.includes('ENTER LOBBY')) {
        await button.click();
        break;
      }
    }
    
    // Wait for lobby page
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log('Current URL after lobby:', page.url());
    
    // Step 3: Create room
    console.log('📍 Step 3: Create room');
    const allButtons = await page.$$('button');
    for (const button of allButtons) {
      const text = await page.evaluate(el => el.textContent, button);
      if (text.includes('Create Room')) {
        await button.click();
        break;
      }
    }
    
    // Wait for room page
    await new Promise(resolve => setTimeout(resolve, 2000));
    console.log('Current URL after room:', page.url());
    
    // Step 4: Start game
    console.log('📍 Step 4: Start game');
    const startTime = Date.now();
    
    const gameButtons = await page.$$('button');
    for (const button of gameButtons) {
      const text = await page.evaluate(el => el.textContent, button);
      if (text.includes('Start Game')) {
        await button.click();
        break;
      }
    }
    
    // Monitor for 8 seconds
    let finalUrl = '';
    let hasWaitingPage = false;
    
    for (let i = 0; i < 8; i++) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      finalUrl = page.url();
      
      // Check for waiting modal
      const waitingElements = await page.$$eval('*', elements => 
        elements.some(el => el.textContent && el.textContent.includes('Waiting for Game'))
      );
      
      if (waitingElements) {
        hasWaitingPage = true;
        console.log(`[${i+1}s] ⏳ Waiting page visible`);
      } else {
        console.log(`[${i+1}s] 📍 URL: ${finalUrl}`);
      }
      
      if (finalUrl.includes('/game/')) {
        const elapsedTime = Date.now() - startTime;
        console.log(`✅ SUCCESS: Reached game page in ${elapsedTime}ms`);
        break;
      }
    }
    
    const totalElapsed = Date.now() - startTime;
    
    // Results
    console.log('\n📊 TEST RESULTS');
    console.log('===============');
    console.log(`⏱️  Time elapsed: ${totalElapsed}ms`);
    console.log(`🎮 Final URL: ${finalUrl}`);
    console.log(`⏳ Waiting page seen: ${hasWaitingPage ? 'YES' : 'NO'}`);
    console.log(`❌ JavaScript errors: ${jsErrors.length}`);
    
    if (jsErrors.length > 0) {
      jsErrors.forEach(err => console.log(`   - ${err}`));
    }
    
    console.log('\n🎯 CONCLUSION');
    console.log('=============');
    if (finalUrl.includes('/game/') && jsErrors.length === 0) {
      console.log('✅ DATA STRUCTURE FIX: SUCCESS!');
      console.log('✅ No JavaScript errors');
      console.log('✅ Game page reached successfully');
    } else if (jsErrors.length > 0) {
      console.log('❌ DATA STRUCTURE FIX: FAILED');
      console.log('❌ JavaScript errors still present');
    } else {
      console.log('🤔 DATA STRUCTURE FIX: INCONCLUSIVE');
      console.log('⚠️  Navigation failed for other reasons');
    }
    
    // Keep browser open for inspection
    console.log('\nBrowser staying open for manual inspection...');
    await new Promise(resolve => setTimeout(resolve, 30000));
    
  } catch (error) {
    console.error('🚫 Test error:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

testSimpleFix().catch(console.error);