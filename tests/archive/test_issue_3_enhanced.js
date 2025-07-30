const { chromium } = require('playwright');

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function logDetailedRoomState(page, stepNumber, label) {
  console.log(`\n📊 STEP ${stepNumber} - ${label}:`);
  console.log('=' .repeat(60));
  
  try {
    // Get all player cards
    const playerCards = await page.locator('.rp-playerCard').all();
    
    console.log(`Total slots visible: ${playerCards.length}`);
    console.log('Slot details:');
    
    for (let i = 0; i < playerCards.length; i++) {
      const card = playerCards[i];
      const isEmpty = await card.locator('.rp-playerAction button:has-text("Add Bot")').count() > 0;
      
      if (isEmpty) {
        console.log(`  Slot ${i + 1}: [EMPTY] - Has "Add Bot" button`);
      } else {
        const nameElement = await card.locator('.rp-playerName').first();
        const name = await nameElement.textContent();
        const isHost = await card.locator('.rp-hostBadge').count() > 0;
        const hasRemoveBtn = await card.locator('button:has-text("Remove")').count() > 0;
        const removeBtn = card.locator('button:has-text("Remove")');
        const isRemovable = hasRemoveBtn && await removeBtn.isEnabled();
        
        console.log(`  Slot ${i + 1}: ${name.trim()}`);
        console.log(`    - Host: ${isHost ? 'YES 👑' : 'NO'}`);
        console.log(`    - Has Remove button: ${hasRemoveBtn ? 'YES' : 'NO'}`);
        console.log(`    - Remove button enabled: ${isRemovable ? 'YES' : 'NO'}`);
      }
    }
    console.log('=' .repeat(60));
  } catch (error) {
    console.log('  ❌ Error capturing room state:', error.message);
  }
}

async function captureNetworkLogs(page, label) {
  console.log(`\n🌐 Network activity for ${label}:`);
  // This would capture WebSocket messages if implemented
}

async function testExactSequence() {
  console.log('🧪 Testing Issue 3: Remove Bot Wrong Slot - FULL 13-STEP SEQUENCE\n');
  console.log('Expected behavior: Remove operations should target the correct slot');
  console.log('Known issue: Remove bot might target wrong slot\n');
  
  const browser = await chromium.launch({ 
    headless: false,
    slowMo: 800 // Slow down to observe actions
  });
  
  try {
    // Create two browser contexts for two players
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // Enable detailed console logging for Player 1
    page1.on('console', msg => {
      const text = msg.text();
      if (text.includes('REMOVE_PLAYER') || text.includes('ADD_BOT') || 
          text.includes('room') || text.includes('player')) {
        console.log(`[P1 Console]: ${text}`);
      }
    });
    
    // Track WebSocket messages
    page1.on('websocket', ws => {
      ws.on('framesent', frame => {
        const payload = frame.payload;
        if (payload && payload.includes('REMOVE') || payload.includes('ADD')) {
          console.log(`[P1 WebSocket OUT]: ${payload}`);
        }
      });
    });
    
    // STEP 1: Player 1 joins lobby
    console.log('\n🎯 STEP 1: Player 1 >> join lobby');
    await page1.goto('http://localhost:5050');
    await page1.fill('input[type="text"]', 'Player1');
    await page1.click('button:has-text("Enter Lobby")');
    await sleep(1500);
    console.log('✅ Player 1 entered lobby');
    
    // STEP 2: Player 1 creates room
    console.log('\n🎯 STEP 2: Player 1 >> create room');
    await page1.click('button:has-text("Create Room")');
    await sleep(2000);
    await logDetailedRoomState(page1, 2, 'Initial room state (Player1 + 3 bots)');
    
    // STEP 3: Player 1 removes bot 2
    console.log('\n🎯 STEP 3: Player 1 >> remove bot 2');
    console.log('Expected: Remove Bot 2 from slot 2');
    const playerCards3 = await page1.locator('.rp-playerCard').all();
    if (playerCards3.length > 1) {
      const bot2Card = playerCards3[1]; // Slot 2 (index 1)
      const bot2Name = await bot2Card.locator('.rp-playerName').textContent();
      console.log(`Targeting slot 2, found: ${bot2Name}`);
      const removeBtn = bot2Card.locator('button:has-text("Remove")');
      if (await removeBtn.isVisible()) {
        await removeBtn.click();
        console.log('✅ Clicked Remove button in slot 2');
      }
    }
    await sleep(1500);
    await logDetailedRoomState(page1, 3, 'After removing Bot 2');
    
    // Store finding in memory
    await page1.evaluate(() => {
      console.log('REMOVE_PLAYER: Step 3 - Attempted to remove Bot 2 from slot 2');
    });
    
    // STEP 4: Player 2 joins lobby
    console.log('\n🎯 STEP 4: Player 2 >> join lobby');
    await page2.goto('http://localhost:5050');
    await page2.fill('input[type="text"]', 'Player2');
    await page2.click('button:has-text("Enter Lobby")');
    await sleep(1500);
    console.log('✅ Player 2 entered lobby');
    
    // STEP 5: Player 1 removes bot 3
    console.log('\n🎯 STEP 5: Player 1 >> remove bot 3');
    console.log('Expected: Remove Bot 3 from its current slot');
    await logDetailedRoomState(page1, 5, 'Before removing Bot 3');
    
    const playerCards5 = await page1.locator('.rp-playerCard').all();
    let bot3Found = false;
    for (let i = 0; i < playerCards5.length; i++) {
      const card = playerCards5[i];
      const nameEl = await card.locator('.rp-playerName');
      if (await nameEl.count() > 0) {
        const name = await nameEl.textContent();
        if (name.includes('Bot 3')) {
          console.log(`Found Bot 3 in slot ${i + 1}`);
          const removeBtn = card.locator('button:has-text("Remove")');
          if (await removeBtn.isVisible()) {
            await removeBtn.click();
            console.log(`✅ Clicked Remove on Bot 3 in slot ${i + 1}`);
            bot3Found = true;
            break;
          }
        }
      }
    }
    if (!bot3Found) {
      console.log('⚠️ Bot 3 not found or not removable');
    }
    await sleep(1500);
    await logDetailedRoomState(page1, 5, 'After removing Bot 3');
    
    // STEP 6: Player 1 removes bot 4
    console.log('\n🎯 STEP 6: Player 1 >> remove bot 4');
    console.log('Expected: Remove Bot 4 from its current slot');
    const playerCards6 = await page1.locator('.rp-playerCard').all();
    let bot4Found = false;
    for (let i = 0; i < playerCards6.length; i++) {
      const card = playerCards6[i];
      const nameEl = await card.locator('.rp-playerName');
      if (await nameEl.count() > 0) {
        const name = await nameEl.textContent();
        if (name.includes('Bot 4')) {
          console.log(`Found Bot 4 in slot ${i + 1}`);
          const removeBtn = card.locator('button:has-text("Remove")');
          if (await removeBtn.isVisible()) {
            await removeBtn.click();
            console.log(`✅ Clicked Remove on Bot 4 in slot ${i + 1}`);
            bot4Found = true;
            break;
          }
        }
      }
    }
    if (!bot4Found) {
      console.log('⚠️ Bot 4 not found or not removable');
    }
    await sleep(1500);
    await logDetailedRoomState(page1, 6, 'After removing Bot 4');
    
    // STEP 7: Player 1 adds bot to slot 3
    console.log('\n🎯 STEP 7: Player 1 >> add bot 3');
    console.log('Expected: Add bot to slot 3');
    const playerCards7 = await page1.locator('.rp-playerCard').all();
    if (playerCards7.length > 2) {
      const slot3 = playerCards7[2]; // Slot 3 (index 2)
      const addBotBtn = slot3.locator('button:has-text("Add Bot")');
      if (await addBotBtn.isVisible()) {
        await addBotBtn.click();
        console.log('✅ Clicked Add Bot on slot 3');
      } else {
        console.log('⚠️ Slot 3 does not have Add Bot button');
      }
    }
    await sleep(1500);
    await logDetailedRoomState(page1, 7, 'After adding bot to slot 3');
    
    // STEP 8: Player 2 joins room
    console.log('\n🎯 STEP 8: Player 2 >> join room');
    const roomCards = await page2.locator('.room-card').all();
    if (roomCards.length > 0) {
      // Find Player1's room
      for (const roomCard of roomCards) {
        const roomText = await roomCard.textContent();
        if (roomText.includes('Player1')) {
          await roomCard.click();
          console.log('✅ Player 2 clicked on Player1\'s room');
          break;
        }
      }
    }
    await sleep(2000);
    await logDetailedRoomState(page1, 8, 'After Player 2 joined (P1 view)');
    
    // STEP 9: Player 1 removes Player 2
    console.log('\n🎯 STEP 9: Player 1 >> remove Player 2');
    console.log('Expected: Remove Player2 from their slot');
    const playerCards9 = await page1.locator('.rp-playerCard').all();
    let player2Found = false;
    for (let i = 0; i < playerCards9.length; i++) {
      const card = playerCards9[i];
      const nameEl = await card.locator('.rp-playerName');
      if (await nameEl.count() > 0) {
        const name = await nameEl.textContent();
        if (name.includes('Player2')) {
          console.log(`Found Player2 in slot ${i + 1}`);
          const removeBtn = card.locator('button:has-text("Remove")');
          if (await removeBtn.isVisible()) {
            await removeBtn.click();
            console.log(`✅ Clicked Remove on Player2 in slot ${i + 1}`);
            player2Found = true;
            break;
          }
        }
      }
    }
    if (!player2Found) {
      console.log('⚠️ Player2 not found or not removable');
    }
    await sleep(1500);
    await logDetailedRoomState(page1, 9, 'After removing Player 2');
    
    // STEP 10: Player 1 removes bot 3
    console.log('\n🎯 STEP 10: Player 1 >> remove bot 3');
    console.log('Expected: Remove the bot that was added in step 7');
    const playerCards10 = await page1.locator('.rp-playerCard').all();
    let botFound10 = false;
    for (let i = 0; i < playerCards10.length; i++) {
      const card = playerCards10[i];
      const nameEl = await card.locator('.rp-playerName');
      if (await nameEl.count() > 0) {
        const name = await nameEl.textContent();
        if (name.includes('Bot') && !name.includes('Player')) {
          console.log(`Found ${name} in slot ${i + 1}`);
          const removeBtn = card.locator('button:has-text("Remove")');
          if (await removeBtn.isVisible()) {
            await removeBtn.click();
            console.log(`✅ Clicked Remove on ${name} in slot ${i + 1}`);
            botFound10 = true;
            break;
          }
        }
      }
    }
    if (!botFound10) {
      console.log('⚠️ No removable bot found');
    }
    await sleep(1500);
    await logDetailedRoomState(page1, 10, 'After removing bot 3');
    
    // STEP 11: Player 1 adds bot to slot 4
    console.log('\n🎯 STEP 11: Player 1 >> add bot 4');
    console.log('Expected: Add bot to slot 4');
    const playerCards11 = await page1.locator('.rp-playerCard').all();
    if (playerCards11.length > 3) {
      const slot4 = playerCards11[3]; // Slot 4 (index 3)
      const addBotBtn = slot4.locator('button:has-text("Add Bot")');
      if (await addBotBtn.isVisible()) {
        await addBotBtn.click();
        console.log('✅ Clicked Add Bot on slot 4');
      } else {
        console.log('⚠️ Slot 4 does not have Add Bot button');
      }
    } else {
      console.log('⚠️ Slot 4 not available');
    }
    await sleep(1500);
    await logDetailedRoomState(page1, 11, 'After adding bot to slot 4');
    
    // STEP 12: Player 1 adds bot to slot 3
    console.log('\n🎯 STEP 12: Player 1 >> add bot 3');
    console.log('Expected: Add bot to slot 3');
    const playerCards12 = await page1.locator('.rp-playerCard').all();
    if (playerCards12.length > 2) {
      const slot3 = playerCards12[2]; // Slot 3 (index 2)
      const addBotBtn = slot3.locator('button:has-text("Add Bot")');
      if (await addBotBtn.isVisible()) {
        await addBotBtn.click();
        console.log('✅ Clicked Add Bot on slot 3');
      } else {
        console.log('⚠️ Slot 3 does not have Add Bot button');
      }
    }
    await sleep(1500);
    await logDetailedRoomState(page1, 12, 'After adding bot to slot 3');
    
    // STEP 13: Player 1 adds bot to slot 2
    console.log('\n🎯 STEP 13: Player 1 >> add bot 2');
    console.log('Expected: Add bot to slot 2');
    const playerCards13 = await page1.locator('.rp-playerCard').all();
    if (playerCards13.length > 1) {
      const slot2 = playerCards13[1]; // Slot 2 (index 1)
      const addBotBtn = slot2.locator('button:has-text("Add Bot")');
      if (await addBotBtn.isVisible()) {
        await addBotBtn.click();
        console.log('✅ Clicked Add Bot on slot 2');
      } else {
        console.log('⚠️ Slot 2 does not have Add Bot button');
      }
    }
    await sleep(1500);
    await logDetailedRoomState(page1, 13, 'Final room state');
    
    // Summary
    console.log('\n' + '='.repeat(80));
    console.log('📊 TEST SEQUENCE COMPLETE - SUMMARY');
    console.log('='.repeat(80));
    console.log('Review the logs above to identify:');
    console.log('1. Did remove operations target the correct slots?');
    console.log('2. Did slots shift unexpectedly after removals?');
    console.log('3. Were the correct players/bots removed?');
    console.log('4. Did add operations fill the expected slots?');
    console.log('='.repeat(80));
    
    // Keep browser open for manual inspection
    console.log('\n⏸️ Browser will stay open for 30 seconds for inspection...');
    await sleep(30000);
    
  } catch (error) {
    console.error('❌ Test error:', error);
  } finally {
    await browser.close();
  }
}

// Run the test
testExactSequence().then(() => {
  console.log('\n✅ Test execution complete');
  process.exit(0);
}).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});