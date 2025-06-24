import './test-setup.js';
import { execSync } from 'child_process';
import globPkg from 'glob';
import path from 'path';

const { glob } = globPkg;

// Simple test runner for React components
class ReactTestRunner {
  constructor() {
    this.tests = [];
    this.results = {
      total: 0,
      passed: 0,
      failed: 0,
      failures: []
    };
  }

  async findTests() {
    const testFiles = await glob('src/tests/**/*.test.js', { cwd: process.cwd() });
    return testFiles.map(file => path.resolve(file));
  }

  async runTest(testFile) {
    try {
      console.log(`\n📝 Running tests in: ${path.basename(testFile)}`);
      
      // Import and run the test file
      const testModule = await import(testFile);
      
      // This is a simplified test runner - in production you'd use Jest or Vitest
      console.log(`   ✅ Test file loaded successfully`);
      
      return { success: true, file: testFile };
    } catch (error) {
      console.log(`   ❌ Test failed: ${error.message}`);
      return { success: false, file: testFile, error: error.message };
    }
  }

  async runAllTests() {
    console.log('🧪 Starting React Component Tests\n');
    
    const testFiles = await this.findTests();
    
    if (testFiles.length === 0) {
      console.log('No test files found in src/tests/');
      return;
    }

    console.log(`Found ${testFiles.length} test files:\n`);

    for (const testFile of testFiles) {
      const result = await this.runTest(testFile);
      this.results.total++;
      
      if (result.success) {
        this.results.passed++;
      } else {
        this.results.failed++;
        this.results.failures.push(result);
      }
    }

    this.printSummary();
  }

  printSummary() {
    console.log('\n' + '='.repeat(50));
    console.log('📊 Test Summary');
    console.log('='.repeat(50));
    console.log(`Total Tests: ${this.results.total}`);
    console.log(`✅ Passed: ${this.results.passed}`);
    console.log(`❌ Failed: ${this.results.failed}`);
    
    if (this.results.failures.length > 0) {
      console.log('\n💥 Failures:');
      this.results.failures.forEach(failure => {
        console.log(`   ${path.basename(failure.file)}: ${failure.error}`);
      });
    }
    
    const successRate = ((this.results.passed / this.results.total) * 100).toFixed(1);
    console.log(`\n🎯 Success Rate: ${successRate}%`);
    
    if (this.results.failed === 0) {
      console.log('\n🎉 All tests passed!');
    }
  }
}

// Mock Jest globals for our simple test runner
global.jest = {
  fn: () => {
    const mockFn = function(...args) {
      mockFn.calls.push(args);
      if (mockFn.mockReturnValue !== undefined) {
        return mockFn.mockReturnValue;
      }
      if (mockFn.mockImplementation) {
        return mockFn.mockImplementation(...args);
      }
    };
    mockFn.calls = [];
    mockFn.mockReturnValue = undefined;
    mockFn.mockImplementation = undefined;
    mockFn.mockClear = () => { mockFn.calls = []; };
    return mockFn;
  },
  clearAllMocks: () => {},
  requireActual: (moduleName) => {
    // Simple mock for react-router-dom actual
    if (moduleName === 'react-router-dom') {
      return {
        BrowserRouter: ({ children }) => children,
        useNavigate: () => () => {}
      };
    }
    return {};
  }
};

global.describe = (name, fn) => {
  console.log(`\n  📋 ${name}`);
  fn();
};

global.test = (name, fn) => {
  try {
    fn();
    console.log(`    ✅ ${name}`);
  } catch (error) {
    console.log(`    ❌ ${name}: ${error.message}`);
    throw error;
  }
};

global.expect = (actual) => ({
  toBe: (expected) => {
    if (actual !== expected) {
      throw new Error(`Expected ${actual} to be ${expected}`);
    }
  },
  toHaveBeenCalled: () => {
    if (!actual.calls || actual.calls.length === 0) {
      throw new Error('Expected function to have been called');
    }
  },
  toHaveBeenCalledWith: (expected) => {
    if (!actual.calls || !actual.calls.some(call => JSON.stringify(call) === JSON.stringify([expected]))) {
      throw new Error(`Expected function to have been called with ${expected}`);
    }
  },
  toHaveBeenCalledTimes: (times) => {
    if (!actual.calls || actual.calls.length !== times) {
      throw new Error(`Expected function to have been called ${times} times, but was called ${actual.calls?.length || 0} times`);
    }
  }
});

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const runner = new ReactTestRunner();
  runner.runAllTests().catch(console.error);
}