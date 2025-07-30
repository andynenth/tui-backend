const { chromium } = require('playwright');

async function analyzeWebSocketIssue() {
  console.log('🔍 Analyzing WebSocket and Room Persistence Issue\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Track all WebSocket messages with full details
  const wsMessages = [];
  
  page.on('websocket', ws => {
    console.log(`🔌 WebSocket connected: ${ws.url()}`);
    
    ws.on('framesent', event => {
      const payload = event.payload;
      console.log(`📤 WS Send (raw): ${payload.substring(0, 100)}...`);
      wsMessages.push({
        direction: 'sent',
        payload: payload,
        timestamp: Date.now()
      });
      
      // Try different parsing approaches
      try {
        const data = JSON.parse(payload);
        console.log(`   Parsed type: ${data.type || data.event || data.action || 'unknown'}`);
      } catch (e) {
        console.log(`   Not JSON format`);
      }
    });
    
    ws.on('framereceived', event => {
      const payload = event.payload;
      console.log(`📥 WS Receive (raw): ${payload.substring(0, 100)}...`);
      wsMessages.push({
        direction: 'received',
        payload: payload,
        timestamp: Date.now()
      });
      
      try {
        const data = JSON.parse(payload);
        console.log(`   Parsed type: ${data.type || data.event || data.action || 'unknown'}`);
        
        // Check for error messages
        if (data.error || data.message?.includes('error') || data.message?.includes('exist')) {
          console.log(`   ⚠️ ERROR: ${JSON.stringify(data)}`);
        }
      } catch (e) {
        console.log(`   Not JSON format`);
      }
    });
  });

  // Monitor console for errors
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.text().includes('Error')) {
      console.log(`\n❌ Console: ${msg.text()}\n`);
    }
  });

  try {
    // Quick flow to reproduce
    console.log('1️⃣ Loading page...');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    console.log('2️⃣ Entering lobby...');
    await page.fill('input[type="text"]', 'DebugPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1500);
    
    console.log('3️⃣ Creating room...');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    // Get room details
    const roomInfo = await page.evaluate(() => {
      const bodyText = document.body.innerText;
      const roomMatch = bodyText.match(/[A-Z]{4}/);
      const urlMatch = window.location.href.match(/room\/([A-Z0-9]+)/);
      return {
        roomCode: roomMatch ? roomMatch[0] : null,
        roomId: urlMatch ? urlMatch[1] : null,
        url: window.location.href,
        hasStartButton: !!document.querySelector('button:has-text("Start")')
      };
    });
    
    console.log(`\n📊 Room Info:`);
    console.log(`   Room Code: ${roomInfo.roomCode}`);
    console.log(`   Room ID: ${roomInfo.roomId}`);
    console.log(`   URL: ${roomInfo.url}`);
    console.log(`   Has Start Button: ${roomInfo.hasStartButton}`);
    
    if (roomInfo.hasStartButton) {
      console.log('\n4️⃣ Clicking Start Game...');
      
      // Clear previous messages to focus on start game flow
      const beforeStartCount = wsMessages.length;
      
      await page.click('button:has-text("Start")');
      
      // Wait and capture what happens
      await page.waitForTimeout(3000);
      
      // Analyze messages sent after clicking start
      console.log('\n📊 Messages after Start click:');
      const afterStartMessages = wsMessages.slice(beforeStartCount);
      afterStartMessages.forEach((msg, i) => {
        console.log(`\n${i + 1}. ${msg.direction.toUpperCase()}:`);
        try {
          const parsed = JSON.parse(msg.payload);
          console.log(`   ${JSON.stringify(parsed, null, 2)}`);
        } catch (e) {
          console.log(`   Raw: ${msg.payload}`);
        }
      });
      
      // Check final state
      const finalState = await page.evaluate(() => ({
        url: window.location.href,
        onLobbyPage: window.location.pathname === '/',
        onRoomPage: window.location.pathname.includes('/room/'),
        onGamePage: window.location.pathname.includes('/game/'),
        bodyText: document.body.innerText.substring(0, 200)
      }));
      
      console.log('\n📊 Final State:');
      console.log(`   URL: ${finalState.url}`);
      console.log(`   On Lobby: ${finalState.onLobbyPage}`);
      console.log(`   On Room: ${finalState.onRoomPage}`);
      console.log(`   On Game: ${finalState.onGamePage}`);
      
      if (finalState.onLobbyPage) {
        console.log('\n⚠️  ISSUE: Redirected back to lobby after start!');
        console.log('   This confirms the room was lost/expired');
      }
    }
    
    // Save all messages for analysis
    const report = {
      timestamp: new Date().toISOString(),
      roomInfo,
      messageCount: wsMessages.length,
      messages: wsMessages.map(msg => {
        try {
          return {
            ...msg,
            parsed: JSON.parse(msg.payload)
          };
        } catch (e) {
          return msg;
        }
      })
    };
    
    await require('fs').promises.writeFile(
      'websocket-analysis.json',
      JSON.stringify(report, null, 2)
    );
    
    console.log('\n💾 Full WebSocket log saved to websocket-analysis.json');
    console.log('\n🔍 Key Finding: The room appears to be lost when trying to start the game.');
    console.log('   Possible causes:');
    console.log('   - Server restarted and lost in-memory room data');
    console.log('   - Room expired due to timeout');
    console.log('   - Session/authentication issue');
    console.log('   - State synchronization problem between frontend and backend');
    
    console.log('\n✅ Analysis complete. Browser remains open.');
    
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

analyzeWebSocketIssue().catch(console.error);