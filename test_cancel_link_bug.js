const { chromium } = require('playwright');

async function testCancelLinkBug() {
  console.log('🐛 Testing Cancel Link Bug on Waiting Page\n');
  console.log('Expected: Cancel link should redirect to lobby');
  console.log('Actual Bug: Shows {"detail":"Not Found"}\n');
  
  const browser = await chromium.launch({
    headless: false,
    devtools: true
  });

  const page = await browser.newPage();
  
  // Monitor network requests
  const apiCalls = [];
  page.on('request', request => {
    if (request.url().includes('/api/') || request.url().includes('/cancel') || request.url().includes('/leave')) {
      console.log(`📤 Request: ${request.method()} ${request.url()}`);
      apiCalls.push({
        method: request.method(),
        url: request.url(),
        headers: request.headers()
      });
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('/api/') || response.url().includes('/cancel') || response.url().includes('/leave')) {
      console.log(`📥 Response: ${response.status()} ${response.url()}`);
      if (response.status() === 404) {
        response.text().then(text => {
          console.log(`   ❌ 404 Response body: ${text}`);
        });
      }
    }
  });

  // Monitor navigation
  page.on('framenavigated', frame => {
    if (frame === page.mainFrame()) {
      console.log(`🧭 Navigated to: ${frame.url()}`);
    }
  });

  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`❌ Console Error: ${msg.text()}`);
    }
  });

  try {
    // Step 1: Enter Lobby
    console.log('📍 Step 1: Navigate and Enter Lobby');
    await page.goto('http://localhost:5050');
    await page.waitForLoadState('networkidle');
    
    await page.fill('input[type="text"]', 'TestPlayer');
    await page.click('button:has-text("Enter Lobby")');
    await page.waitForTimeout(1500);
    console.log('  ✓ Entered lobby');
    
    // Step 2: Create Room
    console.log('\n📍 Step 2: Create Room');
    await page.click('button:has-text("Create Room")');
    await page.waitForTimeout(2000);
    
    const roomCode = await page.$eval('body', body => {
      const text = body.innerText;
      const match = text.match(/[A-Z]{4}/);
      return match ? match[0] : null;
    });
    console.log(`  ✓ Room created: ${roomCode}`);
    
    // Step 3: Start Game
    console.log('\n📍 Step 3: Start Game');
    const startButton = await page.$('button:has-text("Start")');
    if (startButton) {
      await startButton.click();
      console.log('  ✓ Clicked Start Game');
      
      // Wait for waiting page
      await page.waitForTimeout(3000);
      
      // Check current state
      const currentUrl = page.url();
      const pageText = await page.textContent('body');
      
      console.log(`\n📊 Current State:`);
      console.log(`  URL: ${currentUrl}`);
      
      // Look for waiting page and cancel link
      const waitingText = pageText.includes('Waiting') || pageText.includes('waiting');
      
      if (waitingText) {
        console.log('  ✓ On waiting page');
        
        // Look for cancel LINK (not button)
        console.log('\n🔍 Looking for cancel link...');
        
        // Try different selectors for links
        let cancelLink = await page.$('a:has-text("Cancel")') || 
                        await page.$('a:has-text("cancel")') ||
                        await page.$('a:has-text("Leave")') ||
                        await page.$('a:has-text("Exit")');
        
        // Also check for any element with cancel text that might be a link
        if (!cancelLink) {
          const elements = await page.$$('*:has-text("Cancel"), *:has-text("cancel")');
          for (const el of elements) {
            const tagName = await el.evaluate(e => e.tagName);
            const text = await el.textContent();
            console.log(`  Found element: <${tagName}> with text "${text.trim()}"`);
            if (tagName === 'A' || (await el.evaluate(e => e.style.cursor === 'pointer'))) {
              cancelLink = el;
              break;
            }
          }
        }
        
        if (cancelLink) {
          console.log('  ✓ Found cancel link');
          
          // Get link details
          const linkInfo = await cancelLink.evaluate(el => ({
            tagName: el.tagName,
            href: el.href,
            text: el.textContent.trim(),
            onclick: el.onclick ? 'has onclick' : 'no onclick'
          }));
          console.log(`  Link info:`, linkInfo);
          
          // Clear API calls to focus on cancel action
          apiCalls.length = 0;
          
          // Take screenshot before clicking
          await page.screenshot({ path: 'before-cancel-link.png' });
          
          console.log('\n📍 Step 4: Click Cancel Link');
          await cancelLink.click();
          console.log('  ✓ Clicked cancel link');
          
          // Wait for response
          await page.waitForTimeout(3000);
          
          // Check result
          const afterUrl = page.url();
          const afterText = await page.textContent('body');
          
          console.log(`\n📊 After Cancel:`);
          console.log(`  URL: ${afterUrl}`);
          
          if (afterText.includes('"detail":"Not Found"') || afterText.includes('{"detail":"Not Found"}')) {
            console.log('  ❌ BUG CONFIRMED: Got {"detail":"Not Found"} error');
            await page.screenshot({ path: 'not-found-error.png' });
            
            // Analyze the failed request
            console.log('\n🔍 Analyzing Failed Request:');
            if (apiCalls.length > 0) {
              apiCalls.forEach(call => {
                console.log(`  ${call.method} ${call.url}`);
              });
            } else {
              console.log('  No API calls captured - might be a direct navigation');
              console.log(`  Failed URL might be: ${afterUrl}`);
            }
            
          } else if (afterUrl === 'http://localhost:5050/' || afterText.includes('Enter Lobby')) {
            console.log('  ✅ Successfully redirected to lobby');
          } else {
            console.log('  🤔 Unexpected state after cancel');
            console.log(`  Page content: ${afterText.substring(0, 200)}`);
          }
          
          // Take final screenshot
          await page.screenshot({ path: 'after-cancel-link.png' });
          
        } else {
          console.log('  ❌ No cancel link found on waiting page');
          
          // List all links
          const links = await page.$$eval('a', links => 
            links.map(l => ({
              text: l.textContent.trim(),
              href: l.href
            }))
          );
          console.log('  Available links:', links);
          
          // Also check for any clickable text
          console.log('\n  Looking for any clickable elements with "cancel" text...');
          const clickables = await page.$$eval('*', elements => {
            return elements
              .filter(el => el.textContent && el.textContent.toLowerCase().includes('cancel'))
              .map(el => ({
                tag: el.tagName,
                text: el.textContent.trim().substring(0, 50),
                clickable: el.style.cursor === 'pointer' || el.onclick !== null
              }));
          });
          console.log('  Clickable elements:', clickables);
        }
      } else {
        console.log('  ❌ Not on waiting page');
        console.log(`  Page content: ${pageText.substring(0, 200)}`);
      }
      
    } else {
      console.log('  ❌ No start button found');
    }
    
    console.log('\n📊 Summary:');
    console.log('  The bug occurs when clicking the cancel link on the waiting page.');
    console.log('  Instead of redirecting to lobby, it shows {"detail":"Not Found"}');
    console.log('  This suggests the cancel link points to a non-existent route.');
    
    console.log('\n🔧 To investigate further:');
    console.log('  1. Check what URL the cancel link points to');
    console.log('  2. Verify if that route exists in the backend');
    console.log('  3. Check frontend routing configuration');
    
    console.log('\n✅ Test complete. Browser remains open.');
    console.log('Screenshots saved: before-cancel-link.png, after-cancel-link.png');
    
    await new Promise(() => {});
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await page.screenshot({ path: 'test-error.png' });
  }
}

testCancelLinkBug().catch(console.error);