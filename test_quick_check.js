const { chromium } = require('playwright');

async function quickCheck() {
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 500 
  });
  
  try {
    const page = await browser.newPage();
    console.log('🌐 Navigating to http://localhost:5050...');
    
    await page.goto('http://localhost:5050');
    await page.waitForTimeout(2000);
    
    // Take screenshot
    await page.screenshot({ path: 'current_page.png', fullPage: true });
    console.log('📸 Screenshot saved as current_page.png');
    
    // Log page title and URL
    console.log('📄 Page title:', await page.title());
    console.log('🔗 Current URL:', page.url());
    
    // Try to find any input fields
    const inputs = await page.$$('input');
    console.log(`🔍 Found ${inputs.length} input fields`);
    
    for (let i = 0; i < inputs.length; i++) {
      const placeholder = await inputs[i].getAttribute('placeholder');
      const type = await inputs[i].getAttribute('type');
      const className = await inputs[i].getAttribute('class');
      console.log(`  Input ${i}: type="${type}", placeholder="${placeholder}", class="${className}"`);
    }
    
    // Check for any visible text
    const visibleText = await page.evaluate(() => {
      const elements = document.querySelectorAll('h1, h2, h3, p, label, button');
      return Array.from(elements).map(el => el.textContent.trim()).filter(text => text.length > 0);
    });
    
    console.log('\n📝 Visible text on page:');
    visibleText.slice(0, 10).forEach(text => console.log(`  - ${text}`));
    
    console.log('\n✅ Quick check complete. Browser will stay open for inspection.');
    console.log('Press Enter to close...');
    
    await new Promise(resolve => process.stdin.once('data', resolve));
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await browser.close();
  }
}

quickCheck();