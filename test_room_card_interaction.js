const { chromium } = require('playwright');

async function testRoomCardInteraction() {
  console.log('🔍 Testing Room Card Interaction\n');
  
  const browser1 = await chromium.launch({ headless: false, devtools: false });
  const browser2 = await chromium.launch({ headless: false, devtools: false });
  
  const page1 = await browser1.newPage();
  const page2 = await browser2.newPage();
  
  // Monitor WebSocket for Player 2
  page2.on('websocket', ws => {
    ws.on('framesent', event => {
      try {
        const data = JSON.parse(event.payload);
        if (data.event === 'join_room') {
          console.log(`👥 P2 SENT join_room:`, data.data);
        }
      } catch (e) {}
    });
    
    ws.on('framereceived', event => {
      try {
        const data = JSON.parse(event.payload);
        if (data.event === 'room_joined' || data.event === 'error') {
          console.log(`👥 P2 RECEIVED ${data.event}:`, data.data);
        }
      } catch (e) {}
    });
  });
  
  try {
    // Player 1: Create Room
    console.log('🟢 Player 1: Creating room...');
    await page1.goto('http://localhost:5050');
    await page1.fill('input[type="text"]', 'Player1');
    await page1.click('button:has-text("Enter Lobby")');
    await page1.waitForTimeout(1000);
    await page1.click('button:has-text("Create Room")');
    await page1.waitForSelector('button:has-text("Leave Room")', { timeout: 5000 });
    console.log('✅ Player 1 created room');
    
    // Player 2: Enter Lobby
    console.log('🟢 Player 2: Entering lobby...');
    await page2.goto('http://localhost:5050');
    await page2.fill('input[type="text"]', 'Player2');
    await page2.click('button:has-text("Enter Lobby")');
    await page2.waitForTimeout(2000);
    
    // Check what Player 2 sees
    console.log('\\n📊 Player 2 lobby analysis:');
    
    // Check room count display
    const roomCountText = await page2.$eval('.lp-roomCount', el => el.textContent).catch(() => 'Not found');
    console.log('Room count text:', roomCountText);
    
    // Find all room cards
    const roomCards = await page2.$$('.lp-roomCard');
    console.log(`Found ${roomCards.length} room cards`);
    
    if (roomCards.length > 0) {
      const roomCard = roomCards[0];
      
      // Get room card details
      const roomId = await roomCard.$eval('.lp-roomId', el => el.textContent).catch(() => 'No room ID');
      const hostName = await roomCard.$eval('.lp-hostName', el => el.textContent).catch(() => 'No host name');
      const occupancy = await roomCard.$eval('.lp-roomOccupancy', el => el.textContent).catch(() => 'No occupancy');
      
      console.log('\\n🏠 Room card details:');
      console.log('- Room ID:', roomId);
      console.log('- Host:', hostName);
      console.log('- Occupancy:', occupancy);
      
      // Check if room card is clickable
      const isClickable = await roomCard.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.pointerEvents !== 'none' && !el.disabled;
      });
      console.log('- Clickable:', isClickable);
      
      // Check for disabled class
      const hasDisabledClass = await roomCard.evaluate(el => el.classList.contains('lp-full'));
      console.log('- Has lp-full class:', hasDisabledClass);
      
      if (isClickable && !hasDisabledClass) {
        console.log('\\n🎯 Attempting to join room...');
        
        // Click the room card
        await roomCard.click();
        
        // Wait for any response
        await page2.waitForTimeout(3000);
        
        // Check if we navigated to room
        const currentUrl = page2.url();
        console.log('Current URL:', currentUrl);
        
        if (currentUrl.includes('/room/')) {
          console.log('✅ Successfully joined room!');
        } else {
          console.log('❌ Failed to join room - still in lobby');
        }
      } else {
        console.log('❌ Room card is not clickable or disabled');
      }
    } else {
      console.log('❌ No room cards found');
    }
    
    setTimeout(async () => {
      await browser1.close();
      await browser2.close();
    }, 5000);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    await browser1.close();
    await browser2.close();
  }
}

testRoomCardInteraction();