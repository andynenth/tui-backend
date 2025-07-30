/**
 * Comprehensive Playwright test for bot slot management issues
 * 
 * Issues to investigate:
 * 1. Lobby doesn't update when host removes bot (but updates when adding bot)
 * 2. Add bot should target specific slot clicked, not random slot
 * 3. Remove bot should target specific slot clicked, not wrong slot
 */

const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:5050';
const HOST_NAME = 'TestHost';
const OBSERVER_NAME = 'LobbyObserver';

// Evidence collection for debugging
const evidenceDir = './bot_slot_evidence';
const fs = require('fs');
if (!fs.existsSync(evidenceDir)) {
    fs.mkdirSync(evidenceDir, { recursive: true });
}

async function captureEvidence(page, filename, description) {
    const timestamp = Date.now();
    const screenshotPath = `${evidenceDir}/${filename}_${timestamp}.png`;
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`📸 Evidence captured: ${filename} - ${description}`);
    return screenshotPath;
}

async function captureDetailedRoomState(page, testId, stepDescription) {
    console.log(`📊 [${testId}] Capturing room state: ${stepDescription}`);
    
    // Take screenshot
    await captureEvidence(page, `${testId}_${stepDescription.replace(/\s+/g, '_')}`, stepDescription);
    
    // Get room data from the page
    const roomState = await page.evaluate(() => {
        // Look for room data in various places
        const roomData = {};
        
        // Check if there are player cards
        const playerCards = document.querySelectorAll('.rp-playerCard');
        roomData.playerCards = Array.from(playerCards).map((card, index) => {
            const nameElement = card.querySelector('.rp-playerName');
            const hostBadge = card.querySelector('.rp-hostBadge');
            const addBotBtn = card.querySelector('.rp-addBotBtn');
            const removeBtn = card.querySelector('.rp-removeBtn');
            
            return {
                position: index + 1,
                name: nameElement ? nameElement.textContent.trim() : null,
                isHost: !!hostBadge,
                isEmpty: nameElement ? nameElement.textContent.trim() === 'Waiting...' : true,
                hasAddBotButton: !!addBotBtn,
                hasRemoveButton: !!removeBtn,
                cardClasses: card.className
            };
        });
        
        // Check player count
        const playerCountElement = document.querySelector('.rp-playerCount');
        roomData.playerCount = playerCountElement ? playerCountElement.textContent.trim() : 'unknown';
        
        // Check room status
        const roomStatusElement = document.querySelector('.rp-roomStatus');
        roomData.roomStatus = roomStatusElement ? roomStatusElement.textContent.trim() : 'unknown';
        
        return roomData;
    });
    
    console.log(`📊 [${testId}] Room state captured:`, JSON.stringify(roomState, null, 2));
    return roomState;
}

async function captureLobbyState(page, testId, stepDescription) {
    console.log(`🏛️ [${testId}] Capturing lobby state: ${stepDescription}`);
    
    // Take screenshot
    await captureEvidence(page, `${testId}_lobby_${stepDescription.replace(/\s+/g, '_')}`, `Lobby: ${stepDescription}`);
    
    // Get lobby room list
    const lobbyState = await page.evaluate(() => {
        const roomCards = document.querySelectorAll('.room-card, .lobby-room-card, [class*="room"]');
        const rooms = Array.from(roomCards).map((card, index) => {
            const nameElement = card.querySelector('[class*="name"], [class*="host"], h3, .room-title');
            const playersElement = card.querySelector('[class*="player"], [class*="count"]');
            
            return {
                index,
                name: nameElement ? nameElement.textContent.trim() : 'Unknown',
                players: playersElement ? playersElement.textContent.trim() : 'Unknown',
                cardText: card.textContent.trim(),
                cardClasses: card.className
            };
        });
        
        return {
            totalRooms: rooms.length,
            rooms: rooms,
            pageTitle: document.title,
            currentUrl: window.location.href
        };
    });
    
    console.log(`🏛️ [${testId}] Lobby state captured:`, JSON.stringify(lobbyState, null, 2));
    return lobbyState;
}

async function waitForWebSocketMessage(page, eventType, timeout = 5000) {
    console.log(`🔌 Waiting for WebSocket event: ${eventType}`);
    
    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
            reject(new Error(`WebSocket event ${eventType} not received within ${timeout}ms`));
        }, timeout);
        
        const handler = (event) => {
            if (event.detail && event.detail.event === eventType) {
                clearTimeout(timer);
                console.log(`🔌 Received WebSocket event: ${eventType}`, event.detail);
                resolve(event.detail);
            }
        };
        
        page.on('websocket', ws => {
            ws.on('framereceived', frame => {
                try {
                    const data = JSON.parse(frame.payload);
                    if (data.event === eventType) {
                        clearTimeout(timer);
                        console.log(`🔌 Received WebSocket event: ${eventType}`, data);
                        resolve(data);
                    }
                } catch (e) {
                    // Ignore parsing errors
                }
            });
        });
    });
}

async function testBotSlotManagement() {
    console.log('🚀 Starting Bot Slot Management Investigation');
    
    // Launch two browser contexts for concurrent testing
    const browser = await chromium.launch({ 
        headless: false,
        slowMo: 1000  // Slow down for visibility
    });
    
    const hostContext = await browser.newContext();
    const observerContext = await browser.newContext();
    
    const hostPage = await hostContext.newPage();
    const observerPage = await observerContext.newPage();
    
    try {
        console.log('🎭 Setting up Host and Observer pages...');
        
        // Setup host player
        await hostPage.goto(BASE_URL);
        await hostPage.fill('input[type="text"]', HOST_NAME);
        await hostPage.click('button:has-text("Enter Lobby")');
        await hostPage.waitForSelector('.lobby-container', { timeout: 10000 });
        console.log('✅ Host entered lobby');
        
        // Setup observer (for lobby monitoring)
        await observerPage.goto(BASE_URL);
        await observerPage.fill('input[type="text"]', OBSERVER_NAME);
        await observerPage.click('button:has-text("Enter Lobby")');
        await observerPage.waitForSelector('.lobby-container', { timeout: 10000 });
        console.log('✅ Observer entered lobby');
        
        // Capture initial lobby state
        await captureLobbyState(observerPage, 'SETUP', 'initial_empty_lobby');
        
        // Host creates room
        console.log('🏠 Host creating room...');
        await hostPage.click('button:has-text("Create Room")');
        await hostPage.waitForSelector('.rp-gameContainer', { timeout: 10000 });
        console.log('✅ Host created room and entered room page');
        
        // Wait for room to appear in lobby
        await new Promise(resolve => setTimeout(resolve, 2000));
        await captureLobbyState(observerPage, 'SETUP', 'after_room_created');
        
        // Capture initial room state (should be empty except for host)
        const initialRoomState = await captureDetailedRoomState(hostPage, 'SETUP', 'initial_room_state');
        
        console.log('\n🧪 TEST SETUP COMPLETE - Starting Bot Slot Management Tests\n');
        
        // ==============================================
        // TEST 1: Lobby update issue with bot removal
        // ==============================================
        console.log('🧪 TEST 1: Lobby update when host removes bot');
        
        // Step 1: Add bots to all empty slots to populate room
        console.log('🤖 Adding bots to populate room...');
        
        for (let slotNumber = 2; slotNumber <= 4; slotNumber++) {
            console.log(`🤖 Adding bot to slot ${slotNumber}...`);
            
            // Find and click the "Add Bot" button for this slot
            const addBotButton = await hostPage.waitForSelector(
                `.rp-position-${slotNumber} .rp-addBotBtn`, 
                { timeout: 5000 }
            );
            await addBotButton.click();
            
            // Wait for bot to be added
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Capture state after each bot addition
            await captureDetailedRoomState(hostPage, 'TEST1', `after_adding_bot_slot_${slotNumber}`);
            await captureLobbyState(observerPage, 'TEST1', `lobby_after_adding_bot_slot_${slotNumber}`);
        }
        
        // Step 2: Remove one bot and check if lobby updates
        console.log('🗑️ Removing bot from slot 3...');
        const removeBotButton = await hostPage.waitForSelector(
            '.rp-position-3 .rp-removeBtn',
            { timeout: 5000 }
        );
        
        // Capture state before removal
        await captureDetailedRoomState(hostPage, 'TEST1', 'before_removing_bot_slot_3');
        await captureLobbyState(observerPage, 'TEST1', 'lobby_before_removing_bot_slot_3');
        
        await removeBotButton.click();
        
        // Wait for removal to process
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Capture state after removal
        await captureDetailedRoomState(hostPage, 'TEST1', 'after_removing_bot_slot_3');
        await captureLobbyState(observerPage, 'TEST1', 'lobby_after_removing_bot_slot_3');
        
        console.log('✅ TEST 1 COMPLETED: Bot removal lobby update test');
        
        // ==============================================
        // TEST 2: Add bot to specific slot
        // ==============================================
        console.log('\n🧪 TEST 2: Add bot to specific slot (slot 3)');
        
        // Remove all bots first
        console.log('🗑️ Removing all bots to reset state...');
        for (let slotNumber = 2; slotNumber <= 4; slotNumber++) {
            try {
                const removeBtn = await hostPage.waitForSelector(
                    `.rp-position-${slotNumber} .rp-removeBtn`,
                    { timeout: 2000 }
                );
                if (removeBtn) {
                    await removeBtn.click();
                    await new Promise(resolve => setTimeout(resolve, 1500));
                }
            } catch (e) {
                console.log(`No bot to remove in slot ${slotNumber}`);
            }
        }
        
        // Capture empty room state
        await captureDetailedRoomState(hostPage, 'TEST2', 'all_bots_removed');
        
        // Click "Add Bot" specifically on slot 3
        console.log('🤖 Clicking "Add Bot" on slot 3...');
        const slot3AddButton = await hostPage.waitForSelector(
            '.rp-position-3 .rp-addBotBtn',
            { timeout: 5000 }
        );
        await slot3AddButton.click();
        
        // Wait for bot to be added
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Capture result - bot should be in slot 3
        const slot3Result = await captureDetailedRoomState(hostPage, 'TEST2', 'after_adding_bot_to_slot_3');
        
        // Check if bot was added to slot 3 specifically
        const slot3HasBot = slot3Result.playerCards[2] && slot3Result.playerCards[2].name !== 'Waiting...';
        const botInWrongSlot = slot3Result.playerCards.find((card, index) => 
            index !== 2 && card.name !== 'Waiting...' && card.name !== HOST_NAME
        );
        
        console.log(`🧪 TEST 2 RESULT: Bot in slot 3: ${slot3HasBot}, Bot in wrong slot: ${!!botInWrongSlot}`);
        console.log('✅ TEST 2 COMPLETED: Add bot to specific slot test');
        
        // ==============================================
        // TEST 3: Remove bot from specific slot
        // ==============================================
        console.log('\n🧪 TEST 3: Remove bot from specific slot');
        
        // Add bots to slots 2, 3, and 4 for testing
        console.log('🤖 Adding bots to slots 2, 3, and 4...');
        for (let slotNumber = 2; slotNumber <= 4; slotNumber++) {
            try {
                const addButton = await hostPage.waitForSelector(
                    `.rp-position-${slotNumber} .rp-addBotBtn`,
                    { timeout: 2000 }
                );
                if (addButton) {
                    await addButton.click();
                    await new Promise(resolve => setTimeout(resolve, 1500));
                }
            } catch (e) {
                console.log(`Bot already exists in slot ${slotNumber}`);
            }
        }
        
        // Capture state with all bots
        const beforeRemovalState = await captureDetailedRoomState(hostPage, 'TEST3', 'before_removing_bot_from_slot_3');
        console.log('🧪 Before removal - bots in positions:', 
            beforeRemovalState.playerCards.map((card, i) => ({
                position: i + 1,
                hasBot: card.name !== 'Waiting...' && card.name !== HOST_NAME
            }))
        );
        
        // Click remove button specifically on slot 3
        console.log('🗑️ Clicking "Remove" on slot 3...');
        const slot3RemoveButton = await hostPage.waitForSelector(
            '.rp-position-3 .rp-removeBtn',
            { timeout: 5000 }
        );
        await slot3RemoveButton.click();
        
        // Wait for removal to process
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // Capture result
        const afterRemovalState = await captureDetailualRoomState(hostPage, 'TEST3', 'after_removing_bot_from_slot_3');
        console.log('🧪 After removal - bots in positions:', 
            afterRemovalState.playerCards.map((card, i) => ({
                position: i + 1,
                hasBot: card.name !== 'Waiting...' && card.name !== HOST_NAME
            }))
        );
        
        // Check if slot 3 is now empty and other slots still have bots
        const slot3IsEmpty = afterRemovalState.playerCards[2].name === 'Waiting...';
        const slot2StillHasBot = afterRemovalState.playerCards[1].name !== 'Waiting...' && 
                                afterRemovalState.playerCards[1].name !== HOST_NAME;
        const slot4StillHasBot = afterRemovalState.playerCards[3].name !== 'Waiting...' && 
                                afterRemovalState.playerCards[3].name !== HOST_NAME;
        
        console.log(`🧪 TEST 3 RESULT:`);
        console.log(`  - Slot 3 is empty: ${slot3IsEmpty}`);
        console.log(`  - Slot 2 still has bot: ${slot2StillHasBot}`);
        console.log(`  - Slot 4 still has bot: ${slot4StillHasBot}`);
        
        console.log('✅ TEST 3 COMPLETED: Remove bot from specific slot test');
        
        // ==============================================
        // SUMMARY REPORT
        // ==============================================
        console.log('\n📋 BOT SLOT MANAGEMENT INVESTIGATION SUMMARY');
        console.log('==========================================');
        
        console.log('\n🧪 Issue 1: Lobby update when removing bot');
        console.log('   - Need to compare lobby states before/after bot removal');
        console.log('   - Check if lobby room count changes appropriately');
        
        console.log('\n🧪 Issue 2: Add bot to specific slot');
        console.log(`   - Bot added to slot 3 as requested: ${slot3HasBot}`);
        console.log(`   - Bot incorrectly added to wrong slot: ${!!botInWrongSlot}`);
        
        console.log('\n🧪 Issue 3: Remove bot from specific slot');
        console.log(`   - Slot 3 correctly emptied: ${slot3IsEmpty}`);
        console.log(`   - Other slots preserved: Slot 2 = ${slot2StillHasBot}, Slot 4 = ${slot4StillHasBot}`);
        
        console.log('\n📸 Evidence collected in:', evidenceDir);
        console.log('✅ Investigation completed successfully');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
        // Capture error evidence
        await captureEvidence(hostPage, 'ERROR_host_page', 'Error state');
        await captureEvidence(observerPage, 'ERROR_observer_page', 'Error state');
        throw error;
    } finally {
        await browser.close();
    }
}

// Fix typo in function name
async function captureDetailualRoomState(page, testId, stepDescription) {
    return await captureDetailedRoomState(page, testId, stepDescription);
}

// Run the test
testBotSlotManagement().catch(console.error);