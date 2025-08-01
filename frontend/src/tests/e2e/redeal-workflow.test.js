/**
 * End-to-End Tests for Complete Redeal Decision Workflow
 * 
 * Bug ID: REDEAL-001
 * Testing: Full user workflow from game start to redeal decision
 */

import { test, expect } from '@playwright/test';

/**
 * E2E Test Configuration
 */
const TEST_CONFIG = {
  SERVER_URL: 'http://localhost:5050',
  TEST_PLAYER_NAME: 'E2ETestPlayer',
  DEALING_ANIMATION_TIMEOUT: 5000,
  NETWORK_TIMEOUT: 10000,
  REDEAL_DECISION_TIMEOUT: 15000,
};

test.describe('Redeal Decision Workflow E2E Tests', () => {
  
  test.beforeEach(async ({ page }) => {
    // Start with a clean browser state
    await page.goto(TEST_CONFIG.SERVER_URL);
    await page.waitForLoadState('networkidle');
  });

  test('REDEAL-001-E001: Complete redeal decision workflow - Accept redeal', async ({ page }) => {
    // Step 1: Enter lobby
    await page.fill('[data-testid="player-name-input"]', TEST_CONFIG.TEST_PLAYER_NAME);
    await page.click('[data-testid="enter-lobby-button"]');
    await page.waitForURL('**/lobby');
    
    // Step 2: Create and join room
    await page.click('[data-testid="create-room-button"]');
    await page.waitForURL('**/room/**');
    
    // Step 3: Start game
    await page.click('[data-testid="start-game-button"]');
    await page.waitForURL('**/game/**');
    
    // Step 4: Wait for preparation phase
    await expect(page.locator('h1')).toHaveText('Preparation Phase', { 
      timeout: TEST_CONFIG.NETWORK_TIMEOUT 
    });
    
    // Step 5: Wait for dealing animation to complete
    await page.waitForSelector('.dealing-container', { state: 'hidden', timeout: TEST_CONFIG.DEALING_ANIMATION_TIMEOUT });
    
    // Step 6: Check for weak hand detection and debug
    console.log('🔍 E2E: Checking for redeal decision UI...');
    
    // Add debug logging
    await page.evaluate(() => {
      console.log('🔍 E2E DEBUG: Current page state');
      console.log('- URL:', window.location.href);
      console.log('- Phase heading:', document.querySelector('h1')?.textContent);
      console.log('- Weak hand alert exists:', !!document.querySelector('.weak-hand-alert'));
      console.log('- Alert has show class:', document.querySelector('.weak-hand-alert')?.classList.contains('show'));
      console.log('- Redeal buttons count:', document.querySelectorAll('.alert-button').length);
    });
    
    // Step 7: Verify redeal decision UI appears (this is the main bug test)
    const weakHandAlert = page.locator('.weak-hand-alert.show');
    await expect(weakHandAlert).toBeVisible({ timeout: TEST_CONFIG.REDEAL_DECISION_TIMEOUT });
    
    // Step 8: Verify alert content
    await expect(page.locator('text=⚠️ Weak Hand Detected')).toBeVisible();
    await expect(page.locator('text=No piece greater than')).toBeVisible();
    await expect(page.locator('text=penalty if you redeal')).toBeVisible();
    
    // Step 9: Verify buttons are present and clickable
    const acceptButton = page.locator('button:has-text("Request Redeal")');
    const declineButton = page.locator('button:has-text("Keep Hand")');
    
    await expect(acceptButton).toBeVisible();
    await expect(declineButton).toBeVisible();
    await expect(acceptButton).not.toBeDisabled();
    await expect(declineButton).not.toBeDisabled();
    
    // Step 10: Click Accept Redeal
    await acceptButton.click();
    
    // Step 11: Verify redeal animation starts
    await expect(page.locator('text=Redealing Cards')).toBeVisible({ timeout: 3000 });
    
    // Step 12: Wait for redeal to complete and verify new hand
    await page.waitForSelector('.dealing-container', { state: 'hidden', timeout: TEST_CONFIG.DEALING_ANIMATION_TIMEOUT });
    
    // Step 13: Verify game continues to next phase
    await expect(page.locator('h1')).not.toHaveText('Preparation Phase', { timeout: TEST_CONFIG.NETWORK_TIMEOUT });
  });

  test('REDEAL-001-E002: Complete redeal decision workflow - Decline redeal', async ({ page }) => {
    // Follow same setup steps as E001
    await page.fill('[data-testid="player-name-input"]', TEST_CONFIG.TEST_PLAYER_NAME);
    await page.click('[data-testid="enter-lobby-button"]');
    await page.waitForURL('**/lobby');
    
    await page.click('[data-testid="create-room-button"]');
    await page.waitForURL('**/room/**');
    
    await page.click('[data-testid="start-game-button"]');
    await page.waitForURL('**/game/**');
    
    await expect(page.locator('h1')).toHaveText('Preparation Phase');
    await page.waitForSelector('.dealing-container', { state: 'hidden', timeout: TEST_CONFIG.DEALING_ANIMATION_TIMEOUT });
    
    // Wait for and verify redeal decision UI
    const weakHandAlert = page.locator('.weak-hand-alert.show');
    await expect(weakHandAlert).toBeVisible({ timeout: TEST_CONFIG.REDEAL_DECISION_TIMEOUT });
    
    // Click Decline Redeal
    const declineButton = page.locator('button:has-text("Keep Hand")');
    await declineButton.click();
    
    // Verify UI disappears and game continues
    await expect(weakHandAlert).not.toBeVisible({ timeout: 3000 });
    await expect(page.locator('h1')).not.toHaveText('Preparation Phase', { timeout: TEST_CONFIG.NETWORK_TIMEOUT });
  });

  test('REDEAL-001-E003: Multiplayer redeal decision - Sequential mode', async ({ page, context }) => {
    // This test requires multiple players, so we'll simulate with multiple browser contexts
    const player2Page = await context.newPage();
    
    try {
      // Player 1 setup
      await page.fill('[data-testid="player-name-input"]', 'Player1');
      await page.click('[data-testid="enter-lobby-button"]');
      await page.click('[data-testid="create-room-button"]');
      
      // Get room ID from URL
      const roomUrl = page.url();
      const roomId = roomUrl.split('/').pop();
      
      // Player 2 joins same room
      await player2Page.goto(TEST_CONFIG.SERVER_URL);
      await player2Page.fill('[data-testid="player-name-input"]', 'Player2');
      await player2Page.click('[data-testid="enter-lobby-button"]');
      await player2Page.fill('[data-testid="join-room-input"]', roomId);
      await player2Page.click('[data-testid="join-room-button"]');
      
      // Start game from Player 1
      await page.click('[data-testid="start-game-button"]');
      
      // Both players should see preparation phase
      await expect(page.locator('h1')).toHaveText('Preparation Phase');
      await expect(player2Page.locator('h1')).toHaveText('Preparation Phase');
      
      // Wait for dealing animations on both pages
      await Promise.all([
        page.waitForSelector('.dealing-container', { state: 'hidden', timeout: TEST_CONFIG.DEALING_ANIMATION_TIMEOUT }),
        player2Page.waitForSelector('.dealing-container', { state: 'hidden', timeout: TEST_CONFIG.DEALING_ANIMATION_TIMEOUT })
      ]);
      
      // Check which player(s) have weak hands and can see redeal UI
      const player1HasRedealUI = await page.locator('.weak-hand-alert.show').isVisible();
      const player2HasRedealUI = await player2Page.locator('.weak-hand-alert.show').isVisible();
      
      console.log('🔍 E2E Multiplayer: Player 1 has redeal UI:', player1HasRedealUI);
      console.log('🔍 E2E Multiplayer: Player 2 has redeal UI:', player2HasRedealUI);
      
      // At least one player should have a weak hand in a typical game
      expect(player1HasRedealUI || player2HasRedealUI).toBe(true);
      
      // If Player 1 has redeal UI, test their decision
      if (player1HasRedealUI) {
        await page.locator('button:has-text("Keep Hand")').click();
        await expect(page.locator('.weak-hand-alert')).not.toBeVisible();
      }
      
      // If Player 2 has redeal UI, test their decision
      if (player2HasRedealUI) {
        await player2Page.locator('button:has-text("Keep Hand")').click();
        await expect(player2Page.locator('.weak-hand-alert')).not.toBeVisible();
      }
      
    } finally {
      await player2Page.close();
    }
  });

  test('REDEAL-001-E004: Debug data collection - Console logs and network events', async ({ page }) => {
    // Enable console logging
    page.on('console', (msg) => {
      if (msg.text().includes('weak_hands_found') || 
          msg.text().includes('isMyHandWeak') || 
          msg.text().includes('isMyDecision') ||
          msg.text().includes('handleWeakHandsFound')) {
        console.log('🔍 E2E Console:', msg.text());
      }
    });
    
    // Monitor network events
    page.on('websocket', (ws) => {
      ws.on('framereceived', (event) => {
        const data = event.payload;
        if (data.includes('weak_hands_found') || data.includes('redeal')) {
          console.log('🔍 E2E WebSocket Received:', data);
        }
      });
      
      ws.on('framesent', (event) => {
        const data = event.payload;
        if (data.includes('redeal')) {
          console.log('🔍 E2E WebSocket Sent:', data);
        }
      });
    });
    
    // Execute test workflow
    await page.fill('[data-testid="player-name-input"]', TEST_CONFIG.TEST_PLAYER_NAME);
    await page.click('[data-testid="enter-lobby-button"]');
    await page.click('[data-testid="create-room-button"]');
    await page.click('[data-testid="start-game-button"]');
    
    await expect(page.locator('h1')).toHaveText('Preparation Phase');
    
    // Inject debug logging into the page
    await page.evaluate(() => {
      // Override handleWeakHandsFound to add debug logging
      if (window.gameService || window.GameService) {
        const service = window.gameService || window.GameService;
        const originalHandler = service.handleWeakHandsFound;
        
        if (originalHandler) {
          service.handleWeakHandsFound = function(state, data) {
            console.log('🔍 E2E DEBUG: handleWeakHandsFound called');
            console.log('🔍 E2E DEBUG: Input state:', {
              phase: state.phase,
              playerName: state.playerName,
              isMyHandWeak: state.isMyHandWeak,
              isMyDecision: state.isMyDecision,
              myHandLength: state.myHand?.length
            });
            console.log('🔍 E2E DEBUG: Input data:', data);
            
            const result = originalHandler.call(this, state, data);
            
            console.log('🔍 E2E DEBUG: Output state:', {
              phase: result.phase,
              playerName: result.playerName,
              isMyHandWeak: result.isMyHandWeak,
              isMyDecision: result.isMyDecision,
              weakHands: result.weakHands,
              currentWeakPlayer: result.currentWeakPlayer
            });
            
            return result;
          };
        }
      }
      
      console.log('🔍 E2E DEBUG: Debug logging injected');
    });
    
    await page.waitForSelector('.dealing-container', { state: 'hidden', timeout: TEST_CONFIG.DEALING_ANIMATION_TIMEOUT });
    
    // Collect final state data
    const finalState = await page.evaluate(() => {
      const contentSection = document.querySelector('.content-section');
      const weakHandAlert = document.querySelector('.weak-hand-alert');
      
      return {
        url: window.location.href,
        phaseHeading: document.querySelector('h1')?.textContent,
        contentSectionHTML: contentSection?.innerHTML?.substring(0, 200),
        weakHandAlertExists: !!weakHandAlert,
        weakHandAlertVisible: weakHandAlert?.offsetParent !== null,
        weakHandAlertClasses: weakHandAlert?.className,
        redealButtonsCount: document.querySelectorAll('.alert-button').length,
        dealingAnimationVisible: !!document.querySelector('.dealing-container'),
      };
    });
    
    console.log('🔍 E2E FINAL STATE:', JSON.stringify(finalState, null, 2));
    
    // This test is primarily for data collection, so we just verify basic functionality
    expect(finalState.phaseHeading).toBe('Preparation Phase');
  });

  test('REDEAL-001-E005: Performance test - Redeal decision response time', async ({ page }) => {
    const performanceMarks = [];
    
    // Track performance milestones
    await page.addInitScript(() => {
      window.performanceMarks = [];
      window.markPerformance = (label) => {
        const mark = { label, timestamp: performance.now() };
        window.performanceMarks.push(mark);
        console.log(`🔍 E2E Performance: ${label} at ${mark.timestamp}ms`);
      };
    });
    
    // Standard setup
    await page.fill('[data-testid="player-name-input"]', TEST_CONFIG.TEST_PLAYER_NAME);
    await page.click('[data-testid="enter-lobby-button"]');
    await page.click('[data-testid="create-room-button"]');
    
    await page.evaluate(() => window.markPerformance('Game Start'));
    await page.click('[data-testid="start-game-button"]');
    
    await page.evaluate(() => window.markPerformance('Preparation Phase Reached'));
    await expect(page.locator('h1')).toHaveText('Preparation Phase');
    
    await page.evaluate(() => window.markPerformance('Dealing Animation Complete'));
    await page.waitForSelector('.dealing-container', { state: 'hidden', timeout: TEST_CONFIG.DEALING_ANIMATION_TIMEOUT });
    
    // Measure time to redeal UI appearance
    const redealUIAppeared = await page.locator('.weak-hand-alert.show').isVisible();
    if (redealUIAppeared) {
      await page.evaluate(() => window.markPerformance('Redeal UI Appeared'));
      
      // Measure interaction response time
      const startInteraction = Date.now();
      await page.locator('button:has-text("Keep Hand")').click();
      const endInteraction = Date.now();
      
      console.log(`🔍 E2E Performance: Button interaction took ${endInteraction - startInteraction}ms`);
    }
    
    // Collect all performance data
    const allMarks = await page.evaluate(() => window.performanceMarks);
    console.log('🔍 E2E Performance Summary:', allMarks);
    
    // Verify reasonable performance (redeal UI should appear within 2 seconds after dealing)
    if (allMarks.length >= 3) {
      const dealingComplete = allMarks.find(m => m.label === 'Dealing Animation Complete');
      const redealUIAppear = allMarks.find(m => m.label === 'Redeal UI Appeared');
      
      if (dealingComplete && redealUIAppear) {
        const timeDiff = redealUIAppear.timestamp - dealingComplete.timestamp;
        console.log(`🔍 E2E Performance: Redeal UI appeared ${timeDiff}ms after dealing`);
        expect(timeDiff).toBeLessThan(2000); // Should appear within 2 seconds
      }
    }
  });
});

// E2E Test Utilities
export const RedealE2ETestUtils = {
  /**
   * Setup a complete game session up to preparation phase
   */
  setupGameToPreparation: async (page, playerName = 'TestPlayer') => {
    await page.goto(TEST_CONFIG.SERVER_URL);
    await page.fill('[data-testid="player-name-input"]', playerName);
    await page.click('[data-testid="enter-lobby-button"]');
    await page.waitForURL('**/lobby');
    
    await page.click('[data-testid="create-room-button"]');
    await page.waitForURL('**/room/**');
    
    await page.click('[data-testid="start-game-button"]');
    await page.waitForURL('**/game/**');
    
    await expect(page.locator('h1')).toHaveText('Preparation Phase');
    await page.waitForSelector('.dealing-container', { state: 'hidden', timeout: TEST_CONFIG.DEALING_ANIMATION_TIMEOUT });
  },

  /**
   * Wait for and verify redeal UI appears
   */
  waitForRedealUI: async (page, timeout = TEST_CONFIG.REDEAL_DECISION_TIMEOUT) => {
    const weakHandAlert = page.locator('.weak-hand-alert.show');
    await expect(weakHandAlert).toBeVisible({ timeout });
    
    await expect(page.locator('text=⚠️ Weak Hand Detected')).toBeVisible();
    await expect(page.locator('button:has-text("Request Redeal")')).toBeVisible();
    await expect(page.locator('button:has-text("Keep Hand")')).toBeVisible();
    
    return weakHandAlert;
  },

  /**
   * Collect debug information from the page
   */
  collectDebugInfo: async (page) => {
    return await page.evaluate(() => {
      const contentSection = document.querySelector('.content-section');
      const weakHandAlert = document.querySelector('.weak-hand-alert');
      
      return {
        timestamp: new Date().toISOString(),
        url: window.location.href,
        phaseHeading: document.querySelector('h1')?.textContent,
        weakHandAlert: {
          exists: !!weakHandAlert,
          visible: weakHandAlert?.offsetParent !== null,
          classes: weakHandAlert?.className,
          hasShowClass: weakHandAlert?.classList.contains('show'),
        },
        buttons: {
          acceptButton: !!document.querySelector('button:has-text("Request Redeal")'),
          declineButton: !!document.querySelector('button:has-text("Keep Hand")'),
          totalAlertButtons: document.querySelectorAll('.alert-button').length,
        },
        animations: {
          dealingVisible: !!document.querySelector('.dealing-container'),
          redealingVisible: document.querySelector('.dealing-message')?.textContent === 'Redealing Cards',
        },
        contentSection: {
          exists: !!contentSection,
          innerHTML: contentSection?.innerHTML?.substring(0, 300) + '...',
        }
      };
    });
  },
};