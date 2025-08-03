/**
 * WaitingUI Component Tests
 *
 * Comprehensive test suite for WaitingUI component including:
 * - Basic rendering and display
 * - Connection status handling
 * - Phase-specific behavior
 * - User interactions (cancel, retry)
 * - Animation states
 * - Accessibility
 * - Edge cases and error handling
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import WaitingUI from '../game/WaitingUI';

// Mock the child components
jest.mock('../LoadingOverlay', () => ({
  __esModule: true,
  default: ({ message }) => (
    <div data-testid="loading-overlay" data-message={message}>
      {message}
    </div>
  ),
}));

jest.mock('../ConnectionIndicator', () => ({
  __esModule: true,
  default: ({ isConnected, isConnecting, isReconnecting, error }) => (
    <div
      data-testid="connection-indicator"
      data-connected={isConnected}
      data-connecting={isConnecting}
      data-reconnecting={isReconnecting}
      data-error={error}
    >
      Connection Status
    </div>
  ),
}));

describe('WaitingUI Component', () => {
  const defaultProps = {
    isConnected: true,
    isConnecting: false,
    isReconnecting: false,
    connectionError: null,
    message: 'Waiting...',
    phase: 'waiting',
    onRetry: jest.fn(),
    onCancel: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    test('renders with default props', () => {
      render(<WaitingUI {...defaultProps} />);

      expect(screen.getByText('Waiting for Game')).toBeInTheDocument();
      expect(screen.getByText('Waiting...')).toBeInTheDocument();
      expect(screen.getByTestId('connection-indicator')).toBeInTheDocument();
    });

    test('renders correct phase title for each phase', () => {
      const phases = [
        { phase: 'waiting', title: 'Waiting for Game' },
        { phase: 'preparation', title: 'Preparing Cards' },
        { phase: 'declaration', title: 'Making Declarations' },
        { phase: 'turn', title: 'Playing Turn' },
        { phase: 'scoring', title: 'Calculating Scores' },
      ];

      phases.forEach(({ phase, title }) => {
        const { rerender } = render(
          <WaitingUI {...defaultProps} phase={phase} />
        );
        expect(screen.getByText(title)).toBeInTheDocument();
        rerender(<div />); // Clear previous render
      });
    });

    test('renders correct phase icon for each phase', () => {
      const phases = [
        { phase: 'waiting', icon: '⏳' },
        { phase: 'preparation', icon: '🃏' },
        { phase: 'declaration', icon: '🎯' },
        { phase: 'turn', icon: '🎮' },
        { phase: 'scoring', icon: '🏆' },
      ];

      phases.forEach(({ phase, icon }) => {
        const { rerender } = render(
          <WaitingUI {...defaultProps} phase={phase} />
        );
        expect(screen.getByText(icon)).toBeInTheDocument();
        rerender(<div />); // Clear previous render
      });
    });

    test('displays custom message when provided', () => {
      const customMessage = 'Please wait while we set up your game...';
      render(<WaitingUI {...defaultProps} message={customMessage} />);

      expect(screen.getByText(customMessage)).toBeInTheDocument();
    });

    test('uses default message when none provided', () => {
      const { phase, ...propsWithoutMessage } = defaultProps;
      render(<WaitingUI {...propsWithoutMessage} />);

      expect(screen.getByText('Waiting...')).toBeInTheDocument();
    });
  });

  describe('Connection Status Display', () => {
    test('passes correct props to ConnectionIndicator', () => {
      const connectionProps = {
        isConnected: false,
        isConnecting: true,
        isReconnecting: false,
        connectionError: 'Network error',
      };

      render(<WaitingUI {...defaultProps} {...connectionProps} />);

      const indicator = screen.getByTestId('connection-indicator');
      expect(indicator).toHaveAttribute('data-connected', 'false');
      expect(indicator).toHaveAttribute('data-connecting', 'true');
      expect(indicator).toHaveAttribute('data-reconnecting', 'false');
      expect(indicator).toHaveAttribute('data-error', 'Network error');
    });

    test('shows correct connection status text', () => {
      const statusTests = [
        {
          props: {
            isConnected: true,
            isConnecting: false,
            isReconnecting: false,
            connectionError: null,
          },
          expected: 'Connected',
        },
        {
          props: {
            isConnected: false,
            isConnecting: true,
            isReconnecting: false,
            connectionError: null,
          },
          expected: 'Connecting',
        },
        {
          props: {
            isConnected: false,
            isConnecting: false,
            isReconnecting: true,
            connectionError: null,
          },
          expected: 'Reconnecting',
        },
        {
          props: {
            isConnected: false,
            isConnecting: false,
            isReconnecting: false,
            connectionError: 'Error',
          },
          expected: 'Error',
        },
        {
          props: {
            isConnected: false,
            isConnecting: false,
            isReconnecting: false,
            connectionError: null,
          },
          expected: 'Disconnected',
        },
      ];

      statusTests.forEach(({ props, expected }) => {
        const { rerender } = render(<WaitingUI {...defaultProps} {...props} />);
        expect(screen.getByText(expected)).toBeInTheDocument();
        rerender(<div />); // Clear previous render
      });
    });
  });

  describe('Loading States', () => {
    test('shows LoadingOverlay when connecting', () => {
      render(<WaitingUI {...defaultProps} isConnecting={true} />);

      const loadingOverlay = screen.getByTestId('loading-overlay');
      expect(loadingOverlay).toBeInTheDocument();
      expect(loadingOverlay).toHaveAttribute('data-message', 'Connecting...');
    });

    test('shows LoadingOverlay when reconnecting', () => {
      render(<WaitingUI {...defaultProps} isReconnecting={true} />);

      const loadingOverlay = screen.getByTestId('loading-overlay');
      expect(loadingOverlay).toBeInTheDocument();
      expect(loadingOverlay).toHaveAttribute('data-message', 'Reconnecting...');
    });

    test('does not show LoadingOverlay when not connecting', () => {
      render(
        <WaitingUI
          {...defaultProps}
          isConnecting={false}
          isReconnecting={false}
        />
      );

      expect(screen.queryByTestId('loading-overlay')).not.toBeInTheDocument();
    });

    test('shows waiting animation when not connecting and no error', () => {
      render(
        <WaitingUI
          {...defaultProps}
          isConnecting={false}
          connectionError={null}
        />
      );

      const waitingDots = document.querySelectorAll('.waiting-dot');
      expect(waitingDots).toHaveLength(3);
    });

    test('hides waiting animation when connecting or has error', () => {
      const { rerender } = render(
        <WaitingUI {...defaultProps} isConnecting={true} />
      );
      expect(document.querySelectorAll('.waiting-dot')).toHaveLength(0);

      rerender(
        <WaitingUI
          {...defaultProps}
          isConnecting={false}
          connectionError="Error"
        />
      );
      expect(document.querySelectorAll('.waiting-dot')).toHaveLength(0);
    });
  });

  describe('Error Handling', () => {
    test('displays error message when connectionError is provided', () => {
      const errorMessage = 'Failed to connect to server';
      render(<WaitingUI {...defaultProps} connectionError={errorMessage} />);

      expect(
        screen.getByText(`Connection Error: ${errorMessage}`)
      ).toBeInTheDocument();
    });

    test('shows retry button when error and onRetry provided', () => {
      const onRetry = jest.fn();
      render(
        <WaitingUI
          {...defaultProps}
          connectionError="Error"
          onRetry={onRetry}
        />
      );

      const retryButton = screen.getByText('Retry Connection');
      expect(retryButton).toBeInTheDocument();
      expect(retryButton).toHaveAttribute('aria-label', 'Retry connection');
    });

    test('does not show retry button when error but no onRetry', () => {
      render(
        <WaitingUI {...defaultProps} connectionError="Error" onRetry={null} />
      );

      expect(screen.queryByText('Retry Connection')).not.toBeInTheDocument();
    });

    test('does not show error section when no error', () => {
      render(<WaitingUI {...defaultProps} connectionError={null} />);

      expect(screen.queryByText(/Connection Error:/)).not.toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    test('calls onRetry when retry button is clicked', () => {
      const onRetry = jest.fn();
      render(
        <WaitingUI
          {...defaultProps}
          connectionError="Error"
          onRetry={onRetry}
        />
      );

      const retryButton = screen.getByText('Retry Connection');
      fireEvent.click(retryButton);

      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    test('calls onCancel when cancel button is clicked', () => {
      const onCancel = jest.fn();
      render(<WaitingUI {...defaultProps} onCancel={onCancel} />);

      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      expect(onCancel).toHaveBeenCalledTimes(1);
    });

    test('shows cancel button when onCancel provided', () => {
      const onCancel = jest.fn();
      render(<WaitingUI {...defaultProps} onCancel={onCancel} />);

      const cancelButton = screen.getByText('Cancel');
      expect(cancelButton).toBeInTheDocument();
      expect(cancelButton).toHaveAttribute('aria-label', 'Cancel and return');
    });

    test('does not show cancel button when onCancel not provided', () => {
      render(<WaitingUI {...defaultProps} onCancel={null} />);

      expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
    });

    test('retry button has hover effects', () => {
      const onRetry = jest.fn();
      render(
        <WaitingUI
          {...defaultProps}
          connectionError="Error"
          onRetry={onRetry}
        />
      );

      const retryButton = screen.getByText('Retry Connection');

      // Test mouse over
      fireEvent.mouseOver(retryButton);
      expect(retryButton.style.background).toBe('var(--color-danger-dark)');

      // Test mouse out
      fireEvent.mouseOut(retryButton);
      expect(retryButton.style.background).toBe('var(--gradient-danger)');
    });

    test('cancel button has hover effects', () => {
      const onCancel = jest.fn();
      render(<WaitingUI {...defaultProps} onCancel={onCancel} />);

      const cancelButton = screen.getByText('Cancel');

      // Test mouse over
      fireEvent.mouseOver(cancelButton);
      expect(cancelButton.style.color).toBe('var(--color-gray-600)');

      // Test mouse out
      fireEvent.mouseOut(cancelButton);
      expect(cancelButton.style.color).toBe('var(--color-gray-400)');
    });
  });

  describe('Phase Information Display', () => {
    test('displays current phase name', () => {
      render(<WaitingUI {...defaultProps} phase="preparation" />);

      expect(screen.getByText('Phase:')).toBeInTheDocument();
      expect(screen.getByText('preparation')).toBeInTheDocument();
    });

    test('displays connection status in info section', () => {
      render(<WaitingUI {...defaultProps} isConnected={true} />);

      expect(screen.getByText('Status:')).toBeInTheDocument();
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    test('defaults to waiting phase when no phase provided', () => {
      const { phase, ...propsWithoutPhase } = defaultProps;
      render(<WaitingUI {...propsWithoutPhase} />);

      expect(screen.getByText('waiting')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('has proper semantic structure', () => {
      render(<WaitingUI {...defaultProps} />);

      // Check for main content container
      const container = document.querySelector('.min-h-screen');
      expect(container).toBeInTheDocument();

      // Check for properly structured heading
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeInTheDocument();
    });

    test('buttons have proper accessibility labels', () => {
      const onRetry = jest.fn();
      const onCancel = jest.fn();
      render(
        <WaitingUI
          {...defaultProps}
          connectionError="Error"
          onRetry={onRetry}
          onCancel={onCancel}
        />
      );

      const retryButton = screen.getByLabelText('Retry connection');
      const cancelButton = screen.getByLabelText('Cancel and return');

      expect(retryButton).toBeInTheDocument();
      expect(cancelButton).toBeInTheDocument();
    });

    test('error section has proper styling for accessibility', () => {
      render(<WaitingUI {...defaultProps} connectionError="Test error" />);

      const errorSection = document.querySelector(
        '[style*="rgba(220, 53, 69"]'
      );
      expect(errorSection).toBeInTheDocument();
    });
  });

  describe('Visual Styling', () => {
    test('applies correct CSS classes and styles', () => {
      render(<WaitingUI {...defaultProps} />);

      // Check main container
      const container = document.querySelector(
        '.min-h-screen.flex.items-center.justify-center'
      );
      expect(container).toBeInTheDocument();

      // Check card container
      const card = document.querySelector('.rounded-2xl.p-8.max-w-md');
      expect(card).toBeInTheDocument();
      expect(card).toHaveStyle('background: var(--gradient-white)');
    });

    test('applies correct styling to phase icon', () => {
      render(<WaitingUI {...defaultProps} />);

      const icon = screen.getByText('⏳');
      expect(icon.className).toBe('text-6xl mb-4');
    });

    test('applies correct styling to title and message', () => {
      render(<WaitingUI {...defaultProps} />);

      const title = screen.getByText('Waiting for Game');
      expect(title.className).toBe('text-2xl font-bold mb-2');
      expect(title).toHaveStyle('color: var(--color-gray-700)');

      const message = screen.getByText('Waiting...');
      expect(message.className).toBe('text-lg');
      expect(message).toHaveStyle('color: var(--color-gray-500)');
    });
  });

  describe('Edge Cases and Error Conditions', () => {
    test('handles unknown phase gracefully', () => {
      render(<WaitingUI {...defaultProps} phase="unknown_phase" />);

      // Should default to waiting behavior
      expect(screen.getByText('⏳')).toBeInTheDocument();
      expect(screen.getByText('Waiting')).toBeInTheDocument();
    });

    test('handles null or undefined props gracefully', () => {
      expect(() => {
        render(
          <WaitingUI
            isConnected={null}
            isConnecting={undefined}
            message={null}
            phase={undefined}
          />
        );
      }).not.toThrow();
    });

    test('handles empty string message', () => {
      render(<WaitingUI {...defaultProps} message="" />);

      // Should still render without error
      expect(screen.getByText('Waiting for Game')).toBeInTheDocument();
    });

    test('handles boolean connection props correctly', () => {
      // Test with string values (should be falsy)
      render(
        <WaitingUI {...defaultProps} isConnected="false" isConnecting="true" />
      );

      // Should handle non-boolean values appropriately
      expect(
        document.querySelector('[data-connected="false"]')
      ).toBeInTheDocument();
    });

    test('handles missing callback functions', () => {
      expect(() => {
        render(
          <WaitingUI
            {...defaultProps}
            onRetry={undefined}
            onCancel={undefined}
          />
        );
      }).not.toThrow();

      // Should not show buttons when callbacks are undefined
      expect(screen.queryByText('Retry Connection')).not.toBeInTheDocument();
      expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
    });
  });

  describe('Component State Consistency', () => {
    test('shows only one loading state at a time', () => {
      render(
        <WaitingUI
          {...defaultProps}
          isConnecting={true}
          isReconnecting={true}
        />
      );

      // Should prioritize one loading state
      const loadingOverlays = screen.getAllByTestId('loading-overlay');
      expect(loadingOverlays).toHaveLength(1);
    });

    test('error state overrides loading animations', () => {
      render(
        <WaitingUI
          {...defaultProps}
          isConnecting={false}
          isReconnecting={false}
          connectionError="Network error"
        />
      );

      // Should show error, not waiting animation
      expect(screen.getByText(/Connection Error/)).toBeInTheDocument();
      expect(document.querySelectorAll('.waiting-dot')).toHaveLength(0);
    });

    test('maintains consistent state during rapid prop changes', async () => {
      const { rerender } = render(
        <WaitingUI {...defaultProps} isConnecting={true} />
      );

      expect(screen.getByTestId('loading-overlay')).toBeInTheDocument();

      rerender(
        <WaitingUI
          {...defaultProps}
          isConnecting={false}
          connectionError="Error"
        />
      );

      await waitFor(() => {
        expect(screen.queryByTestId('loading-overlay')).not.toBeInTheDocument();
        expect(screen.getByText(/Connection Error/)).toBeInTheDocument();
      });
    });
  });

  describe('Integration with Parent Components', () => {
    test('works correctly when wrapped in providers', () => {
      const TestWrapper = ({ children }) => (
        <div data-testid="wrapper">{children}</div>
      );

      render(
        <TestWrapper>
          <WaitingUI {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByTestId('wrapper')).toBeInTheDocument();
      expect(screen.getByText('Waiting for Game')).toBeInTheDocument();
    });

    test('callback functions receive correct parameters', () => {
      const onRetry = jest.fn();
      const onCancel = jest.fn();

      render(
        <WaitingUI
          {...defaultProps}
          connectionError="Error"
          onRetry={onRetry}
          onCancel={onCancel}
        />
      );

      fireEvent.click(screen.getByText('Retry Connection'));
      fireEvent.click(screen.getByText('Cancel'));

      expect(onRetry).toHaveBeenCalledWith();
      expect(onCancel).toHaveBeenCalledWith();
    });
  });
});
