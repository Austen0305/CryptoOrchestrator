/**
 * Tests for DashboardEnhancements components
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QuickStats, RecentActivity, PerformanceSummary } from '../DashboardEnhancements';

describe('QuickStats', () => {
  it('renders all stat cards', () => {
    render(
      <QuickStats
        totalValue={10000}
        change24h={5.2}
        activeBots={3}
        totalTrades={150}
      />
    );
    
    expect(screen.getByText(/total portfolio/i)).toBeInTheDocument();
    expect(screen.getByText(/active bots/i)).toBeInTheDocument();
    expect(screen.getByText(/total trades/i)).toBeInTheDocument();
    expect(screen.getByText(/status/i)).toBeInTheDocument();
  });

  it('formats currency correctly', () => {
    render(
      <QuickStats
        totalValue={12345.67}
        change24h={0}
        activeBots={0}
        totalTrades={0}
      />
    );
    
    // Should format as currency
    const value = screen.getByText(/\$12,345/);
    expect(value).toBeInTheDocument();
  });

  it('shows positive change in green', () => {
    const { container } = render(
      <QuickStats
        totalValue={10000}
        change24h={5.2}
        activeBots={0}
        totalTrades={0}
      />
    );
    
    const changeElement = container.querySelector('.text-green-500');
    expect(changeElement).toBeInTheDocument();
  });

  it('shows negative change in red', () => {
    const { container } = render(
      <QuickStats
        totalValue={10000}
        change24h={-3.5}
        activeBots={0}
        totalTrades={0}
      />
    );
    
    const changeElement = container.querySelector('.text-red-500');
    expect(changeElement).toBeInTheDocument();
  });
});

describe('RecentActivity', () => {
  const mockActivities = [
    {
      id: '1',
      type: 'trade' as const,
      message: 'Trade executed: BTC/USD',
      timestamp: '2025-01-01 10:00:00',
      status: 'success' as const,
    },
    {
      id: '2',
      type: 'bot' as const,
      message: 'Bot started: Momentum Bot',
      timestamp: '2025-01-01 09:00:00',
      status: 'success' as const,
    },
  ];

  it('renders activity list', () => {
    render(<RecentActivity activities={mockActivities} />);
    
    expect(screen.getByText(/recent activity/i)).toBeInTheDocument();
    expect(screen.getByText(/trade executed/i)).toBeInTheDocument();
    expect(screen.getByText(/bot started/i)).toBeInTheDocument();
  });

  it('shows empty state when no activities', () => {
    render(<RecentActivity activities={[]} />);
    
    expect(screen.getByText(/no recent activity/i)).toBeInTheDocument();
  });

  it('limits displayed activities', () => {
    const manyActivities = Array.from({ length: 20 }, (_, i) => ({
      id: String(i),
      type: 'trade' as const,
      message: `Activity ${i}`,
      timestamp: '2025-01-01 10:00:00',
    }));

    render(<RecentActivity activities={manyActivities} maxItems={5} />);
    
    // Should only show 5 items
    const activities = screen.getAllByText(/activity \d+/);
    expect(activities.length).toBeLessThanOrEqual(5);
  });
});

describe('PerformanceSummary', () => {
  it('renders all performance metrics', () => {
    render(
      <PerformanceSummary
        winRate={65.5}
        avgProfit={125.50}
        totalProfit={1250.75}
        bestTrade={500.00}
        worstTrade={-100.00}
      />
    );
    
    expect(screen.getByText(/win rate/i)).toBeInTheDocument();
    expect(screen.getByText(/avg profit/i)).toBeInTheDocument();
    expect(screen.getByText(/total profit/i)).toBeInTheDocument();
    expect(screen.getByText(/best trade/i)).toBeInTheDocument();
    expect(screen.getByText(/worst trade/i)).toBeInTheDocument();
  });

  it('formats percentages correctly', () => {
    render(
      <PerformanceSummary
        winRate={65.5}
        avgProfit={0}
        totalProfit={0}
        bestTrade={0}
        worstTrade={0}
      />
    );
    
    expect(screen.getByText(/65\.5%/)).toBeInTheDocument();
  });

  it('shows positive profits in green', () => {
    const { container } = render(
      <PerformanceSummary
        winRate={50}
        avgProfit={100}
        totalProfit={1000}
        bestTrade={500}
        worstTrade={-50}
      />
    );
    
    const greenElements = container.querySelectorAll('.text-green-500');
    expect(greenElements.length).toBeGreaterThan(0);
  });

  it('shows negative profits in red', () => {
    const { container } = render(
      <PerformanceSummary
        winRate={50}
        avgProfit={-50}
        totalProfit={-100}
        bestTrade={100}
        worstTrade={-200}
      />
    );
    
    const redElements = container.querySelectorAll('.text-red-500');
    expect(redElements.length).toBeGreaterThan(0);
  });
});

