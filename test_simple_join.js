const { chromium } = require('playwright');

async function testSimpleJoin() {
  console.log('🔍 Testing Simple Room Join\n');
  
  const browser1 = await chromium.launch({ headless: false, devtools: false });
  const browser2 = await chromium.launch({ headless: false, devtools: false });
  
  const page1 = await browser1.newPage();
  const page2 = await browser2.newPage();
  
  try {
    // Player 1: Enter Lobby and Create Room
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
    const roomCards = await page2.$$('[data-testid="room-card"], .room-card, .room-item');
    console.log(`Player 2 sees ${roomCards.length} room cards`);
    
    if (roomCards.length > 0) {
      // Take screenshot of first room card
      await roomCards[0].screenshot({ path: 'room-card.png' });
      const roomText = await roomCards[0].textContent();
      console.log('Room card text:', roomText);
      
      // Try to find Join button
      const joinButton = await roomCards[0].$('button:has-text("Join")');
      if (joinButton) {
        console.log('✅ Found Join button');
        await joinButton.click();
        await page2.waitForTimeout(2000);
        
        // Check if successfully joined
        const url = page2.url();
        console.log('Player 2 URL after join:', url);
        
        if (url.includes('/room/')) {
          console.log('✅ Player 2 successfully joined room!');
        } else {
          console.log('❌ Player 2 failed to join room');
        }
      } else {
        console.log('❌ Join button not found');
      }
    } else {
      console.log('❌ No room cards found for Player 2');
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

testSimpleJoin();