import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

vi.mock('@/hooks/useApi', () => {
  return {
    useRunRiskScenario: () => {
      return {
        mutate: vi.fn(),
        data: null,
        isPending: false,
        error: null,
        reset: vi.fn(),
      };
    },
  };
});

import { RiskScenarioPanel } from '../RiskScenarioPanel';

describe('RiskScenarioPanel', () => {
  it('renders inputs and run button', () => {
    render(<RiskScenarioPanel />);
    expect(screen.getByLabelText(/Portfolio Value/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Baseline VaR/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Shock Percent/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Horizon/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Correlation Factor/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Run Scenario/i })).toBeInTheDocument();
  });

  it('calls mutate when Run Scenario button is clicked', () => {
    const mockMutate = vi.fn();
    vi.doMock('@/hooks/useApi', () => ({
      useRunRiskScenario: () => ({ mutate: mockMutate, data: null, isPending: false, error: null, reset: vi.fn() }),
    }));
    // re-import component under new mock
    const { RiskScenarioPanel: Panel } = require('../RiskScenarioPanel');
    render(<Panel />);
    fireEvent.click(screen.getByRole('button', { name: /Run Scenario/i }));
    expect(mockMutate).toHaveBeenCalledTimes(1);
  });
});
