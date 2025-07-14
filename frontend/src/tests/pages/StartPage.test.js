import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import StartPage from '../../pages/StartPage.jsx';
import { AppContext } from '../../contexts/AppContext.jsx';

// Mock the useNavigate hook
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const TestWrapper = ({ children, contextValue = {} }) => {
  const defaultContext = {
    playerName: '',
    setPlayerName: jest.fn(),
    gameState: null,
    setGameState: jest.fn(),
    connectionStatus: 'disconnected',
    ...contextValue,
  };

  return (
    <BrowserRouter>
      <AppContext.Provider value={defaultContext}>
        {children}
      </AppContext.Provider>
    </BrowserRouter>
  );
};

describe('StartPage Component', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    localStorage.clear();
  });

  test('renders start page with input field', () => {
    render(
      <TestWrapper>
        <StartPage />
      </TestWrapper>
    );

    expect(screen.getByText(/Enter your name/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Your name/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Enter Game/i })
    ).toBeInTheDocument();
  });

  test('updates player name on input change', async () => {
    const user = userEvent.setup();
    const setPlayerName = jest.fn();

    render(
      <TestWrapper contextValue={{ setPlayerName }}>
        <StartPage />
      </TestWrapper>
    );

    const input = screen.getByPlaceholderText(/Your name/i);
    await user.type(input, 'TestPlayer');

    expect(setPlayerName).toHaveBeenCalledWith('TestPlayer');
  });

  test('navigates to lobby when form is submitted with valid name', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper contextValue={{ playerName: 'TestPlayer' }}>
        <StartPage />
      </TestWrapper>
    );

    const button = screen.getByRole('button', { name: /Enter Game/i });
    await user.click(button);

    expect(mockNavigate).toHaveBeenCalledWith('/lobby');
  });

  test('does not navigate with empty name', async () => {
    const user = userEvent.setup();

    render(
      <TestWrapper contextValue={{ playerName: '' }}>
        <StartPage />
      </TestWrapper>
    );

    const button = screen.getByRole('button', { name: /Enter Game/i });
    await user.click(button);

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('loads saved player name from localStorage', () => {
    localStorage.setItem('playerName', 'SavedPlayer');
    const setPlayerName = jest.fn();

    render(
      <TestWrapper contextValue={{ setPlayerName }}>
        <StartPage />
      </TestWrapper>
    );

    expect(setPlayerName).toHaveBeenCalledWith('SavedPlayer');
  });
});
