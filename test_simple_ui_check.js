const { chromium } = require('playwright');

async function testSimpleUICheck() {
  console.log('🚀 Simple UI Check Test...');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });
  
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Capture console errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('❌ Console Error:', msg.text());
      }
    });
    
    page.on('pageerror', error => {
      console.log('❌ Page Error:', error.message);
    });
    
    console.log('1. Going to lobby...');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    console.log('2. Entering player name...');
    const nameInput = await page.locator('input[type="text"]').first();
    await nameInput.fill('TestPlayer');
    
    const startButton = await page.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first();
    await startButton.click();
    
    await page.waitForTimeout(3000);
    
    console.log('3. Checking if lobby page loaded...');
    try {
      const roomCountElement = await page.locator('.lp-roomCount').first();
      const roomCountText = await roomCountElement.textContent();
      console.log('✅ Room count element found:', roomCountText);
      
      const emptyState = await page.locator('.lp-emptyState').isVisible();
      console.log('Empty state visible:', emptyState);
      
      const roomCards = await page.locator('.lp-roomCard').count();
      console.log('Room cards count:', roomCards);
      
    } catch (error) {
      console.log('❌ Error accessing UI elements:', error.message);
    }
    
    console.log('4. Creating room to test UI update...');
    try {
      const createBtn = await page.locator('button').filter({ hasText: /create/i }).first();
      await createBtn.click();
      
      console.log('5. Waiting for room creation...');
      await page.waitForTimeout(5000);
      
      console.log('6. Checking UI after room creation...');
      const roomCountAfter = await page.locator('.lp-roomCount').textContent();
      console.log('Room count after creation:', roomCountAfter);
      
      const roomCardsAfter = await page.locator('.lp-roomCard').count();
      console.log('Room cards after creation:', roomCardsAfter);
      
    } catch (error) {
      console.log('❌ Error during room creation test:', error.message);
    }
    
    // Keep open for inspection
    console.log('⏱️ Keeping browser open for 20 seconds...');
    await page.waitForTimeout(20000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
    console.log('🏁 Test completed');
  }
}

testSimpleUICheck().catch(console.error);