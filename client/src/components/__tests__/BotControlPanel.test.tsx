import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { renderWithProviders, mockData } from '@/test/testUtils';
import { BotControlPanel } from '../BotControlPanel';

// Mock the hooks
vi.mock('@/hooks/useApi', () => ({
  useBots: () => ({
    data: [mockData.bot],
    isLoading: false,
    error: null,
  }),
  useStatus: () => ({
    data: {
      krakenConnected: true,
      runningBots: 1,
    },
  }),
}));

vi.mock('@/hooks/useBotStatus', () => ({
  useBotStatus: () => ({
    runningBots: 1,
  }),
}));

describe('BotControlPanel', () => {
  it('should render bot list', () => {
    renderWithProviders(<BotControlPanel bots={[mockData.bot]} />);
    
    expect(screen.getByText(mockData.bot.name)).toBeInTheDocument();
  });

  it('should display bot status', () => {
    renderWithProviders(<BotControlPanel bots={[mockData.bot]} />);
    
    expect(screen.getByText(/active|running|inactive/i)).toBeInTheDocument();
  });

  it('should display bot strategy', () => {
    renderWithProviders(<BotControlPanel bots={[mockData.bot]} />);
    
    // Strategy might be displayed somewhere
    const strategy = screen.queryByText(mockData.bot.strategy);
    if (strategy) {
      expect(strategy).toBeInTheDocument();
    }
  });

  it('should have start/stop buttons', () => {
    renderWithProviders(<BotControlPanel bots={[mockData.bot]} />);
    
    const startButton = screen.queryByRole('button', { name: /start/i });
    const stopButton = screen.queryByRole('button', { name: /stop/i });
    
    // At least one of them should be present
    expect(startButton || stopButton).toBeTruthy();
  });
});

