const { chromium } = require('playwright');

async function debugTransition() {
  console.log('🚀 Starting Direct Debug of Waiting Page Issue\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor WebSocket
  const wsEvents = [];
  page.on('websocket', ws => {
    console.log('🔌 WebSocket connected:', ws.url());
    
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log('📤 Sent:', data.type);
        wsEvents.push({ type: 'sent', data, timestamp: Date.now() });
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        console.log('📥 Received:', data.type);
        wsEvents.push({ type: 'received', data, timestamp: Date.now() });
        
        // Check for game_started event
        if (data.type === 'game_started') {
          console.log('✅ GAME_STARTED EVENT RECEIVED!');
          console.log('Payload:', JSON.stringify(data.payload, null, 2));
        }
      } catch (e) {}
    });
  });

  // Monitor console
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('❌ Console Error:', msg.text());
    }
  });

  try {
    // Navigate to app
    console.log('1️⃣ Navigating to app...');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    // Wait for lobby page
    console.log('2️⃣ Waiting for lobby page...');
    await page.waitForSelector('button:has-text("Create Room"), button:has-text("Join Room")', { timeout: 10000 });
    
    // Enter name and create room
    console.log('3️⃣ Creating room...');
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Create Room")');
    
    // Wait for room creation
    await page.waitForTimeout(2000);
    
    // Look for room code
    const roomCodeElement = await page.$('text=/[A-Z]{4}/');
    if (roomCodeElement) {
      const roomCode = await roomCodeElement.textContent();
      console.log('4️⃣ Room created:', roomCode);
    }
    
    // Check if we're in waiting room
    const isWaiting = await page.$('text=/Waiting for players/i');
    if (isWaiting) {
      console.log('5️⃣ In waiting room');
    }
    
    // Try to find and click start button
    console.log('6️⃣ Looking for start button...');
    const startButton = await page.$('button:has-text("Start Game")');
    
    if (startButton) {
      console.log('7️⃣ Start button found! Clicking...');
      
      // Monitor for navigation
      const navigationPromise = page.waitForURL('**/game/**', { 
        timeout: 10000 
      }).catch(() => null);
      
      await startButton.click();
      console.log('8️⃣ Start button clicked!');
      
      // Wait for potential navigation
      const navigated = await navigationPromise;
      
      if (navigated) {
        console.log('✅ Successfully navigated to game page!');
      } else {
        console.log('❌ No navigation occurred after 10 seconds');
        
        // Check current state
        const currentUrl = page.url();
        console.log('Current URL:', currentUrl);
        
        // Check if still in waiting room
        const stillWaiting = await page.$('text=/Waiting for players/i');
        if (stillWaiting) {
          console.log('⚠️ Still stuck in waiting room!');
        }
        
        // Check for any error messages
        const errorElement = await page.$('text=/error/i');
        if (errorElement) {
          const errorText = await errorElement.textContent();
          console.log('Error found:', errorText);
        }
      }
    } else {
      console.log('❌ Start button not found!');
      
      // Try to find what's on the page
      const pageText = await page.textContent('body');
      console.log('Page content preview:', pageText.substring(0, 200));
    }
    
    // Print WebSocket event summary
    console.log('\n📊 WebSocket Event Summary:');
    const eventTypes = {};
    wsEvents.forEach(event => {
      const key = `${event.type}: ${event.data.type}`;
      eventTypes[key] = (eventTypes[key] || 0) + 1;
    });
    Object.entries(eventTypes).forEach(([key, count]) => {
      console.log(`  ${key}: ${count}`);
    });
    
    // Check for specific missing events
    const hasGameStarted = wsEvents.some(e => 
      e.type === 'received' && e.data.type === 'game_started'
    );
    
    if (!hasGameStarted) {
      console.log('\n⚠️ WARNING: No game_started event received from server!');
    }
    
    console.log('\n✅ Debug complete. Browser remains open for inspection.');
    console.log('Press Ctrl+C to exit.');
    
    // Keep browser open
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

debugTransition().catch(console.error);