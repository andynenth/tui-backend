import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { PlayHistoryPage } from './PlayHistoryPage';
import { mockPlayHistory } from '../../mocks/playHistoryMock';

// Mock fetch globally
global.fetch = jest.fn();

describe('PlayHistoryPage Integration Tests', () => {
  const mockFetch = global.fetch;
  
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
  
  describe('Complete User Flow', () => {
    it('should load and display game history from URL entry', async () => {
      // Mock successful API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      // Render component with room ID from URL
      renderWithRouter('23BEBA');
      
      // Check loading state appears first
      expect(screen.getByText('Loading game history...')).toBeInTheDocument();
      
      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      // Verify API was called with correct URL
      expect(mockFetch).toHaveBeenCalledWith('/api/rooms/23BEBA/play-history');
      
      // Check all major sections are rendered
      expect(screen.getByText('Andy')).toBeInTheDocument();
      expect(screen.getByText('Bot 1')).toBeInTheDocument();
      expect(screen.getByText('Bot 2')).toBeInTheDocument();
      expect(screen.getByText('Bot 3')).toBeInTheDocument();
      
      // Check turn information
      expect(screen.getByText(/Turn 1/)).toBeInTheDocument();
      
      // Check no navigation elements (admin-only)
      expect(screen.queryByText('Back to Game')).not.toBeInTheDocument();
      expect(screen.queryByText('Home')).not.toBeInTheDocument();
    });
    
    it('should handle round navigation with data updates', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      renderWithRouter('23BEBA');
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      // Find and interact with round selector
      const roundSelector = screen.getByLabelText('Round:');
      expect(roundSelector).toHaveValue('1');
      
      // Change to round 2
      fireEvent.change(roundSelector, { target: { value: '2' } });
      
      // Check UI updates to show round 2
      expect(screen.getByText('Room 23BEBA - Round 2')).toBeInTheDocument();
      expect(roundSelector).toHaveValue('2');
      
      // Verify round 2 specific data is shown
      // (This assumes mockPlayHistory has multiple rounds)
    });
    
    it('should display hand before play for each turn', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      renderWithRouter('23BEBA');
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      // Check for "Hand Before Play" sections
      const handBeforeSections = screen.getAllByText('Hand Before Play');
      expect(handBeforeSections.length).toBeGreaterThan(0);
      
      // Check for piece display in hand
      expect(screen.getByText(/GENERAL\(14\)/)).toBeInTheDocument();
    });
  });
  
  describe('Error Recovery Flows', () => {
    it('should handle and recover from network errors', async () => {
      // First attempt fails
      mockFetch.mockRejectedValueOnce(new Error('Network error'));
      
      renderWithRouter('23BEBA');
      
      // Wait for error state
      await waitFor(() => {
        expect(screen.getByText('Failed to load game history')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
      
      // Find and click retry button
      const retryButton = screen.getByText('Retry');
      expect(retryButton).toBeInTheDocument();
      
      // Mock successful retry
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      fireEvent.click(retryButton);
      
      // Should show loading again
      expect(screen.getByText('Loading game history...')).toBeInTheDocument();
      
      // Should eventually show data
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
    });
    
    it('should handle 404 errors for non-existent rooms', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404
      });
      
      renderWithRouter('INVALID');
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load game history')).toBeInTheDocument();
        expect(screen.getByText('Game history not found')).toBeInTheDocument();
      });
      
      // Retry button should be available
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
    
    it('should handle corrupted data gracefully', async () => {
      // Mock response with invalid data structure
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ invalid: 'data' })
      });
      
      renderWithRouter('23BEBA');
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load game history')).toBeInTheDocument();
        expect(screen.getByText('Invalid game history data')).toBeInTheDocument();
      });
    });
  });
  
  describe('Admin-Specific Features', () => {
    it('should work without authentication', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      renderWithRouter('23BEBA');
      
      // No login prompt or auth errors
      expect(screen.queryByText('Login')).not.toBeInTheDocument();
      expect(screen.queryByText('Unauthorized')).not.toBeInTheDocument();
      
      // Data loads normally
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
    });
    
    it('should display all game details for admin analysis', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      renderWithRouter('23BEBA');
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      // Check comprehensive details are shown
      // Player stats
      expect(screen.getByText('Declared:')).toBeInTheDocument();
      expect(screen.getByText('Captured:')).toBeInTheDocument();
      expect(screen.getByText('Score:')).toBeInTheDocument();
      
      // Turn details
      expect(screen.getByText(/wins/)).toBeInTheDocument();
      
      // Round summary
      expect(screen.getByText('Round Summary')).toBeInTheDocument();
    });
    
    it('should handle direct URL access patterns', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      // Simulate direct navigation (no referrer)
      renderWithRouter('23BEBA');
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      // Should work without any navigation context
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('Data Consistency', () => {
    it('should maintain immutable data throughout interactions', async () => {
      const originalData = JSON.parse(JSON.stringify(mockPlayHistory));
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => originalData
      });
      
      renderWithRouter('23BEBA');
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      // Change rounds multiple times
      const roundSelector = screen.getByLabelText('Round:');
      fireEvent.change(roundSelector, { target: { value: '2' } });
      fireEvent.change(roundSelector, { target: { value: '1' } });
      fireEvent.change(roundSelector, { target: { value: '2' } });
      
      // Original data should remain unchanged
      expect(originalData).toEqual(mockPlayHistory);
    });
  });
});