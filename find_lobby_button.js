const { chromium } = require('playwright');

async function findLobbyButton() {
  console.log('🔍 Finding how to join lobby\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  try {
    console.log('1️⃣ Loading main page...');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Take screenshot of landing page
    await page.screenshot({ path: 'landing-page.png', fullPage: true });
    console.log('📸 Screenshot saved as landing-page.png\n');
    
    // Get all visible text on page
    console.log('📄 Page content:');
    const pageText = await page.textContent('body');
    console.log(pageText.replace(/\s+/g, ' ').trim().substring(0, 300));
    
    // Find all clickable elements
    console.log('\n🔘 All buttons and links:');
    
    // Check buttons
    const buttons = await page.$$eval('button', elements => 
      elements.map(el => ({
        text: el.textContent.trim(),
        visible: el.offsetParent !== null,
        onclick: el.onclick ? 'has onclick' : 'no onclick'
      }))
    );
    
    console.log('\nButtons:');
    buttons.forEach((btn, i) => {
      if (btn.visible) {
        console.log(`  ${i}: "${btn.text}" (${btn.onclick})`);
      }
    });
    
    // Check links
    const links = await page.$$eval('a', elements => 
      elements.map(el => ({
        text: el.textContent.trim(),
        href: el.href,
        visible: el.offsetParent !== null
      }))
    );
    
    console.log('\nLinks:');
    links.forEach((link, i) => {
      if (link.visible && link.text) {
        console.log(`  ${i}: "${link.text}" -> ${link.href}`);
      }
    });
    
    // Check for specific lobby-related text
    console.log('\n🎯 Looking for lobby entry points:');
    const lobbySelectors = [
      'button:has-text("Join Lobby")',
      'button:has-text("Enter Lobby")',
      'button:has-text("Play")',
      'button:has-text("Start")',
      'button:has-text("Multiplayer")',
      'button:has-text("Online")',
      'a:has-text("Lobby")',
      'a:has-text("Play")',
      '*:has-text("Join Lobby")',
      '*:has-text("Enter Lobby")'
    ];
    
    for (const selector of lobbySelectors) {
      const element = await page.$(selector);
      console.log(`  ${selector}: ${element ? '✅ FOUND' : '❌ Not found'}`);
      
      if (element) {
        const text = await element.textContent();
        console.log(`    Text: "${text.trim()}"`);
      }
    }
    
    // Look for any element that might lead to lobby
    console.log('\n🔍 Checking all clickable elements with "lobby" or "play" text:');
    const clickables = await page.$$('button, a, div[onclick], span[onclick]');
    for (const el of clickables) {
      const text = await el.textContent();
      if (text && (text.toLowerCase().includes('lobby') || 
                   text.toLowerCase().includes('play') ||
                   text.toLowerCase().includes('join') ||
                   text.toLowerCase().includes('start'))) {
        const tagName = await el.evaluate(e => e.tagName);
        console.log(`  Found: <${tagName}> with text "${text.trim()}"`);
      }
    }
    
    console.log('\n💡 Tip: The landing page might be:');
    console.log('  - A main menu with "Play" or "Join Lobby" button');
    console.log('  - Already the lobby (if you see "Create Room" options)');
    console.log('  - A login screen (if authentication is required)');
    
    console.log('\n✅ Browser remains open for manual inspection.');
    console.log('Please check landing-page.png to see what\'s on screen.');
    
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

findLobbyButton().catch(console.error);