import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import PlayHistoryPage from './PlayHistoryPage';
import * as usePlayHistoryHook from '../../hooks/usePlayHistory';
import { mockPlayHistory } from '../../mocks/playHistoryMock';

// Mock the usePlayHistory hook
jest.mock('../../hooks/usePlayHistory');

describe('PlayHistoryPage', () => {
  const mockRetry = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  const renderWithRouter = (roomId = '23BEBA') => {
    return render(
      <MemoryRouter initialEntries={[`/history/${roomId}`]}>
        <Routes>
          <Route path="/history/:roomId" element={<PlayHistoryPage />} />
        </Routes>
      </MemoryRouter>
    );
  };
  
  it('should show loading state initially', () => {
    usePlayHistoryHook.usePlayHistory.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      retry: mockRetry
    });
    
    renderWithRouter();
    
    expect(screen.getByText('Loading game history...')).toBeInTheDocument();
  });
  
  it('should render game history when loaded', async () => {
    usePlayHistoryHook.usePlayHistory.mockReturnValue({
      data: mockPlayHistory,
      loading: false,
      error: null,
      retry: mockRetry
    });
    
    renderWithRouter();
    
    await waitFor(() => {
      // Header elements
      expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      expect(screen.getByLabelText('Round:')).toBeInTheDocument();
      
      // Player overview
      expect(screen.getByText('Andy')).toBeInTheDocument();
      expect(screen.getByText('Bot 1')).toBeInTheDocument();
      expect(screen.getByText('Bot 2')).toBeInTheDocument();
      expect(screen.getByText('Bot 3')).toBeInTheDocument();
      
      // Section headers
      expect(screen.getByText('Declaration Phase')).toBeInTheDocument();
      expect(screen.getByText('Turn Timeline')).toBeInTheDocument();
      expect(screen.getByText('Round Summary')).toBeInTheDocument();
    });
  });
  
  it('should handle round selection', async () => {
    usePlayHistoryHook.usePlayHistory.mockReturnValue({
      data: mockPlayHistory,
      loading: false,
      error: null,
      retry: mockRetry
    });
    
    renderWithRouter();
    
    const selector = screen.getByLabelText('Round:');
    fireEvent.change(selector, { target: { value: '2' } });
    
    expect(screen.getByText('Room 23BEBA - Round 2')).toBeInTheDocument();
  });
  
  it('should display error state with retry button', async () => {
    const mockError = {
      message: 'Failed to fetch game history',
      code: 'NETWORK_ERROR',
      canRetry: true
    };
    
    usePlayHistoryHook.usePlayHistory.mockReturnValue({
      data: null,
      loading: false,
      error: mockError,
      retry: mockRetry
    });
    
    renderWithRouter();
    
    expect(screen.getByText('Failed to load game history')).toBeInTheDocument();
    expect(screen.getByText('Failed to fetch game history')).toBeInTheDocument();
    
    const retryButton = screen.getByRole('button', { name: 'Retry' });
    expect(retryButton).toBeInTheDocument();
    
    fireEvent.click(retryButton);
    expect(mockRetry).toHaveBeenCalledTimes(1);
  });
  
  it('should display empty state when no data', () => {
    usePlayHistoryHook.usePlayHistory.mockReturnValue({
      data: null,
      loading: false,
      error: null,
      retry: mockRetry
    });
    
    renderWithRouter();
    
    expect(screen.getByText('No game history found')).toBeInTheDocument();
  });
  
  it('should have data-testid for integration tests', () => {
    usePlayHistoryHook.usePlayHistory.mockReturnValue({
      data: mockPlayHistory,
      loading: false,
      error: null,
      retry: mockRetry
    });
    
    renderWithRouter();
    
    expect(screen.getByTestId('play-history-page')).toBeInTheDocument();
  });
  
  it('should not display any navigation elements (admin-only)', () => {
    usePlayHistoryHook.usePlayHistory.mockReturnValue({
      data: mockPlayHistory,
      loading: false,
      error: null,
      retry: mockRetry
    });
    
    renderWithRouter();
    
    // Should not have any "Back to Game" or navigation links
    expect(screen.queryByText(/Back to Game/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Back to Lobby/i)).not.toBeInTheDocument();
  });
  
  it('should highlight the starter player', () => {
    usePlayHistoryHook.usePlayHistory.mockReturnValue({
      data: mockPlayHistory,
      loading: false,
      error: null,
      retry: mockRetry
    });
    
    renderWithRouter();
    
    // Bot 3 is the starter in our mock data
    const starterBadge = screen.getByText('STARTER');
    expect(starterBadge).toBeInTheDocument();
  });
  
  it('should display winner in turn timeline', () => {
    usePlayHistoryHook.usePlayHistory.mockReturnValue({
      data: mockPlayHistory,
      loading: false,
      error: null,
      retry: mockRetry
    });
    
    renderWithRouter();
    
    // Check for winner display in turn
    expect(screen.getByText('Bot 3 wins')).toBeInTheDocument();
    expect(screen.getByText('• 3 pieces')).toBeInTheDocument();
  });
});