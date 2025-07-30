const { chromium } = require('playwright');

async function diagnosePage() {
  console.log('🔍 Diagnosing Page Elements\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  try {
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    // Wait a bit for any dynamic content
    await page.waitForTimeout(2000);
    
    // Take screenshot
    await page.screenshot({ path: 'page-diagnosis.png', fullPage: true });
    console.log('📸 Screenshot saved as page-diagnosis.png\n');
    
    // Get all button texts
    console.log('🔘 All buttons on page:');
    const buttons = await page.$$eval('button', elements => 
      elements.map((el, i) => ({
        index: i,
        text: el.textContent.trim(),
        visible: el.offsetParent !== null,
        disabled: el.disabled,
        className: el.className,
        id: el.id
      }))
    );
    
    buttons.forEach(btn => {
      console.log(`  Button ${btn.index}:`);
      console.log(`    Text: "${btn.text}"`);
      console.log(`    Visible: ${btn.visible}`);
      console.log(`    Disabled: ${btn.disabled}`);
      console.log(`    Class: ${btn.className}`);
      console.log(`    ID: ${btn.id}`);
    });
    
    // Get all inputs
    console.log('\n📝 All inputs on page:');
    const inputs = await page.$$eval('input', elements => 
      elements.map((el, i) => ({
        index: i,
        type: el.type,
        placeholder: el.placeholder,
        value: el.value,
        visible: el.offsetParent !== null,
        id: el.id,
        name: el.name
      }))
    );
    
    inputs.forEach(input => {
      console.log(`  Input ${input.index}:`);
      console.log(`    Type: ${input.type}`);
      console.log(`    Placeholder: "${input.placeholder}"`);
      console.log(`    Value: "${input.value}"`);
      console.log(`    Visible: ${input.visible}`);
    });
    
    // Get page text content
    console.log('\n📄 Page text content (first 500 chars):');
    const textContent = await page.textContent('body');
    console.log(textContent.substring(0, 500).replace(/\s+/g, ' ').trim());
    
    // Check for specific elements by different selectors
    console.log('\n🎯 Checking specific elements:');
    const selectors = [
      'button:has-text("Create")',
      'button:has-text("Join")',
      'button:has-text("Room")',
      'button[id*="create"]',
      'button[id*="join"]',
      'button[class*="create"]',
      'button[class*="join"]',
      '*:has-text("Create Room")',
      '*:has-text("Join Room")'
    ];
    
    for (const selector of selectors) {
      const element = await page.$(selector);
      console.log(`  ${selector}: ${element ? 'Found' : 'Not found'}`);
    }
    
    // Get the HTML structure around any forms
    console.log('\n🏗️ Form structure:');
    const forms = await page.$$('form');
    console.log(`  Found ${forms.length} forms`);
    
    // Check what happens after entering name
    console.log('\n🎮 Testing interaction:');
    const nameInput = await page.$('input[type="text"]');
    if (nameInput) {
      await nameInput.fill('TestPlayer');
      console.log('  ✓ Filled name input');
      
      // Wait to see if buttons appear
      await page.waitForTimeout(1000);
      
      // Check buttons again
      const buttonsAfter = await page.$$eval('button', elements => 
        elements.map(el => el.textContent.trim())
      );
      console.log('  Buttons after entering name:', buttonsAfter);
    }
    
    console.log('\n✅ Diagnosis complete. Check page-diagnosis.png');
    console.log('Browser remains open for manual inspection.');
    
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

diagnosePage().catch(console.error);