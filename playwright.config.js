/**
 * 🧪 **Playwright Configuration - Game Start Flow Testing Suite**
 * 
 * PlaywrightTester Agent Configuration
 * 
 * Test Categories:
 * - Game Start Flow (Primary bug reproduction & fix validation)
 * - WebSocket Validation (Connection stability & event validation)
 * - Regression Tests (Prevent future regressions)
 */

module.exports = {
  testDir: './tests/playwright',
  timeout: 90000, // 1.5 minute timeout for comprehensive tests
  fullyParallel: false, // Sequential to avoid WebSocket conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1, // Retry once locally for flaky WebSocket tests
  workers: 1, // Single worker to avoid conflicts
  
  // Enhanced reporting for swarm coordination
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
    ['json', { outputFile: 'test-results/test-results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],
  
  use: {
    baseURL: 'http://localhost:5050',
    trace: 'retain-on-failure', // Enhanced tracing
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Optimized timeouts for game testing
    actionTimeout: 15000,       // Increased for bot operations
    navigationTimeout: 15000,   // Increased for game transitions
    
    // Enhanced browser context
    contextOptions: {
      recordVideo: {
        mode: 'retain-on-failure',
        size: { width: 1280, height: 720 }
      }
    }
  },
  
  projects: [
    // Primary browser for comprehensive testing
    {
      name: 'chromium-game-tests',
      use: { 
        ...require('@playwright/test').devices['Desktop Chrome'],
        launchOptions: {
          args: [
            '--enable-logging',
            '--v=1',
            '--disable-web-security', // For WebSocket testing
            '--disable-features=VizDisplayCompositor'
          ]
        },
        // Enhanced browser context for game testing
        contextOptions: {
          permissions: ['clipboard-read', 'clipboard-write'],
          recordHar: { path: 'test-results/network-trace.har' }
        }
      },
      testMatch: ['**/game-start-flow.spec.js', '**/websocket-validation.spec.js']
    },
    
    // Regression testing project
    {
      name: 'regression-tests',
      use: { 
        ...require('@playwright/test').devices['Desktop Chrome'],
        launchOptions: {
          args: ['--enable-logging', '--disable-web-security']
        }
      },
      testMatch: ['**/regression-tests.spec.js']
    },
    
    // Legacy test compatibility
    {
      name: 'legacy-compatibility',
      use: { 
        ...require('@playwright/test').devices['Desktop Chrome'],
        launchOptions: {
          args: ['--enable-logging', '--v=1']
        }
      },
      testMatch: ['**/test_lobby_game_transition.spec.js']
    }
  ],
  
  // Application server configuration
  webServer: [
    {
      command: 'echo "🚀 Ensure the game server is running on http://localhost:5050"',
      port: 5050,
      timeout: 10000,
      reuseExistingServer: true
    }
  ],
  
  // Global test setup
  globalSetup: require.resolve('./tests/playwright/global-setup.js'),
  globalTeardown: require.resolve('./tests/playwright/global-teardown.js'),
  
  // Output directories
  outputDir: 'test-results/',
  
  // Expect configuration for enhanced assertions
  expect: {
    timeout: 10000,
    toHaveScreenshot: { threshold: 0.3 },
    toMatchSnapshot: { threshold: 0.3 }
  }
};