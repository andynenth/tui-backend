const { chromium } = require('playwright');

async function testCancelButtonBug() {
  console.log('🐛 Testing Cancel Button Bug on Waiting Page\n');
  console.log('Expected: Cancel should redirect to lobby');
  console.log('Actual Bug: Shows {"detail":"Not Found"}\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor network requests
  const apiCalls = [];
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      console.log(`📤 API Request: ${request.method()} ${request.url()}`);
      apiCalls.push({
        method: request.method(),
        url: request.url(),
        headers: request.headers()
      });
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      console.log(`📥 API Response: ${response.status()} ${response.url()}`);
      if (response.status() === 404) {
        response.text().then(text => {
          console.log(`   ❌ 404 Response body: ${text}`);
        });
      }
    }
  });

  // Monitor WebSocket
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connected');
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log(`📤 WS: ${data.type || data.action || 'unknown'}`);
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log(`📥 WS: ${data.type || data.action || 'unknown'}`);
      } catch (e) {}
    });
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`❌ Console Error: ${msg.text()}`);
    }
  });

  try {
    // Step 1: Enter Lobby
    console.log('📍 Step 1: Navigate and Enter Lobby');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1500);
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
    
    // Step 3: Start Game
    console.log('\n📍 Step 3: Start Game');
    const startButton = await page.$('button:has-text("Start")');
    if (startButton) {
      await startButton.click();
      console.log('  ✓ Clicked Start Game');
      
      // Wait for waiting page or error
      await page.waitForTimeout(3000);
      
      // Check current state
      const currentUrl = page.url();
      const pageText = await page.textContent('body');
      
      console.log(`\n📊 Current State:`);
      console.log(`  URL: ${currentUrl}`);
      
      if (pageText.includes('room no longer exists')) {
        console.log('  ⚠️  Got "room no longer exists" error');
        console.log('  Waiting for auto-redirect...');
        
        // Wait for timeout redirect
        await page.waitForURL('http://localhost:5050/', { timeout: 15000 });
        console.log('  ✓ Auto-redirected to start page');
        
        // Now test the actual bug scenario
        console.log('\n📍 Reproducing Cancel Button Bug:');
        console.log('  Creating new room to test cancel...');
        
        // Create new room
        await page.fill('input[type="text"]', 'TestPlayer2');
        await page.click('button:has-text("Enter Lobby")');
        await page.waitForTimeout(1500);
        await page.click('button:has-text("Create Room")');
        await page.waitForTimeout(2000);
      }
      
      // Look for waiting page elements
      const waitingText = pageText.includes('Waiting') || pageText.includes('waiting');
      const cancelButton = await page.$('button:has-text("Cancel")') || 
                          await page.$('button:has-text("Leave")') ||
                          await page.$('button:has-text("Exit")');
      
      if (waitingText) {
        console.log('  ✓ On waiting page');
        
        if (cancelButton) {
          console.log('\n📍 Step 4: Test Cancel Button');
          console.log('  Found cancel/leave button');
          
          // Clear API calls to focus on cancel action
          apiCalls.length = 0;
          
          // Take screenshot before cancel
          await page.screenshot({ path: 'before-cancel.png' });
          
          // Click cancel
          await cancelButton.click();
          console.log('  ✓ Clicked cancel button');
          
          // Wait for response
          await page.waitForTimeout(2000);
          
          // Check result
          const afterUrl = page.url();
          const afterText = await page.textContent('body');
          
          console.log(`\n📊 After Cancel:`);
          console.log(`  URL: ${afterUrl}`);
          
          if (afterText.includes('"detail":"Not Found"') || afterText.includes('{"detail":"Not Found"}')) {
            console.log('  ❌ BUG CONFIRMED: Got {"detail":"Not Found"} error');
            await page.screenshot({ path: 'not-found-error.png' });
            
            // Analyze the failed API call
            console.log('\n🔍 Analyzing Failed Request:');
            const failedCall = apiCalls.find(call => call.url.includes('leave') || call.url.includes('cancel'));
            if (failedCall) {
              console.log(`  Method: ${failedCall.method}`);
              console.log(`  URL: ${failedCall.url}`);
              console.log(`  This endpoint returns 404`);
            }
            
          } else if (afterUrl === 'http://localhost:5050/' || afterText.includes('Enter Lobby')) {
            console.log('  ✅ Successfully redirected to lobby');
          } else {
            console.log('  🤔 Unexpected state after cancel');
            console.log(`  Page content: ${afterText.substring(0, 200)}`);
          }
          
          // Take final screenshot
          await page.screenshot({ path: 'after-cancel.png' });
          
        } else {
          console.log('  ❌ No cancel button found on waiting page');
          
          // List all buttons
          const buttons = await page.$$eval('button', btns => 
            btns.map(b => b.textContent.trim())
          );
          console.log('  Available buttons:', buttons);
        }
      } else {
        console.log('  ❌ Not on waiting page');
        console.log(`  Page content: ${pageText.substring(0, 200)}`);
      }
      
    } else {
      console.log('  ❌ No start button found');
    }
    
    console.log('\n📊 Summary:');
    console.log('  The bug occurs when clicking cancel on the waiting page.');
    console.log('  Instead of redirecting to lobby, it shows {"detail":"Not Found"}');
    console.log('  This suggests the cancel/leave endpoint is missing or misconfigured.');
    
    console.log('\n🔧 Likely fixes needed:');
    console.log('  1. Check backend API routes for leave/cancel endpoint');
    console.log('  2. Ensure frontend is calling the correct endpoint');
    console.log('  3. Handle 404 errors gracefully on frontend');
    
    console.log('\n✅ Test complete. Browser remains open.');
    console.log('Screenshots saved: before-cancel.png, after-cancel.png');
    
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await page.screenshot({ path: 'test-error.png' });
  }
}

testCancelButtonBug().catch(console.error);