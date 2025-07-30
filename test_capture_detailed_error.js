const { chromium } = require('playwright');

/**
 * CAPTURE DETAILED ERROR TEST
 * 
 * Captures the exact error details from the join_room failure to identify remaining issues.
 */

async function captureDetailedError() {
  console.log('🔍 CAPTURE DETAILED ERROR TEST');
  console.log('===============================');
  
  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000
  });
  
  try {
    // === Setup Creator ===
    const creatorContext = await browser.newContext();
    const creatorPage = await creatorContext.newPage();
    
    await creatorPage.goto('http://localhost:5050');
    await creatorPage.waitForLoadState('networkidle');
    
    await creatorPage.locator('input[type="text"]').first().fill('Creator');
    await creatorPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await creatorPage.waitForTimeout(2000);
    
    const createBtn = await creatorPage.locator('button').filter({ hasText: /create/i }).first();
    await createBtn.click();
    await creatorPage.waitForTimeout(5000);
    
    // Remove bot
    const removeBtns = await creatorPage.locator('button:has-text("Remove"), button:has-text("Kick")').all();
    if (removeBtns.length > 0) {
      await removeBtns[0].click();
      await creatorPage.waitForTimeout(3000);
    }
    
    // === Setup Joiner with detailed error capture ===
    const joinerContext = await browser.newContext();
    const joinerPage = await joinerContext.newPage();
    
    let detailedError = null;
    
    joinerPage.on('websocket', ws => {
      ws.on('framereceived', data => {
        try {
          const parsed = JSON.parse(data.payload);
          if (parsed.event === 'error' && parsed.data?.message?.includes('join_room')) {
            detailedError = {
              message: parsed.data?.message,
              type: parsed.data?.type,
              details: parsed.data?.details,
              timestamp: new Date().toISOString(),
              fullData: parsed.data
            };
            console.log('❌ DETAILED ERROR CAPTURED:');
            console.log(`   Message: ${detailedError.message}`);
            console.log(`   Type: ${detailedError.type}`);
            console.log(`   Details: ${detailedError.details}`);
            console.log(`   Full data:`, detailedError.fullData);
          }
        } catch (e) {}
      });
    });
    
    await joinerPage.goto('http://localhost:5050');
    await joinerPage.waitForLoadState('networkidle');
    
    await joinerPage.locator('input[type="text"]').first().fill('Joiner');
    await joinerPage.locator('button').filter({ hasText: /play|start|enter|lobby/i }).first().click();
    await joinerPage.waitForTimeout(3000);
    
    // Attempt join
    const roomCards = await joinerPage.locator('.lp-roomCard').all();
    if (roomCards.length > 0) {
      console.log('🎯 Attempting join...');
      await roomCards[0].click();
      await joinerPage.waitForTimeout(5000);
      
      if (detailedError) {
        console.log('\n🔍 ERROR ANALYSIS:');
        
        // Check if it's still the same PlayerJoinedRoom error
        if (detailedError.details && detailedError.details.includes('PlayerJoinedRoom')) {
          console.log('❌ SAME ERROR: PlayerJoinedRoom constructor issue persists');
          console.log('   The fix may not have been applied correctly');
        } else if (detailedError.details && detailedError.details.includes('Room')) {
          console.log('🔍 ROOM RELATED ERROR:', detailedError.details);
        } else {
          console.log('🔍 NEW ERROR TYPE:', detailedError.details);
        }
        
        console.log('\n📋 RECOMMENDED ACTIONS:');
        if (detailedError.details && detailedError.details.includes('game_id')) {
          console.log('   1. Check that the join_room.py file was saved correctly');
          console.log('   2. Verify the server restarted after the fix');
          console.log('   3. Ensure no other code paths are calling PlayerJoinedRoom with game_id');
        } else {
          console.log('   1. Check server logs for full stack trace');
          console.log('   2. Investigate other potential parameter mismatches');
          console.log('   3. Verify all required parameters are provided');
        }
      } else {
        console.log('✅ NO ERROR: Join may have succeeded silently');
        
        const finalUrl = joinerPage.url();
        if (finalUrl.includes('/room/')) {
          console.log('🎉 SUCCESS: Player actually joined the room!');
        } else {
          console.log('❓ UNCLEAR: No error but still in lobby');
        }
      }
    }
    
    console.log('\n⏱️ Keeping browsers open for inspection...');
    await joinerPage.waitForTimeout(20000);
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

captureDetailedError().catch(console.error);