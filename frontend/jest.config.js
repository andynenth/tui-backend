export default {
  // Use jsdom environment for React testing
  testEnvironment: 'jsdom',

  // Setup files to run before tests
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // Module name mapper for CSS and static assets
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/__mocks__/fileMock.js',
    // Map TypeScript service files to JavaScript mocks
    '^../GameService$': '<rootDir>/src/services/__mocks__/GameService.js',
    '^../NetworkService$': '<rootDir>/src/services/__mocks__/NetworkService.js',
  },

  // Transform files with babel-jest
  transform: {
    '^.+\\.(js|jsx)$': [
      'babel-jest',
      {
        presets: [
          ['@babel/preset-env', { targets: { node: 'current' } }],
          ['@babel/preset-react', { runtime: 'automatic' }],
        ],
      },
    ],
    // Don't transform TypeScript files - they'll be imported as modules
    '^.+\\.(ts|tsx)$': 'babel-jest',
  },

  // Test file patterns
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}',
    '<rootDir>/src/**/*.{spec,test}.{js,jsx,ts,tsx}',
  ],

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/build/',
    '/dist/',
    'testUtils\\.js$', // Exclude utility files
    '/setup/', // Exclude setup files
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.js',
    '!src/index.js',
  ],

  // Module directories
  moduleDirectories: ['node_modules', 'src'],

  // File extensions
  moduleFileExtensions: ['js', 'jsx', 'ts', 'tsx', 'json'],
};
