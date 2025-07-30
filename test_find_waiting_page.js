const { chromium } = require('playwright');

async function testFindWaitingPage() {
  console.log('🔍 Repeating Process Until We Find "Waiting for game to start..."\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor WebSocket events
  page.on('websocket', ws => {
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        console.log(`📤 WS Send: ${eventType}`);
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        const eventType = data.event || data.type || 'unknown';
        console.log(`📥 WS Receive: ${eventType}`);
        
        if (eventType === 'game_started') {
          console.log('🎯 GAME_STARTED EVENT RECEIVED!');
        }
      } catch (e) {}
    });
  });

  // Monitor navigation
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      const path = new URL(frame.url()).pathname;
      console.log(`🧭 Navigation: ${path}`);
    }
  });

  page.on('console', msg => {
    if (msg.type() === 'error' && !msg.text().includes('404')) {
      console.log(`❌ Console Error: ${msg.text()}`);
    }
  });

  async function attemptGameStart(attemptNumber) {
    console.log(`\n🔄 ATTEMPT ${attemptNumber}`);
    
    try {
      // Navigate to start if not already there
      if (page.url() !== 'http://localhost:5050/') {
        await page.goto('http://localhost:5050');
        await page.waitForLoadState('networkidle');
      }
      
      // Enter lobby
      await page.fill('input[type="text"]', `Player${attemptNumber}`);
      await page.click('button:has-text("Enter Lobby")');
      await page.waitForTimeout(1500);
      
      // Create room
      await page.click('button:has-text("Create Room")');
      await page.waitForTimeout(1500);
      
      const roomCode = await page.$eval('body', body => {
        const text = body.innerText;
        const match = text.match(/[A-Z]{4}/);
        return match ? match[0] : null;
      });
      console.log(`  Room: ${roomCode}`);
      
      // Start game
      const startButton = await page.$('button:has-text("Start")');
      if (startButton) {
        await startButton.click();
        console.log('  ✓ Clicked Start Game');
        
        // Wait for response
        await page.waitForTimeout(4000);
        
        // Check current state
        const pageText = await page.textContent('body');
        const currentUrl = page.url();
        
        // Check for different states
        if (pageText.includes('Waiting for game to start')) {
          console.log('  🎯 FOUND IT! "Waiting for game to start..." page');
          console.log(`  URL: ${currentUrl}`);
          
          // Take screenshot
          await page.screenshot({ path: `waiting-page-found-${attemptNumber}.png` });
          
          // Wait longer to see if it progresses
          console.log('  ⏳ Monitoring for 10 seconds to see if game progresses...');
          
          let progressDetected = false;
          for (let i = 0; i < 10; i++) {
            await page.waitForTimeout(1000);
            const newText = await page.textContent('body');
            
            if (newText.includes('Declaration') || newText.includes('Choose') || 
                newText.includes('declare') || !newText.includes('Waiting')) {
              console.log(`  ✅ Game progressed after ${i + 1} seconds!`);
              console.log('  Successfully moved beyond waiting page');
              progressDetected = true;
              break;
            }
            
            if (newText.includes('room no longer exists')) {
              console.log(`  ❌ Room error appeared after ${i + 1} seconds`);
              break;
            }
            
            console.log(`    ${i + 1}s: Still waiting...`);
          }
          
          if (!progressDetected) {
            console.log('  ❌ ISSUE CONFIRMED: Game stuck on waiting page for 10 seconds');
            console.log('  This is the core issue - game does not progress beyond waiting');
          }
          
          return 'found_waiting';
          
        } else if (pageText.includes('room no longer exists')) {
          console.log('  ⚠️ Room error (will try again)');
          
          // Wait for auto-redirect
          try {
            await page.waitForURL('http://localhost:5050/', { timeout: 15000 });
            console.log('  ↩️ Auto-redirected to start');
          } catch (e) {
            console.log('  ⏰ Redirect timeout');
          }
          
          return 'room_error';
          
        } else if (pageText.includes('Declaration') || pageText.includes('Choose')) {
          console.log('  ✅ Game started successfully (no waiting page issue)');
          return 'success';
          
        } else {
          console.log('  🤔 Unknown state');
          console.log(`  Content: ${pageText.substring(0, 100)}...`);
          return 'unknown';
        }
        
      } else {
        console.log('  ❌ No Start button found');
        return 'no_button';
      }
      
    } catch (error) {
      console.log(`  ❌ Error in attempt ${attemptNumber}: ${error.message}`);
      return 'error';
    }
  }

  try {
    let attempt = 1;
    let maxAttempts = 10;
    let foundWaiting = false;
    
    while (attempt <= maxAttempts && !foundWaiting) {
      const result = await attemptGameStart(attempt);
      
      if (result === 'found_waiting') {
        foundWaiting = true;
        console.log('\n🎯 SUCCESS! Found the actual waiting page issue');
        break;
      } else if (result === 'success') {
        console.log('\n✅ Game worked perfectly on this attempt');
        console.log('The issue might be intermittent');
      }
      
      // Wait between attempts
      if (attempt < maxAttempts) {
        console.log(`  ⏳ Waiting 2 seconds before next attempt...`);
        await page.waitForTimeout(2000);
      }
      
      attempt++;
    }
    
    if (!foundWaiting && attempt > maxAttempts) {
      console.log(`\n⚠️ Could not reproduce "Waiting for game to start..." after ${maxAttempts} attempts`);
      console.log('The issue might be:');
      console.log('  - Fixed already');
      console.log('  - Intermittent');
      console.log('  - Requiring specific conditions');
    }
    
    console.log('\n✅ Test complete. Browser remains open for inspection.');
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
  }
}

testFindWaitingPage().catch(console.error);