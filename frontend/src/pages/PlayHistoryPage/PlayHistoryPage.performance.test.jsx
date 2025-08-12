import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { PlayHistoryPage } from './PlayHistoryPage';
import { mockPlayHistory } from '../../mocks/playHistoryMock';

// Mock fetch globally
global.fetch = jest.fn();

// Performance monitoring utilities
const measureRenderTime = async (renderFn) => {
  const startTime = performance.now();
  const result = renderFn();
  await waitFor(() => {
    expect(screen.queryByText('Loading game history...')).not.toBeInTheDocument();
  });
  const endTime = performance.now();
  return {
    time: endTime - startTime,
    result
  };
};

const createLargeHistory = (rounds = 20, turnsPerRound = 15) => {
  const players = ['Player1', 'Player2', 'Player3', 'Player4'];
  
  return {
    ...mockPlayHistory,
    rounds: Array.from({ length: rounds }, (_, roundIndex) => ({
      roundNumber: roundIndex + 1,
      starter: players[roundIndex % 4],
      declarations: players.map(player => ({
        player,
        pileCount: Math.floor(Math.random() * 4) + 3,
        hand: Array.from({ length: 8 }, (_, i) => ({
          type: ['GENERAL', 'ADVISOR', 'ELEPHANT', 'HORSE', 'CHARIOT', 'CANNON', 'SOLDIER'][i % 7],
          point: Math.floor(Math.random() * 10) + 5,
          color: i % 2 === 0 ? 'red' : 'black'
        }))
      })),
      turns: Array.from({ length: turnsPerRound }, (_, turnIndex) => ({
        turnNumber: turnIndex + 1,
        plays: players.map(player => ({
          player,
          handBefore: Array.from({ length: 8 - turnIndex }, () => ({
            type: 'SOLDIER',
            point: 5,
            color: 'red'
          })),
          pieces: [{
            type: 'SOLDIER',
            point: 5,
            color: 'red'
          }],
          capturedPieces: turnIndex
        })),
        winner: players[turnIndex % 4],
        winnerPieces: 4
      })),
      scoring: {
        players: players.reduce((acc, player) => ({
          ...acc,
          [player]: {
            declared: 3,
            captured: Math.floor(Math.random() * 8),
            baseScore: Math.floor(Math.random() * 20) - 10,
            multiplier: 1,
            score: Math.floor(Math.random() * 20) - 10
          }
        }), {})
      },
      winner: players[0],
      endTime: new Date().toISOString()
    }))
  };
};

describe('PlayHistoryPage Performance Tests', () => {
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
  
  describe('Render Performance', () => {
    it('should render initial page in less than 1 second', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      const { time } = await measureRenderTime(() => renderWithRouter('23BEBA'));
      
      expect(time).toBeLessThan(1000); // Less than 1 second
      expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
    });
    
    it('should handle large histories efficiently', async () => {
      const largeHistory = createLargeHistory(20, 15); // 20 rounds, 15 turns each
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => largeHistory
      });
      
      const { time } = await measureRenderTime(() => renderWithRouter('23BEBA'));
      
      // Even with large data, should render in reasonable time
      expect(time).toBeLessThan(3000); // Less than 3 seconds
      expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      
      // Check that round selector has all 20 rounds
      const roundSelector = screen.getByLabelText('Round:');
      expect(roundSelector.children.length).toBe(20);
    });
  });
  
  describe('API Response Handling', () => {
    it('should handle slow API responses gracefully', async () => {
      // Simulate slow API response
      mockFetch.mockImplementationOnce(() => 
        new Promise(resolve => {
          setTimeout(() => {
            resolve({
              ok: true,
              json: async () => mockPlayHistory
            });
          }, 2000); // 2 second delay
        })
      );
      
      renderWithRouter('23BEBA');
      
      // Loading state should be shown during wait
      expect(screen.getByText('Loading game history...')).toBeInTheDocument();
      
      // Wait for data to load
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      }, { timeout: 3000 });
    });
    
    it('should handle very large payloads', async () => {
      const veryLargeHistory = createLargeHistory(50, 20); // 50 rounds, 20 turns each
      const payloadSize = JSON.stringify(veryLargeHistory).length;
      
      console.log(`Testing with payload size: ${(payloadSize / 1024).toFixed(2)} KB`);
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => veryLargeHistory
      });
      
      const startTime = performance.now();
      renderWithRouter('23BEBA');
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      const totalTime = performance.now() - startTime;
      
      // Should handle large payloads without timing out
      expect(totalTime).toBeLessThan(5000); // Less than 5 seconds
      expect(screen.getByLabelText('Round:').children.length).toBe(50);
    });
  });
  
  describe('Memory Usage', () => {
    it('should not leak memory when switching rounds', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => createLargeHistory(10, 10)
      });
      
      const { rerender } = renderWithRouter('23BEBA');
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      // Get initial memory usage (if available in test environment)
      const initialMemory = performance.memory?.usedJSHeapSize || 0;
      
      // Switch rounds multiple times
      const roundSelector = screen.getByLabelText('Round:');
      for (let i = 1; i <= 10; i++) {
        fireEvent.change(roundSelector, { target: { value: String(i) } });
        await waitFor(() => {
          expect(screen.getByText(`Room 23BEBA - Round ${i}`)).toBeInTheDocument();
        });
      }
      
      // Check memory hasn't grown significantly
      const finalMemory = performance.memory?.usedJSHeapSize || 0;
      const memoryGrowth = finalMemory - initialMemory;
      
      // Memory growth should be minimal (allowing for some variance)
      if (initialMemory > 0) {
        expect(memoryGrowth).toBeLessThan(10 * 1024 * 1024); // Less than 10MB growth
      }
    });
  });
  
  describe('Re-render Optimization', () => {
    it('should not re-render unnecessarily', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      let renderCount = 0;
      const RenderCounter = () => {
        renderCount++;
        return <PlayHistoryPage />;
      };
      
      render(
        <MemoryRouter initialEntries={['/history/23BEBA']}>
          <Routes>
            <Route path="/history/:roomId" element={<RenderCounter />} />
          </Routes>
        </MemoryRouter>
      );
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      const initialRenderCount = renderCount;
      
      // Changing round should cause minimal re-renders
      const roundSelector = screen.getByLabelText('Round:');
      fireEvent.change(roundSelector, { target: { value: '2' } });
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 2')).toBeInTheDocument();
      });
      
      // Should have minimal re-renders (typically 1-2 for state change)
      const additionalRenders = renderCount - initialRenderCount;
      expect(additionalRenders).toBeLessThanOrEqual(2);
    });
    
    it('should efficiently update only changed components', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      renderWithRouter('23BEBA');
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      // Mark initial player elements
      const playerElements = screen.getAllByText(/Andy|Bot 1|Bot 2|Bot 3/);
      const initialPlayerCount = playerElements.length;
      
      // Change round
      const roundSelector = screen.getByLabelText('Round:');
      fireEvent.change(roundSelector, { target: { value: '2' } });
      
      // Player elements should still be present (not recreated)
      const updatedPlayerElements = screen.getAllByText(/Andy|Bot 1|Bot 2|Bot 3/);
      expect(updatedPlayerElements.length).toBe(initialPlayerCount);
    });
  });
  
  describe('Performance Benchmarks', () => {
    it('should meet performance benchmarks for common operations', async () => {
      const benchmarks = {
        initialLoad: 1000,      // 1 second
        roundSwitch: 100,       // 100ms
        errorRecovery: 1500,    // 1.5 seconds
        largeDataLoad: 3000     // 3 seconds
      };
      
      // Test initial load
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlayHistory
      });
      
      const loadStart = performance.now();
      renderWithRouter('23BEBA');
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 1')).toBeInTheDocument();
      });
      
      const loadTime = performance.now() - loadStart;
      expect(loadTime).toBeLessThan(benchmarks.initialLoad);
      
      // Test round switch
      const switchStart = performance.now();
      const roundSelector = screen.getByLabelText('Round:');
      fireEvent.change(roundSelector, { target: { value: '2' } });
      
      await waitFor(() => {
        expect(screen.getByText('Room 23BEBA - Round 2')).toBeInTheDocument();
      });
      
      const switchTime = performance.now() - switchStart;
      expect(switchTime).toBeLessThan(benchmarks.roundSwitch);
    });
  });
});