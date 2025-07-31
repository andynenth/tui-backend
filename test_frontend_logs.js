const { chromium } = require('playwright');

async function testFrontendLogs() {
  console.log('🔍 Testing Frontend Event Processing\n');
  
  const browser = await chromium.launch({ headless: false, devtools: true });
  const page = await browser.newPage();
  
  // Listen to console logs from the page
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('room') || text.includes('Room') || text.includes('🔄') || text.includes('🎯') || text.includes('📊')) {
      console.log(`[FRONTEND]: ${text}`);
    }
  });
  
  try {
    console.log('🟢 Player entering lobby...');
    await page.goto('http://localhost:5050');
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(3000);
    
    console.log('\\n🏠 Creating room...');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(5000);
    
    console.log('\\n📋 Final check - going back to lobby...');
    await page.click('button:has-text("Leave Room")');
    await page.waitForURL('**/lobby', { timeout: 5000 });
    await page.waitForTimeout(3000);
    
    // Check room count in UI
    const roomCount = await page.$eval('.lp-roomCount', el => el.textContent).catch(() => 'Element not found');
    console.log('\\n🎯 Room count element text:', roomCount);
    
    const roomCards = await page.$$('.lp-roomCard, [data-testid="room-card"]');
    console.log('🃏 Actual room cards found:', roomCards.length);
    
    setTimeout(async () => {
      await browser.close();
    }, 2000);
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    await browser.close();
  }
}

testFrontendLogs();