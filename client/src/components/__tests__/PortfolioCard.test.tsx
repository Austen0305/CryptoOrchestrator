import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { renderWithProviders, mockData } from '@/test/testUtils';
import { PortfolioCard } from '../PortfolioCard';

// Mock the hook
vi.mock('@/hooks/useApi', () => ({
  usePortfolio: () => ({
    data: mockData.portfolio,
    isLoading: false,
    error: null,
  }),
}));

describe('PortfolioCard', () => {
  it('should render portfolio information', () => {
    renderWithProviders(<PortfolioCard />);

    expect(screen.getByText(/portfolio|total/i)).toBeInTheDocument();
  });

  it('should display total value', () => {
    renderWithProviders(<PortfolioCard />);

    expect(screen.getByText(/10,000|10000/)).toBeInTheDocument();
  });

  it('should display profit/loss', () => {
    renderWithProviders(<PortfolioCard />);

    expect(screen.getByText(/profit|loss/i)).toBeInTheDocument();
  });
});

