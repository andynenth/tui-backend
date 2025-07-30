const { chromium } = require('playwright');

async function testCancelRedirectBug() {
  console.log('🐛 Testing Cancel Button Redirect Bug\n');
  console.log('Handling the "room no longer exists" error first, then testing cancel button\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor navigation
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      console.log(`🧭 Navigated to: ${frame.url()}`);
    }
  });

  // Monitor API responses
  page.on('response', response => {
    if (response.status() === 404) {
      response.text().then(text => {
        console.log(`❌ 404 Response: ${response.url()}`);
        console.log(`   Body: ${text}`);
      });
    }
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`❌ Console Error: ${msg.text()}`);
    }
  });

  try {
    // First attempt - will likely hit "room no longer exists"
    console.log('📍 First Attempt - Handling room error');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[type="text"]', 'TestPlayer1');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1500);
    
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    const roomCode1 = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/[A-Z]{4}/);
      return match ? match[0] : null;
    });
    console.log(`  Room created: ${roomCode1}`);
    
    await page.click('button:has-text("Start")');
    console.log('  Clicked Start Game');
    await page.waitForTimeout(3000);
    
    // Check if we got the error
    const pageText = await page.textContent('body');
    if (pageText.includes('room no longer exists')) {
      console.log('  ⚠️  Got "room no longer exists" error as expected');
      console.log('  Waiting for automatic redirect to start page...');
      
      // Wait for auto-redirect (up to 15 seconds)
      try {
        await page.waitForURL('http://localhost:5050/', { timeout: 15000 });
        console.log('  ✅ Auto-redirected to start page\n');
      } catch (e) {
        console.log('  ⏱️  Redirect taking longer than expected...');
      }
    }
    
    // Second attempt - should work properly
    console.log('📍 Second Attempt - Testing Cancel Button');
    
    // Make sure we're on the start page
    if (page.url() !== 'http://localhost:5050/') {
      await page.goto('http://localhost:5050/');
      await page.waitForLoadState('networkidle');
    }
    
    // Enter lobby again
    await page.fill('input[type="text"]', 'TestPlayer2');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1500);
    console.log('  ✓ Entered lobby');
    
    // Create new room
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    const roomCode2 = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/[A-Z]{4}/);
      return match ? match[0] : null;
    });
    console.log(`  ✓ New room created: ${roomCode2}`);
    
    // Start game
    await page.click('button:has-text("Start")');
    console.log('  ✓ Clicked Start Game');
    await page.waitForTimeout(3000);
    
    // Now we should be on the waiting page
    const currentUrl = page.url();
    const currentText = await page.textContent('body');
    
    console.log(`\n📊 Current State:`);
    console.log(`  URL: ${currentUrl}`);
    
    if (currentText.includes('Waiting') || currentText.includes('waiting')) {
      console.log('  ✓ On waiting page (without error this time)');
      
      // Look for Cancel button
      const cancelButton = await page.$('button:has-text("Cancel")');
      
      if (cancelButton) {
        console.log('\n📍 Testing Cancel Button');
        
        // Take screenshot before
        await page.screenshot({ path: 'cancel-before.png' });
        
        // Click cancel
        await cancelButton.click();
        console.log('  ✓ Clicked Cancel button');
        
        // Wait for result
        await page.waitForTimeout(3000);
        
        // Check where we ended up
        const afterUrl = page.url();
        const afterText = await page.textContent('body');
        
        console.log(`\n📊 After Cancel:`);
        console.log(`  URL: ${afterUrl}`);
        
        if (afterText.includes('"detail":"Not Found"') || afterText.includes('{"detail":"Not Found"}')) {
          console.log('  ❌ BUG CONFIRMED: Got {"detail":"Not Found"} error');
          console.log('  Expected: Should redirect to lobby');
          await page.screenshot({ path: 'cancel-404-error.png' });
          
          // Try to identify the problematic route
          if (afterUrl.includes('/api/') || afterUrl !== currentUrl) {
            console.log(`  Problematic URL: ${afterUrl}`);
          }
          
        } else if (afterUrl.includes('/lobby') || afterText.includes('Create Room') || afterText.includes('Join Room')) {
          console.log('  ✅ Successfully redirected to lobby!');
          console.log('  Bug may be fixed or intermittent');
        } else {
          console.log('  🤔 Unexpected result');
          console.log(`  Content preview: ${afterText.substring(0, 200)}`);
        }
        
        await page.screenshot({ path: 'cancel-after.png' });
        
      } else {
        console.log('  ❌ Cancel button not found');
        
        // List all buttons
        const buttons = await page.$$eval('button', btns => 
          btns.map(b => b.textContent.trim())
        );
        console.log('  Available buttons:', buttons);
      }
      
    } else if (currentText.includes('room no longer exists')) {
      console.log('  ⚠️  Still getting room error on second attempt');
      console.log('  This suggests a persistent server issue');
    } else {
      console.log('  ❌ Not on waiting page');
      console.log(`  Page content: ${currentText.substring(0, 200)}`);
    }
    
    console.log('\n📊 Test Summary:');
    console.log('  1. First attempt triggers "room no longer exists" error');
    console.log('  2. After auto-redirect, second attempt should work');
    console.log('  3. Cancel button click results in {"detail":"Not Found"}');
    console.log('  4. This indicates a missing or misconfigured route');
    
    console.log('\n🔧 Next Steps:');
    console.log('  1. Check frontend code for cancel button handler');
    console.log('  2. Verify the API endpoint it\'s trying to call');
    console.log('  3. Ensure backend has the corresponding route');
    
    console.log('\n✅ Test complete. Browser remains open.');
    console.log('Screenshots: cancel-before.png, cancel-404-error.png, cancel-after.png');
    
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await page.screenshot({ path: 'test-error.png' });
  }
}

testCancelRedirectBug().catch(console.error);