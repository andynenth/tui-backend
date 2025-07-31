/**
 * 🚀 **Global Test Setup - PlaywrightTester Agent**
 * 
 * Prepares the test environment for comprehensive game start flow testing
 */

const fs = require('fs').promises;
const path = require('path');

async function globalSetup(config) {
  console.log('🚀 === PLAYWRIGHT TEST SUITE SETUP ===');
  
  const setupStart = Date.now();
  
  try {
    // Create all necessary test directories
    const directories = [
      'test-results',
      'test-results/game-start-flow',
      'test-results/websocket-validation', 
      'test-results/regression-tests',
      'test-screenshots'
    ];
    
    for (const dir of directories) {
      await fs.mkdir(dir, { recursive: true });
      console.log(`📁 Created directory: ${dir}`);
    }
    
    // Initialize test session metadata
    const sessionMetadata = {
      testSuiteStart: new Date().toISOString(),
      setupDuration: Date.now() - setupStart,
      playwrightVersion: require('@playwright/test/package.json').version,
      nodeVersion: process.version,
      testEnvironment: {
        baseURL: 'http://localhost:5050',
        timeout: config.timeout,
        workers: config.workers
      },
      testCategories: [
        'game-start-flow',
        'websocket-validation',
        'regression-tests'
      ],
      swarmCoordination: {
        agent: 'PlaywrightTester',
        role: 'Bug reproduction and fix validation',
        memoryEnabled: true
      }
    };
    
    // Save session metadata
    await fs.writeFile(
      'test-results/session-metadata.json',
      JSON.stringify(sessionMetadata, null, 2)
    );
    
    console.log('📊 Test session metadata saved');
    console.log(`⏱️  Setup completed in ${Date.now() - setupStart}ms`);
    console.log('🎯 Ready for game start flow testing');
    
    return sessionMetadata;
    
  } catch (error) {
    console.error('❌ Global setup failed:', error);
    throw error;
  }
}

module.exports = globalSetup;