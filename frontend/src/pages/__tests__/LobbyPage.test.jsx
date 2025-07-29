import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import LobbyPage from '../LobbyPage';
import { App } from '../../App';
import NetworkService from '../../network/NetworkService';

// Mock NetworkService
jest.mock('../../network/NetworkService', () => ({
  __esModule: true,
  default: {
    getInstance: jest.fn(),
  },
}));

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('Lobby Real-time Updates', () => {
  let mockNetworkService;
  let mockApp;
  let eventListeners;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    mockNavigate.mockReset();
    
    // Create event listener tracking
    eventListeners = {};
    
    // Mock NetworkService instance
    mockNetworkService = {
      isConnected: jest.fn(() => true),
      connectToRoom: jest.fn(() => Promise.resolve()),
      disconnectFromRoom: jest.fn(),
      send: jest.fn(),
      addEventListener: jest.fn((event, handler) => {
        if (!eventListeners[event]) {
          eventListeners[event] = [];
        }
        eventListeners[event].push(handler);
      }),
      removeEventListener: jest.fn((event, handler) => {
        if (eventListeners[event]) {
          eventListeners[event] = eventListeners[event].filter(h => h !== handler);
        }
      }),
    };
    
    NetworkService.getInstance.mockReturnValue(mockNetworkService);
    
    // Mock App instance
    mockApp = {
      playerName: 'TestPlayer',
      goToRoom: jest.fn(),
    };
    
    // Mock global app
    global.app = mockApp;
  });

  afterEach(() => {
    delete global.app;
  });

  // Helper function to emit events
  const emitEvent = (eventName, data) => {
    const handlers = eventListeners[eventName] || [];
    handlers.forEach(handler => {
      handler({ detail: { data } });
    });
  };

  // Helper function to render with router
  const renderWithRouter = (component) => {
    return render(
      <BrowserRouter>
        {component}
      </BrowserRouter>
    );
  };

  describe('Room Creation Visibility', () => {
    test('should display newly created rooms to all lobby users', async () => {
      renderWithRouter(<LobbyPage />);
      
      // Wait for initial connection
      await waitFor(() => {
        expect(mockNetworkService.connectToRoom).toHaveBeenCalledWith('lobby');
      });
      
      // Verify initial get_rooms request
      expect(mockNetworkService.send).toHaveBeenCalledWith('lobby', 'get_rooms', {});
      
      // Simulate empty initial room list
      act(() => {
        emitEvent('room_list_update', {
          rooms: [],
          total_count: 0
        });
      });
      
      // Verify no rooms displayed
      expect(screen.queryByText('Available Rooms')).toBeInTheDocument();
      expect(screen.queryByText('No rooms available')).toBeInTheDocument();
      
      // Simulate new room creation
      act(() => {
        emitEvent('room_list_update', {
          rooms: [{
            room_id: 'ROOM001',
            room_code: 'ROOM001',
            room_name: "Alice's Room",
            host_name: 'Alice',
            player_count: 1,
            max_players: 4,
            game_in_progress: false,
            is_private: false
          }],
          total_count: 1
        });
      });
      
      // Verify new room appears
      await waitFor(() => {
        expect(screen.getByText("Alice's Room")).toBeInTheDocument();
        expect(screen.getByText('1/4 players')).toBeInTheDocument();
      });
    });

    test('should handle multiple rooms appearing simultaneously', async () => {
      renderWithRouter(<LobbyPage />);
      
      await waitFor(() => {
        expect(mockNetworkService.connectToRoom).toHaveBeenCalled();
      });
      
      // Simulate multiple rooms
      act(() => {
        emitEvent('room_list_update', {
          rooms: [
            {
              room_id: 'ROOM001',
              room_code: 'ROOM001',
              room_name: "Alice's Room",
              host_name: 'Alice',
              player_count: 2,
              max_players: 4,
              game_in_progress: false,
              is_private: false
            },
            {
              room_id: 'ROOM002',
              room_code: 'ROOM002',
              room_name: "Bob's Room",
              host_name: 'Bob',
              player_count: 3,
              max_players: 4,
              game_in_progress: false,
              is_private: false
            },
            {
              room_id: 'ROOM003',
              room_code: 'ROOM003',
              room_name: "Charlie's Room",
              host_name: 'Charlie',
              player_count: 4,
              max_players: 4,
              game_in_progress: true,
              is_private: false
            }
          ],
          total_count: 3
        });
      });
      
      // Verify all rooms appear
      await waitFor(() => {
        expect(screen.getByText("Alice's Room")).toBeInTheDocument();
        expect(screen.getByText("Bob's Room")).toBeInTheDocument();
        expect(screen.getByText("Charlie's Room")).toBeInTheDocument();
      });
      
      // Verify room states
      expect(screen.getByText('2/4 players')).toBeInTheDocument();
      expect(screen.getByText('3/4 players')).toBeInTheDocument();
      expect(screen.getByText('FULL')).toBeInTheDocument();
      expect(screen.getByText('In Game')).toBeInTheDocument();
    });
  });

  describe('Player Count Updates', () => {
    test('should update player count when users join/leave rooms', async () => {
      renderWithRouter(<LobbyPage />);
      
      await waitFor(() => {
        expect(mockNetworkService.connectToRoom).toHaveBeenCalled();
      });
      
      // Initial room with 1 player
      act(() => {
        emitEvent('room_list_update', {
          rooms: [{
            room_id: 'ROOM001',
            room_code: 'ROOM001',
            room_name: "Test Room",
            host_name: 'Host',
            player_count: 1,
            max_players: 4,
            game_in_progress: false,
            is_private: false
          }],
          total_count: 1
        });
      });
      
      expect(screen.getByText('1/4 players')).toBeInTheDocument();
      
      // Player joins - count increases
      act(() => {
        emitEvent('room_list_update', {
          rooms: [{
            room_id: 'ROOM001',
            room_code: 'ROOM001',
            room_name: "Test Room",
            host_name: 'Host',
            player_count: 2,
            max_players: 4,
            game_in_progress: false,
            is_private: false
          }],
          total_count: 1
        });
      });
      
      await waitFor(() => {
        expect(screen.getByText('2/4 players')).toBeInTheDocument();
      });
      
      // Player leaves - count decreases
      act(() => {
        emitEvent('room_list_update', {
          rooms: [{
            room_id: 'ROOM001',
            room_code: 'ROOM001',
            room_name: "Test Room",
            host_name: 'Host',
            player_count: 1,
            max_players: 4,
            game_in_progress: false,
            is_private: false
          }],
          total_count: 1
        });
      });
      
      await waitFor(() => {
        expect(screen.getByText('1/4 players')).toBeInTheDocument();
      });
    });

    test('should show FULL status when room reaches capacity', async () => {
      renderWithRouter(<LobbyPage />);
      
      await waitFor(() => {
        expect(mockNetworkService.connectToRoom).toHaveBeenCalled();
      });
      
      // Room with 3 players
      act(() => {
        emitEvent('room_list_update', {
          rooms: [{
            room_id: 'ROOM001',
            room_code: 'ROOM001',
            room_name: "Almost Full Room",
            host_name: 'Host',
            player_count: 3,
            max_players: 4,
            game_in_progress: false,
            is_private: false
          }],
          total_count: 1
        });
      });
      
      expect(screen.getByText('3/4 players')).toBeInTheDocument();
      expect(screen.getByText('Join')).toBeInTheDocument();
      
      // Room becomes full
      act(() => {
        emitEvent('room_list_update', {
          rooms: [{
            room_id: 'ROOM001',
            room_code: 'ROOM001',
            room_name: "Almost Full Room",
            host_name: 'Host',
            player_count: 4,
            max_players: 4,
            game_in_progress: false,
            is_private: false
          }],
          total_count: 1
        });
      });
      
      await waitFor(() => {
        expect(screen.getByText('FULL')).toBeInTheDocument();
        expect(screen.queryByText('Join')).not.toBeInTheDocument();
      });
    });
  });

  describe('Room State Changes', () => {
    test('should remove rooms from lobby when deleted', async () => {
      renderWithRouter(<LobbyPage />);
      
      await waitFor(() => {
        expect(mockNetworkService.connectToRoom).toHaveBeenCalled();
      });
      
      // Initial rooms
      act(() => {
        emitEvent('room_list_update', {
          rooms: [
            {
              room_id: 'ROOM001',
              room_code: 'ROOM001',
              room_name: "Room 1",
              host_name: 'Host1',
              player_count: 2,
              max_players: 4,
              game_in_progress: false,
              is_private: false
            },
            {
              room_id: 'ROOM002',
              room_code: 'ROOM002',
              room_name: "Room 2",
              host_name: 'Host2',
              player_count: 1,
              max_players: 4,
              game_in_progress: false,
              is_private: false
            }
          ],
          total_count: 2
        });
      });
      
      expect(screen.getByText("Room 1")).toBeInTheDocument();
      expect(screen.getByText("Room 2")).toBeInTheDocument();
      
      // Room 2 is deleted
      act(() => {
        emitEvent('room_list_update', {
          rooms: [
            {
              room_id: 'ROOM001',
              room_code: 'ROOM001',
              room_name: "Room 1",
              host_name: 'Host1',
              player_count: 2,
              max_players: 4,
              game_in_progress: false,
              is_private: false
            }
          ],
          total_count: 1
        });
      });
      
      await waitFor(() => {
        expect(screen.getByText("Room 1")).toBeInTheDocument();
        expect(screen.queryByText("Room 2")).not.toBeInTheDocument();
      });
    });

    test('should update room status when game starts', async () => {
      renderWithRouter(<LobbyPage />);
      
      await waitFor(() => {
        expect(mockNetworkService.connectToRoom).toHaveBeenCalled();
      });
      
      // Room in waiting state
      act(() => {
        emitEvent('room_list_update', {
          rooms: [{
            room_id: 'ROOM001',
            room_code: 'ROOM001',
            room_name: "Game Room",
            host_name: 'Host',
            player_count: 4,
            max_players: 4,
            game_in_progress: false,
            is_private: false
          }],
          total_count: 1
        });
      });
      
      expect(screen.getByText('FULL')).toBeInTheDocument();
      expect(screen.queryByText('In Game')).not.toBeInTheDocument();
      
      // Game starts
      act(() => {
        emitEvent('room_list_update', {
          rooms: [{
            room_id: 'ROOM001',
            room_code: 'ROOM001',
            room_name: "Game Room",
            host_name: 'Host',
            player_count: 4,
            max_players: 4,
            game_in_progress: true,
            is_private: false
          }],
          total_count: 1
        });
      });
      
      await waitFor(() => {
        expect(screen.getByText('In Game')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    test('should handle network delays gracefully', async () => {
      renderWithRouter(<LobbyPage />);
      
      // Delay the connection
      mockNetworkService.connectToRoom.mockImplementation(() => 
        new Promise(resolve => setTimeout(resolve, 100))
      );
      
      await waitFor(() => {
        expect(mockNetworkService.connectToRoom).toHaveBeenCalled();
      });
      
      // Should show loading state initially
      expect(screen.getByText(/Connecting to lobby/i)).toBeInTheDocument();
      
      // After connection
      await waitFor(() => {
        expect(screen.queryByText(/Connecting to lobby/i)).not.toBeInTheDocument();
      });
    });

    test('should handle concurrent room updates', async () => {
      renderWithRouter(<LobbyPage />);
      
      await waitFor(() => {
        expect(mockNetworkService.connectToRoom).toHaveBeenCalled();
      });
      
      // Simulate rapid concurrent updates
      const updates = [
        { rooms: [{ room_id: 'R1', room_code: 'R1', room_name: 'Room 1', host_name: 'H1', player_count: 1, max_players: 4, game_in_progress: false, is_private: false }], total_count: 1 },
        { rooms: [{ room_id: 'R1', room_code: 'R1', room_name: 'Room 1', host_name: 'H1', player_count: 2, max_players: 4, game_in_progress: false, is_private: false }], total_count: 1 },
        { rooms: [{ room_id: 'R1', room_code: 'R1', room_name: 'Room 1', host_name: 'H1', player_count: 3, max_players: 4, game_in_progress: false, is_private: false }], total_count: 1 },
      ];
      
      // Send all updates rapidly
      act(() => {
        updates.forEach(update => {
          emitEvent('room_list_update', update);
        });
      });
      
      // Should show final state
      await waitFor(() => {
        expect(screen.getByText('3/4 players')).toBeInTheDocument();
      });
    });

    test('should handle empty lobby state', async () => {
      renderWithRouter(<LobbyPage />);
      
      await waitFor(() => {
        expect(mockNetworkService.connectToRoom).toHaveBeenCalled();
      });
      
      // Empty room list
      act(() => {
        emitEvent('room_list_update', {
          rooms: [],
          total_count: 0
        });
      });
      
      await waitFor(() => {
        expect(screen.getByText('No rooms available')).toBeInTheDocument();
        expect(screen.getByText('Create Room')).toBeInTheDocument();
      });
    });

    test('should refresh room list on manual refresh', async () => {
      renderWithRouter(<LobbyPage />);
      
      await waitFor(() => {
        expect(mockNetworkService.connectToRoom).toHaveBeenCalled();
      });
      
      // Initial room list request
      expect(mockNetworkService.send).toHaveBeenCalledTimes(1);
      
      // Click refresh button
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);
      
      // Should send another get_rooms request
      expect(mockNetworkService.send).toHaveBeenCalledTimes(2);
      expect(mockNetworkService.send).toHaveBeenLastCalledWith('lobby', 'get_rooms', {});
    });
  });
});