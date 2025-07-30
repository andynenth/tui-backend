const { chromium } = require('playwright');

async function testRemoveBotSimple() {
  console.log('🧪 Running headed test to observe UI...\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 1000 // Slow down actions to observe
  });
  
  try {
    const page = await browser.newPage();
    
    // Navigate and wait
    await page.goto('http://localhost:5050');
    await page.waitForTimeout(2000);
    
    // Take screenshot of initial page
    await page.screenshot({ path: 'issue3_1_initial.png' });
    console.log('📸 Screenshot saved: issue3_1_initial.png');
    
    // Try to find any input field
    const inputs = await page.locator('input').all();
    console.log(`Found ${inputs.length} input fields`);
    
    // Try to find any buttons
    const buttons = await page.locator('button').all();
    console.log(`Found ${buttons.length} buttons`);
    
    // Log page content for debugging
    const pageContent = await page.content();
    console.log('\nPage title:', await page.title());
    
    // Check if there's any error message
    const bodyText = await page.locator('body').textContent();
    console.log('\nBody text preview:', bodyText.substring(0, 200));
    
    // Wait for user to manually interact if needed
    console.log('\n⏸️ Browser will stay open for 30 seconds for manual inspection...');
    await page.waitForTimeout(30000);
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
}

testRemoveBotSimple();