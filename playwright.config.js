/**
 * Playwright Configuration for Lobby Auto-Update Bug Investigation
 */

module.exports = {
  testDir: '.',
  timeout: 60000, // 1 minute timeout for each test
  fullyParallel: false, // Run tests sequentially to avoid conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker to avoid WebSocket conflicts
  reporter: [
    ['html'],
    ['list'],
    ['json', { outputFile: 'test-results.json' }]
  ],
  use: {
    baseURL: 'http://localhost:5050',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Increase timeouts for WebSocket operations
    actionTimeout: 10000,
    navigationTimeout: 10000,
  },
  projects: [
    {
      name: 'chromium-lobby-test',
      use: { 
        ...require('@playwright/test').devices['Desktop Chrome'],
        // Enable console logs
        launchOptions: {
          args: ['--enable-logging', '--v=1']
        }
      },
    },
  ],
  // Ensure the application is running before tests
  webServer: [
    {
      command: 'echo "Please ensure the application is running on http://localhost:5050"',
      port: 5050,
      timeout: 5000,
      reuseExistingServer: true
    }
  ],
};