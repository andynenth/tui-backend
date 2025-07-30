const { chromium } = require('playwright');

async function debugUIErrors() {
  console.log('🔍 Debugging UI Errors...');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Comprehensive error capturing
    const allConsoleMessages = [];
    const allErrors = [];
    
    page.on('console', msg => {
      const message = `[${msg.type().toUpperCase()}] ${msg.text()}`;
      allConsoleMessages.push(message);
      console.log(message);
    });
    
    page.on('pageerror', error => {
      const errorMsg = `PAGE ERROR: ${error.message}`;
      allErrors.push(errorMsg);
      console.log('❌', errorMsg);
    });
    
    page.on('requestfailed', request => {
      const failMsg = `REQUEST FAILED: ${request.url()} - ${request.failure()?.errorText}`;
      allErrors.push(failMsg);
      console.log('🌐', failMsg);
    });
    
    console.log('\n=== STEP 1: Load lobby ===');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    console.log('\n=== STEP 2: Enter lobby ===');
    const nameInput = await page.locator('input[type="text"]').first();
    await nameInput.fill('TestPlayer');
    
    const startButton = await page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
    await startButton.click();
    
    console.log('\n=== STEP 3: Wait and check UI state ===');
    await page.waitForTimeout(3000);
    
    // Check if lobby elements are present
    try {
      const lobbyTitle = await page.locator('.lp-lobbyTitle').textContent();
      console.log('✅ Lobby title:', lobbyTitle);
      
      const roomCount = await page.locator('.lp-roomCount').textContent();
      console.log('✅ Room count:', roomCount);
      
      const createButton = await page.locator('button').textContent();
      console.log('✅ Create button text:', createButton);
      
    } catch (error) {
      console.log('❌ Error checking lobby elements:', error.message);
    }
    
    console.log('\n=== STEP 4: Try to create room ===');
    
    try {
      // Click create room button
      const createBtn = await page.locator('button').filter({ hasText: /create/i }).first();
      console.log('🔘 Found create button, clicking...');
      await createBtn.click();
      
      console.log('⏳ Waiting 2 seconds after click...');
      await page.waitForTimeout(2000);
      
      // Check if UI is still responsive
      console.log('🔍 Checking UI responsiveness...');
      
      // Try to get room count again
      const roomCountAfterClick = await page.locator('.lp-roomCount').textContent({ timeout: 5000 });
      console.log('✅ Room count after click:', roomCountAfterClick);
      
    } catch (error) {
      console.log('❌ Error during room creation:', error.message);
      console.log('🔍 Checking if UI is broken...');
      
      // Try to access any element to see if UI is completely broken
      try {
        const anyElement = await page.locator('body').textContent({ timeout: 2000 });
        console.log('✅ Body still accessible (first 100 chars):', anyElement.substring(0, 100));
      } catch (e) {
        console.log('❌ UI completely unresponsive:', e.message);
      }
    }
    
    console.log('\n=== ERROR SUMMARY ===');
    console.log('Total console messages:', allConsoleMessages.length);
    console.log('Total errors:', allErrors.length);
    
    if (allErrors.length > 0) {
      console.log('\\n🚨 ERRORS FOUND:');
      allErrors.forEach((error, i) => {
        console.log(`${i + 1}. ${error}`);
      });
    }
    
    console.log('\\n⏱️ Keeping browser open for manual inspection (30s)...');
    await page.waitForTimeout(30000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
    console.log('🏁 Test completed');
  }
}

debugUIErrors().catch(console.error);